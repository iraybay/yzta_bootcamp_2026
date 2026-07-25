from repositories.db_core import get_db_connection
import datetime

class HesapRepository:
    def __init__(self, db_conn_factory):
        self.get_db = db_conn_factory
        
    def get_all(self, tur=None):
        conn = self.get_db()
        cursor = conn.cursor()
        if tur:
            cursor.execute("SELECT * FROM kasa_banka_hesap WHERE tur = ?", (tur,))
        else:
            cursor.execute("SELECT * FROM kasa_banka_hesap")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
        
    def create(self, ad, tur, hesap_no, iban, sube, doviz_turu, kredibilite='A'):
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO kasa_banka_hesap (ad, tur, hesap_no, iban, sube, doviz_turu, bakiye, kredibilite)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
        ''', (ad, tur, hesap_no, iban, sube, doviz_turu, kredibilite))
        conn.commit()
        conn.close()

class IslemRepository:
    def __init__(self, db_conn_factory):
        self.get_db = db_conn_factory
        
    def get_history(self, hesap_id=None, start_date=None, end_date=None, tur=None):
        conn = self.get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT i.*, h.ad as hesap_ad, c.ad as cari_ad 
            FROM kasa_banka_islem i
            LEFT JOIN kasa_banka_hesap h ON i.hesap_id = h.id
            LEFT JOIN cari c ON i.cari_id = c.id
            WHERE 1=1
        """
        params = []
        if hesap_id:
            query += " AND i.hesap_id = ?"
            params.append(hesap_id)
        if start_date:
            query += " AND i.tarih >= ?"
            params.append(start_date)
        if end_date:
            query += " AND i.tarih <= ?"
            params.append(end_date)
        if tur:
            query += " AND h.tur = ?"
            params.append(tur)
            
        query += " ORDER BY i.tarih DESC, i.id DESC"
        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

class KasaBankaService:
    def __init__(self, db_conn_factory):
        self.get_db = db_conn_factory
        self.hesap_repo = HesapRepository(db_conn_factory)
        self.islem_repo = IslemRepository(db_conn_factory)
        
    def get_account_detail(self, account_id):
        conn = self.get_db()
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
        
    def add_transaction(self, hesap_id, tanim, tutar, islem_turu, tarih, cari_id=None):
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Tip belirleme
        if islem_turu in ['gelir', 'tahsilat']:
            tip = 'giris'
        else:
            tip = 'cikis'
            
        # Islem kaydi
        cursor.execute('''
            INSERT INTO kasa_banka_islem (hesap_id, cari_id, tanim, tutar, tip, tarih, islem_turu)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (hesap_id, cari_id, tanim, tutar, tip, tarih, islem_turu))
        
        # Bakiye guncelleme
        if tip == 'giris':
            cursor.execute("UPDATE kasa_banka_hesap SET bakiye = bakiye + ? WHERE id = ?", (tutar, hesap_id))
        else:
            cursor.execute("UPDATE kasa_banka_hesap SET bakiye = bakiye - ? WHERE id = ?", (tutar, hesap_id))
            
        # Cari islem yansitma
        if cari_id:
            cari_tip = 'alacak' if tip == 'giris' else 'borc'
            cursor.execute('''
                INSERT INTO cari_islem (cari_id, tanim, tutar, tip, tarih, odeme_tarihi)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (cari_id, "Nakit İşlem - " + tanim, tutar, cari_tip, tarih, tarih))
            
        conn.commit()
        conn.close()

# Keep legacy functions exported for AI or dashboard that might use them directly
def get_kasa_banka_accounts(tur=None):
    return HesapRepository(get_db_connection).get_all(tur)

def get_account_detail_and_history(account_id):
    return KasaBankaService(get_db_connection).get_account_detail(account_id)


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
    
    for row in rows:
        ay_str = row['ay']
        if '-' in ay_str:
            month_part = ay_str.split('-')[1]
            if month_part in month_names:
                months.append(month_names[month_part] + " " + ay_str.split('-')[0])
                gelirler.append(row['gelir'] or 0.0)
                giderler.append(row['gider'] or 0.0)
    
    conn.close()
    return {
        "labels": months,
        "gelirler": gelirler,
        "giderler": giderler
    }