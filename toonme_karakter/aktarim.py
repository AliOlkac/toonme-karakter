"""Bilgisayar ile emülatör arasında dosya taşıma ve emülatörü temiz bırakma."""
import logging
import shutil
import time
import uuid
from collections.abc import Iterable
from pathlib import Path

from .adb import AdbHatasi

log = logging.getLogger(__name__)

GIRDI_DIZINI = "/sdcard/Pictures/ToonMeInput"
CIKTI_DIZINI = "/sdcard/Pictures/ToonMe"
DESTEKLENEN = {".jpg", ".jpeg", ".png", ".webp"}


class DesteklenmeyenDosya(Exception):
    pass


class GaleriHatasi(Exception):
    pass


GALERI_DENEME = 20  # 0,5 sn arayla ~10 sn


def dogrula(yerel: Path) -> None:
    if not yerel.is_file():
        raise FileNotFoundError(yerel)
    if yerel.suffix.lower() not in DESTEKLENEN:
        raise DesteklenmeyenDosya(yerel.suffix)


def cikti_yolu(girdi: Path) -> Path:
    aday = girdi.with_name(f"{girdi.stem}_toon.jpg")
    n = 2
    while aday.exists():
        aday = girdi.with_name(f"{girdi.stem}_toon ({n}).jpg")
        n += 1
    return aday


def medya_yolu(uzak: str) -> str:
    return "/storage/emulated/0/" + uzak.removeprefix("/sdcard/")


def gonder(adb, yerel: Path, gecici_dizin: Path, *, uyku=time.sleep, simdi=time.time) -> str:
    # adb'ye yalnızca ASCII yollar verilir; Türkçe karakterli/boşluklu adlar geçici kopya üzerinden gider
    uzanti = yerel.suffix.lower()
    gecici_dizin.mkdir(parents=True, exist_ok=True)
    kopya = gecici_dizin / f"{uuid.uuid4().hex}{uzanti}"
    shutil.copyfile(yerel, kopya)
    uzak = f"{GIRDI_DIZINI}/toonme_{uuid.uuid4().hex}{uzanti}"
    try:
        adb.kabuk("mkdir", "-p", GIRDI_DIZINI)
        adb.gonder(kopya, uzak)
        adb.kabuk("am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{uzak}")
    finally:
        kopya.unlink(missing_ok=True)
    _en_yeni_yap(adb, uzak, uyku, simdi)
    return uzak


def _en_yeni_yap(adb, uzak: str, uyku, simdi) -> None:
    # ToonMe'nin "All" listesi çekim tarihine göre sıralanır; telefondan gelen fotoğrafın EXIF tarihi eski
    # olabileceği için galeri kaydının çekim tarihi "şimdi" yapılır ki listenin başına gelsin
    kosul = f"--where \"_data='{medya_yolu(uzak)}'\""
    for _ in range(GALERI_DENEME):
        if "Row:" in adb.kabuk(f"content query --uri content://media/external/images/media --projection _id {kosul}"):
            adb.kabuk(f"content update --uri content://media/external/images/media "
                      f"--bind datetaken:l:{int(simdi() * 1000)} {kosul}")
            return
        uyku(0.5)
    raise GaleriHatasi(uzak)


def listele(adb, dizin: str) -> set[str]:
    try:
        cikti = adb.kabuk("ls", "-1", dizin)
    except AdbHatasi:
        return set()
    return {f"{dizin}/{ad.strip()}" for ad in cikti.splitlines() if ad.strip()}


def al(adb, uzak: str, hedef: Path, gecici_dizin: Path) -> Path:
    gecici_dizin.mkdir(parents=True, exist_ok=True)
    kopya = gecici_dizin / f"{uuid.uuid4().hex}.jpg"
    adb.al(uzak, kopya)
    shutil.move(kopya, hedef)
    return hedef


def temizle(adb, uzak_yollar: Iterable[str]) -> None:
    for yol in uzak_yollar:
        try:
            adb.kabuk(f"rm -f {yol}; content delete --uri content://media/external/file "
                      f"--where \"_data='{medya_yolu(yol)}'\"")
        except AdbHatasi as h:
            log.warning("Emülatörde %s silinemedi: %s", yol, h)
