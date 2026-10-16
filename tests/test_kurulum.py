import winreg
from pathlib import Path

import pytest

from toonme_karakter.kurulum import kaldir, komut_satiri, kur

TEST_KOK = r"Software\ToonMeKarakterTest"
TEST_ANAHTAR = TEST_KOK + r"\shell\ToonMeKarakter"


@pytest.fixture
def temiz_kayit():
    yield
    for alt in (TEST_ANAHTAR + r"\command", TEST_ANAHTAR, TEST_KOK + r"\shell", TEST_KOK):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, alt)
        except FileNotFoundError:
            pass


def test_komut_satiri():
    assert (komut_satiri(Path(r"C:\P y\pythonw.exe"), Path(r"C:\x\calistir.pyw"))
            == r'"C:\P y\pythonw.exe" "C:\x\calistir.pyw" "%1"')


def test_kur_kaldir(temiz_kayit):
    kur(Path(r"C:\p\pythonw.exe"), Path(r"C:\x\calistir.pyw"), Path(r"C:\s.ico"), TEST_ANAHTAR)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, TEST_ANAHTAR) as k:
        assert winreg.QueryValueEx(k, "MUIVerb")[0] == "ToonMe karakter yap"
        assert winreg.QueryValueEx(k, "Icon")[0] == r"C:\s.ico"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, TEST_ANAHTAR + r"\command") as k:
        assert winreg.QueryValueEx(k, "")[0] == r'"C:\p\pythonw.exe" "C:\x\calistir.pyw" "%1"'
    kaldir(TEST_ANAHTAR)
    kaldir(TEST_ANAHTAR)  # ikinci çağrı hata vermez
    with pytest.raises(FileNotFoundError):
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, TEST_ANAHTAR)
