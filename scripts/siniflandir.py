#!/usr/bin/env python3
"""On siniflandirma: her domaini toxic-imza / beyaz-liste / gri kovasina ayirir.

Kullanim:
    python siniflandir.py --girdi <klasor>/yeni.json --out <klasor>

Bu bir KARAR DEGIL, onceliklendirmedir. Amac Playwright ziyaretlerini dogru yere
yoneltmek: gri kovadakiler ve yuksek etkili olanlar ziyaret edilir, seri uretim spam
aglari ornekleme ile gecilir.

Cikti: siniflandirma.json  (her kayda 'kova', 'kategori', 'imzalar', 'ziyaret_et' eklenir)
       kova_ozet.json      (sayimlar ve ziyaret listesi)
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

# --- Ziyaret esikleri -------------------------------------------------------
# Yanlis pozitifin pahali oldugu yerde gozle dogrula: guclu ve mesru bir linki
# yanlislikla disavow etmek siralama kaybettirir.
DR_ESIK = 30
TRAFIK_ESIK = 10000

# --- Toxic imzalari ---------------------------------------------------------
LINK_SATIS_BASLIK = re.compile(
    r"(directory pages index|domain list page|most visited|website list|domain collection"
    r"|buy .{0,20}backlink|backlinks? for|dofollow|guest post|niche edit|pbn"
    r"|link building|link velocity|domain rating|trust flow|serp boost|crawl budget"
    r"|anchor text|high(er)? da|da/pa|tier.?1|outreach pro|link juice|rank forge|link baron"
    r"|seoexpress|seo express|spent a small fortune|white hat seo|authority backlink"
    r"|contextual link|citation flow|manual outreach|higher d[ar] score|domain authority"
    r"|seo cartel|seo.?anomaly|links.?dealer|masslinker|t\.me/|telegram)",
    re.I,
)
LINK_SATIS_DOMAIN = re.compile(
    r"(seo|link|rank|backlink|boost|guestpost|serp|dofollow)", re.I
)
SATIS_TLD = re.compile(r"\.(shop|store|site|click|agency|online|space|website)$", re.I)

HACK_IMZA = re.compile(
    r"(seo_linkk_order|links?.?dealer|masslinker|seo.?cartel|dark side links"
    r"|black hat seo|situs berita|judi|slot gacor|togel)",
    re.I,
)

# Yetiskin icerik: kelime siniriyla eslesir. "gecelik", "ic giyim", "sutyen", "mayo"
# gibi tekstil terimleri MESRU urun kelimeleridir - buraya asla eklenmez.
YETISKIN = re.compile(
    r"(\bporn|pornhub|xhamster|xnxx|xvideos|\bxxx\b|sikis|sikiş|\bseks\b|sexshop|sex-"
    r"|\bescort|eskort|travesti|erotik|erotic|fetish|hentai|camgirl|webcam show"
    r"|\bmilf\b|ensest|\+18\b)",
    re.I,
)
KUMAR = re.compile(
    r"(casino|casibom|bahis|bahsegel|\d+bet\b|bet\d+|jojobet|holiganbet|tipobet"
    r"|matadorbet|mostbet|1xbet|slot|rulet|iddaa|deneme.?bonus|maxwin|gacor)",
    re.I,
)

OTOMATIK_ICERIK = re.compile(
    r"(encyclopedia q&a|电影网|网址大全|situs berita|生活|焦点|连续剧|美剧)", re.I
)
RASTGELE_HOST = re.compile(r"^[a-z0-9]{8,}\.[a-z0-9-]+\.(xyz|asia|info|site|online)$", re.I)
SUPHELI_TLD = re.compile(r"\.(xyz|asia|info|click|space|icu|top|cfd|sbs)$", re.I)

# --- Beyaz liste ------------------------------------------------------------
BEYAZ_TLD = re.compile(r"\.(gov|edu)(\.[a-z]{2})?$|\.(gov|edu)\.tr$", re.I)
BEYAZ_DOMAIN = {
    "wikipedia.org", "wikimedia.org", "google.com", "google.com.tr", "apple.com",
    "microsoft.com", "linkedin.com", "facebook.com", "instagram.com", "x.com",
    "twitter.com", "youtube.com", "kap.org.tr", "tobb.org.tr", "ticaret.gov.tr",
    "sanayi.gov.tr", "resmigazete.gov.tr", "kariyer.net", "yenibiris.com",
    "eksisozluk.com", "onedio.com", "trendyol.com", "hepsiburada.com", "n11.com",
    "amazon.com.tr", "boyner.com.tr", "brandfetch.com", "crunchbase.com",
}
# Markayi listeleyen zararsiz site tipleri - baslik/icerik kaliplari
LISTELEME_KALIBI = re.compile(
    r"(mağaza|magaza|avm|alışveriş merkez|alisveris merkez|şube|sube|bayilik|franchise"
    r"|iş ilan|is ilan|firma profil|şirket profil|sirket profil|indirim kod|kupon"
    r"|logo|brand assets|adres|iletişim|iletisim)",
    re.I,
)


# Pazar dili disinda kalan dillerin spam agi sinyali olma gucu. Hedef pazarin dilinde
# olmayan bir sayfadan link gelmesi tek basina toxic yapmaz (global markalar, yabanci
# pazaryerleri, kargo siteleri mesru olarak baska dilde olur) - ama pazarla hicbir
# ilgisi olmayan uzak bir dil, otomatik uretim aglarinin en gorunur izidir.
UZAK_DILLER = {"zh", "id", "ja", "ko", "th", "vi", "hi", "bn", "ur", "fa", "ms", "tl"}


def dil_uyumsuz(k, pazar_dilleri):
    """Sayfa dili hedef pazarla uyumsuz ve uzak bir dilse True."""
    if not pazar_dilleri:
        return False
    ham = k.get("diller")
    if not ham:
        return False
    if isinstance(ham, str):
        diller = [d.strip().lower()[:2] for d in ham.replace(";", ",").split(",") if d.strip()]
    else:
        diller = [str(d).strip().lower()[:2] for d in ham if str(d).strip()]
    if not diller:
        return False
    # Pazar dillerinden biri varsa uyumlu say
    if any(d in pazar_dilleri for d in diller):
        return False
    # Ingilizce her pazarda olagan kabul edilir
    if "en" in diller:
        return False
    return any(d in UZAK_DILLER for d in diller)


def imzalari_bul(k, pazar_dilleri=frozenset()):
    host = (k.get("host") or "").lower()
    domain = (k.get("domain") or "").lower()
    baslik = str(k.get("baslik") or "")
    anchor = str(k.get("anchor") or "")
    kategori = str(k.get("sayfa_kategorisi") or "")
    metin = f"{baslik} {anchor}"
    imzalar = []

    if YETISKIN.search(host) or YETISKIN.search(metin) or "/Adult" in kategori:
        imzalar.append("yetiskin-icerik")
    if KUMAR.search(host) or KUMAR.search(metin):
        imzalar.append("kumar")
    if HACK_IMZA.search(metin):
        imzalar.append("hacklenmis-enjeksiyon")
    if LINK_SATIS_BASLIK.search(baslik):
        imzalar.append("link-satis-baslik")
    if LINK_SATIS_DOMAIN.search(domain) and SATIS_TLD.search(domain):
        imzalar.append("link-satis-domain")
    if OTOMATIK_ICERIK.search(baslik):
        imzalar.append("otomatik-icerik")
    if RASTGELE_HOST.match(host):
        imzalar.append("rastgele-host")

    # Yuksek DR + sifir organik trafik: link satis aglarinin en guvenilir parmak izi.
    dr, trafik = k.get("dr"), k.get("trafik_domain")
    if dr is not None and trafik is not None and dr >= 35 and trafik == 0:
        imzalar.append("yuksek-dr-sifir-trafik")

    # Sayfada yuzlerce dis link -> link ciftligi sayfasi
    if (k.get("dis_link") or 0) >= 300:
        imzalar.append("asiri-dis-link")

    if dil_uyumsuz(k, pazar_dilleri):
        imzalar.append("pazar-disi-dil")

    return imzalar


def beyaz_mi(k):
    domain = (k.get("domain") or "").lower()
    if domain in BEYAZ_DOMAIN:
        return "bilinen-platform"
    if BEYAZ_TLD.search(domain) or str(k.get("tld_sinifi") or "") in ("gov", "edu"):
        return "gov-edu"
    return None


def kova_belirle(k, pazar_dilleri=frozenset()):
    imzalar = imzalari_bul(k, pazar_dilleri)

    # Yetiskin ve kumar imzasi beyaz listeyi ezer - bunlar hicbir kosulda temiz sayilmaz
    kritik = {"yetiskin-icerik", "kumar"} & set(imzalar)
    if kritik:
        return "toxic-imza", ("yetiskin-icerik" if "yetiskin-icerik" in kritik else "kumar"), imzalar

    beyaz = beyaz_mi(k)
    if beyaz:
        return "beyaz-liste", beyaz, imzalar

    if "hacklenmis-enjeksiyon" in imzalar:
        return "toxic-imza", "hacklenmis", imzalar
    if {"link-satis-baslik", "link-satis-domain"} & set(imzalar):
        return "toxic-imza", "link-satis", imzalar
    if {"otomatik-icerik", "rastgele-host"} & set(imzalar):
        return "toxic-imza", "icerik-ciftligi", imzalar
    # Pazar disi uzak dil TEK BASINA toxic yapmaz - yabanci pazaryeri, kargo ya da
    # haber sitesi mesru olarak baska dilde olabilir. Ancak supheli uzanti ya da
    # asiri dis link gibi ikinci bir imzayla birlesirse otomatik uretim agidir.
    if "pazar-disi-dil" in imzalar and (
        SUPHELI_TLD.search(k.get("domain") or "") or "asiri-dis-link" in imzalar
    ):
        return "toxic-imza", "icerik-ciftligi", imzalar
    if "yuksek-dr-sifir-trafik" in imzalar and SUPHELI_TLD.search(k.get("domain") or ""):
        return "toxic-imza", "pbn-supheli", imzalar

    # Markayi listeleyen zararsiz siteler: karar yine ziyaretle netlesir ama
    # gri kovada dusuk oncelikli isaretlenir
    if LISTELEME_KALIBI.search(str(k.get("baslik") or "")):
        return "gri", "listeleme-olasi", imzalar

    return "gri", "belirsiz", imzalar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--girdi", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dr-esik", type=float, default=DR_ESIK)
    ap.add_argument("--trafik-esik", type=float, default=TRAFIK_ESIK)
    ap.add_argument(
        "--diller",
        default="",
        help="Hedef pazarin dilleri, virgulle: 'tr' veya 'tr,de'. Bos birakilirsa dil "
             "degerlendirmesi yapilmaz.",
    )
    a = ap.parse_args()
    pazar_dilleri = frozenset(
        d.strip().lower()[:2] for d in a.diller.split(",") if d.strip()
    )

    kayitlar = json.loads(Path(a.girdi).read_text(encoding="utf-8"))

    # Ayni toxic agin kac domaini var? Ornekleme karari icin baslik imzasi sayilir.
    baslik_sayaci = Counter(
        str(k.get("baslik") or "")[:60] for k in kayitlar if str(k.get("baslik") or "")
    )

    for k in kayitlar:
        kova, kategori, imzalar = kova_belirle(k, pazar_dilleri)
        k["kova"], k["kategori"], k["imzalar"] = kova, kategori, imzalar

        yuksek_etkili = (k.get("dr") or 0) >= a.dr_esik or (
            k.get("trafik_domain") or 0
        ) >= a.trafik_esik
        seri_uretim = baslik_sayaci.get(str(k.get("baslik") or "")[:60], 0) >= 5

        # Gri olanlar her halukarda ziyaret edilir. Toxic imzalilar yalnizca yuksek
        # etkiliyse ziyaret edilir - seri uretim aglari orneklemle gecilir.
        if kova == "gri":
            k["ziyaret_et"] = True
        elif kova == "beyaz-liste":
            k["ziyaret_et"] = False
        else:
            k["ziyaret_et"] = yuksek_etkili and not seri_uretim
        k["seri_uretim_agi"] = seri_uretim

    cikti = Path(a.out)
    cikti.mkdir(parents=True, exist_ok=True)
    (cikti / "siniflandirma.json").write_text(
        json.dumps(kayitlar, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    ozet = {
        "toplam": len(kayitlar),
        "pazar_dilleri": sorted(pazar_dilleri) or "belirtilmedi",
        "pazar_disi_dil": sum(1 for k in kayitlar if "pazar-disi-dil" in k["imzalar"]),
        "kovalar": dict(Counter(k["kova"] for k in kayitlar)),
        "kategoriler": dict(Counter(k["kategori"] for k in kayitlar)),
        "ziyaret_edilecek": sum(1 for k in kayitlar if k["ziyaret_et"]),
        "seri_uretim_agi_domain": sum(1 for k in kayitlar if k["seri_uretim_agi"]),
    }
    (cikti / "kova_ozet.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(json.dumps(ozet, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
