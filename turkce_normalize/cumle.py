"""
Türkçe cümle ayırıcı — LLM token akışını cümle cümle TTS'e vermek için.

Doğallık hissinin kaynağı bu: cevabın tamamı bitmeden ilk cümle
seslendirilmeye başlar. Kısaltmalarda ve tarihlerde yanlış bölme yapmaz.

    ayirici = CumleAyirici()
    for parca in llm_akisi:
        for cumle in ayirici.push(parca):
            seslendir(cumle)
    for cumle in ayirici.flush():
        seslendir(cumle)
"""
from __future__ import annotations

import re
from typing import AsyncIterable, AsyncIterator, Iterable, Iterator, List

from .sayilar import turkce_kucuk

#: Ardından nokta gelince cümleyi bitirmeyen kısaltmalar (küçük harfle).
KISALTMALAR = {
    "dr", "prof", "doç", "av", "sn", "sayın", "no", "tel", "vb", "vs", "vd",
    "bkz", "örn", "ltd", "şti", "mah", "cad", "sok", "apt", "bl", "kat",
}

_SONLANDIRICI = re.compile(r"[.!?…]+[\s\"'»)]*")
_KISALTMA_SONU = re.compile(r"([^\W_]+)\.\s*$")
_SAYI_SONU = re.compile(r"\d\.\s*$")

_PENCERE = 64

#: Bundan kısa cümleler tek başına gönderilmez, sonrakiyle birleşir ("Evet.").
MIN_UZUNLUK = 12


class CumleAyirici:
    """Akış halinde cümle üretir.

    LLM'den gelen token'ları ``push()`` ile besle, dönen listedeki cümleleri
    hemen TTS kuyruğuna at. Akış bitince ``flush()`` çağır.
    """

    def __init__(self, min_uzunluk: int = MIN_UZUNLUK) -> None:
        self.min_uzunluk = min_uzunluk
        self._tampon = ""

    def push(self, parca: str) -> List[str]:
        self._tampon += parca
        cikan: List[str] = []
        ara = 0

        while True:
            eslesme = _SONLANDIRICI.search(self._tampon, ara)
            if not eslesme:
                break

            son = eslesme.end()
            aday = self._tampon[:son]
            # Yalnızca adayın sonu incelenir; bütün tamponu her noktada baştan
            # taramak uzun metinde işi ikinci dereceden yavaşlatır.
            kuyruk = aday[-_PENCERE:]
            kisaltma = _KISALTMA_SONU.search(kuyruk)
            if kisaltma is not None and kisaltma.start() == 0 and aday[-_PENCERE - 1:-_PENCERE].isalnum():
                kisaltma = None      # pencereye sığmayan uzun kelime, kısaltma olamaz

            bekle = (
                (kisaltma is not None and turkce_kucuk(kisaltma.group(1)) in KISALTMALAR)  # "Dr. Ayşe"
                or _SAYI_SONU.search(kuyruk) is not None                                   # "15.03.2026"
                or len(aday.strip()) < self.min_uzunluk                                    # "Evet."
            )

            if bekle:
                ara = son            # bu noktayı atla, bir sonrakine bak
                continue

            cikan.append(aday.strip())
            self._tampon = self._tampon[son:]
            ara = 0
        return cikan

    def flush(self) -> List[str]:
        """Akış bittiğinde tamponda kalanı verir."""
        kalan = self._tampon.strip()
        self._tampon = ""
        return [kalan] if kalan else []


def cumleleri_ayir(metin: str, min_uzunluk: int = MIN_UZUNLUK) -> List[str]:
    """Tek parça metni cümlelere böler."""
    ayirici = CumleAyirici(min_uzunluk)
    return ayirici.push(metin) + ayirici.flush()


def cumle_akisi(akis: Iterable[str], min_uzunluk: int = MIN_UZUNLUK) -> Iterator[str]:
    """Parça akışını (ör. LLM stream'i) cümle akışına çevirir."""
    ayirici = CumleAyirici(min_uzunluk)
    for parca in akis:
        yield from ayirici.push(parca)
    yield from ayirici.flush()


async def cumle_akisi_async(akis: AsyncIterable[str], min_uzunluk: int = MIN_UZUNLUK) -> AsyncIterator[str]:
    """``cumle_akisi`` ile aynı, async akışlar için."""
    ayirici = CumleAyirici(min_uzunluk)
    async for parca in akis:
        for cumle in ayirici.push(parca):
            yield cumle
    for cumle in ayirici.flush():
        yield cumle
