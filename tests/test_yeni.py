"""
Kaynakta olmayan, bu pakette eklenen özelliklerin testleri.

Her sınıf README'deki bir başlığa karşılık gelir. Yanlış pozitif testleri
(dokunulmaması gerekenler) en az doğru dönüşümler kadar önemlidir: TTS'te
yanlış okunmuş bir kelime, hiç okunmamış bir kelimeden kötüdür.
"""
import os
import subprocess
import sys
import unittest
from pathlib import Path

from turkce_normalize import bulunma_eki, normalize, ondalik_oku, roma_coz, sayi_oku


class RomaRakamlari(unittest.TestCase):
    def test_yuzyil(self):
        self.assertEqual(normalize("XX. yüzyıl"), "yirminci yüzyıl")
        self.assertEqual(normalize("XIX. yüzyılda yaşadı."), "on dokuzuncu yüzyılda yaşadı.")

    def test_hukumdar_sirasi(self):
        self.assertEqual(normalize("II. Abdülhamit"), "ikinci Abdülhamit")
        self.assertEqual(normalize("III. Selim tahta çıktı."), "üçüncü Selim tahta çıktı.")
        self.assertEqual(normalize("I. Dünya Savaşı"), "birinci Dünya Savaşı")
        self.assertEqual(normalize("Sultan V. Mehmet"), "Sultan beşinci Mehmet")

    def test_cozumleme(self):
        self.assertEqual(roma_coz("MCMXCIX"), 1999)
        self.assertEqual(roma_coz("MMMM"), 4000)
        self.assertEqual(roma_coz("XIV"), 14)

    def test_yanlis_pozitif_yok(self):
        # Soru eki, disk, isim baş harfi, noktasız kullanım
        self.assertEqual(normalize("GELDİ MI. Evet."), "GELDİ MI. Evet.")
        self.assertEqual(normalize("Bu bir CD. Sonra bakarız."), "Bu bir ce de. Sonra bakarız.")
        self.assertEqual(normalize("Mehmet V. Delibaş geldi."), "Mehmet V. Delibaş geldi.")
        self.assertEqual(normalize("DİL. sonra", kisaltma_harf_harf=False), "DİL. sonra")  # İ Roma harfi değil
        self.assertEqual(normalize("Bölüm IIII. kısım"), "Bölüm IIII. kısım")  # geçersiz Roma rakamı
        # Büyük harfli kelime ardından yalnızca küçük, hükümdar sırası gibi sayılar
        self.assertEqual(normalize("Not: MD. Ahmet"), "Not: me de. Ahmet")  # sıra sayısı değil, kısaltma


class Kesirler(unittest.TestCase):
    def test_ozel_kesirler(self):
        self.assertEqual(normalize("1/2 kilo un"), "yarım kilo un")
        self.assertEqual(normalize("1/4 saat"), "çeyrek saat")
        self.assertEqual(normalize("3/4 oranında"), "dörtte üç oranında")
        self.assertEqual(normalize("2/3 çoğunluk"), "üçte iki çoğunluk")

    def test_unlu_ve_unsuz_uyumu(self):
        self.assertEqual(normalize("1/5"), "beşte bir")
        self.assertEqual(normalize("1/6"), "altıda bir")
        self.assertEqual(normalize("1/10"), "onda bir")
        self.assertEqual(normalize("3/40"), "kırkta üç")
        self.assertEqual(normalize("7/8"), "sekizde yedi")
        self.assertEqual(normalize("1/9"), "dokuzda bir")
        self.assertEqual(normalize("1/100"), "yüzde bir")
        self.assertEqual(normalize("1/1000"), "binde bir")

    def test_bulunma_eki(self):
        beklenen = {"bir": "de", "iki": "de", "üç": "te", "dört": "te", "beş": "te", "altı": "da",
                    "yedi": "de", "sekiz": "de", "dokuz": "da", "on": "da", "kırk": "ta",
                    "altmış": "ta", "yetmiş": "te", "doksan": "da", "yüz": "de", "milyon": "da"}
        for kelime, ek in beklenen.items():
            with self.subTest(kelime=kelime):
                self.assertEqual(bulunma_eki(kelime), ek)

    def test_tam_sayili_kesir(self):
        self.assertEqual(normalize("2 1/2 kilo"), "iki buçuk kilo")
        self.assertEqual(normalize("3 3/4 metre"), "üç tam dörtte üç metre")
        self.assertEqual(normalize("½ ekmek, 2½ saat"), "yarım ekmek, iki buçuk saat")

    def test_ek_almis_kesir(self):
        self.assertEqual(normalize("Bütçenin 3/4'ü harcandı."), "Bütçenin dörtte üçü harcandı.")

    def test_tarih_olcek_ve_adres_bozulmaz(self):
        self.assertEqual(normalize("15/03/2026"), "on beş mart iki bin yirmi altı")
        self.assertEqual(normalize("1/25.000 ölçekli"), "yirmi beş binde bir ölçekli")
        self.assertEqual(normalize("1:1000 ölçekli"), "binde bir ölçekli")
        self.assertEqual(normalize("No: 5/7"), "No: beş bölü yedi")
        # Payı paydasından büyük olan kesir sayılmaz
        self.assertEqual(normalize("15/03 tarihinde"), "on beş/üç tarihinde")


