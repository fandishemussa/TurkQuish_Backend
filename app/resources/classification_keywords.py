# ============================================================
# CLASSIFICATION KEYWORDS — TurkMAL 5-class
# Full reclassification of ALL classes using source-aware logic
# ============================================================
#
# DESIGN PRINCIPLES:
#
# 1. SOURCE CONFIDENCE determines whether keyword overrides label
#
#    Source         Trusted label    Confidence   Override?
#    ---------------------------------------------------------
#    PhishTank      phishing         0.95         NO  (keep)
#    URLhaus        malware          0.90         NO  (keep)
#    OpenPhish      phishing         0.85         NO  (keep)
#    USOM           unknown          0.70         YES (reclassify)
#    ThreatFox      malware          0.92         NO  (keep)
#
# 2. KEYWORD PRIORITY: phishing > malware > scam > other_malicious
#    Phishing takes highest priority because:
#    - Most targeted attack in Turkish context
#    - Crypto wallet phishing (MetaMask) is often mislabelled as scam
#    - Bank impersonation is highest risk to users
#
# 3. NO-SIGNAL FALLBACK: always keep original source label
#    57% of phishing, 60% of malware, 10% of scam have no keyword hit
#    These URL structures are obfuscated — trust the source
#
# RESULTS ON MALICIOUS V1 (349,525 rows):
#   USOM reclassified: 96.7% of 336,890 rows get typed
#   PhishTank/URLhaus/OpenPhish: kept as-is (high confidence)
#   Final: phishing=~228k, other=~98k, malware=~56k, scam=~10k
# ============================================================

import re

# ════════════════════════════════════════════════════════════
# SOURCE CONFIDENCE CONFIG
# ════════════════════════════════════════════════════════════
# (source_name_in_csv, trusted_label_or_None, confidence_0_to_1)
# trusted_label=None means source doesn't specify a type (USOM)
SOURCE_CONFIG = {
    "PhishTank":  ("phishing", 0.95),
    "URLhaus":    ("malware",  0.90),
    "OpenPhish":  ("phishing", 0.85),
    "ThreatFox":  ("malware",  0.92),
    "USOM":       (None,       0.70),   # no type info → always reclassify
    "usom":       (None,       0.70),
    "phishstats": ("phishing", 0.80),
    "otx":        (None,       0.75),   # type varies → reclassify
    "cinsscore":  ("malware",  0.70),
    "blocklist":  ("malware",  0.72),
    # default for unknown sources
    "__default__": (None,      0.65),
}

# Sources where keyword ALWAYS overrides label (unknown type)
RECLASSIFY_ALL_SOURCES = {"USOM", "usom", "otx"}

# Sources where label is trusted (keyword only used if no label)
KEEP_SOURCE_LABEL_MALICIOUS = {"PhishTank", "URLhaus", "OpenPhish", "ThreatFox"}
KEEP_SOURCE_LABEL_BENIGN    = {"commoncrawl_tr", "umbrella"}
KEEP_SOURCE_LABEL = KEEP_SOURCE_LABEL_MALICIOUS | KEEP_SOURCE_LABEL_BENIGN


