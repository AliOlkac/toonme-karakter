import subprocess
from pathlib import Path

import pytest

from toonme_karakter.adb import Adb, AdbHatasi


class SahteCalistirici:
    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.sonuc = (returncode, stdout, stderr)
        self.yakalanan = None

    def __call__(self, args, **kw):
        self.yakalanan = args
        rc, out, err = self.sonuc
        return subprocess.CompletedProcess(args, rc, out, err)


def test_komut_seri_ile():
    c = SahteCalistirici(stdout=b"9\n")
    assert Adb(Path(r"C:\x\HD-Adb.exe"), "127.0.0.1:5555", c).kabuk("getprop", "a") == "9\n"
    assert c.yakalanan == [r"C:\x\HD-Adb.exe", "-s", "127.0.0.1:5555", "shell", "getprop", "a"]


def test_komut_hata():
    c = SahteCalistirici(returncode=1, stderr=b"error: device not found")
    with pytest.raises(AdbHatasi, match="device not found"):
        Adb(Path("adb.exe"), "s", c).kabuk("ls")


def test_ekran_goruntusu_ikili():
    c = SahteCalistirici(stdout=b"\x89PNG\r\n")
    assert Adb(Path("adb.exe"), "s", c).ekran_goruntusu() == b"\x89PNG\r\n"
    assert c.yakalanan[-3:] == ["exec-out", "screencap", "-p"]


def test_cikti_utf8():
    c = SahteCalistirici(stdout="Алина П.".encode("utf-8"))
    assert Adb(Path("adb.exe"), "s", c).kabuk("cat", "x") == "Алина П."
