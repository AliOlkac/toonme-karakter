# ToonMe Sağ Tık Aracı — Tasarım

Tarih: 2026-10-16 · Durum: Onaylandı, uygulandı (gerçek cihaz bulgularıyla güncellendi)

## 1. Amaç

Kullanıcı ToonMe'nin "Toon Mirror" kategorisindeki bir şablonla (Алина П., kimlik `48671890`) fotoğrafları
3D animasyon karakterine çeviriyor. Bunun için her seferinde BlueStacks'i açıp menülerde şablonu bulmaktan yorulmuş.

**Hedef:** Windows Gezgini'nde bir veya birden çok fotoğrafa sağ tık → **"ToonMe karakter yap"** → sonuç,
ToonMe'ye hiç dokunmadan orijinalin yanına `<ad>_toon.jpg` olarak kaydedilir.

**Başarı ölçütleri**
- Tek fotoğraf, BlueStacks açıkken: kullanıcı yalnızca sağ tıklar; sonuç dosyası oluşur ve bildirim gelir.
- BlueStacks kapalıyken: araç kendisi başlatır, ek bir şey istemez.
- Aynı anda birden çok fotoğraf: hepsi sırayla işlenir, hiçbiri kaybolmaz veya karışmaz.
- Sonuç, ToonMe'de elle yapılan işlemle aynıdır (aynı şablon, aynı çözünürlük, filigransız).
- Hata olursa kullanıcı bildirimden neyin takıldığını öğrenir; teşhis için ekran görüntüsü saklanır.

**Kapsam dışı (YAGNI):** klasör izleme, şablon seçme arayüzü, API tabanlı ikinci motor, video, Windows dışı sistemler.

## 2. Doğrulanmış ortam bilgileri

| Konu | Değer |
|---|---|
| BlueStacks | 5.22.262 (`C:\Program Files\BlueStacks_nxt`), örnek `Pie64`, Android 9, ekran 1600×900 yatay |
| Başlatma | `HD-Player.exe --instance Pie64` (+ `--cmd launchApp --package com.vicman.toonmeapp` isteğe bağlı) |
| ADB | BlueStacks'in kendi `HD-Adb.exe`'si; port `C:\ProgramData\BlueStacks_nxt\bluestacks.conf` içindeki `bst.instance.Pie64.status.adb_port` (şu an 5555); ADB ayarı `bst.enable_adb_access="1"` olmalı |
| Soğuk başlangıç | BlueStacks kapalıyken `sys.boot_completed=1` olana kadar ~24 sn |
| ToonMe | `com.vicman.toonmeapp` 0.7.26, dışarıdan yüklenmiş; Play Store'dan gelmediği için kendiliğinden güncellenmez (arayüz kimlikleri sabit kalır) |
| Root | Yok; yalnızca `shell` kullanıcısı |

## 3. Akış (gerçek uygulamada test edildi)

| # | Adım | Nasıl | Beklenen ekran / öğe |
|---|---|---|---|
| 1 | Hazırlık | BlueStacks süreci yoksa başlat; `adb connect`; `getprop sys.boot_completed` = 1 bekle | — |
| 2 | Fotoğrafı gönder | `adb push` → `/sdcard/Pictures/ToonMeInput/<benzersiz>.jpg`; `am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://…`; MediaStore kaydı oluşunca `datetaken` = max(şimdi, galerideki en büyük + 1) | — |
| 3 | Şablonu aç | `am force-stop` (temiz süreç) + `am start -W -a android.intent.action.VIEW -d https://toonme.com/d/<şablon_kimliği> com.vicman.toonmeapp`; odak `…PhotoChooserActivity` olana kadar bekle | `NewPhotoChooserActivity` veya `WebPhotoChooserActivity` (şablona göre değişiyor) |
| 4 | Fotoğrafı seç | Metni `All` olan sekme seçili değilse ona dokun (seçilene kadar yinele; seçiliyken dokunmak albüm menüsünü açar); `All` seçiliyken `list_item_2` (kamera ve galeri düğmelerinden sonraki ilk fotoğraf) | `CropNRotateActivity` |
| 5 | Kırpmayı geç | `resource-id …/next_btn` (desc "Edit photo"); varsayılan kırpma fotoğrafın tamamı | `ResultActivity` |
| 6 | Sonucu bekle | İşleme `ResultActivity` içinde yapılır; ilerleme göstergesi kaybolana ve `…/more` tıklanabilir olana kadar bekle (en çok 3 dk) | Sonuç görseli |
| 7 | Kaydet | `…/more` → metni `Save to device` → `ShareActivity` ("Save & Share") → metni `Download` | — |
| 8 | Çıktıyı bul | `Pictures/ToonMe/` klasörünün işlem öncesi/sonrası listesi karşılaştırılır; yeni `.jpg` sonuçtur (test: 960×1288) | — |
| 9 | Bilgisayara al | `adb pull` → orijinalin yanına `<ad>_toon.jpg`; varsa `<ad>_toon (2).jpg` … (üzerine yazmaz) | — |
| 10 | Temizlik | `finally` içinde: bilinen girdi/çıktı + `ToonMeInput` klasörünün tamamı + `ToonMe` klasöründe iş başındaki işaret dosyasından (`/data/local/tmp/toonme_is.isaret`) yeni olanlar silinir, MediaStore kaydı kaldırılır (`content delete --uri content://media/external/file --where "_data='/storage/emulated/0/…'"`); `am force-stop com.vicman.toonmeapp` | — |

