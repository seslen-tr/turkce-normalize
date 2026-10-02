"""
Telaffuz sözlüğü — modelin yanlış okuduğu terimleri yazılışıyla düzeltir.

Model Türkçe fonetiğiyle okur. Bir CBS ya da yazılım metni İngilizce jargonla
doludur (``shapefile``, ``buffer``, ``WMS``) ve bunlar okununca "şapefile" gibi
çıkar. Burada terimi, modelin doğru okuyacağı Türkçe yazımıyla değiştiriyoruz.

Sözlük iki katmanlıdır:
  1. ``CBS_TERIMLERI`` — alan bilgisi, pakete gömülü, herkeste aynı
  2. Kuruma özel sözlük — müşteri adları, proje kodları, yerel yer adları

İkinciyi çalışırken verirsin; birincisini değiştirmek gerekmez::

    sozluk = sozluk_birlestir(VARSAYILAN_SOZLUK, {"KENTGIS": "kent cis"})
    normalize("KENTGIS açılıyor.", telaffuz=sozluk)
    # "kent cis açılıyor."
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

TelaffuzSozlugu = Dict[str, str]

#: CBS ve yazılım jargonu.
#:
#: Kural: anahtar küçük harfle yazılır, eşleşme büyük/küçük harf duyarsızdır.
#: Değer, modelin doğru sesletmesi için Türkçe yazımdır — "doğru İngilizce"
#: değil, "Türk kulağına doğru gelen İngilizce".
CBS_TERIMLERI: TelaffuzSozlugu = {
    # Veri biçimleri ve standartlar
    "shapefile": "şeypfayl",
    "geojson": "ceo ceyson",
    "geotiff": "ceo tif",
    "kml": "ke me le",
    "wms": "ve me se",
    "wfs": "ve fe se",
    "wmts": "ve me te se",
    "postgis": "postcis",
    "geoserver": "ceo sörvır",
    "qgis": "kü cis",
    "arcgis": "ark cis",

    # Analiz terimleri
    "buffer": "bafır",
    "overlay": "ovırley",
    "layer": "leyır",
    "polygon": "poligon",
    "centroid": "sentroid",
    "geocoding": "ceo koding",
    "geocode": "ceo kod",
    "heatmap": "hitmap",
    "clustering": "klastırıng",
    "basemap": "beyzmap",

    # Koordinat sistemleri
    "epsg": "e pe es ge",
    "utm": "u te me",
    "wgs84": "ve ge es seksen dört",
    "crs": "ce re se",

    # Yazılım / altyapı
    "api": "ey pi ay",
    "cache": "keş",
    "cloud": "klaud",
    "dashboard": "daşbord",
    "export": "eksport",
    "token": "tokın",
    "json": "ceyson",
    "url": "u re le",
    "pdf": "pe de fe",
    "csv": "ce se ve",
    "sql": "es kü el",

    # Yapay zekâ
    "embedding": "embeding",
    "chatbot": "çetbot",
}


def sozluk_birlestir(*sozlukler: TelaffuzSozlugu) -> TelaffuzSozlugu:
    """Sözlükleri birleştirir; sonraki gelenler öncekini ezer.

    Anahtarlar sade ``lower()`` ile küçültülür (Türkçe kuralıyla değil):
    eşleştirme zaten büyük/küçük harf duyarsız yapıldığı için "KENTGIS"
    anahtarı metindeki "KENTGIS"i de "kentgis"i de yakalar.
    """
    hepsi: TelaffuzSozlugu = {}
    for s in sozlukler:
        for k, v in s.items():
            hepsi[k.lower()] = v
    return hepsi


#: Pakete gömülü varsayılan sözlük.
VARSAYILAN_SOZLUK: TelaffuzSozlugu = sozluk_birlestir(CBS_TERIMLERI)

# Derlenmiş desenler sözlük içeriğine göre önbelleğe alınır; normalize() her
# cümlede çağrılır, her seferinde yüzlerce desen derlemek boşa iş olur.
_ONBELLEK: Dict[Tuple[Tuple[str, str], ...], List[Tuple[re.Pattern, str]]] = {}


def _desenler(sozluk: TelaffuzSozlugu) -> List[Tuple[re.Pattern, str]]:
    anahtar = tuple(sozluk.items())
    desenler = _ONBELLEK.get(anahtar)
    if desenler is None:
        desenler = [
            (re.compile(r"(?<![^\W_])" + re.escape(terim) + r"(?![^\W_])", re.IGNORECASE), sozluk[terim])
            for terim in sorted(sozluk, key=len, reverse=True)
        ]
        if len(_ONBELLEK) > 32:
            _ONBELLEK.clear()
        _ONBELLEK[anahtar] = desenler
    return desenler


def telaffuz_uygula(metin: str, sozluk: TelaffuzSozlugu = VARSAYILAN_SOZLUK) -> str:
    """Sözlükteki terimleri metinde değiştirir.

    Uzun terimler önce denenir ki ``geojson``, ``json``'dan önce yakalansın.
    Sınırlar harf ve rakama bakar: ``apiyi`` içindeki ``api`` değişmez, çünkü
    Türkçede ek almış hali başka bir kelimedir ve bölmek okumayı bozar.
    """
    m = metin
    for desen, okunus in _desenler(sozluk):
        m = desen.sub(lambda _e, o=okunus: o, m)
    return m
