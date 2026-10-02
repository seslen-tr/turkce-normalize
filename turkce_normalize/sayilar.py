"""
Türkçe sayı okuma — tek yer, tek kaynak.

Hem ``normalize.py`` hem ``cografi.py`` buna dayanır. Ayrı bir modülde
durmasının sebebi döngüsel bağımlılığı önlemek: coğrafi kurallar sayı
okumaya muhtaç, normalizasyon da coğrafi kurallara.

Bağımlılığı yoktur.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Union

BIRLER = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
ONLAR = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
GRUPLAR = ["", "bin", "milyon", "milyar", "trilyon", "katrilyon", "kentilyon"]

SIRA = {
    "bir": "birinci", "iki": "ikinci", "üç": "üçüncü", "dört": "dördüncü", "beş": "beşinci",
    "altı": "altıncı", "yedi": "yedinci", "sekiz": "sekizinci", "dokuz": "dokuzuncu",
    "on": "onuncu", "yirmi": "yirminci", "otuz": "otuzuncu", "kırk": "kırkıncı",
    "elli": "ellinci", "altmış": "altmışıncı", "yetmiş": "yetmişinci",
    "seksen": "sekseninci", "doksan": "doksanıncı", "yüz": "yüzüncü",
    "bin": "bininci", "milyon": "milyonuncu", "milyar": "milyarıncı", "sıfır": "sıfırıncı",
    "trilyon": "trilyonuncu", "katrilyon": "katrilyonuncu", "kentilyon": "kentilyonuncu",
}

#: Harflerin Türkçe okunuşu. Kısaltma, IBAN, pafta kodu ve alan adı
#: uzantısı ("tr" -> "te re") hep bu tabloyu kullanır.
HARF_OKUNUSU = {
    "A": "a", "B": "be", "C": "ce", "Ç": "çe", "D": "de", "E": "e", "F": "fe", "G": "ge",
    "Ğ": "yumuşak ge", "H": "he", "I": "ı", "İ": "i", "J": "je", "K": "ke", "L": "le",
    "M": "me", "N": "ne", "O": "o", "Ö": "ö", "P": "pe", "R": "re", "S": "se", "Ş": "şe",
    "T": "te", "U": "u", "Ü": "ü", "V": "ve", "Y": "ye", "Z": "ze",
    # Türk alfabesinde olmayan ama kısaltmalarda geçen harfler
    "Q": "kü", "W": "çift ve", "X": "iks",
}

Sayi = Union[int, float, str, Decimal]


def turkce_buyuk(s: str) -> str:
    """Türkçe kurallarıyla büyük harfe çevirir: "i" -> "İ", "ı" -> "I"."""
    return s.replace("i", "İ").replace("ı", "I").upper()


def turkce_kucuk(s: str) -> str:
    """Türkçe kurallarıyla küçük harfe çevirir: "İ" -> "i", "I" -> "ı"."""
    return s.replace("İ", "i").replace("I", "ı").lower()


def harf_oku(harf: str) -> str:
    """Tek harfi okur: "K" -> "ke", "ğ" -> "yumuşak ge". Bilinmeyen harf küçülür."""
    return HARF_OKUNUSU.get(turkce_buyuk(harf), turkce_kucuk(harf))


def _tamsayi(deger: Sayi) -> int:
    """JavaScript'teki ``Math.trunc(Number(x))`` karşılığı: sıfıra doğru keser."""
    if isinstance(deger, bool):
        return int(deger)
    if isinstance(deger, int):
        return deger
    if isinstance(deger, (float, Decimal)):
        return int(deger)
    metin = str(deger).strip()
    if not metin:
        return 0
    try:
        return int(Decimal(metin))
    except InvalidOperation as hata:
        raise ValueError(f"Sayı değil: {deger!r}") from hata


def _uclu(n: int) -> str:
    parcalar = []
    yuz, kalan = divmod(n, 100)
    if yuz == 1:
        parcalar.append("yüz")                      # "bir yüz" denmez
    elif yuz > 1:
        parcalar += [BIRLER[yuz], "yüz"]
    on, bir = divmod(kalan, 10)
    if on:
        parcalar.append(ONLAR[on])
    if bir:
        parcalar.append(BIRLER[bir])
    return " ".join(parcalar)


