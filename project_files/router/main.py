from repositories.db_core import get_db_connection
from repositories.cari_repository import get_all_cariler, get_payment_plan, get_cari_islem_history_range, get_cari_detail_and_history
from repositories.dashboard_repository import get_dashboard_data
from repositories.stok_repository import get_stok_liste, get_stok_hareketler, add_stok, add_stok_hareket, update_stok
from flask import Blueprint, render_template, jsonify, request


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/stok-listesi')
def stok_listesi_page():
    return render_template('stok_listesi.html')

@main_bp.route('/cari-listesi')
def cari_listesi_page():
    return render_template('cari_listesi.html')

@main_bp.route('/cari-hareketler')
def cari_hareketler_page():
    return render_template('cari_hareketler.html')

@main_bp.route('/mutabakat-raporu')
def mutabakat_raporu_page():
    return render_template('mutabakat_raporu.html')

@main_bp.route('/api/cari/tum-liste')
def get_tum_cariler():
    cariler = get_all_cariler()
    return jsonify({"success": True, "data": cariler})

@main_bp.route('/api/mutabakat/liste')
def get_mutabakat_liste():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    tip = request.args.get('tip')
    
    result = get_payment_plan(start_date, end_date, tip)
    return jsonify({"success": True, **result})

@main_bp.route('/api/cari/hareketler')
def get_cari_hareketler_api():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    res = get_cari_islem_history_range(start_date, end_date)
    return jsonify({"success": True, **res})

@main_bp.route('/cari-detay/<int:cari_id>')
def cari_detay_page(cari_id):
    return render_template('cari_detay.html', cari_id=cari_id)

@main_bp.route('/api/cari/detay/<int:cari_id>')
def get_cari_detay_api(cari_id):
    res = get_cari_detail_and_history(cari_id)
    if not res:
        return jsonify({"success": False, "message": "Cari bulunamadı."}), 404
    return jsonify({"success": True, **res})

@main_bp.route('/api/fatura/ode', methods=['POST'])
def pay_invoice():
    cari_id = request.form.get('cari_id')
    fatura_id = request.form.get('fatura_id')
    tutar = float(request.form.get('tutar', 0))
    tip = request.form.get('tip', 'gelir')
    tanim = request.form.get('tanim', 'Fatura Ödemesi')
    
    hesap_id_raw = request.form.get('hesap_id')
    tarih = request.form.get('tarih') or str(__import__('datetime').date.today())
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if hesap_id_raw:
        hesap_id = int(hesap_id_raw)
    else:
        cursor.execute("SELECT id FROM kasa_banka_hesap WHERE tur = 'kasa' LIMIT 1")
        hesap = cursor.fetchone()
        hesap_id = hesap['id'] if hesap else 1
        
    kb_tip = 'giris' if tip == 'gelir' else 'cikis'
    islem_turu = 'tahsilat' if tip == 'gelir' else 'odeme'
    
    cursor.execute("""
        INSERT INTO kasa_banka_islem (hesap_id, cari_id, fatura_id, tanim, tutar, tip, tarih, islem_turu) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (hesap_id, cari_id, fatura_id, tanim, tutar, kb_tip, tarih, islem_turu))
    
    # Kasa/Banka hesap bakiyesini güncelle
    cursor.execute("""
        UPDATE kasa_banka_hesap 
        SET bakiye = (
            SELECT COALESCE(SUM(CASE WHEN tip='giris' THEN tutar ELSE -tutar END), 0.0) 
            FROM kasa_banka_islem 
            WHERE hesap_id = ?
        )
        WHERE id = ?
    """, (hesap_id, hesap_id))
    
    # Cari son işlemler tablosuna (cari_islem) ödemeyi yansıt
    cursor.execute("SELECT tip FROM cari WHERE id = ?", (cari_id,))
    c_row = cursor.fetchone()
    is_musteri = c_row['tip'] == 'musteri' if c_row else True
    cari_tip = 'borc' if is_musteri else 'alacak'
    
    cursor.execute("""
        INSERT INTO cari_islem (cari_id, tanim, tutar, tip, tarih, odeme_tarihi)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (cari_id, tanim, tutar, cari_tip, tarih, tarih))
    
    # Faturayı ödendi olarak işaretle
    cursor.execute("SELECT belge_no FROM fatura_irsaliye WHERE id = ?", (fatura_id,))
    f_row = cursor.fetchone()
    belge_no = f_row['belge_no'] if f_row else ""
    
    cursor.execute("UPDATE fatura_irsaliye SET durum = 'Ödendi' WHERE id = ?", (fatura_id,))
    
    if belge_no:
        cursor.execute("UPDATE odeme_plani SET durum = 'Ödendi', kalan_tutar = 0.0 WHERE aciklama LIKE ?", (f"%{belge_no}%",))
        
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@main_bp.route('/api/dashboard', methods=['GET'])
def api_get_dashboard_data():
    data = get_dashboard_data()
    return jsonify(data)

@main_bp.route('/api/stok/liste', methods=['GET'])
def api_stok_liste():
    data = get_stok_liste()
    return jsonify({"success": True, "data": data})

