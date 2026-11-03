"""
Teknik metin — makale, rapor ve belgelerde sık geçen ama genel kuralların yanlış okuduğu yazımlar.

Sorun (03.11.2026, gerçek makalelerden): "Sentinel-2" → "sentinel, iki" (tire duraklama oldu), "Qwen2.5" →
"qweniki virgül beş", "v0.2.1" → "vsıfır nokta…", "10 m" → "on m", "24 kHz" → "khz", "LinkedIn + Medium" → "+"
okunmadı, "LLM" → "le le me". Bu modül normalize()'nin 4. adımından (telaffuz sözlüğü) hemen sonra, sayı
kurallarından önce çalışır:

  1. sürüm: "v0.2.1" → "ve 0 nokta 2 nokta 1"; harfe bitişik noktalı sayı "Qwen2.5" → "Qwen 2 nokta 5"
  2. sözcük içi kısa çizgi boşluk olur: "Sentinel-2" → "Sentinel 2", "e-Devlet" → "e Devlet"
     (sayı aralığı "3-5" ve tarih "2026-03-15" dokunulmadan kalır; onları sonraki kurallar okur)
  3. harf-rakam bitişiği ayrılır: "4o" → "4 o", "GPT4" → "GPT 4" (birim ve terimler hariç: "m2", "wgs84")
  4. sayıdan sonra birim: "10 m" → "10 metre", "24 kHz" → "24 kilohertz", "16 GB" → "16 gigabayt"
  5. simgeler: sözcükler arası "+" → "ve", "→" → virgül, sayılar arası "×" → "çarpı"

Büyük harfli teknik kısaltmaların yerleşik okunuşu TEKNIK_KISALTMALAR'da (kisaltmalari_oku kullanır); İngilizce
teknik terimlerin Türkçe okunuşu TEKNIK_TERIMLER'de (varsayılan telaffuz sözlüğüne katılır).
"""
from __future__ import annotations

import re

#: Harf harf okunduğunda yerleşik okunuştan ayrılan teknik kısaltmalar. Geri kalanı Türkçe harf adlarıyla okunur
#: ("CBS" → "ce be se", "GPU" → "ge pe u"). Ek kesmeden sonra eklenir: "LLM'ler" → "el el emler".
TEKNIK_KISALTMALAR = {
    "LLM": "elelem", "API": "ey pi ay", "AI": "ey ay", "NLP": "en el pi", "ML": "em el", "RAG": "rag",
    "GIS": "cis", "SQL": "es kü el", "HTTP": "ha te te pe", "HTTPS": "ha te te pe es", "GPS": "ce pe es",
    "UI": "yu ay", "UX": "yu eks", "PR": "pi ar", "MIT": "em ay ti", "CC": "si si", "BY": "bay",
    "SA": "es ey", "MOS": "mos", "GGUF": "ce ce yu ef", "ONNX": "oniks", "CUDA": "kuda", "JSON": "ceyson", "WER": "ve e re",
}

