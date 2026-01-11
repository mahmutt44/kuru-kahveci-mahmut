import os
from flask import Flask
from flask import session
from datetime import datetime

from database import get_db_path, init_db
from app.routes.admin import admin_bp
from app.routes.client import client_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Güvenlik: gerçek projede bunu environment değişkeni ile yönetmek gerekir.
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

    # DB konumu
    app.config["DB_PATH"] = get_db_path(os.environ.get("DB_PATH"))

    # İlk açılışta tabloları oluştur.
    init_db(app.config["DB_PATH"])

    # Blueprint kayıtları
    app.register_blueprint(client_bp)
    app.register_blueprint(admin_bp)

    @app.template_filter('datetime_tr')
    def datetime_tr_filter(date_str):
        """Tarih string'ini Türkiye formatında göster"""
        if not date_str:
            return ""
        
        try:
            # Veritabanından gelen string'i parse et
            if isinstance(date_str, str):
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            else:
                dt = date_str
            
            # Türkiye formatında göster
            return dt.strftime("%d.%m.%Y %H:%M")
        except:
            return str(date_str)

    @app.context_processor
    def inject_globals():
        # Template'lerde navbar sepet sayacı için.
        cart = session.get("cart", [])
        cart_count = 0
        if isinstance(cart, list):
            for it in cart:
                try:
                    cart_count += int(it.get("qty", 1))
                except Exception:
                    cart_count += 1
        
        # Cache-busting için timestamp
        import time
        return {"cart_count": cart_count, "cache_bust": int(time.time())}

    return app
