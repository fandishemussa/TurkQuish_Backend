import hashlib
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from app.core.config import get_settings

settings = get_settings()


def hash_url(url: str) -> str:
    salt = settings.url_hash_salt.encode("utf-8")
    return hashlib.sha256(salt + url.encode("utf-8")).hexdigest()


def mask_url(url: str) -> str:
    try:
        parts = urlsplit(url)
        if not parts.query:
            return url
        keys = [k for k, _ in parse_qsl(parts.query, keep_blank_values=True)]
        masked_query = urlencode([(k, "***") for k in keys[:8]])
        if len(keys) > 8:
            masked_query += "&...=***"
        return urlunsplit((parts.scheme, parts.netloc, parts.path, masked_query, ""))
    except Exception:
        return url[:120] + ("..." if len(url) > 120 else "")
