from repositories.fatura_repository import get_fatura_irsaliye_list, add_fatura_irsaliye_full, update_fatura_status, delete_fatura_record
from flask import Blueprint, request, jsonify


fatura_bp = Blueprint('fatura', __name__)

@fatura_bp.route('/liste', methods=['GET'])
def get_fatura_liste():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    durum = request.args.get('durum')
    tip = request.args.get('tip')
    
    data = get_fatura_irsaliye_list(start_date, end_date, durum, tip)
    return jsonify({"success": True, "data": data})

@fatura_bp.route('/ekle', methods=['POST'])
def add_fatura():
    data = request.json or {}
    cari_id = data.get('cari_id')
    unvan = data.get('unvan')
    belge_no = data.get('belge_no')
    tutar = float(data.get('tutar', 0))
    tip = data.get('tip', 'satis')
    durum = data.get('durum', 'Ödenmedi')
    tarih = data.get('tarih', '2026-07-24')
    aciklama = data.get('aciklama', '')
    
    if not cari_id or not unvan or (tip not in ['irsaliye'] and tutar <= 0):
        return jsonify({"success": False, "message": "Cari seçimi ve geçerli tutar zorunludur."}), 400
        
    try:
        new_id = add_fatura_irsaliye_full(cari_id, unvan, belge_no, tutar, tip, durum, tarih, aciklama)
        return jsonify({"success": True, "message": "Fatura/İrsaliye kaydı başarıyla eklendi.", "id": new_id})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@fatura_bp.route('/durum-guncelle/<int:fatura_id>', methods=['POST'])
def update_status(fatura_id):
    data = request.json or {}
    yeni_durum = data.get('durum')
    if not yeni_durum:
        return jsonify({"success": False, "message": "Yeni durum zorunludur."}), 400
    try:
        update_fatura_status(fatura_id, yeni_durum)
        return jsonify({"success": True, "message": "Durum başarıyla güncellendi."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@fatura_bp.route('/sil/<int:fatura_id>', methods=['DELETE'])
def delete_fatura(fatura_id):
    try:
        delete_fatura_record(fatura_id)
        return jsonify({"success": True, "message": "Kayıt başarıyla silindi."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
