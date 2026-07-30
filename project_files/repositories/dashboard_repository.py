from repositories.db_core import get_db_connection
from repositories.kasa_repository import get_monthly_liquidity_data
import datetime

def get_dashboard_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Cari calculations
    cursor.execute("SELECT COUNT(*) FROM cari WHERE tip = 'musteri'")
    musteri_sayisi = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM cari WHERE tip = 'tedarikci'")
    tedarikci_sayisi = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(limit_val) FROM cari WHERE tip = 'musteri'")
    toplam_alacak = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(limit_val) FROM cari WHERE tip = 'tedarikci'")
    toplam_borc = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT id, tanim, tutar, tip, tarih FROM cari_islem ORDER BY tarih DESC, id DESC LIMIT 5")
    cari_islemler = [dict(row) for row in cursor.fetchall()]
    
    # 2. Kasa ve Banka calculations
    cursor.execute("SELECT SUM(bakiye) FROM kasa_banka_hesap WHERE tur = 'kasa'")
    kasa_bakiye = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(bakiye) FROM kasa_banka_hesap WHERE tur = 'banka'")
    banka_bakiye = cursor.fetchone()[0] or 0.0
    toplam_nakit = kasa_bakiye + banka_bakiye
    
    # Monthly Cashflow calculation (July 2026)
    cursor.execute("SELECT SUM(tutar) FROM kasa_banka_islem WHERE tip = 'giris' AND tarih LIKE '2026-07%'")
    aylik_gelir = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(tutar) FROM kasa_banka_islem WHERE tip = 'cikis' AND tarih LIKE '2026-07%'")
    aylik_gider = cursor.fetchone()[0] or 0.0
    
    cursor.execute('''
        SELECT islem.id, islem.tanim, islem.tutar, islem.tip, islem.tarih, hesap.ad as hesap_ad 
        FROM kasa_banka_islem islem 
        JOIN kasa_banka_hesap hesap ON islem.hesap_id = hesap.id 
        ORDER BY islem.tarih DESC, islem.id DESC LIMIT 5
    ''')
    kasa_islemler = [dict(row) for row in cursor.fetchall()]
    
    monthly_chart = get_monthly_liquidity_data()
    
    # 3. Stok calculations
    cursor.execute("SELECT COUNT(*) FROM stok")
    toplam_urun_cesidi = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stok WHERE adet < 15")
    kritik_stok_sayisi = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stok WHERE adet = 0")
    stoksuz_urun_sayisi = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(adet) FROM stok")
    total_stok_adet_db = cursor.fetchone()[0] or 0
    depo_doluluk_orani = min(100.0, round((total_stok_adet_db / 5000.0) * 100, 1))
    
    # Categories distribution
    cursor.execute("SELECT kategori, SUM(adet) as total FROM stok GROUP BY kategori")
    cat_rows = cursor.fetchall()
    
    kategoriler = []
    base_cats = {}
    
    for row in cat_rows:
        cat_name = row['kategori']
        base_cats[cat_name] = row['total']
            
    total_stok_adet = sum(base_cats.values())
    for cat_name, qty in base_cats.items():
        ratio = round((qty / total_stok_adet) * 100, 1) if total_stok_adet > 0 else 0
        kategoriler.append({"ad": cat_name, "oran": ratio, "adet": qty})
        
    cursor.execute("""
        SELECT h.id, s.ad || ' - ' || h.aciklama as tanim, h.tip, h.tarih 
        FROM depo_hareket h
        JOIN stok s ON h.stok_id = s.id
        ORDER BY h.tarih DESC, h.id DESC LIMIT 5
    """)
    stok_islemler = [dict(row) for row in cursor.fetchall()]
    
    # 4. Fatura ve Irsaliye calculations
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye WHERE durum = 'Ödenmedi'")
    odenmemis_fatura = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye WHERE durum = 'Bekliyor'")
    bekleyen_irsaliye = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye")
    kesilen_fatura_bu_ay = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(tutar) FROM fatura_irsaliye WHERE durum != 'Bekliyor'")
    db_fatura_sum = cursor.fetchone()[0] or 0.0
    aylik_fatura_tutari = db_fatura_sum
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye WHERE durum = 'Taslak'")
    taslak_fatura = cursor.fetchone()[0]
    
    cursor.execute("SELECT id, tanim, tutar, durum, tarih FROM fatura_irsaliye ORDER BY id DESC LIMIT 5")
    fatura_islemler = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT id, ad FROM cari")
    tum_cariler = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "cari": {
            "musteri_sayisi": musteri_sayisi,
            "tedarikci_sayisi": tedarikci_sayisi,
            "toplam_alacak": toplam_alacak,
            "toplam_borc": toplam_borc,
            "son_islemler": cari_islemler,
            "tum_liste": tum_cariler
        },
        "kasa_banka": {
            "kasa_bakiye": kasa_bakiye,
            "banka_bakiye": banka_bakiye,
            "toplam_nakit": toplam_nakit,
            "aylik_gelir": aylik_gelir,
            "aylik_gider": aylik_gider,
            "son_islemler": kasa_islemler,
            "monthly_chart": monthly_chart
        },
        "stok": {
            "toplam_urun_cesidi": toplam_urun_cesidi,
            "kritik_stok_sayisi": kritik_stok_sayisi,
            "stoksuz_urun_sayisi": stoksuz_urun_sayisi,
            "depo_doluluk_orani": depo_doluluk_orani,
            "kategoriler": kategoriler,
            "son_islemler": stok_islemler
        },
        "fatura_irsaliye": {
            "taslak_fatura": taslak_fatura,
            "odenmemis_fatura": odenmemis_fatura,
            "kesilen_fatura_bu_ay": kesilen_fatura_bu_ay,
            "bekleyen_irsaliye": bekleyen_irsaliye,
            "aylik_fatura_tutari": aylik_fatura_tutari,
            "son_islemler": fatura_islemler
        }
    }

