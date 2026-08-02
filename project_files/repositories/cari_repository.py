from repositories.db_core import get_db_connection

def get_all_cariler():
    """Tüm cari kayıtlarını listeler."""
    conn = get_db_connection()
    cursor = conn.cursor()
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
                    
        if is_musteri:
            c['bakiye'] = round(total_invoices - total_payments, 2)
        else:
            c['bakiye'] = round(total_payments - total_invoices, 2)
        
    conn.close()
    return cariler

def get_payment_plan(start_date=None, end_date=None, tip=None):
    """Ödeme planı listesini filtreleyerek ve metrikleri hesaplayarak getirir."""
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

def get_cari_islem_history_range(start_date=None, end_date=None):
    """Belirli tarih aralığındaki cari işlemleri filtreleyerek ve özet metrikleri hesaplayarak getirir."""
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
    
    query += " ORDER BY id DESC"
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

def get_cari_detail_and_history(cari_id):
    """Tek bir carinin detaylarını ve işlem geçmişini cari_islem tablosundan getirir."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM cari WHERE id = ?", (cari_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    cari_info = dict(row)
    
    # Query directly from cari_islem table (son işlemler)
    cursor.execute("""
        SELECT 
            'cari_islem' as kaynak,
            ci.id as belge_id,
            fi.id as fatura_id,
            COALESCE(fi.belge_no, 'MKZ-' || kbi.id, 'ISL-' || ci.id) as belge_no,
            ci.tarih,
            ci.tanim as aciklama,
            ci.tutar,
            COALESCE(fi.durum, 'Onaylandı') as durum,
            ci.tip as islem_tipi
        FROM cari_islem ci
        LEFT JOIN fatura_irsaliye fi ON ci.cari_id = fi.cari_id 
                                    AND ci.tarih = fi.tarih 
                                    AND ABS(ci.tutar - fi.tutar) < 0.01
                                    AND ci.tanim = fi.tanim
        LEFT JOIN kasa_banka_islem kbi ON ci.cari_id = kbi.cari_id 
                                      AND ci.tarih = kbi.tarih 
                                      AND ABS(ci.tutar - kbi.tutar) < 0.01
                                      AND ci.tanim = kbi.tanim
        WHERE ci.cari_id = ?
        ORDER BY ci.tarih DESC, ci.id DESC
    """, (cari_id,))
    
    transactions = [dict(r) for r in cursor.fetchall()]
    
    is_musteri = (cari_info['tip'] == 'musteri')
    for t in transactions:
        t_tip = t['islem_tipi']
        t['tip'] = t_tip
        if is_musteri:
            t['yon'] = 'borc' if t_tip == 'alacak' else 'alacak'
        else:
            t['yon'] = 'alacak' if t_tip == 'borc' else 'borc'
        
    conn.close()
    return {
        "cari": cari_info,
        "transactions": transactions
    }

def add_cari_record(ad, tip="musteri", limit_val=0.0, vergi_no="Bilinmiyor", vergi_dairesi="", yetkili_kisi="Bilinmiyor", eposta="", telefon="", il="", ilce="", mahalle="", adres_detay="", cari_grubu="", kredibilite="A"):
    """Veritabanına yeni cari (müşteri/tedarikçi) ekler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cari (ad, tip, limit_val, vergi_no, vergi_dairesi, yetkili_kisi, eposta, telefon, il, ilce, mahalle, adres_detay, cari_grubu, kredibilite)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (ad, tip, limit_val, vergi_no, vergi_dairesi, yetkili_kisi, eposta, telefon, il, ilce, mahalle, adres_detay, cari_grubu, kredibilite))
    conn.commit()
    yeni_id = cursor.lastrowid
    conn.close()
    return yeni_id