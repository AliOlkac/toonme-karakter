# ToonMe Sağ Tık Aracı — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Windows Gezgini'nde fotoğrafa sağ tık → "ToonMe karakter yap" → BlueStacks'teki ToonMe şablonu arka planda uygulanır, sonuç orijinalin yanına `<ad>_toon.jpg` olarak kaydedilir.

**Architecture:** Python paketi `toonme_karakter`. BlueStacks'in `HD-Adb.exe`'si ile ToonMe'yi şablon bağlantısından (`toonme.com/d/<id>`) açar ve arayüz öğelerini `uiautomator dump` XML'i üzerinden kimlik/metinle bulup dokunur. Saf parçalar (XML ayrıştırma, adlandırma, ayarlar) ADB'siz test edilir; cihaza bağlı parçalar `tests/sahte.py`'deki `SahteAdb` ile test edilir; en sonda gerçek BlueStacks'te uçtan uca denenir.

**Tech Stack:** Python 3.14 standart kütüphanesi (subprocess, xml.etree, winreg, msvcrt, logging), pytest 9.1.1, PowerShell (bildirim), BlueStacks 5.22 araçları.

**Spec:** `docs/superpowers/specs/2026-10-16-toonme-sag-tik-design.md`

## Global Constraints

- Çalışma zamanında üçüncü taraf Python paketi yok; pytest yalnızca test için (kurulu: 9.1.1).
- BlueStacks: `C:\Program Files\BlueStacks_nxt` (`HD-Player.exe`, `HD-Adb.exe`), conf `C:\ProgramData\BlueStacks_nxt\bluestacks.conf`, örnek `Pie64`.
- ToonMe paketi `com.vicman.toonmeapp`; varsayılan şablon `https://toonme.com/d/48671890`.
- Zaman sınırları: işleme 180 sn, BlueStacks açılışı 90 sn.
- Çıktı adı `<ad>_toon.jpg`, doluysa `<ad>_toon (2).jpg`, `(3)`…; asla üzerine yazılmaz.
- Emülatör girdi dizini `/sdcard/Pictures/ToonMeInput`, ToonMe çıktı dizini `/sdcard/Pictures/ToonMe`; MediaStore yolu `/storage/emulated/0/…`.
- Emülatör galerisine yardımcı dosya yazılmaz: döküm `/data/local/tmp/ui.xml`, ekran görüntüsü `adb exec-out screencap -p`.
- Öğeler `resource-id` / metin / `content-desc` ile bulunur; koordinat yalnızca bulunan öğenin `bounds` merkezinden hesaplanır.
- Emülatör temizliği (girdi + çıktı silme, `am force-stop`) her durumda `finally` içinde.
- Kayıtlar `%LOCALAPPDATA%\ToonMeKarakter\kayit.log`; hata başına `hatalar\<YYYYAAGG-SSDDss>\`.
- Sağ tık anahtarı `HKCU\Software\Classes\SystemFileAssociations\image\shell\ToonMeKarakter`, görünen ad "ToonMe karakter yap".
- Kullanıcıya görünen tüm metinler Türkçe.

## Review Focus

1. **Türkçe karakterli/boşluklu yol** (`…\Masaüstü\Çocuk fotoğrafı 1.jpg`): normal çalışmalı → Task 4 testi (ASCII geçici kopya üzerinden push/pull).
2. **Panodan gelen şablon URL'si** (`…/d/48671890?utm_source=app`): kabul edilmeli, sorgu kısmı atılmalı (yoksa `?`/`&` adb kabuğunda bozar) → Task 1 testi.
3. **iPhone HEIC veya başka desteklenmeyen dosya**: BlueStacks hiç başlatılmadan anlaşılır hata → Task 9 testi.
4. **Aynı anda çok fotoğraf**: sırayla işlenir, hiçbiri kaybolmaz → Task 7 testi + Task 10 senaryo 2.
5. **Dosya adında `&`, `<`, `"`**: bildirim XML'i bozulmamalı → Task 8 testi.

---

### Task 1: Proje iskeleti ve ayarlar

**Files:**
- Create: `.gitignore` (`__pycache__/`, `.pytest_cache/`, `*.pyc`), `pytest.ini` (`[pytest]` / `testpaths = tests`), `toonme_karakter/__init__.py` (boş), `toonme_karakter/ayarlar.py`, `ayarlar.json`, `tests/__init__.py` (boş)
- Test: `tests/test_ayarlar.py`

**Interfaces:**
- Produces:
  - `class AyarHatasi(Exception)`
  - `@dataclass(frozen=True) class Ayarlar` — `sablon_url: str = "https://toonme.com/d/48671890"`, `isleme_zaman_asimi_sn: int = 180`, `bluestacks_ornek: str = "Pie64"`, `bluestacks_dizini: Path = Path(r"C:\Program Files\BlueStacks_nxt")`, `bluestacks_conf: Path = Path(r"C:\ProgramData\BlueStacks_nxt\bluestacks.conf")`
  - `oku(yol: Path) -> Ayarlar`
  - `veri_dizini() -> Path` — `%LOCALAPPDATA%\ToonMeKarakter`, yoksa oluşturur
  - `PROJE_DIZINI: Path` — `Path(__file__).resolve().parent.parent`

- [ ] **Step 1: Depoyu başlat** — `git init`; `ayarlar.json` içeriği: `{"sablon_url": "https://toonme.com/d/48671890", "isleme_zaman_asimi_sn": 180, "bluestacks_ornek": "Pie64"}`

- [ ] **Step 2: Failing testleri yaz**

