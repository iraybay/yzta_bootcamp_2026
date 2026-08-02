import os
import sys
import webbrowser
from flask import Flask
from dotenv import load_dotenv
load_dotenv(override=True)
import db_manager
import router

def check_and_start_ollama():
    """Ollama API sunucusunu kontrol eder ve çalışmıyorsa otomatik olarak başlatır."""
    import subprocess
    import platform
    import time
    import requests
    
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
    # Base URL for health check
    base_url = "/".join(ollama_url.split("/")[:3]) # e.g. http://localhost:11434
    
    def check_and_pull_model():
        try:
            model_name = os.environ.get("OLLAMA_MODEL", "gemma2:9b")
            tags_res = requests.get(f"{base_url}/api/tags", timeout=2)
            if tags_res.status_code == 200:
                tags_data = tags_res.json()
                models = [m.get("name", "") for m in tags_data.get("models", [])]
                if model_name not in models and f"{model_name}:latest" not in models:
                    print(f"[!] '{model_name}' modeli Ollama'da bulunamadı. Arka planda indirme başlatılıyor (Bu işlem internet hızınıza bağlı olarak zaman alabilir)...")
                    subprocess.Popen(["ollama", "pull", model_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[!] Ollama model kontrolü yapılamadı: {e}")

    try:
        requests.get(base_url, timeout=2)
        print("[*] Ollama arka planda aktif ve çalışıyor.")
        check_and_pull_model()
        return
    except Exception:
        pass
        
    print("[!] Ollama yanıt vermiyor, otomatik başlatılıyor...")
    system_platform = platform.system()
    if system_platform == "Darwin":  # macOS
        try:
            # open -a Ollama opens the application in the background
            subprocess.Popen(["open", "-a", "Ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[*] macOS Ollama uygulaması tetiklendi. Servis bekleniyor...")
            for _ in range(8):
                time.sleep(1)
                try:
                    requests.get(base_url, timeout=1)
                    print("[*] Ollama servisi aktif hale geldi!")
                    check_and_pull_model()
                    return
                except Exception:
                    pass
        except Exception as e:
            print(f"[!] Ollama başlatılamadı: {e}")
    elif system_platform == "Windows":
        try:
            localappdata = os.environ.get("LOCALAPPDATA", "")
            ollama_path = os.path.join(localappdata, "Programs", "Ollama", "ollama app.exe")
            if os.path.exists(ollama_path):
                subprocess.Popen([ollama_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("[*] Windows Ollama uygulaması tetiklendi.")
                # Give it a bit of time then check model
                time.sleep(3)
                check_and_pull_model()
        except Exception as e:
            print(f"[!] Windows'ta Ollama başlatılamadı: {e}")

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

static_folder = os.path.join(base_dir, 'static')
template_folder = os.path.join(base_dir, 'templates')

app = Flask(__name__, 
            static_folder=static_folder,
            template_folder=template_folder)

from flask import session, redirect, url_for, request

app.secret_key = os.environ.get("SECRET_KEY", "bulutis_cok_gizli_ve_guvenli_anahtar_2026")

@app.before_request
def guvenlik_duvari():
    izin_verilenler = ['auth.login', 'static']
    
    if request.endpoint and request.endpoint not in izin_verilenler:
        if 'logged_in' not in session:
            return redirect(url_for('auth.login'))

# Check and start Ollama service on initialization
check_and_start_ollama()

# Initialize SQLite database schema and mock records
db_manager.init_db()

# Register modular blueprints from router directory
router.register_routers(app)

if __name__ == '__main__':
    port = 5002
    
    # Tarayıcıyı otomatik aç (Geliştirme modunda reloader'ın çift açmasını engelle)
    import threading
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        threading.Timer(1.0, lambda: webbrowser.open(f'http://127.0.0.1:{port}')).start()
    
    # Run server on port 5002 to prevent collision and macOS AirPlay collision
    app.run(host='0.0.0.0', port=port, debug=not getattr(sys, 'frozen', False))

