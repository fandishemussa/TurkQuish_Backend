from __future__ import annotations

import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import tldextract

from app.services.feature_extractor import (
    ALL_BRANDS,
    SUSPICIOUS_TLDS,
    levenshtein,
    safe_parse,
    tokens_from_url,
    translit_fold,
)

_tld = tldextract.TLDExtract(suffix_list_urls=())


# High-value organizations whose official domains are known.
# This allowlist is URL-only: it does not call DNS/WHOIS/reputation services.
# A larger curated registry is loaded from app/resources/turkish_protected_brands.json.
DEFAULT_PROTECTED_ENTITIES: list[dict[str, Any]] = [
    {
        "name": "Konya Technical University",
        "category": "university",
        "aliases": [
            "ktun",
            "konya teknik universitesi",
            "konya teknik Ã¼niversitesi",
            "konya technical university",
        ],
        "official_domains": ["ktun.edu.tr"],
    },
    # You can add more protected organizations here, for example:
    # {
    #     "name": "Konya Technical University Institute",
    #     "category": "university",
    #     "aliases": ["lee", "ktun lee"],
    #     "official_domains": ["lee.ktun.edu.tr"],
    # },
]


def _dedupe_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate protected entities while preserving order."""
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for ent in entities:
        name = str(ent.get("name", "")).strip()
        domains = tuple(sorted(str(d).strip().lower() for d in ent.get("official_domains", []) if str(d).strip()))
        if not name:
            continue
        key = (name.lower(), domains)
        if key in seen:
            continue
        seen.add(key)
        ent = dict(ent)
        ent["aliases"] = sorted({str(a).strip().lower() for a in ent.get("aliases", []) if str(a).strip()}, key=len, reverse=True)
        ent["official_domains"] = list(domains)
        out.append(ent)
    return out


def _load_json_protected_entities() -> list[dict[str, Any]]:
    """Load curated Turkish protected-brand registry.

    The JSON file lets you add banks, universities, municipalities, hospitals,
    cargo companies, e-commerce brands, and public portals without editing Python.
    """
    path = Path(__file__).resolve().parents[1] / "resources" / "turkish_protected_brands.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        entities = data.get("entities", data if isinstance(data, list) else [])
        return [e for e in entities if isinstance(e, dict)]
    except Exception:
        return []


PROTECTED_ENTITIES: list[dict[str, Any]] = _dedupe_entities(
    list(DEFAULT_PROTECTED_ENTITIES) + _load_json_protected_entities()
)



@dataclass(frozen=True)
class SimilarBrandMatch:
    brand: str
    token: str
    editDistance: int
    similarity: float
    location: str


class BrandImpersonationService:
    """Detect brand impersonation and Levenshtein/typosquatting signals.

    This service is URL-only. It does not call DNS, WHOIS, HTML, screenshots,
    reputation APIs, or any external network service.

    It combines:
      1. generic brand/Levenshtein checks, and
      2. protected-entity official-domain checks for local organizations such as KTUN.
    """

    def __init__(self, brands: list[str] | None = None, protected_entities: list[dict[str, Any]] | None = None):
        cleaned = []
        for b in brands or ALL_BRANDS:
            b = str(b).strip().lower()
            if len(b) >= 3:
                cleaned.append(b)

        self.protected_entities = protected_entities or PROTECTED_ENTITIES
        for ent in self.protected_entities:
            for alias in ent.get("aliases", []):
                alias = str(alias).strip().lower()
                # Add protected aliases to the generic Levenshtein brand catalog only when
                # they are not very short acronyms. Short aliases such as ITU/TEB/SGK are
                # handled by protected-entity logic with token boundaries to avoid false hits
                # inside unrelated words.
                if len(alias.replace(" ", "")) >= 4 or any(ch.isdigit() for ch in alias):
                    cleaned.append(alias)

        self.brands = sorted(set(cleaned), key=len, reverse=True)

    @staticmethod
    def _parse_url(url: str):
        u = str(url).strip()
        if not u.startswith(("http://", "https://")):
            u = "http://" + u
        parsed = safe_parse(u) or urlparse(u)
        ext = _tld(u)
        return u.lower(), parsed, ext

    @staticmethod
    def _registered_host(domain: str, suffix: str) -> str:
        return ".".join([x for x in [domain, suffix] if x]).lower().strip(".")

    @staticmethod
    def _clean_www(host: str) -> str:
        host = str(host).lower().strip(".")
        if host.startswith("www."):
            return host[4:]
        return host

    @staticmethod
    def _is_official_host(host: str, official_domains: list[str]) -> bool:
        host = BrandImpersonationService._clean_www(host)
        for official in official_domains:
            official = BrandImpersonationService._clean_www(str(official).lower())
            if host == official or host.endswith("." + official):
                return True
        return False

    def _is_known_official_host(self, host: str, reg_host: str) -> bool:
        for ent in self.protected_entities:
            official_domains = [str(d).lower() for d in ent.get("official_domains", [])]
            if self._is_official_host(host, official_domains) or self._is_official_host(reg_host, official_domains):
                return True
        return False

    @staticmethod
    def _official_labels(official_domains: list[str]) -> set[str]:
        labels = set()
        for official in official_domains:
            ext = _tld(str(official).lower())
            if ext.domain:
                labels.add(ext.domain.lower())
        return labels

    @staticmethod
    def _contains_alias_with_extra_chars(domain_label: str, alias: str) -> bool:
        """Catch ktun -> kkktun, ktun-login, myktun etc.

        We intentionally handle short acronyms separately because plain
        Levenshtein similarity is too strict for short words: kkktun vs ktun
        has edit distance 2 but is clearly a prefix-insertion typosquat.
        """
        d = translit_fold(domain_label).replace("-", "").replace("_", "")
        a = translit_fold(alias).replace(" ", "").replace("-", "")
        if len(a) < 3:
            return False
        return a in d and d != a

    @staticmethod
    def _alias_occurs(alias: str, host: str, path: str, query: str) -> bool:
        """Boundary-aware protected alias matching.

        For short acronyms (e.g. ITU, TEB, SGK), raw substring matching creates
        false positives inside unrelated words. Therefore short aliases must appear
        as their own URL token. Longer aliases may match compacted text.
        """
        a = translit_fold(str(alias).lower()).replace(" ", "").replace("-", "")
        if len(a) < 3:
            return False

        text = f"{host} {path} {query}".lower()
        folded_text = translit_fold(text)
        tokens = {
            translit_fold(tok).replace("-", "").replace("_", "")
            for tok in re.split(r"[^a-z0-9Ã§ÄŸÄ±Ã¶ÅŸÃ¼]+", text)
            if tok
        }

        # Short acronym: require exact token occurrence, not substring.
        if len(a) <= 4:
            return a in tokens

        return a in folded_text.replace(" ", "").replace("-", "")

    @staticmethod
    def _domain_tokens(domain: str, subdomain: str) -> list[tuple[str, str]]:
        items: list[tuple[str, str]] = []
        for token in re.split(r"[.\-_]+", domain.lower()):
            if len(token) >= 3:
                items.append((token, "domain"))
        for token in re.split(r"[.\-_]+", subdomain.lower()):
            if len(token) >= 3 and token != "www":
                items.append((token, "subdomain"))
        compact = domain.lower().replace("-", "").replace("_", "")
        if len(compact) >= 4 and compact != domain.lower():
            items.append((compact, "domain_compact"))
        return items

    def _similar_brand_matches(self, domain: str, subdomain: str, url_tokens: list[str]) -> list[dict[str, Any]]:
        candidates = self._domain_tokens(domain, subdomain)
        for token in url_tokens[:25]:
            if len(token) >= 4:
                candidates.append((token.lower(), "url_token"))

        seen = set()
        matches: list[SimilarBrandMatch] = []

        for token, location in candidates:
            folded_token = translit_fold(token)
            for brand in self.brands:
                if len(brand) < 4:
                    continue

                folded_brand = translit_fold(brand)
                if not folded_brand:
                    continue

                # Exact brand mention is handled separately. Here we want look-alikes.
                if folded_token == folded_brand:
                    continue

                # For short acronyms, allow prefix/suffix insertion lookalikes.
                acronym_insert = self._contains_alias_with_extra_chars(folded_token, folded_brand) and len(folded_brand) <= 6

                if not acronym_insert and abs(len(folded_token) - len(folded_brand)) > 2:
                    continue

                d = levenshtein(folded_token, folded_brand, cap=4 if acronym_insert else 3)
                if d <= 0:
                    continue
                if not acronym_insert and d > 2:
                    continue

                similarity = 1.0 - (d / max(len(folded_token), len(folded_brand), 1))
                if not acronym_insert and similarity < 0.72:
                    continue

                key = (brand, token, location)
                if key in seen:
                    continue
                seen.add(key)
                matches.append(SimilarBrandMatch(
                    brand=brand,
                    token=token,
                    editDistance=int(d),
                    similarity=round(float(similarity), 4),
                    location=location,
                ))

        matches.sort(key=lambda m: (m.editDistance, -m.similarity, m.brand))
        return [m.__dict__ for m in matches[:10]]

    def _protected_entity_signals(self, u_lower: str, host: str, reg_host: str, domain: str, path: str, query: str) -> tuple[list[dict[str, Any]], list[str], float]:
        hits: list[dict[str, Any]] = []
        signals: list[str] = []
        score = 0.0
        searchable = f"{host} {path} {query}".lower()

        for ent in self.protected_entities:
            aliases = [str(a).lower() for a in ent.get("aliases", []) if len(str(a).strip()) >= 3]
            official_domains = [str(d).lower() for d in ent.get("official_domains", [])]
            official = self._is_official_host(host, official_domains) or self._is_official_host(reg_host, official_domains)
            official_labels = self._official_labels(official_domains)

            alias_hits = []
            typo_alias_hits = []
            for alias in aliases:
                folded_alias = translit_fold(alias)
                alias_compact = folded_alias.replace(" ", "").replace("-", "")
                folded_domain = translit_fold(domain).replace("-", "").replace("_", "")

                if self._alias_occurs(alias, host, path, query):
                    alias_hits.append(alias)

                # Domain label contains official acronym but is not the official label.
                if self._contains_alias_with_extra_chars(domain, alias):
                    typo_alias_hits.append(alias)

                # Official label edit-distance check: kkktun vs ktun.
                for official_label in official_labels:
                    if domain == official_label:
                        continue
                    folded_label = translit_fold(official_label)
                    if self._contains_alias_with_extra_chars(domain, official_label):
                        typo_alias_hits.append(official_label)
                        continue
                    if len(folded_label) < 5:
                        continue
                    d = levenshtein(folded_domain, folded_label, cap=4)
                    similarity = 1.0 - (d / max(len(folded_domain), len(folded_label), 1))
                    if 0 < d <= 2 and similarity >= 0.78:
                        typo_alias_hits.append(official_label)

            alias_hits = sorted(set(alias_hits), key=len, reverse=True)
            typo_alias_hits = sorted(set(typo_alias_hits), key=len, reverse=True)

            if official:
                continue

            if alias_hits:
                signals.append("protected_brand_on_unofficial_domain")
                score += 4.0
            if typo_alias_hits:
                signals.append("protected_acronym_extra_chars_or_typosquat")
                score += 4.0

            if alias_hits or typo_alias_hits:
                hits.append({
                    "name": ent.get("name"),
                    "category": ent.get("category"),
                    "aliasesMatched": alias_hits,
                    "typoAliasesMatched": typo_alias_hits,
                    "officialDomains": official_domains,
                    "observedRegisteredDomain": reg_host,
                    "officialDomainMatched": False,
                })

        return hits, sorted(set(signals)), score

    def analyze(self, url: str) -> dict[str, Any]:
        u_lower, parsed, ext = self._parse_url(url)
        subdomain = ext.subdomain or ""
        domain = ext.domain or ""
        suffix = ext.suffix or ""
        host = ".".join([x for x in [subdomain, domain, suffix] if x]).lower()
        reg_host = self._registered_host(domain, suffix)
        path = (parsed.path or "").lower()
        query = (parsed.query or "").lower()
        tld = suffix.split(".")[-1].lower() if suffix else ""
        url_tokens = tokens_from_url(u_lower)
        is_known_official = self._is_known_official_host(host, reg_host)

        detected_brands = sorted({b for b in self.brands if b in u_lower}, key=len, reverse=True)
        domain_brands = sorted({b for b in detected_brands if b in domain.lower()}, key=len, reverse=True)
        subdomain_brands = sorted({b for b in detected_brands if b in subdomain.lower()}, key=len, reverse=True)
        path_brands = sorted({b for b in detected_brands if b in path or b in query}, key=len, reverse=True)
        similar = [] if is_known_official else self._similar_brand_matches(domain, subdomain, url_tokens)
        if is_known_official:
            protected_hits, protected_signals, protected_score = [], [], 0.0
        else:
            protected_hits, protected_signals, protected_score = self._protected_entity_signals(u_lower, host, reg_host, domain, path, query)

        signals: list[str] = []
        score = 0.0

        if detected_brands:
            signals.append("brand_mentioned")
            if not is_known_official:
                score += 1.0

        # On official protected domains, brand/service names in subdomains or paths are expected.
        # Keep the detected-brand metadata for explainability, but do not score it as impersonation.
        if not is_known_official:
            if subdomain_brands:
                signals.append("brand_in_subdomain")
                score += 2.0
            if path_brands:
                signals.append("brand_in_path_or_query")
                score += 1.5
            if detected_brands and not domain_brands:
                signals.append("brand_not_registered_domain")
                score += 2.0
            if similar:
                signals.append("levenshtein_brand_lookalike")
                score += 3.0
            if detected_brands and tld in SUSPICIOUS_TLDS:
                signals.append("brand_with_suspicious_tld")
                score += 2.0
            if detected_brands and suffix and suffix not in {"com", "com.tr", "net", "org", "org.tr", "gov.tr", "edu.tr"}:
                signals.append("brand_tld_mismatch")
                score += 1.0
            if any((b + "-") in u_lower or ("-" + b) in u_lower for b in detected_brands):
                signals.append("brand_with_hyphen")
                score += 1.0
        if "xn--" in host:
            signals.append("punycode_domain")
            score += 2.0
        if re.search(r"[Ð°-ÑÐ-Ð¯Î±Î²Î¿ÏÎ½Ñ…Ñ]", url):
            signals.append("homoglyph_characters")
            score += 2.0
        if "@" in host:
            signals.append("at_symbol_host_trick")
            score += 1.5

        signals.extend(protected_signals)
        score += protected_score
        signals = sorted(set(signals))

        impersonation_detected = False if is_known_official else bool(score >= 3.0 or similar or protected_hits)
        if is_known_official:
            risk = "low"
        elif score >= 6.0:
            risk = "high"
        elif score >= 3.0:
            risk = "medium"
        else:
            risk = "low"

        top_match = similar[0] if similar else None
        top_protected = protected_hits[0] if protected_hits else None
        if top_protected:
            en = (
                f"The URL resembles or mentions protected organization '{top_protected['name']}' "
                f"but the registered domain is '{reg_host}', not one of the official domains: "
                f"{', '.join(top_protected['officialDomains'])}."
            )
            tr = (
                f"URL, korunan kurum '{top_protected['name']}' adÄ±nÄ± veya kÄ±saltmasÄ±nÄ± taklit ediyor; "
                f"ancak kayÄ±tlÄ± alan adÄ± '{reg_host}', resmi alan adlarÄ±ndan biri deÄŸil: "
                f"{', '.join(top_protected['officialDomains'])}."
            )
        elif top_match:
            en = (
                f"The domain/token '{top_match['token']}' is very similar to the brand "
                f"'{top_match['brand']}' using Levenshtein edit distance "
                f"{top_match['editDistance']}."
            )
            tr = (
                f"Alan adÄ± veya belirteÃ§ '{top_match['token']}', Levenshtein dÃ¼zenleme mesafesi "
                f"{top_match['editDistance']} ile '{top_match['brand']}' markasÄ±na Ã§ok benziyor."
            )
        elif impersonation_detected and detected_brands:
            en = "The URL mentions a known brand outside the registered domain or in a suspicious URL location."
            tr = "URL, bilinen bir markayÄ± kayÄ±tlÄ± alan adÄ± dÄ±ÅŸÄ±nda veya ÅŸÃ¼pheli bir URL konumunda kullanÄ±yor."
        elif is_known_official:
            en = "The URL is on a protected organization official domain, so brand mentions are treated as expected."
            tr = "URL korunan kurumun resmi alan adinda oldugu icin marka ifadeleri beklenen kullanim olarak degerlendirilir."
        else:
            en = "No strong brand impersonation signal was detected from the URL string."
            tr = "URL metninden gÃ¼Ã§lÃ¼ bir marka taklidi sinyali tespit edilmedi."

        return {
            "impersonationDetected": impersonation_detected,
            "officialDomainMatched": is_known_official,
            "risk": risk,
            "score": round(float(score), 4),
            "registeredDomainLabel": domain,
            "registeredDomain": reg_host,
            "suffix": suffix,
            "detectedBrands": detected_brands[:10],
            "domainBrands": domain_brands[:10],
            "subdomainBrands": subdomain_brands[:10],
            "pathBrands": path_brands[:10],
            "similarBrands": similar,
            "protectedEntityMatches": protected_hits,
            "signals": signals,
            "explanation": {"en": en, "tr": tr},
            "urlOnly": True,
            "method": "turkish_protected_registry_plus_all_brand_rules_plus_levenshtein_edit_distance",
            "protectedRegistrySize": len(self.protected_entities),
            "brandCatalogSize": len(self.brands),
        }

