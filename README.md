# turkce-normalize

TTS (metinden sese) modelleri için Türkçe metin normalizasyonu.

Chatterbox, XTTS, Piper, StyleTTS2 gibi açık kaynak modeller SSML desteklemez
ve `1.250,50 ₺`, `14:05`, `XX. yüzyıl`, `TBMM'de` gibi gösterimleri Türkçe
kurallarına göre okuyamaz. Bu paket metni modele göndermeden önce "okunur"
hale getirir:

```text
Toplantı 14:30'da, %18 KDV dahil 1.250,50 ₺.
→ Toplantı on dört otuzda, yüzde on sekiz katma değer vergisi dahil bin iki yüz elli lira elli kuruş.
```

- Bağımlılığı yoktur (yalnızca standart kütüphane), Python 3.9+.
- Kurallar sıralıdır ve her biri testlerle sabitlenmiştir.
- Akış halinde gelen LLM çıktısı için kısaltma farkında bir cümle ayırıcı içerir.

## Kurulum

```bash
pip install .            # depo kökünde
```

## Kullanım

```python
from turkce_normalize import normalize

normalize("Sözleşme 15.03.2026 tarihinde yenilenecek.")
# 'Sözleşme on beş mart iki bin yirmi altı tarihinde yenilenecek.'

normalize("XX. yüzyılda II. Abdülhamit 1876-1909 arasında hüküm sürdü.")
# 'yirminci yüzyılda ikinci Abdülhamit bin sekiz yüz yetmiş altı ile bin dokuz yüz dokuz arasında hüküm sürdü.'

normalize("TBMM'de TRT ve NATO konuşuldu.")
# 'te be me mede te re te ve nato konuşuldu.'
```

Komut satırından:

```bash
python -m turkce_normalize "Tarifte 1/2 kilo un, 3/4 su bardağı süt var."
# Tarifte yarım kilo un, dörtte üç su bardağı süt var.

echo "3-5 kişilik ekip -5 derecede çalıştı." | python -m turkce_normalize
# üç beş kişilik ekip eksi beş derecede çalıştı.
```

### Seçenekler

```python
normalize(metin,
          telaffuz=None,             # telaffuz sözlüğü (varsayılan: gömülü CBS/yazılım sözlüğü)
          cografi=True,              # koordinat, ölçek, pafta, EPSG kuralları
          kisaltma_harf_harf=True)   # "TBMM" -> "te be me me"
```

### Sayı okuma

```python
from turkce_normalize import sayi_oku, sira_oku, ondalik_oku, rakamlari_tek_tek

sayi_oku(1250)            # 'bin iki yüz elli'
sayi_oku(1_000_000)       # 'bir milyon'
sira_oku(21)              # 'yirmi birinci'
ondalik_oku(3, "05")      # 'üç virgül sıfır beş'
rakamlari_tek_tek("0212") # 'sıfır iki bir iki'
```

### Cümle ayırıcı (LLM akışı için)

Cevabın tamamı bitmeden ilk cümle seslendirilmeye başlasın diye. `Sn. Dr.`
gibi kısaltmalarda ve `15.03.2026` gibi tarihlerde bölmez; 12 karakterden
kısa cümleleri ("Evet.") sonrakiyle birleştirir.

```python
from turkce_normalize import CumleAyirici, cumleleri_ayir

ayirici = CumleAyirici()
for parca in llm_akisi:                 # token token gelen metin
    for cumle in ayirici.push(parca):
        seslendir(normalize(cumle))
for cumle in ayirici.flush():
    seslendir(normalize(cumle))

cumleleri_ayir("Merhaba. Sn. Dr. Ayşe Yılmaz geldi! Devam edelim mi?")
# ['Merhaba. Sn. Dr. Ayşe Yılmaz geldi!', 'Devam edelim mi?']
```

`cumle_akisi(iterable)` ve `cumle_akisi_async(async_iterable)` aynı işi
üreteç olarak yapar.

### Duraklama işaretleri

SSML olmayan modellerde duraklamayı kendin kurmak için metni `[dur]`
işaretlerinden böler:

```python
from turkce_normalize import isaretleri_ayir, isaretleri_temizle

isaretleri_ayir("Sorgu bitti. [dur:0.8] Toplam 340 hektar.")
# [Parca(metin='Sorgu bitti.', duraklama=0.8), Parca(metin='Toplam 340 hektar.', duraklama=0)]

isaretleri_temizle("Sorgu bitti. [dur:0.8] Toplam.")   # altyazı için
# 'Sorgu bitti. Toplam.'
```

`[dur]` tek başına 0,45 sn'dir; üst sınır 5 sn. Bilinmeyen işaretler
(`[vurgu]`) bilerek silinmez — model okur, sen hatayı duyarsın.

