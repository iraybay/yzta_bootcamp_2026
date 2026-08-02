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
echo "[3/3] Uygulama baslatiliyor... (Tarayicida otomatik acilacaktir)"
python3 app.py
