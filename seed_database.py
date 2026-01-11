import os
import sqlite3
from database import get_db_path

def seed_database():
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Mevcut ürünleri kontrol et
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        
        if product_count == 0:
            # Başlangıç ürünlerini ekle
            products = [
                ("Brezilya Santos Koyu", 250.00, "images/Brezilya_Santos_Koyu.png", "Koyu kavrum", "Brezilya", "Natur", True, 50),
                ("Etiyopya Yirgacheffe", 280.00, "images/Etiyopya_Yirgacheffe_Ack.png", "Orta kavrum", "Etiyopya", "Yıkanmış", True, 30),
                ("Kolombiya Supremo", 320.00, "images/Kolombiya_Supremo_Orta.png", "Orta kavrum", "Kolombiya", "Yıkanmış", True, 25)
            ]
            
            cursor.executemany("""
                INSERT INTO products (name, price, image_path, description, origin, process, is_espresso, stock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, products)
            
            conn.commit()
            print(f"{len(products)} ürün eklendi")
        else:
            print(f"Veritabanında zaten {product_count} ürün var")

if __name__ == "__main__":
    seed_database()
