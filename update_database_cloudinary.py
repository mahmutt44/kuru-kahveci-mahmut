#!/usr/bin/env python3
"""
Veritabanındaki görsel URL'lerini Cloudinary URL'leri ile güncelle
"""

from database import execute, fetch_all

def update_database_urls():
    """Veritabanındaki görselleri Cloudinary URL'leri ile güncelle"""
    
    db_path = "kahveci.db"
    
    # Cloudinary URL eşleştirmeleri
    cloudinary_urls = {
        "Kolombiya Supremo": "https://res.cloudinary.com/doduufpwn/image/upload/kahve/f7zzfyfphqbkc02u8ikr",
        "Etiyopya Yirgacheffe": "https://res.cloudinary.com/doduufpwn/image/upload/kahve/fy5s9rhdwrijm3wnzxpr",
        "Brezilya Santos": "https://res.cloudinary.com/doduufpwn/image/upload/kahve/nz5z5tiwedvcxz9fcjrv",
        "Guatemala Antigua": "https://res.cloudinary.com/doduufpwn/image/upload/kahve/i5vxuwqxpeansc4mjag6",
        "Kenya AA": "https://res.cloudinary.com/doduufpwn/image/upload/kahve/icx6z4pf1z1subck6wn3",
        "Costa Rica Tarrazu": "https://res.cloudinary.com/doduufpwn/image/upload/kahve/yr9wetjfpypjg7pjgy5q",
        "Espresso Harmanı": "https://res.cloudinary.com/doduufpwn/image/upload/kahve/zh9aqxetn75eyccwwytr",
        "Filtre Harmanı": "https://res.cloudinary.com/doduufpwn/image/upload/kahve/bmpdmvkeryapy5i2nvzw"
    }
    
    products = fetch_all(db_path, "SELECT id, name, image_path FROM products")
    
    print("Veritabanı Cloudinary URL'leri ile güncelleniyor...")
    
    for product in products:
        product_name = product['name']
        
        if product_name in cloudinary_urls:
            new_url = cloudinary_urls[product_name]
            
            execute(db_path, "UPDATE products SET image_path = ? WHERE id = ?", 
                   (new_url, product['id']))
            
            print(f"✅ {product_name}: {product['image_path'][:50]}... -> {new_url[:50]}...")

if __name__ == "__main__":
    update_database_urls()