Notlar:
- Öğeler koordinatla değil `resource-id` / metin / `content-desc` ile bulunur. Koordinat yalnızca bulunan öğenin
  `bounds` merkezinden hesaplanır.
- Ekran dökümü `/data/local/tmp/ui.xml`'e (her dökümden önce eski dosya silinerek), ekran görüntüsü `adb exec-out screencap -p`
  ile alınır; böylece emülatör galerisine hiçbir yardımcı dosya düşmez ve başarısız döküm eski ekran sanılmaz.
- "Recent" sekmesi galeri değil, ToonMe'nin kendi geçmişidir (eski/silinmiş fotoğrafları gösterir). Galeriyi `All` gösterir ve
  **çekim tarihine (datetaken)** göre sıralar; bu yüzden adım 2'de bizim fotoğrafın çekim tarihi en yeni yapılır.
- Hareketli Ana Sayfa (`uiautomator dump` → "could not get idle state") bağlantı sayesinde hiç açılmaz.

## 4. Bileşenler

Tek Python paketi, **üçüncü taraf bağımlılığı yok** (Python 3.14 standart kütüphanesi + BlueStacks araçları).

```
toonme-karakter/
  toonme_karakter/
    __main__.py      # CLI: `<foto>...` işle | `kur` | `kaldir`
    ayarlar.py       # ayarlar.json (şablon URL'si, zaman aşımları) + varsayılanlar
    adb.py           # HD-Adb.exe sarmalayıcısı; tüm ADB çağrıları buradan geçer
    bluestacks.py    # süreç kontrolü, başlatma, port okuma, açılışı bekleme
    ekran.py         # UI dökümünü ayrıştırma, öğe bulma, dokunma, koşul bekleme, beklenmedik pencere kapatma
    toonme_akis.py   # §3'teki 3–8. adımlar
    aktarim.py       # push/pull, medya taraması ve temizliği, çıktı dosya adı üretimi
    kuyruk.py        # dosya kilidiyle (msvcrt) aynı anda tek iş
    bildirim.py      # Windows bildirimi (PowerShell + Windows.UI.Notifications); tıklayınca sonucu açar
    kurulum.py       # sağ tık menüsünü ekler/kaldırır
  calistir.pyw       # sağ tıktan çağrılan giriş noktası (konsol penceresi açmaz)
  ayarlar.json
  tests/
```

Sorumluluk sınırları:
- `toonme_akis` yalnızca `ekran` ve `adb` arayüzlerini kullanır; dosya sistemi ve Windows'u bilmez.
- `ekran` saf ayrıştırma işlevleri (XML → öğe listesi, seçiciyle eşleme) ve ADB'ye bağlı işlevler olarak ikiye ayrılır;
  saf kısım ADB olmadan test edilir.
- `__main__` işi şöyle düzenler: kuyruk kilidi → bluestacks hazırla → aktarim gönder → akış → aktarim al/temizle → bildirim.

