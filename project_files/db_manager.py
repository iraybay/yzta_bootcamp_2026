import sqlite3
import os
import sys
import datetime

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(APP_DIR, 'bulutis.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)

    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Cari Table with structured address fields & Kredibilite
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            tip TEXT NOT NULL, -- 'musteri' veya 'tedarikci'
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
    
    # 2. Cari Islem Table with ISO Date & Cari Link & Payment Date
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cari_islem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_id INTEGER,
            tanim TEXT NOT NULL,
            tutar REAL DEFAULT 0,
            tip TEXT NOT NULL, -- 'alacak' veya 'borc' veya 'bilgi'
            tarih TEXT NOT NULL, -- YYYY-MM-DD format
            odeme_tarihi TEXT,   -- YYYY-MM-DD format (NULL means unpaid/open invoice)
            FOREIGN KEY (cari_id) REFERENCES cari(id) ON DELETE SET NULL
        )
    ''')
    
    # 3a. Kasa & Banka Hesap Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kasa_banka_hesap (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            tur TEXT NOT NULL, -- 'kasa' veya 'banka'
            hesap_no TEXT,
            iban TEXT,
            sube TEXT,
            doviz_turu TEXT DEFAULT 'TRY',
            bakiye REAL DEFAULT 0,
            kredibilite TEXT DEFAULT 'A'
        )
    ''')

    # 3. Kasa & Banka Islem Table (linked to accounts and cariler)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kasa_banka_islem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hesap_id INTEGER,
            cari_id INTEGER,
            fatura_id INTEGER,
            tanim TEXT NOT NULL,
            tutar REAL DEFAULT 0,
            tip TEXT NOT NULL, -- 'giris' veya 'cikis'
            tarih TEXT NOT NULL,
            islem_turu TEXT NOT NULL DEFAULT 'gelir', -- 'tahsilat', 'odeme', 'transfer', 'gelir', 'gider'
            FOREIGN KEY (hesap_id) REFERENCES kasa_banka_hesap(id) ON DELETE CASCADE,
            FOREIGN KEY (cari_id) REFERENCES cari(id) ON DELETE SET NULL,
            FOREIGN KEY (fatura_id) REFERENCES fatura_irsaliye(id) ON DELETE SET NULL
        )
    ''')
    
    # 4. Stok Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            kategori TEXT NOT NULL,
            adet INTEGER DEFAULT 0
        )
    ''')
    
    # 5. Stok Islem Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stok_islem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanim TEXT NOT NULL,
            tip TEXT NOT NULL, -- 'giris' veya 'cikis' veya 'alarm'
            tarih TEXT NOT NULL
        )
    ''')
    
    # 6. Fatura & Irsaliye Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fatura_irsaliye (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_id INTEGER,
            belge_no TEXT,
            belge_turu TEXT,
            tanim TEXT NOT NULL,
            tutar REAL DEFAULT 0,
            durum TEXT NOT NULL, -- 'Ödendi' veya 'Ödenmedi' veya 'Bekliyor'
            tarih TEXT NOT NULL,
            FOREIGN KEY (cari_id) REFERENCES cari(id)
        )
    ''')

    # 7. Odeme Plani Table (includes kalan_tutar for tracking partial outstanding values)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS odeme_plani (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_ad TEXT NOT NULL,
            tutar REAL DEFAULT 0,
            kalan_tutar REAL DEFAULT 0,
            tip TEXT NOT NULL, -- 'gelir' veya 'borç'
            tarih TEXT NOT NULL,
            aciklama TEXT,
            durum TEXT NOT NULL
        )
    ''')

    # 8. Tahsilat / Ödeme Makbuzları
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cari_makbuz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_id INTEGER NOT NULL,
            hesap_id INTEGER NOT NULL,
            makbuz_no TEXT NOT NULL,
            tip TEXT NOT NULL, -- 'tahsilat' veya 'tediye'
            tutar REAL DEFAULT 0,
            tarih TEXT NOT NULL,
            aciklama TEXT,
            FOREIGN KEY (cari_id) REFERENCES cari(id),
            FOREIGN KEY (hesap_id) REFERENCES kasa_banka_hesap(id)
        )
    ''')

    # 9. Çek / Senet Takibi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cek_senet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_id INTEGER NOT NULL,
            belge_no TEXT NOT NULL,
            tur TEXT NOT NULL, -- 'cek' veya 'senet'
            yon TEXT NOT NULL, -- 'alinan' veya 'verilen'
            tutar REAL DEFAULT 0,
            vade_tarihi TEXT NOT NULL,
            durum TEXT NOT NULL, -- 'portfoyde', 'tahsilde', 'ciro', 'odendi', 'karsiliksiz'
            banka_bilgisi TEXT,
            aciklama TEXT,
            FOREIGN KEY (cari_id) REFERENCES cari(id)
        )
    ''')

    # 10. Masraf / Gider Fişleri
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS masraf_fisi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hesap_id INTEGER NOT NULL,
            fis_no TEXT,
            kategori TEXT NOT NULL, -- 'yemek', 'yakit', 'ofis', vb.
            tutar REAL DEFAULT 0,
            tarih TEXT NOT NULL,
            aciklama TEXT,
            FOREIGN KEY (hesap_id) REFERENCES kasa_banka_hesap(id)
        )
    ''')

    # 11. Siparişler (Alınan / Verilen)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS siparisler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_id INTEGER NOT NULL,
            siparis_no TEXT NOT NULL,
            tip TEXT NOT NULL, -- 'alinan' veya 'verilen'
            tutar REAL DEFAULT 0,
            tarih TEXT NOT NULL,
            teslim_tarihi TEXT,
            durum TEXT NOT NULL, -- 'bekliyor', 'onaylandi', 'iptal', 'faturalandi'
            aciklama TEXT,
            FOREIGN KEY (cari_id) REFERENCES cari(id)
        )
    ''')

    # 12. Depo / Stok Hareket Fişleri (Sayım, Fire, Transfer)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS depo_hareket (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stok_id INTEGER NOT NULL,
            fis_no TEXT NOT NULL,
            tip TEXT NOT NULL, -- 'giris', 'cikis', 'sayim_fazlasi', 'fire'
            miktar INTEGER DEFAULT 0,
            tarih TEXT NOT NULL,
            aciklama TEXT,
            irsaliye_id INTEGER,
            FOREIGN KEY (stok_id) REFERENCES stok(id),
            FOREIGN KEY (irsaliye_id) REFERENCES fatura_irsaliye(id) ON DELETE SET NULL
        )
    ''')
    
    # Check if empty to seed initial demo data
    cursor.execute("SELECT COUNT(*) FROM cari")
    if cursor.fetchone()[0] == 0:
        import random
        from datetime import date, timedelta
        
        # Helper lists for random generation
        ad_list = ["Ahmet", "Ayşe", "Mehmet", "Zeynep", "Caner", "Fatih", "Selin", "Elif", "Murat", "Deniz", "Kemal", "Merve", "Kaan", "Mustafa", "İbrahim", "Fatma", "Ömer", "Cemil", "Hasan", "Bülent"]
        soyad_list = ["Yılmaz", "Kaya", "Demir", "Vural", "Şahin", "Öztürk", "Akdeniz", "Çelik", "Yıldız", "Koç", "Sun", "Mavi", "Arslan", "Doruk", "Enerji", "Alfa", "Kağıt", "Kuzey", "Ege", "Hilal"]
        sirket_tur = ["A.Ş.", "Ltd.", "Grup", "Pazarlama", "Lojistik", "Mimarlık", "Teknoloji", "Gıda", "Sanayi", "Yazılım"]
        sektor_list = ["İnşaat", "Tasarım", "Teknoloji", "Gıda", "Danışmanlık", "Sanayi", "Lojistik", "Reklam", "Mobilya", "Kimya"]
        
        cariler = []
        for i in range(50):
            tip = random.choice(["musteri", "tedarikci"])
            is_company = random.choice([True, False])
            ad = f"{random.choice(ad_list)} {random.choice(soyad_list)}"
            if is_company:
                ad = f"{random.choice(soyad_list)} {random.choice(sirket_tur)}"
            
            limit = round(random.uniform(50000, 500000), 2)
            verg_no = f"{random.randint(1000000000, 9999999999)}"
            kredibilite = random.choice(["A+", "A", "B", "C"])
            sektor = random.choice(sektor_list)
            
            cariler.append((ad, tip, limit, verg_no, "Merkez V.D.", ad, "iletisim@sirket.com", "05550000000", "İstanbul", "Merkez", "Ana Mah.", "Ofis 1", sektor, kredibilite))
            
        cursor.executemany('''
            INSERT INTO cari (ad, tip, limit_val, vergi_no, vergi_dairesi, yetkili_kisi, eposta, telefon, il, ilce, mahalle, adres_detay, cari_grubu, kredibilite)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', cariler)
        
        cursor.execute("SELECT id, ad, tip FROM cari")
        seeded_cariler = [dict(r) for r in cursor.fetchall()]
        
        # 2. Seed Kasa & Banka Hesap
        hesaplar = [
            ("Merkez Kasa", "kasa", None, None, None, "TRY", "A+"),
            ("Döviz Kasası", "kasa", None, None, None, "USD", "A"),
            ("Akbank Ticari", "banka", "4489-012398", "TR450004600192384759281234", "Maslak", "TRY", "A+"),
            ("Garanti Şirket", "banka", "3320-998822", "TR920006200088112233445566", "Levent", "TRY", "A"),
            ("Vakıfbank EUR", "banka", "7740-881100", "TR120001500158007788990011", "Kadıköy", "EUR", "A")
        ]
        for h in hesaplar:
            cursor.execute('''
                INSERT INTO kasa_banka_hesap (ad, tur, hesap_no, iban, sube, doviz_turu, bakiye, kredibilite)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            ''', h)
            
        cursor.execute("SELECT id, ad, tur, doviz_turu FROM kasa_banka_hesap")
        seeded_hesaplar = [dict(r) for r in cursor.fetchall()]

        # 3. Seed Stok (100 items)
        kategori_list = ["Elektronik", "Ofis Malzemeleri", "Aksesuar & Sarf", "Mobilya", "Hırdavat"]
        
        elektronik = ["Laptop Dell XPS", "MacBook Pro 16", "Lenovo ThinkPad", "HP EliteBook", "Monitor LG 27'", "Monitor Samsung 32'", "iPad Pro", "Samsung Galaxy Tab", "Projeksiyon Cihazı", "Yazıcı HP Color"]
        ofis = ["A4 Fotokopi Kağıdı (Koli)", "Tükenmez Kalem Seti", "Klasör Geniş (10'lu)", "Zımba ve Tel Seti", "Not Defteri Çizgili", "Evrak Rafı", "Masa Düzenleyici", "Ajanda 2026", "Yapışkanlı Not Kağıdı", "Tahta Kalemi Seti"]
        aksesuar = ["Kablosuz Mouse Logitech", "Mekanik Klavye", "USB-C Hub 7-in-1", "HDMI Kablo 3m", "Laptop Soğutucu", "Ergonomik Mouse Pad", "Webcam 1080p", "Bluetooth Kulaklık", "Harici Disk 1TB", "Flash Bellek 128GB"]
        mobilya = ["Ergonomik Çalışma Koltuğu", "Yönetici Masası", "Toplantı Masası (8 Kişilik)", "Kesekonlu Dolap", "Kitaplık Ahşap", "Misafir Koltuğu", "Bekleme Salonu Kanepesi", "Metal Dosya Dolabı", "Keson", "Çalışma Masası"]
        hirdavat = ["Matkap Seti", "Tornavida Takımı (12'li)", "Pense ve Yan Keski Seti", "Şerit Metre 5m", "Çekiç", "İngiliz Anahtarı", "Alyan Seti", "Silikon Tabancası", "Vida ve Dübel Seti", "Maket Bıçağı Profesyonel"]
        
        stoklar = []
        for i in range(1, 101):
            kat = random.choice(kategori_list)
            if kat == "Elektronik": base_name = random.choice(elektronik)
            elif kat == "Ofis Malzemeleri": base_name = random.choice(ofis)
            elif kat == "Aksesuar & Sarf": base_name = random.choice(aksesuar)
            elif kat == "Mobilya": base_name = random.choice(mobilya)
            else: base_name = random.choice(hirdavat)
            
            ad = f"{base_name} - Model {random.randint(100, 999)}"
            adet = 0 # Will be populated dynamically
            stoklar.append((ad, kat, adet))
            
        cursor.executemany("INSERT INTO stok (ad, kategori, adet) VALUES (?, ?, ?)", stoklar)
        cursor.execute("SELECT id, ad, kategori, adet FROM stok")
        seeded_stoklar = [dict(r) for r in cursor.fetchall()]
        stok_counts = {s['id']: 0 for s in seeded_stoklar}

        # 4. Generate 3000 Documents
        start_date = date(2025, 1, 1)
        end_date = date(2026, 7, 30)
        days_diff = (end_date - start_date).days
        
        fis_count = 1
        doc_count = 1
        
        # Prepare bulk inserts to be efficient
        batch_depo = []
        batch_stok_islem = []
        batch_cari_islem = []
        batch_odeme = []
        batch_kasa = []
        
        for _ in range(3000):
            c = random.choice(seeded_cariler)
            c_id = c['id']
            c_ad = c['ad']
            c_tip = c['tip']
            
            random_days = random.randint(0, days_diff)
            doc_date = start_date + timedelta(days=random_days)
            doc_date_str = doc_date.isoformat()
            
            is_waybill = random.random() < 0.2
            
            if is_waybill:
                # İrsaliye
                belge_no = f"IR-{doc_date.year}-{fis_count:05d}"
                fis_count += 1
                durum = 'Teslim Edildi'
                tanim = f"{belge_no} — {c_ad} | Sevk İrsaliyesi"
                
                cursor.execute("""
                    INSERT INTO fatura_irsaliye (cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (c_id, belge_no, 'irsaliye', tanim, 0.0, durum, doc_date_str))
                irsaliye_id = cursor.lastrowid
                
                # Multiple products per waybill
                num_products = random.randint(1, 5)
                for _ in range(num_products):
                    linked_stok = random.choice(seeded_stoklar)
                    stok_id = linked_stok['id']
                    stok_ad = linked_stok['ad']
                    stok_qty = random.randint(1, 50)
                    stok_tip = 'cikis' if c_tip == 'musteri' else 'giris'
                    stok_tip_label = "Çıkış (Satış)" if stok_tip == 'cikis' else "Giriş (Alım)"
                    
                    batch_depo.append((stok_id, belge_no, stok_tip, stok_qty, doc_date_str, f"{c_ad} sevk irsaliyesi", irsaliye_id))
                    batch_stok_islem.append((f"{stok_ad} — {stok_qty} Adet {stok_tip_label}", stok_tip, doc_date_str))
                    
                    if stok_tip == 'giris': stok_counts[stok_id] += stok_qty
                    else: stok_counts[stok_id] -= stok_qty
            else:
                # Fatura
                prefix = f"FT-{doc_date.year}-S" if c_tip == 'musteri' else f"FT-{doc_date.year}-A"
                belge_no = f"{prefix}{doc_count:05d}"
                doc_count += 1
                
                belge_turu = 'satis_faturasi' if c_tip == 'musteri' else 'alis_faturasi'
                tutar = round(random.uniform(500.0, 150000.0), 2)
                # 80% paid for older invoices
                prob_paid = 0.8 if doc_date < date(2026, 6, 1) else 0.4
                durum = 'Ödendi' if random.random() < prob_paid else 'Ödenmedi'
                
                fatura_tanim = "Satış Faturası" if c_tip == 'musteri' else "Alım Faturası"
                tanim = f"{belge_no} — {c_ad} | {fatura_tanim}"
                
                cursor.execute("""
                    INSERT INTO fatura_irsaliye (cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (c_id, belge_no, belge_turu, tanim, tutar, durum, doc_date_str))
                fatura_id = cursor.lastrowid
                
                cari_islem_tip = 'alacak' if c_tip == 'musteri' else 'borc'
                odeme_tarihi = None
                
                if durum == 'Ödendi':
                    pay_day = doc_date + timedelta(days=random.randint(1, 45))
                    odeme_tarihi = pay_day.isoformat()
                    
                batch_cari_islem.append((c_id, tanim, tutar, cari_islem_tip, doc_date_str, odeme_tarihi))
                
                op_tip = 'gelir' if c_tip == 'musteri' else 'borç'
                vade = doc_date + timedelta(days=30)
                
                if durum == 'Ödenmedi':
                    op_durum = 'Gecikti' if vade < date.today() else 'Bekliyor'
                    kalan = tutar
                else:
                    op_durum = 'Ödendi'
                    kalan = 0.0
                    
                batch_odeme.append((c_ad, tutar, kalan, op_tip, vade.isoformat(), f"{belge_no} nolu fatura vadesi", op_durum))
                
                if durum == 'Ödendi':
                    linked_account = random.choice(seeded_hesaplar)
                    h_ad = linked_account['ad']
                    
                    kb_tip = 'giris' if c_tip == 'musteri' else 'cikis'
                    islem_turu = 'tahsilat' if c_tip == 'musteri' else 'odeme'
                    kb_tanim = f"{belge_no} Fatura Tahsilatı" if c_tip == 'musteri' else f"{belge_no} Fatura Ödemesi"
                    
                    batch_kasa.append((linked_account['id'], c_id, fatura_id, kb_tanim, tutar, kb_tip, odeme_tarihi, islem_turu))
                    pay_cari_tip = 'borc' if c_tip == 'musteri' else 'alacak'
                    batch_cari_islem.append((c_id, f"{h_ad} — {kb_tanim}", tutar, pay_cari_tip, odeme_tarihi, odeme_tarihi))

        # Bulk inserts
        cursor.executemany("INSERT INTO depo_hareket (stok_id, fis_no, tip, miktar, tarih, aciklama, irsaliye_id) VALUES (?, ?, ?, ?, ?, ?, ?)", batch_depo)
        cursor.executemany("INSERT INTO stok_islem (tanim, tip, tarih) VALUES (?, ?, ?)", batch_stok_islem)
        cursor.executemany("INSERT INTO cari_islem (cari_id, tanim, tutar, tip, tarih, odeme_tarihi) VALUES (?, ?, ?, ?, ?, ?)", batch_cari_islem)
        cursor.executemany("INSERT INTO odeme_plani (cari_ad, tutar, kalan_tutar, tip, tarih, aciklama, durum) VALUES (?, ?, ?, ?, ?, ?, ?)", batch_odeme)
        cursor.executemany("INSERT INTO kasa_banka_islem (hesap_id, cari_id, fatura_id, tanim, tutar, tip, tarih, islem_turu) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", batch_kasa)

        # General expenses
        gider_batch = []
        for i in range(100):
            doc_date = start_date + timedelta(days=random.randint(0, days_diff))
            acc = random.choice(seeded_hesaplar)
            gider_batch.append((acc['id'], None, None, f"Genel Ofis Gideri (#{i})", round(random.uniform(200, 3000), 2), 'cikis', doc_date.isoformat(), 'gider'))
        cursor.executemany("INSERT INTO kasa_banka_islem (hesap_id, cari_id, fatura_id, tanim, tutar, tip, tarih, islem_turu) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", gider_batch)
        
        # Sync Kasa balances
        for h in seeded_hesaplar:
            cursor.execute("SELECT SUM(CASE WHEN tip='giris' THEN tutar ELSE -tutar END) FROM kasa_banka_islem WHERE hesap_id = ?", (h['id'],))
            bakiye = cursor.fetchone()[0] or 0.0
            cursor.execute("UPDATE kasa_banka_hesap SET bakiye = ? WHERE id = ?", (round(bakiye, 2), h['id']))
            
        # Sync Stok counts
        for s_id, count in stok_counts.items():
            cursor.execute("UPDATE stok SET adet = ? WHERE id = ?", (max(0, count), s_id))
            
        conn.commit()
        conn.close()
    # Ek stok ve fatura verilerini ayrı bağlantıyla ekle (idempotent)
    _seed_extra_stok_fatura()


def _seed_extra_stok_fatura():
    """
    Disabled to maintain absolute data integrity and interrelation generated by the main seed logic.
    """
    pass


# --- Domain Query Functions ---

def get_dashboard_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Cari calculations
    cursor.execute("SELECT COUNT(*) FROM cari WHERE tip = 'musteri'")
    musteri_sayisi = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM cari WHERE tip = 'tedarikci'")
    tedarikci_sayisi = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(limit_val) FROM cari WHERE tip = 'musteri'")
    toplam_alacak = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(limit_val) FROM cari WHERE tip = 'tedarikci'")
    toplam_borc = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT id, tanim, tutar, tip, tarih FROM cari_islem ORDER BY tarih DESC, id DESC LIMIT 5")
    cari_islemler = [dict(row) for row in cursor.fetchall()]
    
    # 2. Kasa ve Banka calculations
    cursor.execute("SELECT SUM(bakiye) FROM kasa_banka_hesap WHERE tur = 'kasa'")
    kasa_bakiye = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(bakiye) FROM kasa_banka_hesap WHERE tur = 'banka'")
    banka_bakiye = cursor.fetchone()[0] or 0.0
    toplam_nakit = kasa_bakiye + banka_bakiye
    
    # Monthly Cashflow calculation (July 2026)
    cursor.execute("SELECT SUM(tutar) FROM kasa_banka_islem WHERE tip = 'giris' AND tarih LIKE '2026-07%'")
    aylik_gelir = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(tutar) FROM kasa_banka_islem WHERE tip = 'cikis' AND tarih LIKE '2026-07%'")
    aylik_gider = cursor.fetchone()[0] or 0.0
    
    cursor.execute('''
        SELECT islem.id, islem.tanim, islem.tutar, islem.tip, islem.tarih, hesap.ad as hesap_ad 
        FROM kasa_banka_islem islem 
        JOIN kasa_banka_hesap hesap ON islem.hesap_id = hesap.id 
        ORDER BY islem.tarih DESC, islem.id DESC LIMIT 5
    ''')
    kasa_islemler = [dict(row) for row in cursor.fetchall()]
    
    monthly_chart = get_monthly_liquidity_data()
    
    # 3. Stok calculations
    cursor.execute("SELECT COUNT(*) FROM stok")
    toplam_urun_cesidi = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stok WHERE adet < 15")
    kritik_stok_sayisi = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stok WHERE adet = 0")
    stoksuz_urun_sayisi = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(adet) FROM stok")
    total_stok_adet_db = cursor.fetchone()[0] or 0
    depo_doluluk_orani = min(100.0, round((total_stok_adet_db / 5000.0) * 100, 1))
    
    # Categories distribution
    cursor.execute("SELECT kategori, SUM(adet) as total FROM stok GROUP BY kategori")
    cat_rows = cursor.fetchall()
    
    kategoriler = []
    base_cats = {}
    
    for row in cat_rows:
        cat_name = row['kategori']
        base_cats[cat_name] = row['total']
            
    total_stok_adet = sum(base_cats.values())
    for cat_name, qty in base_cats.items():
        ratio = round((qty / total_stok_adet) * 100, 1) if total_stok_adet > 0 else 0
        kategoriler.append({"ad": cat_name, "oran": ratio, "adet": qty})
        
    cursor.execute("""
        SELECT h.id, s.ad || ' - ' || h.aciklama as tanim, h.tip, h.tarih 
        FROM depo_hareket h
        JOIN stok s ON h.stok_id = s.id
        ORDER BY h.tarih DESC, h.id DESC LIMIT 5
    """)
    stok_islemler = [dict(row) for row in cursor.fetchall()]
    
    # 4. Fatura ve Irsaliye calculations
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye WHERE durum = 'Ödenmedi'")
    odenmemis_fatura = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye WHERE durum = 'Bekliyor'")
    bekleyen_irsaliye = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye")
    kesilen_fatura_bu_ay = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(tutar) FROM fatura_irsaliye WHERE durum != 'Bekliyor'")
    db_fatura_sum = cursor.fetchone()[0] or 0.0
    aylik_fatura_tutari = db_fatura_sum
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye WHERE durum = 'Taslak'")
    taslak_fatura = cursor.fetchone()[0]
    
    cursor.execute("SELECT id, tanim, tutar, durum, tarih FROM fatura_irsaliye ORDER BY id DESC LIMIT 5")
    fatura_islemler = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT id, ad FROM cari")
    tum_cariler = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "cari": {
            "musteri_sayisi": musteri_sayisi,
            "tedarikci_sayisi": tedarikci_sayisi,
            "toplam_alacak": toplam_alacak,
            "toplam_borc": toplam_borc,
            "son_islemler": cari_islemler,
            "tum_liste": tum_cariler
        },
        "kasa_banka": {
            "kasa_bakiye": kasa_bakiye,
            "banka_bakiye": banka_bakiye,
            "toplam_nakit": toplam_nakit,
            "aylik_gelir": aylik_gelir,
            "aylik_gider": aylik_gider,
            "son_islemler": kasa_islemler,
            "monthly_chart": monthly_chart
        },
        "stok": {
            "toplam_urun_cesidi": toplam_urun_cesidi,
            "kritik_stok_sayisi": kritik_stok_sayisi,
            "stoksuz_urun_sayisi": stoksuz_urun_sayisi,
            "depo_doluluk_orani": depo_doluluk_orani,
            "kategoriler": kategoriler,
            "son_islemler": stok_islemler
        },
        "fatura_irsaliye": {
            "taslak_fatura": taslak_fatura,
            "odenmemis_fatura": odenmemis_fatura,
            "kesilen_fatura_bu_ay": kesilen_fatura_bu_ay,
            "bekleyen_irsaliye": bekleyen_irsaliye,
            "aylik_fatura_tutari": aylik_fatura_tutari,
            "son_islemler": fatura_islemler
        }
    }

def get_all_cariler():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch cariler
    cursor.execute("SELECT id, ad, tip, limit_val, vergi_no, vergi_dairesi, yetkili_kisi, eposta, telefon, il, ilce, mahalle, adres_detay, cari_grubu, kredibilite FROM cari ORDER BY id ASC")
    cariler = [dict(row) for row in cursor.fetchall()]
    
    # Calculate dynamic balance for each cari
    for c in cariler:
        c_id = c['id']
        is_musteri = c['tip'] == 'musteri'
        
        cursor.execute("SELECT tutar, tip FROM cari_islem WHERE cari_id = ?", (c_id,))
        transactions = cursor.fetchall()
        
        total_invoices = 0
        total_payments = 0
        
        for t in transactions:
            t_tip = t['tip']
            t_tutar = t['tutar'] or 0.0
            
            if is_musteri:
                if t_tip == 'alacak':
                    total_invoices += t_tutar
                elif t_tip == 'borc':
                    total_payments += t_tutar
            else:
                if t_tip == 'borc':
                    total_invoices += t_tutar
                elif t_tip == 'alacak':
                    total_payments += t_tutar
                    
        # Net balance: for customer positive means receivable (alacak), negative means overpaid/payable.
        # for supplier positive means debt (borc), negative means overpaid/receivable.
        c['bakiye'] = round(total_invoices - total_payments, 2)
        
    conn.close()
    return cariler

def get_cari_detail_and_history(cari_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch Cari Details
    cursor.execute("SELECT * FROM cari WHERE id = ?", (cari_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    cari_info = dict(row)
    
    # 2. Fetch Invoices and Payments combined via UNION
    # We map tip to 'borc' or 'alacak' based on cari tip
    # For a Müşteri: satis_faturasi -> borc, tahsilat -> alacak
    # For a Tedarikçi: alis_faturasi -> alacak, odeme -> borc
    query = """
        SELECT 
            'fatura' as kaynak,
            id as belge_id,
            belge_no,
            tarih,
            tanim as aciklama,
            tutar,
            durum,
            belge_turu as islem_tipi
        FROM fatura_irsaliye
        WHERE cari_id = ?
        
        UNION ALL
        
        SELECT 
            'odeme' as kaynak,
            id as belge_id,
            'MKZ-' || id as belge_no,
            tarih,
            tanim as aciklama,
            tutar,
            'Onaylandı' as durum,
            islem_turu as islem_tipi
        FROM kasa_banka_islem
        WHERE cari_id = ?
        
        ORDER BY tarih DESC, belge_id DESC
    """
    cursor.execute(query, (cari_id, cari_id))
    raw_transactions = [dict(r) for r in cursor.fetchall()]
    
    # Add legacy cari_islem just in case there are old seeded data
    cursor.execute("SELECT id as belge_id, 'cari_islem' as kaynak, 'ESKI-' || id as belge_no, tarih, tanim as aciklama, tutar, 'Eski Kayıt' as durum, tip as islem_tipi FROM cari_islem WHERE cari_id = ?", (cari_id,))
    legacy = [dict(r) for r in cursor.fetchall()]
    
    transactions = raw_transactions + legacy
    # Sort again in Python to merge legacy dates properly
    transactions.sort(key=lambda x: (x['tarih'], x['belge_id']), reverse=True)
    
    # Determine borc/alacak for UI rendering
    is_musteri = (cari_info['tip'] == 'musteri')
    
    for t in transactions:
        t_tip = t['islem_tipi']
        kaynak = t['kaynak']
        
        # Default mapping
        if kaynak == 'cari_islem':
            t['yon'] = t_tip # 'borc' or 'alacak'
        else:
            if is_musteri:
                if t_tip in ['satis_faturasi', 'borc']: t['yon'] = 'borc'
                elif t_tip in ['tahsilat', 'alacak']: t['yon'] = 'alacak'
                elif t_tip == 'irsaliye': t['yon'] = 'bilgi'
                else: t['yon'] = 'bilgi'
            else:
                if t_tip in ['alis_faturasi', 'alacak']: t['yon'] = 'alacak'
                elif t_tip in ['odeme', 'borc']: t['yon'] = 'borc'
                elif t_tip == 'irsaliye': t['yon'] = 'bilgi'
                else: t['yon'] = 'bilgi'
    
    conn.close()
    return {
        "cari": cari_info,
        "transactions": transactions
    }

def get_payment_plan(start_date=None, end_date=None, tip=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, cari_ad, tutar, kalan_tutar, tip, tarih, aciklama, durum FROM odeme_plani WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND tarih >= ?"
        params.append(start_date)
    if end_date:
        query += " AND tarih <= ?"
        params.append(end_date)
    if tip and tip != 'all':
        query += " AND tip = ?"
        params.append(tip)
        
    query += " ORDER BY tarih ASC"
    
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    
    # Metric cards: outstanding (kalan) for gelecek/gidecek, paid (odenen) for denge
    total_gelir = sum(r['kalan_tutar'] for r in rows if r['tip'] == 'gelir')
    total_borç = sum(r['kalan_tutar'] for r in rows if r['tip'] == 'borç')
    toplam_odenen = sum(r['tutar'] - r['kalan_tutar'] for r in rows)
    net_denge = total_gelir - total_borç
    
    conn.close()
    return {
        "liste": rows,
        "toplam_gelir": total_gelir,
        "toplam_borç": total_borç,
        "toplam_odenen": toplam_odenen,
        "net_denge": net_denge
    }

def add_cari_record(ad, tip, limit_val, vergi_no, vergi_dairesi, yetkili_kisi, eposta, telefon, il, ilce, mahalle, adres_detay, cari_grubu, kredibilite='A'):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO cari (ad, tip, limit_val, vergi_no, vergi_dairesi, yetkili_kisi, eposta, telefon, il, ilce, mahalle, adres_detay, cari_grubu, kredibilite)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (ad, tip, limit_val, vergi_no, vergi_dairesi, yetkili_kisi, eposta, telefon, il, ilce, mahalle, adres_detay, cari_grubu, kredibilite))
    
    cari_id = cursor.lastrowid
    
    islem_tip = 'alacak' if tip == 'musteri' else 'borc'
    tanim = f"{ad} ({'Müşteri' if tip == 'musteri' else 'Tedarikçi'}) Eklendi"
    
    cursor.execute("INSERT INTO cari_islem (cari_id, tanim, tutar, tip, tarih) VALUES (?, ?, ?, ?, '2026-07-18')", 
                   (cari_id, tanim, limit_val, islem_tip))
    
    conn.commit()
    conn.close()

def get_cari_islem_history_range(start_date=None, end_date=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, tanim, tutar, tip, tarih FROM cari_islem WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND tarih >= ?"
        params.append(start_date)
    if end_date:
        query += " AND tarih <= ?"
        params.append(end_date)
    
    # Sort with most recent date first
    query += " ORDER BY tarih DESC, id DESC"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    
    total_alacak = sum(r['tutar'] for r in rows if r['tip'] == 'alacak')
    total_borc = sum(r['tutar'] for r in rows if r['tip'] == 'borc')
    net_denge = total_alacak - total_borc
    
    conn.close()
    return {
        "liste": rows,
        "total_alacak": total_alacak,
        "total_borc": total_borc,
        "net_denge": net_denge
    }

def get_kasa_banka_accounts(tur=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if tur:
        cursor.execute("SELECT * FROM kasa_banka_hesap WHERE tur = ?", (tur,))
    else:
        cursor.execute("SELECT * FROM kasa_banka_hesap")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_account_detail_and_history(account_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kasa_banka_hesap WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    account_info = dict(row)
    
    cursor.execute('''
        SELECT islem.id, islem.tanim, islem.tutar, islem.tip, islem.tarih, islem.islem_turu, cari.ad as cari_ad 
        FROM kasa_banka_islem islem 
        LEFT JOIN cari ON islem.cari_id = cari.id 
        WHERE islem.hesap_id = ? 
        ORDER BY islem.tarih DESC, islem.id DESC
    ''', (account_id,))
    transactions = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {
        "hesap": account_info,
        "transactions": transactions
    }

def add_kasa_banka_account_record(ad, tur, hesap_no, iban, sube, doviz_turu, kredibilite='A'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO kasa_banka_hesap (ad, tur, hesap_no, iban, sube, doviz_turu, bakiye, kredibilite)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?)
    ''', (ad, tur, hesap_no, iban, sube, doviz_turu, kredibilite))
    conn.commit()
    conn.close()

