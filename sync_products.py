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
        
        # Örnek ürünler
        products = [
            ("Brezilya Santos Koyu", "Koyu kavrum, bitter ve fındık notaları", "Koyu", 250.0, 480.0, 900.0, 50, "images/Brezilya_Santos_Koyu.png", "Brezilya", "Natur", 1),
            ("Etiyopya Yirgacheffe", "Meyvemsi, çiçeksi ve çikolata notaları", "Orta", 280.0, 540.0, 1000.0, 30, "images/Etiyopya_Yirgacheffe_Ack.png", "Etiyopya", "Yıkanmış", 1),
            ("Kolombiya Supremo", "Karamel ve kuru meyve aromaları", "Orta", 320.0, 600.0, 1100.0, 25, "images/Kolombiya_Supremo_Orta.png", "Kolombiya", "Yıkanmış", 1),
            ("Guatemala Antigua", "Dumanlı, baharatlı ve çikolata notaları", "Koyu", 340.0, 650.0, 1200.0, 20, "images/Brezilya_Santos_Koyu.png", "Guatemala", "Yıkanmış", 1),
            ("Kenya AA", "Asidik, vişne ve karabiber notaları", "Açık", 380.0, 720.0, 1300.0, 15, "images/Etiyopya_Yirgacheffe_Ack.png", "Kenya", "Yıkanmış", 0),
            ("Sumatra Mandheling", "Toprak, mantar ve tropik meyve", "Koyu", 360.0, 680.0, 1250.0, 18, "images/Kolombiya_Supremo_Orta.png", "Endonezya", "Giling Basah", 1),
        ]
        
        cursor.executemany("""
            INSERT INTO products (name, description, roast_type, price_250, price_500, price_1000, stock_gram, image_path, origin, process, espresso_compatible)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, products)
        
        conn.commit()
        print(f"{len(products)} örnek ürün oluşturuldu")

if __name__ == "__main__":
    # Render'dan sync dene, olmazsa örnek ürünler oluştur
    if not sync_from_render():
        create_sample_products()
