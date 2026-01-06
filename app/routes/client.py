from __future__ import annotations

from collections import defaultdict
from typing import Any

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

from database import execute, fetch_all, fetch_one, now_str


client_bp = Blueprint("client", __name__)


GRAM_OPTIONS = [250, 500, 1000]
GRIND_OPTIONS = ["Türk", "Filtre", "Espresso", "Çekirdek"]


def _normalize_phone(phone: str) -> str | None:
    raw = (phone or "").strip()
    digits = "".join(ch for ch in raw if ch.isdigit())

    if digits.startswith("90") and len(digits) >= 12:
        digits = "0" + digits[2:]

    if len(digits) == 10 and digits.startswith("5"):
        digits = "0" + digits

    if len(digits) != 11 or not digits.startswith("05"):
        return None

    return digits


def _get_cart() -> list[dict[str, Any]]:
    cart = session.get("cart")
    if not isinstance(cart, list):
        cart = []
    return cart


def _save_cart(cart: list[dict[str, Any]]):
    session["cart"] = cart
    session.modified = True


def _product_price_by_gram(product_row, gram: int) -> float | None:
    if gram == 250:
        return float(product_row["price_250"])
    if gram == 500:
        return float(product_row["price_500"])
    if gram == 1000:
        return float(product_row["price_1000"])
    return None


@client_bp.get("/")
def home():
    db_path = current_app.config["DB_PATH"]
    q = (request.args.get("q") or "").strip()
    roast_type = (request.args.get("roast_type") or "").strip()
    origin = (request.args.get("origin") or "").strip()
    espresso = (request.args.get("espresso") or "").strip()
    min_price = (request.args.get("min_price") or "").strip()
    max_price = (request.args.get("max_price") or "").strip()

    show_landing = not any([q, roast_type, origin, espresso, min_price, max_price])

    best_sellers = []
    new_arrivals = []
    if show_landing:
        best_sellers = fetch_all(
            db_path,
            """
            SELECT p.*, COUNT(oi.id) AS sold_count
            FROM products p
            JOIN order_items oi ON oi.product_id = p.id
            JOIN orders o ON o.id = oi.order_id
            WHERE p.is_active=1
            GROUP BY p.id
            ORDER BY sold_count DESC, p.id DESC
            LIMIT 4
            """,
        )
        new_arrivals = fetch_all(
            db_path,
            "SELECT * FROM products WHERE is_active=1 ORDER BY id DESC LIMIT 4",
        )

    where = ["is_active=1"]
    params: list[object] = []

    if q:
        where.append("name LIKE ?")
        params.append(f"%{q}%")

    if roast_type in ("Açık", "Orta", "Koyu"):
        where.append("roast_type = ?")
        params.append(roast_type)
    else:
        roast_type = ""

    if origin:
        where.append("origin LIKE ?")
        params.append(f"%{origin}%")

    if espresso in ("1", "on", "true"):
        where.append("espresso_compatible = 1")
        espresso = "1"
    else:
        espresso = ""

    def _pf(v: str) -> float | None:
        try:
            return float(v.replace(",", "."))
        except Exception:
            return None

    min_p = _pf(min_price) if min_price else None
    max_p = _pf(max_price) if max_price else None
    if min_p is not None:
        where.append("price_250 >= ?")
        params.append(min_p)
    if max_p is not None:
        where.append("price_250 <= ?")
        params.append(max_p)

    sql = "SELECT * FROM products"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC"

    products = fetch_all(db_path, sql, tuple(params))
    return render_template(
        "client/home.html",
        products=products,
        gram_options=GRAM_OPTIONS,
        grind_options=GRIND_OPTIONS,
        q=q,
        roast_type=roast_type,
        origin=origin,
        espresso=espresso,
        min_price=min_price,
        max_price=max_price,
        show_landing=show_landing,
        best_sellers=best_sellers,
        new_arrivals=new_arrivals,
    )


