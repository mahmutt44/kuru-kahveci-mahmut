from __future__ import annotations

import os
import uuid
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

from database import execute, execute_many, fetch_all, fetch_one, now_str


def get_upload_dir():
    """Static folder döner"""
    static_folder = current_app.static_folder
    return os.path.join(static_folder, "images")


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


@admin_bp.route("/")
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


@admin_bp.route("/login")
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/login.html")


@admin_bp.route("/login", methods=["POST"])
def login_post():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    if username != _admin_username() or not check_password_hash(_admin_password_hash(), password):
        flash("Kullanıcı adı veya şifre hatalı.", "danger")
        return redirect(url_for("admin.login"))

    session["admin_logged_in"] = True
    flash("Giriş başarılı.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/logout", methods=["POST"])
@admin_required
def logout():
    session.pop("admin_logged_in", None)
    flash("Çıkış yapıldı.", "success")
    return redirect(url_for("admin.login"))


@admin_bp.route("/products")
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


@admin_bp.route("/products/new")
@admin_required
def products_new():
    return render_template("admin/product_form.html", product=None, roast_types=ROAST_TYPES)


@admin_bp.route("/products/new")
@admin_required
def products_new_post():
    db_path = current_app.config["DB_PATH"]

    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    roast_type = (request.form.get("roast_type") or "").strip()

    origin = (request.form.get("origin") or "").strip() or None
    process = (request.form.get("process") or "").strip() or None
    tasting_notes = (request.form.get("tasting_notes") or "").strip() or None

    espresso_compatible = 1 if (request.form.get("espresso_compatible") in ("1", "on", "true")) else 0

    def _f(key: str) -> float:
        return float((request.form.get(key) or "0").replace(",", "."))

    def _i(key: str) -> int:
        return int(request.form.get(key) or "0")

    def _r(key: str) -> int:
        v = int(request.form.get(key) or "3")
        if v < 1:
            v = 1
        if v > 5:
            v = 5
        return v

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
        altitude = _i("altitude") if (request.form.get("altitude") or "").strip() else None
        acidity = _r("acidity")
        body = _r("body")
        sweetness = _r("sweetness")
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
        save_dir = get_upload_dir()
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)
        file.save(file_path)
        image_path = f"images/{filename}"

    product_id = execute(
        db_path,
        """
        INSERT INTO products (
            name, description, roast_type,
            price_250, price_500, price_1000,
            stock_gram, image_path, is_active,
            origin, process, altitude, tasting_notes,
            acidity, body, sweetness,
            espresso_compatible
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            description,
            roast_type,
            price_250,
            price_500,
            price_1000,
            stock_gram,
            image_path,
            origin,
            process,
            altitude,
            tasting_notes,
            acidity,
            body,
            sweetness,
            espresso_compatible,
        ),
    )

    gallery_files = request.files.getlist("gallery_files")
    rows = []
    sort_order = 0
    for f in gallery_files:
        if not f or not f.filename:
            continue
        original = secure_filename(f.filename)
        filename = f"{uuid.uuid4().hex}_{original}" if original else f"{uuid.uuid4().hex}.jpg"
        save_dir = get_upload_dir()
        os.makedirs(save_dir, exist_ok=True)
        f.save(os.path.join(save_dir, filename))
        rows.append((product_id, f"images/{filename}", sort_order, now_str()))
        sort_order += 1

    if rows:
        execute_many(
            db_path,
            """
            INSERT INTO product_images (product_id, image_path, sort_order, created_at)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )

    flash("Ürün eklendi.", "success")
    return redirect(url_for("admin.products_list"))


@admin_bp.route("/products/<int:product_id>/edit")
@admin_required
def products_edit(product_id: int):
    db_path = current_app.config["DB_PATH"]
    product = fetch_one(db_path, "SELECT * FROM products WHERE id=?", (product_id,))
    if not product:
        flash("Ürün bulunamadı.", "danger")
        return redirect(url_for("admin.products_list"))

    images = fetch_all(
        db_path,
        "SELECT * FROM product_images WHERE product_id=? ORDER BY sort_order ASC, id ASC",
        (product_id,),
    )

    return render_template(
        "admin/product_form.html",
        product=product,
        roast_types=ROAST_TYPES,
        images=images,
    )


