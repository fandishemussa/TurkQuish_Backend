# ============================================================
# TURKISH THREAT LEXICONS (TUMC) — IMPROVED / SANITISED
# ============================================================
# Curated Turkish word lists per threat category, with weights
# (3 = highly specific, 1 = weak/contextual).
#
# This version is HYGIENE-CLEANED at source:
#   - duplicates removed (dicts dedupe automatically; brand LIST
#     deduped manually)
#   - generic short tokens that substring-match everywhere
#     (gov, son, index, admin, ing, mod, root, van, bel, ...) are
#     EXCLUDED — they destroy discriminative value
#   - short-but-specific threat terms (otp, apk, slot, iban, sgk,
#     hgs, mhrs, odul, hibe, ...) are KEPT
#
# IMPORTANT: the feature code (step2c_turkish_extended.py) matches
# single-word terms on TOKEN BOUNDARIES, not raw substrings, so
# 'son' would not fire inside 'reason' even if present. The two
# safeguards (clean lexicon + token matching) work together.
#
# HONEST NOTE: these are CURATED, not exhaustive or gold-standard
# validated. Report as a curated resource; note in limitations
# that coverage is incomplete and that vocab-derived features
# share the keyword-circularity caveat for classes whose labels
# were assigned via overlapping lexicons.
# ============================================================

# ── PHISHING: credential/identity theft, fake login/verify ──
TR_PHISHING = {
    # account / login / verification
    "giris":3,"giriş":3,"dogrula":3,"doğrula":3,"dogrulama":3,"doğrulama":3,
    "hesap":2,"sifre":3,"şifre":3,"parola":3,"kimlik":3,"tckimlik":3,
    "guvenlik":2,"güvenlik":2,"guncelle":2,"güncelle":2,"onayla":2,
    "aktivasyon":2,"yenile":2,"askiya":3,"askıya":3,"dogrulamakodu":3,
    "doğrulamakodu":3,"onaykodu":3,"smskod":3,"otp":3,"uyelik":2,"üyelik":2,
    "oturum":2,"guvenli-giris":3,"güvenli-giriş":3,"giris-yap":2,"giriş-yap":2,
    "oturum-ac":2,"oturum-aç":2,"iki-asamali":3,"iki-aşamalı":3,
    # banking / financial / refund phishing
    "internetbankaciligi":3,"internetbankacılığı":3,"mobilbankacilik":3,
    "mobilbankacılık":3,"sifremiunuttum":3,"şifremiunuttum":3,"kartbilgileri":3,
    "sanalkart":2,"3dsecure":2,"kredikarti":3,"kredikartı":3,"hesapozeti":3,
    "hesapözeti":3,"ekstre":2,"aidatiade":3,"aidatıade":3,"kartiade":3,
    "kartback":3,"kumbara":2,"finansonay":2,"bakiye-sorgula":2,"kart-onay":3,
    "puan-iade":3,"puaniade":3,"borcodeme":2,"borçödeme":2,"iban-dogrula":3,
    "iban-doğrula":3,
    # gov / e-devlet phishing
    "edevlet":3,"e-devlet":3,"randevu":2,"basvuru":2,"başvuru":2,"vergiborcu":3,
    "cezasorgulama":2,"sgksorgu":2,"enabiz":3,"e-nabiz":3,"enabız":3,"e-nabız":3,
    "mhrs":2,"geliridaresi":2,"tuvturk":2,"tüvtürk":2,"trafikcezasi":3,
    "trafikcezası":3,"vergiadesi":3,"vergiade":3,"tapusorgu":2,"mirassorgu":3,
    "uyap-sorgu":3,"adlisicil":2,"secmen-sorgu":2,"seçmen-sorgu":2,"kep-ileti":2,
    "pandemidestek":3,"sosyal-yardim":3,"sosyal-yardım":3,"bayramikramiyesi":3,
    # cargo / logistics / invoice phishing
    "kargo":2,"teslimat":2,"takip":2,"kurye":2,"adresguncelle":3,"adresgüncelle":3,
    "kolitakip":3,"siparistakip":2,"sipariştakip":2,"fatura":2,"odeme":2,"ödeme":2,
    "dekont":2,"makbuz":2,"gecikme":2,"gumruk-vergisi":3,"gümrük-vergisi":3,
    "gumrukten":3,"gümrükten":3,"eksik-adres":3,"kolim-nerede":2,
    "teslim-edilemedi":3,"paket-takip":2,"ordino":2,"antrepo":2,
    # social / cloud / corporate phishing
    "instagram":2,"facebook":2,"whatsapp":2,"twitter":2,"tiktok":2,"takipci":2,
    "takipçi":2,"mavitik":3,"telif":3,"telifhakki":3,"telifhakkı":3,"hesapcalma":3,
    "hesapçalma":3,"outlook":2,"hotmail":2,"eposta":2,"e-posta":2,
    "kurumsal-webmail":3,"ik-portal":2,"hr-onay":2,"maas-guncelleme":3,
    "maaş-güncelleme":3,"is-teklifi":2,"iş-teklifi":2,
    # quishing / session
    "qrkod":2,"qr-kod":2,"qrokuma":2,"qr-tarama":2,"session-expired":3,
    "oturum-kapandi":3,"oturum-kapandı":3,"yeniden-giris":2,"yeniden-giriş":2,
}

