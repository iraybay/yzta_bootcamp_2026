# Bulutİş ERP - Kurulum ve Kullanım Kılavuzu

Bu proje, Python kullanılarak geliştirilmiş akıllı bir ERP ve ön muhasebe yönetim sistemidir. Uygulamada yerel yapay zeka (**Ollama**) veya bulut yapay zeka (**Google Gemini API**) asistanı entegredir.

Uygulamayı çalıştırmak için herhangi bir derleme işlemine veya kurulum programına ihtiyacınız yoktur. İşletim sisteminize uygun olan başlatma dosyasını çalıştırmanız yeterlidir.

---

## ⚡ 1. Adım: Yapay Zeka (LLM) Seçimi ve Ayarı

Uygulamanın yapay zeka özelliklerini çalıştırmak için iki yöntemden birini seçebilirsiniz:

### Yöntem A: Google Gemini API (Önerilen - Hızlı ve Sıfır Isınma)
Bu yöntem bulut üzerinden çalıştığı için bilgisayarınızı yormaz, fanları çalıştırmaz ve yanıtları 1 saniyede üretir.
1. [Google AI Studio](https://aistudio.google.com/) adresine gidin (tamamen ücretsizdir).
2. **"Get API Key"** butonuna tıklayarak ücretsiz bir API anahtarı oluşturun.
3. Proje klasöründeki `.env.template` dosyasının adını **`.env`** olarak değiştirin.
4. `.env` dosyasını bir metin editörüyle açın ve aşağıdaki gibi doldurun:
   ```env
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=OLUSTURDUGUNUZ_API_ANAHTARI
   GEMINI_MODEL=gemini-3.5-flash-lite
   ```

### Yöntem B: Yerel Yapay Zeka (Ollama - Çevrimdışı ve Gizli)
Bu yöntem tamamen bilgisayarınızda çalışır, internet bağlantısı gerektirmez ancak bilgisayarınızı yorabilir.
1. [ollama.com](https://ollama.com/) adresinden işletim sisteminize uygun Ollama uygulamasını indirin ve kurun.
2. Ollama uygulamasını çalıştırın.
3. Bilgisayarınızın terminalini (Windows'ta CMD, Mac'te Terminal) açın ve yerel Türkçe modelimizi indirmek için şu komutu çalıştırın:
   ```bash
   ollama pull gemma2:9b
   ```
4. Proje klasöründeki `.env.template` dosyasının adını **`.env`** olarak değiştirin:
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=gemma2:9b
   OLLAMA_URL=http://localhost:11434/api/chat
   ```

---

## 🚀 2. Adım: Uygulamayı Başlatma

### 🪟 Windows İçin Başlatma
1. Proje klasörü içerisindeki **`baslat_windows.bat`** dosyasına çift tıklayın.
2. Açılan siyah ekranda (Terminal) kurulum işlemleri otomatik olarak yapılacaktır.
3. Kurulum bittiğinde uygulama başlatılacak ve varsayılan web tarayıcınızda (örn. Chrome) otomatik açılacaktır.

### 🍎 Mac ve 🐧 Linux İçin Başlatma
1. Proje klasörü içerisindeki **`baslat_mac_linux.command`** dosyasına çift tıklayın.
   - *Mac izin vermezse; dosyaya sağ tıklayıp "Aç" deyin.*
2. Terminal ekranı açılacak ve gerekli ortam otomatik olarak hazırlanacaktır.
3. İşlem tamamlandığında uygulama tarayıcınızda açılacaktır.

---

## 🔒 Güvenlik Notu (GitHub ve Paylaşım)

- **`.env` Dosyası:** Sizin kişisel API anahtarlarınızı barındırır. Bu dosya `.gitignore` içinde kayıtlıdır ve **GitHub'a kesinlikle yüklenmemelidir**. Herkese açık depolarda paylaşılan anahtarlar Google tarafından anında iptal edilir.
- **Paylaşım Seçenekleri:**
  - **GitHub Üzerinden Paylaşım:** Projeyi GitHub'a yükleyin. İndiren kişiler kendi ücretsiz Gemini API anahtarlarını alarak veya Ollama kurarak yukarıdaki adımlarla çalıştırırlar.
  - **Güvenli Kişisel Paylaşım (Zip):** Eğer projeyi sadece güvendiğiniz bir arkadaşınıza doğrudan gönderecekseniz, kendi API anahtarınızın yazılı olduğu `.env` dosyasını da zip dosyasına dahil edebilirsiniz. Bu durumda arkadaşınız hiçbir ayar yapmadan direkt çift tıklayıp projenizi kullanabilir.
