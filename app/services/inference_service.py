from __future__ import annotations
import time
import uuid
from typing import Dict, Tuple
import numpy as np
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import PredictionLog
from app.schemas.prediction import ModelDecision, PredictionResponse
from app.services.artifact_loader import ArtifactBundle
from app.services.brand_impersonation_service import BrandImpersonationService
from app.services.explanation_service import ExplanationService
from app.services.feature_extractor import FeatureExtractor
from app.services.privacy_service import hash_url, mask_url
from app.services.transformer_service import URLTransformerService
from app.services.url_security import normalize_and_validate_url

settings = get_settings()


class InferenceService:
    def __init__(self, artifacts: ArtifactBundle, transformer: URLTransformerService):
        self.artifacts = artifacts
        self.transformer = transformer
        self.extractor = FeatureExtractor(artifacts.features, artifacts.frozen_graph)
        self.explainer = ExplanationService(artifacts.explanation_templates, artifacts.feature_importance)
        self.brand_service = BrandImpersonationService()

    def _proba_map(self, proba: np.ndarray) -> Dict[str, float]:
        labels = self.artifacts.classes
        if not labels:
            labels = [str(x) for x in getattr(self.artifacts.model, "classes_", range(len(proba)))]
        return {labels[i]: float(proba[i]) for i in range(min(len(labels), len(proba)))}

    @staticmethod
    def _confidence_margin(probabilities: Dict[str, float]) -> Tuple[str, float, float]:
        ordered = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        top_class, top_prob = ordered[0]
        second = ordered[1][1] if len(ordered) > 1 else 0.0
        return top_class, float(top_prob), float(top_prob - second)

    @staticmethod
    def _risk_score(probabilities: Dict[str, float]) -> float:
        return float(1.0 - probabilities.get("benign", 0.0))

    @staticmethod
    def _risk_level(risk: float) -> str:
        if risk < 0.30:
            return "low"
        if risk < 0.60:
            return "medium"
        if risk < 0.85:
            return "high"
        return "critical"

    @staticmethod
    def _action(risk: float) -> str:
        if risk < 0.30:
            return "proceed"
        if risk < 0.60:
            return "caution"
        if risk < 0.85:
            return "block"
        return "report"

    @staticmethod
    def _elapsed_ms(start: float) -> float:
        return round((time.perf_counter() - start) * 1000, 4)

    def _needs_transformer(self, hist_conf: float, hist_margin: float, hist_risk: float, full_features: dict, brand_signals: dict | None = None) -> tuple[bool, dict]:
        unseen_ratio = float(full_features.get("unique_token_ratio", 0.0) or 0.0)
        near_boundary = settings.risk_boundary_low <= hist_risk <= settings.risk_boundary_high
        low_conf = hist_conf <= settings.histgb_confidence_threshold
        low_margin = hist_margin < settings.histgb_margin_threshold
        high_unseen = unseen_ratio > 0.50
        brand_impersonation = bool((brand_signals or {}).get("impersonationDetected", False))
        official_domain = bool((brand_signals or {}).get("officialDomainMatched", False))
        brand_score = float((brand_signals or {}).get("score", 0.0) or 0.0)
        trusted_domain_check = official_domain and hist_risk >= settings.risk_boundary_low
        # Run URL-Transformer as an additional raw-character check for uncertain, brand-lookalike,
        # and trusted-official-domain cases where HistGB may be overreacting to brand tokens.
        use = bool(self.transformer.available and (low_conf or low_margin or near_boundary or high_unseen or brand_impersonation or trusted_domain_check))
        return use, {
            "histgbConfidence": round(hist_conf, 6),
            "histgbMargin": round(hist_margin, 6),
            "histgbRiskScore": round(hist_risk, 6),
            "nearBoundary": near_boundary,
            "lowConfidence": low_conf,
            "lowMargin": low_margin,
            "highUnseenTokenRatio": high_unseen,
            "unseenTokenRatio": round(unseen_ratio, 6),
            "brandImpersonationDetected": brand_impersonation,
            "brandOfficialDomainMatched": official_domain,
            "trustedDomainDisagreementCheck": trusted_domain_check,
            "brandImpersonationScore": round(brand_score, 6),
        }

    def _resolve(self, hist_probs: Dict[str, float], trans_probs: Dict[str, float] | None, brand_signals: dict | None = None) -> tuple[str, Dict[str, float], str, bool]:
        hist_cls, hist_conf, hist_margin = self._confidence_margin(hist_probs)
        if not trans_probs:
            return hist_cls, hist_probs, "histgb_confident_or_transformer_unavailable", False

        trans_cls, trans_conf, trans_margin = self._confidence_margin(trans_probs)
        trusted_official = bool((brand_signals or {}).get("officialDomainMatched", False))

        if trusted_official and hist_cls != trans_cls and "benign" in {hist_cls, trans_cls}:
            benign_probs = hist_probs if hist_cls == "benign" else trans_probs
            benign_conf = hist_conf if hist_cls == "benign" else trans_conf
            benign_margin = hist_margin if hist_cls == "benign" else trans_margin
            malicious_conf = trans_conf if hist_cls == "benign" else hist_conf
            malicious_margin = trans_margin if hist_cls == "benign" else hist_margin
            benign_is_strong = benign_conf >= 0.90 and benign_margin >= 0.65
            malicious_is_weak = malicious_conf < 0.75 or malicious_margin < 0.35
            if benign_is_strong and malicious_is_weak:
                return "benign", benign_probs, "trusted_official_domain_benign_model_priority", True

        brand_impersonation = bool((brand_signals or {}).get("impersonationDetected", False))
        weak_histgb = hist_conf <= settings.histgb_confidence_threshold
        strong_transformer = (
            trans_conf >= settings.url_transformer_override_confidence_threshold
            and trans_margin >= settings.url_transformer_override_margin_threshold
        )
        benign_transformer_blocked_by_brand = brand_impersonation and trans_cls == "benign"
        if hist_cls != trans_cls and weak_histgb and strong_transformer and not benign_transformer_blocked_by_brand:
            return trans_cls, trans_probs, "urltransformer_high_confidence_over_weak_histgb", True

        if hist_cls == trans_cls:
            keys = hist_probs.keys()
            mixed = {k: 0.70 * hist_probs[k] + 0.30 * trans_probs.get(k, 0.0) for k in keys}
            final_cls, _, _ = self._confidence_margin(mixed)
            return final_cls, mixed, "histgb_urltransformer_agreement", True

        if hist_cls == "benign" and trans_cls != "benign":
            return trans_cls, trans_probs, "transformer_disagreed_safer_malicious", True
        if hist_cls != "benign" and trans_cls == "benign":
            return hist_cls, hist_probs, "histgb_disagreed_safer_malicious", True
        return hist_cls, hist_probs, "malicious_disagreement_histgb_priority", True


    @staticmethod
    def _apply_brand_override(final_cls: str, final_probs: Dict[str, float], decision_source: str, brand_signals: dict | None) -> tuple[str, Dict[str, float], str]:
        """Raise risk when the URL is a protected-brand lookalike.

        The ML model may classify a short, clean-looking lookalike such as
        kkktun.edu.tr as benign because it has few malicious lexical tokens.
        Protected-brand impersonation is therefore used as a deterministic
        safety layer. This remains URL-only and does not call external services.
        """
        if not brand_signals or brand_signals.get("officialDomainMatched") or not brand_signals.get("impersonationDetected"):
            return final_cls, final_probs, decision_source

        score = float(brand_signals.get("score", 0.0) or 0.0)
        risk = str(brand_signals.get("risk", "low")).lower()
        signals = set(brand_signals.get("signals", []) or [])
        protected_hit = bool(brand_signals.get("protectedEntityMatches"))

        strong_brand_signal = (
            protected_hit
            or score >= 4.0
            or risk in {"medium", "high", "critical"}
            or "protected_brand_on_unofficial_domain" in signals
            or "protected_acronym_extra_chars_or_typosquat" in signals
            or "levenshtein_brand_lookalike" in signals
        )
        if not strong_brand_signal:
            return final_cls, final_probs, decision_source

        # Use phishing as the safest subtype for brand/credential impersonation.
        if final_cls == "benign":
            adjusted = dict(final_probs)
            floor = 0.78 if (protected_hit or score >= 6.0 or risk == "high") else 0.62
            adjusted["benign"] = min(float(adjusted.get("benign", 0.0)), 1.0 - floor)
            adjusted["phishing"] = max(float(adjusted.get("phishing", 0.0)), floor)
            total = sum(max(float(v), 0.0) for v in adjusted.values()) or 1.0
            adjusted = {k: max(float(v), 0.0) / total for k, v in adjusted.items()}
            return "phishing", adjusted, decision_source + "+brand_impersonation_override"

        # If model already predicts malicious, keep subtype but mark that brand layer supported risk.
        return final_cls, final_probs, decision_source + "+brand_impersonation_signal"

    def predict(self, decoded_url: str, locale: str, app_version: str | None, db: Session) -> PredictionResponse:
        t_total = time.perf_counter()
        timing_ms: Dict[str, float] = {}

        t = time.perf_counter()
        normalized, host, reg_domain, tld = normalize_and_validate_url(decoded_url)
        timing_ms["normalization_validation"] = self._elapsed_ms(t)

        t = time.perf_counter()
        # Graph projection is performed inside feature extraction for this pipeline.
        X, full_features = self.extractor.extract_all(normalized, reg_domain, tld)
        timing_ms["feature_extraction"] = self._elapsed_ms(t)

        t = time.perf_counter()
        brand_signals = self.brand_service.analyze(normalized)
        timing_ms["brand_analysis"] = self._elapsed_ms(t)

        t = time.perf_counter()
        Xp = self.artifacts.preprocessor.transform(X)
        timing_ms["preprocessing_vectorization"] = self._elapsed_ms(t)

        t = time.perf_counter()
        hist_proba_arr = self.artifacts.model.predict_proba(Xp)[0]
        timing_ms["histgb_inference"] = self._elapsed_ms(t)

        decision_ms = 0.0
        t = time.perf_counter()
        hist_probs = self._proba_map(hist_proba_arr)
        hist_cls, hist_conf, hist_margin = self._confidence_margin(hist_probs)
        hist_risk = self._risk_score(hist_probs)
        should_transform, uncertainty = self._needs_transformer(hist_conf, hist_margin, hist_risk, full_features, brand_signals)
        decision_ms += self._elapsed_ms(t)

        trans_probs = None
        if should_transform:
            t = time.perf_counter()
            trans_probs, transformer_timing = self.transformer.predict_proba_with_timing(normalized)
            timing_ms.update(transformer_timing)
            timing_ms["fallback_inference"] = self._elapsed_ms(t)

        t = time.perf_counter()
        final_cls, final_probs, decision_source, transformer_used = self._resolve(hist_probs, trans_probs, brand_signals)
        final_cls, final_probs, decision_source = self._apply_brand_override(final_cls, final_probs, decision_source, brand_signals)
        risk = self._risk_score(final_probs)
        risk_level = self._risk_level(risk)
        action = self._action(risk)
        decision_ms += self._elapsed_ms(t)
        timing_ms["decision_fusion"] = round(decision_ms, 4)

        t = time.perf_counter()
        top_features = self.explainer.top_features(full_features, self.artifacts.features, limit=8)
        explanation = self.explainer.explain(final_cls, risk_level, decision_source, top_features, transformer_used, brand_signals)
        timing_ms["explanation_generation"] = self._elapsed_ms(t)

        prediction_id = str(uuid.uuid4())
        latency_ms_for_log = int((time.perf_counter() - t_total) * 1000)

        t = time.perf_counter()
        db.add(PredictionLog(
            prediction_id=prediction_id,
            url_hash=hash_url(normalized),
            masked_url=mask_url(normalized),
            domain=reg_domain,
            predicted_class=final_cls,
            risk_score=float(risk),
            risk_level=risk_level,
            recommended_action=action,
            decision_source=decision_source,
            model_version=self.artifacts.model_version,
            feature_schema_version=self.artifacts.feature_schema_version,
            latency_ms=latency_ms_for_log,
            app_version=app_version,
            locale=locale,
        ))
        db.commit()
        timing_ms["logging_persistence"] = self._elapsed_ms(t)
        timing_ms["total_backend"] = self._elapsed_ms(t_total)
        latency_ms = int(round(timing_ms["total_backend"]))

        return PredictionResponse(
            predictionId=prediction_id,
            normalizedUrl=normalized,
            maskedUrl=mask_url(normalized),
            domain=reg_domain,
            predictedClass=final_cls,
            riskScore=round(float(risk), 6),
            riskLevel=risk_level,
            recommendedAction=action,
            threshold=self.artifacts.threshold_value,
            probabilities={k: round(float(v), 6) for k, v in final_probs.items()},
            explanation=explanation,
            topFeatures=top_features,
            modelVersion=self.artifacts.model_version,
            featureSchemaVersion=self.artifacts.feature_schema_version,
            latencyMs=latency_ms,
            timingMs=timing_ms,
            urlOnly=True,
            decisionSource=decision_source,
            primaryModel=ModelDecision(name="HistGB", used=True, confidence=hist_conf, margin=hist_margin, probabilities={k: round(float(v), 6) for k, v in hist_probs.items()}),
            fallbackModel=ModelDecision(name="URL-Transformer", used=bool(transformer_used), confidence=self._confidence_margin(trans_probs)[1] if trans_probs else None, margin=self._confidence_margin(trans_probs)[2] if trans_probs else None, probabilities={k: round(float(v), 6) for k, v in (trans_probs or {}).items()}) if (should_transform or transformer_used) else None,
            uncertainty=uncertainty,
            brandSignals=brand_signals,
        )
