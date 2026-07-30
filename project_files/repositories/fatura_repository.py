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
        
    query += " ORDER BY f.tarih DESC, f.id DESC"
    
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

def add_fatura_irsaliye_full(cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih):
    """Yeni fatura/irsaliye ekler."""
    return add_fatura(cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih)

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