#: İngilizce teknik terimler → Türk kulağına doğru gelen yazım (CBS_TERIMLERI ile aynı kural: anahtar küçük harf,
#: değer modelin doğru okuyacağı yazım).
TEKNIK_TERIMLER = {
    # yapay zekâ
    "prompt engineering": "prompt encinıring", "fine-tuning": "fayn tuning", "fine tuning": "fayn tuning",
    "finetuning": "fayn tuning", "benchmark": "bençmark", "dataset": "deyta set", "transformer": "transformır",
    "transformers": "transformırs", "inference": "inferıns", "agent": "eycınt", "agents": "eycınts",
    "reasoning": "riizıning", "open source": "opın sors", "open-source": "opın sors", "deep learning": "dip lörning",
    "machine learning": "maşin lörning", "deepseek": "dipsik", "flash": "fleş", "gemma": "cema", "qwen": "kuven",
    "llama": "lama", "claude": "klod", "gemini": "cemini", "chatgpt": "çet ce pe te", "gpt": "ce pe te",
    "openai": "opın ey ay", "anthropic": "antropik", "hugging face": "haging feys", "huggingface": "haging feys",
    "whisper": "visper", "next": "nekst", "plus": "plas", "common voice": "komın voys", "voice": "voys", "iot": "ay o ti", "saas": "sas", "lora": "lora", "llms": "el el emler",
    # yazılım
    "python": "paytın", "pytorch": "paytorç", "github": "githab", "docker": "dokır", "pipeline": "payplayn",
    "framework": "freymvörk", "backend": "bekend", "server": "sörvır", "deploy": "diploy", "open": "opın",
    "software": "softver", "hardware": "hardver", "online": "onlayn", "offline": "oflayn", "streaming": "striming",
    "repository": "repozitori", "postgresql": "postgre es kü el", "linux": "linuks", "javascript": "cavaskript",
    "typescript": "tayp skript", "react": "riekt", "node": "nod", "runtime": "rantaym", "pypi": "pay pi ay",
    "pip": "pip", "espeak": "i spik", "tts": "te te se", "stt": "es te te", "g2p": "ce tu pi", "ipa": "i pe a",
    "utmos": "yu ti mos", "wav2vec2": "veyv tu vek tu", "wav2vec": "veyv tu vek", "styletts2": "stayl te te se iki",
    "voxcpm2": "voks ce pe me iki", "readme": "ridmi", "changelog": "çeynclog",
    "turkce": "türkçe",                                  # paket adı "turkce-vurgu"
    "uslup": "üslup", "sinav": "sınav", "plbert": "pe le bert",     # paket adları "turkce-uslup", "turkce-tts-sinav"
    # lisans ve atıf satırları ("Contains modified Copernicus Sentinel data", "© OpenStreetMap katkıda bulunanlar")
    "contains": "kınteyns", "modified": "modifayd", "copernicus": "kopernikus", "openstreetmap": "opın strit mep",
    # platformlar
    "linkedin": "linkdin", "medium": "midyım", "kaggle": "kegıl", "runpod": "ran pod", "colab": "kolab",
    "notebook": "notbuk", "podcast": "podkast", "startup": "startap", "feedback": "fidbek", "workshop": "vörkşop",
}

#: Noktalı sayıdan önce gelince sayının sürüm olduğunu gösteren adlar ("Llama 3.1", "Python 3.12"): nokta okunur.
SURUMLU_ADLAR = {"llama", "lama", "qwen", "kuven", "gemma", "cema", "gpt", "python", "paytın", "claude", "klod",
                 "gemini", "cemini", "mistral", "phi", "deepseek", "dipsik", "glm", "ubuntu", "android", "ios",
                 "windows", "vindovs", "sürüm", "sürümü", "version"}

_UNLULER = set("AEIİOÖUÜ")


def okunabilir(kelime: str) -> bool:
    """4-5 harfli büyük harfli yazım Türkçe sözcük gibi okunabilir mi ("EVREN", "NATO", "TÜİK", "ODTÜ"; harf harf
    okunur: "TBMM", "KPSS", "EPDK", "İETT"). Başta ünsüz kümesi, üç ünsüz yan yana, sonda aynı ünsüz iki kez ya da
    her üç harfte birden az ünlü varsa okunamaz. 03.11.2026: "EVREN" "e ve re e ne" diye harf harf okunuyordu."""
    if not 4 <= len(kelime) <= 5 or not kelime.isalpha() or set(kelime) <= set("IVXLCDM") or len(set(kelime)) < 3:
        return False
    unlu = [c in _UNLULER for c in kelime]
    if sum(unlu) * 3 < len(kelime) or (not unlu[0] and not unlu[1]):
        return False
    if any(not (unlu[i] or unlu[i + 1] or unlu[i + 2]) for i in range(len(kelime) - 2)):
        return False
    return not (not unlu[-1] and kelime[-1] == kelime[-2])