class Araliklar(unittest.TestCase):
    def test_kucuk_sayilar(self):
        self.assertEqual(normalize("3-5 kişi geldi."), "üç beş kişi geldi.")
        self.assertEqual(normalize("10–20 dakika"), "on yirmi dakika")

    def test_buyuk_aralik(self):
        self.assertEqual(normalize("2020-2025 yılları arasında"),
                         "iki bin yirmi ile iki bin yirmi beş yılları arasında")
        self.assertEqual(normalize("1.000-2.000 TL"), "bin ile iki bin lira")

    def test_sira_ve_yuzde_araligi(self):
        self.assertEqual(normalize("3-5. maddeler"), "üçüncü ile beşinci maddeler")
        self.assertEqual(normalize("%10-20 indirim"), "yüzde on ile yirmi indirim")

    def test_saat_ve_tarih_araligi(self):
        self.assertEqual(normalize("14:30-15:30 arası"), "on dört otuz ile on beş otuz arası")
        self.assertEqual(normalize("01.03.2026-05.03.2026"),
                         "bir mart iki bin yirmi altı ile beş mart iki bin yirmi altı")

    def test_eksi_sayi(self):
        self.assertEqual(normalize("-5 derece"), "eksi beş derece")
        self.assertEqual(normalize("Sıcaklık -12,5 oldu."), "Sıcaklık eksi on iki virgül beş oldu.")

    def test_bozulmamasi_gerekenler(self):
        self.assertEqual(normalize("0212-555-44-33"),
                         "sıfır iki bir iki beş beş beş dört dört üç üç")
        self.assertEqual(normalize("Skor 3-1 bitti."), "Skor üç bir bitti.")       # a ≥ b: aralık değil
        self.assertRegex(normalize("TR33 0006 1005 9700 6410 0000 01"), r"^te re üç üç sıfır")
        self.assertEqual(normalize("Pafta G22-b-14c-2d"), "Pafta ge yirmi iki be on dört ce iki de")


class Kisaltmalar(unittest.TestCase):
    def test_harf_harf(self):
        self.assertEqual(normalize("TBMM toplandı."), "te be me me toplandı.")
        self.assertEqual(normalize("TRT haberleri"), "te re te haberleri")
        self.assertEqual(normalize("AKP ve CHP"), "a ka pe ve ce he pe")
        self.assertEqual(normalize("ÖSYM sınavı"), "ö se ye me sınavı")
        self.assertEqual(normalize("ĞÜŞ"), "yumuşak ge ü şe")
        self.assertEqual(normalize("WWF ve XQ"), "çift ve çift ve fe ve iks kü")

    def test_ek_okunusa_baglanir(self):
        self.assertEqual(normalize("TBMM'de oylama"), "te be me mede oylama")
        self.assertEqual(normalize("ABD'li yetkili"), "a be deli yetkili")
        self.assertEqual(normalize("TBMM'DE"), "te be me mede")

    def test_kelime_gibi_okunanlar(self):
        self.assertEqual(normalize("NATO'ya katıldı."), "natoya katıldı.")
        self.assertEqual(normalize("ASELSAN ve TÜBİTAK"), "aselsan ve tübitak")
        self.assertEqual(normalize("AFAD, TOKİ, ODTÜ"), "afad, toki, odtü")

    def test_sozlukteki_kisaltma_once_gelir(self):
        self.assertEqual(normalize("%18 KDV"), "yüzde on sekiz katma değer vergisi")
        self.assertEqual(normalize("100 TL"), "yüz lira")

    def test_dokunulmamasi_gerekenler(self):
        self.assertEqual(normalize("UYARI: kapı açık"), "UYARI: kapı açık")
        self.assertEqual(normalize("GELDİ MI?"), "GELDİ MI?")
        self.assertEqual(normalize("ANKARA büyükşehir"), "ANKARA büyükşehir")    # 6+ harf
        self.assertEqual(normalize("Henry VIII"), "Henry VIII")                 # Roma rakamı
        self.assertEqual(normalize("APIyi çağır"), "APIyi çağır")               # ek almış kelime
        self.assertEqual(normalize("TBMM", kisaltma_harf_harf=False), "TBMM")


