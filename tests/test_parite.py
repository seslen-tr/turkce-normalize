"""
Parite testleri — TypeScript kaynağındaki (seslen) testlerin birebir karşılığı.

Beklenen çıktılar kaynaktakiyle AYNIDIR. Bir kural değişince buradaki beklenti
de bilinçli olarak değişmeli — sessiz gerileme olmasın diye.

Çalıştırma: ``python -m unittest discover -s tests``
"""
import asyncio
import unittest

from turkce_normalize import (
    VARSAYILAN_DURAKLAMA, Parca, cumle_akisi, cumle_akisi_async, cumleleri_ayir,
    isaret_var, isaretleri_ayir, isaretleri_temizle, normalize, sayi_oku, sira_oku,
    sozluk_birlestir, VARSAYILAN_SOZLUK,
)


class SayiOkuma(unittest.TestCase):
    def test_sayi_okuma(self):
        self.assertEqual(sayi_oku(0), "sıfır")
        self.assertEqual(sayi_oku(7), "yedi")
        self.assertEqual(sayi_oku(100), "yüz")              # "bir yüz" değil
        self.assertEqual(sayi_oku(1000), "bin")             # "bir bin" değil
        self.assertEqual(sayi_oku(1_000_000), "bir milyon")  # ama "bir milyon"
        self.assertEqual(sayi_oku(1250), "bin iki yüz elli")
        self.assertEqual(sayi_oku(2360), "iki bin üç yüz altmış")
        self.assertEqual(sayi_oku(-42), "eksi kırk iki")

    def test_sira_sayisi(self):
        self.assertEqual(sira_oku(3), "üçüncü")
        self.assertEqual(sira_oku(4), "dördüncü")
        self.assertEqual(sira_oku(21), "yirmi birinci")
        self.assertEqual(sira_oku(100), "yüzüncü")


class TemelNormalizasyon(unittest.TestCase):
    def test_para_tarih_yuzde(self):
        self.assertEqual(normalize("Fatura tutarınız 1.250,50 ₺ olarak hesaplandı."),
                         "Fatura tutarınız bin iki yüz elli lira elli kuruş olarak hesaplandı.")
        self.assertEqual(normalize("Sözleşme 15.03.2026 tarihinde yenilenecek."),
                         "Sözleşme on beş mart iki bin yirmi altı tarihinde yenilenecek.")
        self.assertEqual(normalize("Bu ürüne %18 KDV uygulanır."),
                         "Bu ürüne yüzde on sekiz katma değer vergisi uygulanır.")

    def test_saat_sira_ve_kesme_isareti(self):
        self.assertEqual(normalize("Toplantı 14:30'da başlıyor."), "Toplantı on dört otuzda başlıyor.")
        self.assertEqual(normalize("Lütfen 3. maddeyi okuyun."), "Lütfen üçüncü maddeyi okuyun.")
        self.assertEqual(normalize("Ankara'da 2. şube 08:45'te açılıyor."),
                         "Ankarada ikinci şube sekiz kırk beşte açılıyor.")

    def test_kisaltma_birim_telefon(self):
        self.assertEqual(normalize("Sn. Dr. Ayşe Yılmaz aradı."), "sayın doktor Ayşe Yılmaz aradı.")
        self.assertEqual(normalize("Mesafe 12 km, alan 85 m² olarak ölçüldü."),
                         "Mesafe on iki kilometre, alan seksen beş metrekare olarak ölçüldü.")
        self.assertEqual(normalize("Destek için 0212 555 44 33 numarasını arayın."),
                         "Destek için sıfır iki bir iki beş beş beş dört dört üç üç numarasını arayın.")

    def test_iban_harf_harf_okunur(self):
        cikti = normalize("IBAN numaranız TR33 0006 1005 9700 6410 0000 01 olarak kayıtlı.")
        self.assertRegex(cikti, r"^i ban numaranız te re üç üç sıfır sıfır sıfır altı")

    def test_normalize_edilen_metinde_rakam_kalmaz(self):
        cumleler = [
            "Stokta 1.250 adet ürün kaldı, teslimat 3,5 iş günü sürüyor.",
            "Bu hizmete %18 KDV uygulanır, toplam 2.360 TL ödersiniz.",
            "Randevunuz 14:30'da, 3. katta oluşturuldu.",
        ]
        for c in cumleler:
            with self.subTest(c=c):
                self.assertNotRegex(normalize(c), r"\d")

    def test_saat_tek_haneli_dakika_sifir_ile_okunur(self):
        # 10:01 eskiden "on bir" oluyordu, yani saat 11. Sessiz ve tehlikeli bir hataydı.
        self.assertEqual(normalize("Randevu 10:01'de."), "Randevu on sıfır birde.")
        self.assertEqual(normalize("Toplantı 14:05 başlıyor."), "Toplantı on dört sıfır beş başlıyor.")
        self.assertEqual(normalize("Saat 08:07."), "Saat sekiz sıfır yedi.")

    def test_saat_tam_saatte_dakika_okunmaz(self):
        self.assertEqual(normalize("Mesai 09:00'da başlar."), "Mesai dokuzda başlar.")
        self.assertEqual(normalize("14:30'da görüşürüz."), "on dört otuzda görüşürüz.")
        self.assertEqual(normalize("Gece 00:15 kayıt alındı."), "Gece sıfır sıfır on beş kayıt alındı.")


