# ToonMe Karakter Yap

Windows Gezgini'nde bir fotoğrafa sağ tıklayıp **"ToonMe karakter yap"** dediğinizde, BlueStacks'teki ToonMe
uygulamasının *Toon Mirror* şablonu arka planda uygulanır ve sonuç orijinalin yanına `<ad>_toon.jpg` olarak kaydedilir.
ToonMe'yi açmanız, menülerde şablonu aramanız gerekmez.

## Gereksinimler

- Windows 11 (Windows 10'da da çalışması beklenir ama denenmedi)
- Python 3.14 ([python.org](https://www.python.org/downloads/)); kurarken **"Add python.exe to PATH"** kutusunu işaretleyin.
  Ek Python paketi gerekmez. (Araç Python 3.14 ile test edildi.)
- [BlueStacks 5](https://www.bluestacks.com/) ve içinde **ToonMe** (BlueStacks'teki Google Play'den kurun)
- BlueStacks'te ADB açık olmalı: BlueStacks penceresinde **Ctrl+Shift+I** → **Advanced** →
  **Android Debug Bridge (ADB)** anahtarını açın → *Save changes*

## Kurulum (adım adım)

1. **Projeyi indirin.** GitHub sayfasında yeşil **Code** düğmesi → **Download ZIP**, sonra ZIP'i kalıcı bir klasöre
   açın (ör. `Belgeler\toonme-karakter`). Git kullanıyorsanız:

   ```bash
   git clone https://github.com/AliOlkac/toonme-karakter.git
   ```

2. **BlueStacks örnek adınızı kontrol edin.** Varsayılan `Pie64`'tür. Farklıysa `ayarlar.json` içindeki
   `bluestacks_ornek` değerini değiştirin (aşağıya bakın). Adı bulmak için masaüstündeki BlueStacks / ToonMe kısayoluna
   sağ tık → *Özellikler* → *Hedef*: `--instance <AD>` kısmındaki ad sizin örnek adınızdır.

3. **Sağ tık menüsünü kurun.** Proje klasöründe bir terminal (PowerShell) açıp:

   ```bash
   python -m toonme_karakter kur
   ```

   Menü yalnızca sizin kullanıcı hesabınıza eklenir (yönetici izni gerekmez). Windows 11'de menü
   **"Diğer seçenekleri göster"** altında görünür.

4. **Deneyin:** bir fotoğrafa sağ tık → **ToonMe karakter yap**. İlk seferde BlueStacks kapalıysa açılması biraz sürer.

Menü, projenin bulunduğu klasördeki kodu çalıştırır. Klasörü taşır veya silerseniz menü çalışmaz; taşıdıysanız
yeni yerde `kur` komutunu tekrar çalıştırın. Kaldırmak için:

```bash
python -m toonme_karakter kaldir
```

## Kullanım

- Bir veya birden çok fotoğrafı (jpg, png, webp) seçin → sağ tık → **ToonMe karakter yap**.
- "İşleniyor" bildirimi gelir; bitince **"Karakter hazır"** bildirimine tıklayınca sonuç açılır.
- BlueStacks kapalıysa araç kendisi açar.
- Birden çok fotoğraf seçerseniz sırayla işlenir. Windows, 15'ten fazla dosya seçildiğinde bu menüyü göstermez.
- Aynı fotoğrafı tekrar işlerseniz eski sonucun üzerine yazılmaz: `foto_toon (2).jpg`, `(3)`… oluşur.
- Komut satırından da çalışır: `python -m toonme_karakter "C:\yol\foto.jpg"`

**Sonuç beklediğiniz kadar "karakter" olmadıysa** tekrar sağ tıklayın: ToonMe aynı fotoğraftan her seferinde
farklı güçte sonuç üretebiliyor (testlerde aynı fotoğraf bir seferinde tam 3D karakter, bir seferinde neredeyse
fotoğrafın kendisi çıktı). Sade, beyaz zeminli, tam boy fotoğraflarda sonuç daha tutarlıdır.

## Süreler (ölçülen)

| Durum | Süre |
|---|---|
| BlueStacks açıkken, 1 fotoğraf | ~35–40 sn |
| BlueStacks kapalıyken, 1 fotoğraf (araç açar) | ~50–100 sn |
| Aynı anda 3 fotoğraf (sırayla) | ~110 sn |

## Ayarlar (`ayarlar.json`)

```json
{
  "sablon_url": "https://toonme.com/d/48671890",
  "isleme_zaman_asimi_sn": 180,
  "bluestacks_ornek": "Pie64"
}
```

- **`sablon_url`** — kullanılacak ToonMe şablonu. Başka bir şablon için ToonMe'de şablonu açın → sağ üstteki paylaş
  simgesi → **Copy URL** ve bağlantıyı buraya yapıştırın. `?utm_source=app` gibi ekler sorun değildir.
- **`isleme_zaman_asimi_sn`** — ToonMe'nin işlemesi için beklenecek en uzun süre (saniye).
- **`bluestacks_ornek`** — BlueStacks örnek adı (bkz. Kurulum adım 2).
- BlueStacks farklı bir klasöre kuruluysa iki ayar daha ekleyebilirsiniz (varsayılanlar):
  `"bluestacks_dizini": "C:\\Program Files\\BlueStacks_nxt"` ve
  `"bluestacks_conf": "C:\\ProgramData\\BlueStacks_nxt\\bluestacks.conf"`.

## Nasıl çalışır

1. Fotoğraf BlueStacks'in galerisine (`Pictures/ToonMeInput`) kopyalanır, çekim tarihi "şimdi" yapılır.
2. ToonMe şablon bağlantısıyla (`toonme.com/d/<kimlik>`) doğrudan şablonun fotoğraf seçme ekranında açılır.
3. **All** sekmesindeki ilk fotoğraf (bizimki) seçilir, kırpma geçilir, işleme ("Processing…") beklenir.
4. ⋮ → *Save to device* → *Download* ile sonuç kaydedilir ve bilgisayara alınır.
5. Girdi ve çıktı emülatörün galerisinden silinir (hata olsa bile), ToonMe kapatılır.
   Not: ToonMe kullandığı fotoğrafların kopyalarını kendi **Recent** geçmişinde tutar; bunu araç silemez,
   isterseniz ToonMe içinden temizleyebilirsiniz.

Arayüz öğeleri koordinatla değil kimlik/metinle bulunur; araya giren reklam/teklif pencereleri kapatılır.

## Sorun giderme

- Kayıtlar: `%LOCALAPPDATA%\ToonMeKarakter\kayit.log`
- Her hata için o anın ekran görüntüsü ve ekran dökümü: `%LOCALAPPDATA%\ToonMeKarakter\hatalar\<tarih-saat>\`
- "ADB kapalı" bildirimi → yukarıdaki ADB ayarını açın.
- "BlueStacks 90 saniyede açılmadı" → `bluestacks_ornek` adının doğru olduğunu kontrol edin.
- Sağ tıkta menü yok → Windows 11'de "Diğer seçenekleri göster"e bakın; yoksa `python -m toonme_karakter kur`'u
  proje klasöründe tekrar çalıştırın.
- Bir adım takılırsa araç ToonMe'yi kapatıp işi bir kez baştan dener.

## Geliştirme

```bash
python -m pytest
```

Testler gerçek ToonMe ekranlarından alınmış dökümleri (`tests/fixtures/`) kullanır; cihaz gerektirmez.
Tasarım: `docs/superpowers/specs/2026-10-16-toonme-sag-tik-design.md`
