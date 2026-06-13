import pytest
from app.services.url_security import normalize_and_validate_url
from app.core.exceptions import InvalidUrlError


def test_valid_url():
    normalized, host, reg_domain, tld = normalize_and_validate_url("https://example.com/login?a=1")
    assert normalized.startswith("https://")
    assert host == "example.com"


def test_missing_scheme_defaults_https():
    normalized, *_ = normalize_and_validate_url("example.com/path")
    assert normalized.startswith("https://")


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///etc/passwd", "mailto:a@b.com", "data:text/html,hi", "ftp://example.com/a"])
def test_forbidden_schemes(url):
    with pytest.raises(InvalidUrlError):
        normalize_and_validate_url(url)