def sayi_oku(deger: Sayi) -> str:
    """Tam sayıyı Türkçe okur. 1000 -> "bin", 1000000 -> "bir milyon".

    Ondalıklı değer verilirse kesir kısmı atılır (sıfıra doğru keser).
    Kentilyondan büyük sayılar rakam rakam okunur.
    """
    n = _tamsayi(deger)
    if n == 0:
        return "sıfır"
    onek = "eksi " if n < 0 else ""
    n = mutlak = abs(n)

    gruplar = []
    while n > 0:
        n, kalan = divmod(n, 1000)
        gruplar.append(kalan)
    if len(gruplar) > len(GRUPLAR):
        # Adı olmayan büyüklük: sayı olarak okumak anlamsız, kod gibi okunur.
        return onek + rakamlari_tek_tek(str(mutlak))

    parcalar = []
    for i in range(len(gruplar) - 1, -1, -1):
        grup = gruplar[i]
        if grup == 0:
            continue
        if i == 1 and grup == 1:
            parcalar.append("bin")                  # "bir bin" denmez
        else:
            parcalar.append(_uclu(grup))
            if i > 0:
                parcalar.append(GRUPLAR[i])
    return onek + " ".join(parcalar)


def sira_oku(n: Sayi) -> str:
    """3 -> "üçüncü", 21 -> "yirmi birinci", 100 -> "yüzüncü"."""
    kelimeler = sayi_oku(n).split(" ")
    son = kelimeler[-1]
    kelimeler[-1] = SIRA.get(son, son + "ıncı")
    return " ".join(kelimeler)


def ondalik_oku(tam: Sayi, kesir: str) -> str:
    """3,14 -> "üç virgül on dört"; 3,05 -> "üç virgül sıfır beş".

    Sondaki sıfırlar atılır (3,50 -> "üç virgül beş"). Baştaki sıfırlar tek tek
    "sıfır" diye okunur; atılsalardı 3,05 ile 3,5 aynı duyulurdu.
    """
    temiz = re.sub(r"0+$", "", kesir) or "0"
    bas_sifir = len(temiz) - len(temiz.lstrip("0"))
    if bas_sifir and temiz.strip("0"):
        kesir_okunusu = " ".join(["sıfır"] * bas_sifir + [sayi_oku(temiz[bas_sifir:])])
    else:
        kesir_okunusu = sayi_oku(temiz)
    return f"{sayi_oku(tam)} virgül {kesir_okunusu}"


def rakamlari_tek_tek(s: str) -> str:
    """"1250" -> "bir iki beş sıfır". Kod, kimlik ve koordinat kesirleri için."""
    return " ".join(sayi_oku(k) for k in s if k.isdigit())


def sayiyi_coz(s: str) -> int:
    """"1.250" -> 1250 (binlik ayırıcı nokta ve boşluklar atılır)."""
    return int(re.sub(r"[.\s]", "", s) or "0")


#: Kalın ünlüler — ek uyumu için.
_KALIN = set("aıou")
_INCE = set("eiöü")
#: "Fıstıkçı Şahap" — bu ünsüzlerden sonra ekin "d"si "t" olur.
_SERT = set("çfhkpsşt")


def bulunma_eki(kelime: str) -> str:
    """Bulunma ekini ünlü ve ünsüz uyumuna göre seçer.

    "beş" -> "te", "altı" -> "da", "yüz" -> "de", "kırk" -> "ta".
    Kesirlerde ("dörtte üç") ve ölçekte ("milyonda bir") kullanılır.
    """
    kucuk = turkce_kucuk(kelime)
    unlu = next((h for h in reversed(kucuk) if h in _KALIN or h in _INCE), "e")
    sert = bool(kucuk) and kucuk[-1] in _SERT
    return ("t" if sert else "d") + ("a" if unlu in _KALIN else "e")
