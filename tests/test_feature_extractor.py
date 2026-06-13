from app.services.feature_extractor import FeatureExtractor


def test_feature_extractor_schema_order():
    features = ["url_len", "has_query", "rare_token_count", "non_existing_feature"]
    bundle = {"token_total_count": {}, "token_domain_count": {}, "token_malicious_count": {}, "token_benign_count": {}, "tld_token_pairs": {}, "domain_family": {}}
    fx = FeatureExtractor(features, bundle)
    df, full = fx.extract_all("https://example.com/login?a=1", "example.com", "com")
    assert list(df.columns) == features
    assert df.shape == (1, 4)
    assert df.loc[0, "non_existing_feature"] == 0


def test_feature_extractor_handles_empty_suffix_for_suspicious_brand_url():
    features = ["brand_tld_mismatch", "contains_brand", "brand_plus_keyword"]
    bundle = {"token_total_count": {}, "token_domain_count": {}, "token_malicious_count": {}, "token_benign_count": {}, "tld_token_pairs": {}, "domain_family": {}}
    fx = FeatureExtractor(features, bundle)
    df, full = fx.extract_all(
        "https://ziraat-bankasi-guvenli-giris.example/login",
        "ziraat-bankasi-guvenli-giris.example",
        "",
    )
    assert df.shape == (1, 3)
    assert int(df.loc[0, "brand_tld_mismatch"]) == 0
    assert "brand_tld_mismatch" in full
