from repositories.db_core import get_db_connection
from repositories.cari_repository import get_cari_detail_and_history
from repositories.dashboard_repository import get_dashboard_data
from flask import Blueprint, request, jsonify
import datetime
import os
import json
import requests

ai_bp = Blueprint('ai', __name__)

def format_date_tr(date_str):
    if not date_str:
        return ""
    date_str = str(date_str).strip()
    # Eğer tarihin içinde saat de varsa split edelim
    date_str = date_str.split(" ")[0]
    try:
        if "-" in date_str:
            d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        else:
            d = datetime.datetime.strptime(date_str, "%Y%m%d")
        return d.strftime("%d.%m.%Y")
    except Exception:
        return date_str

def format_markdown_to_html(text):
    """Lokal modellerden gelen ham Markdown çıktılarını zengin HTML formatına dönüştürür."""
    import re
    if not text:
        return ""
        
    # Convert headers: ### header -> <br><strong>header</strong><br>
    text = re.sub(r'###\s*(.*?)(?:\n|$)', r'<br><strong>\1</strong><br>', text)
    text = re.sub(r'##\s*(.*?)(?:\n|$)', r'<br><strong>\1</strong><br>', text)
    text = re.sub(r'#\s*(.*?)(?:\n|$)', r'<br><strong>\1</strong><br>', text)
    
    # Convert bold: **text** -> <strong>text</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert bullet points: * item or - item -> <br>• item
    text = re.sub(r'(?:^|\n)\s*[\*\-]\s*(.*?)(?:\n|$)', r'<br>• \1<br>', text)
    
    # Replace newlines with <br>
    text = text.replace('\n', '<br>')
    
    # Clean up multiple consecutive <br>
    text = re.sub(r'(<br>\s*)+', '<br>', text)
    
    while text.startswith('<br>') or text.startswith(' '):
        text = text[4:] if text.startswith('<br>') else text[1:]
    while text.endswith('<br>') or text.endswith(' '):
        text = text[:-4] if text.endswith('<br>') else text[:-1]
    return text.strip()

def run_llm_chain(prompt_text, system_message=None, history=None):
    """Lokal Ollama veya Bulut Gemini API kullanarak LLM çalıştırır."""
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
    
    if provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API seçildi ancak '.env' dosyasında 'GEMINI_API_KEY' tanımlanmamış. "
                "Lütfen Google AI Studio'dan aldığınız API anahtarını ekleyin."
            )
            
        configured_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
        fallback_models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash"]
        
        # Ensure configured model is checked first
        if configured_model in fallback_models:
            fallback_models.remove(configured_model)
        fallback_models.insert(0, configured_model)
        
        last_exception = None
        for model_name in fallback_models:
            contents = []
            if history:
                for msg in history[-10:]:
                    if 'role' in msg and 'content' in msg:
                        role = "user" if msg['role'] == "user" else "model"
                        contents.append({
                            "role": role,
                            "parts": [{"text": msg['content']}]
                        })
            contents.append({
                "role": "user",
                "parts": [{"text": prompt_text}]
            })
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.3
                }
            }
            if system_message:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_message}]
                }
                
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            try:
                print(f"[*] Calling Gemini model: {model_name}...", flush=True)
                response = requests.post(url, json=payload, timeout=45)
                
                # Check for rate limit
                if response.status_code == 429:
                    print(f"[!] Gemini model {model_name} returned 429. Trying next model...", flush=True)
                    continue
                    
                response.raise_for_status()
                res_data = response.json()
                candidate = res_data.get('candidates', [{}])[0]
                part = candidate.get('content', {}).get('parts', [{}])[0]
                raw_content = part.get('text', '')
                if not raw_content:
                    raise ValueError("Gemini API boş bir yanıt döndürdü.")
                return raw_content
            except Exception as e:
                print(f"[!] Error calling Gemini model {model_name}: {str(e)}. Trying next...", flush=True)
                last_exception = e
                continue
                
        # If all Gemini models fail, fall back to Ollama
        print("[!] All Gemini models failed or rate-limited. Falling back to local Ollama (Gemma)...", flush=True)
        provider = "ollama"
        
    # Local Ollama fallback
    if provider == "ollama":
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
        model_name = os.environ.get("OLLAMA_MODEL", "llama3")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
            
        if history:
            for msg in history[-10:]:
                if 'role' in msg and 'content' in msg:
                    messages.append({"role": msg['role'], "content": msg['content']})
                    
        messages.append({"role": "user", "content": prompt_text})
        
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": 8192
            }
        }
        
        try:
            response = requests.post(ollama_url, json=payload, timeout=120)
            if response.status_code == 404:
                raise ValueError(f"'{model_name}' modeli yerel Ollama sunucunuzda bulunamadı veya indirme işlemi (pull) henüz tamamlanmadı. Lütfen indirme işleminin bitmesini bekleyin.")
            response.raise_for_status()
            data = response.json()
            raw_content = data["message"]["content"]
            return raw_content
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            raise ConnectionError(
                f"Lokal Ollama sunucusuna bağlanılamadı. Lütfen Ollama uygulamasının arka planda çalıştığından "
                f"ve '{model_name}' modelinin kurulu olduğundan emin olun. Hata: {str(e)}"
            )

