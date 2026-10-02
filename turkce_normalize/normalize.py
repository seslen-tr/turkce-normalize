"""
Türkçe TTS metin normalizasyonu.

Chatterbox, XTTS, Piper, StyleTTS2 gibi modeller SSML desteklemez ve sayıları,
tarihleri, para birimlerini Türkçe kurallarına göre okuyamaz. Bu modül metni
modele göndermeden önce "okunur" hale getirir.

Kural sırası önemlidir ve rastgele değildir:
  önce bütün bir birim olan gösterimler (e-posta, adres, coğrafi gösterim,
  telaffuz sözlüğü), sonra sayı kuralları. Ters sırada, "WGS84" içindeki 84
  ya da koordinattaki ondalık basamaklar genel sayı kurallarına yem olur ve
  terim bir daha yakalanamaz.

Sıra:
   1. e-posta ve web adresi
   2. sıcaklık (°C)
   3. coğrafi gösterimler (isteğe bağlı)
   4. telaffuz sözlüğü
   5. IBAN
   6. telefon
   7. tarih ve saat (aralıklarıyla)
   8. simgeler (+ = & ± °)
   9. kesirler
  10. sayı aralıkları
  11. eksi sayılar
  12. para
  13. yüzde
  14. kısaltmalar ve birimler
  15. Roma rakamları
  16. büyük harfli kısaltmalar (harf harf)
  17. sıra sayıları
  18. ondalık sayılar
  19. kalan tam sayılar
  20. kesme işareti
"""
from __future__ import annotations

import re
from typing import Optional

from .cografi import cografi_uygula
from .sayilar import (
    bulunma_eki, harf_oku, ondalik_oku, rakamlari_tek_tek, sayi_oku,
    sayiyi_coz, sira_oku, turkce_kucuk,
)
from .telaffuz import VARSAYILAN_SOZLUK, TelaffuzSozlugu, telaffuz_uygula

