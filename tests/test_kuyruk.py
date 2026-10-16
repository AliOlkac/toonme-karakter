import threading
import time

import pytest

from toonme_karakter.kuyruk import sira


def test_ikinci_ilki_bitince_girer(tmp_path):
    k = tmp_path / "kuyruk.kilit"
    kayit = []

    def a():
        with sira(k, aralik=0.02):
            kayit.append("A-gir")
            time.sleep(0.5)
            kayit.append("A-cik")

    def b():
        time.sleep(0.1)
        with sira(k, aralik=0.02):
            kayit.append("B-gir")
            kayit.append("B-cik")

    ta, tb = threading.Thread(target=a), threading.Thread(target=b)
    ta.start(); tb.start(); ta.join(5); tb.join(5)
    assert kayit == ["A-gir", "A-cik", "B-gir", "B-cik"]


def test_hata_olunca_kilit_birakilir(tmp_path):
    k = tmp_path / "kuyruk.kilit"
    with pytest.raises(ValueError):
        with sira(k):
            raise ValueError
    bitti = threading.Event()

    def gir():
        with sira(k, aralik=0.01):
            bitti.set()

    t = threading.Thread(target=gir, daemon=True)
    t.start()
    assert bitti.wait(2), "kilit bırakılmamış"
