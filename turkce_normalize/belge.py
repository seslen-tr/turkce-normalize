"""
Belge okuyucu — Markdown / HTML / düz metin belgesini sesli okunacak düz metne çevirir.

Sorun (03.11.2026): makaleler Markdown'du; "<!-- yorum -->", "#", "**", "- ", tablo çizgileri modele gidince
anlamsız ses çıktı, başlık sonraki paragrafla tek cümle oldu ("…ölçtüm Hazır İngilizce…"), tablo tek dev cümle
oldu ve model çöktü (PL-BERT 512 işaret sınırı). ``okunur_metin`` belgenin yapısını cümle yapısına çevirir:

  - HTML yorumu, etiketi, kod bloğu (```…```) atılır; satır içi `kod` içeriğiyle okunur
  - başlık kendi cümlesi olur ("## İki set" → "İki set.")
  - liste maddesi kendi cümlesi olur; numaralı madde sıra sayısıyla başlar ("1. Madde…" → "Birincisi: Madde…")
  - **kalın**, *eğik*, [bağlantı](adres) işaretleri atılır, yalnız metin kalır; görsel atılır
  - tablo satır satır okunur: ilk hücre, sonra "başlık, değer" çiftleri
  - çıplak web adresi yalnız alan adıyla kalır (yol ve sorgu okunmaz); etiket satırı (#EVREN #LLM) atılır
  - noktalama ile bitmeyen satır (başlık, madde, tablo satırı) nokta alır

Paragraflar boş satırla ayrılır (``paragraflar`` ile listesi alınır); seslendirici paragraf arasında daha uzun
duraklar. ``uzun_cumleyi_bol`` modelin işaret sınırını aşan cümleyi noktalı virgül, virgül ya da sözcük sınırından
böler.
"""
from __future__ import annotations

import re
from typing import List

from .normalize import _alan_adi_oku, eki_uydur, eposta_ve_adres_oku
from .sayilar import sira_oku, turkce_buyuk