_SURUM = re.compile(r"(?<![^\W\d_])[vV](\d+(?:\.\d+)+)(?![\d.]*\d)")
_HARFE_BITISIK_NOKTALI = re.compile(r"(?<=[A-Za-zÇĞİÖŞÜçğıöşü])(\d+)\.(\d+)(?![\d.,]*\d)")
_ADDAN_SONRA_NOKTALI = re.compile(r"(?<![^\W_])([^\W\d_]+)[ \t]+(\d+)\.(\d+)(?![\d.,]*\d)")
_TIRELI = re.compile(r"[^\s]*[-‐‑][^\s]*")
_HARF = re.compile(r"[^\W\d_]")
_HARF_RAKAM = re.compile(r"(?<=[A-Za-zÇĞİÖŞÜçğıöşü])(?=\d)|(?<=\d)(?=[A-Za-zÇĞİÖŞÜçğıöşü])")
#: Harf-rakam bitişiği ayrılmayan yazımlar: birim (m², cm3), sayıya kesmesiz ek yok sayılır, IBAN başı (TR33).
_BITISIK_KALIR = re.compile(r"^(?:[ckm]?m[23²³]|TR\d{2}|\d+'[a-zçğıöşü]{1,6})$")
#: Tek başına ünsüz harf: küçük harf yalnız sayıdan sonra ("gemma-4-31b" → "31 b" → "31 be"; adres okunuşundaki
#: "a bölü b" dokunulmaz), büyük harf her yerde ("B planı"); ardında nokta olan büyük harf (Roma rakamı "V.", baş
#: harf "M.") dokunulmaz.
_TEK_HARF = re.compile(r"(?:(?<=\d )([b-df-hj-np-tv-zçğş])(?![^\W_]|['’])"
                       r"|(?<![^\W_]|['’.])([BCDFGHJ-NP-TV-ZÇĞŞ])(?![^\W_]|['’.]))")

BIRIM_OKUNUSU = {
    "m": "metre", "kHz": "kilohertz", "Hz": "hertz", "MHz": "megahertz", "GHz": "gigahertz",
    "KB": "kilobayt", "kB": "kilobayt", "MB": "megabayt", "GB": "gigabayt", "TB": "terabayt",
    "ms": "milisaniye", "W": "vat", "kW": "kilovat", "kWh": "kilovatsaat", "MW": "megavat", "mAh": "miliamper saat",
    "V": "volt", "dB": "desibel", "fps": "efpiyes", "bit": "bit", "bayt": "bayt", "px": "piksel", "ha": "hektar",
}
_BIRIM = re.compile(r"(?<=\d)[ \t]?(" + "|".join(sorted(map(re.escape, BIRIM_OKUNUSU), key=len, reverse=True))
                    + r")(?![^\W_]|[²³])")
#: Ondalıklı aralık "2,5–5 katı" (tamsayı aralıklarını normalize.araliklari_oku okur).
_ONDALIK_ARALIK = re.compile(r"(?<![\d.,])(\d+,\d+|\d+)[ \t]?[–-][ \t]?(\d+,\d+|\d+)(?![\d.,]*\d)")
#: Ünlüsüz küçük harf kümesi Türkçe sözcük olamaz, harf harf okunur ("seslen-tr" → "seslen te re"); birim ve
#: noktalı kısaltmalar (km, kg, vb.) sonraki kurallara kalır.
_UNSUZ_KUME = re.compile(r"(?<![^\W_]|['’])([b-df-hj-np-tv-zçğş]{2,4})(?![^\W_]|['’]?\.)")
_UNSUZ_KALIR = {"km", "cm", "mm", "kg", "gr", "lt", "ml", "mg", "kb", "mb", "gb", "tb", "ms", "kwh", "kw", "mw",
                "hz", "khz", "mhz", "ghz", "db", "px", "fps", "sn", "dk", "vb", "vs", "vd", "bkz", "nm", "pp"}
