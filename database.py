import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime


DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "kahveci.db")


def _utc_now_str() -> str:
    # SQLite tarafında okunabilir ve filtrelenebilir bir format.
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_db_path(app_db_path: str | None = None) -> str:
    return app_db_path or DEFAULT_DB_PATH


def create_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    # Foreign key kısıtları SQLite'ta default kapalı gelir.
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def db_cursor(db_path: str):
    conn = create_connection(db_path)
    try:
        cur = conn.cursor()
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str):
    with db_cursor(db_path) as (conn, cur):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                roast_type TEXT NOT NULL,
                price_250 REAL NOT NULL,
                price_500 REAL NOT NULL,
                price_1000 REAL NOT NULL,
                stock_gram INTEGER NOT NULL DEFAULT 0,
                image_path TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            );
            """
        )

        cur.execute("PRAGMA table_info(products);")
        product_cols = [r[1] for r in cur.fetchall()]
        if "origin" not in product_cols:
            cur.execute("ALTER TABLE products ADD COLUMN origin TEXT;")
        if "process" not in product_cols:
            cur.execute("ALTER TABLE products ADD COLUMN process TEXT;")
        if "altitude" not in product_cols:
            cur.execute("ALTER TABLE products ADD COLUMN altitude INTEGER;")
        if "tasting_notes" not in product_cols:
            cur.execute("ALTER TABLE products ADD COLUMN tasting_notes TEXT;")
        if "acidity" not in product_cols:
            cur.execute("ALTER TABLE products ADD COLUMN acidity INTEGER NOT NULL DEFAULT 3;")
        if "body" not in product_cols:
            cur.execute("ALTER TABLE products ADD COLUMN body INTEGER NOT NULL DEFAULT 3;")
        if "sweetness" not in product_cols:
            cur.execute("ALTER TABLE products ADD COLUMN sweetness INTEGER NOT NULL DEFAULT 3;")
        if "espresso_compatible" not in product_cols:
            cur.execute("ALTER TABLE products ADD COLUMN espresso_compatible INTEGER NOT NULL DEFAULT 0;")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        cur.execute("PRAGMA table_info(orders);")
        order_cols = [r[1] for r in cur.fetchall()]
        if "delivery_type" not in order_cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_type TEXT NOT NULL DEFAULT 'pickup';")
        if "address" not in order_cols:
            cur.execute("ALTER TABLE orders ADD COLUMN address TEXT;")
        if "note" not in order_cols:
            cur.execute("ALTER TABLE orders ADD COLUMN note TEXT;")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                grind_type TEXT NOT NULL,
                gram INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE RESTRICT
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS product_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                change_gram INTEGER NOT NULL,
                reason TEXT NOT NULL,
                ref_type TEXT,
                ref_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE RESTRICT
            );
            """
        )

        # Basit migration: eski tabloda qty/unit_price varsa, yeni şemaya taşır.
        cur.execute("PRAGMA table_info(order_items);")
        cols = [r[1] for r in cur.fetchall()]
        if "unit_price" in cols or "qty" in cols:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS order_items_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    grind_type TEXT NOT NULL,
                    gram INTEGER NOT NULL,
                    price REAL NOT NULL,
                    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE RESTRICT
                );
                """
            )

            # Eski tabloda price alanı çoğunlukla toplam fiyat olduğu için direkt taşınır.
            cur.execute(
                """
                INSERT INTO order_items_new (id, order_id, product_id, grind_type, gram, price)
                SELECT id, order_id, product_id, grind_type, gram, price
                FROM order_items;
                """
            )
            cur.execute("DROP TABLE order_items;")
            cur.execute("ALTER TABLE order_items_new RENAME TO order_items;")

        # Basit index'ler
        cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_product_images_product_id ON product_images(product_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_product_id ON stock_movements(product_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_created_at ON stock_movements(created_at);")

        # İlk kurulumda örnek ürünler (uygulama boş açılmasın diye).
        cur.execute("SELECT COUNT(*) FROM products;")
        count = int(cur.fetchone()[0])
        if count == 0:
            cur.executemany(
                """
                INSERT INTO products (name, description, roast_type, price_250, price_500, price_1000, stock_gram, image_path, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                [
                    (
                        "Kolombiya Supremo",
                        "Çikolata ve fındık notaları. Dengeli gövde.",
                        "Orta",
                        220.0,
                        410.0,
                        780.0,
                        5000,
                        None,
                    ),
                    (
                        "Etiyopya Yirgacheffe",
                        "Çiçeksi aroma, narenciye asiditesi.",
                        "Açık",
                        250.0,
                        470.0,
                        890.0,
                        4000,
                        None,
                    ),
                    (
                        "Brezilya Santos",
                        "Karamel tatlılığı, düşük asidite.",
                        "Koyu",
                        210.0,
                        395.0,
                        750.0,
                        6000,
                        None,
                    ),
                    (
                        "Guatemala Antigua",
                        "Baharatlı bitiş, kakao notaları.",
                        "Orta",
                        235.0,
                        440.0,
                        840.0,
                        4500,
                        None,
                    ),
                    (
                        "Kenya AA",
                        "Canlı asidite, kırmızı meyve notaları.",
                        "Açık",
                        265.0,
                        495.0,
                        945.0,
                        3500,
                        None,
                    ),
                    (
                        "Costa Rica Tarrazu",
                        "Temiz fincan, karamel ve narenciye.",
                        "Orta",
                        245.0,
                        465.0,
                        895.0,
                        4200,
                        None,
                    ),
                    (
                        "Espresso Harmanı",
                        "Yoğun gövde, kremamsı bitiş. Espresso için ideal.",
                        "Koyu",
                        230.0,
                        430.0,
                        820.0,
                        7000,
                        None,
                    ),
                    (
                        "Filtre Harmanı",
                        "Dengeli, aromatik. Günlük filtre için.",
                        "Orta",
                        215.0,
                        405.0,
                        770.0,
                        6500,
                        None,
                    ),
                ],
            )


def fetch_all(db_path: str, sql: str, params: tuple = ()):
    with db_cursor(db_path) as (conn, cur):
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_one(db_path: str, sql: str, params: tuple = ()):
    with db_cursor(db_path) as (conn, cur):
        cur.execute(sql, params)
        return cur.fetchone()


def execute(db_path: str, sql: str, params: tuple = ()) -> int:
    with db_cursor(db_path) as (conn, cur):
        cur.execute(sql, params)
        return cur.lastrowid


def execute_many(db_path: str, sql: str, seq_of_params: list[tuple]):
    with db_cursor(db_path) as (conn, cur):
        cur.executemany(sql, seq_of_params)


def now_str() -> str:
    return _utc_now_str()
