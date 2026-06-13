from app.schemas.prediction import TopFeature
from app.services.explanation_service import ExplanationService
from app.services.feature_extractor import feature_display_name_tr


def test_feature_display_name_tr_localizes_known_and_fallback_features():
    assert feature_display_name_tr("url_len") == "URL uzunluğu"
    assert feature_display_name_tr("num_phishing_keywords") == "kimlik avı anahtar kelime sayısı"


def test_top_features_include_localized_display_names():
    service = ExplanationService(
        templates={},
        feature_importance={"items": [{"feature": "url_len", "importance": 1.0}]},
    )

    features = service.top_features({"url_len": 2.0}, ["url_len"], limit=1)

    assert features[0].displayName == "Url len"
    assert features[0].displayNameLocalized["en"] == "Url len"
    assert features[0].displayNameLocalized["tr"] == "URL uzunluğu"


def test_explain_uses_localized_feature_group_labels():
    service = ExplanationService(templates={})
    top_features = [
        TopFeature(
            name="url_len",
            displayName="Url len",
            displayNameLocalized={"en": "Url len", "tr": "URL uzunluğu"},
            group="lexical_structural",
            value=2.0,
            impact=0.5,
            direction="malicious",
        )
    ]

    explanation = service.explain(
        "phishing",
        "high",
        "histgb_confident_or_transformer_unavailable",
        top_features,
        transformer_used=False,
    )

    assert "lexical_structural" not in explanation["tr"]
    assert "sözcüksel / yapısal" in explanation["tr"]