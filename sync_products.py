import os
import sqlite3
import requests
from database import get_db_path

def sync_from_render():
    """Render'daki veritabanını yerel'e kopyala (eğer erişilebilirse)"""
    try:
        # Render'dan veritabanını çek (eğer public URL varsa)
        render_url = "https://kuru-kahveci-mahmut.onrender.com"
        
        # Bu yöntem genellikle çalışmaz çünkü veritabanı public değil
        print("Render'dan veritabanı çekilemiyor - güvenlik nedeniyle")
        return False
        
    except Exception as e:
        print(f"Hata: {e}")
        return False

def create_sample_products():
    """Örnek ürünler oluştur"""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Mevcut ürünleri sil
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM product_images")
        
        # İstenen ürünler
        products = [
            ("Guatemala Antigua", "Dumanlı, baharatlı ve çikolata notaları", "Orta", 340.0, 650.0, 1200.0, 25, "images/Guatemala_Antigua_Orta.png", "Guatemala", "Yıkanmış", 1),
            ("Kenya AA", "Asidik, vişne ve karabiber notaları", "Açık", 380.0, 720.0, 1300.0, 20, "images/Kenya_AA_Ack.png", "Kenya", "Yıkanmış", 0),
            ("Costa Rica Tarrazu", "Çikolata, narenciye ve karamel notaları", "Orta", 360.0, 680.0, 1250.0, 22, "images/Kolombiya_Supremo_Orta.png", "Kosta Rika", "Yıkanmış", 1),
            ("Espresso Harmanı", "Espresso için özel harman, kremsi ve tatlı", "Koyu", 280.0, 520.0, 950.0, 40, "images/Brezilya_Santos_Koyu.png", "Harman", "Natur", 1),
            ("Filtre Harmanı", "Filtre kahve için dengeli harman", "Orta", 260.0, 480.0, 880.0, 35, "images/Etiyopya_Yirgacheffe_Ack.png", "Harman", "Yıkanmış", 0),
            ("Brezilya Santos", "Yoğun gövde, fındık ve çikolata", "Koyu", 250.0, 480.0, 900.0, 45, "images/Brezilya_Santos_Koyu.png", "Brezilya", "Natur", 1),
            ("Etiyopya Yirgacheffe", "Meyvemsi, çiçeksi aromalar", "Orta", 280.0, 540.0, 1000.0, 30, "images/Etiyopya_Yirgacheffe_Ack.png", "Etiyopya", "Yıkanmış", 0),
            ("Kolombiya Supremo", "Karamel ve kuru meyve", "Orta", 320.0, 600.0, 1100.0, 28, "images/Kolombiya_Supremo_Orta.png", "Kolombiya", "Yıkanmış", 1),
        ]
        
        cursor.executemany("""
            INSERT INTO products (name, description, roast_type, price_250, price_500, price_1000, stock_gram, image_path, origin, process, espresso_compatible)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, products)
        
        conn.commit()
        print(f"{len(products)} ürün oluşturuldu:")
        for product in products:
            print(f"  - {product[0]} ({product[3]}₺/{product[4]}₺/{product[5]}₺)")

if __name__ == "__main__":
    # Render'dan sync dene, olmazsa örnek ürünler oluştur
    if not sync_from_render():
        create_sample_products()
