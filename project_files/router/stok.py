from flask import Blueprint, request, jsonify
import db_manager

stok_bp = Blueprint('stok', __name__)

@stok_bp.route('/ekle', methods=['POST'])
def add_stok_urun():
    data = request.json or {}
    ad = data.get('ad')
    kategori = data.get('kategori', 'Elektronik')
    adet = int(data.get('adet', 0))
    
    if not ad or adet <= 0:
        return jsonify({"success": False, "message": "Ürün adı ve adet zorunludur."}), 400
        
    try:
        db_manager.add_stok_item(ad, kategori, adet)
        updated_data = db_manager.get_dashboard_data()
        return jsonify({"success": True, "data": updated_data['stok']})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
