import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from toonme_karakter import bildirim
from toonme_karakter.bildirim import goster, toast_xml


def test_toast_kacis():
    x = toast_xml("Karakter hazır", 'Çocuk & <1> "a".jpg', Path(r"C:\Kullanıcı\a b.jpg"))
    ET.fromstring(x)  # geçerli XML
    assert "Çocuk &amp; &lt;1&gt;" in x
    assert 'launch="file:///C:/Kullan%C4%B1c%C4%B1/a%20b.jpg"' in x
    assert 'activationType="protocol"' in x


def test_toast_acilacak_yoksa_launch_yok():
    x = toast_xml("a", "b")
    ET.fromstring(x)
    assert "launch=" not in x


def test_goster_hata_yutar(monkeypatch):
    def patla(*a, **kw):
        raise OSError("powershell yok")

    monkeypatch.setattr(subprocess, "run", patla)
    goster("başlık", "metin")  # fırlatmaz


def test_goster_powershell_kodlu_komut(monkeypatch):
    yakalanan = {}

    def yakala(args, **kw):
        yakalanan["args"] = args
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", yakala)
    goster("başlık", "metin")
    args = yakalanan["args"]
    assert args[0] == "powershell" and "-EncodedCommand" in args
    import base64
    betik = base64.b64decode(args[args.index("-EncodedCommand") + 1]).decode("utf-16-le")
    assert bildirim.POWERSHELL_AUMID in betik