def get_global_rag_context(soru=None):
    """Tüm şirketin özet finansal ve operasyonel profilini hazırlar."""
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
    
    soru_lower = soru.lower() if soru else ""
    
    # Conditional loading flags based on keywords in user question
    is_stok_query = any(k in soru_lower for k in ['stok', 'ürün', 'envanter', 'adet', 'kritik', 'depo', 'çimento', 'demir', 'tuğla', 'alçıpan', 'kablo'])
    is_cari_query = any(k in soru_lower for k in ['cari', 'borç', 'alacak', 'müşteri', 'tedarikçi', 'bakiye', 'limit', 'kredibilite'])
    is_kasa_query = any(k in soru_lower for k in ['kasa', 'banka', 'nakit', 'hesap', 'para', 'döviz', 'likidite', 'tl', 'usd', 'eur'])
    
    # If no specific topic is detected, load a generalized overview of all sections
    if not (is_stok_query or is_cari_query or is_kasa_query):
        is_stok_query = True
        is_cari_query = True
        is_kasa_query = True
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get extra counts explicitly for context
    cursor.execute("SELECT COUNT(*) FROM kasa_banka_hesap WHERE tur = 'kasa'")
    kasa_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM kasa_banka_hesap WHERE tur = 'banka'")
    banka_count = cursor.fetchone()[0]
    
    # 1. Fetch stock items
    all_stocks = []
    critical_products = []
    if is_stok_query:
        cursor.execute("SELECT ad, kategori, adet FROM stok ORDER BY ad ASC")
        all_stocks = [dict(r) for r in cursor.fetchall()]
    else:
        cursor.execute("SELECT ad, adet FROM stok WHERE adet < 15")
        critical_products = [dict(r) for r in cursor.fetchall()]
        
    # 2. Fetch cash & bank accounts
    accounts_detail = []
    if is_kasa_query:
        cursor.execute("SELECT ad, tur, bakiye, doviz_turu FROM kasa_banka_hesap")
        accounts_detail = [dict(r) for r in cursor.fetchall()]
        
    # 3. Fetch cariler list
    top_caris = []
    all_cariler = []
    if is_cari_query:
        from repositories.cari_repository import get_all_cariler
        all_cariler = get_all_cariler()
    else:
        cursor.execute("SELECT ad, tip, kredibilite, limit_val FROM cari ORDER BY limit_val DESC LIMIT 6")
        top_caris = [dict(r) for r in cursor.fetchall()]
        
    # 4. Fetch unpaid invoices
    unpaid_invoices = []
    if is_cari_query or is_kasa_query:
        cursor.execute("""
            SELECT f.belge_no, f.tanim, f.tutar, f.durum, f.tarih, c.ad as cari_ad
            FROM fatura_irsaliye f
            LEFT JOIN cari c ON f.cari_id = c.id
            WHERE f.durum != 'Ödendi' AND f.belge_turu = 'fatura'
            ORDER BY f.tarih DESC LIMIT 15
        """)
        unpaid_invoices = [dict(r) for r in cursor.fetchall()]
        
    conn.close()
    
    context = f"""
### Şirket Genel Finansal Durumu
- **Cari Kart Sayısı**: Toplam {db_data['cari']['musteri_sayisi'] + db_data['cari']['tedarikci_sayisi']} adet ({db_data['cari']['musteri_sayisi']} Müşteri, {db_data['cari']['tedarikci_sayisi']} Tedarikçi)
- **Cari Borç/Alacak Dengesi**: Toplam Müşteri Limiti (Alacak): {total_alacak:,.2f} TL | Toplam Tedarikçi Limiti (Borç): {total_borc:,.2f} TL | Net Fark: {total_alacak - total_borc:,.2f} TL

- **Kasa/Banka Hesap Sayısı**: Toplam {kasa_count + banka_count} adet ({kasa_count} Kasa, {banka_count} Banka Hesabı)
- **Toplam Likidite (Nakit)**: {toplam_nakit:,.2f} TL (Kasalardaki Toplam: {kasa_bakiye:,.2f} TL, Bankalardaki Toplam: {banka_bakiye:,.2f} TL)
- **Aylık Nakit Akışı**: Bu Ay Tahsilat (Gelir): {db_data['kasa_banka']['aylik_gelir']:,.2f} TL | Bu Ay Ödeme (Gider): {db_data['kasa_banka']['aylik_gider']:,.2f} TL

- **Fatura & İrsaliye Durumu**: Kesilen Toplam Fatura Sayısı: {db_data['fatura_irsaliye']['kesilen_fatura_bu_ay']} adet | Ödenmemiş Açık Fatura Sayısı: {odenmemis_fatura} adet | Bekleyen/Sevk Edilmemiş İrsaliye Sayısı: {db_data['fatura_irsaliye']['bekleyen_irsaliye']} adet
- **Aylık Fatura Hacmi**: {aylik_fatura_tutari:,.2f} TL

- **Envanter (Stok) Sayısı**: Sistemde Kayıtlı Toplam Ürün (Stok Kartı) Çeşidi: {urun_sayisi} adet
- **Stok Risk Durumu**: Kritik Stok Seviyesinin Altındaki Ürün Sayısı: {kritik_stok} adet | Stoğu Tamamen Tükenmiş (0) Ürün Sayısı: {db_data['stok']['stoksuz_urun_sayisi']} adet
- **Depo Doluluk Oranı**: %{db_data['stok']['depo_doluluk_orani']}
"""
    if accounts_detail:
        context += "\n### Aktif Kasa ve Banka Hesapları Detayı\n"
        for a in accounts_detail:
            tur_label = "Kasa" if a['tur'] == 'kasa' else "Banka"
            context += f"- **{a['ad']}** ({tur_label}) | Bakiye: {a['bakiye']:,.2f} {a['doviz_turu']}\n"
            
    if all_stocks:
        context += "\n### Şirket Envanter ve Stok Bilgileri (Tüm Liste)\n"
        for p in all_stocks:
            status_label = " (KRİTİK STOK)" if p['adet'] < 15 else ""
            context += f"- **{p['ad']}** (Kategori: {p['kategori']}) | Stok Miktarı: {p['adet']} adet{status_label} | Kritik Sınır: 15 adet\n"
    elif critical_products:
        context += "\n### Kritik Stok Seviyesindeki Ürünler Detayı\n"
        for p in critical_products:
            context += f"- **{p['ad']}** | Mevcut Stok: {p['adet']} | Kritik Seviye Sınırı: 15\n"
            
    if all_cariler:
        context += "\n### Şirket Cari Hesapları (Müşteri & Tedarikçi) Durumu (Tüm Liste)\n"
        for c in all_cariler:
            tip_str = "Müşteri" if c['tip'] == 'musteri' else "Tedarikçi"
            bal_str = f"Bakiye: {abs(c['bakiye']):,.2f} TL"
            if c['bakiye'] > 0:
                bal_str += " (Alacak Bakiyemiz / Müşterinin Borcu)" if c['tip'] == 'musteri' else " (Alacak Bakiyemiz / Bizim Fazla Ödememiz)"
            elif c['bakiye'] < 0:
                bal_str += " (Borç Bakiyemiz / Tedarikçiye Borcumuz)" if c['tip'] == 'tedarikci' else " (Borç Bakiyemiz / Müşterinin Fazla Ödemesi)"
            else:
                bal_str += " (Kapalı Hesap / Bakiye Yok)"
            context += f"- **{c['ad']}** ({tip_str}) | {bal_str} | Limit: {c['limit_val']:,.2f} TL | Kredibilite: {c['kredibilite'] or 'B'}\n"
    elif top_caris:
        context += "\n### Şirketteki En Yüksek Risk Limitli Cariler\n"
        for c in top_caris:
            tip_str = "Müşteri" if c['tip'] == 'musteri' else "Tedarikçi"
            context += f"- **{c['ad']}** ({tip_str}) | Limit: {c['limit_val']:,.2f} TL | Kredibilite Notu: {c['kredibilite'] or 'B'}\n"
            
    if unpaid_invoices:
        context += "\n### Güncel Ödenmemiş / Açık Faturalar (Son 15)\n"
        for f in unpaid_invoices:
            context += f"- **{f['belge_no']}** ({f['tanim']}) | Cari: {f['cari_ad']} | Tutar: {f['tutar']:,.2f} TL | Tarih: {format_date_tr(f['tarih'])} | Durum: {f['durum']}\n"
        
    return context