**Sağ tık menüsü:** `HKCU\Software\Classes\SystemFileAssociations\image\shell\ToonMeKarakter` (yönetici gerekmez).
Görünen ad "ToonMe karakter yap", simge `%ALLUSERSPROFILE%\BlueStacks_nxt\Engine\Pie64\AppCache\com.vicman.toonmeapp.ico`,
komut `"<pythonw.exe>" "<proje>\calistir.pyw" "%1"`. Windows çoklu seçimde dosya başına bir süreç başlatır;
`kuyruk` bunları sıraya koyar. Windows 11'de "Diğer seçenekleri göster" altında görünür.

**Ayarlar (`ayarlar.json`):** `sablon_url` (varsayılan `https://toonme.com/d/48671890`), `isleme_zaman_asimi_sn` (180),
`bluestacks_ornek` (`Pie64`). Şablon değiştirmek için ToonMe'de şablon → paylaş → **Copy URL** ile alınan bağlantı yapıştırılır.

**Kayıtlar:** `%LOCALAPPDATA%\ToonMeKarakter\kayit.log`; hata başına `hatalar\<zaman>\ekran.png` + `ui.xml`.

## 5. Hata durumları

| Durum | Davranış |
|---|---|
| BlueStacks kapalı | Başlat, en çok 90 sn açılmasını bekle |
| ADB kapalı (`enable_adb_access="0"`) | Dur; bildirim: "BlueStacks → Settings → Advanced → ADB'yi aç" |
| Adım zaman aşımı | ToonMe'yi kapat, işi bağlantıdan bir kez baştan dene; yine olmazsa hata kaydı + bildirim "X adımında takıldı" |
| Beklenmedik pencere (VIP teklifi, puanlama, reklam) | Bilinen kapatma öğelerini dene (`close-or-skip-button`, "Close", "Not now", "No thanks"…), olmazsa `KEYCODE_BACK`; en çok 3 kez |
| ToonMe hata mesajı (yüz bulunamadı, ağ hatası) | Mesaj metni bildirimde gösterilir; yeniden deneme yok |
| Desteklenmeyen dosya | Sağ tık yalnızca resim türlerinde görünür; yine de uzantı denetlenir |
| Hedef dosya adı dolu | `_toon (2)`, `_toon (3)` … |

Her durumda emülatör temizliği (§3 adım 10) `finally` içinde çalışır; kullanıcı fotoğrafları emülatörde kalmaz.

## 6. Test

- **Birim (pytest, ADB'siz):** UI dökümü ayrıştırma ve seçici eşleme (incelemede alınan gerçek XML'ler örnek
  veri olarak), çıktı dosya adı üretimi, ayar okuma/varsayılanlar, bluestacks.conf'tan port okuma, kuyruk kilidi.
- **Akış birim testi:** `toonme_akis` sahte bir ekran/ADB katmanıyla (kaydedilmiş döküm dizisi) adım sırası ve
  zaman aşımı/yeniden deneme davranışı için sınanır.
- **Uçtan uca (gerçek BlueStacks):** (1) BlueStacks açıkken tek fotoğraf, (2) aynı anda 3 fotoğraf, (3) BlueStacks
  kapalıyken tek fotoğraf. Her birinde sonuç dosyası, süre ve emülatörün temiz kaldığı doğrulanır. İşleme süresi
  burada ölçülüp README'ye yazılır.

## 7. Uygulamada doğrulanan noktalar (çözüldü)

1. İşleme bitişi: işlem ~17–20 sn sürüyor; bu sırada "Processing…" + `progressBar` var, `more` yok → `more` beklemek yeterli
   (gerçek döküm `tests/fixtures/isleniyor.xml` ile sabitlendi).
2. Fotoğraf seçimi: "Recent" ToonMe geçmişi olduğundan yanlış fotoğraf seçiliyordu → `All` + `datetaken` (bkz. §3).
3. Diğer gerçek cihaz bulguları: aynı ToonMe sürecinde önceden kaydedilen sonuç yeniden kaydedilmiyor (her deneme
   `force-stop` ile başlar); soğuk açılışta odak "Splash Screen" olduğundan Geri'ye basılmaz; seçici geç yüklenirse
   `All` dokunuşu yinelenir.
4. ToonMe aynı fotoğraftan her seferinde farklı güçte sonuç üretebiliyor; araç ToonMe'nin gösterdiğini aynen kaydeder.

## 8. Güvenlik notu

ToonMe'yi güvenilir bir kaynaktan (Google Play) kurmanız önerilir. Araç emülatöre başka bir uygulama kurmaz ve iş
bitince fotoğrafları emülatör galerisinden siler.
