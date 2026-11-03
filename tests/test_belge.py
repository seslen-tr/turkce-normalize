"""Belge okuyucu (belge.py) ve teknik yazımlar (teknik.py): makale, rapor ve README gibi metinler.

03.11.2026'da gerçek makalelerin seslendirilmesinde çıkan hatalardan: Markdown işaretleri okunuyordu, tablo tek
dev cümle oluyordu, tire duraklamaya dönüyordu, model adı ve birim okunmuyordu.
"""
import unittest

from turkce_normalize import normalize, okunur_metin, paragraflar, uzun_cumleyi_bol

MAKALE = """<!--
Yayın notu: okunmaz.
-->

# Türkçe modelleri ölçtük

Bu yazıda **altı modeli** ölçtüm. Ayrıntılar [burada](https://ornek.com/a/b).

## Sonuçlar

| Model | Doğruluk | Süre |
|---|---|---|
| model-a | %81,2 | 3,5 sn |
| model-b | **%77,2** | 4 sn |

**1. Bağlam verilince fark kapanıyor.** Bütün modeller yükseldi.

**3. Görev başına seçim.** Tek model yetmiyor.

- Birinci madde
- İkinci madde: ayrıntı

```python
print("kod okunmaz")
```

> Alıntı satırı

---

Veri: https://evren.ornek.org.tr/datasets/uzun-yol?x=1

#EVREN #LLM #Türkçe
"""


class Belge(unittest.TestCase):
    def setUp(self):
        self.p = paragraflar(MAKALE)

    def test_yorum_kod_ve_etiket_okunmaz(self):
        hepsi = " ".join(self.p)
        for parca in ("Yayın notu", "print", "kod okunmaz", "#EVREN", "#", "**", "|", "```", "<!--", "-->"):
            self.assertNotIn(parca, hepsi)

    def test_baslik_kendi_cumlesi(self):
        self.assertEqual(self.p[0], "Türkçe modelleri ölçtük.")
        self.assertIn("Sonuçlar.", self.p)

    def test_kalin_ve_baglanti_metni_kalir(self):
        self.assertIn("Bu yazıda altı modeli ölçtüm. Ayrıntılar burada.", self.p)

    def test_tablo_satir_satir(self):
        self.assertIn("model-a: Doğruluk, %81,2; Süre, 3,5 sn.", self.p)
        self.assertIn("model-b: Doğruluk, %77,2; Süre, 4 sn.", self.p)

    def test_numarali_madde_sira_sayisiyla(self):
        self.assertTrue(any(p.startswith("Birincisi: Bağlam verilince") for p in self.p))
        self.assertTrue(any(p.startswith("Üçüncüsü: Görev başına") for p in self.p))

    def test_numarali_baslik(self):
        p = paragraflar('## 2. "Bilmiyorum, sorayım" davranışını ölçün\n\nMetin.')
        self.assertEqual(p[0], 'İkincisi: "Bilmiyorum, sorayım" davranışını ölçün.')
        from turkce_normalize import cumleleri_ayir
        self.assertEqual(cumleleri_ayir('2. "Bilmiyorum" dedi. Sonra.'), ['2. "Bilmiyorum" dedi.', "Sonra."])

    def test_liste_maddesi_noktayla_biter(self):
        self.assertIn("Birinci madde.", self.p)
        self.assertIn("İkinci madde: ayrıntı.", self.p)

    def test_adres_yalniz_alan_adi(self):
        self.assertIn("Veri: evren nokta ornek nokta org nokta te re.", self.p)

    def test_semasiz_adresin_yolu_okunmaz(self):
        p = paragraflar("Veri: evren.ssyz.org.tr/users/u43bd0650c87e ve huggingface.co/datasets/mvdelibas/TR-CBS")
        self.assertEqual(p, ["Veri: evren nokta ssyz nokta org nokta te re ve huggingface nokta ce o."])

    def test_okunur_metin_paragraf_boslugu(self):
        self.assertIn("\n\n", okunur_metin(MAKALE))

    def test_uzun_cumle_bolunur(self):
        cumle = "Bir, " * 120 + "son."
        parcalar = uzun_cumleyi_bol(cumle, 220)
        self.assertGreater(len(parcalar), 1)
        self.assertTrue(all(len(p) <= 220 for p in parcalar))
        self.assertEqual(" ".join(parcalar).split(), cumle.split())
        self.assertEqual(uzun_cumleyi_bol("Kısa cümle."), ["Kısa cümle."])