def get_rag_context_for_cari(cari_id):
    """Belirli bir carinin detay bilgilerini, işlem geçmişini ve vade analizini hazırlar."""
    res = get_cari_detail_and_history(cari_id)
    if not res:
        return "Cari hesap bulunamadı."
        
    cari = res['cari']
    transactions = res['transactions']
    
    is_musteri = cari['tip'] == 'musteri'
    total_invoiced = 0
    total_paid = 0
    overdue_invoices = []
    
    # Baseline limit for overdue analysis
    today = datetime.date(2026, 7, 31)
    
    for t in transactions:
        t_val = t['tutar']
        t_date = datetime.datetime.strptime(t['tarih'], "%Y-%m-%d").date()
        is_invoice = (is_musteri and t['islem_tipi'] == 'alacak') or (not is_musteri and t['islem_tipi'] == 'borc')
        
        if is_musteri:
            if t['islem_tipi'] == 'alacak':
                total_invoiced += t_val
            else:
                total_paid += t_val
        else:
            if t['islem_tipi'] == 'borc':
                total_invoiced += t_val
            else:
                total_paid += t_val
                
        if is_invoice:
            due_date = t_date + datetime.timedelta(days=30)
            if due_date < today:
                overdue_invoices.append({
                    "belge_no": t['belge_no'],
                    "tarih": t['tarih'],
                    "tutar": t_val,
                    "vade_tarihi": due_date.strftime("%Y-%m-%d")
                })
                
    bakiye = total_invoiced - total_paid
    bakiye_yon = "Müşterinin Şirkete Borcu Var (Alacak Bakiyemiz)" if bakiye >= 0 else "Şirketin Tedarikçiye Borcu Var (Borç Bakiyemiz)"
    
    context = f"""
### Cari Hesap Künye Bilgileri
- **Cari Ünvanı**: {cari['ad']}
- **Hesap Tipi**: {'Müşteri' if is_musteri else 'Tedarikçi'}
- **Vergi Kimlik**: {cari['vergi_no']} | Vergi Dairesi: {cari['vergi_dairesi']}
- **Güncel Kredibilite Notu**: {cari['kredibilite'] or 'B'}
- **Risk Limiti**: {cari['limit_val']:,.2f} TL
- **Sektörel Grup**: {cari['cari_grubu']}
- **Lokasyon**: {cari['ilce']} / {cari['il']}

### Finansal Bilanço ve Bakiye Özeti
- **Toplam Faturalanan Tutar**: {total_invoiced:,.2f} TL
- **Toplam Kapatılan / Ödenen Tutar**: {total_paid:,.2f} TL
- **Net Kalan Bakiye**: {abs(bakiye):,.2f} TL ({bakiye_yon})
- **Kalan Risk Limiti Kapasitesi**: {(cari['limit_val'] - abs(bakiye) if bakiye >= 0 else cari['limit_val']):,.2f} TL

### Son 10 Cari Hesap Hareketi
"""
    for t in transactions[:10]:
        tip_label = "Fatura (Satış)" if (is_musteri and t['islem_tipi'] == 'alacak') else \
                    "Tahsilat (Giriş)" if (is_musteri and t['islem_tipi'] == 'borc') else \
                    "Fatura (Alış)" if (not is_musteri and t['islem_tipi'] == 'borc') else \
                    "Ödeme (Çıkış)"
        context += f"- {format_date_tr(t['tarih'])} | Belge: {t['belge_no']} | {tip_label} | Tutar: {t['tutar']:,.2f} TL | Açıklama: {t['aciklama']}\n"
        
    if overdue_invoices:
        context += "\n### Vadesi Geciken ve Risk Oluşturan Faturalar\n"
        for o in overdue_invoices[:5]:
            context += f"- Belge: {o['belge_no']} | Tarih: {format_date_tr(o['tarih'])} | Son Ödeme (Vade): {format_date_tr(o['vade_tarihi'])} | Tutar: {o['tutar']:,.2f} TL\n"
    else:
        context += "\n- Vadesi geçmiş veya risk teşkil eden herhangi bir açık fatura kaydı bulunmamaktadır.\n"
        
    return context

