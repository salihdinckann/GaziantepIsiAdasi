"""Geofabrik'in Türkiye OSM dosyasından Gaziantep ilçe ve mahalle sınırlarını çıkarır.

Girdi : data/ham/turkey-latest.osm.pbf  (download.geofabrik.de, 17 Kasım 2026 kopyası)
Çıktı : data/ara/mahalleler.gpkg  (+ göz kontrolü için mahalleler.png)
Çalıştırma (proje kökünden):  .venv\\Scripts\\python pipeline/01_mahalleler.py
"""

import sys
import time
from pathlib import Path

# Betik pipeline/ klasöründen çalıştığı için proje kökünü arama yoluna ekliyoruz.
KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))

import matplotlib.pyplot as plt  # noqa: E402
import pyogrio  # noqa: E402

from isi.bolge import ilceye_ata  # noqa: E402

PBF = KOK / "data" / "ham" / "turkey-latest.osm.pbf"
CIKTI = KOK / "data" / "ara" / "mahalleler.gpkg"

# Gaziantep ilini rahatça içine alan kutu: (batı, güney, doğu, kuzey) derece.
# Sadece bu kutuya değen nesneler okunur; Türkiye'nin geri kalanı atlanır.
GAZIANTEP_KUTU = (36.3, 36.6, 38.2, 37.7)


def main():
    t0 = time.time()
    print("OSM dosyası okunuyor (birkaç dakika sürebilir)...")
    # "multipolygons" katmanı: OSM'deki bütün alan nesneleri (sınırlar dahil)
    sinirlar = pyogrio.read_dataframe(
        PBF,
        layer="multipolygons",
        columns=["osm_id", "name", "admin_level", "boundary"],
        where="boundary = 'administrative' AND admin_level IN ('4', '6', '8')",
        bbox=GAZIANTEP_KUTU,
    )
    print(f"Okundu: {len(sinirlar)} idari sınır, {time.time() - t0:.0f} sn")

    # admin_level 4 = il. Gaziantep il sınırını bul.
    il = sinirlar[(sinirlar["admin_level"] == "4") & (sinirlar["name"] == "Gaziantep")]
    if len(il) != 1:
        raise RuntimeError(f"Gaziantep il sınırı bulunamadı ya da birden fazla: {len(il)}")
    il_sinir = il.geometry.iloc[0]

    # admin_level 6 = ilçe. İçindeki bir noktası il sınırına düşen ilçeleri tut
    # (kutuya giren komşu illerin ilçeleri böylece elenir).
    ilceler = sinirlar[sinirlar["admin_level"] == "6"]
    ilceler = ilceler[ilceler.representative_point().within(il_sinir)]
    ilceler = ilceler.rename(columns={"name": "ilce"})[["ilce", "geometry"]]
    print("Bulunan ilçeler:", sorted(ilceler["ilce"].tolist()))

    # admin_level 8 = mahalle. Her mahalleye kalıcı bir numara ver, ilçeye ata.
    mahalleler = sinirlar[sinirlar["admin_level"] == "8"]
    mahalleler = mahalleler.rename(columns={"name": "ad"})[["osm_id", "ad", "geometry"]]
    mahalleler = mahalleler.sort_values("osm_id")
    mahalleler.insert(0, "mahalle_id", range(1, len(mahalleler) + 1))
    mahalleler = ilceye_ata(mahalleler, ilceler)

    print("\nİlçe başına mahalle sayısı:")
    print(mahalleler["ilce"].value_counts())
    print("Toplam:", len(mahalleler), "| Adı boş:", mahalleler["ad"].isna().sum())

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    mahalleler.to_file(CIKTI, driver="GPKG")
    print("\nKaydedildi:", CIKTI)

    ax = mahalleler.plot(column="ilce", edgecolor="black", linewidth=0.1, legend=True, figsize=(10, 9))
    ax.set_title("Gaziantep OSM mahalle sınırları (resmî değil)")
    plt.savefig(CIKTI.with_suffix(".png"), dpi=150)


if __name__ == "__main__":
    main()