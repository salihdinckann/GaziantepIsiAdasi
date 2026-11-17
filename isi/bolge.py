"""Mahalle sınırlarıyla ilgili mekânsal işlemler."""

import geopandas as gpd

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