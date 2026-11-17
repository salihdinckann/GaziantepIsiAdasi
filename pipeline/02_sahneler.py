"""Kent merkezini kapsayan 2025 yazı Landsat sahnelerini listeler.

Çıktı: data/sonuc/sahneler.csv  (her rakamın izlenebileceği sahne kaydı)
Çalıştırma:  .venv\\Scripts\\python pipeline/02_sahneler.py
"""

from pathlib import Path

import pandas as pd
import pystac_client

KOK = Path(__file__).resolve().parents[1]
CIKTI = KOK / "data" / "sonuc" / "sahneler.csv"

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
KENT_KUTU = [37.25, 36.98, 37.50, 37.15]  # batı, güney, doğu, kuzey
TARIH = "2025-06-01/2025-08-31"
MAKS_BULUT = 10  # sahnenin tamamındaki bulut yüzdesi


def main():
    katalog = pystac_client.Client.open(STAC_URL)
    arama = katalog.search(
        collections=["landsat-c2-l2"],
        bbox=KENT_KUTU,
        datetime=TARIH,
        query={
            "eo:cloud_cover": {"lt": MAKS_BULUT},
            "platform": {"in": ["landsat-8", "landsat-9"]},
        },
    )
    satirlar = []
    for item in arama.items():
        p = item.properties
        satirlar.append({
            "sahne_id": item.id,
            "tarih": item.datetime.date().isoformat(),
            "saat_utc": item.datetime.strftime("%H:%M"),
            "platform": p["platform"],
            "path_row": f"{p['landsat:wrs_path']}/{p['landsat:wrs_row']}",
            "bulut": p["eo:cloud_cover"],
        })

    tablo = pd.DataFrame(satirlar).sort_values(["tarih", "path_row"])
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    tablo.to_csv(CIKTI, index=False, encoding="utf-8")
    print(tablo.to_string(index=False))
    print(f"\n{len(tablo)} sahne, {tablo['tarih'].nunique()} farklı gün → {CIKTI}")


if __name__ == "__main__":
    main()