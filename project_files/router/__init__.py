from .main import main_bp
from .cari import cari_bp
from .kasa import kasa_bp
from .stok import stok_bp
from .fatura import fatura_bp
from .ai import ai_bp

def register_routers(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(cari_bp, url_prefix='/api/cari')
    app.register_blueprint(kasa_bp, url_prefix='/api/kasa-banka')
    app.register_blueprint(stok_bp, url_prefix='/api/stok')
    app.register_blueprint(fatura_bp, url_prefix='/api/fatura')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