def add_kasa_banka_transaction_record(hesap_id, cari_id, tanim, tutar, islem_turu, tarih):
    conn = get_db_connection()
    cursor = conn.cursor()
    tip = 'giris' if tutar > 0 else 'cikis'
    
    # Get account info
    cursor.execute("SELECT ad, tur FROM kasa_banka_hesap WHERE id = ?", (hesap_id,))
    acc = cursor.fetchone()
    h_ad = acc['ad'] if acc else 'Bilinmeyen'
    
    cursor.execute('''
        INSERT INTO kasa_banka_islem (hesap_id, cari_id, tanim, tutar, tip, tarih, islem_turu)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (hesap_id, cari_id, tanim, abs(tutar), tip, tarih, islem_turu))
    
    # Update balance
    cursor.execute("SELECT SUM(CASE WHEN tip='giris' THEN tutar ELSE -tutar END) FROM kasa_banka_islem WHERE hesap_id = ?", (hesap_id,))
    bakiye = cursor.fetchone()[0] or 0.0
    cursor.execute("UPDATE kasa_banka_hesap SET bakiye = ? WHERE id = ?", (bakiye, hesap_id))
    
    # If linked to a Cari, also log a Cari transaction!
    if cari_id:
        cari_tip = 'borc' if tip == 'giris' else 'alacak'
        cursor.execute('''
            INSERT INTO cari_islem (cari_id, tanim, tutar, tip, tarih)
            VALUES (?, ?, ?, ?, ?)
        ''', (cari_id, f"{h_ad} - {tanim}", abs(tutar), cari_tip, tarih))
        
    conn.commit()
    conn.close()

def get_kasa_banka_islem_history(hesap_id=None, start_date=None, end_date=None, tur=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT islem.id, islem.tanim, islem.tutar, islem.tip, islem.tarih, islem.islem_turu, hesap.ad as hesap_ad, hesap.tur as hesap_tur, hesap.doviz_turu
        FROM kasa_banka_islem islem
        JOIN kasa_banka_hesap hesap ON islem.hesap_id = hesap.id
        WHERE 1=1
    '''
    params = []
    
    if hesap_id:
        query += " AND islem.hesap_id = ?"
        params.append(hesap_id)
    if start_date:
        query += " AND islem.tarih >= ?"
        params.append(start_date)
    if end_date:
        query += " AND islem.tarih <= ?"
        params.append(end_date)
    if tur and tur != 'all':
        query += " AND hesap.tur = ?"
        params.append(tur)
        
    query += " ORDER BY islem.tarih DESC, islem.id DESC"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    
    total_giris = sum(r['tutar'] for r in rows if r['tip'] == 'giris')
    total_cikis = sum(r['tutar'] for r in rows if r['tip'] == 'cikis')
    net_denge = total_giris - total_cikis
    
    conn.close()
    return {
        "liste": rows,
        "total_giris": total_giris,
        "total_cikis": total_cikis,
        "net_denge": net_denge
    }

def get_monthly_liquidity_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT substr(tarih, 1, 7) as ay,
               SUM(CASE WHEN tip='giris' THEN tutar ELSE 0 END) as gelir,
               SUM(CASE WHEN tip='cikis' THEN tutar ELSE 0 END) as gider
        FROM kasa_banka_islem
        GROUP BY ay
        ORDER BY ay ASC
    ''')
    rows = cursor.fetchall()
    
    months = []
    gelirler = []
    giderler = []
    
    month_names = {
        "01": "Ocak", "02": "Şubat", "03": "Mart", "04": "Nisan",
        "05": "Mayıs", "06": "Haziran", "07": "Temmuz", "08": "Ağustos",
        "09": "Eylül", "10": "Ekim", "11": "Kasım", "12": "Aralık"
    }
    
    for row in rows:
        ay_str = row['ay']
        if '-' in ay_str:
            month_part = ay_str.split('-')[1]
            if month_part in month_names:
                months.append(month_names[month_part] + " " + ay_str.split('-')[0])
                gelirler.append(row['gelir'] or 0.0)
                giderler.append(row['gider'] or 0.0)
    
    conn.close()
    return {
        "labels": months,
        "gelirler": gelirler,
        "giderler": giderler
    }

def add_kasa_transaction(tanim, tutar, hesap):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fallback compat mapping: get first account of type
    cursor.execute("SELECT id FROM kasa_banka_hesap WHERE tur = ? LIMIT 1", (hesap,))
    row = cursor.fetchone()
    h_id = row[0] if row else 1
    
    conn.close()
    add_kasa_banka_transaction_record(h_id, None, tanim, tutar, 'gelir' if tutar > 0 else 'gider', '2026-07-18')

def add_stok_item(ad, kategori, adet):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO stok (ad, kategori, adet) VALUES (?, ?, ?)", (ad, kategori, adet))
    
    log_tanim = f"{ad} - {adet} Adet Eklendi ({kategori})"
    cursor.execute("INSERT INTO stok_islem (tanim, tip, tarih) VALUES (?, 'giris', '2026-07-18')", (log_tanim,))
    
    conn.commit()
    conn.close()

def add_fatura_record(unvan, tutar, tip):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye")
    f_count = cursor.fetchone()[0] + 109
    prefix = "FT-2026-S" if tip == 'satis' else "FT-2026-A"
    fatura_no = f"{prefix}{f_count:05d}"
    
    log_tanim = f"{fatura_no} - {unvan} Faturası Düzenlendi"
    cursor.execute("INSERT INTO fatura_irsaliye (tanim, tutar, durum, tarih) VALUES (?, ?, 'Ödenmedi', '2026-07-18')", 
                   (log_tanim, tutar))
    
    conn.commit()
    conn.close()

def get_fatura_irsaliye_list(start_date=None, end_date=None, durum=None, tip=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih FROM fatura_irsaliye WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND tarih >= ?"
        params.append(start_date)
    if end_date:
        query += " AND tarih <= ?"
        params.append(end_date)
    if durum and durum != 'tumu':
        query += " AND durum = ?"
        params.append(durum)
        
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    
    result = []
    for r in rows:
        tanim = r['tanim']
        tutar = float(r['tutar'] or 0)
        
        belge_turu_db = r['belge_turu']
        belge_no_db = r['belge_no']
        
        if belge_turu_db:
            belge_turu = belge_turu_db
            if belge_turu == 'irsaliye': belge_label = "Sevk İrsaliyesi"
            elif belge_turu == 'alis_faturasi': belge_label = "Alış Faturası"
            elif belge_turu == 'irsaliyeli_fatura': belge_label = "İrsaliyeli Fatura"
            else: belge_label = "Satış Faturası"
        else:
            if "Sevk İrsaliyesi" in tanim or "IR-" in tanim or "Sevkiyat" in tanim:
                belge_turu = "irsaliye"
                belge_label = "Sevk İrsaliyesi"
            elif "Alış" in tanim or "A00" in tanim:
                belge_turu = "alis"
                belge_label = "Alış Faturası"
            elif "İrsaliyeli" in tanim or "IF-" in tanim:
                belge_turu = "irsaliyeli_fatura"
                belge_label = "İrsaliyeli Fatura"
            else:
                belge_turu = "satis"
                belge_label = "Satış Faturası"
                
        if tip and tip != 'tumu':
            if tip == 'irsaliye' and belge_turu not in ['irsaliye', 'irsaliyeli_fatura']:
                continue
            elif tip == 'satis' and belge_turu not in ['satis', 'satis_faturasi']:
                continue
            elif tip == 'alis' and belge_turu not in ['alis', 'alis_faturasi']:
                continue

        belge_no = belge_no_db if belge_no_db else f"DOC-{r['id']:04d}"
        unvan = "Genel Cari"
        aciklama = tanim

        if " — " in tanim:
            parts = tanim.split(" — ", 1)
            if not belge_no_db: belge_no = parts[0].strip()
            rest = parts[1].strip()
            if " | " in rest:
                sub_parts = rest.split(" | ", 1)
                unvan = sub_parts[0].strip()
                aciklama = sub_parts[1].strip()
            else:
                unvan = rest
                aciklama = rest
        elif " - " in tanim:
            parts = tanim.split(" - ", 1)
            if not belge_no_db: belge_no = parts[0].strip()
            rest = parts[1].strip()
            if " | " in rest:
                sub_parts = rest.split(" | ", 1)
                unvan = sub_parts[0].strip()
                aciklama = sub_parts[1].strip()
            else:
                unvan = rest
                aciklama = rest
        
        r['cari_id'] = r['cari_id']

        r['belge_no'] = belge_no
        r['unvan'] = unvan
        r['aciklama'] = aciklama
        r['belge_turu'] = belge_turu
        r['belge_label'] = belge_label
        result.append(r)
        
    conn.close()
    return result

def add_fatura_irsaliye_full(cari_id, unvan, belge_no, tutar, tip, durum, tarih, aciklama=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye")
    count = cursor.fetchone()[0] + 115
    
    if tip == 'irsaliye':
        prefix = "IR-2026-"
        label = "Sevk İrsaliyesi"
        belge_turu = "irsaliye"
    elif tip == 'alis':
        prefix = "FT-2026-A"
        label = "Alış Faturası"
        belge_turu = "alis_faturasi"
    elif tip == 'irsaliyeli_fatura':
        prefix = "IF-2026-"
        label = "İrsaliyeli Fatura"
        belge_turu = "irsaliyeli_fatura"
    else:
        prefix = "FT-2026-S"
        label = "Satış Faturası"
        belge_turu = "satis_faturasi"
        
    code = belge_no if belge_no else f"{prefix}{count:05d}"
    detail_aciklama = aciklama if aciklama else label
    log_tanim = f"{code} — {unvan} | {detail_aciklama}"
        
    cursor.execute("INSERT INTO fatura_irsaliye (cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (cari_id, code, belge_turu, log_tanim, float(tutar), durum, tarih))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_fatura_status(fatura_id, yeni_durum):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE fatura_irsaliye SET durum = ? WHERE id = ?", (yeni_durum, fatura_id))
    conn.commit()
def delete_fatura_record(fatura_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fatura_irsaliye WHERE id = ?", (fatura_id,))
    conn.commit()
    conn.close()

# --- STOK & DEPO YÖNETİMİ ---
def get_stok_liste():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, ad, kategori, adet FROM stok ORDER BY ad ASC")
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data

def add_stok(ad, kategori, adet):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stok (ad, kategori, adet) VALUES (?, ?, ?)", (ad, kategori, int(adet)))
    new_id = cursor.lastrowid
    
    if int(adet) > 0:
        import datetime
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        fis_no = f"ACILIS-{new_id:04d}"
        cursor.execute("""
            INSERT INTO depo_hareket (stok_id, fis_no, tip, miktar, tarih, aciklama) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (new_id, fis_no, 'giris', int(adet), today, 'Açılış stoğu'))
        
    conn.commit()
    conn.close()
    return new_id

def get_stok_hareketler():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.id, h.stok_id, s.ad as stok_ad, h.fis_no, h.tip, h.miktar, h.tarih, h.aciklama 
        FROM depo_hareket h
        JOIN stok s ON h.stok_id = s.id
        ORDER BY h.id DESC LIMIT 200
    """)
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data

def add_stok_hareket(stok_id, tip, miktar, aciklama):
    import datetime
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Generate simple fis_no
    cursor.execute("SELECT COUNT(*) FROM depo_hareket")
    count = cursor.fetchone()[0] + 1
    fis_no = f"FIS-{count:05d}"
    
    # Check current stock
    cursor.execute("SELECT adet FROM stok WHERE id = ?", (stok_id,))
    stok_row = cursor.fetchone()
    if not stok_row:
        conn.close()
        return False, "Stok bulunamadı"
        
    mevcut_adet = stok_row['adet']
    miktar = int(miktar)
    
    # Calculate new stock
    yeni_adet = mevcut_adet
    if tip in ['giris', 'sayim_fazlasi']:
        yeni_adet += miktar
    elif tip in ['cikis', 'fire']:
        yeni_adet -= miktar
        
    if yeni_adet < 0:
        conn.close()
        return False, "Stok miktarı eksiye düşemez"
        
    # Insert movement
    cursor.execute("""
        INSERT INTO depo_hareket (stok_id, fis_no, tip, miktar, tarih, aciklama) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (stok_id, fis_no, tip, miktar, today, aciklama))
    
    # Update main stock
    cursor.execute("UPDATE stok SET adet = ? WHERE id = ?", (yeni_adet, stok_id))
    
    conn.commit()
    conn.close()
    return True, "Hareket işlendi"