# ── SCAM: fraud, fake prizes, investment/crypto, gambling ───
TR_SCAM = {
    # prizes / giveaways / grants
    "kazandiniz":3,"kazandınız":3,"odul":3,"ödül":3,"hediye":2,"cekilis":3,
    "çekiliş":3,"kampanya":1,"bedava":3,"ucretsiz":2,"ücretsiz":2,"kupon":2,
    "indirim":1,"firsat":2,"fırsat":2,"promosyon":2,"ikramiye":3,"hibe":3,
    "cekilisler":3,"cekilisi":3,"bedava-iphone":3,"hediye-cek":3,"hediye-çek":3,
    "cekilis-sonucu":3,"çekiliş-sonucu":3,
    # investment / task / AI fraud
    "yatirim":3,"yatırım":3,"kripto":3,"bitcoin":3,"kazanc":3,"kazanç":3,
    "borsa":2,"forex":2,"dogalgaz":3,"doğalgaz":3,"altin":2,"altın":2,
    "parakazan":3,"ekgelir":3,"evdecalis":2,"evdeçalış":2,"guvenli-yatirim":3,
    "güvenli-yatırım":3,"katlama":3,"airdrop":3,"gorev-yap":3,"görev-yap":3,
    "begeni-kazanc":3,"beğeni-kazanç":3,"forex-robotu":3,"yapayzeka-kazanc":3,
    "yapayzeka-kazanç":3,"ai-yatirim":3,"ai-yatırım":3,"sinyal-grubu":3,
    "vip-analiz":2,"kaldoracli":2,"kaldıraçlı":2,"petrol-yatirim":3,
    # classifieds / ticket / rental
    "kiralikarac":3,"kiralıkaraç":3,"gunlukkiralik":2,"günlükkiralık":2,
    "filokiralama":3,"bungalov":2,"ucuzbilet":2,"konserbileti":2,"macbileti":2,
    "maçbileti":2,"karaborsa":2,"kapora":3,"sahibinden-acil":2,"devren-satilik":2,
    "devren-satılık":2,
    # gambling
    "bahis":3,"kumar":3,"casino":3,"iddaa":2,"jackpot":3,"slot":3,"rulet":3,
    "sweetbonanza":3,"denemebonusu":3,"poker":3,"blackjack":3,"tuttur":2,
    "canli-casino":3,"canlı-casino":3,"canlibahis":3,"canlıbahis":3,
    "kayip-bonusu":3,"kayıp-bonusu":3,"freebet":3,"freespin":3,"bahissiteleri":3,
    "populer-bahis":2,"popüler-bahis":2,
    # charity / donation fraud
    "yardim":2,"yardım":2,"bagis":2,"bağış":2,"afaddestek":3,"kizilaydestek":3,
    "kızılaydestek":3,"deprem":2,"yardim-vakfi":3,"yardım-vakfı":3,"zekat-bagis":2,
    "zekat-bağış":2,
}