### Telaffuz sözlüğü

Gömülü sözlük CBS ve yazılım jargonunu Türk kulağına doğru gelen yazımla
değiştirir (`shapefile` → `şeypfayl`, `WMS` → `ve me se`, `API` → `ey pi ay`).
Kendi terimlerini ekleyebilirsin:

```python
from turkce_normalize import normalize, sozluk_birlestir, VARSAYILAN_SOZLUK

sozluk = sozluk_birlestir(VARSAYILAN_SOZLUK, {"KENTGIS": "kent cis"})
normalize("KENTGIS açılıyor.", telaffuz=sozluk)    # 'kent cis açılıyor.'
```

Eşleşme büyük/küçük harf duyarsızdır; ek almış kelimeler (`APIyi`) bölünmez.

## Desteklenen gösterimler

| Gösterim | Örnek | Okunuş |
|---|---|---|
| Tam sayı | `1.250` | bin iki yüz elli |
| Ondalık | `3,5` / `3,05` | üç virgül beş / üç virgül sıfır beş |
| Sıra sayısı | `3. madde` | üçüncü madde |
| Para | `1.250,50 ₺`, `2.360 TL` | bin iki yüz elli lira elli kuruş |
| Yüzde | `%18`, `% 18,5` | yüzde on sekiz |
| Tarih | `15.03.2026`, `15/03/2026` | on beş mart iki bin yirmi altı |
| Saat | `14:05`, `09:00'da` | on dört sıfır beş, dokuzda |
| Telefon | `0212 555 44 33`, `0212-555-44-33` | sıfır iki bir iki beş beş beş … |
| IBAN | `TR33 0006 …` | te re üç üç sıfır sıfır … |
| Kısaltma (sözlük) | `KDV`, `Dr.`, `vb.`, `Mah.` | katma değer vergisi, doktor, ve benzeri, mahallesi |
| Birim | `12 km`, `85 m²`, `5 kg` | on iki kilometre, … metrekare, … kilogram |
| **Roma rakamı** | `XX. yüzyıl`, `II. Abdülhamit` | yirminci yüzyıl, ikinci Abdülhamit |
| **Kesir** | `1/2 kilo`, `1/4`, `3/4`, `1/6`, `2 1/2` | yarım kilo, çeyrek, dörtte üç, altıda bir, iki buçuk |
| **Aralık** | `3-5 kişi`, `2020-2025`, `3-5. maddeler` | üç beş kişi, … ile …, üçüncü ile beşinci |
| **Eksi sayı** | `-5 derece` | eksi beş derece |
| **Büyük harfli kısaltma** | `TBMM'de`, `CHP`, `NATO` | te be me mede, ce he pe, nato |
| **E-posta** | `ali.veli@ornek.com.tr` | ali nokta veli et ornek nokta com nokta te re |
| **Web adresi** | `https://www.ornek.gov.tr/harita` | ornek nokta gov nokta te re bölü harita |
| **Simgeler** | `2+2=4`, `&`, `25°C`, `±0,5` | iki artı iki eşittir dört, ve, yirmi beş derece, artı eksi … |
| Koordinat | `39.9334, 32.8597` | enlem otuz dokuz virgül dokuz üç üç dört, boylam … |
| Derece-dakika-saniye | `39°56'12"K` | otuz dokuz derece elli altı dakika on iki saniye kuzey |
| Ölçek | `1/25.000`, `1:1000` | yirmi beş binde bir, binde bir |
| Pafta kodu | `G22-b-14c-2d` | ge yirmi iki be on dört ce iki de |
| EPSG / UTM | `EPSG:5254`, `UTM 35N` | e pe es ge beş iki beş dört, u te me otuz beşinci dilim kuzey |
| Alan birimi | `340 ha`, `12 da` | üç yüz kırk hektar, on iki dekar |

Kalın satırlar kaynak projede olmayıp bu pakette eklenenlerdir. Ayrıntıları:

### Roma rakamları

Yalnızca **ardından nokta gelen** geçerli Roma rakamları (I–MMMM) sıra sayısı
olarak okunur:

- Nokta ve ardından **küçük harfle** başlayan kelime: `XX. yüzyıl` → yirminci yüzyıl.
- Nokta ve ardından **büyük harfle** başlayan kelime (hükümdar sırası): yalnızca
  I, V, X harflerinden oluşan ve 39'u aşmayan rakamlar: `III. Selim` → üçüncü Selim,
  `I. Dünya Savaşı` → birinci Dünya Savaşı.
- Tek harfli rakam büyük harfli bir kelimeden sonra geliyorsa isim baş harfi
  sayılır (`Mehmet V. Delibaş` değişmez); `Sultan`, `Kral`, `Papa` gibi
  unvanlar (`UNVANLAR`) istisnadır.
