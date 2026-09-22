#!/usr/bin/env python3
"""Teslim setini uretir: Excel raporu + GSC'ye yuklenmeye hazir birlesik disavow dosyasi.

Kullanim:
    python rapor_uret.py --kararlar <dosya.json> --out <klasor> \
        [--mevcut-disavow <dosya>] [--marka "Marka Adi"]

--kararlar : Her kayitta en az su alanlar bulunan JSON listesi:
             url, domain, baslik, anchor, dr, trafik_domain, aksiyon, notlar
             'aksiyon' su dortten biri: Disavow (kritik) | Disavow | Kontrol gerekli | Temiz

Uretilenler:
    <marka>-toxic-backlink-raporu.xlsx   Karar sutunlu, renk kodlu Excel
    <marka>-disavow-BIRLESIK.txt         Mevcut liste + yeni tespitler, GSC'ye hazir
    <marka>-disavow-YENI.txt             Yalnizca bu calismada eklenenler
"""

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

BASLIKLAR = [
    "Sayfa URL'i",
    "Domain Rating",
    "Trafik",
    "Domain",
    "Page Title",
    "Anchor Text",
    "Önerilen Aksiyon",
    "Notlar",
]
GENISLIK = [58, 14, 14, 30, 46, 30, 20, 58]

RENK = {
    "Disavow (kritik)": ("FFC7CE", "9C0006"),   # kirmizi
    "Disavow": ("FCE4D6", "974706"),            # turuncu
    "Kontrol gerekli": ("FFF2CC", "7F6000"),    # sari
    "Temiz": ("E2EFDA", "375623"),              # yesil
}
BASLIK_DOLGU = PatternFill("solid", fgColor="1F3864")
BASLIK_YAZI = Font(bold=True, color="FFFFFF")


def disavow_oku(yol):
    domainler = []
    gorulen = set()
    with open(yol, encoding="utf-8-sig", errors="replace") as f:
        for satir in f:
            s = satir.strip()
            if not s or s.startswith("#"):
                continue
            if s.lower().startswith("domain:"):
                d = s[7:].strip().lower().lstrip(".")
                if d.startswith("www."):
                    d = d[4:]
                if d and d not in gorulen:
                    gorulen.add(d)
                    domainler.append(d)
    return domainler


def guvenli_ad(s):
    return re.sub(r"[^\w.-]+", "-", (s or "marka").strip()).strip("-").lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kararlar", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mevcut-disavow")
    ap.add_argument("--marka", default="marka")
    a = ap.parse_args()

    kayitlar = json.loads(Path(a.kararlar).read_text(encoding="utf-8"))
    cikti = Path(a.out)
    cikti.mkdir(parents=True, exist_ok=True)
    ad = guvenli_ad(a.marka)

    # ---- Excel ----
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Toxic Backlink Analizi"
    ws.append(BASLIKLAR)
    for i in range(1, len(BASLIKLAR) + 1):
        ws.cell(1, i).fill = BASLIK_DOLGU
        ws.cell(1, i).font = BASLIK_YAZI
        ws.cell(1, i).alignment = Alignment(vertical="center")

    # Kritik olanlar ustte: kullanici raporu actiginda once onlari gorsun
    sira = {"Disavow (kritik)": 0, "Disavow": 1, "Kontrol gerekli": 2, "Temiz": 3}
    kayitlar.sort(
        key=lambda k: (sira.get(k.get("aksiyon"), 9), -(k.get("dr") or 0))
    )

    for k in kayitlar:
        ws.append([
            k.get("url", ""),
            k.get("dr"),
            k.get("trafik_domain"),
            k.get("domain", ""),
            k.get("baslik", ""),
            k.get("anchor", ""),
            k.get("aksiyon", ""),
            k.get("notlar", ""),
        ])
        r = ws.max_row
        aksiyon = k.get("aksiyon", "")
        if aksiyon in RENK:
            dolgu, yazi = RENK[aksiyon]
            h = ws.cell(r, 7)
            h.fill = PatternFill("solid", fgColor=dolgu)
            h.font = Font(bold=True, color=yazi)

    for i, w in enumerate(GENISLIK, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(BASLIKLAR))}{ws.max_row}"

    # Ozet sayfasi: markaya sunulacak kirilim
    ws2 = wb.create_sheet("Özet")
    ws2.append(["Kategori", "Adet"])
    for i in (1, 2):
        ws2.cell(1, i).fill = BASLIK_DOLGU
        ws2.cell(1, i).font = BASLIK_YAZI
    for aksiyon, adet in Counter(k.get("aksiyon", "") for k in kayitlar).most_common():
        ws2.append([aksiyon, adet])
    ws2.append([])
    ws2.append(["Tespit kategorisi", "Adet"])
    ws2.cell(ws2.max_row, 1).font = Font(bold=True)
    for kat, adet in Counter(
        k.get("kategori", "") for k in kayitlar if str(k.get("aksiyon", "")).startswith("Disavow")
    ).most_common():
        ws2.append([kat, adet])
    ws2.column_dimensions["A"].width = 34
    ws2.column_dimensions["B"].width = 10

    xlsx_yol = cikti / f"{ad}-toxic-backlink-raporu.xlsx"
    wb.save(xlsx_yol)

    # ---- Disavow dosyalari ----
    yeni = []
    gorulen = set()
    for k in kayitlar:
        if not str(k.get("aksiyon", "")).startswith("Disavow"):
            continue
        d = (k.get("domain") or "").lower().lstrip(".")
        if d.startswith("www."):
            d = d[4:]
        if d and d not in gorulen:
            gorulen.add(d)
            yeni.append(d)
    yeni.sort()

    mevcut = disavow_oku(a.mevcut_disavow) if a.mevcut_disavow else []
    mevcut_kume = set(mevcut)
    birlesik = mevcut + [d for d in yeni if d not in mevcut_kume]

    bugun = date.today().isoformat()
    basli = (
        f"# {a.marka} - disavow listesi\n"
        f"# Guncelleme: {bugun}\n"
        f"# Mevcut: {len(mevcut)} domain | Bu calismada eklenen: "
        f"{len(birlesik) - len(mevcut)} domain | Toplam: {len(birlesik)}\n"
    )
    (cikti / f"{ad}-disavow-BIRLESIK.txt").write_text(
        basli + "".join(f"domain:{d}\n" for d in birlesik), encoding="utf-8"
    )
    (cikti / f"{ad}-disavow-YENI.txt").write_text(
        f"# {a.marka} - bu calismada eklenen domainler ({bugun})\n"
        + "".join(f"domain:{d}\n" for d in yeni),
        encoding="utf-8",
    )

    print(json.dumps({
        "excel": str(xlsx_yol),
        "birlesik_disavow": str(cikti / f"{ad}-disavow-BIRLESIK.txt"),
        "yeni_disavow": str(cikti / f"{ad}-disavow-YENI.txt"),
        "toplam_satir": len(kayitlar),
        "yeni_disavow_domain": len(yeni),
        "mevcut_disavow_domain": len(mevcut),
        "birlesik_toplam": len(birlesik),
        "aksiyon_dagilimi": dict(Counter(k.get("aksiyon", "") for k in kayitlar)),
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
