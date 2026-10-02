"""
Coğrafi ve kadastral gösterimlerin okunuşu.

Genel amaçlı TTS servisleri bu gösterimleri bilmez: koordinatı ondalık sayı
sanır, ölçeği bölme işlemi sanır, pafta kodunu hecelemeye çalışır. CBS
uygulamasında bunlar her ekranda geçer.

En kritik olan koordinat çifti. Normalizasyonun ondalık kuralı
``39.9334, 32.8597`` gösterimini tek bir ondalık sayı sanıp
"üç yüz doksan dokuz bin üç yüz otuz dört virgül otuz iki" diye okur —
tamamen yanlış. Bu yüzden coğrafi kurallar sayı kurallarından ÖNCE çalışır.

Koordinat kesirleri rakam rakam okunur: "otuz dokuz virgül dokuz üç üç dört".
Sayı olarak okumak ("dokuz bin üç yüz otuz dört") hem uzun hem yanıltıcı.

``normalize()`` bu modülü varsayılan olarak kullanır; ``cografi=False`` ile
kapatılır. Tek başına da çağrılabilir: ``cografi_uygula(metin)``.
"""
from __future__ import annotations

import re
from typing import Optional

from .sayilar import bulunma_eki, harf_oku, rakamlari_tek_tek, sayi_oku, sira_oku

#: Yön harfleri — hem Türkçe (K/G/D/B) hem İngilizce (N/S/E/W) gösterim.
YONLER = {
    "K": "kuzey", "G": "güney", "D": "doğu", "B": "batı",
    "N": "kuzey", "S": "güney", "E": "doğu", "W": "batı",
    "KD": "kuzeydoğu", "KB": "kuzeybatı", "GD": "güneydoğu", "GB": "güneybatı",
    "NE": "kuzeydoğu", "NW": "kuzeybatı", "SE": "güneydoğu", "SW": "güneybatı",
}

#: Alan ve uzunluk birimleri.
#:
#: Hepsi rakamın ardından gelmek zorunda. "da" (dekar) aynı zamanda Türkçe bir
#: ektir — "bu da", "orada" — rakam şartı olmadan sözlüğe koymak felaket olur.
OLCU_BIRIMLERI = {
    "ha": "hektar",
    "da": "dekar",
    "km²": "kilometrekare", "km2": "kilometrekare",
    "cm²": "santimetrekare", "cm2": "santimetrekare",
    "mm²": "milimetrekare", "mm2": "milimetrekare",
    "km³": "kilometreküp", "km3": "kilometreküp",
}

# Yön harfinin ardından harf gelmemeli: "39°56' Doğu" içindeki "D" yön sanılmasın.
_YON = r"(?:([KGDBNSEW])(?![^\W\d_]))?"

_DMS = re.compile(
    r"(\d{1,3})\s*°\s*(\d{1,2})\s*['′]\s*(?:(\d{1,2}(?:[.,]\d+)?)\s*[\"″]\s*)?" + _YON
)
_ONDALIK_DERECE = re.compile(r"(\d{1,3})[.,](\d+)\s*°\s*" + _YON)
_KOORDINAT_CIFTI = re.compile(r"(?<![\w.-])(-?\d{1,3})\.(\d{4,})\s*,\s*(-?\d{1,3})\.(\d{4,})\b", re.ASCII)
_OLCEK = re.compile(r"\b1\s*[/:]\s*([\d.]{3,})\b", re.ASCII)
_PAFTA = re.compile(r"\b([A-ZĞÜŞİÖÇ])(\d{1,2})((?:-[a-d0-9]{1,3})+)\b", re.ASCII)
_EPSG = re.compile(r"\bEPSG\s*:?\s*(\d{4,6})\b", re.ASCII | re.IGNORECASE)
_UTM = re.compile(r"\bUTM\s*(\d{1,2})(?:\s*([NS]))?\b", re.ASCII | re.IGNORECASE)
_OLCU = [
    (re.compile(r"(?:(?<=\d)|(?<=\d\s))" + re.escape(kisa) + r"(?![^\W_])"), OLCU_BIRIMLERI[kisa])
    for kisa in sorted(OLCU_BIRIMLERI, key=len, reverse=True)
]


def _kesir_oku(kesir: str) -> str:
    """Ondalık kısmı rakam rakam okur: "9334" -> "dokuz üç üç dört"."""
    return rakamlari_tek_tek(kesir)


