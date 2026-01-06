from __future__ import annotations

import os
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from database import execute, fetch_all, fetch_one


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


ROAST_TYPES = ["Açık", "Orta", "Koyu"]
ORDER_STATUSES = ["alındı", "hazırlanıyor", "hazır", "teslim edildi"]


_ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
# Varsayılan şifre: admin123 (yalnızca demo amaçlı)
_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
_ADMIN_PASSWORD_HASH = generate_password_hash(_ADMIN_PASSWORD)


def _admin_username() -> str:
    return _ADMIN_USERNAME


def _admin_password_hash() -> str:
    return _ADMIN_PASSWORD_HASH


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return view_func(*args, **kwargs)

    return wrapper


@admin_bp.get("/")
@admin_required
def dashboard():
    db_path = current_app.config["DB_PATH"]

    daily_count = fetch_one(
        db_path,
        "SELECT COUNT(*) AS c FROM orders WHERE date(created_at)=date('now','localtime')",
    )["c"]

    daily_revenue_row = fetch_one(
        db_path,
        """
        SELECT COALESCE(SUM(oi.price), 0) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        WHERE date(o.created_at)=date('now','localtime')
        """,
    )
    daily_revenue = float(daily_revenue_row["revenue"])

    active_orders = fetch_all(
        db_path,
        "SELECT * FROM orders WHERE status != 'teslim edildi' ORDER BY created_at DESC",
    )

    return render_template(
        "admin/dashboard.html",
        daily_count=daily_count,
        daily_revenue=daily_revenue,
        active_orders=active_orders,
    )


@admin_bp.get("/login")
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/login.html")


@admin_bp.post("/login")
def login_post():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    if username != _admin_username() or not check_password_hash(_admin_password_hash(), password):
        flash("Kullanıcı adı veya şifre hatalı.", "danger")
        return redirect(url_for("admin.login"))

    session["admin_logged_in"] = True
    flash("Giriş başarılı.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/logout")
@admin_required
def logout():
    session.pop("admin_logged_in", None)
    flash("Çıkış yapıldı.", "success")
    return redirect(url_for("admin.login"))


@admin_bp.get("/products")
@admin_required
def products_list():
    db_path = current_app.config["DB_PATH"]
    q = (request.args.get("q") or "").strip()
    roast_type = (request.args.get("roast_type") or "").strip()
    active = (request.args.get("active") or "").strip()

    where = []
    params: list[object] = []

    if q:
        where.append("name LIKE ?")
        params.append(f"%{q}%")

    if roast_type in ROAST_TYPES:
        where.append("roast_type = ?")
        params.append(roast_type)

    if active in ("0", "1"):
        where.append("is_active = ?")
        params.append(int(active))

    sql = "SELECT * FROM products"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC"

    products = fetch_all(db_path, sql, tuple(params))
    return render_template(
        "admin/products_list.html",
        products=products,
        q=q,
        roast_type=roast_type,
        active=active,
        roast_types=ROAST_TYPES,
    )


@admin_bp.get("/products/new")
@admin_required
def products_new():
    return render_template("admin/product_form.html", product=None, roast_types=ROAST_TYPES)


