from repositories.db_core import get_db_connection

def get_fatura_liste(start_date=None, end_date=None, durum=None, tip=None):
    """Tüm fatura ve irsaliye kayıtlarını filtre seçenekleriyle birlikte getirir."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT f.*, c.ad as cari_ad 
        FROM fatura_irsaliye f
        LEFT JOIN cari c ON f.cari_id = c.id
        WHERE 1=1
    '''
    params = []
    
    if start_date and end_date:
        query += " AND f.tarih BETWEEN ? AND ?"
        params.extend([start_date, end_date])
        
    if durum and durum != 'tumu':
        query += " AND f.durum = ?"
        params.append(durum)
        
    if tip and tip != 'tumu':
        query += " AND f.belge_turu = ?"
        params.append(tip)
        
    query += " ORDER BY f.id DESC"
    
    cursor.execute(query, params)
    faturalar = cursor.fetchall()
    conn.close()
    return [dict(row) for row in faturalar]

def add_fatura(cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih):
    """Yeni fatura veya irsaliye ekler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO fatura_irsaliye (cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih))
    conn.commit()
    conn.close()
    return True

def update_fatura_durum(fatura_id, yeni_durum):
    """Faturanın durumunu günceller (Ödendi/Ödenmedi) ve kasa/cari hesap entegrasyonunu tamamlar."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch current invoice details
    cursor.execute("SELECT * FROM fatura_irsaliye WHERE id = ?", (fatura_id,))
    f_row = cursor.fetchone()
    if not f_row:
        conn.close()
        return False
        
    f_info = dict(f_row)
    eski_durum = f_info['durum']
    
    # Update status
    cursor.execute('''
        UPDATE fatura_irsaliye 
        SET durum = ? 
        WHERE id = ?
    ''', (yeni_durum, fatura_id))
    
    # If marked as paid, trigger financial transactions
    if yeni_durum == 'Ödendi' and eski_durum != 'Ödendi':
        # Check if already exists in kasa_banka_islem
        cursor.execute("SELECT COUNT(*) FROM kasa_banka_islem WHERE fatura_id = ?", (fatura_id,))
        exists = cursor.fetchone()[0]
        if exists == 0:
            # Find default cash account
            cursor.execute("SELECT id FROM kasa_banka_hesap WHERE tur = 'kasa' LIMIT 1")
            h_row = cursor.fetchone()
            hesap_id = h_row['id'] if h_row else 1
            
            belge_no = f_info['belge_no'] or ""
            tip = f_info['belge_turu']
            tarih = f_info['tarih']
            tutar = f_info['tutar']
            cari_id = f_info['cari_id']
            
            kb_tip = 'giris' if 'satis' in tip or tip == 'gelir' else 'cikis'
            islem_turu = 'tahsilat' if 'satis' in tip or tip == 'gelir' else 'odeme'
            kb_tanim = f"{belge_no} Fatura Tahsilatı" if 'satis' in tip or tip == 'gelir' else f"{belge_no} Fatura Ödemesi"
            
            # Insert into kasa_banka_islem
            cursor.execute("""
                INSERT INTO kasa_banka_islem (hesap_id, cari_id, fatura_id, tanim, tutar, tip, tarih, islem_turu) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (hesap_id, cari_id, fatura_id, kb_tanim, tutar, kb_tip, tarih, islem_turu))
            
            # Update balance of the account
            cursor.execute("""
                UPDATE kasa_banka_hesap 
                SET bakiye = (
                    SELECT COALESCE(SUM(CASE WHEN tip='giris' THEN tutar ELSE -tutar END), 0.0) 
                    FROM kasa_banka_islem 
                    WHERE hesap_id = ?
                )
                WHERE id = ?
            """, (hesap_id, hesap_id))
            
            # Update cari_islem
            cursor.execute("SELECT tip FROM cari WHERE id = ?", (cari_id,))
            c_row = cursor.fetchone()
            is_musteri = c_row['tip'] == 'musteri' if c_row else True
            cari_tip = 'borc' if is_musteri else 'alacak'
            
            cursor.execute("""
                INSERT INTO cari_islem (cari_id, tanim, tutar, tip, tarih, odeme_tarihi)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cari_id, kb_tanim, tutar, cari_tip, tarih, tarih))
            
            # Update odeme_plani
            if belge_no:
                cursor.execute(
                    "UPDATE odeme_plani SET durum = 'Ödendi', kalan_tutar = 0.0 WHERE aciklama LIKE ?",
                    (f"%{belge_no}%",)
                )
                
    conn.commit()
    conn.close()
    return True

def get_fatura_irsaliye_list(start_date=None, end_date=None, durum=None, tip=None):
    """Tüm fatura ve irsaliye kayıtlarını listeler."""
    return get_fatura_liste(start_date, end_date, durum, tip)

def add_fatura_irsaliye_full(cari_id, unvan, belge_no, tutar, tip, durum, tarih, aciklama):
    """Yeni fatura/irsaliye ekler, tüm cari, kasa, banka ve ödeme planı entegrasyonlarını çalıştırır."""
    import datetime
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Insert into fatura_irsaliye
    tanim = aciklama if aciklama else f"{belge_no} Nolu Fatura"
    cursor.execute('''
        INSERT INTO fatura_irsaliye (cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (cari_id, belge_no, tip, tanim, tutar, durum, tarih))
    fatura_id = cursor.lastrowid
    
    # 2. If it is an invoice, record it in cari_islem (Cari geçmiş)
    if tip in ['satis', 'alis', 'irsaliyeli_fatura']:
        cari_islem_tip = 'alacak' if tip == 'satis' else 'borc'
        odeme_tarihi = tarih if durum == 'Ödendi' else None
        cursor.execute('''
            INSERT INTO cari_islem (cari_id, tanim, tutar, tip, tarih, odeme_tarihi)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cari_id, tanim, tutar, cari_islem_tip, tarih, odeme_tarihi))
        
        # 3. Insert into odeme_plani
        op_tip = 'gelir' if tip == 'satis' else 'borç'
        tarih_dt = datetime.datetime.strptime(tarih, "%Y-%m-%d").date()
        vade = tarih_dt + datetime.timedelta(days=30)
        vade_str = vade.strftime("%Y-%m-%d")
        
        if durum == 'Ödenmedi':
            op_durum = 'Gecikti' if vade < datetime.date(2026, 7, 30) else 'Bekliyor'
            kalan = tutar
        else:
            op_durum = 'Ödendi'
            kalan = 0.0
            
        cursor.execute('''
            INSERT INTO odeme_plani (cari_ad, tutar, kalan_tutar, tip, tarih, aciklama, durum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (unvan, tutar, kalan, op_tip, vade_str, f"{belge_no} nolu fatura vadesi", op_durum))
        
        # 4. If already paid, record the payment transaction in kasa_banka_islem
        if durum == 'Ödendi':
            cursor.execute("SELECT id FROM kasa_banka_hesap WHERE tur = 'kasa' LIMIT 1")
            h_row = cursor.fetchone()
            hesap_id = h_row['id'] if h_row else 1
            
            kb_tip = 'giris' if tip == 'satis' else 'cikis'
            islem_turu = 'tahsilat' if tip == 'satis' else 'odeme'
            kb_tanim = f"{belge_no} Fatura Tahsilatı" if tip == 'satis' else f"{belge_no} Fatura Ödemesi"
            
            cursor.execute("""
                INSERT INTO kasa_banka_islem (hesap_id, cari_id, fatura_id, tanim, tutar, tip, tarih, islem_turu) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (hesap_id, cari_id, fatura_id, kb_tanim, tutar, kb_tip, tarih, islem_turu))
            
            # Update balance of the account
            cursor.execute("""
                UPDATE kasa_banka_hesap 
                SET bakiye = (
                    SELECT COALESCE(SUM(CASE WHEN tip='giris' THEN tutar ELSE -tutar END), 0.0) 
                    FROM kasa_banka_islem 
                    WHERE hesap_id = ?
                )
                WHERE id = ?
            """, (hesap_id, hesap_id))
            
            # Payment record in cari_islem (cancels out invoice)
            payment_cari_tip = 'borc' if tip == 'satis' else 'alacak'
            cursor.execute("""
                INSERT INTO cari_islem (cari_id, tanim, tutar, tip, tarih, odeme_tarihi)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cari_id, kb_tanim, tutar, payment_cari_tip, tarih, tarih))
            
    conn.commit()
    conn.close()
    return fatura_id

def update_fatura_status(fatura_id, yeni_durum):
    """Fatura durumunu günceller."""
    return update_fatura_durum(fatura_id, yeni_durum)

def delete_fatura_record(fatura_id):
    """Fatura kaydını siler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fatura_irsaliye WHERE id = ?", (fatura_id,))
    conn.commit()
    conn.close()
    return True