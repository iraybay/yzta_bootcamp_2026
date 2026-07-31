import sqlite3
import os
import datetime
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(APP_DIR)
DB_FILE = os.path.join(PROJECT_DIR, 'bulutis.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Cari Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            tip TEXT NOT NULL,
            limit_val REAL DEFAULT 0,
            vergi_no TEXT NOT NULL,
            vergi_dairesi TEXT,
            yetkili_kisi TEXT NOT NULL,
            eposta TEXT,
            telefon TEXT,
            il TEXT,
            ilce TEXT,
            mahalle TEXT,
            adres_detay TEXT,
            cari_grubu TEXT,
            kredibilite TEXT DEFAULT 'A'
        )
    ''')
    
    # 2. Cari İşlem Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cari_islem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_id INTEGER,
            tanim TEXT NOT NULL,
            tutar REAL DEFAULT 0,
            tip TEXT NOT NULL,
            tarih TEXT NOT NULL,
            odeme_tarihi TEXT,
            FOREIGN KEY (cari_id) REFERENCES cari(id) ON DELETE SET NULL
        )
    ''')
    
    # 3. Kasa & Banka Hesap Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kasa_banka_hesap (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            tur TEXT NOT NULL,
            hesap_no TEXT,
            iban TEXT,
            sube TEXT,
            doviz_turu TEXT DEFAULT 'TRY',
            bakiye REAL DEFAULT 0,
            kredibilite TEXT DEFAULT 'A'
        )
    ''')

    # 4. Kasa & Banka İşlem Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kasa_banka_islem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hesap_id INTEGER,
            cari_id INTEGER,
            fatura_id INTEGER,
            tanim TEXT NOT NULL,
            tutar REAL DEFAULT 0,
            tip TEXT NOT NULL,
            tarih TEXT NOT NULL,
            islem_turu TEXT NOT NULL DEFAULT 'gelir',
            FOREIGN KEY (hesap_id) REFERENCES kasa_banka_hesap(id) ON DELETE CASCADE,
            FOREIGN KEY (cari_id) REFERENCES cari(id) ON DELETE SET NULL
        )
    ''')
    
    # 5. Stok Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            kategori TEXT NOT NULL,
            adet INTEGER DEFAULT 0
        )
    ''')
    
    # 6. Stok İşlem Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stok_islem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanim TEXT NOT NULL,
            tip TEXT NOT NULL,
            tarih TEXT NOT NULL
        )
    ''')
    
    # 7. Fatura & İrsaliye Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fatura_irsaliye (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_id INTEGER,
            belge_no TEXT,
            belge_turu TEXT,
            tanim TEXT NOT NULL,
            tutar REAL DEFAULT 0,
            durum TEXT NOT NULL,
            tarih TEXT NOT NULL,
            FOREIGN KEY (cari_id) REFERENCES cari(id)
        )
    ''')

    # 8. Ödeme Planı Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS odeme_plani (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_ad TEXT NOT NULL,
            tutar REAL DEFAULT 0,
            kalan_tutar REAL DEFAULT 0,
            tip TEXT NOT NULL,
            tarih TEXT NOT NULL,
            aciklama TEXT,
            durum TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()