SQL_SYSTEM_PROMPT = """
Sen SQLite veritabanı uzmanı bir AI asistansın. Kullanıcının sorusuna cevap bulmak için SQLite veritabanımız üzerinde çalışacak geçerli bir SQL sorgusu hazırlamalısın.
Eğer kullanıcının sorusu veritabanından doğrudan sorgulanacak bir bilgi içeriyorsa (stok adetleri, cari bakiyeleri, kasa/banka hesap sayıları, belirli faturalar veya işlemler gibi), YALNIZCA çalıştırılabilir bir SQLite SELECT sorgusu dönmelisin.
Sorguda markdown kod blokları (```sql veya ```) veya açıklama satırları asla kullanma, doğrudan "SELECT ..." ile başlayan düz metin dön.
Eğer kullanıcının sorusu veritabanı sorgusu gerektirmeyen genel bir sohbet veya açıklama ise (örn: "selam", "nasılsın", "teşekkürler"), YALNIZCA "NO_SQL" ifadesini dön.

VERİTABANI TABLO ŞEMALARI VE ALANLARI:
1. `stok` (Ürün envanteri)
   - id (INTEGER)
   - ad (TEXT): Ürün adı (örn: 'Çimento (50 kg)', 'Tuğla (Standart)')
   - kategori (TEXT)
   - adet (INTEGER): Mevcut stok miktarı
2. `cari` (Müşteri ve Tedarikçiler)
   - id (INTEGER)
   - ad (TEXT): Cari ünvanı (örn: 'Kılıç Teknoloji', 'Aksoy İnşaat')
   - tip (TEXT): 'musteri' veya 'tedarikci'
   - limit_val (REAL): Risk limiti tutarı
   - vergi_no (TEXT)
   - kredibilite (TEXT): 'A+', 'A', 'B', 'C', 'D'
3. `kasa_banka_hesap` (Kasa ve Banka hesapları)
   - id (INTEGER)
   - ad (TEXT): Hesap adı (örn: 'Merkez Kasa', 'Kuveyt Türk - Kurumsal Şube (TRY)')
   - tur (TEXT): 'kasa' veya 'banka'
   - bakiye (REAL): Hesap bakiyesi
   - doviz_turu (TEXT): 'TRY', 'USD', 'EUR'
4. `fatura_irsaliye` (Faturalar ve İrsaliyeler)
   - id (INTEGER)
   - cari_id (INTEGER) -> cari.id
   - belge_no (TEXT)
   - belge_turu (TEXT): 'satis_faturasi', 'alis_faturasi', 'irsaliye', 'irsaliyeli_fatura'
   - tanim (TEXT)
   - tutar (REAL)
   - durum (TEXT): 'Ödendi', 'Ödenmedi', 'Bekliyor', 'Teslim Edildi'
   - tarih (TEXT): 'YYYY-MM-DD'
5. `cari_islem` (Cari hesap hareketleri/faturalar)
   - id (INTEGER)
   - cari_id (INTEGER) -> cari.id
   - tanim (TEXT)
   - tutar (REAL)
   - tip (TEXT): 'alacak' veya 'borc'
   - tarih (TEXT): 'YYYY-MM-DD'
   - odeme_tarihi (TEXT) -> NULL ise ödenmemiş demektir.
6. `kasa_banka_islem` (Kasa ve Banka hareketleri - Tahsilat ve Ödemeler)
   - id (INTEGER)
   - hesap_id (INTEGER) -> kasa_banka_hesap.id
   - cari_id (INTEGER) -> cari.id
   - tanim (TEXT)
   - tutar (REAL)
   - tip (TEXT): 'giris' (tahsilat/gelir) veya 'cikis' (ödeme/gider)
   - tarih (TEXT): 'YYYY-MM-DD'
   - islem_turu (TEXT): 'tahsilat', 'odeme', 'transfer', 'gelir', 'gider'


Örnek Sorular ve Çıktılar:
Soru: Kaç tane kasam var?
Çıktı: SELECT count(*) FROM kasa_banka_hesap WHERE tur = 'kasa';

Soru: Aksoy İnşaat'ın kredibilitesi nedir?
Çıktı: SELECT kredibilite FROM cari WHERE ad LIKE '%Aksoy İnşaat%';

Soru: Çimento stoğu ne kadar?
Çıktı: SELECT adet FROM stok WHERE ad LIKE '%Çimento%';

Soru: Merhaba nasılsın?
Çıktı: NO_SQL
"""

