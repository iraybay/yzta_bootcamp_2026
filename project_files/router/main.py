from repositories.db_core import get_db_connection
from repositories.cari_repository import get_all_cariler, get_payment_plan, get_cari_islem_history_range, get_cari_detail_and_history
from repositories.dashboard_repository import get_dashboard_data
from repositories.stok_repository import get_stok_liste, get_stok_hareketler, add_stok, add_stok_hareket
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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Kasa/Banka işlemi ekle
    # Varsayılan Kasa hesabı bul (genelde ID=1 veya ilk Kasa)
    cursor.execute("SELECT id FROM kasa_banka_hesap WHERE tur = 'kasa' LIMIT 1")
    hesap = cursor.fetchone()
    hesap_id = hesap['id'] if hesap else 1
    
    cursor.execute("""
        INSERT INTO kasa_banka_islem (hesap_id, cari_id, fatura_id, tanim, tutar, tip, tarih, islem_turu) 
        VALUES (?, ?, ?, ?, ?, ?, date('now'), ?)
    """, (hesap_id, cari_id, fatura_id, tanim, tutar, tip, 'tahsilat' if tip == 'gelir' else 'odeme'))
    
    # Faturayı ödendi olarak işaretle
    cursor.execute("UPDATE fatura_irsaliye SET durum = 'Ödendi' WHERE id = ?", (fatura_id,))
    
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

@main_bp.route('/api/stok/hareket-ekle', methods=['POST'])
def api_stok_hareket_ekle():
    req = request.get_json()
    stok_id = req.get('stok_id')
    tip = req.get('tip')
    miktar = req.get('miktar', 1)
    aciklama = req.get('aciklama', '')
    
    if not stok_id or not tip or int(miktar) <= 0:
        return jsonify({"success": False, "message": "Geçersiz veriler"})
        
    success, msg = add_stok_hareket(stok_id, tip, miktar, aciklama)
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

