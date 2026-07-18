from flask import Blueprint, request, jsonify
import db_manager

cari_bp = Blueprint('cari', __name__)

@cari_bp.route('/ekle', methods=['POST'])
def add_cari():
    data = request.json or {}
    ad = data.get('ad')
    tip = data.get('tip', 'musteri')
    limit = float(data.get('limit', 0))
    vergi_no = data.get('vergi_no')
    vergi_dairesi = data.get('vergi_dairesi', '')
    yetkili_kisi = data.get('yetkili_kisi')
    eposta = data.get('eposta', '')
    telefon = data.get('telefon', '')
    il = data.get('il', '')
    ilce = data.get('ilce', '')
    mahalle = data.get('mahalle', '')
    adres_detay = data.get('adres_detay', '')
    cari_grubu = data.get('cari_grubu', '')
    kredibilite = data.get('kredibilite', 'A')
    
    # Validation of required fields
    if not ad or not ad.strip():
        return jsonify({"success": False, "message": "Cari Ünvanı / Müşteri Adı alanı zorunludur."}), 400
    if not vergi_no or not vergi_no.strip():
        return jsonify({"success": False, "message": "Vergi No / TC Kimlik No alanı zorunludur."}), 400
    if not yetkili_kisi or not yetkili_kisi.strip():
        return jsonify({"success": False, "message": "Yetkili Kişi alanı zorunludur."}), 400
        
    try:
        db_manager.add_cari_record(ad, tip, limit, vergi_no, vergi_dairesi, yetkili_kisi, eposta, telefon, il, ilce, mahalle, adres_detay, cari_grubu, kredibilite)
        updated_data = db_manager.get_dashboard_data()
        return jsonify({"success": True, "data": updated_data['cari']})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
