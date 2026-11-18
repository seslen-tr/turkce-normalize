# Değişiklikler

## Yayımlanmamış

- Noktalı ondalık tutar kuruşla okunur: `2450.75 TL` → "iki bin dört yüz elli lira yetmiş beş kuruş", `12.50₺` →
  "on iki lira elli kuruş" (önceden nokta binlik sanılıyordu: "iki yüz kırk beş bin yetmiş beş lira", "bin iki yüz
  elli lira"). Noktadan sonra üç rakam binlik kalır (`1.250 TL`).
- Tek haneli kuruş onluktur: `1,5 TL` → "bir lira elli kuruş" (önceden "beş kuruş").
- Tam kısım sıfırsa lira söylenmez: `0.99 TL` → "doksan dokuz kuruş" (önceden "doksan dokuz lira"), `0,50 TL'ye` →
  "elli kuruşa". Sınır testleri: `99.9 TL`, `1.250,5 TL`, `12.500 TL`, `1.000.000 TL`.

## 0.1.7 — "dört" yumuşar, ekli Roma rakamı

- Ünlüyle başlayan ekte "dört" "dörd" olur: `4'e` → "dörde", `%14'ü` → "yüzde on dördü", `3.14'e` → "üç virgül on
  dörde", `104'ü` → "yüz dördü" (önceden "dörte", "dörtü"). Sayı adlarından yalnız "dört" yumuşar ("kırka", "üçe").
- Ekli ve yalın Roma rakamı okunur (önceden olduğu gibi kalıp harf harf okunuyordu: "IVe", "XIVün"). Bölüm, madde,
  ek, cilt, faz, tip… sözcüğünden sonra asıl sayı (`Bölüm III'te` → "Bölüm üçte", `Tip II` → "Tip iki"), özel addan
  sonra sıra sayısı (`Louis XIV'ün` → "Lui on dördüncünün", `Henri IV` → "Henri dördüncü"), bağlamsız ekli olan asıl
  sayı (`IV'e` → "dörde"). Tek harfli bağlamsız rakam (`X'e`) ve kara listedekiler (`CV`, `MI`) dokunulmaz.
- Yeni: `roma_ekli_oku(deger, ek, sira)`, `ROMA_BOLUM`; `eki_uydur` ve `roma_coz` sayilar.py'ye taşındı (eski yoldan
  da alınır).

## 0.1.6 — alan adı, saat, baştaki sıfır

- Alan adı uzantısının yerleşik okunuşu: `github.com` → "githab nokta kom" (Türkçe harflerle "com" okunuyor, ses
  modeli "c"yi "dʒ" söylüyordu: "noktacağım"); `.io` → "ay o", `.ai` → "ey ay", `.app` → "ep". Adresteki ünsüzlü parça
  harf harf (`seslen-tr` → "seslen tire tere", `b-c` → "be tire ce"; önceden "tr", "b" okunamıyordu).
