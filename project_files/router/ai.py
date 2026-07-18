from flask import Blueprint, request, jsonify
import db_manager

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/sor', methods=['POST'])
def ai_ask():
    data = request.json or {}
    soru = data.get('soru', '').lower().strip()
    
    # Query database data
    db_data = db_manager.get_dashboard_data()
    
    total_alacak = db_data['cari']['toplam_alacak']
    total_borc = db_data['cari']['toplam_borc']
    kasa_bakiye = db_data['kasa_banka']['kasa_bakiye']
    banka_bakiye = db_data['kasa_banka']['banka_bakiye']
    toplam_nakit = db_data['kasa_banka']['toplam_nakit']
    kritik_stok = db_data['stok']['kritik_stok_sayisi']
    urun_sayisi = db_data['stok']['toplam_urun_cesidi']
    odenmemis_fatura = db_data['fatura_irsaliye']['odenmemis_fatura']
    aylik_fatura_tutari = db_data['fatura_irsaliye']['aylik_fatura_tutari']
    
    if 'kasa' in soru or 'banka' in soru or 'nakit' in soru or 'para' in soru or 'likidite' in soru:
        cevap = f"Bulutİş verilerine göre, şu anda Merkez Kasa bakiyeniz <strong>{kasa_bakiye:,.2f} TL</strong>, Banka hesap bakiyeniz <strong>{banka_bakiye:,.2f} TL</strong>'dir. Toplam net likiditeniz ise <strong>{toplam_nakit:,.2f} TL</strong> seviyesindedir. Son 30 günde kasaya giren nakit akışı oldukça kararlı görünmektedir."
    elif 'stok' in soru or 'envanter' in soru or 'ürün' in soru or 'depo' in soru:
        cevap = f"Sistemde kayıtlı toplam <strong>{urun_sayisi}</strong> farklı ürün çeşidi bulunmaktadır. Bunlardan <strong>{kritik_stok}</strong> adedi kritik stok seviyesinin (minimum eşik) altına düşmüştür. Özellikle envanterinizi korumak için kritik seviyedeki ürünleri tedarik etmenizi öneririm."
    elif 'cari' in soru or 'müşteri' in soru or 'tedarikçi' in soru or 'alacak' in soru or 'borç' in soru:
        denge = total_alacak - total_borc
        denge_str = "pozitif" if denge >= 0 else "negatif"
        cevap = f"Cari hesap durumunuza göre, toplam alacaklarınız <strong>{total_alacak:,.2f} TL</strong>, toplam borçlarınız ise <strong>{total_borc:,.2f} TL</strong>'dir. Cari dengeniz <strong>{abs(denge):,.2f} TL</strong> ile <strong>{denge_str}</strong> yöndedir. Müşterilerinizden alacak tahsilatlarını hızlandırmanız borç ödeme kapasitenizi artıracaktır."
    elif 'fatura' in soru or 'irsaliye' in soru or 'ödeme' in soru:
        cevap = f"Bu ay kesilen toplam fatura tutarınız <strong>{aylik_fatura_tutari:,.2f} TL</strong>'dir. Sistemde şu anda ödeme bekleyen <strong>{odenmemis_fatura}</strong> adet fatura bulunmaktadır. Bunların takibini 'Fatura ve İrsaliye' panelinden yapabilirsiniz."
    elif 'tavsiye' in soru or 'analiz' in soru or 'öneri' in soru or 'durum' in soru:
        denge = total_alacak - total_borc
        cevap = f"<strong>Genel Durum Analizi:</strong><br>• Finansal olarak net nakit gücünüz <strong>{toplam_nakit:,.2f} TL</strong> ile yüksek seviyede.<br>• Cari dengeniz {total_alacak - total_borc:,.2f} TL net fark ile olumlu seyrediyor.<br>• Ancak, <strong>{kritik_stok}</strong> adet ürününüzün kritik stok seviyesinde olması tedarik zincirinizde aksamalara yol açabilir. Stok alımlarını planlamanız önerilir."
    else:
        cevap = "Merhaba! Ben BulutAI asistanınız. Size şirketinizin güncel Cari Borç/Alacak dengesi, Kasa/Banka bakiyeleri, Stok seviyeleri ve Fatura durumları hakkında canlı analizler sunabilirim. Örn: 'Kasa durumum nedir?' veya 'Stok analizi yapar mısın?' gibi sorular sorabilirsiniz."
        
    return jsonify({"success": True, "cevap": cevap})
