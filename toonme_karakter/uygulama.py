"""Tek bir fotoğrafın baştan sona işlenmesi ve komut satırı / sağ tık giriş noktası."""
import logging
import time
import traceback
from pathlib import Path

from . import aktarim, bluestacks, kurulum, kuyruk, toonme_akis
from .aktarim import DesteklenmeyenDosya
from .ayarlar import PROJE_DIZINI, AyarHatasi, Ayarlar, oku, veri_dizini
from .bildirim import goster
from .bluestacks import ADBKapali, BaslatmaZamanAsimi
from .ekran import DOKUM_KOMUTU, Ekran
from .toonme_akis import PAKET, AkisHatasi

log = logging.getLogger(__name__)

ADIM_ADLARI = {"sablon": "şablonu açma", "fotograf": "fotoğraf seçme", "kirpma": "kırpma", "isleme": "işleme",
               "kaydetme": "kaydetme", "cikti": "sonucu bulma", "toonme_hatasi": "ToonMe"}


def hata_kaydet(hata: Exception, adb, dizin: Path) -> Path:
    hedef = dizin / time.strftime("%Y%m%d-%H%M%S")
    try:
        hedef.mkdir(parents=True, exist_ok=True)
        (hedef / "hata.txt").write_text("".join(traceback.format_exception(hata)), encoding="utf-8")
        (hedef / "ekran.png").write_bytes(adb.ekran_goruntusu())
        (hedef / "ui.xml").write_text(adb.kabuk(DOKUM_KOMUTU), encoding="utf-8")
    except Exception as h:
        log.warning("Hata kaydı tamamlanamadı: %s", h)
    return hedef


def isle(foto: Path, ayarlar: Ayarlar, *, hazirla=bluestacks.hazirla, akis=toonme_akis.calistir_tekrarli,
         veri: Path | None = None) -> Path:
    veri = veri or veri_dizini()
    aktarim.dogrula(foto)
    adb = uzak_girdi = uzak_cikti = None
    try:
        adb = hazirla(ayarlar)
        uzak_girdi = aktarim.gonder(adb, foto, veri / "gecici")
        uzak_cikti = akis(Ekran(adb), adb, ayarlar.sablon_url, ayarlar.isleme_zaman_asimi_sn)
        return aktarim.al(adb, uzak_cikti, aktarim.cikti_yolu(foto), veri / "gecici")
    except Exception as h:
        if adb:
            log.error("Hata kaydı: %s", hata_kaydet(h, adb, veri / "hatalar"))
        raise
    finally:
        if adb:
            aktarim.temizle(adb, [y for y in (uzak_girdi, uzak_cikti) if y])
            try:
                adb.kabuk("am", "force-stop", PAKET)
            except Exception as h:
                log.warning("ToonMe kapatılamadı: %s", h)


def kullanici_mesaji(hata: Exception) -> str:
    if isinstance(hata, ADBKapali):
        return "BlueStacks'te ADB kapalı. Settings → Advanced → Android Debug Bridge (ADB) anahtarını açın."
    if isinstance(hata, BaslatmaZamanAsimi):
        return "BlueStacks 90 saniyede açılmadı."
    if isinstance(hata, DesteklenmeyenDosya):
        return "Bu dosya türü desteklenmiyor (jpg, png, webp)."
    if isinstance(hata, AkisHatasi):
        return f"ToonMe '{ADIM_ADLARI.get(hata.adim, hata.adim)}' adımında takıldı: {hata.ayrinti}"
    if isinstance(hata, AyarHatasi):
        return str(hata)
    if isinstance(hata, FileNotFoundError):
        return f"Dosya bulunamadı: {hata}"
    return "Beklenmeyen hata; ayrıntı kayit.log dosyasında."


def main(argv: list[str]) -> int:
    veri = veri_dizini()
    logging.basicConfig(filename=veri / "kayit.log", encoding="utf-8", level=logging.INFO,
                        format="%(asctime)s %(process)d %(levelname)s %(name)s: %(message)s")
    if argv == ["kur"]:
        kurulum.kur(kurulum.pythonw_yolu(), PROJE_DIZINI / "calistir.pyw", kurulum.SIMGE)
        print("Sağ tık menüsü eklendi: ToonMe karakter yap")
        return 0
    if argv == ["kaldir"]:
        kurulum.kaldir()
        print("Sağ tık menüsü kaldırıldı")
        return 0
    if not argv:
        print("Kullanım: python -m toonme_karakter <foto>... | kur | kaldir")
        return 2

    try:
        ayarlar = oku(PROJE_DIZINI / "ayarlar.json")
    except AyarHatasi as h:
        goster("ToonMe karakter yapılamadı", kullanici_mesaji(h))
        return 1

    hata_var = False
    for yol in map(Path, argv):
        goster("ToonMe", f"İşleniyor: {yol.name}")
        try:
            with kuyruk.sira(veri / "kuyruk.kilit"):
                log.info("Başladı: %s", yol)
                hedef = isle(yol, ayarlar)
            log.info("Bitti: %s -> %s", yol, hedef)
            goster("Karakter hazır", hedef.name, hedef)
        except Exception as h:
            hata_var = True
            log.exception("Başarısız: %s", yol)
            goster("ToonMe karakter yapılamadı", kullanici_mesaji(h))
    return 1 if hata_var else 0
