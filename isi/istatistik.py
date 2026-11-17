"""Dur/devam kontrolleri ve ilişki analizi için istatistik fonksiyonları."""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr


def gunluk_birlestir(uzun: pd.DataFrame) -> pd.DataFrame:
    """Aynı gün birden fazla sahne varsa, her mahalle için en iyi ölçümü seçer.

    Önce ölçümü olan (NaN olmayan), sonra geçerli pikseli çok olan sahne tercih edilir.
    """
    sirali = uzun.assign(_olcum=uzun["lst_medyan"].notna()).sort_values(
        ["_olcum", "gecerli_piksel"], ascending=False
    )
    return (
        sirali.drop_duplicates(["tarih", "mahalle_id"])
        .drop(columns="_olcum")
        .sort_values(["tarih", "mahalle_id"])
        .reset_index(drop=True)
    )


def sira_tutarliligi(uzun: pd.DataFrame, deger: str = "lst_medyan", min_ortak: int = 30):
    """Gün çiftleri arasında mahalle sıralamasının Spearman korelasyonu.

    Dönüş: (tarih × tarih matrisi, çiftlerin medyanı). Ortak ölçülen mahalle
    sayısı min_ortak'tan az olan çiftler NaN bırakılır ve medyana katılmaz.
    """
    genis = uzun.pivot(index="mahalle_id", columns="tarih", values=deger)
    matris = genis.corr(method="spearman", min_periods=min_ortak)
    ust_ucgen = matris.where(np.triu(np.ones(matris.shape, dtype=bool), k=1))
    return matris, float(np.nanmedian(ust_ucgen.to_numpy()))


def iliski(x: pd.Series, y: pd.Series) -> dict:
    """x ile y arasındaki ilişki: Spearman ρ ve %95 güven aralıklı OLS eğimi."""
    veri = pd.DataFrame({"x": x, "y": y}).dropna()
    rho, p = spearmanr(veri["x"], veri["y"])
    model = sm.OLS(veri["y"], sm.add_constant(veri["x"])).fit()
    alt, ust = model.conf_int(alpha=0.05).loc["x"]
    return {
        "spearman_rho": float(rho), "p": float(p),
        "egim": float(model.params["x"]), "egim_alt": float(alt), "egim_ust": float(ust),
        "n": int(len(veri)),
    }