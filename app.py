import os
from flask import Flask
from flask import session

from database import get_db_path, init_db
from app.routes.admin import admin_bp
from app.routes.client import client_bp


def create_app():
    app = Flask(__name__, template_folder="app/templates", static_folder="app/static")

    # Güvenlik: gerçek projede bunu environment değişkeni ile yönetmek gerekir.
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

    # DB konumu
    app.config["DB_PATH"] = get_db_path(os.environ.get("DB_PATH"))

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


app = create_app()

# For gunicorn/deployment
application = app

if __name__ == "__main__":
    # Windows'ta debug=True ile otomatik reload bazen problem çıkarabiliyor; ihtiyaç halinde açabilirsiniz.
    app.run(host="127.0.0.1", port=5000, debug=True)
