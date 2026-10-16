"""Gezgin'deki "ToonMe karakter yap" sağ tık menüsünü ekleme/kaldırma (yalnızca HKCU, yönetici gerekmez)."""
import os
import sys
import winreg
from pathlib import Path

ANAHTAR = r"Software\Classes\SystemFileAssociations\image\shell\ToonMeKarakter"
SIMGE = Path(os.environ["ALLUSERSPROFILE"]) / r"BlueStacks_nxt\Engine\Pie64\AppCache\com.vicman.toonmeapp.ico"


def komut_satiri(pythonw: Path, betik: Path) -> str:
    return f'"{pythonw}" "{betik}" "%1"'


def pythonw_yolu() -> Path:
    return Path(sys.executable).with_name("pythonw.exe")


def kur(pythonw: Path, betik: Path, simge: Path, anahtar: str = ANAHTAR) -> None:
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, anahtar) as k:
        winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, "ToonMe karakter yap")
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, str(simge))
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, anahtar + r"\command") as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, komut_satiri(pythonw, betik))


def kaldir(anahtar: str = ANAHTAR) -> None:
    for alt in (anahtar + r"\command", anahtar):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, alt)
        except FileNotFoundError:
            pass
