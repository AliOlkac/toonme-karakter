"""ayarlar.json okuma ve uygulama genelindeki sabit yollar."""
import dataclasses
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

PROJE_DIZINI = Path(__file__).resolve().parent.parent


class AyarHatasi(Exception):
    pass


@dataclass(frozen=True)
class Ayarlar:
    sablon_url: str = "https://toonme.com/d/48671890"
    isleme_zaman_asimi_sn: int = 180
    bluestacks_ornek: str = "Pie64"
    bluestacks_dizini: Path = Path(r"C:\Program Files\BlueStacks_nxt")
    bluestacks_conf: Path = Path(r"C:\ProgramData\BlueStacks_nxt\bluestacks.conf")


def oku(yol: Path) -> Ayarlar:
    if not yol.exists():
        return Ayarlar()
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (ValueError, OSError) as h:
        raise AyarHatasi(f"{yol.name} okunamadı: {h}") from h
    if not isinstance(veri, dict):
        raise AyarHatasi(f"{yol.name} bir JSON nesnesi olmalı")

    alanlar = {f.name: f for f in dataclasses.fields(Ayarlar)}
    degerler = {}
    for ad, deger in veri.items():
        if ad not in alanlar:
            continue
        varsayilan = alanlar[ad].default
        if isinstance(varsayilan, Path):
            deger = Path(deger)
        elif isinstance(varsayilan, int) and (not isinstance(deger, int) or isinstance(deger, bool)):
            raise AyarHatasi(f"{ad} bir tam sayı olmalı: {deger!r}")
        degerler[ad] = deger

    if "sablon_url" in degerler:
        url = str(degerler["sablon_url"]).split("?")[0]
        if not re.fullmatch(r"https://toonme\.com/d/\d+", url):
            raise AyarHatasi(f"sablon_url geçersiz (https://toonme.com/d/<sayı> olmalı): {degerler['sablon_url']}")
        degerler["sablon_url"] = url
    return Ayarlar(**degerler)


def veri_dizini() -> Path:
    dizin = Path(os.environ["LOCALAPPDATA"]) / "ToonMeKarakter"
    dizin.mkdir(parents=True, exist_ok=True)
    return dizin
