import pytest

from toonme_karakter.ekran import Ekran, EkranZamanAsimi, Secici, bul, odak_ayristir
from tests.sahte import SahteAdb
from tests.veri import F


class SahteSaat:
    def __init__(self):
        self.an = 0.0

    def saat(self):
        return self.an

    def uyku(self, sn):
        self.an += sn


def ekran(adb):
    s = SahteSaat()
    return Ekran(adb, uyku=s.uyku, saat=s.saat)


def test_hemen_bulur():
    assert ekran(SahteAdb(ekranlar=[F("sonuc.xml")])).bekle(Secici(kimlik="more"), 5).merkez == (1552, 78)


def test_dok_tek_kabuk_cagrisi():
    adb = SahteAdb(ekranlar=[F("sonuc.xml")])
    ekran(adb).dok()
    assert adb.cagrilar == ["uiautomator dump /data/local/tmp/ui.xml >/dev/null && cat /data/local/tmp/ui.xml"]


def test_reklami_kapatip_bulur():
    adb = SahteAdb(ekranlar=[F("reklam.xml"), F("sonuc.xml")])
    ekran(adb).bekle(Secici(kimlik="more"), 10)
    assert "input tap 1557 43" in adb.cagrilar


def test_yabanci_pakette_geri():
    adb = SahteAdb({"dumpsys window": ["  mCurrentFocus=Window{1 u0 com.baska/X}"]},
                   ekranlar=["<hierarchy/>", F("sonuc.xml")])
    ekran(adb).bekle(Secici(kimlik="more"), 10, beklenen_paket="com.vicman.toonmeapp")
    assert "input keyevent 4" in adb.cagrilar


def test_kendi_paketindeyken_geri_basmaz():
    adb = SahteAdb({"dumpsys window": ["  mCurrentFocus=Window{1 u0 com.vicman.toonmeapp/X}"]},
                   ekranlar=["<hierarchy/>", F("sonuc.xml")])
    ekran(adb).bekle(Secici(kimlik="more"), 10, beklenen_paket="com.vicman.toonmeapp")
    assert "input keyevent 4" not in adb.cagrilar


@pytest.mark.parametrize("odak", [
    "  mCurrentFocus=Window{1 u0 Splash Screen com.vicman.toonmeapp}",  # soğuk açılış (gerçek cihazda görüldü)
    "  mCurrentFocus=null",
])
def test_odak_belirsizken_geri_basmaz(odak):
    adb = SahteAdb({"dumpsys window": [odak]}, ekranlar=["<hierarchy/>", F("sonuc.xml")])
    ekran(adb).bekle(Secici(kimlik="more"), 10, beklenen_paket="com.vicman.toonmeapp")
    assert "input keyevent 4" not in adb.cagrilar


def test_en_fazla_uc_engel():
    adb = SahteAdb(ekranlar=[F("reklam.xml")])
    with pytest.raises(EkranZamanAsimi):
        ekran(adb).bekle(Secici(kimlik="more"), 20)
    assert adb.cagrilar.count("input tap 1557 43") == 3


def test_zaman_asimi_son_ogeler():
    with pytest.raises(EkranZamanAsimi) as h:
        ekran(SahteAdb(ekranlar=[F("kirpma.xml")])).bekle(Secici(kimlik="more"), 5)
    assert h.value.aranan == Secici(kimlik="more")
    assert bul(h.value.son_ogeler, Secici(kimlik="next_btn"))


def test_kosul_her_turda():
    cagri = []

    def kosul(ogeler):
        cagri.append(len(ogeler))
        return len(cagri) >= 2

    adb = SahteAdb(ekranlar=[F("sonuc.xml")])
    assert ekran(adb).bekle(Secici(kimlik="more"), 10, kosul=kosul)
    assert len(cagri) == 2
    assert adb.cagrilar.count("uiautomator dump /data/local/tmp/ui.xml >/dev/null && cat /data/local/tmp/ui.xml") == 2


def test_kosul_firlatirsa_yayilir():
    def kosul(ogeler):
        raise ValueError("hata ekranı")

    with pytest.raises(ValueError):
        ekran(SahteAdb(ekranlar=[F("sonuc.xml")])).bekle(Secici(kimlik="more"), 10, kosul=kosul)


def test_dokun_merkeze():
    adb = SahteAdb(ekranlar=[F("kirpma.xml")])
    e = ekran(adb)
    e.dokun(e.bekle(Secici(kimlik="next_btn"), 5))
    assert adb.cagrilar[-1] == "input tap 1534 750"


def test_odak_ayristir():
    metin = ("  mCurrentFocus=Window{2213f51 u0 com.vicman.toonmeapp/"
             "com.vicman.photolab.activities.NewPhotoChooserActivity}")
    assert odak_ayristir(metin) == "com.vicman.toonmeapp/com.vicman.photolab.activities.NewPhotoChooserActivity"
    assert odak_ayristir("mCurrentFocus=null") == ""
