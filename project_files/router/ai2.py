from flask import Blueprint, jsonify
import google.generativeai as genai
import os
import sqlite3

yapay_zeka_bp = Blueprint('yapay_zeka', __name__)

@yapay_zeka_bp.route('/finans-ozeti', methods=['GET'])
def finans_ozeti():
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return jsonify({"error": "API anahtarı bulunamadı (.env dosyanızı kontrol edin)", "status": "error"}), 500
        
        genai.configure(api_key=api_key)
        conn = sqlite3.connect('bulutis.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tarih, tip, tutar, tanim 
            FROM kasa_banka_islem 
            ORDER BY id DESC LIMIT 15
        """)
        hareketler = cursor.fetchall()
        conn.close()

        if not hareketler:
            return jsonify({"ozet": "Henüz analiz edilecek kasa hareketi bulunmuyor.", "status": "success"})

        hareket_metni = "\n".join([f"Tarih: {h[0]}, Tip: {h[1]}, Tutar: {h[2]} TL, Açıklama: {h[3]}" for h in hareketler])
        
        prompt = f"""Sen bir şirketin ön muhasebe ve finans danışmanısın. 
        Aşağıda şirketimizin son 15 kasa/banka hareketi verilmiştir:
        
        {hareket_metni}
        
        Lütfen patrona (yöneticiye) yönelik çok kısa, anlaşılır ve profesyonel bir durum özeti çıkar. 
        Son 15 işlemdeki giriş çıkış dengesini yorumla ve varsa dikkat edilmesi gereken bir nakit açığı/fazlası durumunu belirt. 
        Yanıtın 3 veya 4 cümleyi geçmesin."""

        model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        return jsonify({"ozet": response.text, "status": "success"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "status": "error"}), 500
