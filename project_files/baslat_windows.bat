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
echo [3/3] Uygulama baslatiliyor... (Tarayicida otomatik acilacaktir)
python app.py

pause
