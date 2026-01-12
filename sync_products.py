import os
import sqlite3
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
        
        # İstenen ürünler - tam şemaya göre
        products = [
            (
                "Guatemala Antigua", 
                "Dumanlı, baharatlı ve çikolata notaları", 
                "Orta", 
                340.0, 650.0, 1200.0,  # price_250, price_500, price_1000
                25, # stock_gram
                "images/Guatemala_Antigua_Orta.png", # image_path
                1, # is_active
                "Guatemala", # origin
                "Yıkanmış", # process
                1500, # altitude
                "Dumanlı, baharatlı, çikolata, vanilya", # tasting_notes
                3, # acidity
                3, # body
                3, # sweetness
                1, # espresso_compatible
            ),
            (
                "Kenya AA", 
                "Asidik, vişne ve karabiber notaları", 
                "Açık", 
                380.0, 720.0, 1300.0,
                20,
                "images/Kenya_AA_Ack.png",
                1,
                "Kenya",
                "Yıkanmış",
                1800,
                "Vişne, kiraz, ahududu, greyfurt",
                4,
                2,
                2,
                0,
            ),
            (
                "Costa Rica Tarrazu", 
                "Çikolata, narenciye ve karamel notaları", 
                "Orta", 
                360.0, 680.0, 1250.0,
                22,
                "images/Costa_Rica_Tarrazu_Orta.png",
                1,
                "Kosta Rika",
                "Yıkanmış",
                1400,
                "Çikolata, narenciye, karamel, badem",
                3,
                3,
                3,
                1,
            ),
            (
                "Espresso Harmanı", 
                "Espresso için özel harman, kremsi ve tatlı", 
                "Koyu", 
                280.0, 520.0, 950.0,
                40,
                "images/Espresso_Harmanı_Koyu.png",
                1,
                "Harman",
                "Natur",
                None,
                "Kremsi, tatlı, karamel, fındık",
                3,
                4,
                3,
                1,
            ),
            (
                "Filtre Harmanı", 
                "Filtre kahve için dengeli harman", 
                "Orta", 
                260.0, 480.0, 880.0,
                35,
                "images/Filtre_Harmanı_Orta.png",
                1,
                "Harman",
                "Yıkanmış",
                None,
                "Meyvemsi, çiçeksi, narenciye",
                4,
                3,
                2,
                0,
            ),
            (
                "Brezilya Santos", 
                "Yoğun gövde, fındık ve çikolata", 
                "Koyu", 
                250.0, 480.0, 900.0,
                45,
                "images/Brezilya_Santos_Koyu.png",
                1,
                "Brezilya",
                "Natur",
                900,
                "Fındık, çikolata, karamel, vanilya",
                2,
                4,
                3,
                1,
            ),
            (
                "Etiyopya Yirgacheffe", 
                "Meyvemsi, çiçeksi aromalar", 
                "Orta", 
                280.0, 540.0, 1000.0,
                30,
                "images/Etiyopya_Yirgacheffe_Ack.png",
                1,
                "Etiyopya",
                "Yıkanmış",
                1800,
                "Meyve, çiçek, narenciye, limon",
                5,
                2,
                2,
                0,
            ),
            (
                "Kolombiya Supremo", 
                "Karamel ve kuru meyve", 
                "Orta", 
                320.0, 600.0, 1100.0,
                28,
                "images/Kolombiya_Supremo_Orta.png",
                1,
                "Kolombiya",
                "Yıkanmış",
                1700,
                "Karamel, kurutulmuş meyve, ceviz",
                3,
                3,
                3,
                1,
            ),
        ]
        
        cursor.executemany("""
            INSERT INTO products (
                name, description, roast_type, 
                price_250, price_500, price_1000, stock_gram, 
                image_path, is_active, origin, process, altitude, 
                tasting_notes, acidity, body, sweetness, 
                espresso_compatible
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, products)
        
        conn.commit()
        print(f"{len(products)} ürün oluşturuldu:")
        for product in products:
            print(f"  - {product[0]} ({product[3]}₺/{product[4]}₺/{product[5]}₺)")

if __name__ == "__main__":
    # Render'dan sync dene, olmazsa örnek ürünler oluştur
    if not sync_from_render():
        create_sample_products()
