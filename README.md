# ToonMe Karakter Yap

Windows Gezgini'nde bir fotoğrafa sağ tıklayıp **"ToonMe karakter yap"** dediğinizde, BlueStacks'teki ToonMe
uygulamasının *Toon Mirror* şablonu arka planda uygulanır ve sonuç orijinalin yanına `<ad>_toon.jpg` olarak kaydedilir.
ToonMe'yi açmanız, menülerde şablonu aramanız gerekmez.

## Gereksinimler

- Windows 11, Python 3.14 (ek paket gerekmez)
- BlueStacks 5 (`C:\Program Files\BlueStacks_nxt`) ve içinde ToonMe
- BlueStacks'te ADB açık olmalı: BlueStacks penceresinde **Ctrl+Shift+I** → **Advanced** → **Android Debug Bridge (ADB)** → *Save changes*

## Kurulum

```bash
python -m toonme_karakter kur
```

Sağ tık menüsü yalnızca sizin kullanıcı hesabınıza eklenir (yönetici izni gerekmez). Windows 11'de menü
**"Diğer seçenekleri göster"** altında görünür. Kaldırmak için:

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

## Şablonu değiştirmek

`ayarlar.json` içindeki `sablon_url` değerini değiştirin. Bağlantıyı almak için ToonMe'de istediğiniz şablonu açın →
sağ üstteki paylaş simgesi → **Copy URL**. `?utm_source=app` gibi ekler sorun değildir.

```json
{
  "sablon_url": "https://toonme.com/d/48671890",
  "isleme_zaman_asimi_sn": 180,
  "bluestacks_ornek": "Pie64"
}
```

## Nasıl çalışır

1. Fotoğraf BlueStacks'in galerisine (`Pictures/ToonMeInput`) kopyalanır, çekim tarihi "şimdi" yapılır.
2. ToonMe şablon bağlantısıyla (`toonme.com/d/<kimlik>`) doğrudan şablonun fotoğraf seçme ekranında açılır.
3. **All** sekmesindeki ilk fotoğraf (bizimki) seçilir, kırpma geçilir, işleme ("Processing…") beklenir.
4. ⋮ → *Save to device* → *Download* ile sonuç kaydedilir ve bilgisayara alınır.
5. Girdi ve çıktı emülatörden silinir, ToonMe kapatılır; fotoğraflarınız emülatörde birikmez.

Arayüz öğeleri koordinatla değil kimlik/metinle bulunur; araya giren reklam/teklif pencereleri kapatılır.

## Sorun giderme

- Kayıtlar: `%LOCALAPPDATA%\ToonMeKarakter\kayit.log`
- Her hata için o anın ekran görüntüsü ve ekran dökümü: `%LOCALAPPDATA%\ToonMeKarakter\hatalar\<tarih-saat>\`
- "ADB kapalı" bildirimi → yukarıdaki ADB ayarını açın.
- Bir adım takılırsa araç ToonMe'yi kapatıp işi bir kez baştan dener.

## Geliştirme

```bash
python -m pytest
```

Testler gerçek ToonMe ekranlarından alınmış dökümleri (`tests/fixtures/`) kullanır; cihaz gerektirmez.
Tasarım: `docs/superpowers/specs/2026-10-16-toonme-sag-tik-design.md`
