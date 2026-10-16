"""Testler için Adb yerine geçen kayıt tutan sahte."""
from pathlib import Path


class SahteAdb:
    def __init__(self, yanitlar=None, ekranlar=None):
        self.yanitlar = {k: list(v) for k, v in (yanitlar or {}).items()}
        self.ekranlar = list(ekranlar or [])
        self.cagrilar: list[str] = []
        self._sira: dict[str, int] = {}

    def _siradaki(self, anahtar, liste):
        i = self._sira.get(anahtar, 0)
        self._sira[anahtar] = i + 1
        return liste[min(i, len(liste) - 1)]

    def kabuk(self, *arg, zaman_asimi=30):
        komut = " ".join(arg)
        self.cagrilar.append(komut)
        if komut.startswith("uiautomator dump"):
            return self._siradaki("__ekran__", self.ekranlar) if self.ekranlar else ""
        for anahtar, liste in self.yanitlar.items():
            if komut.startswith(anahtar) and liste:
                yanit = self._siradaki(anahtar, liste)
                if isinstance(yanit, Exception):
                    raise yanit
                return yanit
        return ""

    def gonder(self, yerel: Path, uzak: str) -> None:
        self.cagrilar.append(f"push {yerel} {uzak}")

    def al(self, uzak: str, yerel: Path) -> None:
        self.cagrilar.append(f"pull {uzak} {yerel}")
        Path(yerel).write_bytes(b"jpg")

    def ekran_goruntusu(self) -> bytes:
        return b"png"
