from db_manager import get_db_connection

class CariRepository:
    
    @staticmethod
    def tum_carileri_getir():
        """Tüm cari kayıtlarını listeler."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cari ORDER BY unvan ASC")
        cariler = cursor.fetchall()
        conn.close()
        return [dict(row) for row in cariler]

    @staticmethod
    def id_ile_cari_getir(cari_id: int):
        """ID'ye göre tek bir cari getirir."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cari WHERE id = ?", (cari_id,))
        cari = cursor.fetchone()
        conn.close()
        return dict(cari) if cari else None

    @staticmethod
    def cari_ekle(unvan: str, telefon: str = "", eposta: str = "", adres: str = ""):
        """Yeni cari kaydı oluşturur."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cari (unvan, telefon, eposta, adres, bakiye)
            VALUES (?, ?, ?, ?, 0.0)
        """, (unvan.strip(), telefon.strip(), eposta.strip(), adres.strip()))
        conn.commit()
        yeni_id = cursor.lastrowid
        conn.close()
        return yeni_id

    @staticmethod
    def cari_guncelle(cari_id: int, unvan: str, telefon: str, eposta: str, adres: str):
        """Mevcut cari bilgilerini günceller."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE cari 
            SET unvan = ?, telefon = ?, eposta = ?, adres = ?
            WHERE id = ?
        """, (unvan.strip(), telefon.strip(), eposta.strip(), adres.strip(), cari_id))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def cari_sil(cari_id: int):
        """Cari kaydını siler."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cari WHERE id = ?", (cari_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def cari_hareket_ekle(cari_id: int, tarih: str, islem_tipi: str, aciklama: str, tutar: float):
        """Cariye borç/alacak hareketi ekler ve bakiyesini günceller."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO cari_hareketleri (cari_id, tarih, islem_tipi, aciklama, tutar)
            VALUES (?, ?, ?, ?, ?)
        """, (cari_id, tarih, islem_tipi, aciklama, tutar))

        bakiye_degisim = tutar if islem_tipi == 'BORC' else -tutar
        cursor.execute("UPDATE cari SET bakiye = bakiye + ? WHERE id = ?", (bakiye_degisim, cari_id))

        conn.commit()
        conn.close()
        return True

    @staticmethod
    def cari_hareketleri_getir(cari_id: int):
        """Bir carinin tüm hareket geçmişini getirir."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM cari_hareketleri 
            WHERE cari_id = ? 
            ORDER BY tarih DESC, id DESC
        """, (cari_id,))
        hareketler = cursor.fetchall()
        conn.close()
        return [dict(row) for row in hareketler]