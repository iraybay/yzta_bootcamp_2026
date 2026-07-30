from repositories.db_core import get_db_connection

def get_all_cariler():
    """Tüm cari kayıtlarını listeler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cari ORDER BY ad ASC")
    cariler = cursor.fetchall()
    conn.close()
    return [dict(row) for row in cariler]

def get_payment_plan():
    """Ödeme planı listesini getirir."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM odeme_plani ORDER BY tarih ASC")
    plan = cursor.fetchall()
    conn.close()
    return [dict(row) for row in plan]

def get_cari_islem_history_range(start_date, end_date):
    """Belirli tarih aralığındaki cari işlemleri getirir."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cari_islem WHERE tarih BETWEEN ? AND ? ORDER BY tarih DESC", (start_date, end_date))
    islemler = cursor.fetchall()
    conn.close()
    return [dict(row) for row in islemler]

def get_cari_detail_and_history(cari_id):
    """Tek bir carinin detaylarını ve işlem geçmişini getirir."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cari WHERE id = ?", (cari_id,))
    cari = cursor.fetchone()
    
    cursor.execute("SELECT * FROM cari_islem WHERE cari_id = ? ORDER BY tarih DESC", (cari_id,))
    islemler = cursor.fetchall()
    conn.close()
    
    return dict(cari) if cari else None, [dict(row) for row in islemler]

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