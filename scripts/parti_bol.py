#!/usr/bin/env python3
"""Inceleme listesini Sonnet alt ajanlarina dagitilmak uzere partilere boler.

Kullanim:
    python parti_bol.py --girdi <klasor>/siniflandirma.json --out <klasor>/partiler \
        [--boyut 70]

Partileri rastgele degil ANLAMLI boler:
  - Ayni aga ait domainler (ayni baslik imzasi) ayni partide toplanir; alt ajan agi
    bir kez tanir, kalanini hizla siniflandirir.
  - Yuksek DR'li domainler kendi partisinde toplanir; bunlar en dikkatli bakilmasi
    gerekenlerdir ve alt ajanin dikkatini dagitmamak gerekir.

Cikti: parti-1.json, parti-2.json, ... + parti_ozet.json
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

YUKSEK_DR = 30
YUKSEK_TRAFIK = 10000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--girdi", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boyut", type=int, default=70,
                    help="Parti basina domain sayisi (varsayilan 70)")
    a = ap.parse_args()

    kayitlar = json.loads(Path(a.girdi).read_text(encoding="utf-8"))
    incelenecek = [k for k in kayitlar if k.get("ziyaret_et")]

    # Yuksek etkili olanlari ayir - kendi partilerinde toplanacaklar
    yuksek, normal = [], []
    for k in incelenecek:
        if (k.get("dr") or 0) >= YUKSEK_DR or (k.get("trafik_domain") or 0) >= YUKSEK_TRAFIK:
            yuksek.append(k)
        else:
            normal.append(k)

    # Normal olanlari baslik imzasina gore grupla ki ayni ag birlikte kalsin
    gruplar = defaultdict(list)
    for k in normal:
        anahtar = str(k.get("baslik") or "")[:60] or f"__tekil__{k['domain']}"
        gruplar[anahtar].append(k)

    # Buyuk gruplar once: ag halindekiler partileri doldursun
    sirali = sorted(gruplar.values(), key=len, reverse=True)

    partiler, mevcut = [], []
    for grup in sirali:
        # Tek bir ag parti boyutunu asiyorsa kendi partilerine bolunur
        if len(grup) >= a.boyut:
            if mevcut:
                partiler.append(mevcut)
                mevcut = []
            for i in range(0, len(grup), a.boyut):
                partiler.append(grup[i:i + a.boyut])
            continue
        if len(mevcut) + len(grup) > a.boyut:
            partiler.append(mevcut)
            mevcut = []
        mevcut.extend(grup)
    if mevcut:
        partiler.append(mevcut)

    # Yuksek etkili olanlar en basta, kendi partilerinde
    yuksek_partiler = [yuksek[i:i + a.boyut] for i in range(0, len(yuksek), a.boyut)]
    partiler = yuksek_partiler + partiler

    cikti = Path(a.out)
    cikti.mkdir(parents=True, exist_ok=True)
    ozet = []
    for i, parti in enumerate(partiler, start=1):
        yol = cikti / f"parti-{i}.json"
        yol.write_text(json.dumps(parti, ensure_ascii=False, indent=1), encoding="utf-8")
        ozet.append({
            "parti": i,
            "dosya": str(yol),
            "karar_dosyasi": str(cikti / f"parti-{i}-karar.json"),
            "domain": len(parti),
            "yuksek_etkili": i <= len(yuksek_partiler),
            "dr_araligi": [
                min((k.get("dr") or 0) for k in parti),
                max((k.get("dr") or 0) for k in parti),
            ],
            "ornek_domainler": [k["domain"] for k in parti[:3]],
        })

    (cikti / "parti_ozet.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(json.dumps({
        "incelenecek_toplam": len(incelenecek),
        "yuksek_etkili": len(yuksek),
        "parti_sayisi": len(partiler),
        "parti_boyutu": a.boyut,
        "partiler": ozet,
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
