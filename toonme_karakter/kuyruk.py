"""Aynı anda tek ToonMe işi: sağ tıkla açılan süreçler bir kilit dosyasında sıraya girer."""
import msvcrt
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def sira(kilit_yolu: Path, aralik: float = 0.5) -> Iterator[None]:
    kilit_yolu.parent.mkdir(parents=True, exist_ok=True)
    with open(kilit_yolu, "a+b") as f:
        f.seek(0)
        while True:
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                time.sleep(aralik)
        try:
            yield
        finally:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
