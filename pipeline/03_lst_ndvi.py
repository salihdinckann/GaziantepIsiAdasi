"""Her sahne için kent mahallelerinin yüzey sıcaklığı ve NDVI medyanını hesaplar.

Girdi : data/sonuc/sahneler.csv, data/ara/mahalleler.gpkg
Çıktı : data/ara/sahne/<sahne_id>.csv (+ .png göz kontrolü)
        data/ara/sahne_mahalle.csv     (bütün sahneler, uzun tablo)
Yarıda kalırsa tekrar çalıştır: biten sahneleri atlar.
"""

import os
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))

# Bulut dosyalarını okurken GDAL'ın gereksiz klasör listelemesini kapat (hızlandırır)
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"

import geopandas as gpd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import planetary_computer  # noqa: E402
import pystac_client  # noqa: E402
import rioxarray  # noqa: E402
from shapely.geometry import box  # noqa: E402

from isi.bolge import mahalle_istatistik  # noqa: E402
from isi.landsat import gecerli_maske, lst_c, ndvi, yansima  # noqa: E402

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
KENT_KUTU = (37.25, 36.98, 37.50, 37.15)
SAHNE_KLASOR = KOK / "data" / "ara" / "sahne"


def bant_oku(item, bant):
    """Bir bandın sadece kent kutusuna düşen parçasını indirir."""
    da = rioxarray.open_rasterio(item.assets[bant].href)
    return da.rio.clip_box(*KENT_KUTU, crs="EPSG:4326")


def sahne_isle(item, mahalleler):
    termal = bant_oku(item, "lwir11")
    red = bant_oku(item, "red").values[0]
    nir = bant_oku(item, "nir08").values[0]
    qa = bant_oku(item, "qa_pixel").values[0]
    if not (termal.shape[1:] == red.shape == nir.shape == qa.shape):
        raise ValueError(f"Bant boyutları farklı: {item.id}")

    gecerli = gecerli_maske(qa)
    lst = lst_c(termal.values[0])
    nd = ndvi(yansima(red), yansima(nir))
    tr, crs = termal.rio.transform(), termal.rio.crs

    a = mahalle_istatistik(lst, gecerli, tr, crs, mahalleler)
    b = mahalle_istatistik(nd, gecerli, tr, crs, mahalleler)
    tablo = a.rename(columns={"medyan": "lst_medyan"})
    tablo["ndvi_medyan"] = b["medyan"]
    return tablo, np.where(gecerli, lst, np.nan)


def main():
    sahneler = pd.read_csv(KOK / "data" / "sonuc" / "sahneler.csv")
    mahalleler = gpd.read_file(KOK / "data" / "ara" / "mahalleler.gpkg")
    mahalleler = mahalleler[mahalleler.within(box(*KENT_KUTU))]
    print(f"Kent kutusundaki mahalle: {len(mahalleler)}")

    katalog = pystac_client.Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)
    items = katalog.search(collections=["landsat-c2-l2"], ids=sahneler["sahne_id"].tolist()).items()
    SAHNE_KLASOR.mkdir(parents=True, exist_ok=True)

    for item in items:
        dosya = SAHNE_KLASOR / f"{item.id}.csv"
        if dosya.exists():
            print(f"atlandı (hazır): {item.id}")
            continue
        try:
            tablo, harita = sahne_isle(item, mahalleler)
        except Exception as hata:
            print(f"HATA {item.id}: {type(hata).__name__}: {hata} → tekrar çalıştırınca yeniden denenecek")
            continue
        tarih = item.datetime.date().isoformat()
        tablo.insert(0, "tarih", tarih)
        tablo.insert(0, "sahne_id", item.id)
        tablo.to_csv(dosya, index=False)

        plt.figure(figsize=(8, 6))
        plt.imshow(harita, cmap="inferno", vmin=25, vmax=55)
        plt.colorbar(label="Yüzey sıcaklığı (°C)")
        plt.title(f"{tarih}  {item.id}\nYüzey sıcaklığı (uydu), hava sıcaklığı değildir")
        plt.axis("off")
        plt.savefig(dosya.with_suffix(".png"), dpi=100)
        plt.close()

        olculen = tablo["lst_medyan"].notna().sum()
        print(f"{tarih} {item.id}: {olculen}/{len(tablo)} mahalle ölçüldü, "
              f"kent medyanı {tablo['lst_medyan'].median():.1f} °C")

    hepsi = pd.concat([pd.read_csv(f) for f in sorted(SAHNE_KLASOR.glob("*.csv"))])
    hepsi.to_csv(KOK / "data" / "ara" / "sahne_mahalle.csv", index=False)
    print(f"\nToplam {hepsi['sahne_id'].nunique()} sahne birleştirildi.")


if __name__ == "__main__":
    main()