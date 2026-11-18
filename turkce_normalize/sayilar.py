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
#: uzantısı ("tr" -> "tere") hep bu tabloyu kullanır (bitişik okunuş: harfleri_oku).
HARF_OKUNUSU = {
    "A": "a", "B": "be", "C": "ce", "Ç": "çe", "D": "de", "E": "e", "F": "fe", "G": "ge",
    # K: kısaltmalarda yaygın okunuş "ka" (KDV → ka de ve, PKK → pe ka ka); TDK alfabesinde "ke".
    "Ğ": "yumuşak ge", "H": "he", "I": "ı", "İ": "i", "J": "je", "K": "ka", "L": "le",
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
    """Tek harfi okur: "K" -> "ka", "ğ" -> "yumuşak ge". Bilinmeyen harf küçülür."""
    return HARF_OKUNUSU.get(turkce_buyuk(harf), turkce_kucuk(harf))


def harfleri_oku(kelime: str) -> str:
    """Kısaltmayı harf harf, tek sözcük gibi bitişik okur: "TBMM" -> "tebememe", "TR" -> "tere". İki sözcüklü harf
    adı ve ünsüzle biten harf adının ardı ayrı kalır ("AĞ" -> "a yumuşak ge", "XQ" -> "iks kü"). 0.1.5'e kadar harf
    adları boşlukla ayrıydı ("te be me me"); ses modeli ayrık harf adlarında ünlüleri yutuyordu ("tbmmede", "ap elli"),
    bitişikte okunuş denetiminde takılan 21 → 5 / 72."""
    okunus = ""
    for h in kelime:
        o = harf_oku(h)
        if okunus and okunus[-1] not in "aeıioöuü ":
            okunus += " "
        okunus += f" {o} " if " " in o else o
    return " ".join(okunus.split())


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


def saat_oku(saat: str, dakika: str) -> str:
    """("14", "30") -> "on dört otuz", ("14", "05") -> "on dört sıfır beş", ("09", "00") -> "dokuz".
    Tek haneli dakikada "sıfır" şart: 10:01 aksi halde "on bir" okunur, yani saat 11."""
    s = "sıfır sıfır" if int(saat) == 0 else sayi_oku(saat)
    d = int(dakika)
    if d == 0:
        return s                                     # 09:00 -> "dokuz", ekiyle "dokuzda"
    return f"{s} sıfır {sayi_oku(d)}" if d < 10 else f"{s} {sayi_oku(d)}"


def tam_sayi_oku(sayi: str, sifir_oku: bool = True) -> str:
    """"1.250" -> "bin iki yüz elli"; baştaki sıfırlar okunur: "042" -> "sıfır kırk iki", "007" -> "sıfır sıfır
    yedi" (kod ve numarada sıfır düşüyordu: "TR-042" -> "tere kırk iki", 17.11.2026). Tek "0", binlik ayırıcılı
    yazım ve sifir_oku=False (normalize: "/"den sonra, "15/03" günü ayı) değişmez."""
    sayi = re.sub(r"\.$", "", sayi)
    sifir = len(sayi) - len(sayi.lstrip("0"))
    if sifir_oku and sifir and len(sayi) > 1 and "." not in sayi:
        return " ".join(["sıfır"] * sifir + ([sayi_oku(int(sayi[sifir:]))] if sayi[sifir:] else []))
    return sayi_oku(sayiyi_coz(sayi))


_UNLULER = "aeıioöuü"
_ROMA_DEGER = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roma_coz(rakam: str) -> int:
    """"XIV" -> 14. Geçerlilik denetimi yapmaz; desen zaten yalnızca geçerlileri yakalar."""
    toplam = 0
    for i, h in enumerate(rakam):
        deger = _ROMA_DEGER[h]
        sonraki = _ROMA_DEGER[rakam[i + 1]] if i + 1 < len(rakam) else 0
        toplam += -deger if deger < sonraki else deger
    return toplam


def eki_uydur(kelime: str, ek: str) -> str:
    """Eki kelimeye ünlü ve ünsüz uyumuyla uydurur: ("lira", "den") -> "dan", ("kuruş", "den") -> "tan",
    ("kuruş", "yi") -> "u" (ünsüzle biten kelimede kaynaştırma harfi düşer), ("lira", "lik") -> "lık"."""
    ek = turkce_kucuk(ek)
    son = next((c for c in reversed(kelime) if c in _UNLULER), "e")
    kalin, yuvarlak = son in "aıou", son in "oöuü"
    if kelime[-1] not in _UNLULER:
        if len(ek) > 1 and ek[0] in "yns" and ek[1] in _UNLULER:
            ek = ek[1:]
        if kelime[-1] in "fstkçşhp" and ek[0] in "dc":
            ek = {"d": "t", "c": "ç"}[ek[0]] + ek[1:]
    cikti = []
    for h in ek:
        if h in "ea":
            h, yuvarlak = ("a" if kalin else "e"), False
        elif h in "ıiuü":
            h = {(True, True): "u", (True, False): "ı", (False, True): "ü", (False, False): "i"}[(kalin, yuvarlak)]
        elif h in "oö":
            kalin, yuvarlak = h == "o", True
        cikti.append(h)
    return "".join(cikti)


def roma_ekli_oku(deger: int, ek: str = "", sira: bool = False) -> str:
    """Roma rakamının değeri + kesmeden sonraki ek: (4, "e") -> "dörde", (3, "te") -> "üçte", (14, "ün", sira=True) ->
    "on dördüncünün". Ünlüyle biten okunuşa ünlüyle başlayan ek: ilgi eki "n", ötekiler "y" alır; ünlüden sonra
    "t" "d" olur; "dört" yumuşar."""
    okunus = sira_oku(deger) if sira else sayi_oku(deger)
    if okunus.endswith("dört") and ek[:1].lower() in _UNLULER:
        okunus = okunus[:-1] + "d"
    return ek_ekle(okunus, ek)


def ek_ekle(okunus: str, ek: str) -> str:
    """Kesmeden sonraki eki, başka bir yazıma göre yazılmış olsa da okunuşa ekler: ("yirmi beş avro", "e") ->
    "… avroya" (€25'e), ("beş dolar", "te") -> "… dolarda" ($5'te). Ünlüyle biten okunuşa ünlüyle başlayan ek: ilgi
    eki "n", ötekiler "y" alır; sert olmayan sesten sonra "t" "d", "ç" "c" olur."""
    ek = turkce_kucuk(ek)
    if not ek:
        return okunus
    if okunus[-1] in _UNLULER and ek[0] in _UNLULER:
        ek = ("n" if re.match(r"[ıiuü]n(?![aeıioöuü])", ek) else "y") + ek
    elif okunus[-1] not in "fstkçşhp" and ek[0] in "tç":
        ek = {"t": "d", "ç": "c"}[ek[0]] + ek[1:]
    return okunus + eki_uydur(okunus.split()[-1], ek)


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


# --------------------------------------------------------------------------
# Para: lira, dolar, avro, sterlin (normalize adım 12)
# --------------------------------------------------------------------------

#: Para birimi yazımı -> (birim, alt birim). "Avro" TDK yazımı ve resmî kullanım ("euro" değil).
PARA_BIRIMLERI = {
    "₺": ("lira", "kuruş"), "TL": ("lira", "kuruş"), "lira": ("lira", "kuruş"),
    "$": ("dolar", "sent"), "USD": ("dolar", "sent"), "dolar": ("dolar", "sent"),
    "€": ("avro", "sent"), "EUR": ("avro", "sent"), "avro": ("avro", "sent"),
    "£": ("sterlin", "peni"), "GBP": ("sterlin", "peni"), "sterlin": ("sterlin", "peni"),
}
_PARA_EKI = r"(?:['’]([a-zA-ZçğıöşüÇĞİÖŞÜ]+))?"
# Ardında birim: "1.250,50 TL", "2450.75 $", "25 €'ya". Kesmeden sonraki ek yazılan birime göredir (TL'den = "tele"
# göre); okunuşta son sözcüğe uydurulur.
_PARA_ARDINDA = re.compile(r"\b([\d.]+?)(?:,(\d{1,2}))?\s?(₺|[$€£]|(?:TL|USD|EUR|GBP|lira|dolar|avro|sterlin)\b)"
                           + _PARA_EKI, re.ASCII)
# Önünde simge: "$100", "€1.250,50", "$2,450.75" (İngilizce yazım), "£5'a"
_PARA_ONUNDE = re.compile(r"(?<![\w$€£₺])([$€£₺])\s?(\d(?:[\d.,]*\d)?)" + _PARA_EKI)
_INGILIZCE_TUTAR = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?")


def tutar_oku(tam: str, kurus: str, birim: str, ek: str = "") -> str:
    """("1.250", "5", "TL") -> "bin iki yüz elli lira elli kuruş", ("2450.75", "", "$") -> "iki bin dört yüz elli
    dolar yetmiş beş sent", ("0", "99", "€") -> "doksan dokuz sent" (sıfır ana birim söylenmez)."""
    ana, alt = PARA_BIRIMLERI[birim]
    # "2450.75 TL": noktadan sonra 1-2 rakam binlik grup olamaz, İngilizce usulü kuruştur (önceden 245.075 lira)
    noktali = re.fullmatch(r"(\d+)\.(\d{1,2})", tam)
    if noktali and not kurus:
        tam, kurus = noktali.groups()
    if kurus and len(kurus) == 1:
        kurus += "0"  # "1,5 TL" bir lira elli kuruştur, beş kuruş değil
    deger = sayiyi_coz(tam)
    cikti = f"{sayi_oku(deger)} {ana}"
    if kurus and int(kurus):
        cikti = (f"{cikti} " if deger else "") + f"{sayi_oku(kurus)} {alt}"
    return ek_ekle(cikti, ek)


def _onunde_oku(e: re.Match) -> str:
    birim, tutar, ek = e.group(1), e.group(2), e.group(3) or ""
    if _INGILIZCE_TUTAR.fullmatch(tutar):
        tam, _, kurus = tutar.replace(",", "").partition(".")
    else:
        tam, _, kurus = tutar.rpartition(",") if "," in tutar else (tutar, "", "")
    if not re.fullmatch(r"[\d.]+", tam):
        return e.group(0)
    if len(kurus) > 2:  # "$3,14159": tutar değil ondalık sayı
        okunus = f"{ondalik_oku(sayiyi_coz(tam), kurus)} {PARA_BIRIMLERI[birim][0]}"
        return ek_ekle(okunus, ek)
    return tutar_oku(tam, kurus, birim, ek)


def para_oku(metin: str) -> str:
    """Tutarları okur: "1.250,50 ₺" -> "bin iki yüz elli lira elli kuruş", "$100'den" -> "yüz dolardan",
    "25 €" -> "yirmi beş avro", "10,5 GBP" -> "on sterlin elli peni"."""
    m = _PARA_ARDINDA.sub(lambda e: tutar_oku(e.group(1), e.group(2) or "", e.group(3), e.group(4) or ""), metin)
    return _PARA_ONUNDE.sub(_onunde_oku, m)
