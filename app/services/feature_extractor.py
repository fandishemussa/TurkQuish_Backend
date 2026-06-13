from __future__ import annotations

import base64
import math
import re
from collections import Counter
from urllib.parse import urlparse, unquote

import numpy as np
import pandas as pd
import tldextract

try:
    from app.resources.classification_keywords import PHISHING_KEYWORDS, MALWARE_KEYWORDS, SCAM_KEYWORDS
except Exception:  # pragma: no cover
    PHISHING_KEYWORDS = ["login", "verify", "account", "password", "banking", "paypal"]
    MALWARE_KEYWORDS = [".exe", ".msi", ".apk", "payload", "trojan", "malware"]
    SCAM_KEYWORDS = ["casino", "bitcoin", "giveaway", "lottery", "prize"]

try:
    from app.resources.turkish_lexicons import (
        TR_PHISHING, TR_SCAM, TR_MALWARE, TR_URGENCY, TR_BRANDS,
        TR_TRANSLIT, TR_BRANDS_WITH_TRCHARS,
    )
except Exception:  # pragma: no cover
    TR_PHISHING, TR_SCAM, TR_MALWARE, TR_URGENCY = {}, {}, {}, {}
    TR_BRANDS, TR_BRANDS_WITH_TRCHARS = [], []
    TR_TRANSLIT = {"ÅŸ": "s", "ÄŸ": "g", "Ä±": "i", "Ã¶": "o", "Ã¼": "u", "Ã§": "c"}

_tld = tldextract.TLDExtract(suffix_list_urls=())

KEEP_SUBSTRING_SHORT = {"iade", "onay", "iban", "2fa", "worm", "mhrs", "mlm", "odul", "otp", "apk", "sgk"}
LETTER = r"[a-z\u00e7\u011f\u0131\u00f6\u015f\u00fc]"


def compile_keywords(keywords, short_len: int = 5):
    parts = []
    if isinstance(keywords, dict):
        keywords = list(keywords.keys())
    for kw in keywords:
        kw = str(kw)
        if not kw:
            continue
        if any(c in kw for c in r"\.^$*+?{}[]|()/"):
            parts.append(kw)
        elif " " in kw or "-" in kw:
            parts.append(re.escape(kw))
        elif len(kw) < short_len and kw not in KEEP_SUBSTRING_SHORT:
            parts.append(r"(?<!" + LETTER + r")" + re.escape(kw) + r"(?!" + LETTER + r")")
        else:
            parts.append(re.escape(kw))
    if not parts:
        return re.compile(r"a^", re.IGNORECASE)
    return re.compile("|".join(parts), re.IGNORECASE)


PATTERN_PHISHING_FULL = compile_keywords(PHISHING_KEYWORDS)
PATTERN_MALWARE_FULL = compile_keywords(MALWARE_KEYWORDS)
PATTERN_SCAM_FULL = compile_keywords(SCAM_KEYWORDS)
PATTERN_TURKISH_FULL = compile_keywords(TR_PHISHING)
PATTERN_TR_SCAM = compile_keywords(TR_SCAM)
PATTERN_TR_MALWARE = compile_keywords(TR_MALWARE)
PATTERN_TR_URGENCY = compile_keywords(TR_URGENCY)
PHISHING_KW_COMPACT = ["login", "signin", "verify", "secure", "account", "update", "confirm", "banking", "paypal", "password", "credential", "webscr", "submit", "checkout", "redirect"]
PATTERN_PHISHING_EN = compile_keywords(PHISHING_KW_COMPACT)

SUSPICIOUS_TLDS = {"xyz", "top", "club", "online", "site", "website", "space", "info", "click", "link", "live", "stream", "work", "pw", "tk", "ml", "ga", "cf", "lat", "cfd", "sbs"}
FREE_HOSTING = {"github.io", "netlify.app", "vercel.app", "glitch.me", "000webhostapp.com", "weebly.com", "wixsite.com", "blogspot.com", "wordpress.com", "pages.dev", "workers.dev", "duckdns.org", "hopto.org", "zapto.org", "no-ip.com"}
GLOBAL_BRANDS = [
    "microsoft", "google", "apple", "amazon", "facebook", "instagram", "whatsapp", "twitter", "tiktok", "linkedin", "office365", "outlook", "icloud", "dropbox", "adobe", "zoom", "netflix", "spotify", "youtube", "paypal", "binance", "coinbase", "metamask", "trustwallet", "dhl", "fedex", "ups", "ebay", "booking", "airbnb", "github", "openai", "chatgpt", "gmail", "cloudflare", "docker", "visa", "mastercard", "nike", "adidas", "steam", "xbox",
]
ALL_BRANDS = sorted(set(list(TR_BRANDS) + GLOBAL_BRANDS), key=len, reverse=True)
TR_CHARS = set("Ã§ÄŸÄ±Ã¶ÅŸÃ¼Ã‡ÄžÄ°Ã–ÅžÃœ")
VOWELS = set("aeÄ±ioÃ¶uÃ¼")
FRONT = set("eiÃ¶Ã¼")
BACK = set("aÄ±ou")