```python
def test_dosya_yoksa_varsayilanlar(tmp_path):
    assert oku(tmp_path / "yok.json") == Ayarlar()

def test_kismi_dosya_digerleri_varsayilan(tmp_path):
    (tmp_path / "a.json").write_text('{"isleme_zaman_asimi_sn": 60}', encoding="utf-8")
    a = oku(tmp_path / "a.json")
    assert a.isleme_zaman_asimi_sn == 60 and a.sablon_url == "https://toonme.com/d/48671890"

def test_bilinmeyen_anahtar_yok_sayilir(tmp_path): ...  # {"foo": 1} -> Ayarlar()

def test_url_sorgusu_atilir(tmp_path):  # Review Focus 2
    # {"sablon_url": "https://toonme.com/d/53865123?utm_source=app"}
    assert oku(p).sablon_url == "https://toonme.com/d/53865123"

def test_gecersiz_url_hata(tmp_path):
    # {"sablon_url": "https://example.com/x"} -> pytest.raises(AyarHatasi, match="sablon_url")

def test_bozuk_json_hata(tmp_path):
    # "{bozuk" -> pytest.raises(AyarHatasi, match="ayarlar.json")

def test_veri_dizini_localappdata(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert veri_dizini() == tmp_path / "ToonMeKarakter" and veri_dizini().is_dir()
```

- [ ] **Step 3: Çalıştır, FAIL gör** — `python -m pytest tests/test_ayarlar.py -v` → ImportError

- [ ] **Step 4: `ayarlar.py`'yi yaz** — URL doğrulaması `re.fullmatch(r"https://toonme\.com/d/\d+", url.split("?")[0])`; sayı alanı `int` değilse `AyarHatasi`.

- [ ] **Step 5: Çalıştır, PASS gör** — aynı komut → 7 passed

- [ ] **Step 6: Commit** — spec ve plan dahil: `git add -A && git commit -m "feat: proje iskeleti ve ayarlar"`

---

### Task 2: Ekran dökümü ayrıştırma (saf)

