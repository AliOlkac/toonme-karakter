import pytest

from toonme_karakter import uygulama
from toonme_karakter.adb import AdbHatasi
from toonme_karakter.aktarim import DesteklenmeyenDosya, GaleriHatasi
from toonme_karakter.ayarlar import Ayarlar
from toonme_karakter.bluestacks import ADBKapali, BaslatmaZamanAsimi
from toonme_karakter.toonme_akis import AkisHatasi
from toonme_karakter.uygulama import isle, kullanici_mesaji, main
from tests.sahte import SahteAdb

GALERIDE = {"content query": ["Row: 0 _id=1"]}


def patlayan(ayarlar):
    raise AssertionError("BlueStacks hazırlanmamalıydı")


def test_desteklenmeyen_dosyada_bluestacks_acilmaz(tmp_path):
    (f := tmp_path / "a.heic").touch()
    with pytest.raises(DesteklenmeyenDosya):
        isle(f, Ayarlar(), hazirla=patlayan, veri=tmp_path)


def test_basarili_is(tmp_path):
    (f := tmp_path / "foto.jpg").write_bytes(b"x")
    adb = SahteAdb(GALERIDE)
    hedef = isle(f, Ayarlar(), hazirla=lambda a: adb, akis=lambda *a: "/sdcard/Pictures/ToonMe/c.jpg",
                 veri=tmp_path / "v")
    assert hedef == tmp_path / "foto_toon.jpg" and hedef.exists()
    assert any("rm -f /sdcard/Pictures/ToonMeInput/" in c for c in adb.cagrilar)
    assert "rm -f /sdcard/Pictures/ToonMe/c.jpg" in " ".join(adb.cagrilar)
    assert "am force-stop com.vicman.toonmeapp" in adb.cagrilar


def test_akisa_ayarlar_aktarilir(tmp_path):
    (f := tmp_path / "foto.jpg").write_bytes(b"x")
    alinan = []

    def akis(ekran, adb, url, zaman_asimi):
        alinan.append((url, zaman_asimi))
        return "/sdcard/Pictures/ToonMe/c.jpg"

    isle(f, Ayarlar(sablon_url="https://toonme.com/d/1", isleme_zaman_asimi_sn=60),
         hazirla=lambda a: SahteAdb(GALERIDE), akis=akis, veri=tmp_path / "v")
    assert alinan == [("https://toonme.com/d/1", 60)]


def test_hatada_kayit_ve_temizlik(tmp_path):
    (f := tmp_path / "foto.jpg").write_bytes(b"x")
    adb = SahteAdb(GALERIDE)

    def akis(*a):
        raise AkisHatasi("kirpma", "next_btn bulunamadı", [])

    with pytest.raises(AkisHatasi):
        isle(f, Ayarlar(), hazirla=lambda a: adb, akis=akis, veri=tmp_path / "v")
    kayitlar = list((tmp_path / "v" / "hatalar").iterdir())
    assert len(kayitlar) == 1
    assert "next_btn bulunamadı" in (kayitlar[0] / "hata.txt").read_text(encoding="utf-8")
    assert (kayitlar[0] / "ekran.png").read_bytes() == b"png"
    assert any("rm -f /sdcard/Pictures/ToonMeInput/" in c for c in adb.cagrilar)
    assert "am force-stop com.vicman.toonmeapp" in adb.cagrilar
    assert not (tmp_path / "foto_toon.jpg").exists()


def test_mesaj_adb_kapali():
    assert "ADB kapalı" in kullanici_mesaji(ADBKapali())


def test_mesaj_baslatma():
    assert kullanici_mesaji(BaslatmaZamanAsimi()) == "BlueStacks 90 saniyede açılmadı."


def test_mesaj_akis():
    assert (kullanici_mesaji(AkisHatasi("isleme", "zaman aşımı", []))
            == "ToonMe 'işleme' adımında takıldı: zaman aşımı")


def test_mesaj_desteklenmeyen():
    assert kullanici_mesaji(DesteklenmeyenDosya(".heic")) == "Bu dosya türü desteklenmiyor (jpg, png, webp)."


