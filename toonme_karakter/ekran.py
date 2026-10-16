"""uiautomator dökümünden arayüz öğelerini okuma, bulma ve cihazda öğe bekleme."""
import logging
import re
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Oge:
    metin: str
    kimlik: str
    aciklama: str
    sinif: str
    tiklanabilir: bool
    sinirlar: tuple[int, int, int, int]
    secili: bool = False

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
            secili=n.get("selected") == "true",
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


# Akışın üstüne açılabilen reklam / teklif / puanlama pencerelerinin kapatma öğeleri
KAPATICILAR = (Secici(kimlik="close-or-skip-button"), Secici(metin="Not now"), Secici(metin="No thanks"),
               Secici(metin="Skip"), Secici(metin="Close"))
EN_FAZLA_ENGEL = 3
# Döküm galeriye düşmesin diye /sdcard yerine /data/local/tmp kullanılır
# uiautomator "could not get idle state" verip yine 0 ile çıkabiliyor; önceki dosya canlı ekran sanılmasın diye
# önce silinir. Döküm alınamazsa çıktı boş kalır ve ayristir() [] döndürür (çağıranlar beklemeye devam eder).
DOKUM_KOMUTU = ("rm -f /data/local/tmp/ui.xml; uiautomator dump /data/local/tmp/ui.xml >/dev/null; "
                "cat /data/local/tmp/ui.xml 2>/dev/null; true")


class EkranZamanAsimi(Exception):
    def __init__(self, aranan: Secici, son_ogeler: list[Oge]):
        super().__init__(f"{aranan} bulunamadı")
        self.aranan = aranan
        self.son_ogeler = son_ogeler


def odak_ayristir(dumpsys: str) -> str:
    m = re.search(r"mCurrentFocus=Window\{\S+ \S+ ([^}\s]+)\}", dumpsys)
    return m.group(1) if m else ""


class Ekran:
    def __init__(self, adb, uyku=time.sleep, saat=time.monotonic):
        self.adb = adb
        self.uyku = uyku
        self.saat = saat
        self.son_ogeler: list[Oge] = []

    def dok(self) -> list[Oge]:
        self.son_ogeler = ayristir(self.adb.kabuk(DOKUM_KOMUTU))
        return self.son_ogeler

    def odak(self) -> str:
        return odak_ayristir(self.adb.kabuk("dumpsys", "window", "windows"))

    def dokun(self, oge: Oge) -> None:
        x, y = oge.merkez
        self.adb.kabuk("input", "tap", str(x), str(y))

    def geri(self) -> None:
        self.adb.kabuk("input", "keyevent", "4")

    def _yabanci_onde(self, paket: str) -> bool:
        # Odak boşsa veya "Splash Screen" gibi geçiş penceresiyse (ayrıştırılamaz) Geri'ye basmak açılışı bozar
        odak = self.odak()
        return bool(odak) and not odak.startswith(paket + "/")

    def bekle(self, secici: Secici, zaman_asimi: float, *,
              kosul: Callable[[list[Oge]], bool] | None = None,
              beklenen_paket: str | None = None, aralik: float = 1.0) -> Oge:
        bitis = self.saat() + zaman_asimi
        engel = 0
        while True:
            ogeler = self.dok()
            tamam = kosul(ogeler) if kosul else True
            hedef = bul(ogeler, secici)
            if hedef and tamam:
                return hedef
            if not hedef and engel < EN_FAZLA_ENGEL:
                kapatici = next((o for s in KAPATICILAR if (o := bul(ogeler, s))), None)
                if kapatici:
                    log.info("Açılır pencere kapatılıyor: %s", kapatici)
                    self.dokun(kapatici)
                    engel += 1
                elif beklenen_paket and self._yabanci_onde(beklenen_paket):
                    log.info("Başka bir uygulama önde, Geri basılıyor")
                    self.geri()
                    engel += 1
            if self.saat() >= bitis:
                raise EkranZamanAsimi(secici, ogeler)
            self.uyku(aralik)
