from app.services.inference_service import InferenceService


ALL_CLASSES = ["benign", "phishing", "malware", "scam", "other_malicious"]


def _probs(**values):
    return {key: float(values.get(key, 0.0)) for key in ALL_CLASSES}


def test_trusted_official_domain_uses_strong_benign_transformer_over_weak_histgb():
    svc = InferenceService.__new__(InferenceService)
    hist = _probs(benign=0.40, phishing=0.60)
    trans = _probs(benign=0.999, phishing=0.001)

    label, _, source, used = svc._resolve(
        hist,
        trans,
        {"officialDomainMatched": True, "impersonationDetected": False},
    )

    assert used is True
    assert label == "benign"
    assert source == "trusted_official_domain_benign_model_priority"


def test_strong_transformer_overrides_weak_histgb_when_no_brand_impersonation():
    svc = InferenceService.__new__(InferenceService)
    hist = _probs(benign=0.40, phishing=0.60)
    trans = _probs(benign=0.999, phishing=0.001)

    label, _, source, used = svc._resolve(
        hist,
        trans,
        {"officialDomainMatched": False, "impersonationDetected": False},
    )

    assert used is True
    assert label == "benign"
    assert source == "urltransformer_high_confidence_over_weak_histgb"


def test_brand_override_does_not_raise_official_domain_to_phishing():
    hist = _probs(benign=0.96, phishing=0.04)

    label, probs, source = InferenceService._apply_brand_override(
        "benign",
        hist,
        "histgb_urltransformer_agreement",
        {
            "officialDomainMatched": True,
            "impersonationDetected": True,
            "score": 5.0,
            "risk": "medium",
            "signals": ["brand_not_registered_domain"],
            "protectedEntityMatches": [],
        },
    )

    assert label == "benign"
    assert probs == hist
    assert source == "histgb_urltransformer_agreement"


class _AvailableTransformer:
    available = True


def test_primary_confidence_at_or_below_089_activates_transformer():
    svc = InferenceService.__new__(InferenceService)
    svc.transformer = _AvailableTransformer()

    use, uncertainty = svc._needs_transformer(
        hist_conf=0.89,
        hist_margin=0.50,
        hist_risk=0.20,
        full_features={},
        brand_signals=None,
    )

    assert use is True
    assert uncertainty["lowConfidence"] is True


def test_primary_confidence_above_089_does_not_activate_by_confidence_alone():
    svc = InferenceService.__new__(InferenceService)
    svc.transformer = _AvailableTransformer()

    use, uncertainty = svc._needs_transformer(
        hist_conf=0.90,
        hist_margin=0.50,
        hist_risk=0.20,
        full_features={},
        brand_signals=None,
    )

    assert use is False
    assert uncertainty["lowConfidence"] is False


def test_brand_impersonation_blocks_benign_transformer_override():
    svc = InferenceService.__new__(InferenceService)
    hist = _probs(benign=0.40, phishing=0.60)
    trans = _probs(benign=0.999, phishing=0.001)

    label, _, source, used = svc._resolve(
        hist,
        trans,
        {"officialDomainMatched": False, "impersonationDetected": True},
    )

    assert used is True
    assert label == "phishing"
    assert source == "histgb_disagreed_safer_malicious"


def test_strong_malicious_transformer_overrides_weak_benign_histgb():
    svc = InferenceService.__new__(InferenceService)
    hist = _probs(benign=0.70, phishing=0.30)
    trans = _probs(benign=0.001, phishing=0.999)

    label, _, source, used = svc._resolve(
        hist,
        trans,
        {"officialDomainMatched": False, "impersonationDetected": False},
    )

    assert used is True
    assert label == "phishing"
    assert source == "urltransformer_high_confidence_over_weak_histgb"


def test_prediction_response_accepts_timing_ms():
    from app.schemas.prediction import ModelDecision, PredictionResponse

    response = PredictionResponse(
        predictionId="p1",
        normalizedUrl="https://example.com",
        maskedUrl="https://example.com",
        domain="example.com",
        predictedClass="benign",
        riskScore=0.1,
        riskLevel="low",
        recommendedAction="proceed",
        threshold=0.5,
        probabilities={"benign": 0.9, "phishing": 0.1},
        explanation={"en": "ok", "tr": "ok"},
        topFeatures=[],
        modelVersion="m",
        featureSchemaVersion="s",
        latencyMs=12,
        timingMs={"total_backend": 12.3, "histgb_inference": 0.4},
        decisionSource="histgb_confident_or_transformer_unavailable",
        primaryModel=ModelDecision(name="HistGB"),
    )

    assert response.timingMs["total_backend"] == 12.3
    assert response.timingMs["histgb_inference"] == 0.4