@main_bp.route('/api/stok/hareketler', methods=['GET'])
def api_stok_hareketler():
    data = get_stok_hareketler()
    return jsonify({"success": True, "data": data})

@main_bp.route('/api/stok/ekle', methods=['POST'])
def api_stok_ekle():
    req = request.get_json()
    ad = req.get('ad')
    kategori = req.get('kategori', '')
    adet = req.get('adet', 0)
    
    if not ad:
        return jsonify({"success": False, "message": "Ürün adı zorunludur"})
        
    add_stok(ad, kategori, adet)
    return jsonify({"success": True, "message": "Ürün başarıyla eklendi"})

@main_bp.route('/api/stok/duzenle', methods=['POST'])
def api_stok_duzenle():
    req = request.get_json()
    stok_id = req.get('id')
    ad = req.get('ad')
    kategori = req.get('kategori', '')
    
    if not stok_id or not ad:
        return jsonify({"success": False, "message": "Geçersiz veriler"})
        
    update_stok(stok_id, ad, kategori)
    return jsonify({"success": True, "message": "Ürün başarıyla güncellendi"})

@main_bp.route('/api/stok/hareket-ekle', methods=['POST'])
def api_stok_hareket_ekle():
    req = request.get_json()
    stok_id = req.get('stok_id')
    tip = req.get('tip')
    miktar = req.get('miktar', 1)
    aciklama = req.get('aciklama', '')
    cari_id = req.get('cari_id')
    
    if not stok_id or not tip or int(miktar) <= 0:
        return jsonify({"success": False, "message": "Geçersiz veriler"})
        
    success, msg = add_stok_hareket(stok_id, tip, miktar, aciklama, cari_id)
    return jsonify({"success": success, "message": msg})

@main_bp.route('/kasa-listesi')
def kasa_listesi_page():
    return render_template('kasa_listesi.html')

@main_bp.route('/banka-listesi')
def banka_listesi_page():
    return render_template('banka_listesi.html')

@main_bp.route('/kasa-hareketler')
def kasa_hareketler_page():
    return render_template('kasa_hareketler.html')

@main_bp.route('/kasa-detay/<int:hesap_id>')
def kasa_detay_page(hesap_id):
    return render_template('kasa_detay.html', hesap_id=hesap_id)

@main_bp.route('/banka-detay/<int:hesap_id>')
def banka_detay_page(hesap_id):
    return render_template('banka_detay.html', hesap_id=hesap_id)

@main_bp.route('/fatura-irsaliye')
@main_bp.route('/fatura-listesi')
def fatura_irsaliye_page():
    return render_template('fatura_irsaliye.html')

@main_bp.route('/api/global-search')
def global_search():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify({"success": True, "results": []})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    results = []
    like_query = f"%{q}%"
    
    # 1. Search Cariler
    cursor.execute("""
        SELECT id, ad, tip 
        FROM cari 
        WHERE ad LIKE ? OR cari_grubu LIKE ? 
        LIMIT 5
    """, (like_query, like_query))
    for row in cursor.fetchall():
        tip_label = "Müşteri" if row['tip'] == 'musteri' else "Tedarikçi"
        results.append({
            "text": f"{row['ad']} ({tip_label})",
            "icon": "fa-solid fa-user",
            "target": f"/cari-detay/{row['id']}"
        })
        
    # 2. Search Stoklar
    cursor.execute("""
        SELECT id, ad, kategori 
        FROM stok 
        WHERE ad LIKE ? OR kategori LIKE ? 
        LIMIT 5
    """, (like_query, like_query))
    for row in cursor.fetchall():
        results.append({
            "text": f"{row['ad']} ({row['kategori']}) - Stok Ürünü",
            "icon": "fa-solid fa-box",
            "target": "/stok-listesi"
        })
        
    # 3. Search Kasalar & Bankalar
    cursor.execute("""
        SELECT id, ad, tur 
        FROM kasa_banka_hesap 
        WHERE ad LIKE ? 
        LIMIT 5
    """, (like_query,))
    for row in cursor.fetchall():
        target_url = f"/kasa-detay/{row['id']}" if row['tur'] == 'kasa' else f"/banka-detay/{row['id']}"
        type_label = "Kasa Hesabı" if row['tur'] == 'kasa' else "Banka Hesabı"
        results.append({
            "text": f"{row['ad']} ({type_label})",
            "icon": "fa-solid fa-wallet" if row['tur'] == 'kasa' else "fa-solid fa-building-columns",
            "target": target_url
        })
        
    # 4. Search Faturalar
    cursor.execute("""
        SELECT id, belge_no, belge_turu, tutar 
        FROM fatura_irsaliye 
        WHERE belge_no LIKE ? OR tanim LIKE ? 
        LIMIT 5
    """, (like_query, like_query))
    for row in cursor.fetchall():
        type_label = "Satış Faturası" if row['belge_turu'] == 'satis_faturasi' else ("Alış Faturası" if row['belge_turu'] == 'alis_faturasi' else "İrsaliye")
        results.append({
            "text": f"{row['belge_no']} - {type_label} ({row['tutar']} ₺)",
            "icon": "fa-solid fa-file-invoice-dollar",
            "target": "/fatura-irsaliye"
        })
        
    conn.close()
    return jsonify({"success": True, "results": results})