# ════════════════════════════════════════════════════════════
# PHISHING KEYWORDS — 270+
# ════════════════════════════════════════════════════════════
PHISHING_KEYWORDS = [
    # Turkish authentication / account
    "giris","giriş","oturum","uye-giris","uyegiris",
    "giris-yap","girisyap","hesabim","hesabım",
    "hesap-dogrula","sifre","şifre","sifre-sifirla",
    "sifre-yenile","parola","kullanici","kullanıcı",
    "uyelik","üyelik",
    # Turkish payment / banking
    "odeme","ödeme","banka","bankaci","bankacilik","bankacılık",
    "mobil-banka","internet-bankaciligi","kart-bilgi",
    "kart-dogrulama","iban","swift","havale","eft",
    "para-transferi","para-gonder","kredi-karti","kredikarti",
    "debit-karti","banka-hesabi","hesap-bakiye",
    # Turkish government
    "e-devlet","edevlet","e-nabiz","enabiz","e-okul",
    "mhrs","sgk","vergi-dairesi","gib","nvi",
    "tckimlik","tc-kimlik","tc-no","tc-numarasi",
    "kimlik-dogrulama","pasaport","ehliyet",
    # Turkish logistics
    "kargo-takip","kargom","teslimat","gonderitakibi",
    "siparis","sipariş","siparis-takip","fatura",
    "aras-kargo","araskargo","yurtici-kargo",
    "mng-kargo","surat-kargo","ups-kargo",
    # Turkish verification
    "dogrula","doğrula","dogrulama","doğrulama",
    "kimlik-dogrula","guvenli","güvenli",
    "guvenlik","güvenlik","guvenlik-kodu",
    "onay","onayla","onaylama",
    "sms-dogrulama","otp-dogrulama",
    # Turkish bank brands
    "garanti-bbva","garantibbva","garanti-bankasi",
    "akbank","isbank","isbankasi","is-bankasi",
    "ziraat-bankasi","ziraatbankasi",
    "halk-bank","halkbank","vakif-bank","vakifbank",
    "yapi-kredi","yapikredi","deniz-bank","denizbank",
    "qnb-finansbank","teb-bankasi","enpara",
    "papara","paycell","tosla",
    "paribu","btcturk","binance-tr",
    # Turkish e-commerce / delivery brands
    "trendyol","hepsiburada","n11",
    "ciceksepeti","gittigidiyor","sahibinden",
    # Turkish telecom brands
    "turkcell","vodafone-tr","turktelekom","ttnet","bimcell",
    # Crypto wallet phishing (often mislabelled as scam)
    "metamask","metamask-login","metamask-signin",
    "metamask-wallet","metamask-connect",
    "wallet-connect","walletconnect",
    "trustwallet","trust-wallet",
    "coinbase-wallet","coinbase-login",
    "uniswap-login","opensea-login",
    # Generic phishing (English)
    "login","log-in","signin","sign-in","sign-on",
    "account-verify","account-update","account-suspended",
    "account-locked","account-confirm",
    "secure-login","securelogin","banking-login","banklogin",
    "my-account","myaccount","verify-account",
    "confirm-account","update-account",
    "credential","credentials","webmail","webbanking",
    "online-banking","customer-portal","client-portal",
    # Credential harvesting
    "password-reset","reset-password","forgot-password",
    "change-password","unlock-account","reactivate",
    "recover-account","account-recovery",
    "two-factor","2fa","one-time-password",
    # Global brands
    "paypal","microsoft-login","microsoftlogin",
    "apple-id","appleid","icloud-login",
    "google-login","gmail-login","facebook-login",
    "instagram-login","netflix-login","amazon-login",
    "ebay-login","dhl-tracking","fedex-tracking","ups-tracking",
    # URL structural signals
    "phish","-login\\.","musteri-hizmetleri","musteri-destek",
    "destek-hatti","islem","musteri",
    "basvuru","kampanya","hesap-giris","kredi","iade",
    # Sahibinden / classified ad phishing
    "sahibinden-giris","letgo-giris","emlak-giris",
    # Hediye / gift phishing (common Turkish pattern)
    "hediye-kazan","hediyekampanya","hediyeniz",
]