- Noktalı saat "saat" sözcüğü olmadan da: ardında zaman eki olan (`06.45'te` → "altı kırk beşte", `12.30'da` → "on
  iki otuzda", `10.00'a` → "ona") ya da sıfırla başlayan (`06.45`) saat; önceden ondalık okunuyordu ("altı virgül
  kırk beşte"). Tek haneli saat ondalık kalır (`3.14'e`).
- Baştaki sıfır okunur: `TR-042` → "tere sıfır kırk iki", `007` → "sıfır sıfır yedi" (önceden "kırk iki", "yedi").
- Birim: `g` → gram, `mg` → miligram, `ml` → mililitre (`250 g un` önceden "ge un").
- Teknik terim: MediaSpeech → "midiya spiç".
- Yeni: `saat_oku(saat, dakika)`, `tam_sayi_oku(sayi)` (sayilar).

## 0.1.5 — kısaltmalar bitişik okunur

- Harf harf okunan kısaltma tek sözcük gibi bitişik yazılır: `TBMM'de` → "tebememede", `TR` → "tere", `CBS'e` →
  "cebeseye" (önceden "te be me mede", "te re", "ce be seye"). Ayrık harf adlarında ses modeli ünlüleri yutuyordu
  ("tbmmede", "ap elli", "sg ka"); seslen-tts ile 18 kısaltma cümlesi × 4 seste okunuş denetiminde takılan 21 → 5.
  Alan adı uzantısı ("ornek.com.tr" → "… tere"), IBAN başı ve teknik metindeki ünsüz kümesi ("seslen-tr") de aynı.
  Ünsüzle biten ya da iki sözcüklü harf adı ayrı kalır (`XQ` → "iks kü", `Ğ` → "yumuşak ge").
- Yeni: `harfleri_oku(kelime)`.

## 0.1.4 — belge ve teknik metin

Gerçek makaleler (Markdown) seslendirilirken çıkan hatalardan:
- **Belge okuyucu** (`okunur_metin`, `paragraflar`): Markdown / HTML belge okunacak düz metne çevrilir. Yorum, kod
  bloğu, etiket satırı (#EVREN) atılır; başlık ve liste maddesi kendi cümlesi olur; numaralı madde sıra sayısıyla
  başlar ("1. …" → "Birincisi: …"); tablo satır satır, başlıklarıyla okunur; web adresi yalnız alan adıyla.
- **`uzun_cumleyi_bol`**: uzun cümle noktalı virgül, virgül ya da sözcük sınırından bölünür (modelin işaret sınırı).
  **`virgulden_bol`**: uzun cümle virgül / noktalı virgül / iki noktadan kısa parçalara (seslendirici ayrı okur).
- **Okunabilir büyük harfli yazım sözcük gibi okunur**: "EVREN'in" → "evrenin", "TÜİK", "ODTÜ" (başta ünsüz kümesi,
  üç ünsüz yan yana ya da az ünlü varsa eskisi gibi harf harf: "TBMM", "KPSS", "EPDK"). "LLM" → "elelem".
- Cümle bölücü küçük harfle devam eden yerde bölmez ("XX. yüzyıl"); cümle sonundaki noktalı ondalık bozulmaz
  ("ODbL 1.0." eskiden "on" okunuyordu).
- **Teknik yazımlar** (`teknik_uygula`, normalize'nin 4b adımı): sözcük içi tire boşluk olur ("Sentinel-2" →
  "Sentinel iki", "Ar-Ge" → "Ar Ge"; aralık ve tarih değişmez), sürüm ("v0.2.1" → "ve sıfır nokta iki nokta bir"),
  model adı ("Qwen2.5" → "kuven iki nokta beş", "Llama 3.1" → "lama üç nokta bir"), sayıdan sonra birim ("10 m" →
  "on metre", "24 kHz", "16 GB"), ondalıklı aralık ("2,5–5" → "iki virgül beş ile beş"), "+" ve "→", ünsüz kümesi
  harf harf ("seslen-tr" → "seslen te re").
- **Teknik kısaltma ve terimler** (`TEKNIK_KISALTMALAR`, `TEKNIK_TERIMLER`): "LLM" → "elelem", "NLP", "RAG", "GPS",
  "WER"; prompt engineering, fine-tuning, benchmark, PyTorch, PyPI, LinkedIn, Hugging Face, OpenStreetMap,
  Copernicus atıf satırı… Türk kulağına doğru gelen yazımla. Paket adları Türkçe harfleriyle ("turkce-uslup" →
  "türkçe üslup", "turkce-tts-sinav" → "… sınav").
- **Karışık harfli kısaltma** harf harf ("ODbL" → "o de be le", "PhD" → "pe he de"); ".0" ile biten noktalı sayı
  addan sonra sürümdür ("Common Voice 27.0" → "yirmi yedi nokta sıfır"; Türkçede ondalık virgülle yazılır).
- Numaralı başlık da sıra sayısıyla ("## 2. Başlık" → "İkincisi: Başlık"); cümle bölücü yalnız sıra numarasından
  oluşan cümle üretmez ('2. "Bilmiyorum…"' bölünüp tek başına "iki." okunuyordu).
- Şemasız web adresinin yolu okunmaz ("evren.ssyz.org.tr/users/u43bd…" → yalnız alan adı).
- "Qwen2.5 da karşılaştırıldı": bağlaç "da" artık "dekar" okunmuyor (rakam bir ada bitişikse ölçü değil).

## 0.1.3 — yabancı adlar

- Gömülü sözlüğe sık geçen yabancı kişi, yer ve marka adları eklendi (`YABANCI_ADLAR`, 87 ad): `Michael
  Jackson'ın` → "Maykıl Ceksının", `Sophie` → "Sofi", `Kenji` → "Kenci", `New York` → "Nevyork". Önceden Türkçe
  harf okunuşuyla okunuyordu ("miça cakson", "sopiye"). Türkçe adla karışabilenler (Can, Mark, Jean) eklenmedi.

## 0.1.2 — para eki

- Para ekinin uyumu: ek "TL"ye göre yazılır, okunuşta lira / kuruşa uydurulur (`10,50 TL'den` → "on lira elli
  kuruştan", `20 TL'ye` → "yirmi liraya"; önceden "kuruşden", "liraye"). `eki_uydur()` ünlü uyumu, sertleşme ve
  kaynaştırma harfi düşmesiyle.

## 0.1.1 — belgeler

- README ve CHANGELOG koda göre güncellendi (kurulum, kullanım, API, düzen); kod davranışı değişmedi.

## 0.1.0 — ilk açık sürüm

- İlk yayın (PyPI: `turkce-normalize`). Ayrıntılar README'de.
- `normalize()`: sayı, ondalık, sıra sayısı, para, yüzde, tarih (ISO ve tireli dahil), saat (noktalı saat
  "saat" sözcüğünden sonra), telefon, IBAN, kısaltma ve birim, Roma rakamı, kesir (ekli kesir: `1/2'si` →
  yarısı), aralık ve skor, eksi sayı, büyük harfli kısaltma (K → "ka"), e-posta ve web adresi, simgeler,
  sürüm numarası (`1.2.3`), `24/7`; coğrafi gösterimler (koordinat, ölçek, pafta, EPSG/UTM, alan birimi).
- Gömülü CBS/yazılım telaffuz sözlüğü ve `sozluk_birlestir`.
- LLM akışı için kısaltma farkında cümle ayırıcı (`CumleAyirici`, `cumleleri_ayir`, `cumle_akisi`,
  `cumle_akisi_async`) ve `[dur]` duraklama işaretleri.
- Komut satırı: `turkce-normalize` / `python -m turkce_normalize` (`--cografi-kapali`).
- Bağımlılık yok; Python 3.9+. Testler GitHub Actions'ta 3.9 ve 3.12 ile.
