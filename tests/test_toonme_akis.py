import pytest

from toonme_karakter.ekran import Ekran
from toonme_karakter.toonme_akis import AkisHatasi, calistir, calistir_tekrarli
from tests.sahte import SahteAdb
from tests.test_ekran_bekle import SahteSaat
from tests.veri import F

URL = "https://toonme.com/d/48671890"
# "Recent" ToonMe'nin kendi geçmişi; galeriyi gösteren "All" seçilir (gerçek cihazda yanlış foto seçilmişti)
MUTLU = [F("secici_recent.xml"), F("secici_all.xml"), F("kirpma.xml"), F("sonuc.xml"), F("menu.xml"),
         F("kaydet_paylas.xml")]
DOKUM = "uiautomator dump /data/local/tmp/ui.xml >/dev/null && cat /data/local/tmp/ui.xml"
HATA = ('<hierarchy><node text="No faces found" resource-id="com.vicman.toonmeapp:id/snackbar_text" '
        'class="android.widget.TextView" content-desc="" clickable="false" bounds="[0,0][10,10]"/></hierarchy>')


SECICI_ODAGI = "  mCurrentFocus=Window{1 u0 com.vicman.toonmeapp/com.vicman.photolab.activities.NewPhotoChooserActivity}"
ANA_ODAK = "  mCurrentFocus=Window{1 u0 com.vicman.toonmeapp/com.vicman.photolab.activities.portrait.MainActivityTablet}"


def kur(ekranlar, ls=("", "f39d.jpg\n"), odaklar=(SECICI_ODAGI,)):
    adb = SahteAdb({"ls -1 /sdcard/Pictures/ToonMe": list(ls), "dumpsys window": list(odaklar)}, ekranlar=ekranlar)
    s = SahteSaat()
    return adb, Ekran(adb, uyku=s.uyku, saat=s.saat)


def dokunuslar(adb):
    return [c for c in adb.cagrilar if c.startswith("input tap")]


def test_mutlu_yol():
    adb, e = kur(MUTLU)
    assert calistir(e, adb, URL, 180) == "/sdcard/Pictures/ToonMe/f39d.jpg"
    assert dokunuslar(adb)[0] == "input tap 75 155"  # All sekmesi
    assert dokunuslar(adb)[1:4] == ["input tap 332 260", "input tap 1534 750", "input tap 1552 78"]
    assert len(dokunuslar(adb)) == 6  # + Save to device + Download
    assert any(c.startswith("am start") and URL in c for c in adb.cagrilar)


def test_her_deneme_toonme_kapatilarak_baslar():
    # Aynı süreçte daha önce kaydedilmiş bir sonucu ToonMe yeniden kaydetmiyor (gerçek cihazda görüldü)
    adb, e = kur(MUTLU)
    calistir(e, adb, URL, 180)
    i_stop = adb.cagrilar.index("am force-stop com.vicman.toonmeapp")
    i_start = next(i for i, c in enumerate(adb.cagrilar) if c.startswith("am start"))
    assert i_stop < i_start


def test_sablon_secici_ekrani_beklenir():
    # ana ekranın şablon ızgarasında da list_item_0 ve seçili "All" var; orada dokunmak başka şablon açar
    adb, e = kur([F("secici_all.xml"), F("secici_all.xml")] + MUTLU[1:], odaklar=(ANA_ODAK, SECICI_ODAGI))
    calistir(e, adb, URL, 180)
    i_start = next(i for i, c in enumerate(adb.cagrilar) if c.startswith("am start"))
    i_ilk_dokunus = next(i for i, c in enumerate(adb.cagrilar) if c.startswith("input tap"))
    # odak önce ana ekran, sonra seçici: ilk dokunuştan önce odak en az iki kez sorulmuş olmalı
    assert adb.cagrilar[i_start:i_ilk_dokunus].count("dumpsys window windows") >= 2


def test_secici_ekrani_gelmezse_sablon_hatasi():
    adb, e = kur([F("secici_all.xml")], odaklar=(ANA_ODAK,))
    with pytest.raises(AkisHatasi) as h:
        calistir(e, adb, URL, 180)
    assert h.value.adim == "sablon"
    assert not any(c.startswith("input tap") for c in adb.cagrilar)


def test_yeni_dosyalarin_sonuncusu_secilir():
    adb, e = kur(MUTLU, ls=("eski.jpg\n", "eski.jpg\nb.jpg\na.jpg\nnot.txt\n"))
    assert calistir(e, adb, URL, 180) == "/sdcard/Pictures/ToonMe/b.jpg"