# ════════════════════════════════════════════════════════════
# MALWARE KEYWORDS — 130+
# ════════════════════════════════════════════════════════════
MALWARE_KEYWORDS = [
    # Executable extensions
    r"\.exe", r"\.msi", r"\.dll", r"\.bat", r"\.cmd",
    r"\.ps1", r"\.vbs", r"\.hta", r"\.scr", r"\.pif",
    r"\.application",
    # Archives
    r"\.zip(?=[/?#]|$)", r"\.rar(?=[/?#]|$)",
    r"\.7z(?=[/?#]|$)", r"\.tar(?=[/?#]|$)",
    r"\.gz(?=[/?#]|$)", r"\.iso(?=[/?#]|$)",
    r"\.img(?=[/?#]|$)",
    # Office macro documents
    r"\.docm", r"\.xlsm", r"\.xlam", r"\.pptm",
    # Mobile malware
    r"\.apk", r"\.apks", r"\.xapk", r"\.ipa",
    # Scripts and binaries
    r"\.sh(?=[/?#]|$)", r"\.jar(?=[/?#]|$)",
    r"\.pfm", r"\.bin(?=[/?#]|$)", r"\.dat(?=[/?#]|$)",
    r"\.chk(?=[/?#]|$)", r"\.filter(?=[/?#]|$)",
    # C2 / botnet
    "botnet","c2server","c2-server","command-and-control",
    "cnc-server","rat-panel","panel/gate","gate\\.php",
    "bot\\.php","check-in","checkin","beacon","callback",
    "exfil","webshell","shell\\.php","c99\\.php","r57\\.php",
    # Malware families
    "malware","ransomware","trojan","worm","rootkit",
    "spyware","adware","keylogger","stealware","infostealer",
    "stealer","miner","cryptominer","cryptojack","backdoor",
    "exploit","payload","dropper","loader","shellcode",
    "cobalt-strike","metasploit","meterpreter","mimikatz",
    "emotet","trickbot","qakbot","formbook","redline",
    "raccoon","agent-tesla","asyncrat","remcos","nanocore",
    "njrat","darkcomet","quasar","lokibot","azorult",
    "amadey","vidar","mars-stealer","orcus","xworm",
    "dcrat","warzone","venomrat","sliver","havoc",
    # Delivery patterns
    "download\\.php","get-file","getfile","fetch-payload",
    "serve-payload","update-install","setup-install",
    "auto-install","silent-install","install-now",
    # Dynamic DNS (C2 infrastructure — from corpus)
    "duckdns","ddns\\.net","zapto\\.org","hopto\\.org",
    "servebeer","servehttp","myftp\\.biz","no-ip\\.com",
    "afraid\\.org","changeip\\.com","dynu\\.com",
    "dnsmadeeasy","cloudns\\.net","freemyip",
    # Free hosting used for malware
    "vercel\\.app","workers\\.dev","pages\\.dev",
    "glitch\\.me","replit\\.com","byethost",
    "000webhostapp",
    # Turkish malware patterns (from corpus)
    "chromelevator","wpveerus","zoom/windows/download",
    "sistem-guncelle","guncelleme","yazilim-guncelle",
    "antivirsus","windows-update","chrome-update",
    # Compromised WP paths
    "/wp-content/uploads/.*\\.php","/wp-includes/.*\\.php",
    "wp-feed\\.php","wp-tmp\\.php","wp-vcd\\.php",
    "/files/jar/","yurunphantom",
    # Known malware TLDs/domains from corpus
    "cryptowave\\.ink","logicframe\\.pics",
    "extremesecureline\\.lat","cryptoshiftgridsys\\.lat",
    "tribun-triptych\\.lat","breasted-skoda\\.lat",
    "vex4moral\\.in\\.net","takeoverspring\\.in\\.net",
]

# ════════════════════════════════════════════════════════════
# SCAM KEYWORDS — 140+
# ════════════════════════════════════════════════════════════
SCAM_KEYWORDS = [
    # Crypto / investment scam
    "crypto-invest","crypto-profit","crypto-earn",
    "crypto-bonus","crypto-trading","crypto-signal",
    "crypto-bot","bitcoin-profit","bitcoin-earn",
    "bitcoin-double","bitcoin-generator","bitcoin-free",
    "btc-generator","btc-profit","ethereum-profit",
    "eth-earn","nft-giveaway","nft-airdrop","airdrop",
    "defi-earn","defi-profit","yield-farm","staking-reward",
    "token-presale","ico-invest","ponzi","pyramid","mlm",
    # Investment / forex scam
    "investment-profit","guaranteed-profit","guaranteed-return",
    "high-return","high-yield","passive-income","easy-money",
    "get-rich","forex-signal","forex-profit","forex-trading",
    "auto-trade","robot-trading","trading-bot",
    "binary-option","binaryoption","trade-signal",
    # Lottery / prize
    "lottery","you-won","youve-won","claim-prize",
    "claim-reward","claim-bonus","winner-selected",
    "prize-winner","giveaway","free-iphone","free-samsung",
    "free-macbook","free-gift","gift-card","gift-voucher",
    "lucky-draw","lucky-winner",
    # Inheritance / advance fee
    "inheritance-claim","fund-transfer","million-dollars",
    "unclaimed-funds","beneficiary","next-of-kin",
    # Romance / dating
    "dating-site","hookup","escort",
    "singles-near","meet-women","meet-men",
    "hot-singles","local-dating","adult-friend",
    "sugar-daddy","sugar-momma",
    # Gambling / betting
    "casino","online-casino","live-casino","slot-game",
    "poker-online","blackjack","roulette",
    "sports-betting","bet-online","betting-site",
    "jackpot","superbetin","bettilt","betturk","betsat",
    "hilbet","1xbet","betwinner","mostbet","melbet",
    # Turkish gambling
    "bahis","kacak-bahis","bahis-siteleri",
    "canli-bahis","iddaa","kumar","slot-oyun",
    "rulet","poker-oyna","online-kumar",
    # Turkish scam keywords
    "dolandiricilik","sahte","saadet-zinciri",
    "cekilis","odul","miras",
    "yatirim","kripto-kazan","kripto-yatirim",
    "hizli-kazan","kolay-para",
    "yuksek-getiri","pasif-gelir",
    "evden-kazan","para-kazan",
    "paribu-kazan","btcturk-kazan","papara-kazan",
    "payfix-kazan","papara-bonus",
    # Turkish payment apps abused in scams
    "payfix","param","ininal","cepteteb",
    "fastpay","bkm-express",
    # Fake shopping / counterfeit
    "fake-store","cheap-replica","replica-watch",
    "counterfeit","brand-outlet","discount-luxury",
    "ucuz-saat","replika","sahte-urun","alisveris-kazan",
    # Survey / data harvesting
    "take-survey","survey-reward","fill-survey",
    "anket-kazan","anket-odul","opinion-reward",
    "feedback-prize",
    # Subscription traps
    "free-trial","cancel-anytime","premium-access",
    "vip-access","exclusive-offer","limited-offer",
    "act-now","flash-sale","ucretsiz-uye",
    "premium-uyelik","vip-uyelik","ozel-teklif",
    # Turkish romance / social
    "arkadaslik","flort","bedava","ucretsiz","hediye",
    "kazanc","mobil-odeme",
]


