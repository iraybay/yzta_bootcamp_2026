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
    """Faturanın durumunu günceller (Ödendi/Ödenmedi)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE fatura_irsaliye 
        SET durum = ? 
        WHERE id = ?
    ''', (yeni_durum, fatura_id))
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