# ── MALWARE: downloads, fake updates, cracked software ──────
TR_MALWARE = {
    # downloads / installers
    "indir":2,"indirme":2,"kurulum":2,"yukle":1,"yükle":1,"crack":3,"kirik":2,
    "kırık":2,"aktivator":3,"aktivatör":3,"keygen":3,"lisans":2,"guncelleme":2,
    "güncelleme":2,"flashplayer":3,"plugin":2,"eklenti":2,"apk":2,"warez":3,
    "torrent":2,"bedavaprogram":3,"fullprogram":3,"crackli":3,"kraklı":3,
    # game cheats / mods
    "oyunhile":3,"hile":2,"aimbot":3,"wallhack":3,"pubghile":3,"valoranthile":3,
    "csgohile":3,"skin-hile":2,"uc-hilesi":3,"vbucks":2,"robloxmod":2,
    "minecraft-crack":3,"hilesi":2,"hileli-apk":3,"free-skins":2,"valorant-vp":2,
    "pubg-uc":2,
    # payloads / tools
    "faturapdf":3,"dekontpdf":3,"stealer":3,"miner":3,"ransomware":3,"fidye":3,
    "trojan":3,"virus":2,"virüs":2,"keylogger":3,"kmsauto":3,"officecrack":3,
    "win-crack":3,"bypass-av":3,"kriptominer":3,"macro-enabled":3,"xlsm":2,"docm":2,
}

# ── OTHER MALICIOUS / DEFACEMENT-style markers ──────────────
# NOTE: TUMC has no separate 'defacement' class; provided for
# completeness / future use as 'other-malicious' linguistic markers.
# Generic tokens (admin, root, index, mod, shell, cyber, mirror,
# leak, owned) deliberately EXCLUDED — they match benign content.
TR_DEFACEMENT = {
    "hacklendi":3,"defaced":3,"pwned":3,"guvenlikacigi":2,"güvenlikaçığı":2,
    "saldiri":2,"saldırı":2,"sistemhata":2,"c99shell":3,"r57shell":3,"b374k":3,
    "zone-h":3,"zoneh":3,"turkhack":3,"turkhackteam":2,"siber-tim":3,
    "cyber-army":3,"hacked-by":3,"deface-mirror":3,"mass-deface":3,"exploit":2,
    "zeroday":3,"sqli":2,"payload":2,"sibersaldiri":3,"sibersaldırı":3,
    "verisizintisi":3,"veri-sizintisi":3,"databasedump":3,"ayyildiz":2,
    "cyberwarrior":2,"redhack":2,"cyber-operation":3,
}

# ── SEMANTIC URGENCY: pressure/time terms (cross-category) ──
# 'son','saat','kalan','dakika' EXCLUDED (match benign words/paths).
TR_URGENCY = {
    "acil":3,"hemen":3,"sondakika":3,"simdi":2,"şimdi":2,"hizli":2,"hızlı":2,
    "derhal":3,"bugun":2,"bugün":2,"suresi":2,"süresi":2,"dolacak":2,"bitiyor":3,
    "uyari":2,"uyarı":2,"dikkat":2,"onemli":2,"önemli":2,"askiya":3,"askıya":3,
    "kapatilacak":3,"kapatılacak":3,"engellendi":3,"iptal":2,"donduruldu":3,
    "silinecek":3,"sonuyari":3,"sonuyarı":3,"aninda":2,"anında":2,"hemenode":3,
    "hemenöde":3,"haciz":3,"icra":3,"son-gun":2,"son-gün":2,"kritik":2,"zorunlu":2,
    "hemen-basvur":3,"gecikmeli":2,"hesap-kapatma":3,"risk-tespiti":3,"bloke":3,
    "kisitlama":2,"kısıtlama":2,"yasal-takip":3,"son-uyari":3,"son-uyarı":3,
}