class EpostaVeAdres(unittest.TestCase):
    def test_eposta(self):
        self.assertEqual(normalize("ali.veli@ornek.com.tr"),
                         "ali nokta veli et ornek nokta com nokta te re")
        self.assertEqual(normalize("Yazın: destek_2@site.org."),
                         "Yazın: destek alt çizgi iki et site nokta org.")

    def test_url(self):
        self.assertEqual(normalize("https://www.ornek.gov.tr/harita"),
                         "ornek nokta gov nokta te re bölü harita")
        self.assertEqual(normalize("Bkz. http://site.com/a/b-c?x=1&y=2."),
                         "Bkz. site nokta com bölü a bölü b tire c.")

    def test_semasiz_alan_adi(self):
        self.assertEqual(normalize("Detay için ornek.com.tr adresine bakın."),
                         "Detay için ornek nokta com nokta te re adresine bakın.")

    def test_adres_parcalarina_telaffuz_uygulanir(self):
        # Adres sözlükten ÖNCE parçalanır ("api." kalıbı bozulmaz), parçalar
        # sonra sözlükten geçer: "api" -> "ey pi ay", "pdf" -> "pe de fe".
        self.assertEqual(normalize("api.ornek.com"), "ey pi ay nokta ornek nokta com")
        self.assertEqual(normalize("https://ornek.com/rapor.pdf"),
                         "ornek nokta com bölü rapor nokta pe de fe")

    def test_sayi_ve_kisaltma_sanilmaz(self):
        # Noktalı kısaltmalar ve büyük harfli uzantılar alan adı sayılmaz
        self.assertEqual(normalize("vb. şeyler"), "ve benzeri şeyler")
        self.assertEqual(normalize("ABC A.Ş. merkezi"), "a be ce anonim şirketi merkezi")
        self.assertEqual(normalize("Oraya gittim.De ki"), "Oraya gittim.De ki")


class Simgeler(unittest.TestCase):
    def test_islemler(self):
        self.assertEqual(normalize("2+2=4"), "iki artı iki eşittir dört")
        self.assertEqual(normalize("3 + 5 = 8"), "üç artı beş eşittir sekiz")

    def test_ve_isareti(self):
        self.assertEqual(normalize("Ar-Ge & Pazarlama"), "Ar-Ge ve Pazarlama")

    def test_derece(self):
        self.assertEqual(normalize("Hava 25°C, gece -3 °C."), "Hava yirmi beş derece, gece eksi üç derece.")
        self.assertEqual(normalize("Ateş 38,5°C'ye çıktı."), "Ateş otuz sekiz virgül beş dereceye çıktı.")
        self.assertEqual(normalize("45° açı"), "kırk beş derece açı")

    def test_arti_eksi(self):
        self.assertEqual(normalize("±0,5 mm"), "artı eksi sıfır virgül beş milimetre")

    def test_telefon_onekindeki_arti_degismez(self):
        self.assertTrue(normalize("+90 hattı").startswith("+"))


class Iyilestirmeler(unittest.TestCase):
    """Kaynaktaki küçük hataların düzeltmeleri."""

    def test_ondalikta_bastaki_sifir(self):
        # Kaynakta 3,05 "üç virgül beş" okunuyordu, yani 3,5.
        self.assertEqual(ondalik_oku(3, "05"), "üç virgül sıfır beş")
        self.assertEqual(normalize("3,05 metre"), "üç virgül sıfır beş metre")
        self.assertEqual(ondalik_oku(3, "50"), "üç virgül beş")

    def test_milyonluk_olcek_unlu_uyumu(self):
        self.assertEqual(normalize("1:1.000.000 ölçek"), "bir milyonda bir ölçek")

    def test_eksi_koordinat(self):
        self.assertEqual(normalize("-12.3456, 45.6789"),
                         "enlem eksi on iki virgül üç dört beş altı, boylam kırk beş virgül altı yedi sekiz dokuz")

    def test_utm_dilim_tekrari(self):
        self.assertEqual(normalize("UTM 35 dilimi"), "u te me otuz beşinci dilimi")
        self.assertEqual(normalize("UTM 35N"), "u te me otuz beşinci dilim kuzey")

    def test_cok_buyuk_sayi(self):
        self.assertEqual(sayi_oku(10 ** 18), "bir kentilyon")
        self.assertEqual(sayi_oku(10 ** 24), "bir " + " ".join(["sıfır"] * 24))


