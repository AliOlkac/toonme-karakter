from toonme_karakter.ekran import Secici, ayristir, bul, gorunen_metinler
from tests.veri import F


def yukle(ad):
    return ayristir(F(ad))


def test_sonuc_more():
    o = bul(yukle("sonuc.xml"), Secici(kimlik="more"))
    assert o.tiklanabilir and o.merkez == (1552, 78)


def test_kirpma_next():
    assert bul(yukle("kirpma.xml"), Secici(kimlik="next_btn")).merkez == (1534, 750)


def test_recent_ilk_foto():
    o = yukle("secici_recent.xml")
    assert bul(o, Secici(metin="Recent"))
    assert bul(o, Secici(aciklama="list_item_2")).merkez == (332, 260)


def test_recommended_sekmesinde_all_var():
    assert bul(yukle("secici_recommended.xml"), Secici(metin="All")).merkez == (75, 155)


def test_menu_save():
    assert bul(yukle("menu.xml"), Secici(metin="Save to device"))


def test_kaydet_download():
    assert bul(yukle("kaydet_paylas.xml"), Secici(metin="Download"))


def test_reklam_kapat():
    assert bul(yukle("reklam.xml"), Secici(kimlik="close-or-skip-button")).merkez == (1557, 43)


def test_sonucta_progressbar_yok():
    assert not any("ProgressBar" in o.sinif for o in yukle("sonuc.xml"))


def test_bozuk_xml_bos_liste():
    assert ayristir("") == []
    assert ayristir("ERROR: could not get idle state.") == []


def test_gorunen_metinler_tekrarsiz():
    metinler = gorunen_metinler(yukle("sonuc.xml"))
    assert metinler[:1] == ["Result"]
    assert len(metinler) == len(set(metinler))


def test_secici_tum_alanlar_eslesmeli():
    o = yukle("kirpma.xml")
    assert bul(o, Secici(kimlik="next_btn", aciklama="Edit photo"))
    assert bul(o, Secici(kimlik="next_btn", aciklama="baska")) is None
