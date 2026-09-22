#!/usr/bin/env python3
"""Ahrefs backlink verisini normalize eder ve mevcut disavow listesiyle kesisimi ayirir.

Kullanim:
    python hazirla.py --backlinks <dosya> [--disavow <dosya>] --out <klasor>

--backlinks : Ahrefs verisi. JSON (MCP ciktisi), CSV/TSV (UI export, UTF-16) ya da XLSX.
--disavow   : Mevcut GSC disavow dosyasi (duz metin, "domain:ornek.com" satirlari).
              Verilmezse ilk disavow calismasi varsayilir.
--out       : Cikti klasoru. Uc dosya yazilir:
                yeni.json       -> analiz edilecek, disavow'da olmayan kayitlar
                zaten_var.json  -> mevcut disavow listesinin kapsadigi kayitlar
                ozet.json       -> sayimlar

Domain cikarimi Public Suffix List ile yapilir; .com.tr / .co.uk gibi cok parcali
uzantilar ve web.app / blogspot.com gibi barindirma alanlari dogru ayrissin diye.
"""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import tldextract
except ImportError:
    sys.exit("tldextract gerekli:  pip install tldextract")

# suffix_list_urls=() -> paket icindeki PSL anlik goruntusu, ag istegi yok
# include_psl_private_domains=True -> erkek-kol-saati.web.app kendi adiyla kalir,
#   yoksa web.app'e indirgenir ve tum Firebase alanini disavow etmis oluruz
_EX = tldextract.TLDExtract(suffix_list_urls=(), include_psl_private_domains=True)


def host_of(url):
    u = (url or "").strip()
    if not u:
        return ""
    if "://" not in u:
        u = "http://" + u
    try:
        return (urlparse(u).hostname or "").lower().strip(".")
    except ValueError:
        return ""


def kok_domain(url_veya_host):
    h = url_veya_host if "/" not in str(url_veya_host) else host_of(url_veya_host)
    if "://" in str(url_veya_host):
        h = host_of(url_veya_host)
    h = (h or "").lower().strip(".")
    if not h:
        return ""
    r = _EX(h)
    # tldextract >=5.4 'registered_domain'i 'top_domain_under_public_suffix' olarak
    # yeniden adlandirdi; her iki surumde de calissin diye ikisini de destekle
    return getattr(r, "top_domain_under_public_suffix", None) or r.registered_domain or h


def disavow_oku(yol):
    """GSC disavow dosyasindan domain kumesini cikarir. Yorum ve url: satirlari atlanir."""
    domainler = set()
    with open(yol, encoding="utf-8-sig", errors="replace") as f:
        for satir in f:
            s = satir.strip()
            if not s or s.startswith("#"):
                continue
            if s.lower().startswith("domain:"):
                d = s[7:].strip().lower().lstrip(".")
                if d.startswith("www."):
                    d = d[4:]
                if d:
                    domainler.add(d)
            elif "://" in s:
                d = kok_domain(s)
                if d:
                    domainler.add(d)
    return domainler


def kapsaniyor_mu(domain, disavow_kumesi):
    """domain veya ust alan adlarindan biri disavow listesindeyse True."""
    if not domain:
        return False
    parcalar = domain.split(".")
    for i in range(len(parcalar) - 1):
        if ".".join(parcalar[i:]) in disavow_kumesi:
            return True
    return False


def backlink_oku(yol):
    """JSON / CSV / TSV / XLSX destekler. Ahrefs UI export'lari UTF-16 + sekme ayracli."""
    p = Path(yol)
    son = p.suffix.lower()

    if son == ".json":
        veri = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(veri, dict):
            for anahtar in ("backlinks", "data", "rows", "items"):
                if anahtar in veri:
                    return veri[anahtar]
            return [veri]
        return veri

    if son in (".xlsx", ".xlsm"):
        import openpyxl

        ws = openpyxl.load_workbook(p, read_only=True, data_only=True).active
        satirlar = ws.iter_rows(values_only=True)
        basliklar = [str(h) if h is not None else "" for h in next(satirlar)]
        return [dict(zip(basliklar, r)) for r in satirlar]

    import csv

    csv.field_size_limit(10 ** 9)
    for kodlama, ayrac in (("utf-16", "\t"), ("utf-8-sig", ","), ("utf-8-sig", "\t")):
        try:
            with open(p, encoding=kodlama, newline="") as f:
                satirlar = list(csv.DictReader(f, delimiter=ayrac))
            if satirlar and len(satirlar[0]) > 1:
                return satirlar
        except (UnicodeDecodeError, UnicodeError):
            continue
    sys.exit(f"Dosya okunamadi: {p}")


