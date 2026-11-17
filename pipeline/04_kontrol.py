"""Dur/devam kontrolleri: (a) günler arası sıra tutarlılığı, (b) yeşil–sıcaklık ilişkisi.

Girdi : data/ara/sahne_mahalle.csv, data/ara/mahalleler.gpkg
Çıktı : data/ara/kontrol.json, tutarlilik.png, yesil_sicaklik.png
"""

import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))

import geopandas as gpd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from isi.istatistik import gunluk_birlestir, iliski, sira_tutarliligi  # noqa: E402

ARA = KOK / "data" / "ara"
# Kentin tamamını gören günler (Landsat yörünge 174)
TAM_GUNLER = ["2025-06-11", "2025-06-19", "2025-06-27", "2025-07-05",
              "2025-07-29", "2025-08-14", "2025-08-22"]
ESIK_RHO = 0.7


def main():
    gunluk = gunluk_birlestir(pd.read_csv(ARA / "sahne_mahalle.csv"))

    # --- (a) Tutarlılık ---
    matris, medyan_tum = sira_tutarliligi(gunluk)
    _, medyan_tam = sira_tutarliligi(gunluk[gunluk["tarih"].isin(TAM_GUNLER)])
    ust = matris.where(np.triu(np.ones(matris.shape, dtype=bool), k=1)).stack()
    print("(a) GÜNLER ARASI SIRA TUTARLILIĞI (Spearman ρ)")
    print(f"    19 gün, {len(ust)} çift: medyan {medyan_tum:.2f}, en düşük {ust.min():.2f}")
    print(f"    7 tam gün:             medyan {medyan_tam:.2f}")
    print(f"    Ölçüt medyan ≥ {ESIK_RHO}: {'GEÇTİ' if medyan_tum >= ESIK_RHO else 'KALDI'}")

    plt.figure(figsize=(9, 7))
    plt.imshow(matris, vmin=0, vmax=1, cmap="viridis")
    plt.colorbar(label="Spearman ρ")
    plt.xticks(range(len(matris)), [t[5:] for t in matris.columns], rotation=90)
    plt.yticks(range(len(matris)), [t[5:] for t in matris.index])
    plt.title("Mahalle sıcaklık sıralamasının günler arası tutarlılığı")
    plt.tight_layout()
    plt.savefig(ARA / "tutarlilik.png", dpi=120)
    plt.close()

    # --- (b) Yeşil–sıcaklık ilişkisi (7 tam günün mahalle medyanı) ---
    tam = gunluk[gunluk["tarih"].isin(TAM_GUNLER)]
    mahalle = tam.groupby("mahalle_id").agg(
        lst=("lst_medyan", "median"), ndvi=("ndvi_medyan", "median"), gun=("lst_medyan", "count")
    )
    sonuc = iliski(mahalle["ndvi"], mahalle["lst"])
    print("\n(b) YEŞİL (NDVI) – YÜZEY SICAKLIĞI İLİŞKİSİ")
    print(f"    n={sonuc['n']} mahalle, Spearman ρ={sonuc['spearman_rho']:.2f} (p={sonuc['p']:.1e})")
    print(f"    NDVI 0.1 artınca: {sonuc['egim'] / 10:+.2f} °C "
          f"[%95 GA {sonuc['egim_alt'] / 10:+.2f}, {sonuc['egim_ust'] / 10:+.2f}]")
    print(f"    Ölçüt eğim üst sınırı < 0: {'GEÇTİ' if sonuc['egim_ust'] < 0 else 'KALDI'}")

    plt.figure(figsize=(7, 5))
    plt.scatter(mahalle["ndvi"], mahalle["lst"], s=14)
    plt.xlabel("Mahalle medyan NDVI (yeşillik)")
    plt.ylabel("Mahalle medyan yüzey sıcaklığı (°C)")
    plt.title(f"{sonuc['n']} kent mahallesi, 7 yaz günü\nYüzey sıcaklığı (uydu), hava sıcaklığı değildir")
    plt.tight_layout()
    plt.savefig(ARA / "yesil_sicaklik.png", dpi=120)
    plt.close()

    # En sıcak 10 mahalle: kenardaki boş araziler mi, yoğun yerleşim mi?
    adlar = gpd.read_file(ARA / "mahalleler.gpkg")[["mahalle_id", "ad", "ilce"]]
    sicak = mahalle.reset_index().merge(adlar, on="mahalle_id").nlargest(10, "lst")
    print("\nEn sıcak 10 mahalle:")
    print(sicak[["ad", "ilce", "lst", "ndvi", "gun"]].round(2).to_string(index=False))

    json.dump({"tutarlilik_medyan_19gun": medyan_tum, "tutarlilik_medyan_7gun": medyan_tam,
               "tutarlilik_en_dusuk": float(ust.min()), "yesil_sicaklik": sonuc},
              open(ARA / "kontrol.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()