def test_main_hata_bildirimi_ve_kod(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    bildirimler = []
    monkeypatch.setattr(uygulama, "goster", lambda *a: bildirimler.append(a))

    def isle_hata(foto, ayarlar, **kw):
        raise AkisHatasi("isleme", "zaman aşımı", [])

    monkeypatch.setattr(uygulama, "isle", isle_hata)
    assert main([str(tmp_path / "foto.jpg")]) == 1
    assert bildirimler[-1] == ("ToonMe karakter yapılamadı", "ToonMe 'işleme' adımında takıldı: zaman aşımı")


def test_main_basari_bildirimi(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    bildirimler = []
    monkeypatch.setattr(uygulama, "goster", lambda *a: bildirimler.append(a))
    monkeypatch.setattr(uygulama, "isle", lambda foto, ayarlar, **kw: foto.with_name("foto_toon.jpg"))
    assert main([str(tmp_path / "foto.jpg")]) == 0
    assert bildirimler[0] == ("ToonMe", "İşleniyor: foto.jpg")
    assert bildirimler[-1] == ("Karakter hazır", "foto_toon.jpg", tmp_path / "foto_toon.jpg")


def test_mesaj_galeri():
    assert kullanici_mesaji(GaleriHatasi()) == "Fotoğraf emülatör galerisine eklenemedi."


def test_yukleme_sonrasi_hatada_girdi_yine_silinir(tmp_path):
    # push başarılı, sonraki adım (galeri taraması) hata veriyor: fotoğraf emülatörde kalmamalı
    (f := tmp_path / "foto.jpg").write_bytes(b"x")
    adb = SahteAdb({"am broadcast": [AdbHatasi("broadcast hatası")],
                    "ls -1 /sdcard/Pictures/ToonMeInput": ["toonme_abc.jpg\n"]})
    with pytest.raises(AdbHatasi):
        isle(f, Ayarlar(), hazirla=lambda a: adb, akis=lambda *a: "x", veri=tmp_path / "v")
    assert "rm -f /sdcard/Pictures/ToonMeInput/toonme_abc.jpg" in " ".join(adb.cagrilar)


def test_gec_olusan_cikti_da_silinir(tmp_path):
    # işten sonra çıktı klasöründe yeni olan her şey (geç gelen önceki deneme dosyası dahil) silinir
    (f := tmp_path / "foto.jpg").write_bytes(b"x")
    # yalnızca iş başında konan işaretten yeni dosyalar silinir; kullanıcının eski ToonMe kayıtları kalır
    adb = SahteAdb({"find /sdcard/Pictures/ToonMe": ["/sdcard/Pictures/ToonMe/c.jpg\n/sdcard/Pictures/ToonMe/gec.jpg\n"],
                    **GALERIDE})
    isle(f, Ayarlar(), hazirla=lambda a: adb, akis=lambda *a: "/sdcard/Pictures/ToonMe/c.jpg", veri=tmp_path / "v")
    hepsi = " ".join(adb.cagrilar)
    i_isaret = next(i for i, c in enumerate(adb.cagrilar) if c.startswith("touch /data/local/tmp/"))
    i_push = next(i for i, c in enumerate(adb.cagrilar) if c.startswith("push "))
    assert i_isaret < i_push
    assert "rm -f /sdcard/Pictures/ToonMe/gec.jpg" in hepsi and "rm -f /sdcard/Pictures/ToonMe/c.jpg" in hepsi


def test_main_goreli_yol(tmp_path, monkeypatch):
    # komut satırından "foto.jpg" verildiğinde sonuç kaydedilir ve başarı bildirimi gösterilebilmeli
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    from toonme_karakter.bildirim import toast_xml
    monkeypatch.setattr(uygulama, "goster", lambda *a: toast_xml(*a))
    monkeypatch.setattr(uygulama, "isle", lambda foto, ayarlar, **kw: foto.with_name("foto_toon.jpg"))
    assert main(["foto.jpg"]) == 0