AYLAR = ["", "ocak", "şubat", "mart", "nisan", "mayıs", "haziran",
         "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]

KISALTMALAR = {
    "KDV": "katma değer vergisi", "ÖTV": "özel tüketim vergisi",
    "A.Ş.": "anonim şirketi", "Ltd.": "limited", "Şti.": "şirketi",
    "Dr.": "doktor", "Prof.": "profesör", "Doç.": "doçent", "Av.": "avukat",
    "Sn.": "sayın", "No.": "numara", "Tel.": "telefon", "Fax.": "faks",
    "Mah.": "mahallesi", "Cad.": "caddesi", "Sok.": "sokak", "Apt.": "apartmanı",
    "vb.": "ve benzeri", "vs.": "vesaire", "vd.": "ve diğerleri", "bkz.": "bakınız",
    "örn.": "örneğin", "TL": "lira", "USD": "dolar", "EUR": "euro",
    "T.C.": "te ce", "TCKN": "te ce kimlik numarası", "IBAN": "i ban",
}

BIRIMLER = {
    "km": "kilometre", "cm": "santimetre", "mm": "milimetre",
    "kg": "kilogram", "gr": "gram", "lt": "litre",
    "m²": "metrekare", "m2": "metrekare", "m³": "metreküp",
    "sa.": "saat", "dk.": "dakika", "sn.": "saniye",
}

#: Büyük harfle yazılıp KELİME gibi okunan kısaltmalar. Harf harf okunmaz,
#: Türkçe küçük harfe çevrilir ki model de hecelemeye kalkmasın
#: ("NATO'ya" -> "natoya"). Listeye eklemek serbesttir:
#:     KELIME_GIBI_OKUNANLAR.add("TEKNOFEST")
KELIME_GIBI_OKUNANLAR = {
    # Kurumlar
    "AFAD", "ASKİ", "BEDAŞ", "BOTAŞ", "BUSKİ", "EGO", "İSKİ", "İŞKUR", "İZSU",
    "MİT", "ODTÜ", "RTÜK", "SEDAŞ", "TEDAŞ", "TEİAŞ", "TOKİ", "TÜİK", "YÖK",
    "KOSGEB", "MÜSİAD", "TÜBİTAK", "TÜSİAD", "TÜPRAŞ", "TÜRKSAT",
    # Savunma sanayii ve şirketler
    "ASELSAN", "HAVELSAN", "ROKETSAN", "TOGG",
    # Uluslararası
    "NATO", "NASA", "OPEC", "FIFA", "UEFA", "UNESCO", "UNICEF",
    # Diğer
    "COVID",
}

#: Tamamı büyük harfle yazıldığında kısaltma SANILMAMASI gereken sıradan
#: kelimeler (başlık, uyarı, büyük harfli cümle). Kısaltma kuralı yalnızca 2–5
#: harfli tokenlara baktığı için liste kısa kelimelerden oluşur.
BILINEN_KELIMELER = {
    # Bağlaçlar, edatlar, soru ekleri
    "VE", "VEYA", "İLE", "YA", "DA", "DE", "Kİ", "MI", "Mİ", "MU", "MÜ", "AMA",
    "FAKAT", "ANCAK", "ÇÜNKÜ", "GİBİ", "İÇİN", "KADAR", "SONRA", "ÖNCE", "HEM",
    # Zamirler ve sık kelimeler
    "BU", "ŞU", "BEN", "SEN", "BİZ", "SİZ", "ONLAR", "HER", "HİÇ", "NE", "NASIL",
    "NEDEN", "NİÇİN", "KİM", "NERDE", "VAR", "YOK", "EVET", "HAYIR", "TAMAM",
    "ÇOK", "AZ", "EN", "DAHA", "İYİ", "KÖTÜ", "BÜYÜK", "KÜÇÜK", "YENİ", "ESKİ",
    "İLK", "SON", "ŞİMDİ", "BUGÜN", "YARIN", "DÜN", "SAAT", "GÜN", "AY", "YIL",
    "HAFTA", "ADET",
    # Sayılar
    "BİR", "İKİ", "ÜÇ", "DÖRT", "BEŞ", "ALTI", "YEDİ", "SEKİZ", "DOKUZ", "ON",
    "YÜZ", "BİN",
    # Arayüz ve tabela kelimeleri
    "UYARI", "DİKKAT", "NOT", "HATA", "BİLGİ", "ACİL", "YASAK", "ÖZEL", "GİRİŞ",
    "ÇIKIŞ", "KAYIT", "ARA", "SİL", "EKLE", "İPTAL", "ONAY", "DUR", "GİT", "GEL",
    "BAK", "AÇ", "KAPAT", "AÇIK", "BAŞLA", "BİTTİ", "HABER", "FİYAT", "SATIŞ",
    "KİRA", "SORU", "CEVAP", "ÖRNEK", "KONU", "ÖZET", "SONUÇ", "AMAÇ",
}

#: Roma rakamı gibi görünen ama sık kullanılan kelime ve kısaltmalar.
#: "MI." soru ekidir, "CD." bir disktir, 1001 ya da 400 değil.
ROMA_KARA_LISTE = {
    "MI", "DI", "LI", "CD", "DC", "CV", "MD", "MC", "CC", "CM", "MM", "CL",
    "DL", "ML", "CI", "DIX", "MIX", "LIV", "DIV",
}

#: Tek harfli Roma rakamından önce gelebilen unvanlar ("Sultan V. Mehmet").
#: Bunlar dışında büyük harfli bir kelimeden sonra gelen tek harf ("Mehmet V.
#: Delibaş") isim baş harfi sayılır.
UNVANLAR = {
    "Sultan", "Padişah", "Kral", "Kraliçe", "İmparator", "İmparatoriçe",
    "Papa", "Çar", "Şah", "Han", "Hakan", "Prens", "Prenses", "Dük",
}

# --------------------------------------------------------------------------
# Yardımcılar
# --------------------------------------------------------------------------

# JavaScript'teki \b ve \d ASCII'dir. Kaynak kurallar o anlamla yazıldığından
# taşınan desenler re.ASCII ile derlenir; Unicode boşluklar en başta düz
# boşluğa çevrildiği için \s'nin ASCII olması bir şey kaybettirmez.
_A = re.ASCII

_UNICODE_BOSLUK = re.compile(r"[   -   　]")


def _harf_harf(kelime: str) -> str:
    return " ".join(harf_oku(h) for h in kelime)


# Komşu kelimeye bakarken yalnızca yakın çevre taranır; bütün ön metni taramak
# uzun metinlerde işi ikinci dereceden yavaşlatır.
_PENCERE = 40


def _oncesi(e: re.Match) -> str:
    return e.string[max(0, e.start() - _PENCERE):e.start()]


def _sonrasi(e: re.Match) -> str:
    return e.string[e.end():e.end() + _PENCERE]


def _kesme_sonrasi_harf(e: re.Match) -> bool:
    return e.string[e.end():e.end() + 1] in ("'", "’")


# --------------------------------------------------------------------------
# 1) E-posta ve web adresi
# --------------------------------------------------------------------------

_AYRAC_OKUNUSU = {
    ".": "nokta", "-": "tire", "_": "alt çizgi", "+": "artı", "/": "bölü",
    ":": "iki nokta", "@": "et", "~": "yaklaşık", "%": "yüzde",
}
_EPOSTA = re.compile(r"(?<![A-Za-z0-9._%+-])([A-Za-z0-9][A-Za-z0-9._%+-]*)@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
_URL = re.compile(r"(?:https?://|www\.)[^\s<>\"'’]+", re.IGNORECASE)
_UZANTILAR = ("com|net|org|gov|edu|mil|int|info|biz|io|ai|dev|app|tr|de|uk|eu|us|fr|nl|az|kz")
_ALAN_ADI = re.compile(
    r"(?<![\w@./-])[a-z][a-z0-9-]*(?:\.[a-z0-9-]+)*\.(?:" + _UZANTILAR + r")(?![\w-])(?:/[^\s<>\"'’]*)?"
)
_SONDAKI_NOKTALAMA = re.compile(r"[.,;:!?)\]]+$")


def _parca_oku(parca: str) -> str:
    """Adresin bir parçasını okur: harfler olduğu gibi, sayılar sayı, ayraçlar adıyla."""
    kelimeler = []
    for oge in re.findall(r"\d+|[^\W\d_]+|[^\w\s]|_", parca):
        if oge.isdigit():
            kisa = len(oge) <= 4 and not (len(oge) > 1 and oge[0] == "0")
            kelimeler.append(sayi_oku(oge) if kisa else rakamlari_tek_tek(oge))
        elif oge in _AYRAC_OKUNUSU:
            kelimeler.append(_AYRAC_OKUNUSU[oge])
        elif oge[0].isalpha():
            kelimeler.append(turkce_kucuk(oge))
        # tanınmayan işaretler sessizce düşer
    return " ".join(kelimeler)


def _alan_adi_oku(alan: str) -> str:
    """"ornek.com.tr" -> "ornek nokta com nokta te re". İki harfli ülke uzantısı harf harf."""
    alan, _, port = alan.partition(":")
    etiketler = alan.split(".")
    okunus = []
    for i, etiket in enumerate(etiketler):
        if i == len(etiketler) - 1 and len(etiket) == 2 and etiket.isalpha():
            okunus.append(_harf_harf(etiket))
        else:
            okunus.append(_parca_oku(etiket))
    sonuc = " nokta ".join(okunus)
    if port:
        sonuc += " iki nokta " + _parca_oku(port)
    return sonuc


def _adres_oku(adres: str) -> str:
    """Web adresini okur: şema ve "www" atılır, sorgu ve çapa okunmaz."""
    a = re.sub(r"^https?://", "", adres, flags=re.IGNORECASE)
    a = re.sub(r"^www\.", "", a, flags=re.IGNORECASE)
    a = re.split(r"[?#]", a, maxsplit=1)[0].rstrip("/")
    alan, _, yol = a.partition("/")
    parcalar = [_alan_adi_oku(alan.lower())]
    parcalar += [_parca_oku(p) for p in yol.split("/") if p]
    return " bölü ".join(p for p in parcalar if p)


def _sondaki_noktalamayi_ayir(e: re.Match):
    metin = e.group(0)
    son = _SONDAKI_NOKTALAMA.search(metin)
    if son:
        return metin[:son.start()], son.group(0)
    return metin, ""


def _url_degistir(e: re.Match) -> str:
    adres, kuyruk = _sondaki_noktalamayi_ayir(e)
    return _adres_oku(adres) + kuyruk


def eposta_ve_adres_oku(metin: str) -> str:
    """E-posta ve web adreslerini okunur hale getirir.

    "ali.veli@ornek.com.tr" -> "ali nokta veli et ornek nokta com nokta te re"
    "https://www.ornek.gov.tr/harita" -> "ornek nokta gov nokta te re bölü harita"
    """
    m = _EPOSTA.sub(
        lambda e: f"{_parca_oku(e.group(1))} et {_alan_adi_oku(e.group(2).lower())}", metin
    )
    m = _URL.sub(_url_degistir, m)
    m = _ALAN_ADI.sub(_url_degistir, m)
    return m


# --------------------------------------------------------------------------
# 2) Sıcaklık ve 8) simgeler
# --------------------------------------------------------------------------

_SANTIGRAT = re.compile(r"[ \t]*(?:°[ \t]*C|℃)(?![^\W_])")
_FAHRENHAYT = re.compile(r"[ \t]*(?:°[ \t]*F|℉)(?![^\W_])")
_ARTI = re.compile(r"(?<=\d)[ \t]*\+[ \t]*(?=\d)")
_ESITTIR = re.compile(r"[ \t]*=[ \t]*")
_VE = re.compile(r"[ \t]*&[ \t]*")
_ARTI_EKSI = re.compile(r"[ \t]*±[ \t]*")
_DERECE = re.compile(r"(?<=\d)[ \t]*°")


def simgeleri_oku(metin: str) -> str:
    """"2 + 2 = 4" -> "2 artı 2 eşittir 4", "&" -> "ve", "±" -> "artı eksi", "45°" -> "45 derece"."""
    m = _ARTI.sub(" artı ", metin)
    m = _ESITTIR.sub(" eşittir ", m)
    m = _VE.sub(" ve ", m)
    m = _ARTI_EKSI.sub(" artı eksi ", m)
    m = _DERECE.sub(" derece", m)
    return m


# --------------------------------------------------------------------------
# 5–7) IBAN, telefon, tarih, saat
# --------------------------------------------------------------------------

_IBAN = re.compile(r"\bTR\d{2}(?:\s?\d{4}){2,6}\b", _A)
# Kaynakta yalnızca boşluklu yazım vardı; tireli yazım ("0212-555-44-33") da eklendi.
_TELEFON = re.compile(r"\b0\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b", _A)
_TARIH_KALIBI = r"\d{1,2}[./]\d{1,2}[./]\d{4}"
_SAAT_KALIBI = r"(?:[01]?\d|2[0-3]):[0-5]\d"
_ZAMAN_ARALIGI = re.compile(
    rf"\b({_TARIH_KALIBI}|{_SAAT_KALIBI})\s?[-–]\s?({_TARIH_KALIBI}|{_SAAT_KALIBI})\b", _A
)
_TARIH = re.compile(r"\b(\d{1,2})([./-])(\d{1,2})\2(\d{4})\b", _A)   # 15.03.2026, 15/03/2026, 15-03-2026
_ISO_TARIH = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b", _A)              # 2026-03-15
# Türkçede saat sık sık noktayla yazılır: "saat 14.30". Yalnız "saat" sözcüğünden sonra (3.14 ondalıktır).
_SAAT_NOKTALI = re.compile(r"(?<=\b[Ss]aat )([01]?\d|2[0-3])\.([0-5]\d)\b")
# Sürüm numarası: noktalı ve en az üç grup; grupların hepsi üç rakamlı değilse binlik değildir ("1.2.3").
_SURUM = re.compile(r"(?<![\d.,])\d+(?:\.\d+){2,}(?![\d.])", _A)
# İngilizce usulü ondalık nokta: ardında tam 3 rakam yoksa binlik ayırıcı değildir ("3.5", "2.75").
_NOKTALI_ONDALIK = re.compile(r"(?<![\d.,])(\d+)\.(\d{1,2}|\d{4,})(?![\d.])", _A)
_SAAT = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", _A)


def _iban_oku(e: re.Match) -> str:
    ham = re.sub(r"\s", "", e.group(0))
    return _harf_harf(ham[:2]) + " " + rakamlari_tek_tek(ham[2:])


def _tarih_oku(e: re.Match) -> str:
    gun, ay = int(e.group(1)), int(e.group(3))
    if ay < 1 or ay > 12 or gun < 1 or gun > 31:
        return e.group(0)
    return f"{sayi_oku(gun)} {AYLAR[ay]} {sayi_oku(e.group(4))}"


def _surum_oku(e: re.Match) -> str:
    gruplar = e.group(0).split(".")
    if len(gruplar[0]) <= 3 and all(len(g) == 3 for g in gruplar[1:]):
        return e.group(0)                            # "1.250.000": binlik ayırıcı
    return " nokta ".join(sayi_oku(g) for g in gruplar)   # "1.2.3" -> "bir nokta iki nokta üç"


def _iso_tarih_oku(e: re.Match) -> str:
    yil, ay, gun = e.group(1), int(e.group(2)), int(e.group(3))
    if ay < 1 or ay > 12 or gun < 1 or gun > 31:
        return e.group(0)
    return f"{sayi_oku(gun)} {AYLAR[ay]} {sayi_oku(yil)}"


def _saat_oku(e: re.Match) -> str:
    # 14:30 -> "on dört otuz", 14:05 -> "on dört sıfır beş", 09:00 -> "dokuz".
    # Tek haneli dakikada "sıfır" şart: 10:01 aksi halde "on bir" okunur, yani saat 11.
    saat = "sıfır sıfır" if int(e.group(1)) == 0 else sayi_oku(e.group(1))
    dakika = int(e.group(2))
    if dakika == 0:
        return saat                                  # 09:00 -> "dokuz", ekiyle "dokuzda"
    if dakika < 10:
        return f"{saat} sıfır {sayi_oku(dakika)}"    # 14:05 -> "on dört sıfır beş"
    return f"{saat} {sayi_oku(dakika)}"              # 14:30 -> "on dört otuz"


# --------------------------------------------------------------------------
# 9) Kesirler
# --------------------------------------------------------------------------

_KESIR = re.compile(r"(?<![\w.,/:\-–])(?:(\d+) )?([1-9]\d*)/([1-9]\d*)(?![\w/]|[.,]\d)(?:['’]([^\W\d_]+))?")
_KESIR_KARAKTERI = re.compile(r"(?<![\w.,])(?:(\d+)[ \t]?)?([½¼¾])")
_KESIR_KARAKTERLERI = {"½": (1, 2), "¼": (1, 4), "¾": (3, 4)}
# Adreste "No: 5/7" bir kesir değil, kapı numarasıdır ve "beş bölü yedi" okunur.
_ADRES_ONCESI = re.compile(r"\b(?:no|numara|daire|kapı|blok)\s*[:.]?\s*$", re.IGNORECASE)


def _kesir_metni(pay: int, payda: int, tam: Optional[str], ekli: bool) -> str:
    if pay == 1 and payda == 2 and not ekli:
        return f"{sayi_oku(tam)} buçuk" if tam else "yarım"
    if pay == 1 and payda == 4 and not ekli and not tam:
        return "çeyrek"
    payda_okunusu = sayi_oku(payda)
    kesir = f"{payda_okunusu}{bulunma_eki(payda_okunusu)} {sayi_oku(pay)}"
    return f"{sayi_oku(tam)} tam {kesir}" if tam else kesir


_UYUM_KALIN_DUZ = str.maketrans("iüueöo", "ıııaaa")      # yarı + ek: si → sı, ye → ya
_UYUM_INCE_DUZ = str.maketrans("ıuüaoö", "iiieee")       # çeyrek + ek: ü → i


def _kesir_oku(e: re.Match) -> str:
    tam, pay, payda, ek = e.group(1), int(e.group(2)), int(e.group(3)), e.group(4) or ""
    if _ADRES_ONCESI.search(_oncesi(e)):
        return (f"{tam} " if tam else "") + f"{sayi_oku(pay)} bölü {sayi_oku(payda)}" + ek
    if (pay, payda) == (24, 7) and not tam:
        return "yirmi dört yedi" + ek                # "24/7 açık"
    if pay >= payda or payda < 2:
        return e.group(0)                            # "15/03": kesir değil
    if ek and not tam and (pay, payda) == (1, 2):
        return "yarı" + turkce_kucuk(ek).translate(_UYUM_KALIN_DUZ)   # "1/2'si" -> "yarısı"
    if ek and not tam and (pay, payda) == (1, 4):
        ek = turkce_kucuk(ek).translate(_UYUM_INCE_DUZ)
        return ("çeyreğ" if ek[0] in "aeıioöuü" else "çeyrek") + ek    # "1/4'ü" -> "çeyreği"
    return _kesir_metni(pay, payda, tam, bool(ek)) + turkce_kucuk(ek)   # "3/4'ü" -> "dörtte üçü"


def kesirleri_oku(metin: str) -> str:
    """"3/4" -> "dörtte üç", "1/2 kilo" -> "yarım kilo", "2 1/2" -> "iki buçuk"."""
    m = _KESIR.sub(_kesir_oku, metin)
    return _KESIR_KARAKTERI.sub(
        lambda e: _kesir_metni(*_KESIR_KARAKTERLERI[e.group(2)], e.group(1), _kesme_sonrasi_harf(e)), m
    )


# --------------------------------------------------------------------------
# 10–11) Aralıklar ve eksi sayılar
# --------------------------------------------------------------------------

_ARALIK_SAYI = r"\d{1,3}(?:\.\d{3})+|\d+"
_ARALIK = re.compile(
    rf"(?<![\w.,/%\-–−])({_ARALIK_SAYI})[ \t]?[-–][ \t]?({_ARALIK_SAYI})(?![\w/\-–]|[.,]\d)(\.(?=\s+([^\W\d_])))?"
)
_YUZDE_ARALIGI = re.compile(r"%[ \t]?(\d+)[ \t]?[-–][ \t]?%?[ \t]?(\d+)(?![\d.,])")
_EKSI = re.compile(r"(?<![\w.,)\]/%])[-−](?=\d)")


def _aralik_oku(e: re.Match) -> str:
    a_metin, b_metin, nokta, sonraki = e.groups()
    if any(len(s) > 1 and s[0] == "0" for s in (a_metin, b_metin)):
        return e.group(0)                            # "0532-123": kod ya da numara
    a, b = sayiyi_coz(a_metin), sayiyi_coz(b_metin)
    if a >= b:
        if b <= 99 and a <= 99:
            return f"{sayi_oku(a)} {sayi_oku(b)}" + (nokta or "")   # skor: "3-1" -> "üç bir"
        return e.group(0)
    if nokta and sonraki.islower():
        return f"{sira_oku(a)} ile {sira_oku(b)}"    # "3-5. maddeler"
    if b <= 100:
        okunus = f"{sayi_oku(a)} {sayi_oku(b)}"      # "3-5 kişi" -> "üç beş kişi"
    else:
        okunus = f"{sayi_oku(a)} ile {sayi_oku(b)}"  # "2020-2025" -> "... ile ..."
    return okunus + (nokta or "")


def araliklari_oku(metin: str) -> str:
    """"3-5 kişi" -> "üç beş kişi", "2020-2025" -> "iki bin yirmi ile iki bin yirmi beş"."""
    m = _YUZDE_ARALIGI.sub(lambda e: f"yüzde {sayi_oku(e.group(1))} ile {sayi_oku(e.group(2))}", metin)
    return _ARALIK.sub(_aralik_oku, m)


# --------------------------------------------------------------------------
# 12–14) Para, yüzde, kısaltmalar
# --------------------------------------------------------------------------

_PARA = re.compile(r"\b([\d.]+?)(?:,(\d{1,2}))?\s?(?:₺|TL\b|lira\b)", _A)
# Sayı: binlik gruplu ya da düz; "[\d.]+" cümle sonu noktasını da yutuyordu ("%18." → nokta kayboluyordu)
_YUZDE = re.compile(r"%\s?(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?", _A)
_SOZLUK_DESENLERI = [
    (re.compile(r"(?<![^\W_])" + re.escape(kisa) + r"(?![^\W_])"), sozluk[kisa])
    for sozluk in (KISALTMALAR, BIRIMLER)
    for kisa in sorted(sozluk, key=len, reverse=True)
]


def _para_oku(e: re.Match) -> str:
    cikti = f"{sayi_oku(sayiyi_coz(e.group(1)))} lira"
    kurus = e.group(2)
    if kurus and int(kurus):
        cikti += f" {sayi_oku(kurus)} kuruş"
    return cikti


def _yuzde_oku(e: re.Match) -> str:
    tam, kesir = e.group(1), e.group(2)
    return "yüzde " + (ondalik_oku(sayiyi_coz(tam), kesir) if kesir else sayi_oku(sayiyi_coz(tam)))


# --------------------------------------------------------------------------
# 15) Roma rakamları
# --------------------------------------------------------------------------

_ROMA = re.compile(
    r"(?<![\w.])(?=[MDCLXVI])(M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))"
    r"\.(?=\s+([^\W\d_]))"
)
_ROMA_DEGER = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
_ONCEKI_KELIME = re.compile(r"([^\W\d_]+)\s+$")


def roma_coz(rakam: str) -> int:
    """"XIV" -> 14. Geçerlilik denetimi yapmaz; desen zaten yalnızca geçerlileri yakalar."""
    toplam = 0
    for i, h in enumerate(rakam):
        deger = _ROMA_DEGER[h]
        sonraki = _ROMA_DEGER[rakam[i + 1]] if i + 1 < len(rakam) else 0
        toplam += -deger if deger < sonraki else deger
    return toplam


def _roma_oku(e: re.Match) -> str:
    rakam, sonraki = e.group(1), e.group(2)
    if not rakam or rakam in ROMA_KARA_LISTE:
        return e.group(0)
    deger = roma_coz(rakam)
    if sonraki.islower():
        return sira_oku(deger)                       # "XX. yüzyıl" -> "yirminci yüzyıl"
    # Büyük harfle başlayan kelime: yalnızca hükümdar sırası gibi küçük sayılar
    # ("II. Abdülhamit", "I. Dünya Savaşı"). "CD. Sonra" gibi cümle sonları elenir.
    if set(rakam) <= set("IVX") and deger <= 39:
        if len(rakam) == 1:
            onceki = _ONCEKI_KELIME.search(_oncesi(e))
            if onceki and onceki.group(1)[0].isupper() and onceki.group(1) not in UNVANLAR:
                return e.group(0)                    # "Mehmet V. Delibaş": baş harf
        return sira_oku(deger)
    return e.group(0)


# --------------------------------------------------------------------------
# 16) Büyük harfli kısaltmalar
# --------------------------------------------------------------------------

_KISALTMA_ADAYI = re.compile(
    r"(?<![^\W_])([A-ZÇĞİÖŞÜ]{2,})(?:['’]([a-zçğıöşüâîûA-ZÇĞİÖŞÜ]+))?(?![^\W_])"
)
_YALNIZ_ROMA = re.compile(r"^[IVX]+$")  # "XX", "VIII": Roma rakamı, kısaltma değil
_ONCEKI_TOKEN = re.compile(r"([^\W\d_]+)[^\w\n]*$")
_SONRAKI_TOKEN = re.compile(r"^[^\w\n]*([^\W\d_]+)")


def _buyuk_harfli_cumlede(e: re.Match) -> bool:
    """Komşu kelime büyük harfle yazılmış sıradan bir kelimeyse ("GELDİ MI")
    metin büyük harfli bir cümledir; içindeki kelimeler kısaltma değildir."""
    komsular = (_ONCEKI_TOKEN.search(_oncesi(e)), _SONRAKI_TOKEN.search(_sonrasi(e)))
    return any(k is not None and k.group(1) in BILINEN_KELIMELER for k in komsular)


def _kisaltma_oku(e: re.Match) -> str:
    kelime, ek = e.group(1), turkce_kucuk(e.group(2) or "")
    if kelime in KELIME_GIBI_OKUNANLAR:
        return turkce_kucuk(kelime) + ek             # "NATO'ya" -> "natoya"
    if (len(kelime) > 5 or kelime in BILINEN_KELIMELER or _YALNIZ_ROMA.match(kelime)
            or _buyuk_harfli_cumlede(e)):
        return e.group(0)
    return _harf_harf(kelime) + ek                   # "TBMM'de" -> "te be me mede"


def kisaltmalari_oku(metin: str) -> str:
    """2–5 harfli büyük harfli kısaltmaları harf harf okur: "TRT" -> "te re te"."""
    return _KISALTMA_ADAYI.sub(_kisaltma_oku, metin)


# --------------------------------------------------------------------------
# 17–20) Sıra, ondalık, tam sayı, kesme işareti
# --------------------------------------------------------------------------

_SIRA = re.compile(r"(?<![A-Za-z0-9_])(\d+)\.(?=\s+([^\W\d_]))")
_ONDALIK = re.compile(r"\b([\d.]+),(\d+)\b", _A)
_TAM_SAYI = re.compile(r"\b\d[\d.]*\b", _A)
_KESME = re.compile(r"(?<=[^\W_])['’](?=[^\W\d_])")


def _sira_oku(e: re.Match) -> str:
    # Cümle sonu noktasıyla karışmasın diye ardından küçük harfle başlayan
    # bir kelime aranır: "3. madde" sıra sayısıdır, "3. Sonra" değildir.
    if not e.group(2).islower():
        return e.group(0)
    return sira_oku(int(e.group(1)))


# --------------------------------------------------------------------------
# Ana işlev
# --------------------------------------------------------------------------


def normalize(
    metin: str,
    telaffuz: Optional[TelaffuzSozlugu] = None,
    cografi: bool = True,
    kisaltma_harf_harf: bool = True,
) -> str:
    """Metni TTS modeline verilmeye hazır hale getirir.

    :param telaffuz: Telaffuz sözlüğü. Verilmezse pakete gömülü CBS/yazılım
        sözlüğü kullanılır. Kuruma özel terimler için
        ``sozluk_birlestir(VARSAYILAN_SOZLUK, kendi_sozlugun)``.
    :param cografi: Coğrafi gösterim kuralları (koordinat, ölçek, pafta, EPSG).
        Varsayılan açık. CBS dışı bir metinde kapatmak isteyebilirsin.
    :param kisaltma_harf_harf: "TBMM" gibi büyük harfli kısaltmaları harf harf
        okut ("te be me me"). Varsayılan açık.
    """
    m = _UNICODE_BOSLUK.sub(" ", metin)

    # 1) E-posta ve web adresi — en önce. Adresin içindeki nokta, tire ve
    #    rakamlar sonraki kuralların hepsine yem olur ("ornek2.com.tr").
    m = eposta_ve_adres_oku(m)

    # 2) Sıcaklık — coğrafi kurallardan önce; yoksa "25,5°C" ondalık derece
    #    (koordinat) sanılır ve "C" ortada kalır.
    m = _SANTIGRAT.sub(" derece", m)
    m = _FAHRENHAYT.sub(" derece fahrenhayt", m)

    # 3) Coğrafi gösterimler. İki sebeple sayı kurallarından ve telaffuz
    #    sözlüğünden önce:
    #    - koordinat çifti "39.9334, 32.8597" aksi halde tek bir ondalık sayı sanılır;
    #    - sözlük "EPSG"yi "e pe es ge"ye çevirirse "EPSG:5254" kalıbı bir daha
    #      yakalanamaz ve kod sayı olarak okunur.
    if cografi:
        m = cografi_uygula(m)

    # 4) Telaffuz sözlüğü — sayı kurallarından önce, yoksa "wgs84" gibi
    #    terimlerin içindeki rakam bölünür ve terim yakalanmaz.
    m = telaffuz_uygula(m, VARSAYILAN_SOZLUK if telaffuz is None else telaffuz)

    # 5) IBAN — harfler ve rakamlar tek tek
    m = _IBAN.sub(_iban_oku, m)

    # 6) Telefon — 0212 555 44 33
    m = _TELEFON.sub(lambda e: rakamlari_tek_tek(e.group(0)), m)

    # 7) Tarih ve saat. Önce aralıklar: "14:30-15:30" -> "14:30 ile 15:30"
    m = _ZAMAN_ARALIGI.sub(r"\1 ile \2", m)
    m = _ISO_TARIH.sub(_iso_tarih_oku, m)            # 2026-03-15 (aralık kuralından önce)
    m = _TARIH.sub(_tarih_oku, m)                    # 15.03.2026 / 15/03/2026 / 15-03-2026
    m = _SAAT.sub(_saat_oku, m)
    m = _SAAT_NOKTALI.sub(_saat_oku, m)              # "saat 14.30"

    # 8) Simgeler — "2+2", "=", "&", "±", "45°"
    m = simgeleri_oku(m)

    # 9) Kesirler — tarihten ve ölçekten SONRA: "15/03/2026" ve "1/25.000"
    #    o kurallarda tüketilmiş olur.
    m = kesirleri_oku(m)

    # 10) Aralıklar — paradan önce ki "1.000-2.000 TL" iki ayrı tutar olarak okunsun.
    m = araliklari_oku(m)

    # 11) Eksi sayılar — "-5 derece" -> "eksi beş derece"
    m = _EKSI.sub("eksi ", m)

    # 12) Para — 1.250,50 ₺ / 1.250,50 TL
    m = _PARA.sub(_para_oku, m)

    # 13) Yüzde — %18 / % 18,5
    m = _YUZDE.sub(_yuzde_oku, m)

    # 14) Kısaltmalar ve birimler — uzundan kısaya, parça eşleşmesini önlemek için
    for desen, okunus in _SOZLUK_DESENLERI:
        m = desen.sub(lambda _e, o=okunus: o, m)

    # 15) Roma rakamları — "XX. yüzyıl", "II. Abdülhamit". Harf harf kısaltma
    #     kuralından önce, yoksa "XX" "iks iks" olur.
    m = _ROMA.sub(_roma_oku, m)

    # 16) Büyük harfli kısaltmalar — sözlükteki kısaltmalardan (KDV, TL) sonra
    if kisaltma_harf_harf:
        m = kisaltmalari_oku(m)

    # 17) Sıra sayısı — "3. madde"
    m = _SIRA.sub(_sira_oku, m)

    # 18) Ondalık sayı — 3,5; İngilizce usulü "3.5" de (ardında tam 3 rakam yoksa binlik değildir)
    m = _ONDALIK.sub(lambda e: ondalik_oku(sayiyi_coz(e.group(1)), e.group(2)), m)
    m = _SURUM.sub(_surum_oku, m)
    m = _NOKTALI_ONDALIK.sub(lambda e: ondalik_oku(int(e.group(1)), e.group(2)), m)

    # 19) Kalan tam sayılar — 1.250 / 42
    m = _TAM_SAYI.sub(lambda e: sayi_oku(sayiyi_coz(re.sub(r"\.$", "", e.group(0)))), m)

    # 20) Kesme işaretini kaldır — "14:30'da" -> "on dört otuzda"
    m = _KESME.sub("", m)

    return re.sub(r"\s{2,}", " ", m).strip()