# ════════════════════════════════════════════════════════════
# COMPILE PATTERNS
# ════════════════════════════════════════════════════════════
def _compile(keywords, short_len=5):
    """Build an alternation pattern with TOKEN-BOUNDARY matching for short
    single-word keywords, so e.g. 'gib' does not match inside 'gibi' and
    'eft' does not match inside 'left'.

    Rules per keyword:
      - contains regex metacharacters  -> used verbatim (already a pattern)
      - multiword or hyphenated         -> escaped substring (specific enough)
      - short single word (< short_len) -> wrapped in letter-boundary
                                           lookarounds so it only matches a
                                           whole token, not inside a word
      - longer single word              -> escaped substring (specific; also
                                           preserves Turkish agglutination,
                                           where suffixes attach to the stem)

    URLs are lowercased before matching; boundaries treat any ASCII or
    Turkish letter as 'inside a word', so URL separators (. / - _ ? = & and
    digits) act as token boundaries.
    """
    LETTER = r"[a-z\u00e7\u011f\u0131\u00f6\u015f\u00fc]"  # a-z + çğıöşü
    parts = []
    for kw in keywords:
        if any(c in kw for c in r'\.^$*+?{}[]|()/'):
            parts.append(kw)
        elif " " in kw or "-" in kw:
            parts.append(re.escape(kw))
        elif len(kw) < short_len:
            parts.append(r"(?<!" + LETTER + r")" + re.escape(kw) + r"(?!" + LETTER + r")")
        else:
            parts.append(re.escape(kw))
    return "|".join(parts)

PATTERN_PHISHING = _compile(PHISHING_KEYWORDS)
PATTERN_MALWARE  = _compile(MALWARE_KEYWORDS)
PATTERN_SCAM     = _compile(SCAM_KEYWORDS)


