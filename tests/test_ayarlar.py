import json

import pytest

from toonme_karakter.ayarlar import AyarHatasi, Ayarlar, oku, veri_dizini


def yaz(yol, veri):
    yol.write_text(json.dumps(veri), encoding="utf-8")
    return yol


def test_dosya_yoksa_varsayilanlar(tmp_path):
    assert oku(tmp_path / "yok.json") == Ayarlar()


def test_kismi_dosya_digerleri_varsayilan(tmp_path):
    a = oku(yaz(tmp_path / "a.json", {"isleme_zaman_asimi_sn": 60}))
    assert a.isleme_zaman_asimi_sn == 60
    assert a.sablon_url == "https://toonme.com/d/48671890"


def test_bilinmeyen_anahtar_yok_sayilir(tmp_path):
    assert oku(yaz(tmp_path / "a.json", {"foo": 1})) == Ayarlar()


def test_url_sorgusu_atilir(tmp_path):
    p = yaz(tmp_path / "a.json", {"sablon_url": "https://toonme.com/d/53865123?utm_source=app"})
    assert oku(p).sablon_url == "https://toonme.com/d/53865123"


def test_gecersiz_url_hata(tmp_path):
    p = yaz(tmp_path / "a.json", {"sablon_url": "https://example.com/x"})
    with pytest.raises(AyarHatasi, match="sablon_url"):
        oku(p)


def test_sayi_alani_sayi_degilse_hata(tmp_path):
    p = yaz(tmp_path / "a.json", {"isleme_zaman_asimi_sn": "uzun"})
    with pytest.raises(AyarHatasi, match="isleme_zaman_asimi_sn"):
        oku(p)


def test_bozuk_json_hata(tmp_path):
    p = tmp_path / "ayarlar.json"
    p.write_text("{bozuk", encoding="utf-8")
    with pytest.raises(AyarHatasi, match="ayarlar.json"):
        oku(p)


def test_veri_dizini_localappdata(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert veri_dizini() == tmp_path / "ToonMeKarakter"
    assert veri_dizini().is_dir()
