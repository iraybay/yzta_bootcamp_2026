from repositories.db_core import get_db_connection

def get_stok_liste():
    """Tüm stok kalemlerini listeler, adet bilgisini depo_hareket sorgusuyla dinamik hesaplar."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stok ORDER BY id ASC")
    stoklar = [dict(row) for row in cursor.fetchall()]
    
    for s in stoklar:
        s_id = s['id']
        cursor.execute("SELECT tip, miktar FROM depo_hareket WHERE stok_id = ?", (s_id,))
        hm = cursor.fetchall()
        
        total = 0
        for h in hm:
            if h['tip'] in ['giris', 'sayim_fazlasi']:
                total += h['miktar']
            elif h['tip'] in ['cikis', 'fire']:
                total -= h['miktar']
        s['adet'] = total
        
    conn.close()
    return stoklar

def get_stok_hareketler():
    """Stok işlem hareketlerini depo_hareket tablosundan getirir, ilişkili irsaliyeleri de içerir."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.id, h.stok_id, s.ad as stok_ad, h.fis_no, h.tip, h.miktar, h.tarih, h.aciklama, 
               h.irsaliye_id, f.belge_no as irsaliye_no
        FROM depo_hareket h
        JOIN stok s ON h.stok_id = s.id
        LEFT JOIN fatura_irsaliye f ON h.irsaliye_id = f.id
        ORDER BY h.id DESC LIMIT 300
    """)
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data

def add_stok(ad, kategori, adet=0):
    """Yeni stok kalemi ekler ve gerekirse depo_hareket tablosuna açılış kaydı ekler."""
    import datetime
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stok (ad, kategori, adet) VALUES (?, ?, ?)", (ad, kategori, int(adet)))
    new_id = cursor.lastrowid
    
    if int(adet) > 0:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        fis_no = f"ACILIS-{new_id:04d}"
        cursor.execute("""
            INSERT INTO depo_hareket (stok_id, fis_no, tip, miktar, tarih, aciklama) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (new_id, fis_no, 'giris', int(adet), today, 'Açılış stoğu'))
        
    conn.commit()
    conn.close()
    return True

def add_stok_hareket(stok_id, tip, miktar, aciklama, cari_id=None):
    """Stok hareket kaydı oluşturur. Eğer çıkış yapılıyorsa ve cari belirtilmişse sevk irsaliyesi de düzenler."""
    import datetime
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get stock name
    cursor.execute("SELECT ad FROM stok WHERE id = ?", (stok_id,))
    stok_row = cursor.fetchone()
    if not stok_row:
        conn.close()
        return False, "Stok bulunamadı"
    stok_ad = stok_row['ad']
    
    # Generate simple fis_no
    cursor.execute("SELECT COUNT(*) FROM depo_hareket")
    count = cursor.fetchone()[0] + 1
    fis_no = f"FIS-{count:05d}"
    
    # Verify that the new total won't go below 0
    # First, calculate dynamic total
    cursor.execute("SELECT tip, miktar FROM depo_hareket WHERE stok_id = ?", (stok_id,))
    hm = cursor.fetchall()
    dynamic_total = 0
    for h in hm:
        if h['tip'] in ['giris', 'sayim_fazlasi']:
            dynamic_total += h['miktar']
        elif h['tip'] in ['cikis', 'fire']:
            dynamic_total -= h['miktar']
            
    miktar = int(miktar)
    yeni_adet = dynamic_total
    if tip in ['giris', 'sayim_fazlasi']:
        yeni_adet += miktar
    elif tip in ['cikis', 'fire']:
        yeni_adet -= miktar
        
    if yeni_adet < 0:
        conn.close()
        return False, "Stok miktarı eksiye düşemez"
        
    # Automatic waybill creation for shipments
    irsaliye_id = None
    if tip == 'cikis' and cari_id:
        try:
            cari_id = int(cari_id)
            import random
            belge_no = f"IR-2026-{random.randint(10000, 99999)}"
            irsaliye_tanim = f"{stok_ad} - {miktar} adet sevkiyat kaydı"
            cursor.execute("""
                INSERT INTO fatura_irsaliye (cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih)
                VALUES (?, ?, 'irsaliye', ?, 0.0, 'Bekliyor', ?)
            """, (cari_id, belge_no, irsaliye_tanim, today))
            irsaliye_id = cursor.lastrowid
        except Exception as ex:
            pass
            
    # Insert movement
    cursor.execute("""
        INSERT INTO depo_hareket (stok_id, fis_no, tip, miktar, tarih, aciklama, irsaliye_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (stok_id, fis_no, tip, miktar, today, aciklama, irsaliye_id))
    
    # Also update the stock table cache value
    cursor.execute("UPDATE stok SET adet = ? WHERE id = ?", (yeni_adet, stok_id))
    
    conn.commit()
    conn.close()
    return True, "Hareket işlendi"

def add_stok_item(ad, kategori, adet=0):
    """add_stok ile aynı işlevi görür."""
    return add_stok(ad, kategori, adet)

def update_stok(stok_id, ad, kategori):
    """Stok kalemi bilgilerini günceller."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE stok SET ad = ?, kategori = ? WHERE id = ?", (ad, kategori, stok_id))
    conn.commit()
    conn.close()
    return True