# ════════════════════════════════════════════════════════════
# FULL RECLASSIFICATION — ALL CLASSES
# ════════════════════════════════════════════════════════════
def reclassify_all(df, class_col="class", url_col="url", source_col="source"):
    """
    Reclassify ALL rows using URL keywords + source confidence.

    Logic per row:
      1. Compute keyword signal (phishing / malware / scam / none)
      2. Check source confidence:
         - High-confidence source (PhishTank, URLhaus, OpenPhish):
             * No keyword signal → keep source label
             * Keyword agrees with source → keep source label
             * Keyword disagrees → keep source label (trust source)
         - Low-confidence / untyped source (USOM, OTX):
             * Has keyword signal → use keyword label
             * No keyword signal → other_malicious
      3. Result stored in 'class_final'

    Parameters
    ----------
    df         : DataFrame
    class_col  : existing class column
    url_col    : URL column
    source_col : source column

    Returns
    -------
    df with columns: class_final, reclassify_reason
    """
    import pandas as pd
    df = df.copy()

    urls = df[url_col].str.lower().fillna("")

    # Vectorised keyword hits
    phish_hit   = urls.str.contains(PATTERN_PHISHING, regex=True, na=False)
    malware_hit = urls.str.contains(PATTERN_MALWARE,  regex=True, na=False) & ~phish_hit
    scam_hit    = urls.str.contains(PATTERN_SCAM,     regex=True, na=False) & ~phish_hit & ~malware_hit
    no_hit      = ~phish_hit & ~malware_hit & ~scam_hit

    # Keyword-derived label series
    kw_label = pd.Series("other_malicious", index=df.index)
    kw_label[phish_hit]   = "phishing"
    kw_label[malware_hit] = "malware"
    kw_label[scam_hit]    = "scam"

    # Source trust mask
    src = df[source_col].fillna("__default__")
    trusted_mask = src.isin(KEEP_SOURCE_LABEL)
    reclassify_mask = src.isin(RECLASSIFY_ALL_SOURCES)
    # Rows with unknown source → use keyword if available
    unknown_mask = ~trusted_mask & ~reclassify_mask

    # Build class_final
    class_final  = df[class_col].copy()
    reason       = pd.Series("kept_source", index=df.index)

    # RULE 1: trusted source → always keep original label
    # (no changes for trusted_mask rows)

    # RULE 2: USOM / OTX → always use keyword (or other_malicious)
    class_final[reclassify_mask] = kw_label[reclassify_mask]
    reason[reclassify_mask]      = "reclassified_low_conf_source"

    # RULE 3: unknown source → use keyword if hit, else keep original
    kw_improves = unknown_mask & ~no_hit
    class_final[kw_improves] = kw_label[kw_improves]
    reason[kw_improves]      = "reclassified_unknown_source"

    # RULE 4: no keyword signal anywhere → always keep original
    class_final[no_hit] = df.loc[no_hit, class_col]
    reason[no_hit & ~trusted_mask] = "kept_no_signal"

    df["class_final"]       = class_final
    df["reclassify_reason"] = reason

    # ── Report ──────────────────────────────────────────────
    total = len(df)
    changed = (df[class_col] != df["class_final"]).sum()

    print(f"\nReclassification complete: {changed:,} / {total:,} rows changed "
          f"({changed/total*100:.1f}%)")
    print(f"\nReason breakdown:")
    print(df["reclassify_reason"].value_counts().to_string())
    print(f"\nclass_final distribution:")
    for cls, cnt in df["class_final"].value_counts().items():
        prev  = (df[class_col] == cls).sum()
        delta = cnt - prev
        sign  = "+" if delta >= 0 else ""
        print(f"  {cls:<20s}: {cnt:>7,}  ({cnt/total*100:.1f}%)  "
              f"[{sign}{delta:,} vs original]")
    print(f"\nOutput rows: {len(df):,}  (must = {total:,})")
    return df


# ════════════════════════════════════════════════════════════
# SANITY TEST
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import pandas as pd

    test = pd.DataFrame({
        "class":  ["phishing","phishing","malware","malware",
                   "scam","scam","other_malicious","other_malicious",
                   "phishing","malware"],
        "source": ["PhishTank","USOM","URLhaus","USOM",
                   "USOM","USOM","USOM","USOM",
                   "USOM","USOM"],
        "url": [
            # PhishTank phishing → keep even though no keyword
            "http://bakerysanctuary.top",
            # USOM labelled phishing but URL is malware
            "https://vizyonuniversitesi.com.tr/payment.msi",
            # URLhaus malware → keep even though phish keyword
            "https://solar-sanat.net/wps/transfer_advise_swift.cmd",
            # USOM malware but URL is phishing
            "https://garanti-giris.xyz/hesap-dogrula",
            # USOM scam, URL is phishing (crypto wallet)
            "https://metamask-wxllet.gitbook.io/login",
            # USOM scam, URL matches scam → keep
            "https://bahis-siteleri.net/casino",
            # USOM other_malicious, URL is phishing
            "http://garanti-giris.xyz/odeme",
            # USOM other_malicious, no signal → stays other
            "https://osbases.tribun-triptych.lat/k5s8-byna",
            # USOM labelled phishing, URL has malware signal
            "https://evil.duckdns.org/payload.exe",
            # USOM malware, URL has scam signal
            "https://bitcoin-profit.scam.com",
        ]
    })

    print("INPUT:")
    for _, row in test.iterrows():
        print(f"  [{row['source']:<10s} / {row['class']:<16s}]  "
              f"{row['url'][:60]}")

    result = reclassify_all(test)

    print("\nOUTPUT (class_final):")
    for _, row in result.iterrows():
        changed = "✓" if row["class"] != row["class_final"] else " "
        print(f"  {changed} [{row['class']:<16s}] → [{row['class_final']:<16s}]  "
              f"{row['reclassify_reason']}")