- `MI`, `CD`, `CM`, `MM`, `DIV` … gibi kelime/kısaltma olabilenler kara
  listededir (`ROMA_KARA_LISTE`).

### Kesirler

- `1/2` → yarım, `1/4` → çeyrek; ötekiler "payda + bulunma eki + pay":
  `3/4` → dörtte üç, `2/3` → üçte iki, `1/6` → altıda bir, `3/40` → kırkta üç.
- Bulunma eki ünlü uyumuna ve ünsüz benzeşmesine uyar (`bulunma_eki()`):
  ç, f, h, k, p, s, ş, t'den sonra **te/ta**, diğerlerinde **de/da**.
- Tam sayılı kesir: `2 1/2` → iki buçuk, `3 3/4` → üç tam dörtte üç; `½ ¼ ¾`
  karakterleri de okunur.
- Yalnızca **bayağı kesirler** (pay < payda) okunur. `24/7`, `15/03` dokunulmaz.
- Tarih (`15/03/2026`) ve ölçek (`1/25.000`, `1:1000`) kuralları önce çalışır.
- Adreste kapı numarası: `No: 5/7` → No: beş bölü yedi.

### Aralıklar

- İki sayı da 100 veya küçük ve ilki küçükse günlük konuşmadaki gibi:
  `3-5 kişi` → üç beş kişi, `10–20 dakika` → on yirmi dakika.
- Diğerleri "X ile Y": `2020-2025` → iki bin yirmi ile iki bin yirmi beş,
  `1.000-2.000 TL` → bin ile iki bin lira.
- Sıra sayısı aralığı: `3-5. maddeler` → üçüncü ile beşinci maddeler.
- Saat ve tarih aralığı: `14:30-15:30` → on dört otuz ile on beş otuz;
  yüzde aralığı: `%10-20` → yüzde on ile yirmi.
- İlki büyük ya da eşitse (`3-1` skor olabilir), sıfırla başlıyorsa (kod) veya
  ikiden fazla sayı tireyle bağlıysa (`0212-555-44-33`) aralık sayılmaz.
- Önünde harf/rakam olmayan tire eksi işaretidir: `-5 derece` → eksi beş derece.

### Büyük harfli kısaltmalar

- 2–5 büyük harften oluşan tokenlar Türkçe harf adlarıyla okunur:
  `TBMM` → te be me me, `AKP` → a ke pe. Harf adları: a, be, ce, çe, de, e, fe,
  ge, yumuşak ge, he, ı, i, je, ke, le, me, ne, o, ö, pe, re, se, şe, te, u, ü,
  ve, ye, ze; Q kü, W çift ve, X iks.
- Kesmeden sonraki ek okunuşa bitişir: `TBMM'de` → te be me mede,
  `ABD'li` → a be deli.
- Kelime gibi okunan kısaltmalar (`KELIME_GIBI_OKUNANLAR`) harf harf okunmaz,
  modelin hecelememesi için küçük harfe çevrilir: NATO, NASA, AFAD, TOKİ,
  BOTAŞ, TEDAŞ, İSKİ, ASKİ, ODTÜ, YÖK, TÜİK, İŞKUR, MİT, ASELSAN, TÜBİTAK,
  HAVELSAN, ROKETSAN, KOSGEB, UNESCO, UNICEF … `ÖSYM`, `SGK`, `İETT`, `PTT`
  harf harf okunur.
- Büyük harfle yazılmış sıradan kelimeler (`UYARI`, `VE`, `MI` …,
  `BILINEN_KELIMELER`) ve bunların komşusu olan büyük harfli kelimeler
  (`GELDİ MI`) kısaltma sayılmaz. 6+ harfli tokenlar ve yalnızca I/V/X'ten
  oluşanlar (Roma rakamı) dokunulmaz.
- Sözlükteki kısaltmalar (`KDV`, `TL`, `IBAN` …) önce gelir.
- Listeler genişletilebilir kümelerdir:

  ```python
  from turkce_normalize import KELIME_GIBI_OKUNANLAR, BILINEN_KELIMELER
  KELIME_GIBI_OKUNANLAR.add("TEKNOFEST")
  BILINEN_KELIMELER.add("KAMPANYA")
  ```

### E-posta ve web adresi

- `@` → et, `.` → nokta, `/` → bölü, `-` → tire, `_` → alt çizgi.
- `http(s)://` ve `www.` atılır; sorgu (`?…`) ve çapa (`#…`) okunmaz.
- Son etiket iki harfli ülke uzantısıysa harf harf okunur (`tr` → te re);
  `com`, `gov`, `org` yazıldığı gibi kalır.
