from flask import Blueprint, render_template, jsonify, request
import db_manager

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

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
    cariler = db_manager.get_all_cariler()
    return jsonify({"success": True, "data": cariler})

@main_bp.route('/api/mutabakat/liste')
def get_mutabakat_liste():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    tip = request.args.get('tip')
    
    result = db_manager.get_payment_plan(start_date, end_date, tip)
    return jsonify({"success": True, **result})

@main_bp.route('/api/cari/hareketler')
def get_cari_hareketler_api():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    res = db_manager.get_cari_islem_history_range(start_date, end_date)
    return jsonify({"success": True, **res})

@main_bp.route('/cari-detay/<int:cari_id>')
def cari_detay_page(cari_id):
    return render_template('cari_detay.html', cari_id=cari_id)

@main_bp.route('/api/cari/detay/<int:cari_id>')
def get_cari_detay_api(cari_id):
    res = db_manager.get_cari_detail_and_history(cari_id)
    if not res:
        return jsonify({"success": False, "message": "Cari bulunamadı."}), 404
    return jsonify({"success": True, **res})

@main_bp.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    data = db_manager.get_dashboard_data()
    return jsonify(data)

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

