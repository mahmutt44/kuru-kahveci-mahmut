#!/usr/bin/env python3
"""
Cloudinary bağlantısını test et
"""

import os
from dotenv import load_dotenv

# Environment variables'ı yükle
load_dotenv()

print("=== CLOUDINARY AYARLARI ===")
cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
api_key = os.getenv('CLOUDINARY_API_KEY')
api_secret = os.getenv('CLOUDINARY_API_SECRET')

print(f"Cloud Name: {cloud_name}")
print(f"API Key: {api_key}")
print(f"API Secret: {'*' * len(api_secret) if api_secret else 'None'}")

# Cloudinary'i başlatmayı dene
try:
    import cloudinary
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )
    print("\n✅ Cloudinary başarıyla yapılandırıldı")
    
    # Test upload
    print("\nTest görsel yükleniyor...")
    result = cloudinary.uploader.upload(
        "https://via.placeholder.com/150",
        folder="test",
        resource_type="image"
    )
    print(f"✅ Test başarılı: {result['secure_url']}")
    
except Exception as e:
    print(f"\n❌ Hata: {e}")
