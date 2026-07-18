from flask import Blueprint, request, jsonify
import db_manager

fatura_bp = Blueprint('fatura', __name__)

@fatura_bp.route('/ekle', methods=['POST'])
def add_fatura():
    data = request.json or {}
    unvan = data.get('unvan')
    tutar = float(data.get('tutar', 0))
    tip = data.get('tip', 'satis')
    
    if not unvan or tutar <= 0:
        return jsonify({"success": False, "message": "Cari unvanı ve tutar zorunludur."}), 400
        
    try:
        db_manager.add_fatura_record(unvan, tutar, tip)
        updated_data = db_manager.get_dashboard_data()
        return jsonify({"success": True, "data": updated_data['fatura_irsaliye']})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
