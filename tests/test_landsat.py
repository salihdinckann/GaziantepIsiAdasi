import numpy as np
import pytest

from isi.landsat import gecerli_maske, lst_c, ndvi, yansima


def test_lst_c_donusum():
    sonuc = lst_c(np.array([44000]))
    assert sonuc[0] == pytest.approx(44000 * 0.00341802 + 149.0 - 273.15)  # ≈ 26.24 °C


def test_lst_c_dolgu_nan():
    # DN = 0, "ölçüm yok" (dolgu) demek; 0 °C sanılmamalı
    assert np.isnan(lst_c(np.array([0]))[0])


def test_yansima_donusum_ve_dolgu():
    sonuc = yansima(np.array([10000, 0]))
    assert sonuc[0] == pytest.approx(10000 * 0.0000275 - 0.2)  # 0.075
    assert np.isnan(sonuc[1])


def test_ndvi_bitki_ve_sifir_payda():
    sonuc = ndvi(np.array([0.05, 0.0]), np.array([0.45, 0.0]))
    assert sonuc[0] == pytest.approx(0.8)  # (0.45-0.05)/(0.45+0.05)
    assert np.isnan(sonuc[1])  # 0/0 → NaN, hata değil


def test_maske_bitleri():
    qa = np.array([
        21824,      # Landsat'ta tipik "açık, bulutsuz kara" değeri → geçerli
        0b1000000,  # sadece "açık" biti (6) → geçerli
        0b1,        # dolgu (0)
        0b10,       # genişletilmiş bulut (1)
        0b100,      # cirrus (2)
        0b1000,     # bulut (3)
        0b10000,    # bulut gölgesi (4)
        0b100000,   # kar (5)
    ])
    assert gecerli_maske(qa).tolist() == [True, True, False, False, False, False, False, False]