METIN = ("Merhaba. Sn. Dr. Ayşe Yılmaz adına kayıtlı sözleşmeniz 15.03.2026 "
         "tarihinde yenilenecek! Toplam tutar 1.250,50 ₺ olarak hesaplandı. Devam edelim mi?")


class CumleAyiriciTesti(unittest.TestCase):
    def test_kisaltmada_ve_tarihte_bolmez(self):
        cumleler = cumleleri_ayir(METIN)
        self.assertEqual(len(cumleler), 3)
        self.assertIn("Sn. Dr. Ayşe", cumleler[0], "kısaltmada bölünmemeli")
        self.assertIn("15.03.2026", cumleler[0], "tarihte bölünmemeli")
        self.assertEqual(cumleler[2], "Devam edelim mi?")

    def test_token_token_gelen_akis_ayni_sonucu_verir(self):
        parcalar = [METIN[i:i + 7] for i in range(0, len(METIN), 7)]
        self.assertEqual(list(cumle_akisi(parcalar)), cumleleri_ayir(METIN))

    def test_async_akis_ayni_sonucu_verir(self):
        async def akis():
            for i in range(0, len(METIN), 7):
                yield METIN[i:i + 7]

        async def topla():
            return [c async for c in cumle_akisi_async(akis())]

        self.assertEqual(asyncio.run(topla()), cumleleri_ayir(METIN))

    def test_kisa_cumle_tek_basina_gonderilmez(self):
        self.assertEqual(cumleleri_ayir("Evet. Anladım, hemen kontrol ediyorum."),
                         ["Evet. Anladım, hemen kontrol ediyorum."])


class Telaffuz(unittest.TestCase):
    def test_cbs_jargonu_turkce_fonetikle_okunur(self):
        self.assertEqual(normalize("WMS katmanını buffer ile analiz et."),
                         "ve me se katmanını bafır ile analiz et.")
        self.assertEqual(normalize("Shapefile dosyasını GeoJSON olarak dışa aktar."),
                         "şeypfayl dosyasını ceo ceyson olarak dışa aktar.")

    def test_rakamli_terim_sayi_kuralina_yem_olmaz(self):
        # wgs84 sayı kurallarından önce yakalanmalı; sonra yakalansa "wgs seksen dört" olurdu
        self.assertEqual(normalize("Koordinat sistemi WGS84."), "Koordinat sistemi ve ge es seksen dört.")

    def test_uzun_terim_kisa_terimden_once_gelir(self):
        # "geojson" yakalanmalı, içindeki "json" değil
        self.assertRegex(normalize("GeoJSON çıktısı"), r"^ceo ceyson")

    def test_ek_almis_kelime_bolunmez(self):
        # "APIyi" bir Türkçe kelimedir, içindeki API'yi değiştirmek okumayı bozar
        self.assertRegex(normalize("APIyi çağır"), r"APIyi")

    def test_kuruma_ozel_sozluk_eklenebilir(self):
        sozluk = sozluk_birlestir(VARSAYILAN_SOZLUK, {"KENTGIS": "kent cis"})
        self.assertEqual(normalize("KENTGIS açılıyor.", telaffuz=sozluk), "kent cis açılıyor.")
        # Varsayılan sözlükte yokken değişmemeli
        self.assertEqual(normalize("KENTGIS açılıyor."), "KENTGIS açılıyor.")