# ── TURKISH BRANDS (for impersonation / transliteration) ────
# Deduped; generic short tokens (gov, bel, ing, van, abb, ibb, sok,
# son, index...) and bare municipality/ministry single words removed
# because they cause false brand-impersonation matches. Kept: real,
# distinctive brand names >=5 chars or clearly specific.
TR_BRANDS = sorted(set([
    # banks / fintech
    "garanti","garantibbva","akbank","isbank","isbankasi","işbank","işbankası",
    "yapikredi","yapıkredi","ziraat","ziraatbank","ziraatbankasi","halkbank",
    "halkbankasi","vakifbank","vakıfbank","denizbank","finansbank","qnbfinansbank",
    "ingbank","kuveytturk","kuveyttürk","albaraka","sekerbank","şekerbank",
    "odeabank","anadolubank","fibabanka","enpara","papara","tosla","ininal",
    "paycell","fastpay","hayatfinans","sipay","colendi","ozanpay","nkolay",
    "bkmexpress","vakifkatilim","ziraatkatilim","emlakkatilim","turkiyefinans",
    "alternatifbank","burganbank","turkishbank","illerbankasi","turkeximbank",
    # gov / public
    "edevlet","turkiye","türkiye","turksat","ttnet","enabiz","enabız","geliridaresi",
    "tarimkredi","tarımkredi","tuvturk","tüvtürk","kizilay","kızılay","iskur","işkur",
    "mersis","turkiyesigorta","türkiyesigorta","saglikbakanligi","hayatevesigar",
    "mebbis","turkiyeburslari","adaletbakanligi","webtapu","tarimorman",
    "btkakademi","ysksecmen","gocidaresi","cumhurbaskanligi","ulusaltezmerkezi",
    # telecom
    "turkcell","türkcell","vodafone","turktelekom","türktelekom","superonline",
    "millenicom","turknet","türknet","gibirnet","netgsm",
    # e-commerce / retail
    "trendyol","hepsiburada","sahibinden","gittigidiyor","ciceksepeti","çiçeksepeti",
    "yemeksepeti","migros","carrefour","carrefoursa","sokmarket","şokmarket","letgo",
    "dolap","pazarama","istegelsin","tazedirekt","getirbuyuk","getirbüyük","obilet",
    "enuygun","teknosa","mediamarkt","vatanbilgisayar","incehesap","itopya","boyner",
    "lcwaikiki","defacto","koton","gratis","watsons","rossmann","petlebi","macrocenter",
    "hakmar","koctas","evidea","vivense","trendyolyemek","migroshemen","banabi","fuudy",
    # cargo
    "araskargo","yurticikargo","yurtiçikargo","mngkargo","suratkargo","süratkargo",
    "pttkargo","upskargo","kolaygelsin","hepsijet","trendyolexpress","sendeo","kargoturk",
    # crypto / streaming
    "paribu","btcturk","binance","trbinance","gateio","netflix","spotify","exxen",
    "disney","blutv","tivibu","tvplus",
    # metro municipalities (kept distinctive multi-char only)
    "bursabb","antalyabb","adanabb","konyabb","gaziantepbb","kayseribb","kocaelibb",
    "mersinbb","eskisehirbb","samsunbb","trabzonbb","malatyabb","diyarbakirbb",
    "erzurumbb","balikesirbb","tekirdagbb","kahramanmarasbb","denizlibb","manisabb",
    "sakaryabb","sanliurfabb","istanbulsenin","ankarakart","kentkart","sehirkart",
    # gov platforms / agencies (distinctive)
    "mebbis","turkiyeburslari","uyapvatandas","uyapavukat","etebligat","hayatevesigar",
    "saglikbakanligi","ticaretbakanligi","cumhurbaskanligi","anadoluajansi","enerjisa",
    "baskentgaz","kayitlionelektronikposta","dijitaldonusum","acikveri",
]))

# Turkish→ASCII transliteration map (the evasion attackers use)
TR_TRANSLIT = {"ş":"s","Ş":"s","ğ":"g","Ğ":"g","ı":"i","İ":"i",
               "ö":"o","Ö":"o","ü":"u","Ü":"u","ç":"c","Ç":"c"}

# Brands whose CANONICAL form contains Turkish characters — vulnerable
# to transliteration evasion. Used by the transliteration-score feature.
TR_BRANDS_WITH_TRCHARS = sorted(set([
    "yapıkredi","vakıfbank","şekerbank","türkiye","türktelekom","yurtiçikargo",
    "süratkargo","çiçeksepeti","halkbankası","ziraatbankası","işbank","işbankası",
    "türkcell","kuveyttürk","enabız","e-nabız","tarımkredi","tüvtürk","türknet",
    "kızılay","işkur","şokmarket","getirbüyük","türkiyesigorta","türkiyeburslari",
]))

def all_lexicons():
    return {"phishing":TR_PHISHING,"scam":TR_SCAM,"malware":TR_MALWARE,
            "defacement":TR_DEFACEMENT,"urgency":TR_URGENCY}

if __name__ == "__main__":
    for name, lex in all_lexicons().items():
        print(f"{name:<12s}: {len(lex):>3d} terms (weight sum {sum(lex.values())})")
    print(f"brands           : {len(TR_BRANDS)} canonical (deduped)")
    print(f"brands w/ TR char: {len(TR_BRANDS_WITH_TRCHARS)}")
    # sanity: no dangerous short tokens leaked in
    bad = [t for lex in all_lexicons().values() for t in lex
           if len(t)<5 and "-" not in t and " " not in t]
    print(f"\nshort single-word terms kept (verify all are specific): {sorted(set(bad))}")