def execute_sql_query(sql):
    """Verilen SQL sorgusunu veritabanında çalıştırır ve sonucu list formatında döner."""
    clean_sql = sql.strip().strip(';').strip()
    # Remove markdown code formatting if any survived
    clean_sql = clean_sql.replace('```sql', '').replace('```', '').strip()
    if not clean_sql.upper().startswith('SELECT'):
        return "Hata: Yalnızca veri okuma (SELECT) sorguları desteklenmektedir."
        
    try:
        conn = get_db_connection()
        conn.row_factory = None
        cursor = conn.cursor()
        cursor.execute(clean_sql)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        return f"Hata (SQL Çalıştırılamadı): {str(e)}"

@ai_bp.route('/sor', methods=['POST'])
def ai_ask():
    data = request.json or {}
    soru = data.get('soru', '').strip()
    history = data.get('history', [])
    
    # 1. Ask Gemma to write SQL query
    sql_prompt = f"Kullanıcı Sorusu: {soru}"
    sql_query_raw = run_llm_chain(sql_prompt, SQL_SYSTEM_PROMPT).strip()
    
    # Clean up markdown block if model outputted it
    import re
    match = re.search(r'```sql\s*(.*?)\s*```', sql_query_raw, re.DOTALL | re.IGNORECASE)
    if match:
        sql_query_raw = match.group(1).strip()
    else:
        match_generic = re.search(r'```\s*(.*?)\s*```', sql_query_raw, re.DOTALL)
        if match_generic:
            sql_query_raw = match_generic.group(1).strip()
            
    sql_query = sql_query_raw.strip().replace('\n', ' ')
    
    sql_results = None
    sql_execution_context = ""
    
    # 2. Execute SQL if not NO_SQL and query starts with SELECT
    is_valid_sql = "NO_SQL" not in sql_query and any(x in sql_query.upper() for x in ["SELECT", "FROM"])
    if is_valid_sql:
        results = execute_sql_query(sql_query)
        sql_results = results
        sql_execution_context = f"\n### SQL Sorgusu ve Sonucu\nÇalıştırılan Sorgu: {sql_query}\nSorgu Sonucu: {str(results)}\n"
    
    # 3. Get the standard global RAG context
    global_context = get_global_rag_context(soru)
    
    # 4. Combine global context and SQL execution results
    combined_context = global_context
    if sql_execution_context:
        combined_context = sql_execution_context + "\n" + global_context
        
    system_prompt = (
        "Sen BulutAI, Bulutİş ERP sisteminin entegre yapay zeka finansal asistanısın. "
        "Aşağıdaki şirket finansal özeti verilerine sadık kalarak kullanıcının sorusuna Türkçe, "
        "net, doğru ve finansal analizlerle desteklenmiş eyleme dönüştürülebilir yanıtlar vermelisin.\n"
        "ÖNEMLİ: Eğer bağlamda '### SQL Sorgusu ve Sonucu' varsa, kullanıcının sorusuna doğrudan ve kesin olarak "
        "bu SQL sorgusu sonucundaki veriye dayanarak cevap ver! Yanlış veya tahmini sayılar söyleme.\n"
        "Cevap verirken sadece ham sayıyı yazmak yerine, sorunun içeriğine uygun tam bir açıklayıcı cümle kur (örn: 'Sistemde kayıtlı 5 adet kasa bulunmaktadır').\n"
        "ÖNEMLİ KURALLAR:\n"
        "1. Asla markdown biçimlendirmesi (###, **, *, ***, #, vb.) kullanma.\n"
        "2. Önemli finansal tutarları, bakiye durumlarını veya kelimeleri <strong> </strong> arasına al.\n"
        "3. Satır başları veya listelemeler için direkt <br> veya <ul><li> etiketlerini kullan.\n"
        "4. Cevabını gereksiz yere uzatma, anlaşılır ve net tut."
    )
    prompt = f"""
Şirket Finansal Veri Bağlamı (Context):
{combined_context}

Kullanıcı Sorusu:
{soru}
"""
    
    try:
        cevap = run_llm_chain(prompt, system_prompt, history)
        formatted_cevap = format_markdown_to_html(cevap)
        
        # No SQL query is printed at the bottom as requested
            
        return jsonify({"success": True, "cevap": formatted_cevap})
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lokal Yapay Zeka Hatası: {str(e)}"
        }), 500

