"""BlueStacks'i bulma, gerekirse başlatma ve ADB bağlantısını hazırlama."""
import logging
import re
import subprocess
import time
from dataclasses import dataclass

from .adb import PENCERESIZ, Adb
from .ayarlar import Ayarlar

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConfBilgisi:
    adb_acik: bool
    adb_port: int


class ADBKapali(Exception):
    pass


class BaslatmaZamanAsimi(Exception):
    pass


def _deger(metin: str, anahtar: str) -> str | None:
    m = re.search(rf'^{re.escape(anahtar)}="([^"]*)"', metin, re.MULTILINE)
    return m.group(1) if m else None


def conf_oku(metin: str, ornek: str) -> ConfBilgisi:
    port = (_deger(metin, f"bst.instance.{ornek}.status.adb_port")
            or _deger(metin, f"bst.instance.{ornek}.adb_port") or "5555")
    return ConfBilgisi(_deger(metin, "bst.enable_adb_access") == "1", int(port))


def _calisiyor_mu() -> bool:
    s = subprocess.run(["tasklist", "/FI", "IMAGENAME eq HD-Player.exe", "/NH"],
                       capture_output=True, text=True, creationflags=PENCERESIZ)
    return "HD-Player.exe" in s.stdout


def _baglan(ayarlar: Ayarlar, port: int) -> bool:
    s = subprocess.run([str(ayarlar.bluestacks_dizini / "HD-Adb.exe"), "connect", f"127.0.0.1:{port}"],
                       capture_output=True, text=True, timeout=15, creationflags=PENCERESIZ)
    return "connected to" in s.stdout


def hazirla(ayarlar: Ayarlar, bekleme_sn: float = 90) -> Adb:
    bilgi = conf_oku(ayarlar.bluestacks_conf.read_text(encoding="utf-8", errors="replace"), ayarlar.bluestacks_ornek)
    if not bilgi.adb_acik:
        raise ADBKapali()
    if not _calisiyor_mu():
        log.info("BlueStacks başlatılıyor (%s)", ayarlar.bluestacks_ornek)
        subprocess.Popen([str(ayarlar.bluestacks_dizini / "HD-Player.exe"), "--instance", ayarlar.bluestacks_ornek],
                         creationflags=subprocess.DETACHED_PROCESS)
    bitis = time.monotonic() + bekleme_sn
    while True:
        # port açılış sırasında değişebildiği için conf her turda yeniden okunur
        bilgi = conf_oku(ayarlar.bluestacks_conf.read_text(encoding="utf-8", errors="replace"), ayarlar.bluestacks_ornek)
        try:
            if _baglan(ayarlar, bilgi.adb_port):
                adb = Adb(ayarlar.bluestacks_dizini / "HD-Adb.exe", f"127.0.0.1:{bilgi.adb_port}")
                if adb.kabuk("getprop", "sys.boot_completed", zaman_asimi=10).strip() == "1":
                    return adb
        except Exception as h:  # açılış sırasında adb geçici olarak hata verebilir
            log.debug("BlueStacks henüz hazır değil: %s", h)
        if time.monotonic() > bitis:
            raise BaslatmaZamanAsimi()
        time.sleep(3)
