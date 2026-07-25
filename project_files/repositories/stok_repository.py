from repositories.db_core import get_db_connection
import datetime

def add_stok_item(ad, kategori, adet):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO stok (ad, kategori, adet) VALUES (?, ?, ?)", (ad, kategori, adet))
    
    log_tanim = f"{ad} - {adet} Adet Eklendi ({kategori})"
    cursor.execute("INSERT INTO stok_islem (tanim, tip, tarih) VALUES (?, 'giris', '2026-07-18')", (log_tanim,))
    
    conn.commit()
    conn.close()

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

