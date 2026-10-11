# Değişiklikler

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
