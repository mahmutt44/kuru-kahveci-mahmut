# Kurulum Talimatları (Görsel Sorunu Çözümü)

## Diğer PC'de Kurulum

### 1. Projeyi Klonlayın
```bash
git clone https://github.com/mahmutt44/kuru-kahveci-mahmut.git
cd kuru-kahveci-mahmut
```

### 2. Python Kurulumu
```bash
pip install -r requirements.txt
```

### 3. Veritabanını Sıfırlayın (ÖNEMLİ)
```bash
# Eski veritabanını sil
del kahveci.db

# Yeni veritabanı oluştur (görsellerle birlikte)
python app.py
```

### 4. Görsellerin Geldiğini Kontrol Edin
```bash
# Görsel klasörünü kontrol et
dir app\static\images

# Çıktı şöyle olmalı:
# Brezilya Santos Koyu.png
# Costa Rica Tarrazu Orta.png
# Espresso Harmanı Koyu.png
# Etiyopya Yirgacheffe Açık.png
# Filtre Harmanı Orta.png
# Guatemala Antigua Orta.png
# Kenya AA Açık.png
# Kolombiya Supremo Orta.png
```

### 5. Siteyi Açın
Tarayıcıda: http://127.0.0.1:5000

## Eğer Görseller Hala Görünmüyorsa

### Seçenek 1: Manuel Görsel İndirme
Görselleri GitHub'dan manuel indirin:
https://github.com/mahmutt44/kuru-kahveci-mahmut/tree/main/app/static/images

### Seçenek 2: Git LFS Kullanımı
```bash
git lfs pull
```

### Seçenek 3: Veritabanını Güncelleme
```bash
python -c "
from database import execute
execute('kahveci.db', 'UPDATE products SET image_path = NULL')
print('Görsel path\'leri sıfırlandı')
"
```

## Not
- İlk kurulumda `database.py` içindeki `init_db()` fonksiyonu otomatik çalışır
- Tüm görseller doğru path'lerle yüklenir
- Stoklar kg olarak ayarlanır