_YORUM = re.compile(r"<!--.*?(?:-->|$)", re.S)
_KOD_BLOGU = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.S | re.M)
_ETIKET = re.compile(r"</?[A-Za-z][^>\n]{0,200}>")
_GORSEL = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_BAGLANTI = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_SATIR_ICI_KOD = re.compile(r"`([^`\n]+)`")
_KALIN = re.compile(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1")
_EGIK = re.compile(r"(?<![\w*])([*_])(?=\S)(.+?)(?<=\S)\1(?![\w*])")
_BASLIK = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
_MADDE = re.compile(r"^\s*[-*+•]\s+(.*)$")
_NUMARALI = re.compile(r"^\s*(\d{1,3})[.)]\s+(.*)$")
_ALINTI = re.compile(r"^\s*>\s?")
_CIZGI = re.compile(r"^\s*([-*_=])(?:\s*\1){2,}\s*$")
_TABLO_AYRAC = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?\s*$")
_ETIKET_SATIRI = re.compile(r"^\s*(?:#[^\s#]+\s*)+$")
_SONDAKI_ETIKET = re.compile(r"(?:\s+#[^\W\d_][\w]*)+\s*$")
_URL = re.compile(r"(?:https?://|www\.)([^\s/<>\"'’)]+)[^\s<>\"'’)]*", re.IGNORECASE)
_BITIS = re.compile(r"[.!?…:;]$")
_CIPLAK_ADRES = re.compile(r"(?<![\w@./-])([a-zA-Z0-9][a-zA-Z0-9-]*(?:\.[a-zA-Z0-9-]+)*\.(?:com|net|org|gov|edu|io|ai|"
                           r"dev|app|co|tr|de|uk|eu|us|info))/[^\s<>\"'’)\]]*")


def _satir_ici(s: str) -> str:
    s = _GORSEL.sub("", s)
    s = _BAGLANTI.sub(r"\1", s)
    s = _SATIR_ICI_KOD.sub(r"\1", s)
    s = _KALIN.sub(r"\2", s)
    s = _EGIK.sub(r"\2", s)
    # yalnız alan adı, okunur hâliyle ("evren nokta ornek nokta org nokta te re"): noktalı yazım cümle bölücüde
    # "evren." "ornek." diye ayrı cümlelere bölünüyordu
    s = _URL.sub(lambda e: eposta_ve_adres_oku(e.group(1).removeprefix("www.").rstrip(".,;:").lower()), s)
    # şemasız adres ("evren.ssyz.org.tr/users/u43bd…"): yolu da okunmaz, yalnız alan adı (03.11: kimlik okunuyordu)
    s = _CIPLAK_ADRES.sub(lambda e: _alan_adi_oku(e.group(1).lower()), s)
    return re.sub(r"\s+", " ", s).strip()


def _sirali(n: int, metin: str) -> str:
    """Numaralı madde ya da başlık: 3, "Görev" → "Üçüncüsü: Görev" (birincisi, üçüncüsü, altıncısı)."""
    sira = sira_oku(n)
    sira += eki_uydur(sira, "si")
    return f"{turkce_buyuk(sira[0])}{sira[1:]}: {metin}"


def _bitir(s: str) -> str:
    s = s.strip()
    return s if not s or _BITIS.search(s) else s + "."


def _hucreler(satir: str) -> List[str]:
    return [_satir_ici(h) for h in satir.strip().strip("|").split("|")]


def _tablo(satirlar: List[str]) -> List[str]:
    """Başlık + satırlar → her satır bir cümle: "deepseek: Mevzuat, %81,2; Madde verilince, %100."."""
    baslik, cumleler = _hucreler(satirlar[0]), []
    for s in satirlar[1:]:
        if _TABLO_AYRAC.match(s):
            continue
        h = _hucreler(s)
        ciftler = [f"{b}, {d}" if b else d for b, d in zip(baslik[1:], h[1:]) if d]
        cumleler.append(_bitir(f"{h[0]}: " + "; ".join(ciftler) if ciftler else h[0]))
    return cumleler


def paragraflar(metin: str) -> List[str]:
    """Belgeyi okunacak paragraflara böler (her biri bir ya da daha çok cümle)."""
    m = _YORUM.sub("\n", metin.replace("\r\n", "\n"))
    m = _KOD_BLOGU.sub("\n", m)
    m = _ETIKET.sub(" ", m)
    satirlar, cikti, paragraf = m.split("\n"), [], []

    def kapat():
        if paragraf:
            cikti.append(" ".join(paragraf))
            paragraf.clear()

    i = 0
    while i < len(satirlar):
        s = satirlar[i]
        if "|" in s and i + 1 < len(satirlar) and _TABLO_AYRAC.match(satirlar[i + 1]):
            kapat()
            j = i + 2
            while j < len(satirlar) and "|" in satirlar[j] and satirlar[j].strip():
                j += 1
            cikti += _tablo([s] + satirlar[i + 1:j])           # her satır kendi paragrafı (bölücü karıştırmasın)
            i = j
            continue
        i += 1
        if not s.strip() or _CIZGI.match(s) or _ETIKET_SATIRI.match(s):
            kapat()
            continue
        s = _ALINTI.sub("", s)
        if (b := _BASLIK.match(s)) is not None:
            kapat()
            baslik = _satir_ici(b.group(1))
            if (n := _NUMARALI.match(baslik)) is not None:              # "## 2. Başlık" → "İkincisi: Başlık"
                baslik = _sirali(int(n.group(1)), n.group(2))
            cikti.append(_bitir(baslik))
            continue
        if (b := _MADDE.match(s)) is not None:
            kapat()
            paragraf.append(_bitir(_satir_ici(b.group(1))))
            kapat()
            continue
        if (b := _NUMARALI.match(_KALIN.sub(r"\2", s))) is not None:      # "**1. Madde…**" de numaralı
            kapat()
            paragraf.append(_bitir(_sirali(int(b.group(1)), _satir_ici(b.group(2)))))
            continue
        paragraf.append(_satir_ici(_SONDAKI_ETIKET.sub("", s)))
    kapat()
    sonuc: List[str] = []
    for p in (re.sub(r"\s+", " ", _bitir(p)).strip() for p in cikti):
        if p and p != "." and (not sonuc or sonuc[-1] != p):          # art arda aynı satır (iki bağlantı) bir kez
            sonuc.append(p)
    return sonuc


def okunur_metin(metin: str) -> str:
    """Belge → düz metin; paragraflar boş satırla ayrılır."""
    return "\n\n".join(paragraflar(metin))


def virgulden_bol(cumle: str, en_cok_sozcuk: int = 12, en_az_sozcuk: int = 4) -> List[str]:
    """Uzun cümleyi virgül, noktalı virgül ve iki noktadan parçalara böler; her parça en çok ``en_cok_sozcuk``
    sözcük (sınırda virgül yoksa olduğundan uzun kalır), en az ``en_az_sozcuk`` (kısa parça komşusuyla birleşir).
    Noktalama parçada kalır ("…, " virgülle biter): seslendirici parçaları ayrı okuyup virgül kadar durur."""
    if len(cumle.split()) <= en_cok_sozcuk:
        return [cumle]
    ham = [p for p in re.split(r"(?<=[,;:])\s+", cumle) if p.strip()]
    cikti: List[str] = []
    for p in ham:
        if cikti and (len(cikti[-1].split()) < en_az_sozcuk
                      or len(cikti[-1].split()) + len(p.split()) <= en_cok_sozcuk):
            cikti[-1] = f"{cikti[-1]} {p}"
        else:
            cikti.append(p)
    if len(cikti) > 1 and len(cikti[-1].split()) < en_az_sozcuk:      # sondaki kısa parça öncekine
        cikti[-2:] = [f"{cikti[-2]} {cikti[-1]}"]
    return cikti


def uzun_cumleyi_bol(cumle: str, en_cok: int = 220) -> List[str]:
    """Uzun cümleyi önce noktalı virgül / iki noktadan, sonra virgülden, en son sözcük sınırından böler; her parça
    ``en_cok`` karakteri aşmaz. Kısa cümle olduğu gibi döner."""
    if len(cumle) <= en_cok:
        return [cumle]
    for ayrac in (r"(?<=[;:])\s+", r"(?<=,)\s+"):
        parca = [p for p in re.split(ayrac, cumle) if p.strip()]
        if len(parca) > 1:
            birlesik, cikti = "", []
            for p in parca:
                if birlesik and len(birlesik) + 1 + len(p) > en_cok:
                    cikti.append(birlesik)
                    birlesik = p
                else:
                    birlesik = f"{birlesik} {p}".strip()
            cikti.append(birlesik)
            return [q for c in cikti for q in uzun_cumleyi_bol(c, en_cok)]
    sozcuk, cikti, satir = cumle.split(), [], ""
    for w in sozcuk:
        if satir and len(satir) + 1 + len(w) > en_cok:
            cikti.append(satir)
            satir = w
        else:
            satir = f"{satir} {w}".strip()
    return cikti + [satir]