@client_bp.get("/product/<int:product_id>")
def product_detail(product_id: int):
    db_path = current_app.config["DB_PATH"]
    product = fetch_one(db_path, "SELECT * FROM products WHERE id=?", (product_id,))
    if not product or int(product["is_active"]) != 1:
        flash("Ürün bulunamadı veya satışta değil.", "danger")
        return redirect(url_for("client.home"))

    gallery = fetch_all(
        db_path,
        "SELECT image_path FROM product_images WHERE product_id=? ORDER BY sort_order ASC, id ASC",
        (product_id,),
    )

    images = []
    if "image_path" in product.keys() and product["image_path"]:
        images.append({"image_path": product["image_path"]})
    for g in gallery:
        if "image_path" not in g.keys() or not g["image_path"]:
            continue
        if images and images[0].get("image_path") == g["image_path"]:
            continue
        images.append({"image_path": g["image_path"]})

    return render_template(
        "client/product_detail.html",
        product=product,
        images=images,
        gram_options=GRAM_OPTIONS,
        grind_options=GRIND_OPTIONS,
    )


@client_bp.post("/cart/add")
def cart_add():
    db_path = current_app.config["DB_PATH"]

    try:
        product_id = int(request.form.get("product_id", "0"))
        gram = int(request.form.get("gram", "0"))
        grind_type = (request.form.get("grind_type") or "").strip()
        qty = int(request.form.get("qty", "1"))
    except ValueError:
        flash("Geçersiz seçim.", "danger")
        return redirect(url_for("client.home"))

    if gram not in GRAM_OPTIONS:
        flash("Geçersiz gramaj.", "danger")
        return redirect(url_for("client.product_detail", product_id=product_id))

    if grind_type not in GRIND_OPTIONS:
        flash("Geçersiz öğütme türü.", "danger")
        return redirect(url_for("client.product_detail", product_id=product_id))

    if qty < 1 or qty > 20:
        flash("Geçersiz adet.", "danger")
        return redirect(url_for("client.product_detail", product_id=product_id))

    product = fetch_one(db_path, "SELECT * FROM products WHERE id=?", (product_id,))
    if not product or int(product["is_active"]) != 1:
        flash("Ürün bulunamadı.", "danger")
        return redirect(url_for("client.home"))

    unit_price = _product_price_by_gram(product, gram)
    if unit_price is None:
        flash("Fiyat bulunamadı.", "danger")
        return redirect(url_for("client.product_detail", product_id=product_id))

    cart = _get_cart()

    # Aynı ürün + gram + öğütme ile eklenirse birleştir.
    merged = False
    for item in cart:
        if (
            int(item.get("product_id")) == product_id
            and int(item.get("gram")) == gram
            and item.get("grind_type") == grind_type
        ):
            item["qty"] = int(item.get("qty", 1)) + qty
            merged = True
            break

    if not merged:
        cart.append(
            {
                "product_id": product_id,
                "product_name": product["name"],
                "image_path": product["image_path"],
                "gram": gram,
                "grind_type": grind_type,
                "qty": qty,
                "unit_price": unit_price,
            }
        )

    _save_cart(cart)
    flash("Sepete eklendi.", "success")
    return redirect(url_for("client.cart"))


@client_bp.post("/cart/qty")
def cart_qty():
    cart = _get_cart()
    try:
        idx = int(request.form.get("idx", "-1"))
        delta = int(request.form.get("delta", "0"))
    except ValueError:
        return redirect(url_for("client.cart"))

    if not (0 <= idx < len(cart)):
        return redirect(url_for("client.cart"))

    if delta not in (-1, 1):
        return redirect(url_for("client.cart"))

    current = int(cart[idx].get("qty", 1))
    new_qty = current + delta

    if new_qty <= 0:
        cart.pop(idx)
    else:
        if new_qty > 20:
            new_qty = 20
        cart[idx]["qty"] = new_qty

    _save_cart(cart)
    return redirect(url_for("client.cart"))