**Files:**
- Create: `toonme_karakter/ekran.py` (yalnızca saf kısım), `tests/fixtures/*.xml`
- Test: `tests/test_ekran_ayristirma.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class Oge` — `metin: str`, `kimlik: str` (`resource-id`'nin son `/` sonrası; yoksa `""`), `aciklama: str` (`content-desc`), `sinif: str`, `tiklanabilir: bool`, `sinirlar: tuple[int, int, int, int]`; `@property merkez -> tuple[int, int]` (tam sayı bölmeyle orta nokta)
  - `ayristir(xml: str) -> list[Oge]` — bozuk/boş XML → `[]`
  - `@dataclass(frozen=True) class Secici` — `metin: str | None = None`, `kimlik: str | None = None`, `aciklama: str | None = None`; `eslesir(oge: Oge) -> bool` (verilen tüm alanlar birebir eşit)
  - `bul(ogeler: list[Oge], secici: Secici) -> Oge | None` — ilk eşleşen
  - `gorunen_metinler(ogeler: list[Oge]) -> list[str]` — boş olmayan `metin`ler, sıra korunur, tekrarsız

- [ ] **Step 1: Gerçek dökümleri kopyala** — kaynak: inceleme sırasında BlueStacks'ten alınan dökümler (`snaps\`):
  `p1.xml→secici_recent.xml`, `dl1.xml→secici_recommended.xml`, `p2.xml→kirpma.xml`, `r1.xml→sonuc.xml`, `r2.xml→menu.xml`, `r3.xml→kaydet_paylas.xml`, `s4.xml→reklam.xml` (hedef `tests/fixtures/`).

- [ ] **Step 2: Failing testleri yaz** (`yukle(ad)` yardımcı: fixture'ı okuyup `ayristir`'dan geçirir)

```python
def test_sonuc_more(): o = bul(yukle("sonuc.xml"), Secici(kimlik="more")); assert o.tiklanabilir and o.merkez == (1552, 78)
def test_kirpma_next(): assert bul(yukle("kirpma.xml"), Secici(kimlik="next_btn")).merkez == (1534, 750)
def test_recent_ilk_foto():
    o = yukle("secici_recent.xml")
    assert bul(o, Secici(metin="Recent")) and bul(o, Secici(aciklama="list_item_2")).merkez == (332, 260)
def test_recommended_sekmesinde_all_var(): assert bul(yukle("secici_recommended.xml"), Secici(metin="All")).merkez == (75, 155)
def test_menu_save(): assert bul(yukle("menu.xml"), Secici(metin="Save to device"))
def test_kaydet_download(): assert bul(yukle("kaydet_paylas.xml"), Secici(metin="Download"))
def test_reklam_kapat(): assert bul(yukle("reklam.xml"), Secici(kimlik="close-or-skip-button")).merkez == (1557, 43)
def test_sonucta_progressbar_yok(): assert not any("ProgressBar" in o.sinif for o in yukle("sonuc.xml"))
def test_bozuk_xml_bos_liste(): assert ayristir("") == [] and ayristir("ERROR: could not get idle state.") == []
def test_gorunen_metinler_tekrarsiz(): assert gorunen_metinler(yukle("sonuc.xml"))[:1] == ["Result"]
```

- [ ] **Step 3: FAIL gör** — `python -m pytest tests/test_ekran_ayristirma.py -v`
- [ ] **Step 4: Saf kısmı yaz** — `xml.etree.ElementTree.fromstring`, `bounds` için `re.findall(r"\d+", …)`.
- [ ] **Step 5: PASS gör** — 10 passed
- [ ] **Step 6: Commit** — `git commit -m "feat: ekran dökümü ayrıştırma ve seçiciler"`

---

### Task 3: ADB sarmalayıcı, sahte ADB ve BlueStacks hazırlama

**Files:**
- Create: `toonme_karakter/adb.py`, `toonme_karakter/bluestacks.py`, `tests/sahte.py`
- Test: `tests/test_adb.py`, `tests/test_bluestacks.py`

**Interfaces:**
- Consumes: `Ayarlar` (Task 1)
- Produces:
  - `class AdbHatasi(Exception)`
  - `class Adb(exe: Path, seri: str, calistirici=subprocess.run)` — `komut(*arg: str, zaman_asimi: float = 30) -> str` (`[exe, "-s", seri, *arg]`; çıkış kodu ≠ 0 → `AdbHatasi(stderr)`; çıktı UTF-8 `errors="replace"`), `kabuk(*arg, zaman_asimi=30) -> str` (= `komut("shell", *arg)`), `gonder(yerel: Path, uzak: str) -> None`, `al(uzak: str, yerel: Path) -> None`, `ekran_goruntusu() -> bytes` (`exec-out screencap -p`, ikili)
  - `@dataclass(frozen=True) class ConfBilgisi(adb_acik: bool, adb_port: int)`
  - `conf_oku(metin: str, ornek: str) -> ConfBilgisi` — `bst.enable_adb_access="1"`; port önce `bst.instance.<ornek>.status.adb_port`, sonra `bst.instance.<ornek>.adb_port`, yoksa 5555
  - `class ADBKapali(Exception)`, `class BaslatmaZamanAsimi(Exception)`
  - `hazirla(ayarlar: Ayarlar, bekleme_sn: float = 90) -> Adb` — conf'ta ADB kapalıysa hiçbir şey başlatmadan `ADBKapali`; `HD-Player.exe` çalışmıyorsa (`tasklist /FI "IMAGENAME eq HD-Player.exe"`) `--instance <ornek>` ile ayrık başlat; 3 sn'de bir conf'u yeniden oku (port açılışta değişebilir), `adb connect 127.0.0.1:<port>` çıktısında `connected to` ve `getprop sys.boot_completed` = `1` olunca `Adb` döndür
  - `tests/sahte.py` → `class SahteAdb(yanitlar: dict[str, list[str]] | None = None, ekranlar: list[str] | None = None)`: `kabuk(*arg, zaman_asimi=30)` komutu boşlukla birleştirip `self.cagrilar: list[str]`'e ekler; `"uiautomator dump"` ile başlayan komutta `ekranlar`dan sıradakini döndürür (son eleman tekrarlanır); aksi halde komutun başladığı ilk `yanitlar` anahtarının listesinden sıradakini döndürür (son tekrarlanır; değer `AdbHatasi` örneğiyse fırlatır); eşleşme yoksa `""`. `gonder`/`al` çağrıları `"push <yerel> <uzak>"` / `"pull <uzak> <yerel>"` olarak kaydedilir; `al` hedefe `b"jpg"` yazar. `ekran_goruntusu()` → `b"png"`.

- [ ] **Step 1: Failing testleri yaz**

```python
def test_komut_seri_ile(): # sahte calistirici argümanları yakalar
    assert yakalanan == [r"C:\x\HD-Adb.exe", "-s", "127.0.0.1:5555", "shell", "getprop", "a"]
def test_komut_hata(): # returncode=1, stderr="device not found" -> pytest.raises(AdbHatasi, match="device not found")
def test_conf_status_portu_oncelikli():
    assert conf_oku('bst.enable_adb_access="1"\nbst.instance.Pie64.adb_port="5555"\nbst.instance.Pie64.status.adb_port="5565"', "Pie64") == ConfBilgisi(True, 5565)
def test_conf_yedek_port(): ...  # yalnız adb_port="5555" -> ConfBilgisi(True, 5555)
def test_conf_adb_kapali(): ...  # enable_adb_access="0" -> adb_acik is False
def test_conf_anahtar_yok(): assert conf_oku("", "Pie64") == ConfBilgisi(False, 5555)
def test_hazirla_adb_kapaliysa_baslatmaz(tmp_path, monkeypatch):
    # conf dosyası enable_adb_access="0"; subprocess.Popen'i patlayan sahteyle değiştir
    with pytest.raises(ADBKapali): hazirla(Ayarlar(bluestacks_conf=conf))
```

- [ ] **Step 2: FAIL gör** — `python -m pytest tests/test_adb.py tests/test_bluestacks.py -v`
- [ ] **Step 3: `adb.py`, `bluestacks.py`, `tests/sahte.py`'yi yaz**
- [ ] **Step 4: PASS gör**
- [ ] **Step 5: Gerçek cihaz kontrolü** — BlueStacks açıkken `python -c "from toonme_karakter.ayarlar import Ayarlar; from toonme_karakter.bluestacks import hazirla; print(hazirla(Ayarlar()).kabuk('getprop','ro.build.version.release'))"` → `9`
- [ ] **Step 6: Commit** — `git commit -m "feat: ADB sarmalayıcı ve BlueStacks hazırlama"`

---

### Task 4: Dosya aktarımı ve emülatör temizliği

**Files:**
- Create: `toonme_karakter/aktarim.py`
- Test: `tests/test_aktarim.py`

**Interfaces:**
- Consumes: `Adb`, `AdbHatasi`, `SahteAdb` (Task 3)
- Produces:
  - `GIRDI_DIZINI = "/sdcard/Pictures/ToonMeInput"`, `CIKTI_DIZINI = "/sdcard/Pictures/ToonMe"`, `DESTEKLENEN = {".jpg", ".jpeg", ".png", ".webp"}`
  - `class DesteklenmeyenDosya(Exception)`
  - `dogrula(yerel: Path) -> None` — yoksa `FileNotFoundError`; uzantı (küçük harf) `DESTEKLENEN`'de değilse `DesteklenmeyenDosya`
  - `cikti_yolu(girdi: Path) -> Path`
  - `medya_yolu(uzak: str) -> str` — `/sdcard/` → `/storage/emulated/0/`
  - `gonder(adb, yerel: Path, gecici_dizin: Path) -> str` — önce `gecici_dizin/<uuid>.<uzantı>` ASCII kopya, onu `GIRDI_DIZINI/toonme_<uuid hex><uzantı>`'ya push, `am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://<uzak>`, geçici kopyayı sil; uzak yolu döndür
  - `listele(adb, dizin: str) -> set[str]` — `ls -1 <dizin>` → tam yollar; `AdbHatasi` (dizin yok) → `set()`
  - `al(adb, uzak: str, hedef: Path, gecici_dizin: Path) -> Path` — geçici ASCII dosyaya pull, `shutil.move` ile hedefe
  - `temizle(adb, uzak_yollar: Iterable[str]) -> None` — her yol için `rm -f <yol>` ve `content delete --uri content://media/external/file --where "_data='<medya_yolu>'"` (tek kabuk dizesi olarak); `AdbHatasi`'nı kaydedip yutar

- [ ] **Step 1: Failing testleri yaz**

```python
def test_cikti_yolu_bos(tmp_path): assert cikti_yolu(tmp_path / "foto.jpg") == tmp_path / "foto_toon.jpg"
def test_cikti_yolu_doluysa_numara(tmp_path):
    (tmp_path / "foto_toon.jpg").touch(); (tmp_path / "foto_toon (2).jpg").touch()
    assert cikti_yolu(tmp_path / "foto.png") == tmp_path / "foto_toon (3).jpg"
def test_medya_yolu(): assert medya_yolu("/sdcard/Pictures/ToonMe/a.jpg") == "/storage/emulated/0/Pictures/ToonMe/a.jpg"
def test_dogrula_heic(tmp_path): (tmp_path/"a.HEIC").touch(); pytest.raises(DesteklenmeyenDosya, dogrula, tmp_path/"a.HEIC")
def test_gonder_turkce_yol(tmp_path):  # Review Focus 1
    f = tmp_path / "Masaüstü" / "Çocuk fotoğrafı 1.JPG"; f.parent.mkdir(); f.write_bytes(b"x")
    uzak = gonder(adb := SahteAdb(), f, tmp_path / "gecici")
    assert re.fullmatch(r"/sdcard/Pictures/ToonMeInput/toonme_[0-9a-f]{32}\.jpg", uzak)
    push = next(c for c in adb.cagrilar if c.startswith("push "))
    assert push.split(" ")[1].isascii()
    assert any("MEDIA_SCANNER_SCAN_FILE" in c and f"file://{uzak}" in c for c in adb.cagrilar)
def test_al_turkce_hedef(tmp_path):
    h = tmp_path / "Çocuk_toon.jpg"; al(SahteAdb(), "/sdcard/Pictures/ToonMe/x.jpg", h, tmp_path / "gecici")
    assert h.read_bytes() == b"jpg"
def test_listele(): assert listele(SahteAdb({"ls -1 /sdcard/Pictures/ToonMe": ["a.jpg\nb.jpg\n"]}), CIKTI_DIZINI) == {f"{CIKTI_DIZINI}/a.jpg", f"{CIKTI_DIZINI}/b.jpg"}
def test_listele_dizin_yok(): assert listele(SahteAdb({"ls": [AdbHatasi("No such file")]}), CIKTI_DIZINI) == set()
def test_temizle_medya_kaydi(): ...  # cagrilar'da "rm -f /sdcard/…/a.jpg" ve "_data='/storage/emulated/0/…/a.jpg'"
def test_temizle_hata_yutar(): temizle(SahteAdb({"rm": [AdbHatasi("x")]}), ["/sdcard/a.jpg"])  # fırlatmaz
```

- [ ] **Step 2: FAIL gör** — `python -m pytest tests/test_aktarim.py -v`
- [ ] **Step 3: `aktarim.py`'yi yaz**
- [ ] **Step 4: PASS gör**
- [ ] **Step 5: Commit** — `git commit -m "feat: dosya aktarımı ve emülatör temizliği"`

---

### Task 5: Ekran — cihaz üzerinde bekleme ve engel kapatma

**Files:**
- Modify: `toonme_karakter/ekran.py` (Task 2'nin altına ekle)
- Test: `tests/test_ekran_bekle.py`

**Interfaces:**
- Consumes: `Oge`, `Secici`, `bul`, `ayristir` (Task 2); `SahteAdb` (Task 3)
- Produces:
  - `KAPATICILAR = (Secici(kimlik="close-or-skip-button"), Secici(metin="Not now"), Secici(metin="No thanks"), Secici(metin="Skip"), Secici(metin="Close"))`
  - `class EkranZamanAsimi(Exception)` — öznitelikler `aranan: Secici`, `son_ogeler: list[Oge]`
  - `odak_ayristir(dumpsys: str) -> str` — `mCurrentFocus=Window{… u0 <paket/aktivite>}` → `"<paket/aktivite>"`, yoksa `""`
  - `class Ekran(adb, uyku=time.sleep, saat=time.monotonic)`:
    - `dok() -> list[Oge]` — tek kabuk çağrısı: `uiautomator dump /data/local/tmp/ui.xml >/dev/null && cat /data/local/tmp/ui.xml`
    - `odak() -> str` — `dumpsys window windows` → `odak_ayristir`
    - `dokun(oge: Oge) -> None` — `input tap x y`; `geri() -> None` — `input keyevent 4`
    - `bekle(secici: Secici, zaman_asimi: float, *, kosul: Callable[[list[Oge]], bool] | None = None, beklenen_paket: str | None = None, aralik: float = 1.0) -> Oge` — her turda `dok()`; `kosul` verilmişse **her turda** çağrılır (fırlatabilir); hedef bulundu ve `kosul` doğruysa döner. Bulunamadıysa engel turu (bekle başına en çok 3): `KAPATICILAR`'dan biri varsa ona dokun; yoksa `beklenen_paket` verilmiş ve `odak()` `beklenen_paket + "/"` ile başlamıyorsa `geri()`. Süre dolunca `EkranZamanAsimi`.

- [ ] **Step 1: Failing testleri yaz** (sahte saat: `uyku` çağrıldıkça `saat` ilerler)

```python
def test_hemen_bulur(): assert e(ekranlar=[F("sonuc.xml")]).bekle(Secici(kimlik="more"), 5).merkez == (1552, 78)
def test_reklami_kapatip_bulur():
    adb = SahteAdb(ekranlar=[F("reklam.xml"), F("sonuc.xml")]); Ekran(adb, ...).bekle(Secici(kimlik="more"), 10)
    assert "input tap 1557 43" in adb.cagrilar
def test_yabanci_pakette_geri():
    adb = SahteAdb({"dumpsys window": ["  mCurrentFocus=Window{1 u0 com.baska/X}"]}, ekranlar=["<hierarchy/>", F("sonuc.xml")])
    Ekran(adb, ...).bekle(Secici(kimlik="more"), 10, beklenen_paket="com.vicman.toonmeapp")
    assert "input keyevent 4" in adb.cagrilar
def test_en_fazla_uc_engel():
    adb = SahteAdb(ekranlar=[F("reklam.xml")])
    with pytest.raises(EkranZamanAsimi): Ekran(adb, ...).bekle(Secici(kimlik="more"), 20)
    assert adb.cagrilar.count("input tap 1557 43") == 3
def test_zaman_asimi_son_ogeler():
    with pytest.raises(EkranZamanAsimi) as h: e(ekranlar=[F("kirpma.xml")]).bekle(Secici(kimlik="more"), 5)
    assert bul(h.value.son_ogeler, Secici(kimlik="next_btn"))
def test_kosul_her_turda(): ...  # kosul ilk çağrıda False, ikincide True -> iki dök sonra döner
def test_odak_ayristir():
    assert odak_ayristir("  mCurrentFocus=Window{2213f51 u0 com.vicman.toonmeapp/com.vicman.photolab.activities.NewPhotoChooserActivity}") == "com.vicman.toonmeapp/com.vicman.photolab.activities.NewPhotoChooserActivity"
```

- [ ] **Step 2: FAIL gör** — `python -m pytest tests/test_ekran_bekle.py -v`
- [ ] **Step 3: `Ekran`'ı yaz**
- [ ] **Step 4: PASS gör** — Task 2 testleri de geçmeli: `python -m pytest tests/test_ekran_*.py -v`
- [ ] **Step 5: Commit** — `git commit -m "feat: ekranda bekleme ve açılır pencere kapatma"`

---

### Task 6: ToonMe akışı ve yeniden deneme

**Files:**
- Create: `toonme_karakter/toonme_akis.py`
- Test: `tests/test_toonme_akis.py`

**Interfaces:**
- Consumes: `Ekran`, `Secici`, `bul`, `gorunen_metinler`, `EkranZamanAsimi` (Task 2, 5); `listele`, `CIKTI_DIZINI` (Task 4)
- Produces:
  - `PAKET = "com.vicman.toonmeapp"`
  - `class AkisHatasi(Exception)` — öznitelikler `adim: str`, `ayrinti: str`, `son_ogeler: list[Oge]`; `str()` → `"<adim>: <ayrinti>"`
  - Adım adları: `"sablon"`, `"fotograf"`, `"kirpma"`, `"isleme"`, `"kaydetme"`, `"cikti"`, `"toonme_hatasi"`
  - `calistir(ekran: Ekran, adb, sablon_url: str, isleme_zaman_asimi: float) -> str` — ToonMe çıktısının uzak yolu
  - `calistir_tekrarli(ekran, adb, sablon_url, isleme_zaman_asimi, deneme: int = 2) -> str` — `AkisHatasi`'da (adım `"toonme_hatasi"` hariç) `am force-stop com.vicman.toonmeapp` ve baştan dener

Akış (spec §3 adım 3–8; her `EkranZamanAsimi` → `AkisHatasi(adim, f"{secici} bulunamadı; ekranda: {gorunen_metinler(son)[:8]}", son)`):

| adım | işlem | bekleme |
|---|---|---|
| — | `once = listele(adb, CIKTI_DIZINI)` | — |
| sablon | `am start -W -a android.intent.action.VIEW -d <url> com.vicman.toonmeapp`; `bekle(Secici(aciklama="list_item_0"), 30, beklenen_paket=PAKET)` | 30 sn |
| fotograf | aynı ögelerde `Recent` varsa ona, yoksa `All`'a dokun; `bekle(Secici(aciklama="list_item_2"), 15)` → dokun | 15 sn |
| kirpma | `bekle(Secici(kimlik="next_btn"), 20)` → dokun | 20 sn |
| isleme | `bekle(Secici(kimlik="more"), isleme_zaman_asimi, kosul=_isleme_bitti, beklenen_paket=PAKET)` → dokun | 180 sn |
| kaydetme | `bekle(Secici(metin="Save to device"), 10)` → dokun; `bekle(Secici(metin="Download"), 15)` → dokun | 10+15 sn |
| cikti | 1 sn arayla `listele` (en çok 20 sn); `sonra - once` içindeki `.jpg`'lerin sıralı sonuncusu | 20 sn |

`_isleme_bitti(ogeler) -> bool`: kimliği `snackbar_text` veya `message` olan öğe varsa `AkisHatasi("toonme_hatasi", <o öğenin metni>, ogeler)` fırlatır; sınıfında `ProgressBar` geçen öğe yoksa `True`.

- [ ] **Step 1: Failing testleri yaz**

```python
MUTLU = [F("secici_recent.xml"), F("secici_recent.xml"), F("kirpma.xml"), F("sonuc.xml"), F("menu.xml"), F("kaydet_paylas.xml")]
def test_mutlu_yol():
    adb = SahteAdb({"ls -1 /sdcard/Pictures/ToonMe": ["", "f39d.jpg\n"]}, ekranlar=MUTLU)
    assert calistir(Ekran(adb, ...), adb, "https://toonme.com/d/48671890", 180) == "/sdcard/Pictures/ToonMe/f39d.jpg"
    dokunuslar = [c for c in adb.cagrilar if c.startswith("input tap")]
    assert dokunuslar[1:4] == ["input tap 332 260", "input tap 1534 750", "input tap 1552 78"]
    assert any(c.startswith("am start") and "https://toonme.com/d/48671890" in c for c in adb.cagrilar)
def test_web_secicide_all_sekmesi():  # ekranlar=[secici_recommended] + MUTLU[1:] -> sonuç döner ve "input tap 75 155" cagrilar'da
def test_kirpma_zaman_asimi_adim_adi():  # ekranlar=[secici_recent]*… -> AkisHatasi.adim == "kirpma"
def test_isleme_progressbar_varken_beklenir():  # sonuc.xml'e ProgressBar düğümü eklenmiş sentetik ekran önce gelir; "more"ye ancak sonra dokunulur
def test_toonme_hatasi_tekrar_yok():
    hata = '<hierarchy><node text="No faces found" resource-id="com.vicman.toonmeapp:id/snackbar_text" class="android.widget.TextView" content-desc="" clickable="false" bounds="[0,0][10,10]"/></hierarchy>'
    # ekranlar=[recent, recent, kirpma, hata] -> calistir_tekrarli AkisHatasi(adim="toonme_hatasi", "No faces found" in ayrinti); "am start" sadece 1 kez
def test_tekrarli_bir_kez_yeniden_dener():  # ilk deneme kirpmada düşer, ikincisi MUTLU -> sonuç döner; "am force-stop com.vicman.toonmeapp" 1 kez, "am start" 2 kez
```

- [ ] **Step 2: FAIL gör** — `python -m pytest tests/test_toonme_akis.py -v`
- [ ] **Step 3: `toonme_akis.py`'yi yaz**
- [ ] **Step 4: PASS gör** — `python -m pytest -v` (tüm testler)
- [ ] **Step 5: Commit** — `git commit -m "feat: ToonMe akışı ve yeniden deneme"`

---

### Task 7: İş kuyruğu

**Files:**
- Create: `toonme_karakter/kuyruk.py`
- Test: `tests/test_kuyruk.py`

**Interfaces:**
- Produces: `@contextmanager sira(kilit_yolu: Path, aralik: float = 0.5) -> Iterator[None]` — dosyayı `"a+b"` açar, `msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)` `OSError` verdikçe `aralik` uyuyup yeniden dener; `finally`'de `LK_UNLCK` ve kapatır. (Windows bayt kilitleri tanıtıcı başınadır; aynı süreçteki iki iş parçacığı da birbirini bekler.)

- [ ] **Step 1: Failing testleri yaz**

```python
def test_ikinci_ilki_bitince_girer(tmp_path):  # Review Focus 4
    # A iş parçacığı sira() içinde 0.5 sn bekler; B 0.1 sn sonra sira()'ya girer
    assert sira_kaydi == ["A-gir", "A-cik", "B-gir", "B-cik"]
def test_hata_olunca_kilit_birakilir(tmp_path):
    with pytest.raises(ValueError):
        with sira(k): raise ValueError
    with sira(k, aralik=0.01): pass  # takılmadan girer
```

- [ ] **Step 2: FAIL gör** — `python -m pytest tests/test_kuyruk.py -v`
- [ ] **Step 3: `kuyruk.py`'yi yaz**
- [ ] **Step 4: PASS gör**
- [ ] **Step 5: Commit** — `git commit -m "feat: dosya kilidiyle iş kuyruğu"`

---

### Task 8: Windows bildirimi ve sağ tık menüsü

**Files:**
- Create: `toonme_karakter/bildirim.py`, `toonme_karakter/kurulum.py`
- Test: `tests/test_bildirim.py`, `tests/test_kurulum.py`

**Interfaces:**
- Produces:
  - `POWERSHELL_AUMID = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"`
  - `toast_xml(baslik: str, metin: str, acilacak: Path | None = None) -> str` — `<toast>` + `ToastGeneric` bağlamalı iki `<text>`; `acilacak` verilirse `<toast activationType="protocol" launch="<acilacak.as_uri()>">`; metinler `xml.sax.saxutils.escape`, öznitelik `quoteattr`
  - `goster(baslik: str, metin: str, acilacak: Path | None = None) -> None` — `powershell -NoProfile -WindowStyle Hidden -EncodedCommand <base64 UTF-16LE>`; betik `Windows.Data.Xml.Dom.XmlDocument`'e XML'i yükler, `ToastNotificationManager::CreateToastNotifier(POWERSHELL_AUMID).Show(...)`; hata kaydedilip yutulur
  - `ANAHTAR = r"Software\Classes\SystemFileAssociations\image\shell\ToonMeKarakter"`
  - `komut_satiri(pythonw: Path, betik: Path) -> str` → `'"<pythonw>" "<betik>" "%1"'`
  - `pythonw_yolu() -> Path` → `Path(sys.executable).with_name("pythonw.exe")`
  - `SIMGE = Path(os.environ["ALLUSERSPROFILE"]) / r"BlueStacks_nxt\Engine\Pie64\AppCache\com.vicman.toonmeapp.ico"`
  - `kur(pythonw: Path, betik: Path, simge: Path, anahtar: str = ANAHTAR) -> None` — HKCU'da `MUIVerb="ToonMe karakter yap"`, `Icon=str(simge)`, alt anahtar `command` varsayılan değeri `komut_satiri(...)`
  - `kaldir(anahtar: str = ANAHTAR) -> None` — önce `command`, sonra anahtar; yoksa sessizce geçer

- [ ] **Step 1: Failing testleri yaz**

```python
def test_toast_kacis():  # Review Focus 5
    x = toast_xml("Karakter hazır", 'Çocuk & <1> "a".jpg', Path(r"C:\Kullanıcı\a b.jpg"))
    ET.fromstring(x)  # geçerli XML
    assert "Çocuk &amp; &lt;1&gt;" in x and 'launch="file:///C:/Kullan%C4%B1c%C4%B1/a%20b.jpg"' in x
def test_toast_acilacak_yoksa_launch_yok(): assert "launch=" not in toast_xml("a", "b")
def test_komut_satiri(): assert komut_satiri(Path(r"C:\P y\pythonw.exe"), Path(r"C:\x\calistir.pyw")) == r'"C:\P y\pythonw.exe" "C:\x\calistir.pyw" "%1"'
TEST_ANAHTAR = r"Software\ToonMeKarakterTest\shell\ToonMeKarakter"
def test_kur_kaldir():
    kur(Path("C:/p/pythonw.exe"), Path("C:/x/calistir.pyw"), Path("C:/s.ico"), TEST_ANAHTAR)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, TEST_ANAHTAR) as k: assert winreg.QueryValueEx(k, "MUIVerb")[0] == "ToonMe karakter yap"
    kaldir(TEST_ANAHTAR); kaldir(TEST_ANAHTAR)  # ikinci çağrı hata vermez
    pytest.raises(FileNotFoundError, winreg.OpenKey, winreg.HKEY_CURRENT_USER, TEST_ANAHTAR)
    # teardown: Software\ToonMeKarakterTest ağacını sil
```

- [ ] **Step 2: FAIL gör** — `python -m pytest tests/test_bildirim.py tests/test_kurulum.py -v`
- [ ] **Step 3: İki modülü yaz**
- [ ] **Step 4: PASS gör**
- [ ] **Step 5: Gerçek bildirim** — `python -c "from toonme_karakter.bildirim import goster; goster('Deneme','ToonMe bildirimi')"` → çıkış kodu 0; kullanıcıdan ekranda bildirimi gördüğünü teyit etmesini iste
- [ ] **Step 6: Commit** — `git commit -m "feat: Windows bildirimi ve sağ tık menüsü"`

---

### Task 9: Uygulama düzenleyici ve giriş noktaları

**Files:**
- Create: `toonme_karakter/uygulama.py`, `toonme_karakter/__main__.py`, `calistir.pyw`
- Test: `tests/test_uygulama.py`

**Interfaces:**
- Consumes: Task 1–8'deki tüm arayüzler
- Produces:
  - `isle(foto: Path, ayarlar: Ayarlar, *, hazirla=bluestacks.hazirla, akis=toonme_akis.calistir_tekrarli, veri: Path | None = None) -> Path` — sıra: `aktarim.dogrula(foto)` (BlueStacks'ten önce) → `adb = hazirla(ayarlar)` → `uzak_girdi = aktarim.gonder(adb, foto, veri/"gecici")` → `uzak_cikti = akis(Ekran(adb), adb, ayarlar.sablon_url, ayarlar.isleme_zaman_asimi_sn)` → `aktarim.al(adb, uzak_cikti, aktarim.cikti_yolu(foto), veri/"gecici")`. `except`: `adb` varsa `hata_kaydet(hata, adb, veri/"hatalar")`, yeniden fırlat. `finally`: `aktarim.temizle(adb, [girdi, çıktı (varsa)])` ve `am force-stop com.vicman.toonmeapp` (hatalar yutulur). `veri` verilmezse `veri_dizini()` (modülü `from .ayarlar import Ayarlar, veri_dizini, PROJE_DIZINI` ile al; `ayarlar` adı parametreye ait).
  - `hata_kaydet(hata: Exception, adb, dizin: Path) -> Path` — `dizin/<YYYYAAGG-SSDDss>/` içine `hata.txt` (traceback), `ekran.png` (`adb.ekran_goruntusu()`), `ui.xml` (`uiautomator dump … && cat …` çıktısı); kendi hataları yutulur
  - `ADIM_ADLARI = {"sablon": "şablonu açma", "fotograf": "fotoğraf seçme", "kirpma": "kırpma", "isleme": "işleme", "kaydetme": "kaydetme", "cikti": "sonucu bulma", "toonme_hatasi": "ToonMe"}`
  - `kullanici_mesaji(hata: Exception) -> str` — `ADBKapali` → `"BlueStacks'te ADB kapalı. Settings → Advanced → Android Debug Bridge (ADB) anahtarını açın."`; `BaslatmaZamanAsimi` → `"BlueStacks 90 saniyede açılmadı."`; `DesteklenmeyenDosya` → `"Bu dosya türü desteklenmiyor (jpg, png, webp)."`; `AkisHatasi` → `f"ToonMe '{ADIM_ADLARI[adim]}' adımında takıldı: {ayrinti}"`; `AyarHatasi` → `str(hata)`; diğer → `"Beklenmeyen hata; ayrıntı kayit.log dosyasında."`
  - `main(argv: list[str]) -> int` — `logging` → `veri_dizini()/"kayit.log"`; `argv == ["kur"]` → `kurulum.kur(pythonw_yolu(), PROJE_DIZINI/"calistir.pyw", SIMGE)`, `["kaldir"]` → `kurulum.kaldir()`; aksi halde her yol için `goster("ToonMe", f"İşleniyor: {ad}")`, `with kuyruk.sira(veri_dizini()/"kuyruk.kilit"): hedef = isle(...)`, başarıda `goster("Karakter hazır", hedef.name, hedef)`, hatada `goster("ToonMe karakter yapılamadı", kullanici_mesaji(h))`; bir hata bile varsa `1`, yoksa `0`. Ayarlar `PROJE_DIZINI/"ayarlar.json"`'dan.
  - `__main__.py`: `raise SystemExit(main(sys.argv[1:]))`; `calistir.pyw`: proje dizinini `sys.path`'e ekler, aynısını yapar

- [ ] **Step 1: Failing testleri yaz**

```python
def test_desteklenmeyen_dosyada_bluestacks_acilmaz(tmp_path):  # Review Focus 3
    (f := tmp_path / "a.heic").touch()
    with pytest.raises(DesteklenmeyenDosya): isle(f, Ayarlar(), hazirla=patlayan, veri=tmp_path)
def test_basarili_is(tmp_path):
    (f := tmp_path / "foto.jpg").write_bytes(b"x"); adb = SahteAdb()
    hedef = isle(f, Ayarlar(), hazirla=lambda a: adb, akis=lambda *a: "/sdcard/Pictures/ToonMe/c.jpg", veri=tmp_path / "v")
    assert hedef == tmp_path / "foto_toon.jpg" and hedef.exists()
    assert any("rm -f /sdcard/Pictures/ToonMeInput/" in c for c in adb.cagrilar)
    assert "rm -f /sdcard/Pictures/ToonMe/c.jpg" in " ".join(adb.cagrilar)
    assert "am force-stop com.vicman.toonmeapp" in adb.cagrilar
def test_hatada_kayit_ve_temizlik(tmp_path):
    # akis AkisHatasi("kirpma", ...) fırlatır -> isle yeniden fırlatır; v/hatalar/*/hata.txt ve ekran.png var; girdi rm edildi
def test_mesaj_adb_kapali(): assert "ADB kapalı" in kullanici_mesaji(ADBKapali())
def test_mesaj_akis(): assert kullanici_mesaji(AkisHatasi("isleme", "zaman aşımı", [])) == "ToonMe 'işleme' adımında takıldı: zaman aşımı"
```

- [ ] **Step 2: FAIL gör** — `python -m pytest tests/test_uygulama.py -v`
- [ ] **Step 3: Üç dosyayı yaz**
- [ ] **Step 4: PASS gör** — `python -m pytest -v` (tüm testler)
- [ ] **Step 5: Commit** — `git commit -m "feat: uygulama düzenleyici, CLI ve sağ tık giriş noktası"`

---

### Task 10: Gerçek BlueStacks'te uçtan uca test ve README

**Files:**
- Create: `README.md`
- Modify: gözleme göre `toonme_karakter/toonme_akis.py` (`_isleme_bitti`, sekme seçimi), `toonme_karakter/ekran.py` (`KAPATICILAR`)

Test fotoğrafı: yerel bir test fotoğrafı (yalnızca bu testler için; depoya girmez).

- [ ] **Step 1: Senaryo 1, BlueStacks açıkken** — `Measure-Command { python -m toonme_karakter "<test1.jpg>" }` → çıkış kodu 0; yanında `test1_toon.jpg` (960×1288 civarı) oluşur; sonucu aç ve test fotoğrafındaki kişinin karakteri olduğunu doğrula (spec §7.2: yanlış fotoğraf seçilmediği; emülatörde `DCIM/SharedFolder/foto_4.jpg` var). Yanlış fotoğraf seçildiyse **dur ve kullanıcıya bildir**: spec'teki yedek yol (galeri düğmesi → sistem seçicisi) ayrı bir tasarım kararı gerektirir. Süreyi not et.
- [ ] **Step 2: Emülatör temiz mi** — `HD-Adb.exe -s 127.0.0.1:5555 shell content query --uri content://media/external/images/media --projection _data` → `ToonMeInput` kaydı yok, yeni ToonMe çıktısı yok.
- [ ] **Step 3: İşleme bitiş işareti (spec §7.1)** — işleme sırasında `ekran.dok()` ile döküm alan kısa bir betikle işlemenin ilerleme göstergesini doğrula. `ProgressBar` görünmüyorsa veya kaydetme erken tetikleniyorsa `_isleme_bitti`'yi gözlenen işarete göre düzelt, Task 6'ya o dökümle bir test ekle.
- [ ] **Step 4: Senaryo 2, aynı anda 3 fotoğraf** — `test1.jpg`'yi `a.jpg`, `b.jpg`, `c.jpg` olarak kopyala; üçünü `Start-Process pythonw calistir.pyw <dosya>` ile aynı anda başlat → üç `_toon.jpg` oluşur, `kayit.log`'da işler sıralı.
- [ ] **Step 5: Senaryo 3, BlueStacks kapalıyken** — kullanıcıya BlueStacks'i kapatacağını söyleyip onay al, kapat, Senaryo 1'i tekrarla → çalışır; toplam süreyi not et.
- [ ] **Step 6: Sağ tık menüsü** — `python -m toonme_karakter kur`; kullanıcıdan Gezgini'nde bir fotoğrafa sağ tık → "Diğer seçenekleri göster" → "ToonMe karakter yap" ile denemesini iste.
- [ ] **Step 7: README.md yaz** — kurulum (`python -m toonme_karakter kur` / `kaldir`), ADB ayarı, kullanım, şablon değiştirme (ToonMe → şablon → paylaş → Copy URL → `ayarlar.json`), ölçülen süreler, sorun giderme (`%LOCALAPPDATA%\ToonMeKarakter\kayit.log`, `hatalar\`), Windows'un 15'ten fazla dosya seçiminde menüyü gizlediği notu.
- [ ] **Step 8: Tüm testler + commit** — `python -m pytest -v` → hepsi PASS; `git commit -am "docs: README ve uçtan uca doğrulama düzeltmeleri"`
