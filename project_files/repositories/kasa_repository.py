from repositories.db_core import get_db_connection

def get_banka_hesaplari(tur=None):
    """Kasa veya banka hesaplarını türe göre güvenli bir şekilde getirir."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if tur:
            cursor.execute("SELECT * FROM kasa_banka_hesap WHERE tur = ? ORDER BY ad ASC", (tur,))
        else:
            cursor.execute("SELECT * FROM kasa_banka_hesap ORDER BY ad ASC")
            
        hesaplar = cursor.fetchall()
        conn.close()
        return [dict(row) for row in hesaplar]
    except Exception as e:
        print(f"KASA/BANKA REPO HATASI (get_banka_hesaplari): {e}")
        return []

def get_hesaplar(tur=None):
    """get_banka_hesaplari ile eşdeğerdir."""
    return get_banka_hesaplari(tur)

def get_monthly_liquidity_data():
    """Aylık likidite verilerini güvenli bir şekilde getirir."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT strftime('%Y-%m', tarih) as ay, tip, SUM(tutar) as toplam 
            FROM kasa_banka_islem 
            GROUP BY ay, tip
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"KASA/BANKA REPO HATASI (get_monthly_liquidity_data): {e}")
        return []