@client_bp.post("/cart/set")
def cart_set():
    cart = _get_cart()
    try:
        idx = int(request.form.get("idx", "-1"))
        qty = int(request.form.get("qty", "1"))
    except ValueError:
        return redirect(url_for("client.cart"))

    if not (0 <= idx < len(cart)):
        return redirect(url_for("client.cart"))

    if qty <= 0:
        cart.pop(idx)
    else:
        if qty > 20:
            qty = 20
        cart[idx]["qty"] = qty

    _save_cart(cart)
    return redirect(url_for("client.cart"))


@client_bp.get("/cart")
def cart():
    cart = _get_cart()
    total = 0.0
    for item in cart:
        total += float(item.get("unit_price", 0)) * int(item.get("qty", 1))

    return render_template("client/cart.html", cart=cart, total=total)


@client_bp.post("/cart/remove")
def cart_remove():
    cart = _get_cart()
    try:
        idx = int(request.form.get("idx", "-1"))
    except ValueError:
        idx = -1

    if 0 <= idx < len(cart):
        cart.pop(idx)
        _save_cart(cart)
        flash("Ürün sepetten çıkarıldı.", "success")
    else:
        flash("Sepet satırı bulunamadı.", "danger")

    return redirect(url_for("client.cart"))


@client_bp.get("/checkout")
def checkout():
    cart = _get_cart()
    if not cart:
        flash("Sepet boş.", "warning")
        return redirect(url_for("client.home"))

    total = 0.0
    for item in cart:
        total += float(item.get("unit_price", 0)) * int(item.get("qty", 1))

    return render_template(
        "client/checkout.html",
        cart=cart,
        total=total,
        last_phone=session.get("last_phone", ""),
    )


