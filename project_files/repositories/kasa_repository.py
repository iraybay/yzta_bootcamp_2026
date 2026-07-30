from db_manager import get_db_connection

class KasaRepository:

    @staticmethod
    def tum_kasalari_getir():
        """Sistemdeki tüm kasaları getirir."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kasa ORDER BY kasa_adi ASC")
        kasalar = cursor.fetchall()
        conn.close()
        return [dict(row) for row in kasalar]

    @staticmethod
    def id_ile_kasa_getir(kasa_id: int):
        """ID'ye göre tek bir kasa getirir."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kasa WHERE id = ?", (kasa_id,))
        kasa = cursor.fetchone()
        conn.close()
        return dict(kasa) if kasa else None

    @staticmethod
    def kasa_ekle(kasa_adi: str, aciklama: str = ""):
        """Yeni bir kasa tanımı oluşturur."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO kasa (kasa_adi, bakiye, aciklama)
            VALUES (?, 0.0, ?)
        """, (kasa_adi.strip(), aciklama.strip()))
        conn.commit()
        yeni_id = cursor.lastrowid
        conn.close()
        return yeni_id

    @staticmethod
    def kasa_hareket_ekle(kasa_id: int, tarih: str, aciklama: str, tutar: float, islem_tipi: str):
        """Kasaya para girişi ('GIRIS') veya para çıkışı ('CIKIS') kaydeder."""
        if islem_tipi not in ('GIRIS', 'CIKIS'):
            raise ValueError("İşlem tipi sadece 'GIRIS' veya 'CIKIS' olabilir.")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO kasa_hareketleri (kasa_id, tarih, aciklama, tutar, islem_tipi)
            VALUES (?, ?, ?, ?, ?)
        """, (kasa_id, tarih, aciklama.strip(), tutar, islem_tipi))

        bakiye_degisim = tutar if islem_tipi == 'GIRIS' else -tutar
        cursor.execute("UPDATE kasa SET bakiye = bakiye + ? WHERE id = ?", (bakiye_degisim, kasa_id))

        conn.commit()
        conn.close()
        return True

    @staticmethod
    def kasa_hareketleri_getir(kasa_id: int):
        """Belirtilen kasanın tüm işlem geçmişini getirir."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM kasa_hareketleri 
            WHERE kasa_id = ? 
            ORDER BY tarih DESC, id DESC
        """, (kasa_id,))
        hareketler = cursor.fetchall()
        conn.close()
        return [dict(row) for row in hareketler]