class Cografi(unittest.TestCase):
    def test_koordinat_cifti_ondalik_sayi_sanilmaz(self):
        # Bu kural olmadan "üç yüz doksan dokuz bin üç yüz otuz dört virgül otuz iki"
        # çıkıyordu; koordinat tamamen kayboluyordu.
        self.assertEqual(
            normalize("Merkez 39.9334, 32.8597 noktasında."),
            "Merkez enlem otuz dokuz virgül dokuz üç üç dört, "
            "boylam otuz iki virgül sekiz beş dokuz yedi noktasında.",
        )

    def test_derece_dakika_saniye(self):
        self.assertEqual(normalize("Sınır 39°56'12\"K noktasından geçiyor."),
                         "Sınır otuz dokuz derece elli altı dakika on iki saniye kuzey noktasından geçiyor.")
        self.assertEqual(normalize("Konum 32°51'D."), "Konum otuz iki derece elli bir dakika doğu.")

    def test_ondalik_derece_ve_yon(self):
        self.assertEqual(normalize("Enlem 39.9334° K"), "Enlem otuz dokuz virgül dokuz üç üç dört derece kuzey")

    def test_olcek_bolme_islemi_gibi_okunmaz(self):
        self.assertEqual(normalize("1/25.000 ölçekli pafta"), "yirmi beş binde bir ölçekli pafta")
        self.assertEqual(normalize("1:1000 ölçekli"), "binde bir ölçekli")

    def test_pafta_kodu_harf_harf_okunur(self):
        self.assertEqual(normalize("Pafta G22-b-14c-2d"), "Pafta ge yirmi iki be on dört ce iki de")

    def test_epsg_kodu_sayi_degil_koddur(self):
        self.assertEqual(normalize("Koordinat sistemi EPSG:5254"),
                         "Koordinat sistemi e pe es ge beş iki beş dört")

    def test_alan_birimi_yalnizca_rakamdan_sonra(self):
        self.assertEqual(normalize("Toplam 340 ha alan."), "Toplam üç yüz kırk hektar alan.")
        self.assertEqual(normalize("Parsel 12 da büyüklüğünde."), "Parsel on iki dekar büyüklüğünde.")
        # "da" Türkçe bir ektir; rakam yoksa dokunulmamalı
        self.assertRegex(normalize("Bu da önemli."), r"^Bu da önemli\.$")

    def test_kapatilabilir(self):
        kapali = normalize("1/25.000 ölçekli", cografi=False)
        self.assertNotIn("binde bir", kapali, "cografi=False ölçek kuralını atlamalı")


class Isaretler(unittest.TestCase):
    def test_dur_metni_parcalara_boler(self):
        p = isaretleri_ayir("Sorgu bitti. [dur:0.8] Toplam 340 hektar.")
        self.assertEqual(len(p), 2)
        self.assertEqual(p[0].metin, "Sorgu bitti.")
        self.assertEqual(p[0].duraklama, 0.8)
        self.assertEqual(p[1].metin, "Toplam 340 hektar.")
        self.assertEqual(p[1].duraklama, 0)

    def test_art_arda_isaretler_duraklamayi_toplar(self):
        p = isaretleri_ayir("Bir. [dur] [dur] İki.")
        self.assertEqual(len(p), 2)
        self.assertEqual(p[0].duraklama, VARSAYILAN_DURAKLAMA * 2)

    def test_bilinmeyen_isaret_sessizce_silinmez(self):
        # Silseydik "çalışıyor" sanırdın; model okuyunca hatayı duyarsın
        self.assertRegex(isaretleri_ayir("Merhaba [vurgu] dünya.")[0].metin, r"\[vurgu\]")

    def test_altyazi_metninde_isaret_kalmaz(self):
        self.assertEqual(isaretleri_temizle("Sorgu bitti. [dur:0.8] Toplam."), "Sorgu bitti. Toplam.")

    def test_isaretsiz_metin_tek_parca_kalir(self):
        self.assertFalse(isaret_var("Düz bir cümle."))
        self.assertEqual(isaretleri_ayir("Düz bir cümle."), [Parca(metin="Düz bir cümle.", duraklama=0)])

    def test_isaret_var_sonraki_ayirmayi_bozmaz(self):
        # Kaynakta g bayraklı tek bir regex paylaşılıyordu ve test() lastIndex'i
        # kaydırıp ardından gelen ayırmada işareti atlatıyordu.
        m = "Birinci cümle. [dur:0.1] İkinci cümle."
        self.assertTrue(isaret_var(m))
        p = isaretleri_ayir(m)
        self.assertEqual(len(p), 2)
        self.assertEqual(p[0].duraklama, 0.1)


if __name__ == "__main__":
    unittest.main()
