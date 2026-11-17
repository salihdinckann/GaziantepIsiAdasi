"""Landsat Collection 2 Level-2 ham değerlerini fiziksel birimlere çevirir."""

import numpy as np

# USGS Landsat C2 L2 katsayıları
LST_CARPAN, LST_EK = 0.00341802, 149.0   # termal: DN → Kelvin
SR_CARPAN, SR_EK = 0.0000275, -0.2       # yansıma: DN → 0–1 oranı
KELVIN = 273.15

# QA_PIXEL'de biri bile 1 ise pikseli atıyoruz:
# 0 dolgu, 1 genişletilmiş bulut, 2 cirrus, 3 bulut, 4 bulut gölgesi, 5 kar
KOTU_BITLER = (0, 1, 2, 3, 4, 5)


def lst_c(dn: np.ndarray) -> np.ndarray:
    """Termal bant DN → yüzey sıcaklığı (°C). DN=0 (dolgu) → NaN."""
    dn = np.asarray(dn, dtype="float64")
    sonuc = dn * LST_CARPAN + LST_EK - KELVIN
    sonuc[dn == 0] = np.nan
    return sonuc


def yansima(dn: np.ndarray) -> np.ndarray:
    """Optik bant DN → yüzey yansıması (0–1). DN=0 (dolgu) → NaN."""
    dn = np.asarray(dn, dtype="float64")
    sonuc = dn * SR_CARPAN + SR_EK
    sonuc[dn == 0] = np.nan
    return sonuc


def ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Bitki örtüsü indeksi. Payda 0 ise NaN (sıfıra bölme hatası yerine)."""
    payda = nir + red
    with np.errstate(divide="ignore", invalid="ignore"):
        sonuc = (nir - red) / payda
    return np.where(payda == 0, np.nan, sonuc)


def gecerli_maske(qa: np.ndarray) -> np.ndarray:
    """Kötü bitlerin hiçbiri açık değilse True (piksel kullanılabilir)."""
    kotu = 0
    for bit in KOTU_BITLER:
        kotu |= 1 << bit  # 1 << 3 = 0b1000: sadece 3. biti açık bir sayı
    return (np.asarray(qa, dtype="uint16") & kotu) == 0