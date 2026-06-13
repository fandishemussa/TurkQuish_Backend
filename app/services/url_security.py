from urllib.parse import urlparse, urlunparse
import re
import tldextract
from app.core.config import get_settings
from app.core.exceptions import InvalidUrlError

settings = get_settings()
_tld = tldextract.TLDExtract(suffix_list_urls=())

FORBIDDEN_SCHEMES = {"javascript", "data", "file", "mailto", "tel", "sms", "ftp", "intent"}


def normalize_and_validate_url(raw: str) -> tuple[str, str, str, str]:
    if raw is None:
        raise InvalidUrlError("QR payload is empty.")

    url = str(raw).strip()
    if not url:
        raise InvalidUrlError("QR payload is empty.")
    if len(url) > settings.max_url_length:
        raise InvalidUrlError("URL is too long.")

    lower = url.lower()
    scheme_match = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*):", lower)
    if scheme_match:
        scheme = scheme_match.group(1)
        if scheme in FORBIDDEN_SCHEMES or scheme not in {"http", "https"}:
            raise InvalidUrlError("Only http:// and https:// URLs are supported.")
    else:
        # QR often omits the scheme. Treat as https for normalization.
        url = "https://" + url

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise InvalidUrlError("Only http:// and https:// URLs are supported.")
    if not parsed.netloc:
        raise InvalidUrlError("URL host is missing.")
    if any(x in parsed.netloc for x in [" ", "\t", "\n"]):
        raise InvalidUrlError("URL host is malformed.")

    # Trigger port parsing error if invalid port exists.
    try:
        _ = parsed.port
    except ValueError:
        raise InvalidUrlError("URL port is invalid.")

    hostname = (parsed.hostname or "").lower().strip(".")
    if not hostname:
        raise InvalidUrlError("URL host is missing.")

    normalized_netloc = hostname
    if parsed.port:
        normalized_netloc = f"{normalized_netloc}:{parsed.port}"

    path = parsed.path or "/"
    normalized = urlunparse((parsed.scheme.lower(), normalized_netloc, path, "", parsed.query, ""))

    ext = _tld(normalized)
    reg_domain = ".".join([p for p in [ext.domain, ext.suffix] if p]) or hostname
    tld = ext.suffix.split(".")[-1] if ext.suffix else ""
    return normalized, hostname, reg_domain, tld
