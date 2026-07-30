from repositories.db_core import get_db_connection
from repositories.cari_repository import get_cari_detail_and_history
from repositories.dashboard_repository import get_dashboard_data
from flask import Blueprint, request, jsonify

import datetime

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/sor', methods=['POST'])
def ai_ask():
    data = request.json or {}
    soru = data.get('soru', '').lower().strip()
    
    # Query database data
    db_data = get_dashboard_data()
    
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

@ai_bp.route('/kredibilite-analiz', methods=['POST'])
def analyze_kredibilite():
    data = request.json or {}
    cari_id = data.get('cari_id')
    if not cari_id:
        return jsonify({"success": False, "message": "Cari ID zorunludur."}), 400
        
    res = get_cari_detail_and_history(cari_id)
    if not res:
        return jsonify({"success": False, "message": "Cari bulunamadı."}), 404
        
    cari = res['cari']
    transactions = res['transactions']
    
    # Kriter 1: Ödeme Geçmişi (Borç işlemlerinin tutarı ve düzeni)
    is_musteri = cari['tip'] == 'musteri'
    total_tutar = sum(t['tutar'] for t in transactions)
    trans_count = len(transactions)
    
    # Calculate ratios
    invoice_sum = 0
    payment_sum = 0
    for t in transactions:
        if is_musteri:
            if t['tip'] == 'alacak': invoice_sum += t['tutar']
            else: payment_sum += t['tutar']
        else:
            if t['tip'] == 'borc': invoice_sum += t['tutar']
            else: payment_sum += t['tutar']
            
    # Calculate delayed payments
    delayed_count = 0
    delayed_sum = 0
    today_limit = datetime.date(2026, 7, 30)
    
    for t in transactions:
        t_val = t['tutar']
        t_date = datetime.datetime.strptime(t['tarih'], "%Y-%m-%d").date()
        is_invoice = (is_musteri and t['tip'] == 'alacak') or (not is_musteri and t['tip'] == 'borc')
        if is_invoice:
            due_date = t_date + datetime.timedelta(days=30)
            if due_date < today_limit:
                delayed_count += 1
                delayed_sum += t_val

    net_ratio = (payment_sum / invoice_sum) if invoice_sum > 0 else 1.0
    
    # Base Score calculation
    if net_ratio >= 0.95:
        score = "A+"
        ratio_desc = "Kusursuz ve zamanında ödeme disiplini."
    elif net_ratio >= 0.85:
        score = "A"
        ratio_desc = "Güvenilir nakit akışı ve istikrarlı ödeme yapısı."
    elif net_ratio >= 0.70:
        score = "B"
        ratio_desc = "Orta seviye borçluluk, sürdürülebilir döngü."
    elif net_ratio >= 0.50:
        score = "C"
        ratio_desc = "Yüksek borç oranı ve düzensiz nakit akışı."
    else:
        score = "D"
        ratio_desc = "Ciddi risk ve ödeme yetersizliği."
        
    # Findeks Rule: If there are overdue payments, suppress rating score
    score_desc = "Normal Cari Seyri"
    if delayed_count > 0:
        score_desc = "Geciken Fatura Risk Uyarısı (Findeks Skoru Düşürüldü)"
        if score == "A+": score = "A"
        elif score == "A": score = "B"
        elif score == "B": score = "C"
        elif score == "C": score = "D"
        
    # Write score back to DB to persist
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE cari SET kredibilite = ? WHERE id = ?", (score, cari_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True, 
        "kredibilite": score,
        "payment_ratio": net_ratio * 100,
        "score_desc": score_desc,
        "delayed_count": delayed_count,
        "delayed_sum": delayed_sum
    })