def test_web_secicide_all_sekmesi():
    adb, e = kur([F("secici_recommended.xml")] + MUTLU[1:])
    assert calistir(e, adb, URL, 180) == "/sdcard/Pictures/ToonMe/f39d.jpg"
    assert dokunuslar(adb)[0] == "input tap 75 155"


def test_all_zaten_seciliyse_dokunulmaz():
    # seçili "All"a tekrar dokunmak albüm menüsünü açar
    adb, e = kur([F("secici_all.xml")] + MUTLU[1:])
    calistir(e, adb, URL, 180)
    assert "input tap 75 155" not in adb.cagrilar
    assert dokunuslar(adb)[0] == "input tap 332 260"


def test_all_dokunusu_tutmazsa_tekrar_dokunulur():
    # soğuk açılışta seçici geç yüklenince ilk "All" dokunuşu boşa gitti (gerçek cihazda görüldü)
    recent = F("secici_recent.xml")
    adb, e = kur([recent, recent, recent] + MUTLU[1:])
    assert calistir(e, adb, URL, 180) == "/sdcard/Pictures/ToonMe/f39d.jpg"
    assert adb.cagrilar.count("input tap 75 155") == 3


def test_all_secilmeden_foto_secilmez():
    adb, e = kur([F("secici_recent.xml")])
    with pytest.raises(AkisHatasi) as h:
        calistir(e, adb, URL, 180)
    assert h.value.adim == "fotograf"
    assert "input tap 332 260" not in adb.cagrilar


def test_kirpma_zaman_asimi_adim_adi():
    adb, e = kur([F("secici_recent.xml"), F("secici_all.xml")])
    with pytest.raises(AkisHatasi) as h:
        calistir(e, adb, URL, 180)
    assert h.value.adim == "kirpma"
    assert "Recent" in h.value.ayrinti


def test_cikti_gelmezse_adim_adi():
    adb, e = kur(MUTLU, ls=("",))
    with pytest.raises(AkisHatasi) as h:
        calistir(e, adb, URL, 180)
    assert h.value.adim == "cikti"


def test_isleme_progressbar_varken_beklenir():
    isleniyor = F("sonuc.xml").replace(
        "</hierarchy>",
        '<node text="" resource-id="" class="android.widget.ProgressBar" content-desc="" clickable="false" '
        'bounds="[700,400][900,600]"/></hierarchy>')
    adb, e = kur(MUTLU[:3] + [isleniyor, F("sonuc.xml")] + MUTLU[4:])
    calistir(e, adb, URL, 180)
    i_kirpma = adb.cagrilar.index("input tap 1534 750")
    i_more = adb.cagrilar.index("input tap 1552 78")
    assert adb.cagrilar[i_kirpma:i_more].count(DOKUM) == 2


def test_gercek_isleniyor_ekraninda_kaydetmeye_gecilmez():
    # gerçek cihazda işleme ~17 sn sürüyor; bu sırada "Processing…" ve progressBar var, "more" yok
    adb, e = kur(MUTLU[:3] + [F("isleniyor.xml")] * 3 + MUTLU[3:])
    calistir(e, adb, URL, 180)
    i_kirpma = adb.cagrilar.index("input tap 1534 750")
    i_more = adb.cagrilar.index("input tap 1552 78")
    assert adb.cagrilar[i_kirpma:i_more].count(DOKUM) == 4


def test_toonme_hatasi_tekrar_yok():
    adb, e = kur(MUTLU[:3] + [HATA])
    with pytest.raises(AkisHatasi) as h:
        calistir_tekrarli(e, adb, URL, 180)
    assert h.value.adim == "toonme_hatasi"
    assert "No faces found" in h.value.ayrinti
    assert sum(c.startswith("am start") for c in adb.cagrilar) == 1


def test_tekrarli_bir_kez_yeniden_dener():
    # ilk deneme kırpma ekranı yerine seçici ekranında kalır (20 sn), ikinci deneme mutlu yol
    takili = [F("secici_recent.xml")] + [F("secici_all.xml")] * 22
    adb, e = kur(takili + MUTLU, ls=("", "", "f39d.jpg\n"))  # her deneme önce çıktı klasörünü listeler
    assert calistir_tekrarli(e, adb, URL, 180) == "/sdcard/Pictures/ToonMe/f39d.jpg"
    assert adb.cagrilar.count("am force-stop com.vicman.toonmeapp") == 2  # her denemenin başında
    assert sum(c.startswith("am start") for c in adb.cagrilar) == 2


def test_tekrarli_ikinci_hatada_firlatir():
    adb, e = kur([F("secici_recent.xml")])
    with pytest.raises(AkisHatasi):
        calistir_tekrarli(e, adb, URL, 180)
    assert sum(c.startswith("am start") for c in adb.cagrilar) == 2
