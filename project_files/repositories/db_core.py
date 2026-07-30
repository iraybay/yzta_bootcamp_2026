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

    # --- ÖRNEK (SEED) VERİLER ---
    cursor.execute("SELECT COUNT(*) FROM cari")
    if cursor.fetchone()[0] == 0:
        cariler = [
            ("Ahmet Yılmaz", "musteri", 150000.0, "12345678901", "Kadıköy V.D.", "Ahmet Yılmaz", "ahmet@yilmazinsaat.com", "0532 111 22 33", "İstanbul", "Kadıköy", "Caferağa Mah.", "Moda Cad. No:12 D:4", "İnşaat", "A+"),
            ("Ayşe Kaya", "musteri", 100000.0, "23456789012", "Beşiktaş V.D.", "Ayşe Kaya", "ayse@kayatasarim.com", "0533 222 33 44", "İstanbul", "Beşiktaş", "Sinanpaşa Mah.", "Ihlamurdere Cad. No:45", "Tasarım & Mimarlık", "A"),
            ("TeknoMarket A.Ş.", "musteri", 50000.0, "9876543210", "Zincirlikuyu V.D.", "Mehmet Demir", "info@teknomarket.com", "0212 555 44 33", "İstanbul", "Şişli", "Esentepe Mah.", "Büyükdere Cad. No:199", "Teknoloji", "B"),
            ("Doruk Toptan Gıda", "tedarikci", 100000.0, "1231231234", "Gıda İhtisas V.D.", "Mustafa Doruk", "bilgi@dorukgida.com", "0212 222 33 44", "İstanbul", "Esenler", "Menderes Mah.", "Toptancılar Sitesi B Blok No:14", "Gıda Tedarik", "A")
        ]
        cursor.executemany('''
            INSERT INTO cari (ad, tip, limit_val, vergi_no, vergi_dairesi, yetkili_kisi, eposta, telefon, il, ilce, mahalle, adres_detay, cari_grubu, kredibilite)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', cariler)

    cursor.execute("SELECT COUNT(*) FROM kasa_banka_hesap")
    if cursor.fetchone()[0] == 0:
        hesaplar = [
            ("Merkez Kasa", "kasa", None, None, None, "TRY", 50000.0, "A+"),
            ("Dış Saha Kasası", "kasa", None, None, None, "TRY", 15000.0, "B"),
            ("Akbank Ticari", "banka", "4489-012398", "TR450004600192384759281234", "Maslak", "TRY", 125000.0, "A+"),
            ("Garanti Şirket", "banka", "3320-998822", "TR920006200088112233445566", "Levent", "TRY", 85000.0, "A")
        ]
        cursor.executemany('''
            INSERT INTO kasa_banka_hesap (ad, tur, hesap_no, iban, sube, doviz_turu, bakiye, kredibilite)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', hesaplar)

    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye")
    if cursor.fetchone()[0] == 0:
        faturalar = [
            (1, "FT-2026-00045", "fatura", "FT-2026-00045 - Satış Faturası", 18500.0, "Ödenmedi", "2026-07-18"),
            (2, "IR-2026-00021", "irsaliye", "IR-2026-00021 - Sevk İrsaliyesi", 0.0, "Bekliyor", "2026-07-18"),
            (3, "FT-2026-00044", "fatura", "FT-2026-00044 - Alış Faturası", 22000.0, "Ödendi", "2026-07-17")
        ]
        cursor.executemany('''
            INSERT INTO fatura_irsaliye (cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', faturalar)

    conn.commit()
    conn.close()

init_db()