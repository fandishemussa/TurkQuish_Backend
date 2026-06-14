# ============================================================
# LEXICON CLEANER — sanitises the expanded Turkish lexicons
# ============================================================
# Fixes four problems in the raw expanded lexicons:
#   1. Duplicates (esp. in TR_BRANDS) → dedup
#   2. Dangerous generic short tokens (gov, son, index, ing, mod,
#      admin, root...) that substring-match everywhere → drop
#   3. Too-short single-word terms (<5 chars, not hyphenated/
#      multiword) that are too match-prone → drop
#   4. (matching side, in the feature code) substring → token-aware
#
# KEEP-list: short terms that ARE specific & valuable (otp, sms, apk,
# iban, hgs, mhrs, sgk, gib...) are explicitly allowed.
# ============================================================

# Short terms that are SPECIFIC despite length — keep these
ALLOWLIST_SHORT = {
    "otp","sms","apk","iban","hgs","mhrs","sgk","gib","ivd","eba",
    "kpss","yks","ales","yds","msb","kgm","tcdd","dhmi","btk","ysk",
    "spk","bddk","epdk","kvkk","nvi","egm","afad","sgk","mhrs","exe",
    "qr-kod","qrkod","3dsecure","e-devlet","e-nabiz","e-nabız",
}

# Generic tokens that match too broadly — always drop from lexicons/brands
DANGEROUS = {
    "index","admin","root","mod","mirror","login","user","profil","setup",
    "download","zip","rar","tar","iso","bat","cmd","scr","vbs","7z","tg",
    "mobi","gain","hadi","fast","son","saat","para","gelir","destek","kalan",
    "dakika","bonus","slot","token","gov","bel","van","ordu","sok","ing",
    "teb","abb","ibb","ego","cyber","leak","rat","kik","yok","trt","hbg",
    "owned","root","admin","mod","index","fatih","konak","van","gain","mavi",
    "kep","fups","hadi","mobi","getir","sok","bim","a101","flo","koton",
    "gost","tks","tez","cks","cbs","kep","seyir","asi","nabiz","vakif",
    "gain","fast","son","ek-belge","macro-enabled","shell",
}

MIN_LEN = 5

def _specific(t):
    return (" " in t) or ("-" in t)

def clean_lexicon(lex):
    out = {}
    for term, w in lex.items():
        t = term.strip().lower()
        if t in ALLOWLIST_SHORT:
            out[t] = w; continue
        if t in DANGEROUS:
            continue
        if len(t) < MIN_LEN and not _specific(t):
            continue
        out[t] = w
    return out

def clean_brands(brands):
    seen, out = set(), []
    for b in brands:
        t = b.strip().lower()
        if t in ALLOWLIST_SHORT:
            if t not in seen: seen.add(t); out.append(t)
            continue
        if t in DANGEROUS:
            continue
        if len(t) < MIN_LEN and not _specific(t):
            continue
        if t in seen:
            continue
        seen.add(t); out.append(t)
    return out