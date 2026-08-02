from repositories.stok_repository import add_stok_item, add_stok
from repositories.dashboard_repository import get_dashboard_data
from flask import Blueprint, request, jsonify


stok_bp = Blueprint('stok', __name__)

@stok_bp.route('/ekle', methods=['POST'])
def add_stok_urun():
    data = request.json or {}
    ad = data.get('ad')
    kategori = data.get('kategori', 'Elektronik')
    adet = int(data.get('adet', 0))
    kritik_seviye = int(data.get('kritik_seviye', 10))
    
    if not ad or adet < 0:
        return jsonify({"success": False, "message": "Ürün adı zorunludur ve adet sıfırdan küçük olamaz."}), 400
        
    try:
        add_stok_item(ad, kategori, adet, kritik_seviye)
        updated_data = get_dashboard_data()
        return jsonify({"success": True, "data": updated_data['stok']})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
