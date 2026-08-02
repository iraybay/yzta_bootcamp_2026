@echo off
title BulutIs ERP Baslatici
echo ==========================================
echo BulutIs ERP Kurulum ve Baslatma Araci
echo ==========================================
echo.

if not exist ".venv" (
    echo [1/3] Sanal ortam (virtual environment) kuruluyor...
    python -m venv .venv
) else (
    echo [1/3] Sanal ortam zaten mevcut.
)

if not exist ".env" (
    echo .env dosyasi bulunamadi. .env.template kopyalaniyor...
    copy .env.template .env
)

echo [2/3] Sanal ortam aktif ediliyor ve kutuphaneler yukleniyor...
call .venv\Scripts\activate
pip install -r requirements.txt

echo.
where ollama >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [3/4] Yerel yapay zeka modelleri kontrol ediliyor (gemma2:9b ve phi3)...
    ollama pull gemma2:9b
    ollama pull phi3
) else (
    echo [!] Ollama bilgisayarinizda kurulu degil. Otomatik olarak indiriliyor...
    curl -L https://ollama.com/download/OllamaSetup.exe -o OllamaSetup.exe
    echo Kurulum ekrani acilacak. Lutfen kurulumu tamamlayin...
    start /wait OllamaSetup.exe
    echo Kurulum tamamlandiktan sonra lutfen bu pencereyi kapatin ve baslatici dosyayi yeniden calistirin!
    pause
    exit
)

echo.
echo [4/4] Uygulama baslatiliyor... (Tarayicida otomatik acilacaktir)
python app.py

pause