class Teknik(unittest.TestCase):
    def test_teknik_kisaltma(self):
        self.assertEqual(normalize("LLM'ler ve API"), "elelemler ve ey pi ay")
        self.assertEqual(normalize("CBS ile SQL"), "ce be se ile es kü el")

    def test_sozcuk_ici_tire(self):
        self.assertEqual(normalize("Sentinel-2 ve e-Devlet"), "Sentinel iki ve e Devlet")

    def test_aralik_ve_tarih_bozulmaz(self):
        self.assertEqual(normalize("3-5 kişi"), "üç beş kişi")
        self.assertEqual(normalize("2026-03-15"), "on beş mart iki bin yirmi altı")

    def test_surum_ve_model_adi(self):
        self.assertEqual(normalize("v0.2.1"), "ve sıfır nokta iki nokta bir")
        self.assertEqual(normalize("Qwen2.5"), "kuven iki nokta beş")
        self.assertEqual(normalize("Llama 3.1"), "lama üç nokta bir")
        self.assertEqual(normalize("oran 0.75"), "oran sıfır virgül yetmiş beş")       # ondalık kalır

    def test_birim(self):
        self.assertEqual(normalize("10 m çözünürlük, 24 kHz"), "on metre çözünürlük, yirmi dört kilohertz")
        self.assertEqual(normalize("16 GB"), "on altı gigabayt")

    def test_simgeler(self):
        self.assertEqual(normalize("LinkedIn + Medium"), "linkdin ve midyım")
        self.assertEqual(normalize("1920x1080"), "bin dokuz yüz yirmi çarpı bin seksen")

    def test_kucuk_harfli_teknik_ad(self):
        self.assertEqual(normalize("seslen-tts PyPI'da"), "seslen te te se pay pi ayda")
        self.assertEqual(normalize("seslen-tr altında"), "seslen te re altında")
        self.assertEqual(normalize("5 km yol, vb. şeyler"), "beş kilometre yol, ve benzeri şeyler")

    def test_okunabilir_buyuk_harf_sozcuk_gibi(self):
        self.assertEqual(normalize("EVREN'in verisi"), "evrenin verisi")
        self.assertEqual(normalize("TÜİK ve ODTÜ"), "tüik ve odtü")
        self.assertEqual(normalize("TBMM, KPSS, EPDK, İETT"), "te be me me, ka pe se se, e pe de ka, i e te te")

    def test_unluyle_biten_okunusa_kaynastirma(self):
        self.assertEqual(normalize("CBS'e bağlamak"), "ce be seye bağlamak")
        self.assertEqual(normalize("PDF'i aç"), "pe de feyi aç")
        self.assertEqual(normalize("Ankara'ya, İstanbul'a"), "Ankaraya, İstanbula")      # doğru yazım değişmez

    def test_ondalikli_aralik(self):
        self.assertEqual(normalize("2,5–5 katı"), "iki virgül beş ile beş katı")

    def test_cumle_sonu_noktali_ondalik(self):
        self.assertEqual(normalize("Lisans ODbL 1.0."), "Lisans o de be le bir nokta sıfır.")
        self.assertEqual(normalize("Toplam 1.250."), "Toplam bin iki yüz elli.")          # binlik kalır

    def test_sifirla_biten_noktali_sayi_surum(self):
        self.assertEqual(normalize("Türkçe 27.0 sürümü"), "Türkçe yirmi yedi nokta sıfır sürümü")
        self.assertEqual(normalize("oran 0.75 ve 3.5 kat"), "oran sıfır virgül yetmiş beş ve üç virgül beş kat")

    def test_karisik_kisaltma_ve_paket_adlari(self):
        self.assertEqual(normalize("PhD ve PyPI"), "pe he de ve pay pi ay")
        self.assertEqual(normalize("turkce-uslup ve turkce-tts-sinav"), "türkçe üslup ve türkçe te te se sınav")

    def test_kucuk_harfle_devam_eden_cumle_bolunmez(self):
        from turkce_normalize import cumleleri_ayir
        self.assertEqual(cumleleri_ayir('"1.250,50 ₺", "XX. yüzyıl" gibi gösterimler okunur. Sonra biter.'),
                         ['"1.250,50 ₺", "XX. yüzyıl" gibi gösterimler okunur.', "Sonra biter."])

    def test_iban_ve_roma_bozulmaz(self):
        self.assertTrue(normalize("TR33 0006 1005 1978 6457 8413 26").startswith("te re üç üç"))
        self.assertEqual(normalize("XX. yüzyıl"), "yirminci yüzyıl")


if __name__ == "__main__":
    unittest.main()