@ai_bp.route('/cari-sor', methods=['POST'])
def ask_cari_question():
    data = request.json or {}
    cari_id = data.get('cari_id')
    soru = data.get('soru', '').strip()
    history = data.get('history', [])
    
    if not cari_id or not soru:
        return jsonify({"success": False, "message": "Cari ID ve soru zorunludur."}), 400
        
    res = get_cari_detail_and_history(cari_id)
    if not res:
        return jsonify({"success": False, "message": "Cari bulunamadı."}), 404
        
    context = get_rag_context_for_cari(cari_id)
    
    system_prompt = (
        "Sen BulutAI, bu cariden (müşteri/tedarikçi) sorumlu kıdemli kredi risk analistisin. "
        "Kullanıcının sorusuna verilen geçmiş verilerine tam olarak sadık kalarak, tarihleri ve tutarları "
        "birebir referans göstererek Türkçe, doğru ve profesyonel bir üslupla cevap vermelisin.\n"
        "ÖNEMLİ KURALLAR:\n"
        "1. Asla markdown biçimlendirmesi (###, **, *, ***, #, vb.) kullanma.\n"
        "2. Önemli finansal tutarları, bakiye durumlarını veya kelimeleri <strong> </strong> arasına al.\n"
        "3. Satır başları veya listelemeler için direkt <br> veya <ul><li> etiketlerini kullan.\n"
        "4. Cevabını gereksiz yere uzatma, anlaşılır ve net tut."
    )
    
    prompt = f"""
Cari Bilgileri ve Hesap Geçmişi (Context):
{context}

Kullanıcının Cari Hakkındaki Sorusu:
{soru}
"""
    
    try:
        cevap = run_llm_chain(prompt, system_prompt, history)
        formatted_cevap = format_markdown_to_html(cevap)
        return jsonify({"success": True, "cevap": formatted_cevap})
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lokal Yapay Zeka Hatası: {str(e)}"
        }), 500

