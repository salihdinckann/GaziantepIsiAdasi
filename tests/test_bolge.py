import geopandas as gpd
import numpy as np
from rasterio.transform import from_origin
from shapely.geometry import box

from isi.bolge import ilceye_ata, mahalle_istatistik


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
    assert sonuc.iloc[0].geometry.equals(mahalleler.iloc[0].geometry)


def test_ilceye_ata_disarida():
    mahalleler = gpd.GeoDataFrame(
        {"mahalle_id": [1, 2], "ad": ["İçeride", "Dışarıda"]},
        geometry=[box(37.36, 37.01, 37.37, 37.02), box(38.0, 38.0, 38.01, 38.01)],
        crs="EPSG:4326",
    )
    sonuc = ilceye_ata(mahalleler, _ilceler())
    assert sonuc["ad"].tolist() == ["İçeride"]
    assert sonuc.iloc[0]["ilce"] == "B"


# --- mahalle_istatistik: 10x10 piksellik, 30 m çözünürlüklü yapay raster ---
X0, Y0, P = 300000, 4100000, 30  # sol üst köşe (UTM 37N, metre), piksel boyu
TRANSFORM = from_origin(X0, Y0, P, P)
CRS = "EPSG:32637"


def _raster():
    deger = np.full((10, 10), 40.0)
    deger[:, :5] = 30.0  # sol yarı 30 °C, sağ yarı 40 °C
    return deger


def _iki_mahalle():
    sol = box(X0, Y0 - 10 * P, X0 + 5 * P, Y0)           # sol 5 sütun = 50 piksel
    sag = box(X0 + 5 * P, Y0 - 10 * P, X0 + 10 * P, Y0)  # sağ 5 sütun = 50 piksel
    return gpd.GeoDataFrame({"mahalle_id": [1, 2]}, geometry=[sol, sag], crs=CRS)


def test_mahalle_istatistik_medyan():
    gecerli = np.ones((10, 10), dtype=bool)
    sonuc = mahalle_istatistik(_raster(), gecerli, TRANSFORM, CRS, _iki_mahalle())
    assert sonuc["mahalle_id"].tolist() == [1, 2]
    assert sonuc["medyan"].tolist() == [30.0, 40.0]
    assert sonuc["gecerli_piksel"].tolist() == [50, 50]
    assert sonuc["toplam_piksel"].tolist() == [50, 50]


def test_az_gecerli_piksel_nan():
    # Sol mahallenin %60'ı bulutlu (30/50 piksel) → güvenilmez, NaN olmalı
    gecerli = np.ones((10, 10), dtype=bool)
    gecerli[:6, :5] = False
    sonuc = mahalle_istatistik(_raster(), gecerli, TRANSFORM, CRS, _iki_mahalle())
    assert np.isnan(sonuc.loc[0, "medyan"])
    assert sonuc.loc[0, "gecerli_piksel"] == 20
    assert sonuc.loc[1, "medyan"] == 40.0


def test_cok_kucuk_mahalle_nan():
    # 2x2 = 4 piksellik mahalle, min_piksel=20'nin altında → NaN
    kucuk = gpd.GeoDataFrame(
        {"mahalle_id": [7]}, geometry=[box(X0, Y0 - 2 * P, X0 + 2 * P, Y0)], crs=CRS
    )
    sonuc = mahalle_istatistik(_raster(), np.ones((10, 10), dtype=bool), TRANSFORM, CRS, kucuk)
    assert sonuc.loc[0, "toplam_piksel"] == 4
    assert np.isnan(sonuc.loc[0, "medyan"])