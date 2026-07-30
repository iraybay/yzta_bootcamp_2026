from db_manager import get_db_connection

class StokRepository:

    @staticmethod
    def tum_stoklari_getir():
        """Tüm stok ve ürün kayıtlarını listeler."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stok ORDER BY stok_adi ASC")
        stoklar = cursor.fetchall()
        conn.close()
        return [dict(row) for row in stoklar]

    @staticmethod
    def id_ile_stok_getir(stok_id: int):
        """ID'ye göre tek bir stok kartı getirir."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stok WHERE id = ?", (stok_id,))
        stok = cursor.fetchone()
        conn.close()
        return dict(stok) if stok else None

    @staticmethod
    def stok_ekle(stok_kodu: str, stok_adi: str, birim: str = "Adet", miktar: float = 0.0, birim_fiyat: float = 0.0, kdv: float = 20.0):
        """Yeni stok kartı oluşturur."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO stok (stok_kodu, stok_adi, birim, miktar, birim_fiyat, kdv)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (stok_kodu.strip(), stok_adi.strip(), birim.strip(), miktar, birim_fiyat, kdv))
        conn.commit()
        yeni_id = cursor.lastrowid
        conn.close()
        return yeni_id

    @staticmethod
    def stok_sil(stok_id: int):
        """Stok kartını siler."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stok WHERE id = ?", (stok_id,))
        conn.commit()
        conn.close()
        return True