@client_bp.post("/checkout")
def checkout_submit():
    db_path = current_app.config["DB_PATH"]
    cart = _get_cart()
    if not cart:
        flash("Sepet boş.", "warning")
        return redirect(url_for("client.home"))

    delivery_type = (request.form.get("delivery_type") or "pickup").strip()
    address = (request.form.get("address") or "").strip()
    note = (request.form.get("note") or "").strip()

    if delivery_type not in ("pickup", "delivery"):
        flash("Teslimat tipi geçersiz.", "danger")
        return redirect(url_for("client.checkout"))

    customer_name = (request.form.get("customer_name") or "").strip()
    customer_phone = (request.form.get("customer_phone") or "").strip()

    if len(customer_name) < 2:
        flash("İsim alanı zorunludur.", "danger")
        return redirect(url_for("client.checkout"))

    normalized_phone = _normalize_phone(customer_phone)
    if not normalized_phone:
        flash("Telefon formatı geçersiz. Örn: 05xx xxx xx xx", "danger")
        return redirect(url_for("client.checkout"))

    customer_phone = normalized_phone

    if delivery_type == "delivery" and len(address) < 10:
        flash("Adrese teslim için adres alanı zorunludur.", "danger")
        return redirect(url_for("client.checkout"))

    if len(note) > 250:
        note = note[:250]

    # Stok kontrolü: ürün bazında toplam gram ihtiyacı
    required_grams = defaultdict(int)
    for item in cart:
        pid = int(item["product_id"])
        gram = int(item["gram"])
        qty = int(item.get("qty", 1))
        required_grams[pid] += gram * qty

    # Ürünleri çekip stok kontrol et
    for pid, need_gram in required_grams.items():
        product = fetch_one(db_path, "SELECT id, name, stock_gram, is_active FROM products WHERE id=?", (pid,))
        if not product or int(product["is_active"]) != 1:
            flash("Sepette satışta olmayan ürün var. Lütfen sepeti güncelleyin.", "danger")
            return redirect(url_for("client.cart"))

        stock = int(product["stock_gram"]) if product["stock_gram"] is not None else 0
        if stock < need_gram:
            flash(f"Stok yetersiz: {product['name']} (Gerekli: {need_gram}g / Stok: {stock}g)", "danger")
            return redirect(url_for("client.cart"))

    # Sipariş oluşturma: transaction mantığı için tek connection ile ilerlemek daha sağlıklı.
    from database import create_connection

    conn = create_connection(db_path)
    try:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO orders (customer_name, customer_phone, status, created_at, delivery_type, address, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (customer_name, customer_phone, "alındı", now_str(), delivery_type, address or None, note or None),
        )
        order_id = cur.lastrowid

        # Order item insert
        item_rows = []
        for item in cart:
            pid = int(item["product_id"])
            gram = int(item["gram"])
            qty = int(item.get("qty", 1))
            unit_price = float(item.get("unit_price", 0))
            # Şemada qty yok; qty kadar satır ekleyerek ilerliyoruz.
            for _ in range(qty):
                item_rows.append((order_id, pid, item["grind_type"], gram, unit_price))

        cur.executemany(
            """
            INSERT INTO order_items (order_id, product_id, grind_type, gram, price)
            VALUES (?, ?, ?, ?, ?)
            """,
            item_rows,
        )

        # Stok düş
        for pid, need_gram in required_grams.items():
            cur.execute(
                "UPDATE products SET stock_gram = stock_gram - ? WHERE id=? AND stock_gram >= ?",
                (need_gram, pid, need_gram),
            )
            if cur.rowcount != 1:
                # Çok nadiren yarış durumunda (concurrency) stok düşmeyebilir.
                raise RuntimeError("Stok güncellenemedi. Lütfen tekrar deneyin.")

        movement_rows = []
        for pid, need_gram in required_grams.items():
            movement_rows.append(
                (
                    pid,
                    -int(need_gram),
                    "Sipariş ile stok düşümü",
                    "order",
                    int(order_id),
                    now_str(),
                )
            )
        if movement_rows:
            cur.executemany(
                """
                INSERT INTO stock_movements (product_id, change_gram, reason, ref_type, ref_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                movement_rows,
            )

        conn.commit()

    except Exception as e:
        conn.rollback()
        flash(f"Sipariş oluşturulamadı: {str(e)}", "danger")
        return redirect(url_for("client.checkout"))
    finally:
        conn.close()

    # Sepeti temizle
    _save_cart([])

    # Kullanıcı siparişlerini daha sonra görebilsin diye.
    session["last_phone"] = customer_phone
    session.modified = True
    return render_template("client/order_success.html", order_id=order_id)


@client_bp.get("/orders")
def orders():
    db_path = current_app.config["DB_PATH"]

    phone_query = (request.args.get("phone") or "").strip()
    phone_session = (session.get("last_phone") or "").strip()

    phone = phone_query or phone_session
    normalized = _normalize_phone(phone) if phone else None

    orders_rows = []
    if phone and not normalized:
        flash("Telefon formatı geçersiz. Örn: 05xx xxx xx xx", "danger")

    if normalized:
        orders_rows = fetch_all(
            db_path,
            """
            SELECT o.*, COALESCE(SUM(oi.price), 0) AS total
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE o.customer_phone = ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
            """,
            (normalized,),
        )

    return render_template(
        "client/orders.html",
        orders=orders_rows,
        phone=normalized or phone_query or phone_session,
    )


@client_bp.get("/orders/<int:order_id>")
def order_detail(order_id: int):
    db_path = current_app.config["DB_PATH"]

    phone_query = (request.args.get("phone") or "").strip()
    phone_session = (session.get("last_phone") or "").strip()
    normalized = _normalize_phone(phone_query or phone_session)

    if not normalized:
        flash("Sipariş detayı için telefon doğrulaması gerekli.", "warning")
        return redirect(url_for("client.orders"))

    order = fetch_one(
        db_path,
        "SELECT * FROM orders WHERE id=? AND customer_phone=?",
        (order_id, normalized),
    )
    if not order:
        flash("Sipariş bulunamadı.", "danger")
        return redirect(url_for("client.orders", phone=normalized))

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
        "client/order_detail.html",
        order=order,
        items=items,
        total=total,
        phone=normalized,
    )


@client_bp.get("/about")
def about():
    return render_template("client/about.html")
