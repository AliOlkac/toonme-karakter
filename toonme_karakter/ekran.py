"""uiautomator dökümünden arayüz öğelerini okuma ve bulma."""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass(frozen=True)
class Oge:
    metin: str
    kimlik: str
    aciklama: str
    sinif: str
    tiklanabilir: bool
    sinirlar: tuple[int, int, int, int]

    @property
    def merkez(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.sinirlar
        return (x1 + x2) // 2, (y1 + y2) // 2


def ayristir(xml: str) -> list[Oge]:
    try:
        kok = ET.fromstring(xml)
    except ET.ParseError:
        return []
    ogeler = []
    for n in kok.iter("node"):
        sayilar = [int(s) for s in re.findall(r"\d+", n.get("bounds", ""))]
        if len(sayilar) != 4:
            continue
        ogeler.append(Oge(
            metin=n.get("text", ""),
            kimlik=n.get("resource-id", "").rsplit("/", 1)[-1],
            aciklama=n.get("content-desc", ""),
            sinif=n.get("class", ""),
            tiklanabilir=n.get("clickable") == "true",
            sinirlar=tuple(sayilar),
        ))
    return ogeler


@dataclass(frozen=True)
class Secici:
    metin: str | None = None
    kimlik: str | None = None
    aciklama: str | None = None

    def eslesir(self, oge: Oge) -> bool:
        return ((self.metin is None or oge.metin == self.metin)
                and (self.kimlik is None or oge.kimlik == self.kimlik)
                and (self.aciklama is None or oge.aciklama == self.aciklama))


def bul(ogeler: list[Oge], secici: Secici) -> Oge | None:
    return next((o for o in ogeler if secici.eslesir(o)), None)


def gorunen_metinler(ogeler: list[Oge]) -> list[str]:
    return list(dict.fromkeys(o.metin for o in ogeler if o.metin))
