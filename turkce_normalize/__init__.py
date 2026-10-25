"""
turkce-normalize — TTS için Türkçe metin normalizasyonu.

Sayıları, tarihleri, saatleri, para tutarlarını, kısaltmaları, Roma
rakamlarını, kesirleri, e-posta ve web adreslerini Türkçe okunuşlarına
çevirir. Bağımlılığı yoktur.

    >>> from turkce_normalize import normalize
    >>> normalize("Toplantı 14:30'da, %18 KDV dahil 1.250,50 ₺.")
    'Toplantı on dört otuzda, yüzde on sekiz katma değer vergisi dahil bin iki yüz elli lira elli kuruş.'
"""
from .cografi import cografi_uygula
from .cumle import CumleAyirici, cumle_akisi, cumle_akisi_async, cumleleri_ayir
from .isaretler import (
    EN_UZUN_DURAKLAMA, VARSAYILAN_DURAKLAMA, Parca,
    isaret_var, isaretleri_ayir, isaretleri_temizle,
)
from .normalize import (
    BILINEN_KELIMELER, BIRIMLER, KELIME_GIBI_OKUNANLAR, KISALTMALAR, ROMA_KARA_LISTE,
    araliklari_oku, eposta_ve_adres_oku, kesirleri_oku, kisaltmalari_oku,
    normalize, roma_coz, simgeleri_oku,
)
from .sayilar import (
    HARF_OKUNUSU, bulunma_eki, harf_oku, ondalik_oku, rakamlari_tek_tek,
    sayi_oku, sayiyi_coz, sira_oku, turkce_buyuk, turkce_kucuk,
)
from .telaffuz import CBS_TERIMLERI, VARSAYILAN_SOZLUK, sozluk_birlestir, telaffuz_uygula

__version__ = "0.1.2"

__all__ = [
    "normalize",
    # sayılar
    "sayi_oku", "sira_oku", "ondalik_oku", "rakamlari_tek_tek", "sayiyi_coz",
    "bulunma_eki", "harf_oku", "turkce_buyuk", "turkce_kucuk", "HARF_OKUNUSU",
    # alt adımlar
    "cografi_uygula", "telaffuz_uygula", "eposta_ve_adres_oku", "simgeleri_oku",
    "kesirleri_oku", "araliklari_oku", "kisaltmalari_oku", "roma_coz",
    # sözlükler
    "KISALTMALAR", "BIRIMLER", "KELIME_GIBI_OKUNANLAR", "BILINEN_KELIMELER",
    "ROMA_KARA_LISTE", "CBS_TERIMLERI", "VARSAYILAN_SOZLUK", "sozluk_birlestir",
    # cümle ayırıcı
    "CumleAyirici", "cumleleri_ayir", "cumle_akisi", "cumle_akisi_async",
    # işaretler
    "Parca", "isaretleri_ayir", "isaret_var", "isaretleri_temizle",
    "VARSAYILAN_DURAKLAMA", "EN_UZUN_DURAKLAMA",
    "__version__",
]