# Ahrefs MCP alan adlari ile UI export basliklari arasindaki koprü
ALAN_ESLEME = {
    "url": ("url_from", "Referring page URL", "url"),
    "baslik": ("title", "Referring page title"),
    "anchor": ("anchor", "Anchor"),
    "dr": ("domain_rating_source", "Domain rating", "Domain Rating"),
    "trafik_domain": ("traffic_domain", "Domain traffic"),
    "trafik_sayfa": ("traffic", "Page traffic"),
    "is_spam": ("is_spam", "Is spam"),
    "diller": ("languages", "Language"),
    "tld_sinifi": ("tld_class_source",),
    "sayfa_tipi": ("page_type_source", "Page type"),
    "sayfa_kategorisi": ("page_category_source", "Page category"),
    "dis_link": ("links_external", "External links"),
    "http_kodu": ("http_code", "Referring page HTTP code"),
    "ilk_gorulme": ("first_seen_link", "First seen"),
    "kayip_mi": ("is_lost", "Lost status"),
}


def alan_al(kayit, mantiksal_ad):
    for aday in ALAN_ESLEME.get(mantiksal_ad, ()):
        if aday in kayit and kayit[aday] not in (None, ""):
            return kayit[aday]
    return None


def sayi(v):
    if v in (None, ""):
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backlinks", required=True)
    ap.add_argument("--disavow")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ham = backlink_oku(a.backlinks)
    mevcut = disavow_oku(a.disavow) if a.disavow else set()

    yeni, zaten_var, urlsiz = [], [], 0
    gorulen = set()

    for k in ham:
        url = alan_al(k, "url")
        if not url:
            urlsiz += 1
            continue
        host = host_of(url)
        domain = kok_domain(url)
        if not domain:
            urlsiz += 1
            continue

        kayit = {
            "url": url,
            "host": host,
            "domain": domain,
            "baslik": alan_al(k, "baslik") or "",
            "anchor": alan_al(k, "anchor") or "",
            "dr": sayi(alan_al(k, "dr")),
            "trafik_domain": sayi(alan_al(k, "trafik_domain")),
            "trafik_sayfa": sayi(alan_al(k, "trafik_sayfa")),
            "is_spam": str(alan_al(k, "is_spam")).lower() in ("true", "1", "yes"),
            "diller": alan_al(k, "diller"),
            "tld_sinifi": alan_al(k, "tld_sinifi"),
            "sayfa_tipi": alan_al(k, "sayfa_tipi"),
            "sayfa_kategorisi": alan_al(k, "sayfa_kategorisi"),
            "dis_link": sayi(alan_al(k, "dis_link")),
            "http_kodu": sayi(alan_al(k, "http_kodu")),
            "ilk_gorulme": str(alan_al(k, "ilk_gorulme") or ""),
        }

        if kapsaniyor_mu(domain, mevcut):
            zaten_var.append(kayit)
        elif domain in gorulen:
            continue  # ayni kok domainden ikinci kayit - disavow domain seviyesinde
        else:
            gorulen.add(domain)
            yeni.append(kayit)

    cikti = Path(a.out)
    cikti.mkdir(parents=True, exist_ok=True)
    (cikti / "yeni.json").write_text(
        json.dumps(yeni, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (cikti / "zaten_var.json").write_text(
        json.dumps(zaten_var, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    ozet = {
        "toplam_kayit": len(ham),
        "mevcut_disavow_domain": len(mevcut),
        "zaten_kapsanan": len(zaten_var),
        "analiz_edilecek": len(yeni),
        "urlsiz_atlanan": urlsiz,
    }
    (cikti / "ozet.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(json.dumps(ozet, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
