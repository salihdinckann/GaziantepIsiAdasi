"""Mahalle sınırlarıyla ilgili mekânsal işlemler."""

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.features import rasterize

# UTM 37N: Gaziantep'i kapsayan, birimi METRE olan projeksiyon.
# Enlem/boylam (derece) ile alan hesaplanmaz; önce buna çeviriyoruz.
METRIK_CRS = "EPSG:32637"


def ilceye_ata(mahalleler: gpd.GeoDataFrame, ilceler: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Her mahalleyi, alanının en büyük kısmının düştüğü ilçeye atar.

    Hiçbir ilçeyle kesişmeyen mahalleler sonuçtan çıkarılır.
    Mahalle geometrileri kesilmez, olduğu gibi döner.
    """
    m = mahalleler[["mahalle_id", "geometry"]].to_crs(METRIK_CRS)
    i = ilceler[["ilce", "geometry"]].to_crs(METRIK_CRS)

    # Mahalle ile ilçenin örtüşen parçaları: her (mahalle, ilçe) çifti için bir satır
    parcalar = gpd.overlay(m, i, how="intersection")
    parcalar["alan_m2"] = parcalar.geometry.area

    # Her mahalle için en büyük parçayı tut
    en_buyuk = (
        parcalar.sort_values("alan_m2", ascending=False)
        .drop_duplicates("mahalle_id")
    )

    # Orijinal (kesilmemiş) mahalle tablosuna ilçe adını ekle.
    # how="inner": ilçesi bulunamayan mahalle düşer.
    return mahalleler.merge(en_buyuk[["mahalle_id", "ilce"]], on="mahalle_id", how="inner")

def mahalle_istatistik(
    deger: np.ndarray,
    gecerli: np.ndarray,
    transform,
    crs,
    mahalleler: gpd.GeoDataFrame,
    min_piksel: int = 20,
    min_gecerli_oran: float = 0.5,
) -> pd.DataFrame:
    """Her mahalle için geçerli piksellerin medyanını hesaplar.

    Geçerli piksel sayısı min_piksel'den azsa ya da mahallenin
    min_gecerli_oran'ından azı geçerliyse medyan NaN olur (güvenilmez ölçüm).
    """
    m = mahalleler.to_crs(crs)

    # Mahalle çokgenlerini rasterle aynı ızgaraya "boya": her piksel, merkezi
    # hangi mahalledeyse o mahallenin numarasını alır (0 = hiçbir mahalle).
    bolge = rasterize(
        zip(m.geometry, m["mahalle_id"]),
        out_shape=deger.shape,
        transform=transform,
        fill=0,
        dtype="int32",
    )

    tablo = pd.DataFrame({
        "mahalle_id": bolge.ravel(),
        "deger": deger.ravel(),
        "gecerli": gecerli.ravel() & ~np.isnan(deger.ravel()),
    })
    tablo = tablo[tablo["mahalle_id"] > 0]

    toplam = tablo.groupby("mahalle_id").size()
    iyi = tablo[tablo["gecerli"]]
    sayi = iyi.groupby("mahalle_id").size()
    medyan = iyi.groupby("mahalle_id")["deger"].median()

    sonuc = pd.DataFrame({"mahalle_id": m["mahalle_id"].to_numpy()})
    sonuc["toplam_piksel"] = sonuc["mahalle_id"].map(toplam).fillna(0).astype(int)
    sonuc["gecerli_piksel"] = sonuc["mahalle_id"].map(sayi).fillna(0).astype(int)
    sonuc["medyan"] = sonuc["mahalle_id"].map(medyan)

    yetersiz = (sonuc["gecerli_piksel"] < min_piksel) | (
        sonuc["gecerli_piksel"] < min_gecerli_oran * sonuc["toplam_piksel"]
    )
    sonuc.loc[yetersiz, "medyan"] = np.nan
    return sonuc.sort_values("mahalle_id").reset_index(drop=True)