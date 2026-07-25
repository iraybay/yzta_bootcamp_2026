from repositories.db_core import get_db_connection
import datetime

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