@admin_bp.route("/products/<int:product_id>/edit")
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

    origin = (request.form.get("origin") or "").strip() or None
    process = (request.form.get("process") or "").strip() or None
    tasting_notes = (request.form.get("tasting_notes") or "").strip() or None
    espresso_compatible = 1 if (request.form.get("espresso_compatible") in ("1", "on", "true")) else 0

    def _f(key: str) -> float:
        return float((request.form.get(key) or "0").replace(",", "."))

    def _i(key: str) -> int:
        return int(request.form.get(key) or "0")

    def _r(key: str) -> int:
        v = int(request.form.get(key) or "3")
        if v < 1:
            v = 1
        if v > 5:
            v = 5
        return v

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
        altitude = _i("altitude") if (request.form.get("altitude") or "").strip() else None
        acidity = _r("acidity")
        body = _r("body")
        sweetness = _r("sweetness")
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
        save_dir = get_upload_dir()
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)
        file.save(file_path)
        image_path = f"images/{filename}"

    execute(
        db_path,
        """
        UPDATE products
        SET
            name=?, description=?, roast_type=?,
            price_250=?, price_500=?, price_1000=?,
            stock_gram=?, image_path=?,
            origin=?, process=?, altitude=?, tasting_notes=?,
            acidity=?, body=?, sweetness=?,
            espresso_compatible=?
        WHERE id=?
        """,
        (
            name,
            description,
            roast_type,
            price_250,
            price_500,
            price_1000,
            stock_gram,
            image_path,
            origin,
            process,
            altitude,
            tasting_notes,
            acidity,
            body,
            sweetness,
            espresso_compatible,
            product_id,
        ),
    )

    old_stock = int(product["stock_gram"]) if product["stock_gram"] is not None else 0
    diff = int(stock_gram) - old_stock
    if diff != 0:
        execute(
            db_path,
            """
            INSERT INTO stock_movements (product_id, change_gram, reason, ref_type, ref_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (product_id, diff, "Admin stok güncelleme", "admin", None, now_str()),
        )

    gallery_files = request.files.getlist("gallery_files")
    rows = []
    sort_order = 0
    if gallery_files:
        last = fetch_one(
            db_path,
            "SELECT COALESCE(MAX(sort_order), -1) AS m FROM product_images WHERE product_id=?",
            (product_id,),
        )
        sort_order = int(last["m"]) + 1

    for f in gallery_files:
        if not f or not f.filename:
            continue
        original = secure_filename(f.filename)
        filename = f"{uuid.uuid4().hex}_{original}" if original else f"{uuid.uuid4().hex}.jpg"
        save_dir = get_upload_dir()
        os.makedirs(save_dir, exist_ok=True)
        f.save(os.path.join(save_dir, filename))
        rows.append((product_id, f"images/{filename}", sort_order, now_str()))
        sort_order += 1

    if rows:
        execute_many(
            db_path,
            """
            INSERT INTO product_images (product_id, image_path, sort_order, created_at)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )

    flash("Ürün güncellendi.", "success")
    return redirect(url_for("admin.products_list"))


@admin_bp.route("/products/<int:product_id>/images/<int:image_id>/delete")
@admin_required
def product_image_delete(product_id: int, image_id: int):
    db_path = current_app.config["DB_PATH"]
    execute(db_path, "DELETE FROM product_images WHERE id=? AND product_id=?", (image_id, product_id))
    flash("Görsel kaldırıldı.", "success")
    return redirect(url_for("admin.products_edit", product_id=product_id))


@admin_bp.route("/stock-movements")
@admin_required
def stock_movements():
    db_path = current_app.config["DB_PATH"]
    movements = fetch_all(
        db_path,
        """
        SELECT
            sm.id,
            sm.product_id,
            p.name AS product_name,
            sm.change_gram,
            sm.reason,
            sm.ref_type,
            sm.ref_id,
            sm.created_at
        FROM stock_movements sm
        JOIN products p ON p.id = sm.product_id
        ORDER BY sm.created_at DESC, sm.id DESC
        LIMIT 200
        """,
    )
    return render_template("admin/stock_movements.html", movements=movements)


@admin_bp.route("/products/<int:product_id>/delete")
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


@admin_bp.route("/products/<int:product_id>/toggle")
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


@admin_bp.route("/orders")
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


@admin_bp.route("/orders/<int:order_id>")
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


@admin_bp.route("/orders/<int:order_id>/print")
@admin_required
def orders_print(order_id: int):
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
        "admin/order_print.html",
        order=order,
        items=items,
        total=total,
    )


@admin_bp.route("/orders/<int:order_id>/status")
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
