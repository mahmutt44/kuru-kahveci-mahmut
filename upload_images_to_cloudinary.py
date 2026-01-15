#!/usr/bin/env python3
"""
Mevcut görselleri Cloudinary'e yükle
"""

import os
from cloudinary_config import init_cloudinary, upload_image_to_cloudinary

def upload_existing_images():
    """Mevcut görselleri Cloudinary'e yükle"""
    
    # Cloudinary'i başlat
    init_cloudinary()
    
    images_dir = "app/static/images"
    
    # Görseller ve Cloudinary'deki isimleri
    image_mappings = {
        "Brezilya Santos Koyu.png": "brezilya-santos-koyu",
        "Costa Rica Tarrazu Orta.png": "costa-rica-tarrazu-orta", 
        "Espresso Harmanı Koyu.png": "espresso-harmani-koyu",
        "Etiyopya Yirgacheffe Açık.png": "etiyopya-yirgacheffe-acik",
        "Filtre Harmanı Orta.png": "filtre-harmani-orta",
        "Guatemala Antigua Orta.png": "guatemala-antigua-orta",
        "Kenya AA Açık.png": "kenya-aa-acik",
        "Kolombiya Supremo Orta.png": "kolombiya-supremo-orta"
    }
    
    print("Görseller Cloudinary'e yükleniyor...")
    
    for filename, cloudinary_name in image_mappings.items():
        file_path = os.path.join(images_dir, filename)
        
        if os.path.exists(file_path):
            # Cloudinary'e yükle
            url = upload_image_to_cloudinary(file_path, "kahve")
            
            if url:
                print(f"✅ {filename} -> {url}")
            else:
                print(f"❌ {filename} yüklenemedi")
        else:
            print(f"❌ Dosya bulunamadı: {file_path}")

if __name__ == "__main__":
    upload_existing_images()
