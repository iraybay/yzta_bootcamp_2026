from repositories.db_core import get_db_connection

def get_stok_liste():
    """Tüm stok kalemlerini listeler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stok ORDER BY ad ASC")
    stoklar = cursor.fetchall()
    conn.close()
    return [dict(row) for row in stoklar]

def get_stok_hareketler():
    """Stok işlem hareketlerini getirir[cite: 8]."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            si.id,
            COALESCE(si.tarih, '') as tarih,
            COALESCE(si.fis_no, 'FIS-' || si.id) as fis_no,
            COALESCE(s.ad, si.tanim, 'Ürün Belirtilmemiş') as urun,
            COALESCE(si.tip, 'GIRIS') as tip,
            COALESCE(si.miktar, 1) as miktar
        FROM stok_islem si
        LEFT JOIN stok s ON si.stok_id = s.id
        ORDER BY si.tarih DESC, si.id DESC
    """)
    hareketler = cursor.fetchall()
    conn.close()
    
    sonuc = []
    for row in hareketler:
        d = dict(row)
        amt = d['miktar']
        if d['tip'] in ('CIKIS', 'ALARM') and amt > 0:
            amt = -amt
        d['miktar'] = amt
        sonuc.append(d)
        
    return sonuc

def add_stok(ad, kategori, adet=0):
    """Yeni stok kalemi ekler[cite: 8]."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stok (ad, kategori, adet)
        VALUES (?, ?, ?)
    """, (ad, kategori, adet))
    conn.commit()
    conn.close()
    return True

def add_stok_hareket(tanim, tip, tarih):
    """Yeni stok hareketi ekler[cite: 8]."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stok_islem (tanim, tip, tarih)
        VALUES (?, ?, ?)
    """, (tanim, tip, tarih))
    conn.commit()
    conn.close()
    return True

def add_stok_item(ad, kategori, adet=0):
    """add_stok ile aynı işlevi görür[cite: 8]."""
    return add_stok(ad, kategori, adet)