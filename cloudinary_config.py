"""
Cloudinary görsel yükleme ve yönetimi
"""

import os
import cloudinary
from cloudinary.uploader import upload
from dotenv import load_dotenv

# Environment variables'ı yükle
load_dotenv()

def init_cloudinary():
    """Cloudinary'i başlat"""
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )

def upload_image_to_cloudinary(file_path, folder="kahve"):
    """Görseli Cloudinary'e yükle"""
    try:
        result = upload(
            file_path,
            folder=folder,
            resource_type="image"
        )
        return result['secure_url']
    except Exception as e:
        print(f"Cloudinary yükleme hatası: {e}")
        return None

def get_cloudinary_url(image_name, folder="kahve"):
    """Cloudinary URL'i oluştur"""
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    return f"https://res.cloudinary.com/{cloud_name}/image/upload/{folder}/{image_name}"