class KomutSatiri(unittest.TestCase):
    def test_modul_olarak_calisir(self):
        kok = Path(__file__).resolve().parent.parent
        sonuc = subprocess.run(
            [sys.executable, "-m", "turkce_normalize", "Toplantı 14:30'da."],
            cwd=kok, capture_output=True, encoding="utf-8",
            env=dict(os.environ, PYTHONUTF8="1"),
        )
        self.assertEqual(sonuc.returncode, 0, sonuc.stderr)
        self.assertEqual(sonuc.stdout.strip(), "Toplantı on dört otuzda.")


if __name__ == "__main__":
    unittest.main()


class Eklenenler(unittest.TestCase):
    """03.10: K "ka", ekli kesir, noktalı ondalık/saat, sürüm, 24/7, skor, ISO ve tireli tarih."""

    def test_k_harfi(self):
        self.assertEqual(normalize("PKK ve TDK"), "pe ka ka ve te de ka")

    def test_ekli_kesir(self):
        self.assertEqual(normalize("Pastanın 1/2'si, 1/4'ü ve 3/4'ü kaldı."),
                         "Pastanın yarısı, çeyreği ve dörtte üçü kaldı.")
        self.assertEqual(normalize("1/2'sini aldım"), "yarısını aldım")

    def test_noktali_ondalik_ve_saat(self):
        self.assertEqual(normalize("3.5 milyon"), "üç virgül beş milyon")
        self.assertEqual(normalize("3.500 lira"), "üç bin beş yüz lira")
        self.assertEqual(normalize("Saat 14.30'da"), "Saat on dört otuzda")
        self.assertEqual(normalize("pi 3.14"), "pi üç virgül on dört")

    def test_surum(self):
        self.assertEqual(normalize("1.2.3 sürümü"), "bir nokta iki nokta üç sürümü")
        self.assertEqual(normalize("1.250.000 kişi"), "bir milyon iki yüz elli bin kişi")

    def test_24_7_skor_tarih(self):
        self.assertEqual(normalize("24/7 açık"), "yirmi dört yedi açık")
        self.assertEqual(normalize("Maç 3-1 bitti."), "Maç üç bir bitti.")
        self.assertEqual(normalize("2026-10-03"), "üç ekim iki bin yirmi altı")
        self.assertEqual(normalize("03-10-2026"), "üç ekim iki bin yirmi altı")

    def test_yuzde_cumle_sonu(self):
        self.assertEqual(normalize("KDV %18."), "katma değer vergisi yüzde on sekiz.")
        self.assertEqual(normalize("%1.250 arttı"), "yüzde bin iki yüz elli arttı")


class ParaEki(unittest.TestCase):
    """Ek "TL"ye göre yazılır (TL'den, TL'ye); okunuşta lira / kuruşa uymalı."""

    def test_lira(self):
        self.assertEqual(normalize("20 TL'ye"), "yirmi liraya")
        self.assertEqual(normalize("100 TL'yi"), "yüz lirayı")
        self.assertEqual(normalize("50 TL'lik"), "elli liralık")
        self.assertEqual(normalize("200 TL'nin"), "iki yüz liranın")
        self.assertEqual(normalize("5 ₺'den"), "beş liradan")

    def test_kurus(self):
        self.assertEqual(normalize("10,50 TL'den"), "on lira elli kuruştan")
        self.assertEqual(normalize("5,25 TL'yi"), "beş lira yirmi beş kuruşu")
        self.assertEqual(normalize("1,50 TL'si"), "bir lira elli kuruşu")
        self.assertEqual(normalize("Fiyatı 3.499,90 TL'den 2.750 TL'ye düştü."),
                         "Fiyatı üç bin dört yüz doksan dokuz lira doksan kuruştan iki bin yedi yüz elli liraya düştü.")

    def test_zaten_uyumlu(self):
        self.assertEqual(normalize("3.500 lira'dan"), "üç bin beş yüz liradan")
