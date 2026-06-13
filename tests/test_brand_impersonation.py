from app.services.brand_impersonation_service import BrandImpersonationService


def test_levenshtein_brand_lookalike_detected():
    svc = BrandImpersonationService(brands=["garanti", "ziraat", "paypal"])
    res = svc.analyze("https://garantii-login.xyz/hesap-dogrula")
    assert res["impersonationDetected"] is True
    assert "levenshtein_brand_lookalike" in res["signals"]
    assert res["similarBrands"][0]["brand"] == "garanti"


def test_brand_in_path_outside_domain_detected():
    svc = BrandImpersonationService(brands=["paypal"])
    res = svc.analyze("https://secure-check.xyz/paypal/verify")
    assert res["impersonationDetected"] is True
    assert "brand_not_registered_domain" in res["signals"]


def test_ktun_extra_prefix_edu_tr_detected():
    from app.services.brand_impersonation_service import BrandImpersonationService
    s = BrandImpersonationService()
    r = s.analyze("https://www.kkktun.edu.tr")
    assert r["impersonationDetected"] is True
    assert r["risk"] in {"medium", "high"}
    assert "protected_acronym_extra_chars_or_typosquat" in r["signals"]
    assert r["protectedEntityMatches"]


def test_official_ktun_not_flagged():
    from app.services.brand_impersonation_service import BrandImpersonationService
    s = BrandImpersonationService()
    r = s.analyze("https://www.ktun.edu.tr")
    assert r["impersonationDetected"] is False



def test_ktun_extra_prefix_is_detected():
    from app.services.brand_impersonation_service import BrandImpersonationService
    s = BrandImpersonationService()
    out = s.analyze("https://www.kkktun.edu.tr")
    assert out["impersonationDetected"] is True
    assert out["risk"] in {"medium", "high"}
    assert "protected_acronym_extra_chars_or_typosquat" in out["signals"]
    assert out["protectedEntityMatches"]


def test_official_ktun_is_not_flagged():
    from app.services.brand_impersonation_service import BrandImpersonationService
    s = BrandImpersonationService()
    out = s.analyze("https://www.ktun.edu.tr")
    assert out["impersonationDetected"] is False


def test_turkish_bank_protected_brand_login_is_detected():
    from app.services.brand_impersonation_service import BrandImpersonationService
    s = BrandImpersonationService()
    out = s.analyze("https://akbank-login.xyz/secure")
    assert out["impersonationDetected"] is True
    assert "protected_brand_on_unofficial_domain" in out["signals"] or "brand_with_suspicious_tld" in out["signals"]


def test_official_akbank_is_not_flagged():
    from app.services.brand_impersonation_service import BrandImpersonationService
    s = BrandImpersonationService()
    out = s.analyze("https://www.akbank.com")
    assert out["impersonationDetected"] is False


def test_turkcell_invoice_lookalike_is_detected():
    from app.services.brand_impersonation_service import BrandImpersonationService
    s = BrandImpersonationService()
    out = s.analyze("https://turkcell-fatura.xyz/odeme")
    assert out["impersonationDetected"] is True
    assert out["score"] >= 3.0


def test_official_service_subdomains_are_trusted_not_impersonation():
    s = BrandImpersonationService()
    for url in ["https://www.mebbis.meb.gov.tr", "https://www.webtapu.tkgm.gov.tr"]:
        out = s.analyze(url)
        assert out["officialDomainMatched"] is True
        assert out["impersonationDetected"] is False
        assert out["risk"] == "low"
        assert "brand_not_registered_domain" not in out["signals"]
        assert "brand_in_subdomain" not in out["signals"]
