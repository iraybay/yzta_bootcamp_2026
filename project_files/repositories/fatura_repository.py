from db_manager import get_db_connection

class FaturaRepository:

    @staticmethod
    def tum_faturalari_getir():
        """Tüm fatura kayıtlarını listeler."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, c.unvan as cari_unvan 
            FROM fatura_irsaliye f
            JOIN cari c ON f.cari_id = c.id
            ORDER BY f.tarih DESC, f.id DESC
        """)
        faturalar = cursor.fetchall()
        conn.close()
        return [dict(row) for row in faturalar]

    @staticmethod
    def fatura_ekle(fatura_no: str, cari_id: int, tarih: str, fatura_tipi: str, genel_toplam: float, aciklama: str = ""):
        """Yeni fatura kaydı oluşturur."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fatura_irsaliye (fatura_no, cari_id, tarih, fatura_tipi, genel_toplam, aciklama)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (fatura_no.strip(), cari_id, tarih, fatura_tipi, genel_toplam, aciklama.strip()))
        conn.commit()
        yeni_id = cursor.lastrowid
        conn.close()
        return yeni_id