import sqlite3
import os
import datetime

DB_FILE = 'bulutis.db'

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
    
    # 2. Cari Islem Table with ISO Date & Cari Link
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cari_islem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_id INTEGER,
            tanim TEXT NOT NULL,
            tutar REAL DEFAULT 0,
            tip TEXT NOT NULL, -- 'alacak' veya 'borc' veya 'bilgi'
            tarih TEXT NOT NULL, -- YYYY-MM-DD format
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
            tanim TEXT NOT NULL,
            tutar REAL DEFAULT 0,
            tip TEXT NOT NULL, -- 'giris' veya 'cikis'
            tarih TEXT NOT NULL,
            islem_turu TEXT NOT NULL DEFAULT 'gelir', -- 'tahsilat', 'odeme', 'transfer', 'gelir', 'gider'
            FOREIGN KEY (hesap_id) REFERENCES kasa_banka_hesap(id) ON DELETE CASCADE,
            FOREIGN KEY (cari_id) REFERENCES cari(id) ON DELETE SET NULL
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
            tanim TEXT NOT NULL,
            tutar REAL DEFAULT 0,
            durum TEXT NOT NULL, -- 'Ödendi' veya 'Ödenmedi' veya 'Bekliyor'
            tarih TEXT NOT NULL
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
    
    # Check if empty to seed initial demo data
    cursor.execute("SELECT COUNT(*) FROM cari")
    if cursor.fetchone()[0] == 0:
        # Seed 22 Cari with limit values determined by credibility rating:
        # A+ -> 150.000 TL, A -> 100.000 TL, B -> 50.000 TL, C -> 15.000 TL, D -> 5.000 TL
        cariler = [
            ("Ahmet Yılmaz", "musteri", 150000.0, "12345678901", "Kadıköy V.D.", "Ahmet Yılmaz", "ahmet@yilmazinsaat.com", "0532 111 22 33", "İstanbul", "Kadıköy", "Caferağa Mah.", "Moda Cad. No:12 D:4", "İnşaat", "A+"),
            ("Ayşe Kaya", "musteri", 100000.0, "23456789012", "Beşiktaş V.D.", "Ayşe Kaya", "ayse@kayatasarim.com", "0533 222 33 44", "İstanbul", "Beşiktaş", "Sinanpaşa Mah.", "Ihlamurdere Cad. No:45", "Tasarım & Mimarlık", "A"),
            ("TeknoMarket A.Ş.", "musteri", 50000.0, "9876543210", "Zincirlikuyu V.D.", "Mehmet Demir", "info@teknomarket.com", "0212 555 44 33", "İstanbul", "Şişli", "Esentepe Mah.", "Büyükdere Cad. No:199", "Teknoloji", "B"),
            ("Vural İnşaat Ltd.", "musteri", 150000.0, "1122334455", "Ataşehir V.D.", "Caner Vural", "muhasebe@vuralinsaat.com", "0216 444 55 66", "İstanbul", "Ataşehir", "Barbaros Mah.", "Kardelen Sok. No:8/B", "İnşaat", "A+"),
            ("Zeynep Şahin", "musteri", 15000.0, "34567890123", "Bakırköy V.D.", "Zeynep Şahin", "zeynep@sahindanismanlik.com", "0535 333 44 55", "İstanbul", "Bakırköy", "Kartaltepe Mah.", "İncirli Cad. No:12", "Danışmanlık", "C"),
            ("Caner Demir", "musteri", 50000.0, "45678901234", "Kartal V.D.", "Caner Demir", "caner@demirmetal.com", "0536 444 55 66", "İstanbul", "Kartal", "Kordonboyu Mah.", "Ankara Cad. No:98", "Sanayi & Metal", "B"),
            ("Öztürk Gıda", "musteri", 100000.0, "2233445566", "Mecidiyeköy V.D.", "Fatih Öztürk", "siparis@ozturkgida.com", "0212 666 77 88", "İstanbul", "Kağıthane", "Merkez Mah.", "Sadabad Cad. No:4", "Gıda Toptan", "A"),
            ("Akdeniz Lojistik", "musteri", 150000.0, "3344556677", "Tuzla V.D.", "Selin Akdeniz", "operasyon@akdenizlojistik.com", "0216 777 88 99", "İstanbul", "Tuzla", "Aydınlı Mah.", "Liman Yolu No:89", "Lojistik & Nakliye", "A+"),
            ("Elif Çelik", "musteri", 50000.0, "56789012345", "Beyoğlu V.D.", "Elif Çelik", "elif@celikreklam.com", "0537 555 66 77", "İstanbul", "Beyoğlu", "Cihangir Mah.", "Sıraselviler Cad. No:20", "Reklam & Medya", "B"),
            ("Yıldız Mobilya", "musteri", 50000.0, "4455667788", "İkitelli V.D.", "Murat Yıldız", "destek@yildizmobilya.com", "0212 888 99 00", "İstanbul", "Başakşehir", "Ziya Gökalp Mah.", "İkitelli Org. San. No:5", "Mobilya Üretim", "B"),
            ("Maslak Yazılım", "musteri", 100000.0, "5566778899", "Maslak V.D.", "Deniz Koç", "hakedis@maslakyazilim.com", "0212 999 00 11", "İstanbul", "Sarıyer", "Maslak Mah.", "Maslak Link Plaza No:4", "Teknoloji", "A"),
            ("Beta Kimya", "musteri", 15000.0, "6677889900", "Gebze V.D.", "Kemal Sun", "kalite@betakimya.com", "0262 111 22 33", "Kocaeli", "Gebze", "Güzeller Mah.", "Gençlik Cad. No:14", "Kimya & Kozmetik", "C"),
            ("Mavi Mimarlık", "musteri", 100000.0, "7788990011", "Üsküdar V.D.", "Merve Mavi", "proje@mavimimarlik.com", "0216 333 44 55", "İstanbul", "Üsküdar", "Mimar Sinan Mah.", "Bosna Bulvarı No:110", "Tasarım & Mimarlık", "A"),
            ("Kaan Arslan", "musteri", 50000.0, "67890123456", "Pendik V.D.", "Kaan Arslan", "kaan@arslanmontaj.com", "0538 666 77 88", "İstanbul", "Pendik", "Batı Mah.", "Erol Kaya Cad. No:50", "Teknik Servis", "B"),
            
            # Suppliers (tedarikci)
            ("Doruk Toptan Gıda", "tedarikci", 100000.0, "1231231234", "Gıda İhtisas V.D.", "Mustafa Doruk", "bilgi@dorukgida.com", "0212 222 33 44", "İstanbul", "Esenler", "Menderes Mah.", "Toptancılar Sitesi B Blok No:14", "Gıda Tedarik", "A"),
            ("Çelik Hırdavat", "tedarikci", 50000.0, "2342342345", "Karaköy V.D.", "İbrahim Çelik", "satis@celikhirdavat.com", "0212 333 44 55", "İstanbul", "Fatih", "Kemalpaşa Mah.", "Karaköy Palas No:3", "Hırdavat & Yapı", "B"),
            ("Global Enerji A.Ş.", "tedarikci", 150000.0, "3453453456", "Büyük Mükellefler V.D.", "Fatma Enerji", "fatura@globalenerji.com", "0312 444 0 555", "Ankara", "Çankaya", "Kavaklıdere Mah.", "Atatürk Bulvarı No:250", "Enerji & Akaryakıt", "A+"),
            ("Alfa Ambalaj", "tedarikci", 50000.0, "4564564567", "Halkalı V.D.", "Ömer Alfa", "kutu@alfaambalaj.com", "0212 444 55 77", "İstanbul", "Küçükçekmece", "Halkalı Merkez Mah.", "Fatih Cad. No:99", "Ambalaj Sanayi", "B"),
            ("Mega Kağıtçılık", "tedarikci", 15000.0, "5675675678", "Topkapı V.D.", "Cemil Kağıt", "siparis@megakagit.com", "0212 555 66 88", "İstanbul", "Zeytinburnu", "Maltepe Mah.", "Litros Yolu No:10", "Kırtasiye & Sarf", "C"),
            ("Kuzey Tekstil", "tedarikci", 100000.0, "6786786789", "Güneşli V.D.", "Hasan Kuzey", "kumas@kuzeytekstil.com", "0212 666 77 99", "İstanbul", "Bağcılar", "Güneşli Mah.", "Evren Cad. No:64", "Tekstil & Hammadde", "A"),
            ("Ege Elektrik", "tedarikci", 50000.0, "7897897890", "İzmir Kordon V.D.", "Bülent Ege", "servis@egeelektrik.com", "0232 444 88 99", "İzmir", "Konak", "Alsancak Mah.", "Kordon Boyu No:2", "Elektrik Malzeme", "B"),
            ("Hilal Demir Sanayi", "tedarikci", 100000.0, "8908908901", "Karabük V.D.", "Ahmet Hilal", "demir@hilaldemir.com", "0370 444 11 22", "Karabük", "Merkez", "Yeşil Mah.", "Demir Çelik Bulvarı No:45", "Metal & Hammadde", "A")
        ]
        cursor.executemany('''
            INSERT INTO cari (ad, tip, limit_val, vergi_no, vergi_dairesi, yetkili_kisi, eposta, telefon, il, ilce, mahalle, adres_detay, cari_grubu, kredibilite)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', cariler)
        
        # Fetch seeded Cari info to get IDs programmatically
        cursor.execute("SELECT id, ad, tip FROM cari")
        all_seeded_cariler = cursor.fetchall()
        
        import random
        # Spreading dates starting from 2026-05-15 to 2026-07-18
        start_date = datetime.date(2026, 5, 15)
        
        # Programmatic generation of exactly 20 transactions per Cari
        # Total transactions seeded: 22 * 20 = 440 transactions
        cari_islemler = []
        for cari in all_seeded_cariler:
            c_id = cari['id']
            c_ad = cari['ad']
            c_tip = cari['tip']
            
            for i in range(1, 21):
                # Add randomized date spacing
                date_diff = i * 3 + random.randint(-1, 1)
                date_diff = max(1, date_diff)
                t_date = (start_date + datetime.timedelta(days=date_diff)).isoformat()
                
                if c_tip == 'musteri':
                    if i % 2 == 1:
                        # Sale/Receivable (randomized amount)
                        desc = f"{c_ad} - Ürün Satış Faturası düzenlendi (İşlem #{i})"
                        tutar = round(2000.0 + (i * random.randint(250, 450)) + random.random() * 99, 2)
                        tip = "alacak"
                    else:
                        # Collection/Payment received
                        desc = f"{c_ad} - Banka Havalesi İle Tahsilat (İşlem #{i})"
                        tutar = round(1800.0 + (i * random.randint(240, 440)) + random.random() * 99, 2)
                        tip = "borc"
                else: # Supplier
                    if i % 2 == 1:
                        # Purchase/Payable
                        desc = f"{c_ad} - Hammadde Satın Alım Faturası (İşlem #{i})"
                        tutar = round(2500.0 + (i * random.randint(400, 600)) + random.random() * 99, 2)
                        tip = "borc"
                    else:
                        # Payment made
                        desc = f"{c_ad} - Tedarikçi Ödemesi EFT (İşlem #{i})"
                        tutar = round(2400.0 + (i * random.randint(390, 590)) + random.random() * 99, 2)
                        tip = "alacak"
                
                cari_islemler.append((c_id, desc, tutar, tip, t_date))
                
        cursor.executemany("INSERT INTO cari_islem (cari_id, tanim, tutar, tip, tarih) VALUES (?, ?, ?, ?, ?)", cari_islemler)
        
        # Seed Kasa & Banka Hesap
        hesaplar = [
            ("Merkez Kasa", "kasa", None, None, None, "TRY", "A+"),
            ("Dış Saha Kasası", "kasa", None, None, None, "TRY", "B"),
            ("Döviz Kasası", "kasa", None, None, None, "USD", "A"),
            ("Akbank Ticari", "banka", "4489-012398", "TR450004600192384759281234", "Maslak", "TRY", "A+"),
            ("Garanti Şirket", "banka", "3320-998822", "TR920006200088112233445566", "Levent", "TRY", "A"),
            ("Ziraat TRY", "banka", "1102-445533", "TR560001000022334455667788", "Merkez", "TRY", "B"),
            ("Vakıfbank EUR", "banka", "7740-881100", "TR120001500158007788990011", "Kadıköy", "EUR", "A")
        ]
        for h in hesaplar:
            cursor.execute('''
                INSERT INTO kasa_banka_hesap (ad, tur, hesap_no, iban, sube, doviz_turu, bakiye, kredibilite)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            ''', h)
        
        # Fetch seeded accounts
        cursor.execute("SELECT id, ad, tur, doviz_turu FROM kasa_banka_hesap")
        all_seeded_hesaplar = cursor.fetchall()
        
        # Programmatic generation of 20 transactions per account (total 140)
        kasa_banka_islemler = []
        k_start_date = datetime.date(2026, 5, 15)
        
        for hesap in all_seeded_hesaplar:
            h_id = hesap['id']
            h_ad = hesap['ad']
            h_tur = hesap['tur']
            h_doviz = hesap['doviz_turu']
            
            for i in range(1, 21):
                date_diff = i * 3 + random.randint(-1, 1)
                date_diff = max(1, date_diff)
                t_date = (k_start_date + datetime.timedelta(days=date_diff)).isoformat()
                
                # Pick a random Cari to link to
                linked_cari = random.choice(all_seeded_cariler)
                cari_id = linked_cari['id']
                cari_ad = linked_cari['ad']
                
                if h_tur == 'kasa':
                    if i % 2 == 1:
                        # Cash income / receipt
                        tanim = f"Nakit Tahsilat - {cari_ad} (İşlem #{i})"
                        tutar = round(500.0 + (i * random.randint(100, 150)) + random.random() * 50, 2)
                        tip = 'giris'
                        islem_turu = 'tahsilat'
                    else:
                        # Cash expense
                        tanim = f"Nakit Ödeme (Ofis & Kırtasiye) - İşlem #{i}"
                        tutar = round(150.0 + (i * random.randint(20, 40)) + random.random() * 20, 2)
                        tip = 'cikis'
                        islem_turu = 'gider'
                        cari_id = None # Not related to a Cari
                else: # Bank account
                    if i % 2 == 1:
                        # Bank transfer in
                        tanim = f"{h_ad} Gelen EFT - {cari_ad} (Fatura Ödemesi #{i})"
                        tutar = round(5000.0 + (i * random.randint(1200, 1800)) + random.random() * 500, 2)
                        tip = 'giris'
                        islem_turu = 'tahsilat'
                    else:
                        # Bank transfer out
                        tanim = f"{h_ad} Gönderilen EFT - {cari_ad} (Tedarikçi Ödemesi #{i})"
                        tutar = round(3000.0 + (i * random.randint(700, 1100)) + random.random() * 300, 2)
                        tip = 'cikis'
                        islem_turu = 'odeme'
                
                kasa_banka_islemler.append((h_id, cari_id, tanim, tutar, tip, t_date, islem_turu))
        
        cursor.executemany('''
            INSERT INTO kasa_banka_islem (hesap_id, cari_id, tanim, tutar, tip, tarih, islem_turu)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', kasa_banka_islemler)
        
        # Update balances of accounts dynamically based on their transactions sum
        cursor.execute("SELECT id FROM kasa_banka_hesap")
        ids = [row[0] for row in cursor.fetchall()]
        for h_id in ids:
            cursor.execute("SELECT SUM(CASE WHEN tip='giris' THEN tutar ELSE -tutar END) FROM kasa_banka_islem WHERE hesap_id = ?", (h_id,))
            bakiye = cursor.fetchone()[0] or 0.0
            cursor.execute("UPDATE kasa_banka_hesap SET bakiye = ? WHERE id = ?", (bakiye, h_id))
        
        # Seed Stok
        stoklar = [
            ("Dell Latitude 5540", "Elektronik", 496),
            ("Ergonomik Ofis Koltuğu", "Ofis Malzemeleri", 434),
            ("Kablosuz Mouse", "Aksesuar & Sarf", 310)
        ]
        cursor.executemany("INSERT INTO stok (ad, kategori, adet) VALUES (?, ?, ?)", stoklar)
        
        # Seed Stok Islem
        stok_islemler = [
            ("Dell Latitude 5540 - 10 Adet Giriş", "giris", "2026-07-18"),
            ("Ergonomik Ofis Koltuğu - 5 Adet Çıkış", "cikis", "2026-07-18"),
            ("Kablosuz Mouse - Stok Alarmı (Kritik Eşik)", "alarm", "2026-07-17")
        ]
        cursor.executemany("INSERT INTO stok_islem (tanim, tip, tarih) VALUES (?, ?, ?)", stok_islemler)
        
        # Seed Fatura & Irsaliye
        faturalar = [
            ("FT-2026-00045 - Satış Faturası Oluşturuldu", 18500.0, "Ödenmedi", "2026-07-18"),
            ("IR-2026-00021 - Sevk İrsaliyesi Hazırlandı", 0, "Bekliyor", "2026-07-18"),
            ("FT-2026-00044 - Alış Faturası Kaydedildi", 22000.0, "Ödendi", "2026-07-17"),
            ("FT-2026-00043 - Hizmet Faturası Ödendi", 3500.0, "Ödendi", "2026-07-14")
        ]
        cursor.executemany("INSERT INTO fatura_irsaliye (tanim, tutar, durum, tarih) VALUES (?, ?, ?, ?)", faturalar)

        # Seed 50+ payment plan items (Receivables & Payables)
        odeme_listesi = [
            ("Ahmet Yılmaz", 5379.03, "gelir", "2026-07-20", "Ürün Satış Bedeli", "Bekliyor"),
            ("Ayşe Kaya", 3089.23, "gelir", "2026-07-22", "Hizmet Bedeli Tahsilatı", "Bekliyor"),
            ("TeknoMarket A.Ş.", 16105.23, "gelir", "2026-07-25", "Yarı Yıl Hak Edişi", "Kısmi Ödendi"),
            ("Vural İnşaat Ltd.", 43302.14, "gelir", "2026-07-30", "Şantiye Destek Bedeli", "Bekliyor"),
            ("Zeynep Şahin", 1322.41, "gelir", "2026-08-02", "Danışmanlık Hizmeti", "Bekliyor"),
            ("Caner Demir", 10084.82, "gelir", "2026-08-05", "Malzeme Satışı", "Bekliyor"),
            ("Öztürk Gıda", 13988.1, "gelir", "2026-08-10", "Toptan Gıda Satış Bedeli", "Bekliyor"),
            ("Akdeniz Lojistik", 41143.42, "gelir", "2026-08-15", "Taşıma Hizmet Bedeli", "Bekliyor"),
            ("Elif Çelik", 4686.38, "gelir", "2026-08-18", "Tasarım Proje Tahsilatı", "Bekliyor"),
            ("Yıldız Mobilya", 30786.01, "gelir", "2026-08-22", "Ofis Mobilyaları Satışı", "Bekliyor"),
            ("Maslak Yazılım", 31901.05, "gelir", "2026-08-25", "Yazılım Geliştirme Bedeli", "Kısmi Ödendi"),
            ("Beta Kimya", 17823.77, "gelir", "2026-08-28", "Kimyasal Madde Satışı", "Bekliyor"),
            ("Mavi Mimarlık", 22003.91, "gelir", "2026-09-02", "Proje Çizim Bedeli", "Bekliyor"),
            ("Kaan Arslan", 7806.96, "gelir", "2026-09-05", "Montaj Hizmet Tahsilatı", "Bekliyor"),
            ("Ahmet Yılmaz", 4724.26, "gelir", "2026-09-10", "Ek Sipariş Ödemesi", "Bekliyor"),
            ("TeknoMarket A.Ş.", 31046.12, "gelir", "2026-09-15", "Donanım Teslimat Bedeli", "Bekliyor"),
            ("Vural İnşaat Ltd.", 84021.4, "gelir", "2026-09-25", "2. Etap Hak Ediş Ödemesi", "Bekliyor"),
            ("Öztürk Gıda", 21521.63, "gelir", "2026-10-01", "Gıda Sevkiyat Ödemesi", "Bekliyor"),
            ("Akdeniz Lojistik", 39749.74, "gelir", "2026-10-10", "Lojistik Destek Tahsilatı", "Bekliyor"),
            ("Yıldız Mobilya", 15511.28, "gelir", "2026-10-15", "Ekipman Satış Bakiyesi", "Bekliyor"),
            ("Maslak Yazılım", 29063.64, "gelir", "2026-10-20", "Bakım Anlaşması Bedeli", "Bekliyor"),
            ("Beta Kimya", 10622.1, "gelir", "2026-10-25", "Laboratuvar Malzeme Satışı", "Bekliyor"),
            ("Mavi Mimarlık", 30112.54, "gelir", "2026-11-02", "Rölöve Çalışması Tahsilatı", "Bekliyor"),
            ("Caner Demir", 5274.28, "gelir", "2026-11-10", "Yedek Parça Satış Bedeli", "Bekliyor"),
            ("Ayşe Kaya", 2711.69, "gelir", "2026-11-15", "Eğitim Hizmet Tahsilatı", "Bekliyor"),
            ("Doruk Toptan Gıda", 4578.03, "borç", "2026-07-21", "Toptan Ürün Tedarik Ödemesi", "Bekliyor"),
            ("Çelik Hırdavat", 4625.09, "borç", "2026-07-24", "Şantiye Malzeme Faturası", "Bekliyor"),
            ("Global Enerji A.Ş.", 37221.67, "borç", "2026-07-28", "Fabrika Elektrik Faturası", "Kısmi Ödendi"),
            ("Alfa Ambalaj", 13935.28, "borç", "2026-08-01", "Koli ve Ambalaj Malzemesi", "Bekliyor"),
            ("Mega Kağıtçılık", 6282.85, "borç", "2026-08-04", "Ofis Kırtasiye Alımları", "Bekliyor"),
            ("Kuzey Tekstil", 15208.34, "borç", "2026-08-08", "Kumaş Tedarik Ödemesi", "Bekliyor"),
            ("Ege Elektrik", 9139.02, "borç", "2026-08-12", "Trafo Bakım Bedeli", "Bekliyor"),
            ("Hilal Demir Sanayi", 44481.87, "borç", "2026-08-20", "Demir Profil Alım Bedeli", "Bekliyor"),
            ("Doruk Toptan Gıda", 10539.88, "borç", "2026-08-25", "Aylık Gıda Alım Faturası", "Bekliyor"),
            ("Çelik Hırdavat", 4180.22, "borç", "2026-09-01", "El Aletleri Tedarik Faturası", "Bekliyor"),
            ("Global Enerji A.Ş.", 27209.69, "borç", "2026-09-08", "Aylık Tesis Enerji Gideri", "Bekliyor"),
            ("Alfa Ambalaj", 9843.33, "borç", "2026-09-12", "Paketleme Malzemesi Alımı", "Bekliyor"),
            ("Mega Kağıtçılık", 5943.73, "borç", "2026-09-18", "Matbaa Baskı İşleri Ödemesi", "Bekliyor"),
            ("Kuzey Tekstil", 18014.28, "borç", "2026-09-22", "İplik ve Kumaş Siparişi", "Bekliyor"),
            ("Ege Elektrik", 7680.52, "borç", "2026-10-02", "Pano Kurulum Hakedişi", "Bekliyor"),
            ("Hilal Demir Sanayi", 45276.37, "borç", "2026-10-08", "Sac Levha Sipariş Bakiyesi", "Bekliyor"),
            ("Global Enerji A.Ş.", 25013.09, "borç", "2026-10-15", "Enerji Dağıtım Hakedişi", "Bekliyor"),
            ("Kuzey Tekstil", 15531.57, "borç", "2026-10-22", "Kışlık Ürün Ham Hammaddesi", "Bekliyor"),
            ("Doruk Toptan Gıda", 8083.01, "borç", "2026-11-01", "Market Reyon Siparişi", "Bekliyor"),
            ("Çelik Hırdavat", 2905.65, "borç", "2026-11-05", "Kaynak Malzemeleri Faturası", "Bekliyor"),
            ("Alfa Ambalaj", 7565.12, "borç", "2026-11-12", "Etiket ve Kutu Alımı", "Bekliyor"),
            ("Mega Kağıtçılık", 4833.37, "borç", "2026-11-18", "Arşiv Klasörleri Alımı", "Bekliyor"),
            ("Ege Elektrik", 4755.14, "borç", "2026-11-20", "Aydınlatma Sistemleri Faturası", "Bekliyor"),
            ("Hilal Demir Sanayi", 19926.62, "borç", "2026-11-25", "Kaynak Telleri Sevkiyatı", "Bekliyor"),
            ("Global Enerji A.Ş.", 20381.34, "borç", "2026-11-28", "Trafo Yenileme Ödemesi", "Bekliyor")
        ]
        # Calculate dynamic remaining outstanding balance (kalan_tutar) based on status
        odeme_listesi_processed = []
        for item in odeme_listesi:
            cari_ad, tutar, tip, tarih, aciklama, durum = item
            kalan = tutar
            if durum == "Ödendi":
                kalan = 0.0
            elif durum == "Kısmi Ödendi":
                kalan = round(tutar * 0.4, 2)
            odeme_listesi_processed.append((cari_ad, tutar, kalan, tip, tarih, aciklama, durum))
            
        cursor.executemany("INSERT INTO odeme_plani (cari_ad, tutar, kalan_tutar, tip, tarih, aciklama, durum) VALUES (?, ?, ?, ?, ?, ?, ?)", odeme_listesi_processed)
        
    conn.commit()
    conn.close()
    # Ek stok ve fatura verilerini ayrı bağlantıyla ekle (idempotent)
    _seed_extra_stok_fatura()


def _seed_extra_stok_fatura():
    """
    Single Responsibility: Sadece stok ve fatura seed işleminden sorumludur.
    Cari bloğundan bağımsız olarak idempotent çalışır — mevcut kayıtlar varsa atlar.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM stok')
    if cursor.fetchone()[0] < 10:
        extra_stok = [
            ('Lenovo ThinkPad X1', 'Elektronik', 144),
            ('Apple MacBook Air M2', 'Elektronik', 56),
            ('LG UltraWide Monitor', 'Elektronik', 89),
            ('Logitech MX Keys', 'Aksesuar & Sarf', 215),
            ('USB-C Hub 7 Port', 'Aksesuar & Sarf', 380),
            ('Ergonomik Masa', 'Ofis Malzemeleri', 67),
            ('Çok Fonksiyonlu Yazıcı', 'Elektronik', 24),
            ('A4 Kağıt (Koli)', 'Aksesuar & Sarf', 600),
            ('Dosyalama Kabini', 'Ofis Malzemeleri', 45),
            ('Web Kamera HD', 'Elektronik', 130),
            ('Bluetooth Kulaklık', 'Aksesuar & Sarf', 98),
            ('Projeksiyon Cihazı', 'Elektronik', 12),
            ('Ofis Koltuğu Executive', 'Ofis Malzemeleri', 38),
            ('Ayarlanabilir Masa Lambası', 'Ofis Malzemeleri', 155),
        ]
        cursor.executemany(
            'INSERT INTO stok (ad, kategori, adet) VALUES (?, ?, ?)',
            extra_stok
        )
        extra_stok_islem = [
            ('Lenovo ThinkPad X1 — 15 Adet Giriş', 'giris', '2026-06-10'),
            ('Apple MacBook Air M2 — 5 Adet Çıkış (Satış)', 'cikis', '2026-06-15'),
            ('LG UltraWide Monitor — Stok Alarmı (Kritik)', 'alarm', '2026-07-01'),
            ('Logitech MX Keys — 40 Adet Giriş', 'giris', '2026-07-05'),
            ('Çok Fonksiyonlu Yazıcı — 3 Adet Çıkış (Servis)', 'cikis', '2026-07-08'),
            ('Projeksiyon Cihazı — Stok Alarmı (Kritik)', 'alarm', '2026-07-10'),
        ]
        cursor.executemany(
            'INSERT INTO stok_islem (tanim, tip, tarih) VALUES (?, ?, ?)',
            extra_stok_islem
        )

    cursor.execute('SELECT COUNT(*) FROM fatura_irsaliye')
    if cursor.fetchone()[0] < 10:
        extra_faturalar = [
            ('FT-2026-S00110 — Ahmet Yılmaz Ürün Satış Faturası', 12500.0, 'Ödendi', '2026-06-01'),
            ('FT-2026-S00111 — TeknoMarket A.Ş. Donanım Teslimatı', 45000.0, 'Ödenmedi', '2026-06-05'),
            ('FT-2026-A00050 — Doruk Toptan Gıda Alış Faturası', 18000.0, 'Ödendi', '2026-06-08'),
            ('IR-2026-00022 — Vural İnşaat Sevk İrsaliyesi', 0.0, 'Bekliyor', '2026-06-12'),
            ('FT-2026-S00112 — Maslak Yazılım Hizmet Faturası', 35000.0, 'Ödendi', '2026-06-18'),
            ('FT-2026-A00051 — Kuzey Tekstil Hammadde Alımı', 28500.0, 'Ödenmedi', '2026-06-20'),
            ('FT-2026-S00113 — Akdeniz Lojistik Taşıma Hizmeti', 9800.0, 'Ödendi', '2026-07-02'),
            ('FT-2026-A00052 — Global Enerji Fatura Ödemesi', 67000.0, 'Ödendi', '2026-07-05'),
            ('IR-2026-00023 — Beta Kimya Malzeme Sevkiyatı', 0.0, 'Bekliyor', '2026-07-10'),
            ('FT-2026-S00114 — Mavi Mimarlık Proje Bedeli', 24000.0, 'Ödenmedi', '2026-07-12'),
            ('FT-2026-A00053 — Ege Elektrik Malzeme Alımı', 15500.0, 'Ödendi', '2026-07-14'),
            ('FT-2026-S00115 — Yıldız Mobilya Ofis Ürünleri', 31000.0, 'Ödenmedi', '2026-07-16'),
        ]
        cursor.executemany(
            'INSERT INTO fatura_irsaliye (tanim, tutar, durum, tarih) VALUES (?, ?, ?, ?)',
            extra_faturalar
        )

    conn.commit()
    conn.close()


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
    toplam_urun_cesidi = 1237 + cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stok WHERE adet < 15")
    kritik_stok_sayisi = 11 + cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stok WHERE adet = 0")
    stoksuz_urun_sayisi = 3 + cursor.fetchone()[0]
    
    # Categories distribution
    cursor.execute("SELECT kategori, SUM(adet) as total FROM stok GROUP BY kategori")
    cat_rows = cursor.fetchall()
    
    kategoriler = []
    base_cats = {
        "Elektronik": 0,
        "Ofis Malzemeleri": 0,
        "Aksesuar & Sarf": 0
    }
    
    for row in cat_rows:
        cat_name = row['kategori']
        base_cats[cat_name] = row['total']
            
    total_stok_adet = sum(base_cats.values())
    for cat_name, qty in base_cats.items():
        ratio = round((qty / total_stok_adet) * 100, 1) if total_stok_adet > 0 else 0
        kategoriler.append({"ad": cat_name, "oran": ratio, "adet": qty})
        
    cursor.execute("SELECT id, tanim, tip, tarih FROM stok_islem ORDER BY id DESC LIMIT 5")
    stok_islemler = [dict(row) for row in cursor.fetchall()]
    
    # 4. Fatura ve Irsaliye calculations
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye WHERE durum = 'Ödenmedi'")
    odenmemis_fatura = 22 + cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye WHERE durum = 'Bekliyor'")
    bekleyen_irsaliye = 4 + cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye")
    kesilen_fatura_bu_ay = 108 + cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(tutar) FROM fatura_irsaliye WHERE durum != 'Bekliyor'")
    db_fatura_sum = cursor.fetchone()[0] or 0.0
    aylik_fatura_tutari = 578000.0 + db_fatura_sum
    
    taslak_fatura = 8
    
    cursor.execute("SELECT id, tanim, tutar, durum, tarih FROM fatura_irsaliye ORDER BY id DESC LIMIT 5")
    fatura_islemler = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "cari": {
            "musteri_sayisi": musteri_sayisi,
            "tedarikci_sayisi": tedarikci_sayisi,
            "toplam_alacak": toplam_alacak,
            "toplam_borc": toplam_borc,
            "son_islemler": cari_islemler
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
            "depo_doluluk_orani": 68.5,
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
    cursor.execute("SELECT id, ad, tip, limit_val, vergi_no, vergi_dairesi, yetkili_kisi, eposta, telefon, il, ilce, mahalle, adres_detay, cari_grubu, kredibilite FROM cari ORDER BY id ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

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
    
    # 2. Fetch specific past transactions linked to this Cari
    cursor.execute("SELECT id, tanim, tutar, tip, tarih FROM cari_islem WHERE cari_id = ? ORDER BY tarih DESC, id DESC", (cari_id,))
    transactions = [dict(r) for r in cursor.fetchall()]
    
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
    
    default_data = {
        "01": (150000, 120000), "02": (180000, 110000), "03": (220000, 150000),
        "04": (290000, 210000), "05": (270000, 180000), "06": (310000, 220000),
        "07": (0, 0)
    }
    
    for row in rows:
        ay_str = row['ay']
        if '-' in ay_str:
            month_part = ay_str.split('-')[1]
            if month_part in default_data:
                default_data[month_part] = (row['gelir'] or 0.0, row['gider'] or 0.0)
    
    for m_code in sorted(default_data.keys()):
        months.append(month_names[m_code])
        gelirler.append(default_data[m_code][0])
        giderler.append(default_data[m_code][1])
        
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