TURKISH_STOPWORDS = {"ve", "veya", "ile", "icin", "iÃ§in", "bir", "bu", "da", "de", "mi", "mu", "mÄ±", "mÃ¼", "en", "Ã§ok", "cok", "yeni", "giris", "giriÅŸ"}
TR_SUFFIXES = ["lar", "ler", "lik", "lÄ±k", "luk", "lÃ¼k", "ci", "cÄ±", "cu", "cÃ¼", "siz", "sÄ±z", "dan", "den", "tan", "ten", "dir", "dÄ±r", "dur", "dÃ¼r", "im", "Ä±m", "um", "Ã¼m"]
TR_BANK_TERMS = {"banka", "bankasi", "bankasÄ±", "kredi", "kart", "iban", "eft", "havale", "odeme", "Ã¶deme", "hesap"}
TR_GOV_TERMS = {"edevlet", "e-devlet", "sgk", "mhrs", "vergi", "nvi", "uyap", "tckimlik", "kimlik", "randevu"}
TR_ECOM_TERMS = {"kargo", "siparis", "sipariÅŸ", "teslimat", "indirim", "kampanya", "kupon", "trendyol", "hepsiburada"}
TR_TELECOM_TERMS = {"turkcell", "vodafone", "turktelekom", "tÃ¼rk telekom", "ttnet", "superonline"}
COMMON_TR_BIGRAMS = {"ar", "la", "le", "in", "en", "er", "an", "da", "de", "li", "lik", "ci", "si", "sa", "ma", "me", "ka", "ya", "ye"}
COMMON_EN_BIGRAMS = {"th", "he", "in", "er", "an", "re", "on", "at", "en", "nd", "ti", "es", "or", "te", "of", "ed"}


def safe_parse(url: str):
    try:
        u = str(url).strip()
        if not u.startswith(("http://", "https://")):
            u = "http://" + u
        p = urlparse(u)
        _ = p.port
        return p
    except Exception:
        return None


def entropy(s: str) -> float:
    s = str(s)
    if not s:
        return 0.0
    freq = Counter(s)
    n = len(s)
    return float(-sum((c / n) * math.log2(c / n) for c in freq.values()))


def tokens_from_url(url: str) -> list[str]:
    return [x for x in re.split(r"[^a-zA-Z0-9Ã§ÄŸÄ±Ã¶ÅŸÃ¼Ã‡ÄžÄ°Ã–ÅžÃœ]+", str(url).lower()) if x]


def levenshtein(a: str, b: str, cap: int = 4) -> int:
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        best = i
        for j, cb in enumerate(b, 1):
            val = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            cur.append(val)
            best = min(best, val)
        if best > cap:
            return cap + 1
        prev = cur
    return prev[-1]


def translit_fold(s: str) -> str:
    return "".join(TR_TRANSLIT.get(c, TR_TRANSLIT.get(c.lower(), c.lower())) for c in str(s))


def vowel_harmony_score(token: str) -> float:
    v = [c for c in str(token).lower() if c in VOWELS]
    if len(v) < 2:
        return 0.0
    front_count = sum(c in FRONT for c in v)
    back_count = sum(c in BACK for c in v)
    return max(front_count, back_count) / len(v)


def is_mostly_consonants(s: str) -> int:
    letters = [c for c in str(s).lower() if c.isalpha()]
    if len(letters) < 6:
        return 0
    vowels = sum(c in VOWELS for c in letters)
    return int((len(letters) - vowels) / max(len(letters), 1) > 0.75)


