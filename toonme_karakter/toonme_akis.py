"""ToonMe içinde şablonu açıp fotoğrafı işleyen ve sonucu kaydeden adımlar (spec §3, adım 3–8)."""
import logging

from .aktarim import CIKTI_DIZINI, listele
from .ekran import Ekran, EkranZamanAsimi, Oge, Secici, bul, gorunen_metinler

log = logging.getLogger(__name__)

PAKET = "com.vicman.toonmeapp"
CIKTI_BEKLEME_SN = 20


class AkisHatasi(Exception):
    def __init__(self, adim: str, ayrinti: str, son_ogeler: list[Oge]):
        super().__init__(f"{adim}: {ayrinti}")
        self.adim = adim
        self.ayrinti = ayrinti
        self.son_ogeler = son_ogeler


def _isleme_bitti(ogeler: list[Oge]) -> bool:
    for o in ogeler:
        if o.kimlik in ("snackbar_text", "message") and o.metin:
            raise AkisHatasi("toonme_hatasi", o.metin, ogeler)
    return not any("ProgressBar" in o.sinif for o in ogeler)


def _bekle_dokun(ekran: Ekran, adim: str, secici: Secici, zaman_asimi: float, **kw) -> None:
    try:
        oge = ekran.bekle(secici, zaman_asimi, **kw)
    except EkranZamanAsimi as h:
        raise AkisHatasi(adim, f"{secici} bulunamadı; ekranda: {gorunen_metinler(h.son_ogeler)[:8]}",
                         h.son_ogeler) from h
    log.info("%s: %s", adim, secici)
    ekran.dokun(oge)


def calistir(ekran: Ekran, adb, sablon_url: str, isleme_zaman_asimi: float) -> str:
    once = listele(adb, CIKTI_DIZINI)

    adb.kabuk("am", "start", "-W", "-a", "android.intent.action.VIEW", "-d", sablon_url, PAKET)
    try:
        ekran.bekle(Secici(aciklama="list_item_0"), 30, beklenen_paket=PAKET)
    except EkranZamanAsimi as h:
        raise AkisHatasi("sablon", f"şablon ekranı açılmadı; ekranda: {gorunen_metinler(h.son_ogeler)[:8]}",
                         h.son_ogeler) from h

    # Bazı şablonlar "Recent", bazıları "Recommended" sekmesiyle açılır; ilk fotoğraf Recent/All'da bizimkidir
    sekme = bul(ekran.son_ogeler, Secici(metin="Recent")) or bul(ekran.son_ogeler, Secici(metin="All"))
    if sekme:
        ekran.dokun(sekme)
    _bekle_dokun(ekran, "fotograf", Secici(aciklama="list_item_2"), 15)
    _bekle_dokun(ekran, "kirpma", Secici(kimlik="next_btn"), 20)
    _bekle_dokun(ekran, "isleme", Secici(kimlik="more"), isleme_zaman_asimi,
                 kosul=_isleme_bitti, beklenen_paket=PAKET)
    _bekle_dokun(ekran, "kaydetme", Secici(metin="Save to device"), 10)
    _bekle_dokun(ekran, "kaydetme", Secici(metin="Download"), 15)

    bitis = ekran.saat() + CIKTI_BEKLEME_SN
    while True:
        yeni = sorted(y for y in listele(adb, CIKTI_DIZINI) - once if y.lower().endswith(".jpg"))
        if yeni:
            return yeni[-1]
        if ekran.saat() >= bitis:
            raise AkisHatasi("cikti", f"{CIKTI_DIZINI} içinde yeni dosya oluşmadı", ekran.son_ogeler)
        ekran.uyku(1)


def calistir_tekrarli(ekran: Ekran, adb, sablon_url: str, isleme_zaman_asimi: float, deneme: int = 2) -> str:
    for i in range(1, deneme + 1):
        try:
            return calistir(ekran, adb, sablon_url, isleme_zaman_asimi)
        except AkisHatasi as h:
            if h.adim == "toonme_hatasi" or i == deneme:
                raise
            log.warning("Deneme %d başarısız (%s); ToonMe kapatılıp baştan deneniyor", i, h)
            adb.kabuk("am", "force-stop", PAKET)
    raise AssertionError("ulaşılamaz")
