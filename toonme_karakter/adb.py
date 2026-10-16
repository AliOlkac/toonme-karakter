"""BlueStacks'in HD-Adb.exe'si için ince sarmalayıcı. Tüm ADB çağrıları buradan geçer."""
import subprocess
from pathlib import Path

# pythonw'dan (sağ tık) çalışırken her ADB çağrısında konsol penceresi açılmasın
PENCERESIZ = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class AdbHatasi(Exception):
    pass


class Adb:
    def __init__(self, exe: Path, seri: str, calistirici=subprocess.run):
        self.exe = exe
        self.seri = seri
        self._calistirici = calistirici

    def _calistir(self, *arg: str, zaman_asimi: float = 30) -> bytes:
        try:
            s = self._calistirici([str(self.exe), "-s", self.seri, *arg], capture_output=True,
                                  timeout=zaman_asimi, creationflags=PENCERESIZ)
        except subprocess.TimeoutExpired as h:
            raise AdbHatasi(f"adb {' '.join(arg)}: {zaman_asimi} sn içinde yanıt yok") from h
        if s.returncode != 0:
            hata = (s.stderr or s.stdout or b"").decode("utf-8", errors="replace").strip()
            raise AdbHatasi(f"adb {' '.join(arg)}: {hata}")
        return s.stdout

    def komut(self, *arg: str, zaman_asimi: float = 30) -> str:
        return self._calistir(*arg, zaman_asimi=zaman_asimi).decode("utf-8", errors="replace")

    def kabuk(self, *arg: str, zaman_asimi: float = 30) -> str:
        return self.komut("shell", *arg, zaman_asimi=zaman_asimi)

    def gonder(self, yerel: Path, uzak: str) -> None:
        self.komut("push", str(yerel), uzak, zaman_asimi=120)

    def al(self, uzak: str, yerel: Path) -> None:
        self.komut("pull", uzak, str(yerel), zaman_asimi=120)

    def ekran_goruntusu(self) -> bytes:
        return self._calistir("exec-out", "screencap", "-p")
