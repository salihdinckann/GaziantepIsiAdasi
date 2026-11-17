"""Deneme: sadece yapılaşmış (ESA WorldCover sınıf 50) pikselleri sayınca NDVI–LST ilişkisi."""
import os, sys
from pathlib import Path
KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"

import geopandas as gpd, numpy as np, pandas as pd, planetary_computer, pystac_client, rioxarray
from rasterio.enums import Resampling
from rasterio.features import rasterize
from shapely.geometry import box
from isi.bolge import mahalle_istatistik
from isi.landsat import gecerli_maske, lst_c, ndvi, yansima
from isi.istatistik import iliski

KUTU = (37.25, 36.98, 37.50, 37.15)
TAM = ["20250611", "20250619", "20250627", "20250705", "20250729", "20250814", "20250822"]
kat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=planetary_computer.sign_inplace)

m = gpd.read_file(KOK / "data/ara/mahalleler.gpkg")
m = m[m.within(box(*KUTU))]

wc_items = list(kat.search(collections=["esa-worldcover"], bbox=list(KUTU)).items())
wc_item = sorted(wc_items, key=lambda i: i.properties.get("start_datetime") or "")[-1]
print("WorldCover:", wc_item.id, len(wc_items), "kalem")
wc = rioxarray.open_rasterio(wc_item.assets["map"].href).rio.clip_box(*KUTU, crs="EPSG:4326")

def oku(item, b):
    return rioxarray.open_rasterio(item.assets[b].href).rio.clip_box(*KUTU, crs="EPSG:4326")

items = list(kat.search(collections=["landsat-c2-l2"], bbox=list(KUTU), datetime="2025-06-01/2025-08-31",
                        query={"landsat:wrs_path": {"eq": "174"}}).items())
items = [i for i in items if i.id.split("_")[3] in TAM]
print("Landsat sahne:", len(items))

tablolar, oranlar = [], None
for it in items:
    t = oku(it, "lwir11")
    red, nir, qa = (oku(it, b).values[0] for b in ("red", "nir08", "qa_pixel"))
    if oranlar is None:  # WorldCover sınıf oranlarını Landsat 30 m ızgarasına bir kez taşı
        oranlar = {}
        for ad, sinif in [("yapi", 50), ("agac", 10), ("ciplak", 60), ("cayir", 30), ("tarim", 40)]:
            maske = wc.copy(data=(wc.values == sinif).astype("float32"))
            oranlar[ad] = maske.rio.reproject_match(t, resampling=Resampling.average).values[0]
        bolge = rasterize(zip(m.to_crs(t.rio.crs).geometry, m["mahalle_id"]), out_shape=t.shape[1:],
                          transform=t.rio.transform(), fill=0, dtype="int32")
    yapili = gecerli_maske(qa) & (oranlar["yapi"] >= 0.5)
    lst, nd = lst_c(t.values[0]), ndvi(yansima(red), yansima(nir))
    a = mahalle_istatistik(lst, yapili, t.rio.transform(), t.rio.crs, m, min_piksel=20, min_gecerli_oran=0)
    b = mahalle_istatistik(nd, yapili, t.rio.transform(), t.rio.crs, m, min_piksel=20, min_gecerli_oran=0)
    a["ndvi"] = b["medyan"]; a["tarih"] = it.id.split("_")[3]
    tablolar.append(a.rename(columns={"medyan": "lst"}))
    print(it.id, "yapılaşmış piksel:", int(yapili.sum()))

uzun = pd.concat(tablolar)
mh = uzun.groupby("mahalle_id").agg(lst=("lst", "median"), ndvi=("ndvi", "median"), yapi_piksel=("gecerli_piksel", "median"))
# Mahalle başına arazi örtüsü oranları (30 m ızgarada ortalama)
oz = pd.DataFrame({"mahalle_id": bolge.ravel(), **{k: v.ravel() for k, v in oranlar.items()}})
oz = oz[oz.mahalle_id > 0].groupby("mahalle_id").mean()
mh = mh.join(oz).join(m.set_index("mahalle_id")[["ad", "ilce"]])
mh.to_csv(KOK / "data/ara/yapilasmis_deneme.csv")

ok = mh.dropna(subset=["lst", "ndvi"])
print(f"\nYapılaşmış piksel ≥20 olan mahalle: {len(ok)}/{len(mh)}")
for x in ["ndvi", "agac"]:
    s = iliski(ok[x], ok["lst"])
    print(f"{x:5s}: rho={s['spearman_rho']:+.2f} p={s['p']:.1e}  eğim/0.1={s['egim']/10:+.2f} [{s['egim_alt']/10:+.2f},{s['egim_ust']/10:+.2f}] n={s['n']}")
print("\nTüm piksel LST ile çıplak arazi oranı:")
eski = pd.read_csv(KOK / "data/ara/sahne_mahalle.csv")
eski = eski[eski.tarih.str.replace("-", "").isin(TAM)].groupby("mahalle_id").lst_medyan.median()
s = iliski(mh["ciplak"] + mh["cayir"], eski.reindex(mh.index))
print(f"çıplak+çayır oranı vs LST: rho={s['spearman_rho']:+.2f}")
print("\nYapılaşmışta en sıcak 10:")
print(ok.nlargest(10, "lst")[["ad", "lst", "ndvi", "agac", "yapi"]].round(2).to_string())
print("\nYapılaşmışta en serin 10:")
print(ok.nsmallest(10, "lst")[["ad", "lst", "ndvi", "agac", "yapi"]].round(2).to_string())