def extract_lexical(url: str) -> dict[str, float]:
    u = str(url).strip()
    ext = _tld(u if u.startswith("http") else "http://" + u)
    parsed = safe_parse(u)
    u_lower = u.lower()
    subdomain = ext.subdomain or ""
    domain = ext.domain or ""
    suffix = ext.suffix or ""
    path = parsed.path if parsed else ""
    query = parsed.query if parsed else ""
    netloc = parsed.netloc if parsed else ""
    n = max(len(u), 1)
    f: dict[str, float] = {}
    f["url_len"] = len(u)
    f["num_dots"] = u.count(".")
    f["num_slashes"] = u.count("/")
    f["num_digits"] = sum(c.isdigit() for c in u)
    f["num_specials"] = sum(not c.isalnum() and c not in "://.-_" for c in u)
    f["subdomain_len"] = len(subdomain)
    f["domain_len"] = len(domain)
    f["tld_len"] = len(suffix)
    f["is_tr_domain"] = int("tr" in suffix.lower().split("."))
    f["digit_ratio"] = sum(c.isdigit() for c in u) / n
    f["alpha_ratio"] = sum(c.isalpha() for c in u) / n
    f["special_ratio"] = f["num_specials"] / n
    parts = subdomain.split(".") if subdomain else []
    f["num_subdomains"] = len(parts) if subdomain else 0
    f["has_www"] = int(subdomain.lower() == "www" or subdomain.lower().startswith("www."))
    f["subdomain_digits"] = sum(c.isdigit() for c in subdomain)
    path_parts = [p for p in path.split("/") if p]
    f["path_len"] = len(path)
    f["path_depth"] = len(path_parts)
    f["path_digits"] = sum(c.isdigit() for c in path)
    f["has_php"] = int(".php" in path.lower())
    f["has_exe"] = int(any(x in path.lower() for x in [".exe", ".zip", ".bat", ".msi", ".apk", ".jar"]))
    f["has_query"] = int(len(query) > 0)
    f["query_len"] = len(query)
    f["num_params"] = len(query.split("&")) if query else 0
    f["num_hyphens"] = u.count("-")
    f["num_underscores"] = u.count("_")
    f["num_at_signs"] = u.count("@")
    f["num_ampersands"] = u.count("&")
    f["num_equals"] = u.count("=")
    f["num_percent"] = u.count("%")
    f["has_at_in_url"] = int("@" in u)
    try:
        port = parsed.port if parsed else None
    except Exception:
        port = None
    f["has_port"] = int(bool(port))
    f["has_ip"] = int(bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", netloc.split(":")[0])))
    f["is_https"] = int(u_lower.startswith("https"))
    f["has_double_slash"] = int("//" in path)
    f["url_entropy"] = round(entropy(u), 4)
    f["domain_entropy"] = round(entropy(domain), 4)
    f["path_entropy"] = round(entropy(path), 4)
    f["has_repeated_chars"] = int(bool(re.search(r"(.)\1{3,}", u)))
    f["has_hex_encoding"] = int("%2" in u_lower or "%3" in u_lower)
    f["num_encoded_chars"] = len(re.findall(r"%[0-9a-fA-F]{2}", u))
    f["has_double_dot"] = int(".." in u)
    tr_hits = PATTERN_TURKISH_FULL.findall(u_lower)
    ph_hits = PATTERN_PHISHING_EN.findall(u_lower)
    mw_hits = PATTERN_MALWARE_FULL.findall(u_lower)
    sc_hits = PATTERN_SCAM_FULL.findall(u_lower)
    f["has_turkish_keyword"] = int(bool(tr_hits))
    f["num_turkish_keywords"] = len(tr_hits)
    f["has_phishing_keyword"] = int(bool(ph_hits))
    f["num_phishing_keywords"] = len(ph_hits)
    f["has_malware_keyword"] = int(bool(mw_hits))
    f["num_malware_keywords"] = len(mw_hits)
    f["has_scam_keyword"] = int(bool(sc_hits))
    f["num_scam_keywords"] = len(sc_hits)
    f["domain_hyphen_count"] = domain.count("-")
    f["domain_digit_count"] = sum(c.isdigit() for c in domain)
    f["domain_has_number"] = int(any(c.isdigit() for c in domain))
    tld = suffix.split(".")[-1].lower() if suffix else ""
    f["is_suspicious_tld"] = int(tld in SUSPICIOUS_TLDS)
    host = ".".join([p for p in [subdomain, domain, suffix] if p]).lower()
    f["is_free_hosting"] = int(any(host.endswith(x) for x in FREE_HOSTING))
    f["url_len_bucket"] = int(np.digitize(len(u), [30, 60, 100, 150, 250]))
    toks = tokens_from_url(u)
    f["num_tokens"] = len(toks)
    f["max_token_len"] = max((len(t) for t in toks), default=0)
    f["mean_token_len"] = float(np.mean([len(t) for t in toks])) if toks else 0.0
    return f


def extract_adversarial(url: str) -> dict[str, float]:
    u = str(url).strip()
    ul = u.lower()
    p = safe_parse(u)
    ext = _tld(u if u.startswith("http") else "http://" + u)
    subdomain = ext.subdomain or ""
    domain = ext.domain or ""
    suffix = ext.suffix or ""
    host = ".".join([x for x in [subdomain, domain, suffix] if x]).lower()
    path = p.path.lower() if p else ""
    query = p.query.lower() if p else ""
    toks = tokens_from_url(ul)
    domain_tokens = tokens_from_url(domain)
    brands = [b for b in ALL_BRANDS if len(b) >= 2]
    mentioned = sorted({b for b in brands if b in ul})
    domain_brand = any(b in domain for b in mentioned)
    f: dict[str, float] = {}
    f["contains_brand"] = int(bool(mentioned))
    f["brand_in_subdomain"] = int(any(b in subdomain for b in mentioned))
    f["brand_in_path"] = int(any(b in path for b in mentioned))
    f["brand_not_in_domain"] = int(bool(mentioned) and not domain_brand)
    f["brand_tld_mismatch"] = int(bool(mentioned) and bool(suffix) and suffix not in {"com", "com.tr", "net", "org", "org.tr", "gov.tr", "edu.tr"})
    f["num_brands_mentioned"] = len(mentioned)
    f["brand_with_hyphen"] = int(any((b + "-") in ul or ("-" + b) in ul for b in mentioned))
    f["brand_plus_keyword"] = int(bool(mentioned) and bool(PATTERN_PHISHING_FULL.search(ul)))
    min_dist = 9
    for tok in domain_tokens + toks[:20]:
        if len(tok) < 4:
            continue
        for b in brands[:300]:
            if abs(len(tok) - len(b)) <= 2:
                min_dist = min(min_dist, levenshtein(tok, b, cap=3))
    f["min_brand_edit_dist"] = min_dist if min_dist != 9 else 9
    f["is_typo_squat"] = int(0 < f["min_brand_edit_dist"] <= 2 and len(domain) >= 4)
    f["has_char_substitution"] = int(bool(re.search(r"[0@1!3$5]", domain)))
    f["has_doubled_char"] = int(bool(re.search(r"([a-z])\1", domain)))
    f["brand_homoglyph"] = int(bool(re.search(r"[Ð°-ÑÐ-Ð¯Î±Î²Î¿ÏÎ½Ñ…Ñ]", u)))
    f["excessive_subdomains"] = int(len(subdomain.split(".")) >= 3 if subdomain else 0)
    f["tr_in_subdomain"] = int("tr" in subdomain.split(".") if subdomain else 0)
    f["com_in_subdomain"] = int("com" in subdomain.split(".") if subdomain else 0)
    f["brand_dot_in_subdomain"] = int(any((b + ".") in subdomain for b in mentioned))
    f["deep_subdomain_nesting"] = len(subdomain.split(".")) if subdomain else 0
    tld = suffix.split(".")[-1].lower() if suffix else ""
    f["susp_tld_with_brand"] = int(tld in SUSPICIOUS_TLDS and bool(mentioned))
    f["susp_tld_with_keyword"] = int(tld in SUSPICIOUS_TLDS and bool(PATTERN_PHISHING_FULL.search(ul)))
    f["short_domain_susp_tld"] = int(len(domain) <= 6 and tld in SUSPICIOUS_TLDS)
    f["numeric_with_susp_tld"] = int(any(c.isdigit() for c in domain) and tld in SUSPICIOUS_TLDS)
    f["pct_encoded_ratio"] = len(re.findall(r"%[0-9a-fA-F]{2}", u)) / max(len(u), 1)
    f["has_unicode_escape"] = int("\\u" in u or "%u" in ul)
    f["has_punycode"] = int("xn--" in host)
    f["hex_in_domain"] = int(bool(re.search(r"[a-f0-9]{16,}", domain)))
    f["excessive_hyphens"] = int(domain.count("-") >= 3)
    f["random_looking_domain"] = int(entropy(domain) > 3.4 and len(domain) >= 10)
    f["consonant_heavy_domain"] = is_mostly_consonants(domain)
    f["long_random_path"] = int(len(path) > 60 and entropy(path) > 4.0)
    segments = [x for x in re.split(r"[/._\-]", path) if x]
    f["hash_like_segment"] = int(any(re.fullmatch(r"[a-f0-9]{16,}", x) for x in segments))
    def is_b64(x):
        if len(x) < 16 or len(x) % 4 != 0:
            return False
        try:
            base64.b64decode(x + "===", validate=False)
            return bool(re.fullmatch(r"[A-Za-z0-9+/=_-]+", x))
        except Exception:
            return False
    f["base64_like_segment"] = int(any(is_b64(x) for x in segments))
    f["many_path_dirs"] = int(path.count("/") >= 5)
    f["suspicious_file_in_path"] = int(any(path.endswith(x) or x in path for x in [".exe", ".scr", ".apk", ".msi", ".jar", ".docm", ".xlsm", ".zip", ".rar"]))
    f["has_url_in_url"] = int("http%3a" in ul or "https%3a" in ul or "http://" in path or "https://" in path)
    f["has_redirect_param"] = int(bool(re.search(r"(redirect|redir|url|next|continue|return|target)=", query)))
    f["at_symbol_trick"] = int("@" in (p.netloc if p else u))
    f["double_protocol"] = int(ul.count("http://") + ul.count("https://") > 1)
    return f


def extract_turkish_linguistic(url: str) -> dict[str, float]:
    u = str(url)
    ul = u.lower()
    p = safe_parse(u)
    ext = _tld(u if u.startswith("http") else "http://" + u)
    domain = ext.domain or ""
    path = p.path if p else ""
    toks = tokens_from_url(ul)
    f: dict[str, float] = {}
    tr_count = sum(c in TR_CHARS for c in u)
    f["tr_char_count"] = tr_count
    f["tr_char_ratio"] = tr_count / max(len(u), 1)
    f["has_tr_char"] = int(tr_count > 0)
    f["tr_char_in_domain"] = int(any(c in TR_CHARS for c in domain))
    f["tr_char_in_path"] = int(any(c in TR_CHARS for c in path))
    f["distinct_tr_chars"] = len({c.lower() for c in u if c in TR_CHARS})
    stop_count = sum(t in TURKISH_STOPWORDS for t in toks)
    f["tr_stopword_count"] = stop_count
    f["tr_stopword_ratio"] = stop_count / max(len(toks), 1)
    suffix_count = sum(any(t.endswith(s) and len(t) > len(s) + 2 for s in TR_SUFFIXES) for t in toks)
    f["tr_suffix_count"] = suffix_count
    vh = [vowel_harmony_score(t) for t in toks if any(c in VOWELS for c in t)]
    f["vowel_harmony_score"] = float(np.mean(vh)) if vh else 0.0
    tr_like = sum((t in TURKISH_STOPWORDS) or any(t.endswith(s) for s in TR_SUFFIXES) or any(c in TR_CHARS for c in t) for t in toks)
    f["tr_token_ratio"] = tr_like / max(len(toks), 1)
    joined_alpha = "".join(c for c in ul if c.isalpha())
    bigrams = [joined_alpha[i : i + 2] for i in range(len(joined_alpha) - 1)]
    tr_b = sum(bg in COMMON_TR_BIGRAMS for bg in bigrams)
    en_b = sum(bg in COMMON_EN_BIGRAMS for bg in bigrams)
    f["tr_bigram_score"] = tr_b / max(len(bigrams), 1)
    f["tr_vs_en_bigram"] = (tr_b - en_b) / max(len(bigrams), 1)
    f["langid_tr_confidence"] = min(1.0, f["tr_token_ratio"] * 0.5 + f["tr_bigram_score"] * 2.0 + f["tr_char_ratio"] * 3.0)
    f["is_turkish_dominant"] = int(f["langid_tr_confidence"] >= 0.35)
    joined = " ".join(toks)
    f["has_tr_bank_term"] = int(any(t in joined for t in TR_BANK_TERMS))
    f["has_tr_gov_term"] = int(any(t in joined for t in TR_GOV_TERMS))
    f["has_tr_ecommerce_term"] = int(any(t in joined for t in TR_ECOM_TERMS))
    f["has_tr_telecom_term"] = int(any(t in joined for t in TR_TELECOM_TERMS))
    f["tr_sector_count"] = f["has_tr_bank_term"] + f["has_tr_gov_term"] + f["has_tr_ecommerce_term"] + f["has_tr_telecom_term"]
    return f


def lex_score(tokens: list[str], joined: str, lexicon: dict | list) -> float:
    if isinstance(lexicon, dict):
        return float(sum(w for term, w in lexicon.items() if term in tokens or str(term).replace("-", "") in joined or str(term) in joined))
    return float(sum(1 for term in lexicon if term in tokens or str(term) in joined))


def extract_extended(url: str) -> dict[str, float]:
    ul = str(url).lower()
    toks = tokens_from_url(ul)
    joined = "".join(toks)
    folded = translit_fold(joined)
    f: dict[str, float] = {}
    f["tr_phishing_vocab_score"] = lex_score(toks, joined, TR_PHISHING)
    f["tr_scam_vocab_score"] = lex_score(toks, joined, TR_SCAM)
    f["tr_semantic_urgency_score"] = lex_score(toks, joined, TR_URGENCY)
    brand_score = 0
    translit_score = 0
    for b in TR_BRANDS:
        if b in joined:
            brand_score += 2
        bf = translit_fold(b)
        if bf and bf in folded and b not in joined:
            brand_score += 1
    for b in TR_BRANDS_WITH_TRCHARS:
        bf = translit_fold(b)
        if bf and bf in folded and b not in joined:
            translit_score += 1
    f["tr_brand_impersonation_score"] = float(brand_score)
    f["tr_transliteration_score"] = float(translit_score)
    return f


def tok_struct(url: str) -> list[str]:
    u = re.sub(r"^https?://", "", str(url).lower())
    return [p for p in re.split(r"[/\.\-_?=&]", u) if len(p) >= 4 and not p.isdigit()]


def tok_domain(domain: str) -> list[str]:
    return [t for t in re.split(r"[\.\-_]", str(domain).lower()) if len(t) >= 3]


def _counter_from(bundle: dict, key: str) -> dict:
    return bundle.get(key) or bundle.get("object", {}).get(key, {}) if isinstance(bundle.get("object"), dict) else bundle.get(key, {})


def extract_graph(url: str, reg_domain: str, tld: str, graph_bundle: dict) -> dict[str, float]:
    # Supports the bundle created by the export cell.
    bundle = graph_bundle.get("object") if isinstance(graph_bundle.get("object"), dict) else graph_bundle
    tot = bundle.get("token_total_count") or bundle.get("token_total_counts") or bundle.get("token_doc_freq") or {}
    dom_ct = bundle.get("token_domain_count") or bundle.get("domain_token_counts") or bundle.get("token_domain_doc_freq") or {}
    mal = bundle.get("token_malicious_count") or bundle.get("token_malicious_counts") or {}
    ben = bundle.get("token_benign_count") or bundle.get("token_benign_counts") or {}
    tld_pairs = bundle.get("tld_token_pairs") or bundle.get("tld_token_counts") or {}
    fam = bundle.get("domain_family") or bundle.get("domain_family_counts") or {}
    campaign_min = int(bundle.get("campaign_min", 3))
    rare_threshold = int(bundle.get("rare_threshold", 50))

    domain = reg_domain or (_tld(url).registered_domain if hasattr(_tld(url), "registered_domain") else "")
    toks = set(tok_struct(url))
    rare = [t for t in toks if int(tot.get(t, 0)) >= campaign_min and int(dom_ct.get(t, 999)) < rare_threshold]
    f: dict[str, float] = {}
    f["rare_token_count"] = len(rare)
    f["max_token_cluster_size"] = max((int(tot.get(t, 0)) for t in toks), default=0)
    f["shared_token_degree"] = sum(int(tot.get(t, 0)) for t in toks)
    camp = sum(1 for t in rare if (int(mal.get(t, 0)) + int(ben.get(t, 0))) > 0 and int(mal.get(t, 0)) / (int(mal.get(t, 0)) + int(ben.get(t, 0))) > 0.8)
    f["campaign_token_score"] = camp
    nt = max(len(toks), 1)
    f["unique_token_ratio"] = sum(1 for t in toks if int(tot.get(t, 0)) <= 2) / nt
    f["token_reuse_score"] = sum(1 for t in toks if int(tot.get(t, 0)) > 10) / nt
    sig = domain[:3] + domain[-3:] if len(domain) >= 6 else domain
    f["domain_family_size"] = int(fam.get(sig, 1))
    f["tld_token_cooccur"] = sum(int(tld_pairs.get(f"{tld}|||{t}", 0)) for t in toks)
    f["sibling_domain_count"] = max(f["domain_family_size"] - 1, 0)
    f["domain_ngram_cluster"] = sum(int(dom_ct.get(t, 0)) for t in tok_domain(domain))
    f["registrant_pattern_score"] = len(domain) + domain.count("-") * 3 + sum(c.isdigit() for c in domain) * 2
    f["subdomain_reuse_count"] = sum(1 for t in toks if int(dom_ct.get(t, 0)) > 5)
    f["path_template_reuse"] = sum(int(tot.get(t, 0)) for t in rare)
    f["host_pattern_degree"] = len([t for t in toks if int(tot.get(t, 0)) >= campaign_min])
    f["campaign_membership"] = int(camp > 0 or f["domain_family_size"] > 5)
    f["token_centrality"] = round(f["shared_token_degree"] / nt, 2)
    f["is_hub_domain"] = int(f["max_token_cluster_size"] > 100)
    ms = sum(int(mal.get(t, 0)) for t in toks)
    ts = sum(int(mal.get(t, 0)) + int(ben.get(t, 0)) for t in toks)
    f["cluster_malicious_ratio"] = round(ms / max(ts, 1), 4)
    return f


class FeatureExtractor:
    def __init__(self, feature_names: list[str], graph_bundle: dict):
        self.feature_names = feature_names
        self.graph_bundle = graph_bundle

    def extract_all(self, url: str, reg_domain: str, tld: str) -> tuple[pd.DataFrame, dict[str, float]]:
        f: dict[str, float] = {}
        f.update(extract_lexical(url))
        f.update(extract_adversarial(url))
        f.update(extract_turkish_linguistic(url))
        f.update(extract_extended(url))
        f.update(extract_graph(url, reg_domain, tld, self.graph_bundle))

        # exact deployment schema; unknown/missing are zero-filled
        row = {name: float(f.get(name, 0.0) or 0.0) for name in self.feature_names}
        df = pd.DataFrame([row], columns=self.feature_names)
        df = df.replace([np.inf, -np.inf], np.nan)
        return df, f


FEATURE_DISPLAY_NAMES_TR: dict[str, str] = {
    "alpha_ratio": "Alfabetik karakter oranÄ±",
    "at_symbol_trick": "@ iÅŸareti hilesi",
    "base64_like_segment": "Base64 benzeri segment",
    "brand_dot_in_subdomain": "Alt alanda marka noktasÄ±",
    "brand_homoglyph": "Marka homoglif belirtisi",
    "brand_in_path": "Yol iÃ§inde marka",
    "brand_in_subdomain": "Alt alanda marka",
    "brand_not_in_domain": "Marka kayÄ±tlÄ± alanda deÄŸil",
    "brand_plus_keyword": "Marka ve ÅŸÃ¼pheli anahtar kelime",
    "brand_tld_mismatch": "Marka/TLD uyumsuzluÄŸu",
    "brand_with_hyphen": "Tireli marka kullanÄ±mÄ±",
    "campaign_membership": "Kampanya Ã¼yeliÄŸi",
    "cluster_malicious_ratio": "KÃ¼me zararlÄ± oranÄ±",
    "com_in_subdomain": "Alt alanda com",
    "contains_brand": "Marka iÃ§eriyor",
    "deep_subdomain_nesting": "Derin alt alan iÃ§ iÃ§eliÄŸi",
    "double_protocol": "Ã‡ift protokol",
    "has_at_in_url": "URL iÃ§inde @ var",
    "has_double_dot": "Ã‡ift nokta var",
    "has_double_slash": "Ã‡ift eÄŸik Ã§izgi var",
    "has_exe": "Ã‡alÄ±ÅŸtÄ±rÄ±labilir dosya iÅŸareti",
    "has_hex_encoding": "Hex kodlama var",
    "has_ip": "IP adresi kullanÄ±mÄ±",
    "has_php": "PHP dosya iÅŸareti",
    "has_punycode": "Punycode alan adÄ±",
    "has_query": "Sorgu parametresi var",
    "has_redirect_param": "YÃ¶nlendirme parametresi",
    "has_url_in_url": "URL iÃ§inde URL",
    "has_www": "www kullanÄ±mÄ±",
    "hash_like_segment": "Hash benzeri segment",
    "hex_in_domain": "Alan adÄ±nda hex dizi",
    "is_free_hosting": "Ãœcretsiz barÄ±ndÄ±rma kullanÄ±mÄ±",
    "is_https": "HTTPS kullanÄ±mÄ±",
    "is_suspicious_tld": "ÅžÃ¼pheli TLD",
    "is_tr_domain": ".tr alan adÄ±",
    "is_turkish_dominant": "TÃ¼rkÃ§e baskÄ±nlÄ±ÄŸÄ±",
    "is_typo_squat": "YazÄ±m benzeri alan adÄ±",
    "langid_tr_confidence": "TÃ¼rkÃ§e dil gÃ¼veni",
    "long_random_path": "Uzun rastgele yol",
    "many_path_dirs": "Ã‡ok sayÄ±da yol dizini",
    "min_brand_edit_dist": "En dÃ¼ÅŸÃ¼k marka dÃ¼zenleme mesafesi",
    "pct_encoded_ratio": "YÃ¼zde kodlama oranÄ±",
    "random_looking_domain": "Rastgele gÃ¶rÃ¼nen alan adÄ±",
    "short_domain_susp_tld": "KÄ±sa alan ve ÅŸÃ¼pheli TLD",
    "susp_tld_with_brand": "Marka ile ÅŸÃ¼pheli TLD",
    "susp_tld_with_keyword": "Anahtar kelime ile ÅŸÃ¼pheli TLD",
    "suspicious_file_in_path": "Yolda ÅŸÃ¼pheli dosya",
    "tld_token_cooccur": "TLD-belirteÃ§ birlikte gÃ¶rÃ¼lme",
    "tr_vs_en_bigram": "TÃ¼rkÃ§e-Ä°ngilizce bigram farkÄ±",
    "url_len": "URL uzunluÄŸu",
}

FEATURE_TOKEN_NAMES_TR: dict[str, str] = {
    "ampersands": "& iÅŸareti",
    "bank": "banka",
    "brand": "marka",
    "brands": "marka",
    "campaign": "kampanya",
    "centrality": "merkezilik",
    "char": "karakter",
    "chars": "karakter",
    "cluster": "kÃ¼me",
    "consonant": "Ã¼nsÃ¼z",
    "count": "sayÄ±sÄ±",
    "degree": "derece",
    "digit": "rakam",
    "digits": "rakam",
    "dirs": "dizin",
    "domain": "alan adÄ±",
    "dots": "nokta",
    "encoded": "kodlanmÄ±ÅŸ",
    "entropy": "entropi",
    "equals": "eÅŸittir iÅŸareti",
    "excessive": "aÅŸÄ±rÄ±",
    "family": "aile",
    "file": "dosya",
    "gov": "kamu",
    "graph": "graf",
    "heavy": "aÄŸÄ±rlÄ±klÄ±",
    "host": "host",
    "hub": "merkez",
    "hyphen": "tire",
    "hyphens": "tire",
    "keyword": "anahtar kelime",
    "keywords": "anahtar kelime",
    "len": "uzunluÄŸu",
    "like": "benzeri",
    "malicious": "zararlÄ±",
    "malware": "zararlÄ± yazÄ±lÄ±m",
    "max": "en yÃ¼ksek",
    "mean": "ortalama",
    "ngram": "n-gram",
    "num": "sayÄ±sÄ±",
    "numeric": "sayÄ±sal",
    "params": "parametre",
    "path": "yol",
    "pattern": "Ã¶rÃ¼ntÃ¼",
    "percent": "yÃ¼zde iÅŸareti",
    "phishing": "kimlik avÄ±",
    "query": "sorgu",
    "random": "rastgele",
    "rare": "nadir",
    "ratio": "oranÄ±",
    "registrant": "kayÄ±t sahibi",
    "reuse": "tekrar",
    "scam": "dolandÄ±rÄ±cÄ±lÄ±k",
    "score": "skoru",
    "sector": "sektÃ¶r",
    "semantic": "anlamsal",
    "segment": "segment",
    "shared": "paylaÅŸÄ±lan",
    "sibling": "kardeÅŸ",
    "slashes": "eÄŸik Ã§izgi",
    "specials": "Ã¶zel karakter",
    "subdomain": "alt alan",
    "subdomains": "alt alan",
    "suffix": "ek",
    "telecom": "telekom",
    "term": "terim",
    "template": "ÅŸablon",
    "tld": "TLD",
    "token": "belirteÃ§",
    "tokens": "belirteÃ§",
    "tr": "TÃ¼rkÃ§e",
    "transliteration": "transliterasyon",
    "turkish": "TÃ¼rkÃ§e",
    "underscores": "alt Ã§izgi",
    "unicode": "Unicode",
    "unique": "benzersiz",
    "urgency": "aciliyet",
    "url": "URL",
    "vocab": "sÃ¶zlÃ¼k",
    "vowel": "Ã¼nlÃ¼",
    "www": "www",
}


def feature_display_name(name: str) -> str:
    return name.replace("_", " ").strip().capitalize()


def _capitalize(value: str) -> str:
    return value[:1].upper() + value[1:] if value else value


def _feature_phrase_tr(value: str) -> str:
    words = [FEATURE_TOKEN_NAMES_TR.get(word, word) for word in value.split("_") if word]
    return " ".join(words)


def feature_display_name_tr(name: str) -> str:
    normalized = str(name).strip().lower().replace("-", "_")
    if normalized in FEATURE_DISPLAY_NAMES_TR:
        return FEATURE_DISPLAY_NAMES_TR[normalized]
    for prefix, suffix in (("has_", " var"), ("num_", " sayÄ±sÄ±")):
        if normalized.startswith(prefix):
            return _feature_phrase_tr(normalized[len(prefix):]) + suffix
    for suffix, label in (("_ratio", " oranÄ±"), ("_score", " skoru"), ("_count", " sayÄ±sÄ±"), ("_len", " uzunluÄŸu")):
        if normalized.endswith(suffix):
            return _feature_phrase_tr(normalized[:-len(suffix)]) + label
    if normalized.startswith("is_"):
        return _capitalize(_feature_phrase_tr(normalized[3:]))
    return _capitalize(_feature_phrase_tr(normalized))


def feature_display_names(name: str) -> dict[str, str]:
    return {"en": feature_display_name(name), "tr": feature_display_name_tr(name)}


def feature_group(name: str) -> str:
    n = name.lower()
    if any(k in n for k in ["cluster", "token_reuse", "domain_family", "centrality", "campaign", "hub", "ngram", "path_template", "shared_token"]):
        return "graph_infrastructure"
    if n.startswith("tr_") or any(k in n for k in ["turkish", "vowel", "harmony", "suffix", "translit"]):
        return "turkish_linguistic"
    if any(k in n for k in ["brand", "typo", "squat", "homoglyph", "punycode", "obfus", "redirect"]):
        return "adversarial_brand"
    if any(k in n for k in ["phishing", "malware", "scam", "keyword", "vocab", "urgency"]):
        return "lexical_keyword"
    return "lexical_structural"