@admin_bp.post("/products/new")
@admin_required
def products_new_post():
    db_path = current_app.config["DB_PATH"]

    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    roast_type = (request.form.get("roast_type") or "").strip()

    def _f(key: str) -> float:
        return float((request.form.get(key) or "0").replace(",", "."))

    def _i(key: str) -> int:
        return int(request.form.get(key) or "0")

    if len(name) < 2:
        flash("Ürün adı zorunludur.", "danger")
        return redirect(url_for("admin.products_new"))

    if roast_type not in ROAST_TYPES:
        flash("Kavrum türü seçiniz.", "danger")
        return redirect(url_for("admin.products_new"))

    try:
        price_250 = _f("price_250")
        price_500 = _f("price_500")
        price_1000 = _f("price_1000")
        stock_gram = _i("stock_gram")
    except ValueError:
        flash("Fiyat/stock alanları geçersiz.", "danger")
        return redirect(url_for("admin.products_new"))

    if min(price_250, price_500, price_1000) <= 0:
        flash("Fiyatlar 0'dan büyük olmalıdır.", "danger")
        return redirect(url_for("admin.products_new"))

    if stock_gram < 0:
        flash("Stok negatif olamaz.", "danger")
        return redirect(url_for("admin.products_new"))

    image_path = (request.form.get("image_path") or "").strip() or None

    # İsteğe bağlı: dosya upload
    file = request.files.get("image_file")
    if file and file.filename:
        filename = secure_filename(file.filename)
        save_dir = os.path.join(current_app.static_folder, "images")
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)
        file.save(file_path)
        image_path = f"images/{filename}"

    execute(
        db_path,
        """
        INSERT INTO products (name, description, roast_type, price_250, price_500, price_1000, stock_gram, image_path, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (name, description, roast_type, price_250, price_500, price_1000, stock_gram, image_path),
    )

    flash("Ürün eklendi.", "success")
    return redirect(url_for("admin.products_list"))


@admin_bp.get("/products/<int:product_id>/edit")
@admin_required
def products_edit(product_id: int):
    db_path = current_app.config["DB_PATH"]
    product = fetch_one(db_path, "SELECT * FROM products WHERE id=?", (product_id,))
    if not product:
        flash("Ürün bulunamadı.", "danger")
        return redirect(url_for("admin.products_list"))

    return render_template("admin/product_form.html", product=product, roast_types=ROAST_TYPES)


@admin_bp.post("/products/<int:product_id>/edit")
@admin_required
def products_edit_post(product_id: int):
    db_path = current_app.config["DB_PATH"]
    product = fetch_one(db_path, "SELECT * FROM products WHERE id=?", (product_id,))
    if not product:
        flash("Ürün bulunamadı.", "danger")
        return redirect(url_for("admin.products_list"))

    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    roast_type = (request.form.get("roast_type") or "").strip()

    def _f(key: str) -> float:
        return float((request.form.get(key) or "0").replace(",", "."))

    def _i(key: str) -> int:
        return int(request.form.get(key) or "0")

    if len(name) < 2:
        flash("Ürün adı zorunludur.", "danger")
        return redirect(url_for("admin.products_edit", product_id=product_id))

    if roast_type not in ROAST_TYPES:
        flash("Kavrum türü seçiniz.", "danger")
        return redirect(url_for("admin.products_edit", product_id=product_id))

    try:
        price_250 = _f("price_250")
        price_500 = _f("price_500")
        price_1000 = _f("price_1000")
        stock_gram = _i("stock_gram")
    except ValueError:
        flash("Fiyat/stock alanları geçersiz.", "danger")
        return redirect(url_for("admin.products_edit", product_id=product_id))

    if min(price_250, price_500, price_1000) <= 0:
        flash("Fiyatlar 0'dan büyük olmalıdır.", "danger")
        return redirect(url_for("admin.products_edit", product_id=product_id))

    if stock_gram < 0:
        flash("Stok negatif olamaz.", "danger")
        return redirect(url_for("admin.products_edit", product_id=product_id))

    image_path = (request.form.get("image_path") or "").strip() or None

    file = request.files.get("image_file")
    if file and file.filename:
        filename = secure_filename(file.filename)
        save_dir = os.path.join(current_app.static_folder, "images")
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)
        file.save(file_path)
        image_path = f"images/{filename}"

    execute(
        db_path,
        """
        UPDATE products
        SET name=?, description=?, roast_type=?, price_250=?, price_500=?, price_1000=?, stock_gram=?, image_path=?
        WHERE id=?
        """,
        (name, description, roast_type, price_250, price_500, price_1000, stock_gram, image_path, product_id),
    )

    flash("Ürün güncellendi.", "success")
    return redirect(url_for("admin.products_list"))


@admin_bp.post("/products/<int:product_id>/delete")
@admin_required
def products_delete(product_id: int):
    db_path = current_app.config["DB_PATH"]

    # Siparişlerde kullanılan ürünleri silmek FK nedeniyle engellenir; bu durumda pasif yapabilirsiniz.
    try:
        execute(db_path, "DELETE FROM products WHERE id=?", (product_id,))
        flash("Ürün silindi.", "success")
    except Exception:
        flash("Ürün silinemedi. Siparişlerde kullanılmış olabilir; pasif yapmayı deneyin.", "danger")

    return redirect(url_for("admin.products_list"))


@admin_bp.post("/products/<int:product_id>/toggle")
@admin_required
def products_toggle(product_id: int):
    db_path = current_app.config["DB_PATH"]
    product = fetch_one(db_path, "SELECT id, is_active FROM products WHERE id=?", (product_id,))
    if not product:
        flash("Ürün bulunamadı.", "danger")
        return redirect(url_for("admin.products_list"))

    new_state = 0 if int(product["is_active"]) == 1 else 1
    execute(db_path, "UPDATE products SET is_active=? WHERE id=?", (new_state, product_id))
    flash("Ürün durumu güncellendi.", "success")
    return redirect(url_for("admin.products_list"))


@admin_bp.get("/orders")
@admin_required
def orders_list():
    db_path = current_app.config["DB_PATH"]
    status = (request.args.get("status") or "").strip()
    selected_status = status if status in ORDER_STATUSES else ""

    where = []
    params: list[object] = []

    if selected_status:
        where.append("o.status = ?")
        params.append(selected_status)

    sql = (
        "SELECT o.*, COALESCE(SUM(oi.price), 0) AS total "
        "FROM orders o "
        "LEFT JOIN order_items oi ON oi.order_id = o.id "
    )
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    sql += "GROUP BY o.id ORDER BY o.created_at DESC"

    orders = fetch_all(db_path, sql, tuple(params))
    return render_template(
        "admin/orders_list.html",
        orders=orders,
        statuses=ORDER_STATUSES,
        selected_status=selected_status,
    )


@admin_bp.get("/orders/<int:order_id>")
@admin_required
def orders_detail(order_id: int):
    db_path = current_app.config["DB_PATH"]

    order = fetch_one(db_path, "SELECT * FROM orders WHERE id=?", (order_id,))
    if not order:
        flash("Sipariş bulunamadı.", "danger")
        return redirect(url_for("admin.orders_list"))

    items = fetch_all(
        db_path,
        """
        SELECT
            oi.product_id,
            p.name AS product_name,
            oi.grind_type,
            oi.gram,
            COUNT(*) AS qty,
            oi.price AS unit_price,
            (COUNT(*) * oi.price) AS subtotal
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id=?
        GROUP BY oi.product_id, p.name, oi.grind_type, oi.gram, oi.price
        ORDER BY p.name ASC
        """,
        (order_id,),
    )

    total = sum(float(i["subtotal"]) for i in items)

    return render_template(
        "admin/order_detail.html",
        order=order,
        items=items,
        total=total,
        statuses=ORDER_STATUSES,
    )


@admin_bp.post("/orders/<int:order_id>/status")
@admin_required
def orders_update_status(order_id: int):
    db_path = current_app.config["DB_PATH"]

    status = (request.form.get("status") or "").strip()
    if status not in ORDER_STATUSES:
        flash("Geçersiz durum.", "danger")
        return redirect(url_for("admin.orders_detail", order_id=order_id))

    execute(db_path, "UPDATE orders SET status=? WHERE id=?", (status, order_id))
    flash("Sipariş durumu güncellendi.", "success")
    return redirect(url_for("admin.orders_detail", order_id=order_id))
