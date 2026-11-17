import geopandas as gpd
from shapely.geometry import box

from isi.bolge import ilceye_ata


def _ilceler():
    # Gaziantep civarında, yan yana iki kare "ilçe" (boylam, enlem; EPSG:4326)
    return gpd.GeoDataFrame(
        {"ilce": ["A", "B"]},
        geometry=[box(37.30, 37.00, 37.35, 37.05), box(37.35, 37.00, 37.40, 37.05)],
        crs="EPSG:4326",
    )


def test_ilceye_ata_alan_coklugu():
    # Mahalle 37.315–37.365 boylamları arasında: %70'i A'da, %30'u B'de
    mahalleler = gpd.GeoDataFrame(
        {"mahalle_id": [1], "ad": ["Sınırdaki"]},
        geometry=[box(37.315, 37.01, 37.365, 37.02)],
        crs="EPSG:4326",
    )
    sonuc = ilceye_ata(mahalleler, _ilceler())
    assert len(sonuc) == 1
    assert sonuc.iloc[0]["ilce"] == "A"
    # Geometri kesilmemeli: mahalle sınırı aynen korunur
    assert sonuc.iloc[0].geometry.equals(mahalleler.iloc[0].geometry)


def test_ilceye_ata_disarida():
    # Hiçbir ilçeyle kesişmeyen mahalle sonuçtan çıkarılır
    mahalleler = gpd.GeoDataFrame(
        {"mahalle_id": [1, 2], "ad": ["İçeride", "Dışarıda"]},
        geometry=[box(37.36, 37.01, 37.37, 37.02), box(38.0, 38.0, 38.01, 38.01)],
        crs="EPSG:4326",
    )
    sonuc = ilceye_ata(mahalleler, _ilceler())
    assert sonuc["ad"].tolist() == ["İçeride"]
    assert sonuc.iloc[0]["ilce"] == "B"
