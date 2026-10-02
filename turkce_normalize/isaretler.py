"""
Satır içi duraklama işaretleri — SSML'in olmadığı yerde en yakın şey.

Birçok açık kaynak TTS modeli SSML desteklemez. Ama metni işaretlerden bölüp
parçaları ayrı üretir, aralarına sessizlik koyarsan duraklamayı kendin kurarsın::

    Sorgu tamamlandı. [dur:0.8] Toplam üç yüz kırk hektar.

``[dur]`` tek başına varsayılan duraklamadır.

Vurgu için ayrı bir işaret yok ve olmamalı: çoğu modelde vurgu parametresi
bulunmuyor, uydurulmuş bir işaret sessizce hiçbir şey yapardı.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

#: ``[dur]`` işaretinin varsayılan uzunluğu, saniye.
VARSAYILAN_DURAKLAMA = 0.45

#: İşaretlerin izin verilen üst sınırı — 5 saniyeden uzun sessizlik hata gibi duyulur.
EN_UZUN_DURAKLAMA = 5.0

# Python'da derlenmiş desenin durumu yoktur (JavaScript'teki ``lastIndex``
# tuzağı burada yaşanmaz); tek desen güvenle paylaşılır.
_ISARET = re.compile(r"\[dur(?::\s*(\d+(?:[.,]\d+)?))?\]", re.IGNORECASE)


@dataclass
class Parca:
    """Seslendirilecek bir parça."""

    #: Seslendirilecek metin.
    metin: str
    #: Bu parçadan sonra bırakılacak sessizlik, saniye.
    duraklama: float


def isaretleri_ayir(metin: str) -> List[Parca]:
    """Metni işaretlerden böler.

    Bilinmeyen bir işaret (``[vurgu]`` gibi) metinde bırakılır — model onu okur
    ve sen hatayı duyarsın. Sessizce silmek, işaretin çalıştığını sanmana yol açardı.
    """
    parcalar: List[Parca] = []
    son = 0

    for e in _ISARET.finditer(metin):
        oncesi = metin[son:e.start()].strip()
        uzunluk = (
            min(float(e.group(1).replace(",", ".")), EN_UZUN_DURAKLAMA)
            if e.group(1) else VARSAYILAN_DURAKLAMA
        )

        if oncesi:
            parcalar.append(Parca(oncesi, uzunluk))
        elif parcalar:
            # Art arda iki işaret: önceki duraklamayı uzat
            parcalar[-1].duraklama += uzunluk
        son = e.end()

    kalan = metin[son:].strip()
    if kalan:
        parcalar.append(Parca(kalan, 0))

    return parcalar if parcalar else [Parca(metin.strip(), 0)]


def isaret_var(metin: str) -> bool:
    """Metinde işaret var mı — tek üretimle geçilebilecek mi diye bakmak için."""
    return _ISARET.search(metin) is not None


def isaretleri_temizle(metin: str) -> str:
    """İşaretleri temizler. Altyazı metni için — okuyucu ``[dur:0.8]`` görmemeli."""
    return re.sub(r"\s{2,}", " ", _ISARET.sub(" ", metin)).strip()
