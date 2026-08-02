#!/bin/bash

# Dosyanin oldugu dizine gec
cd "$(dirname "$0")"

echo "=========================================="
echo " BulutIs ERP Kurulum ve Baslatma Araci"
echo "=========================================="
echo ""

if [ ! -d ".venv" ]; then
    echo "[1/3] Sanal ortam (virtual environment) kuruluyor..."
    python3 -m venv .venv
else
    echo "[1/3] Sanal ortam zaten mevcut."
fi

if [ ! -f ".env" ]; then
    echo ".env dosyasi bulunamadi. .env.template kopyalaniyor..."
    cp .env.template .env
fi

echo "[2/3] Sanal ortam aktif ediliyor ve kutuphaneler yukleniyor..."
source .venv/bin/activate
pip install -r requirements.txt

echo ""
if command -v ollama >/dev/null 2>&1; then
    echo "[3/4] Yerel yapay zeka modelleri kontrol ediliyor (gemma2:9b ve phi3)..."
    ollama pull gemma2:9b
    ollama pull phi3
else
    echo "[!] Ollama bilgisayarinizda kurulu degil. Otomatik olarak indiriliyor ve kuruluyor..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "[3/4] Yerel yapay zeka modelleri kontrol ediliyor (gemma2:9b ve phi3)..."
    ollama pull gemma2:9b
    ollama pull phi3
fi

echo ""
echo "[4/4] Uygulama baslatiliyor... (Tarayicida otomatik acilacaktir)"
python3 app.py
