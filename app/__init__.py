import os
from flask import Flask
from flask import session

from database import get_db_path, init_db
from app.routes.admin import admin_bp
from app.routes.client import client_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Güvenlik: gerçek projede bunu environment değişkeni ile yönetmek gerekir.
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

    # DB konumu - Render disk kullan
    db_path = os.environ.get("DB_PATH", "kahveci.db")
    if os.path.exists("/opt/render/project"):
        # Render environment
        db_path = "/opt/render/project/data/kahveci.db"
        # Data klasörünü oluştur
        os.makedirs("/opt/render/project/data", exist_ok=True)
    app.config["DB_PATH"] = get_db_path(db_path)

    # İlk açılışta tabloları oluştur.
    init_db(app.config["DB_PATH"])

    # Blueprint kayıtları
    app.register_blueprint(client_bp)
    app.register_blueprint(admin_bp)

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
        return {"cart_count": cart_count}

    return app
