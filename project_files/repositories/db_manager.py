import sqlite3
import os

# Veritabanı dosyasının mutlak yolu (project_files/bulutis.db)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bulutis.db")

def get_db_connection():
    """
    Sadece SQLite bağlantısı kurar, Row factory ayarlar 
    ve Foreign Key kısıtlamalarını aktif eder.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Dict tarzı erişim için (row['kolon_adi'])
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """
    Sadece tablolar yoksa oluşturur (Schema Initializer).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS cari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unvan TEXT NOT NULL,
            telefon TEXT DEFAULT '',
            eposta TEXT DEFAULT '',
            adres TEXT DEFAULT '',
            bakiye REAL DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS kasa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kasa_adi TEXT NOT NULL,
            bakiye REAL DEFAULT 0.0,
            aciklama TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS kasa_hareketleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kasa_id INTEGER NOT NULL,
            tarih TEXT NOT NULL,
            aciklama TEXT DEFAULT '',
            tutar REAL NOT NULL DEFAULT 0.0,
            islem_tipi TEXT CHECK(islem_tipi IN ('GIRIS', 'CIKIS')),
            FOREIGN KEY (kasa_id) REFERENCES kasa (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS cari_hareketleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_id INTEGER NOT NULL,
            tarih TEXT NOT NULL,
            islem_tipi TEXT NOT NULL,
            aciklama TEXT DEFAULT '',
            tutar REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (cari_id) REFERENCES cari (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS stok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stok_kodu TEXT UNIQUE NOT NULL,
            stok_adi TEXT NOT NULL,
            birim TEXT DEFAULT 'Adet',
            miktar REAL DEFAULT 0.0,
            birim_fiyat REAL DEFAULT 0.0,
            kdv REAL DEFAULT 20.0
        );

        CREATE TABLE IF NOT EXISTS fatura_irsaliye (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fatura_no TEXT NOT NULL,
            cari_id INTEGER NOT NULL,
            tarih TEXT NOT NULL,
            fatura_tipi TEXT CHECK(fatura_tipi IN ('SATIS', 'ALIS')),
            genel_toplam REAL DEFAULT 0.0,
            aciklama TEXT DEFAULT '',
            FOREIGN KEY (cari_id) REFERENCES cari (id) ON DELETE RESTRICT
        );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()