@ai_bp.route('/kredibilite-analiz', methods=['POST'])
def analyze_kredibilite():
    data = request.json or {}
    cari_id = data.get('cari_id')
    if not cari_id:
        return jsonify({"success": False, "message": "Cari ID zorunludur."}), 400
        
    res = get_cari_detail_and_history(cari_id)
    if not res:
        return jsonify({"success": False, "message": "Cari bulunamadı."}), 404
        
    context = get_rag_context_for_cari(cari_id)
    
    system_prompt = (
        "Sen profesyonel bir kurumsal finansal risk analistisin. Sana sunulan cari hesap verilerini analiz etmeli "
        "ve çıktı olarak YALNIZCA geçerli bir JSON objesi dönmelisin. Ekstra açıklama, markdown backtick (```json) "
        "veya önsöz/sonsöz yazmamalısın. Dönülecek JSON yapısı tam olarak şu alanları ve anahtarları içermelidir: "
        "kredibilite (A+, A, B, C veya D derecelerinden biri), payment_ratio (tahsilat/ödeme oranı yüzdesi), "
        "score_desc (risk durumu özet cümlesi), delayed_count (gecikmiş fatura sayısı), "
        "delayed_sum (toplam geciken tutar), risk_raporu (bu cari hakkında detaylı kredibilite analizi, gecikme riskleri, "
        "limit doluluğu ve risk yönetimi önerilerini içeren HTML formatında yazılmış en fazla 1-2 kısa paragraflık profesyonel ve öz bir rapor). "
        "ÖNEMLİ: delayed_sum alanı sayı (float) olmalı ve binlik ayırıcı virgül içermemelidir (örn: 293593.78)."
    )
    
    prompt = f"""
Aşağıdaki verileri inceleyip istenen JSON formatında rapor üret:
{context}
"""
    
    is_musteri = res['cari']['tip'] == 'musteri'
    invoice_sum = 0
    payment_sum = 0
    delayed_count = 0
    delayed_sum = 0
    today = datetime.date(2026, 7, 31)
    
    for t in res['transactions']:
        t_val = t['tutar']
        t_date = datetime.datetime.strptime(t['tarih'], "%Y-%m-%d").date()
        is_invoice = (is_musteri and t['islem_tipi'] == 'alacak') or (not is_musteri and t['islem_tipi'] == 'borc')
        
        if is_musteri:
            if t['islem_tipi'] == 'alacak': invoice_sum += t_val
            else: payment_sum += t_val
        else:
            if t['islem_tipi'] == 'borc': invoice_sum += t_val
            else: payment_sum += t_val
            
        if is_invoice:
            due_date = t_date + datetime.timedelta(days=30)
            if due_date < today:
                delayed_count += 1
                delayed_sum += t_val
                
    net_ratio = (payment_sum / invoice_sum) if invoice_sum > 0 else 1.0
    
    try:
        llm_response = run_llm_chain(prompt, system_prompt).strip()
        
        # Robust JSON extraction using regex
        import re
        match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if match:
            llm_response = match.group(0)
            
        # Clean up thousands separators from unquoted numbers in JSON (e.g. 293,593.78 -> 293593.78)
        llm_response = re.sub(r'(\d+),(\d+)', r'\1\2', llm_response)
            
        parsed = {}
        try:
            parsed = json.loads(llm_response)
        except Exception:
            import ast
            try:
                parsed = ast.literal_eval(llm_response)
            except Exception:
                # Fallback to empty to let code-based calculations handle it
                parsed = {}
                
        score = parsed.get("kredibilite", "A" if net_ratio >= 0.9 else "B" if net_ratio >= 0.7 else "C")
        payment_ratio = parsed.get("payment_ratio", net_ratio * 100)
        score_desc = parsed.get("score_desc", "Tahsilat dengeli seyretmektedir." if net_ratio >= 0.9 else "Tahsilat oranında hafif gecikmeler mevcuttur.")
        delayed_count_val = parsed.get("delayed_count", delayed_count)
        delayed_sum_val = parsed.get("delayed_sum", delayed_sum)
        
        # Format risk raporu if missing or failed to parse
        risk_raporu = parsed.get("risk_raporu")
        if not risk_raporu:
            risk_raporu = (
                f"Cari hesap verilerinin lokal analizi:<br>"
                f"Toplam faturalanan tutar <strong>{invoice_sum:,.2f} TL</strong> olup, tahsil edilen/kapatılan tutar <strong>{payment_sum:,.2f} TL</strong>'dir. "
                f"Hesap kapatma oranı %<strong>{net_ratio * 100:.1f}</strong> olarak gerçekleşmiştir.<br>"
                f"Vadesi gecikmiş fatura sayısı: <strong>{delayed_count}</strong>. Toplam geciken riskli bakiye: <strong>{delayed_sum:,.2f} TL</strong>'dir. "
                f"Mevcut veriler ışığında, risk limit aşımı veya temerrüt ihtimali düşüktür."
            )
            
        # Persist the score to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE cari SET kredibilite = ? WHERE id = ?", (score, cari_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "kredibilite": score,
            "payment_ratio": payment_ratio,
            "score_desc": score_desc,
            "delayed_count": delayed_count_val,
            "delayed_sum": delayed_sum_val,
            "risk_raporu": risk_raporu
        })
    except Exception as e:
        import traceback
        print("=== Kredibilite Analizi Hatası ===")
        traceback.print_exc()
        # Final fallback to guarantee the screen never crashes
        score = "A" if net_ratio >= 0.9 else "B" if net_ratio >= 0.7 else "C"
        return jsonify({
            "success": True,
            "kredibilite": score,
            "payment_ratio": net_ratio * 100,
            "score_desc": "Sistem verilerinden hesaplanan cari risk durumu.",
            "delayed_count": delayed_count,
            "delayed_sum": delayed_sum,
            "risk_raporu": f"Lokal veri analizinde teknik bir gecikme oluştu, ancak finansal veritabanı hesaplamaları başarıyla tamamlandı. Gecikmiş fatura tutarı: <strong>{delayed_sum:,.2f} TL</strong>."
        })