def _yon_oku(harf: Optional[str]) -> str:
    if not harf:
        return ""
    return " " + YONLER.get(harf.upper(), harf)


def _dms_oku(e: re.Match) -> str:
    """Derece-dakika-saniye: 39°56'12"K"""
    derece, dakika, saniye, yon = e.groups()
    parcalar = [f"{sayi_oku(derece)} derece", f"{sayi_oku(dakika)} dakika"]
    if saniye is not None:
        tam, _, kesir = saniye.replace(",", ".").partition(".")
        parcalar.append(
            f"{sayi_oku(tam)} virgül {_kesir_oku(kesir)} saniye" if kesir else f"{sayi_oku(tam)} saniye"
        )
    return " ".join(parcalar) + _yon_oku(yon)


def _pafta_oku(e: re.Match) -> str:
    """Pafta kodu — G22-b-14c-2d. Harf harf ve parça parça okunur."""
    harf, sayi, kuyruk = e.groups()
    parcalar = [harf_oku(harf), sayi_oku(sayi)]
    for p in filter(None, kuyruk.split("-")):
        for oge in re.findall(r"\d+|[a-d]", p):
            parcalar.append(sayi_oku(oge) if oge.isdigit() else harf_oku(oge))
    return " ".join(parcalar)


def _olcek_oku(e: re.Match) -> str:
    """Ölçek — 1/25.000 -> "yirmi beş binde bir", 1:1.000.000 -> "bir milyonda bir"."""
    payda = sayi_oku(e.group(1).replace(".", ""))
    return f"{payda}{bulunma_eki(payda)} bir"


def _utm_oku(e: re.Match) -> str:
    """UTM dilimi — "UTM 35N" -> "u te me otuz beşinci dilim kuzey".

    Metin zaten "dilim" kelimesiyle devam ediyorsa ("UTM 35 dilimi") tekrar eklenmez.
    """
    devami = e.string[e.end():].lstrip()
    dilim = "" if devami.startswith("dilim") else " dilim"
    return f"u te me {sira_oku(int(e.group(1)))}{dilim}{_yon_oku(e.group(2))}"


def cografi_uygula(metin: str) -> str:
    """Koordinat, ölçek, pafta, EPSG, UTM ve alan birimlerini okunur hale getirir."""
    m = metin

    # 1) Derece-dakika-saniye — 39°56'12"K / 39° 56' 12" K
    m = _DMS.sub(_dms_oku, m)

    # 2) Ondalık derece — 39.9334° K / 39,9334° K
    m = _ONDALIK_DERECE.sub(
        lambda e: f"{sayi_oku(e.group(1))} virgül {_kesir_oku(e.group(2))} derece{_yon_oku(e.group(3))}",
        m,
    )

    # 3) Derece işaretsiz koordinat çifti — 39.9334, 32.8597
    #    Dört ve üzeri ondalık basamak koordinat sayılır; para ve ölçüm bu kadar
    #    hassas yazılmaz. Enlem/boylam sırası CBS'de standarttır, adıyla okunur.
    m = _KOORDINAT_CIFTI.sub(
        lambda e: f"enlem {sayi_oku(e.group(1))} virgül {_kesir_oku(e.group(2))}, "
                  f"boylam {sayi_oku(e.group(3))} virgül {_kesir_oku(e.group(4))}",
        m,
    )

    # 4) Ölçek — 1/25.000 ve 1:25000 -> "yirmi beş binde bir"
    m = _OLCEK.sub(_olcek_oku, m)

    # 5) Pafta kodu — G22-b-14c-2d
    #    Harf harf ve parça parça okunur; hecelemeye çalışmak anlaşılmaz çıkarır.
    m = _PAFTA.sub(_pafta_oku, m)

    # 6) EPSG kodu — EPSG:5254. Kod, sayı değil; rakam rakam okunur.
    m = _EPSG.sub(lambda e: f"e pe es ge {rakamlari_tek_tek(e.group(1))}", m)

    # 7) UTM dilimi — UTM 35N
    m = _UTM.sub(_utm_oku, m)

    # 8) Alan ve uzunluk birimleri — yalnızca rakamın ardından
    for desen, okunus in _OLCU:
        m = desen.sub(okunus, m)

    return m
