# BulutIs - Kurulum ve Kullanım Kılavuzu

Bu proje, Python kullanılarak geliştirilmiş bir web uygulamasıdır (BulutIs). Uygulamayı kullanmak için herhangi bir ekstra program kurulumuna veya `.exe` / `.app` dosyasına ihtiyacınız yoktur. İşletim sisteminize uygun olan başlatma dosyasını çalıştırmanız yeterlidir. Uygulama sizin için gerekli ortamı kendi kuracak ve web tarayıcınızda otomatik olarak açılacaktır.

## Sistem Gereksinimleri
- Bilgisayarınızda **Python 3.x** sürümünün kurulu olması gerekmektedir. Eğer kurulu değilse [python.org](https://www.python.org/downloads/) adresinden indirip kurabilirsiniz. *(Windows için kurulum sırasında "Add Python to PATH" seçeneğini işaretlemeyi unutmayın!)*

---

## 🪟 Windows İçin Kurulum ve Başlatma

1. Proje klasörünü açın.
2. Klasör içerisindeki **`baslat_windows.bat`** dosyasına çift tıklayın.
3. Açılan siyah ekranda (Terminal) kurulum işlemleri (yaklaşık 1-2 dakika sürebilir) otomatik olarak yapılacaktır.
4. Kurulum bittiğinde uygulama başlatılacak ve varsayılan web tarayıcınızda (örn. Chrome) otomatik olarak açılacaktır.
5. Uygulamayı kullanmayı bitirdiğinizde siyah ekranı kapatabilirsiniz.
   - *Bir sonraki kullanımlarınızda kurulum yapmayacak, sadece uygulamayı başlatacağı için daha hızlı açılacaktır.*

---

## 🍎 Mac ve 🐧 Linux İçin Kurulum ve Başlatma

1. Proje klasörünü açın.
2. Klasör içerisindeki **`baslat_mac_linux.command`** dosyasına çift tıklayın.
   - *Eğer Mac güvenlik nedeniyle açılmasına izin vermezse; dosyaya sağ tıklayın, **Aç**'a basın ve çıkan uyarıda tekrar **Aç**'a tıklayın.*
3. Terminal ekranı açılacak ve gerekli kurulumlar otomatik olarak yapılacaktır.
4. İşlem tamamlandığında uygulama tarayıcınızda açılacaktır.
5. Kullanımınız bittiğinde Terminal penceresini kapatmanız yeterlidir.

---

### Sorun Giderme (Sık Karşılaşılan Hatalar)

- **Siyah ekran (Terminal) hemen kapanıyor ve açılmıyorsa:**
  Büyük ihtimalle bilgisayarınızda Python yüklü değildir. Python'u yüklediğinizden ve Windows'ta Path'e eklediğinizden emin olun.
- **Port kullanımda hatası:**
  Arka planda başka bir uygulamanın açık kalmış olma ihtimali yüksektir. Terminal pencerelerini tamamen kapatıp tekrar başlatmayı deneyin.
- **Mac'te "İzin reddedildi" (Permission denied) hatası:**
  Uygulamayı indirdiğinizde çalıştırma izni kaybolmuş olabilir. Uygulamalar (Launchpad) > Terminal'i açıp şu komutu yazabilirsiniz: `chmod +x /dosya/yolu/baslat_mac_linux.command` (Komutu yazıp, dosyayı terminalin içine sürükleyerek yolu ekleyebilirsiniz).

---

> **Not:** `.exe` dosyası hazırlamak veya paket program kullanmak yerine bu başlatıcı dosyaları (.bat / .command) kullanmak, hem her cihazda %100 çalışmasını sağlar hem de güncellemeleri çok daha kolay yapmanıza olanak tanır.