@ai_bp.route('/stok-sor', methods=['POST'])
def ask_stok_question():
    data = request.json or {}
    soru = data.get('soru', '').strip()
    history = data.get('history', [])
    
    if not soru:
        return jsonify({"success": False, "message": "Soru boş olamaz."})

    # Web search check
    search_keywords = ["fiyat", "araştır", "internet", "web", "ne kadar"]
    web_context = ""
    if any(k in soru.lower() for k in search_keywords):
        try:
            from ddgs import DDGS
            search_query = soru + " fiyat"
            results = DDGS().text(search_query, max_results=3)
            web_context = "### Canlı İnternet Arama Sonuçları:\n"
            for r in results:
                web_context += f"- Kaynak Linki: {r.get('href')} | **{r.get('title')}**: {r.get('body')}\n"
        except Exception as e:
            print(f"Web search error: {e}")
            web_context = "### İnternet Araması Yapılamadı.\n"
            
    # Get DB context for critical stocks and movements
    db_context = ""
    try:
        from repositories.stok_repository import get_stok_liste
        stoklar = get_stok_liste()
        
        # 2. Sıfır Stok (Yok Satanlar)
        sifir_stoklar = [s for s in stoklar if s.get('adet', 0) == 0]
        db_context += "### Sıfır Stok (Yok Satanlar):\n"
        if sifir_stoklar:
            for ss in sifir_stoklar:
                db_context += f"- {ss['ad']} (Kategori: {ss['kategori']})\n"
        else:
            db_context += "- Şu an stoğu tamamen bitmiş (0 adet) ürün bulunmuyor.\n"
            
        kritik_stoklar = [s for s in stoklar if s.get('adet', 0) < s.get('kritik_seviye', 10)]
        db_context += "\n### Sistemdeki Kritik Stoklar (Kritik Seviyenin Altındakiler):\n"
        if kritik_stoklar:
            for ks in kritik_stoklar:
                db_context += f"- {ks['ad']} (Kategori: {ks['kategori']}) - Mevcut: {ks['adet']} adet (Kritik Sınır: {ks.get('kritik_seviye', 10)})\n"
        else:
            db_context += "Kritik seviyenin altında stok bulunmamaktadır.\n"
            
        # 3. Kategori Bazlı Özet
        import collections
        kategori_count = collections.defaultdict(int)
        kategori_adet = collections.defaultdict(int)
        for s in stoklar:
            cat = s.get('kategori', 'Diğer') or 'Diğer'
            kategori_count[cat] += 1
            kategori_adet[cat] += s.get('adet', 0)
            
        db_context += "\n### Kategori Bazlı Özet:\n"
        for cat, count in kategori_count.items():
            db_context += f"- {cat} Kategorisi: {count} farklı çeşit ürün, depoda toplam {kategori_adet[cat]} adet.\n"
            
        # 5. Genel Envanter Özeti
        toplam_kalem = len(stoklar)
        toplam_adet = sum(s.get('adet', 0) for s in stoklar)
        db_context += f"\n### Genel Envanter Özeti:\n"
        db_context += f"- Toplam {toplam_kalem} farklı kalem ürünümüz var. Depoda toplam {toplam_adet} adet mal bulunmaktadır.\n"

        # 6. Tüm Stok Listesi (AI'nin spesifik sorulara doğru yanıt vermesi için)
        db_context += "\n### Güncel Stok Listesi (Ürünler ve Adetleri):\n"
        for s in stoklar:
            db_context += f"- {s.get('ad')}: {s.get('adet', 0)} adet\n"

    except Exception as e:
        print(f"DB context error: {e}")
        
    combined_context = f"{web_context}\n\n{db_context}"
    
    system_prompt = (
        "Sen BulutAI, Bulutİş ERP sisteminin Stok ve Tedarik asistanısın. "
        "Aşağıdaki sistem verilerine (varsa web arama sonuçlarına) dayanarak kullanıcının stoklarla ilgili sorusuna Türkçe cevap ver.\n"
        "ÇOK ÖNEMLİ KURALLAR (TOKEN TASARRUFU İÇİN):\n"
        "1. SADECE VE SADECE kullanıcının sorduğu spesifik soruya yanıt ver. Ekstra açıklama, tavsiye veya genel özet kesinlikle ekleme.\n"
        "2. Yanıtın olabildiğince kısa olsun (mümkünse tek bir cümle veya kelime öbeği). Uzun uzadıya yorum yapma.\n"
        "3. Kullanıcı genel bir özet (tüm stok durumu) istemedikçe, genel envanter veya diğer ürünlerden bahsetme.\n"
        "4. Asla markdown biçimlendirmesi (###, **, *, ***, #, vb.) kullanma. Önemli kelimeleri <strong> </strong> arasına al.\n"
        "5. Satır başları veya listelemeler için direkt <br> veya <ul><li> etiketlerini kullan."
    )
    
    prompt = f"Bağlam:\n{combined_context}\n\nSoru: {soru}"
    
    try:
        cevap = run_llm_chain(prompt, system_prompt, history)
        formatted_cevap = format_markdown_to_html(cevap)
        return jsonify({"success": True, "cevap": formatted_cevap})
    except Exception as e:
        return jsonify({"success": False, "message": f"Hata: {str(e)}"}), 500
