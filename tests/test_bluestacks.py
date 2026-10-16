import subprocess

import pytest

from toonme_karakter.ayarlar import Ayarlar
from toonme_karakter.bluestacks import ADBKapali, ConfBilgisi, conf_oku, hazirla


def test_conf_status_portu_oncelikli():
    metin = ('bst.enable_adb_access="1"\nbst.instance.Pie64.adb_port="5555"\n'
             'bst.instance.Pie64.status.adb_port="5565"')
    assert conf_oku(metin, "Pie64") == ConfBilgisi(True, 5565)


def test_conf_yedek_port():
    metin = 'bst.enable_adb_access="1"\nbst.instance.Pie64.adb_port="5555"'
    assert conf_oku(metin, "Pie64") == ConfBilgisi(True, 5555)


def test_conf_adb_kapali():
    metin = 'bst.enable_adb_access="0"\nbst.instance.Pie64.status.adb_port="5555"'
    assert conf_oku(metin, "Pie64").adb_acik is False


def test_conf_baska_ornegin_portu_karismaz():
    metin = 'bst.enable_adb_access="1"\nbst.instance.Nougat64.status.adb_port="5575"'
    assert conf_oku(metin, "Pie64") == ConfBilgisi(True, 5555)


def test_conf_anahtar_yok():
    assert conf_oku("", "Pie64") == ConfBilgisi(False, 5555)


def test_hazirla_adb_kapaliysa_baslatmaz(tmp_path, monkeypatch):
    conf = tmp_path / "bluestacks.conf"
    conf.write_text('bst.enable_adb_access="0"\n', encoding="utf-8")

    def patla(*a, **kw):
        raise AssertionError("BlueStacks başlatılmamalıydı")

    monkeypatch.setattr(subprocess, "Popen", patla)
    with pytest.raises(ADBKapali):
        hazirla(Ayarlar(bluestacks_conf=conf))
