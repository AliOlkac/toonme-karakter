import re

import pytest

from toonme_karakter.adb import AdbHatasi
from toonme_karakter.aktarim import (CIKTI_DIZINI, DesteklenmeyenDosya, GaleriHatasi, al, cikti_yolu, dogrula,
                                     gonder, listele, medya_yolu, temizle)
from tests.sahte import SahteAdb


def test_cikti_yolu_bos(tmp_path):
    assert cikti_yolu(tmp_path / "foto.jpg") == tmp_path / "foto_toon.jpg"


def test_cikti_yolu_doluysa_numara(tmp_path):
    (tmp_path / "foto_toon.jpg").touch()
    (tmp_path / "foto_toon (2).jpg").touch()
    assert cikti_yolu(tmp_path / "foto.png") == tmp_path / "foto_toon (3).jpg"


def test_medya_yolu():
    assert medya_yolu("/sdcard/Pictures/ToonMe/a.jpg") == "/storage/emulated/0/Pictures/ToonMe/a.jpg"


def test_dogrula_heic(tmp_path):
    (tmp_path / "a.HEIC").touch()
    with pytest.raises(DesteklenmeyenDosya):
        dogrula(tmp_path / "a.HEIC")


def test_dogrula_buyuk_harf_jpg_gecer(tmp_path):
    (tmp_path / "a.JPG").touch()
    dogrula(tmp_path / "a.JPG")


def test_dogrula_dosya_yok(tmp_path):
    with pytest.raises(FileNotFoundError):
        dogrula(tmp_path / "yok.jpg")


def test_gonder_turkce_yol(tmp_path):
    f = tmp_path / "Masaüstü" / "Çocuk fotoğrafı 1.JPG"
    f.parent.mkdir()
    f.write_bytes(b"x")
    adb = SahteAdb({"content query": ["Row: 0 _id=1"]})
    uzak = gonder(adb, f, tmp_path / "gecici", uyku=lambda sn: None)
    assert re.fullmatch(r"/sdcard/Pictures/ToonMeInput/toonme_[0-9a-f]{32}\.jpg", uzak)
    push = next(c for c in adb.cagrilar if c.startswith("push "))
    assert push.split(" ")[1].isascii()
    assert any("MEDIA_SCANNER_SCAN_FILE" in c and f"file://{uzak}" in c for c in adb.cagrilar)
    assert list((tmp_path / "gecici").iterdir()) == []  # geçici kopya silindi


def test_al_turkce_hedef(tmp_path):
    h = tmp_path / "Çocuk_toon.jpg"
    al(SahteAdb(), "/sdcard/Pictures/ToonMe/x.jpg", h, tmp_path / "gecici")
    assert h.read_bytes() == b"jpg"


def test_listele():
    adb = SahteAdb({"ls -1 /sdcard/Pictures/ToonMe": ["a.jpg\nb.jpg\n"]})
    assert listele(adb, CIKTI_DIZINI) == {f"{CIKTI_DIZINI}/a.jpg", f"{CIKTI_DIZINI}/b.jpg"}


def test_listele_dizin_yok():
    assert listele(SahteAdb({"ls": [AdbHatasi("No such file")]}), CIKTI_DIZINI) == set()


def test_temizle_medya_kaydi():
    adb = SahteAdb()
    temizle(adb, ["/sdcard/Pictures/ToonMe/a.jpg"])
    hepsi = " ".join(adb.cagrilar)
    assert "rm -f /sdcard/Pictures/ToonMe/a.jpg" in hepsi
    assert "_data='/storage/emulated/0/Pictures/ToonMe/a.jpg'" in hepsi


def test_temizle_hata_yutar():
    temizle(SahteAdb({"rm": [AdbHatasi("x")]}), ["/sdcard/a.jpg"])


def test_gonder_cekim_tarihini_simdi_yapar(tmp_path):
    # ToonMe'nin "All" listesi çekim tarihine göre sıralı; eski EXIF tarihli fotoğraf başa gelmeli
    (f := tmp_path / "a.jpg").write_bytes(b"x")
    adb = SahteAdb({"content query": ["", "Row: 0 _id=7"]})
    uzak = gonder(adb, f, tmp_path / "gecici", uyku=lambda sn: None, simdi=lambda: 1800000000.5)
    sorgular = [c for c in adb.cagrilar if c.startswith("content query") and "--projection _id" in c]
    assert len(sorgular) == 2
    guncelleme = next(c for c in adb.cagrilar if c.startswith("content update"))
    assert "datetaken:l:1800000000500" in guncelleme
    assert f"_data='{medya_yolu(uzak)}'" in guncelleme
    assert adb.cagrilar.index(guncelleme) > adb.cagrilar.index(sorgular[-1])


def test_gonder_galeriye_eklenmezse_hata(tmp_path):
    (f := tmp_path / "a.jpg").write_bytes(b"x")
    with pytest.raises(GaleriHatasi):
        gonder(SahteAdb(), f, tmp_path / "gecici", uyku=lambda sn: None)


def test_gonder_gelecek_tarihli_fotografin_onune_gecer(tmp_path):
    # galeride çekim tarihi "şimdi"den ileri bir fotoğraf varsa bizimki yine en yeni olmalı
    (f := tmp_path / "a.jpg").write_bytes(b"x")
    adb = SahteAdb({"content query --uri content://media/external/images/media --projection datetaken":
                    ["Row: 0 datetaken=4102444800000\nRow: 1 datetaken=1792128061000"],
                    "content query": ["Row: 0 _id=7"]})
    gonder(adb, f, tmp_path / "gecici", uyku=lambda sn: None, simdi=lambda: 1800000000.0)
    guncelleme = next(c for c in adb.cagrilar if c.startswith("content update"))
    assert "datetaken:l:4102444800001" in guncelleme