@ai_bp.route('/cari-sor', methods=['POST'])
def ask_cari_question():
    data = request.json or {}
    cari_id = data.get('cari_id')
    soru = data.get('soru', '').lower().strip()
    
    if not cari_id or not soru:
        return jsonify({"success": False, "message": "Cari ID ve soru zorunludur."}), 400
        
    res = get_cari_detail_and_history(cari_id)
    if not res:
        return jsonify({"success": False, "message": "Cari bulunamadı."}), 404
        
    cari = res['cari']
    transactions = res['transactions']
    
    # Precompute statistics
    is_musteri = cari['tip'] == 'musteri'
    invoice_sum = 0
    payment_sum = 0
    delayed_count = 0
    delayed_sum = 0
    
    today_limit = datetime.date(2026, 7, 30)
    
    for t in transactions:
        t_val = t['tutar']
        t_date = datetime.datetime.strptime(t['tarih'], "%Y-%m-%d").date()
        is_invoice = (is_musteri and t['tip'] == 'alacak') or (not is_musteri and t['tip'] == 'borc')
        
        if is_musteri:
            if t['tip'] == 'alacak': invoice_sum += t_val
            else: payment_sum += t_val
        else:
            if t['tip'] == 'borc': invoice_sum += t_val
            else: payment_sum += t_val
            
        if is_invoice:
            due_date = t_date + datetime.timedelta(days=30)
            if due_date < today_limit:
                delayed_count += 1
                delayed_sum += t_val
                
    net_bal = invoice_sum - payment_sum
    bal_str = f"{abs(net_bal):,.2f} TRY"
    
    # Simple rule-based chatbot replies for the specific Cari
    if 'vade' in soru or 'gecik' in soru or 'geciken' in soru or 'son gün' in soru:
        if delayed_count > 0:
            cevap = f"Bu cari hesaba ait vadesi geçen <strong>{delayed_count} adet</strong> fatura bulunmaktadır. Toplam gecikmiş bakiye tutarı <strong>{delayed_sum:,.2f} TRY</strong> seviyesindedir. Ödemenin acilen kapatılması risk yönetimi açısından kritiktir."
        else:
            cevap = "Harika! Bu cari hesaba ait vadesi geçmiş veya gecikmiş herhangi bir fatura bulunmamaktadır. Tüm işlemler zamanında kapatılmış."
            
    elif 'bakiye' in soru or 'net' in soru or 'borç' in soru or 'alacak' in soru:
        if is_musteri:
            cevap = f"Müşterinin toplam fatura tutarı <strong>{invoice_sum:,.2f} TRY</strong>, yaptığı toplam ödemeler ise <strong>{payment_sum:,.2f} TRY</strong> seviyesindedir. Net alacak bakiyemiz <strong>{bal_str}</strong>'dir."
        else:
            cevap = f"Tedarikçiden aldığımız fatura tutarı <strong>{invoice_sum:,.2f} TRY</strong>, yaptığımız toplam ödemeler ise <strong>{payment_sum:,.2f} TRY</strong> seviyesindedir. Tedarikçiye net borç bakiyemiz <strong>{bal_str}</strong>'dir."
            
    elif 'ödeme' in soru or 'performans' in soru or 'kredibilite' in soru or 'güven' in soru:
        ratio = (payment_sum / invoice_sum * 100) if invoice_sum > 0 else 100.0
        cevap = f"Cari hesabın kredibilite notu <strong>{cari['kredibilite'] or 'A'}</strong> derecesindedir. Borç kapama / tahsilat performansı <strong>%{ratio:.1f}</strong> seviyesindedir. Ödeme alışkanlıkları kararlı ve güvenilirdir."
        
    else:
        cevap = f"BulutAI Asistanı: <strong>{cari['ad']}</strong> cari hesabı hakkında toplam <strong>{len(transactions)} işlem</strong> kaydını analiz ettim. Cari tipi <strong>{ 'Müşteri' if is_musteri else 'Tedarikçi' }</strong>, kredibilite notu <strong>{cari['kredibilite'] or 'A'}</strong>, güncel net bakiyesi ise <strong>{bal_str}</strong>'dir. Daha detaylı bilgi için: 'Vadesi geçen var mı?' veya 'Bakiye durumu nedir?' gibi sorular sorabilirsiniz."
        
    return jsonify({"success": True, "cevap": cevap})

