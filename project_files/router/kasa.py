from flask import Blueprint, request, jsonify
import db_manager
from repositories import KasaBankaService

kasa_bp = Blueprint('kasa', __name__)


def _svc() -> KasaBankaService:
    """
    Her istek için bağımsız bir service örneği döner (thread-safe).
    Dependency Inversion: Router sqlite3'e değil, KasaBankaService soyutlamasına bağlıdır.
    """
    return KasaBankaService(db_manager.get_db_connection)


# ---------------------------------------------------------------------------
# POST /api/kasa-banka/hesap-ekle
# ---------------------------------------------------------------------------
@kasa_bp.route('/hesap-ekle', methods=['POST'])
def add_account():
    """Yeni kasa veya banka hesabı oluşturur."""
    data = request.json or {}
    ad = (data.get('ad') or '').strip()
    if not ad:
        return jsonify({'success': False, 'message': 'Hesap Adı zorunludur.'}), 400
    try:
        _svc().hesap_repo.create(
            ad=ad,
            tur=data.get('tur', 'kasa'),
            hesap_no=data.get('hesap_no', ''),
            iban=data.get('iban', ''),
            sube=data.get('sube', ''),
            doviz_turu=data.get('doviz_turu', 'TRY'),
            kredibilite=data.get('kredibilite', 'A'),
        )
        return jsonify({'success': True})
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


# ---------------------------------------------------------------------------
# POST /api/kasa-banka/islem-ekle
# ---------------------------------------------------------------------------
@kasa_bp.route('/islem-ekle', methods=['POST'])
def add_transaction():
    """Mevcut bir hesaba işlem ekler; cari bağlantısı varsa cari_islem'e de yansır."""
    data = request.json or {}
    hesap_id = data.get('hesap_id')
    tanim = (data.get('tanim') or '').strip()

    if not hesap_id or not tanim:
        return jsonify({
            'success': False,
            'message': 'hesap_id, tanim ve tutar alanları zorunludur.'
        }), 400

    try:
        tutar = float(data.get('tutar', 0))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Geçersiz tutar değeri.'}), 400

    if tutar == 0:
        return jsonify({'success': False, 'message': 'Tutar sıfır olamaz.'}), 400

    cari_id_raw = data.get('cari_id')
    cari_id = int(cari_id_raw) if cari_id_raw else None

    try:
        _svc().add_transaction(
            hesap_id=int(hesap_id),
            tanim=tanim,
            tutar=tutar,
            islem_turu=data.get('islem_turu', 'gelir'),
            tarih=data.get('tarih') or str(__import__('datetime').date.today()),
            cari_id=cari_id,
        )
        return jsonify({'success': True})
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/kasa-banka/hesaplar
# ---------------------------------------------------------------------------
@kasa_bp.route('/hesaplar', methods=['GET'])
def get_accounts():
    """Tüm hesapları ya da tur parametresiyle filtrelenmiş hesapları döner."""
    tur = request.args.get('tur') or None
    try:
        accounts = _svc().hesap_repo.get_all(tur)
        return jsonify({'success': True, 'data': accounts})
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/kasa-banka/hareketler
# ---------------------------------------------------------------------------
@kasa_bp.route('/hareketler', methods=['GET'])
def get_transactions():
    """Filtrelenebilir kasa/banka işlem geçmişi; toplam giriş/çıkış/net döner."""
    hesap_id_raw = request.args.get('hesap_id')
    hesap_id = int(hesap_id_raw) if hesap_id_raw else None
    start_date = request.args.get('start_date') or None
    end_date = request.args.get('end_date') or None
    tur = request.args.get('tur') or None

    try:
        svc = _svc()
        rows = svc.islem_repo.get_history(hesap_id, start_date, end_date, tur)
        total_giris = sum(r['tutar'] for r in rows if r['tip'] == 'giris')
        total_cikis = sum(r['tutar'] for r in rows if r['tip'] == 'cikis')
        return jsonify({
            'success': True,
            'liste': rows,
            'total_giris': total_giris,
            'total_cikis': total_cikis,
            'net_denge': total_giris - total_cikis,
        })
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/kasa-banka/detay/<hesap_id>
# ---------------------------------------------------------------------------
@kasa_bp.route('/detay/<int:hesap_id>', methods=['GET'])
def get_account_detail(hesap_id: int):
    """Hesap kartı bilgisi + işlem geçmişini döner."""
    try:
        result = _svc().get_account_detail(hesap_id)
        if not result:
            return jsonify({'success': False, 'message': 'Hesap bulunamadı.'}), 404
        return jsonify({'success': True, **result})
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500
