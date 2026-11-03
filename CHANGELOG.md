# Değişiklikler

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
