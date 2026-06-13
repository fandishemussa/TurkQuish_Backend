from __future__ import annotations
from typing import Dict, List

from app.schemas.prediction import TopFeature
from app.services.feature_extractor import feature_display_name, feature_display_names, feature_group


FEATURE_GROUP_LABELS = {
    'lexical_structural': {'en': 'lexical / structural', 'tr': 'sözcüksel / yapısal'},
    'lexical_keyword': {'en': 'lexical / keyword', 'tr': 'sözcüksel / anahtar kelime'},
    'turkish_linguistic': {'en': 'Turkish linguistic', 'tr': 'Türkçe dilsel'},
    'adversarial_brand': {'en': 'adversarial / brand', 'tr': 'yanıltıcı / marka'},
    'graph_infrastructure': {'en': 'graph infrastructure', 'tr': 'graf altyapısı'},
    'other': {'en': 'other', 'tr': 'diğer'},
}


def feature_group_label(group: str, locale: str) -> str:
    labels = FEATURE_GROUP_LABELS.get(group, FEATURE_GROUP_LABELS['other'])
    return labels.get(locale, labels['en'])


class ExplanationService:
    def __init__(self, templates: dict, feature_importance: dict | None = None):
        self.templates = templates or {}
        self.feature_importance = feature_importance or {}
        self.importance_map = {}
        for item in self.feature_importance.get("items", []):
            self.importance_map[item.get("feature")] = float(item.get("importance", 0.0))

    def top_features(self, full_features: Dict[str, float], schema_features: list[str], limit: int = 8) -> List[TopFeature]:
        items = []
        for name in schema_features:
            value = full_features.get(name, 0.0)
            try:
                abs_value = abs(float(value))
            except Exception:
                abs_value = 0.0
            importance = self.importance_map.get(name, 0.0)
            score = importance * (1.0 + abs_value)
            if score <= 0 and abs_value > 0:
                score = min(abs_value / 100.0, 1.0)
            if score > 0:
                items.append((score, name, value))
        items.sort(reverse=True, key=lambda x: x[0])
        out = []
        for score, name, value in items[:limit]:
            direction = "malicious" if float(value or 0) > 0 else "benign"
            out.append(TopFeature(
                name=name,
                displayName=feature_display_name(name),
                displayNameLocalized=feature_display_names(name),
                group=feature_group(name),
                value=float(value) if isinstance(value, (int, float)) else str(value),
                impact=round(float(score), 6),
                direction=direction,
            ))
        return out

    def explain(self, predicted_class: str, risk_level: str, decision_source: str, top_features: List[TopFeature], transformer_used: bool, brand_signals: dict | None = None) -> Dict[str, str]:
        class_templates = self.templates.get("class_templates", {})
        risk_templates = self.templates.get("risk_templates", {})
        base = class_templates.get(predicted_class, {})
        risk = risk_templates.get(risk_level, {})
        en = base.get("en", f"The URL was classified as {predicted_class}.")
        tr = base.get("tr", f"URL {predicted_class} olarak sınıflandırıldı.")
        if top_features:
            groups = sorted(set(f.group for f in top_features[:4]))
            en_groups = [feature_group_label(group, "en") for group in groups]
            tr_groups = [feature_group_label(group, "tr") for group in groups]
            en += " Main contributing feature groups: " + ", ".join(en_groups) + "."
            tr += " Başlıca katkı sağlayan özellik grupları: " + ", ".join(tr_groups) + "."
        if transformer_used:
            en += " The engineered-feature model was uncertain, so the URL-Transformer was used as a secondary raw-character check."
            tr += " Özellik tabanlı model kararsız olduğu için URL-Transformer ham karakter düzeyinde ikinci kontrol olarak kullanıldı."
        if brand_signals and brand_signals.get("impersonationDetected"):
            b_exp = brand_signals.get("explanation", {})
            en += " Brand impersonation check: " + b_exp.get("en", "A suspicious brand impersonation signal was detected.")
            tr += " Marka taklidi kontrolü: " + b_exp.get("tr", "Şüpheli bir marka taklidi sinyali tespit edildi.")
        if risk:
            en += " " + risk.get("en", "")
            tr += " " + risk.get("tr", "")
        return {"en": en.strip(), "tr": tr.strip()}
