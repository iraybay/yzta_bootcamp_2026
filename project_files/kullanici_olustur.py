import sqlite3
from werkzeug.security import generate_password_hash

def create_admin():
    conn = sqlite3.connect('bulutis.db')
    c = conn.cursor()
    
    # Kullanıcılar tablosunu oluştur
    c.execute('''CREATE TABLE IF NOT EXISTS kullanicilar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kullanici_adi TEXT UNIQUE,
                    sifre TEXT
                )''')
    
    # Varsayılan kullanıcı: admin / Sifre: 123456
    hashed_pw = generate_password_hash('123456')
    
    try:
        c.execute("INSERT INTO kullanicilar (kullanici_adi, sifre) VALUES (?, ?)", ('admin', hashed_pw))
        conn.commit()
        print("✅ Kullanıcı tablosu oluşturuldu!")
        print("✅ Varsayılan kullanıcı eklendi -> Kullanıcı Adı: admin | Şifre: 123456")
    except sqlite3.IntegrityError:
        print("ℹ️ 'admin' kullanıcısı zaten mevcut.")
        
    conn.close()

if __name__ == '__main__':
    create_admin()