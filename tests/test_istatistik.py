import numpy as np
import pandas as pd

from isi.istatistik import gunluk_birlestir, iliski, sira_tutarliligi


def _uzun(gunler: dict) -> pd.DataFrame:
    """{tarih: [mahalle 1, 2, ... değerleri]} → uzun tablo."""
    satirlar = []
    for tarih, degerler in gunler.items():
        for i, d in enumerate(degerler, start=1):
            satirlar.append({"tarih": tarih, "mahalle_id": i, "lst_medyan": d})
    return pd.DataFrame(satirlar)


def test_tutarlilik_ayni_sira():
    x = np.arange(40, dtype=float)
    uzun = _uzun({"g1": x, "g2": 2 * x + 5, "g3": x + 10})  # ölçek farklı, sıra aynı
    matris, medyan = sira_tutarliligi(uzun)
    assert matris.shape == (3, 3)
    assert medyan == 1.0


def test_tutarlilik_az_ortak_atlanir():
    x = np.arange(40, dtype=float)
    g3 = np.full(40, np.nan)
    g3[:10] = -x[:10]  # sadece 10 ortak mahalle, ters sıra
    matris, medyan = sira_tutarliligi(_uzun({"g1": x, "g2": x, "g3": g3}), min_ortak=30)
    assert np.isnan(matris.loc["g1", "g3"])  # 10 < 30 → hesaba katılmaz
    assert medyan == 1.0


def test_iliski_negatif():
    rng = np.random.default_rng(0)
    x = pd.Series(rng.uniform(0, 0.6, 200))
    y = pd.Series(-10 * x + rng.normal(0, 1, 200))
    sonuc = iliski(x, y)
    assert sonuc["n"] == 200
    assert sonuc["spearman_rho"] < 0
    assert sonuc["egim_alt"] < -10 < sonuc["egim_ust"] < 0


def test_iliski_nan_atlanir():
    x = pd.Series([0.1, 0.2, np.nan, 0.4, 0.5])
    y = pd.Series([5.0, 4.0, 3.0, np.nan, 1.0])
    assert iliski(x, y)["n"] == 3


def test_gunluk_birlestir_iyi_olani_secer():
    uzun = pd.DataFrame({
        "sahne_id": ["A", "A", "B", "B"],
        "tarih": ["g1"] * 4,
        "mahalle_id": [1, 2, 1, 2],
        "lst_medyan": [30.0, np.nan, 31.0, 41.0],
        "gecerli_piksel": [90, 99, 50, 80],
    })
    sonuc = gunluk_birlestir(uzun)
    assert len(sonuc) == 2
    # Mahalle 1: A'da daha çok piksel → A. Mahalle 2: A'da NaN → ölçülmüş olan B
    assert sonuc.set_index("mahalle_id")["sahne_id"].to_dict() == {1: "A", 2: "B"}