_SOZCUK_ARTI = re.compile(r"(?<=[^\W\d_])[ \t]+\+[ \t]+(?=[^\W\d_])")
_OK = re.compile(r"[ \t]*(?:→|⇒|->|=>)[ \t]*")
_CARPI = re.compile(r"(?<=\d)[ \t]*[×x][ \t]*(?=\d)")
#: Arasında tek küçük harf olan büyük harfli kısaltma ("ODbL", "PhD"): büyük harfe çevrilip kısaltma gibi okunur
#: (03.11.2026: "ODbL" "odbu" duyuluyordu). Teknik terimler ("PyPI") kendi okunuşunu korur.
_KARISIK_KISALTMA = re.compile(r"(?<![^\W_])([A-ZÇĞİÖŞÜ]{1,3}[a-zçğıöşü][A-ZÇĞİÖŞÜ]{1,3})(?![^\W_])")


def _surum(e: re.Match) -> str:
    return "ve " + " nokta ".join(e.group(1).split("."))


def _addan_sonra(e: re.Match) -> str:
    """"Llama 3.1", "CC BY 4.0", "ODbL 1.0", "Common Voice 27.0": ad sürümlüyse, en az iki büyük harfli kısaltmaysa
    ya da sayı ".0" ile bitiyorsa (Türkçede ondalık virgülle yazılır; "27.0" sürümdür) nokta okunur; yoksa ondalık."""
    ad, a, b = e.groups()
    if ad.lower() in SURUMLU_ADLAR or sum(c.isupper() for c in ad) >= 2 or b == "0":
        return f"{ad} {a} nokta {b}"
    return e.group(0)


def _tire(e: re.Match) -> str:
    """Harf içeren tireli yazımda ("Sentinel-2", "e-Devlet", "gemma-4-31b") tire boşluk olur. Harfsiz olanlar
    (aralık "3-5", tarih "2026-03-15", telefon) sonraki kurallara kalır."""
    t = e.group(0)
    return re.sub(r"[-‐‑]", " ", t) if _HARF.search(t) else t


def _ayir(e: re.Match) -> str:
    t = e.group(0)
    return t if _BITISIK_KALIR.match(t) else _HARF_RAKAM.sub(" ", t)


def teknik_uygula(metin: str) -> str:
    """Sürüm, sözcük içi tire, harf-rakam bitişiği, birim ve simgeler (bkz. modül açıklaması)."""
    from .sayilar import harf_oku
    m = _SURUM.sub(_surum, metin)
    m = _KARISIK_KISALTMA.sub(lambda e: e.group(1) if e.group(1).lower() in TEKNIK_TERIMLER
                              else e.group(1).replace("i", "İ").replace("ı", "I").upper(), m)
    m = _HARFE_BITISIK_NOKTALI.sub(lambda e: f" {e.group(1)} nokta {e.group(2)}", m)
    m = _TIRELI.sub(_tire, m)
    m = _ADDAN_SONRA_NOKTALI.sub(_addan_sonra, m)
    m = re.sub(r"[^\s.,;:!?()\[\]\"]+", _ayir, m)
    m = _BIRIM.sub(lambda e: " " + BIRIM_OKUNUSU[e.group(1)], m)
    m = _CARPI.sub(" çarpı ", m)
    m = _ONDALIK_ARALIK.sub(lambda e: f"{e.group(1)} ile {e.group(2)}" if "," in e.group(0) else e.group(0), m)
    m = _UNSUZ_KUME.sub(lambda e: e.group(1) if e.group(1) in _UNSUZ_KALIR
                        else " ".join(harf_oku(h) for h in e.group(1)), m)
    m = _TEK_HARF.sub(lambda e: harf_oku(e.group(1) or e.group(2)), m)    # tek başına ünsüz: "31 b" → "31 be"
    m = _SOZCUK_ARTI.sub(" ve ", m)
    return _OK.sub(", ", m)