- Şemasız alan adları yalnızca küçük harfle ve bilinen bir uzantıyla
  (`com`, `net`, `org`, `gov`, `edu`, `tr`, `io` …) yazılmışsa yakalanır.
- Adres parçaları sonra telaffuz sözlüğünden geçer: `rapor.pdf` → rapor nokta pe de fe.

### Simgeler

`&` → ve; `+` iki sayı arasında → artı (`+90` gibi önekler dokunulmaz);
`=` → eşittir; `°C` / `℃` → derece; `°F` → derece fahrenhayt;
sayıdan sonra `°` → derece; `±` → artı eksi.

## Kural sırası

Sıra rastgele değildir; bütün bir birim olan gösterimler sayı kurallarından
önce gelir, yoksa içlerindeki rakamlar genel kurallara yem olur:

1. e-posta ve web adresi → 2. sıcaklık → 3. coğrafi gösterimler →
4. telaffuz sözlüğü → 5. IBAN → 6. telefon → 7. tarih ve saat →
8. simgeler → 9. kesirler → 10. aralıklar → 11. eksi sayılar → 12. para →
13. yüzde → 14. kısaltmalar ve birimler → 15. Roma rakamları →
16. büyük harfli kısaltmalar → 17. sıra sayıları → 18. ondalık →
19. tam sayılar → 20. kesme işaretinin kaldırılması

## Sınırlamalar

- Ek uyumu yapılmaz: `5'te` → beşte doğru çıkar çünkü ek zaten okunuşa göre
  yazılmıştır; ama yanlış yazılmış ekler düzeltilmez.
- Nokta binlik ayırıcıdır: `3.5` "otuz beş" okunur (Türkçe yazımda ondalık
  ayırıcı virgüldür).
- Sıra sayısı ve Roma rakamı için ardından bir kelime gelmesi gerekir; cümle
  sonundaki `XIV.` dokunulmaz.
- Cümle başındaki büyük harf, dönüştürülen kelimeyle birlikte kaybolur
  (`XX. yüzyıl` → yirminci yüzyıl).
- Büyük harfli kısaltma tespiti sezgiseldir: listede olmayan 2–5 harfli büyük
  harfli sıradan kelimeler harf harf okunabilir; tamamı büyük harfle yazılmış
  metinlerde `kisaltma_harf_harf=False` kullanın. Tek harfli Roma rakamı bir
  ismin baş harfiyle karışabilir (`romanı V. Hugo yazdı`).
- Ek almış kesirlerde (`1/2'si`) ek paya bağlanır: "ikide birsi".
- `24/7` gibi bileşik kesirler, ISO tarih (`2026-03-15`), skor (`3-1`) ve
  tireli tarih (`15-03-2026`) özel olarak okunmaz.
- Şemasız alan adlarında Türkçe karakter (IDN) desteklenmez.
- İngilizce normalizasyon kapsam dışıdır; metin Türkçe kabul edilir.

## Testler

```bash
python -m unittest discover -s tests
```

`tests/test_parite.py` kaynak TypeScript projesindeki testlerin birebir
karşılığıdır (beklenen çıktılar aynı); `tests/test_yeni.py` bu pakette
eklenen özellikleri ve yanlış pozitifleri sabitler.

## Lisans

MIT — bkz. [LICENSE](LICENSE).

---

## English summary

**turkce-normalize** is a dependency-free Python (3.9+) text normalizer that
prepares Turkish text for TTS engines without SSML support (Chatterbox, XTTS,
Piper, StyleTTS2…). It spells out numbers, ordinals, decimals, money, percent,
dates, times, phone numbers, IBANs, abbreviations and units; Roman numerals
(`XX. yüzyıl` → "yirminci yüzyıl"), fractions with correct vowel harmony
(`3/4` → "dörtte üç"), numeric ranges, negative numbers, all-caps acronyms read
letter by letter with Turkish letter names (`TBMM'de` → "te be me mede", with a
configurable list of acronyms read as words such as NATO, TÜBİTAK), e-mail
addresses and URLs, common symbols, and GIS notation (coordinates, map scale,
sheet codes, EPSG/UTM). It also ships an abbreviation-aware streaming sentence
splitter for LLM output and an inline pause-marker parser (`[dur:0.8]`).

```python
from turkce_normalize import normalize
normalize("Toplantı 14:30'da, %18 KDV dahil 1.250,50 ₺.")
# 'Toplantı on dört otuzda, yüzde on sekiz katma değer vergisi dahil bin iki yüz elli lira elli kuruş.'
```

CLI: `python -m turkce_normalize "metin"`. Tests: `python -m unittest discover -s tests`. License: MIT.
