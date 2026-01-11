# Kuru Kahveci Mahmut 

Flask tabanlı kahve dükkanı e-ticaret platformu.

## Özellikler

- Ürün listeleme ve sepet yönetimi
- Kahve özellikleri (köken, işleme, espresso uyumluluğu)
- Responsive tasarım (mobil uyumlu)
- Dark/Light theme desteği
- Admin paneli (ürün yönetimi, sipariş takibi)
- Stok takibi ve hareketleri
- Modern UI (Bootstrap 5 + Lucide icons)

## Canlı Demo

[https://kuru-kahveci-mahmut.onrender.com](https://kuru-kahveci-mahmut.onrender.com)

## Kurulum

### Gereksinimler
- Python 3.8+
- pip

### Adımlar
```bash
# Klonla
git clone https://github.com/mahmutt44/kuru-kahveci-mahmut.git
cd kuru-kahveci-mahmut

# Kurulum
pip install -r requirements.txt

# Veritabanını başlat
python sync_products.py

# Çalıştır
python app.py
```

Site: http://127.0.0.1:5000

## Admin Paneli

- URL: `/admin`
- Kullanıcı: `admin`
- Şifre: `admin123`

## Teknolojiler

- **Backend:** Flask, SQLite
- **Frontend:** Bootstrap 5, JavaScript
- **Icons:** Lucide Icons
- **Deployment:** Render

## Proje Yapısı

```
├── app/
│   ├── __init__.py          # Flask app konfigürasyonu
│   ├── routes/
│   │   ├── client.py        # Müşteri route'ları
│   │   └── admin.py        # Admin route'ları
│   ├── templates/
│   │   ├── client/          # Müşteri template'leri
│   │   └── admin/           # Admin template'leri
│   └── static/
│       ├── css/             # Stil dosyaları
│       └── images/          # Ürün görselleri
├── database.py              # Veritabanı işlemleri
├── app.py                   # Ana uygulama dosyası
├── wsgi.py                  # Deployment için WSGI
└── requirements.txt         # Python bağımlılıkları
```

## UI Özellikler

- Kahve temalı renk paleti
- Sticky sepet butonu
- Ürün kartları (stok durumu, köken bilgisi)
- Dark/Light theme toggle
- Responsive mobil menü

## Admin Özellikler

- Ürün yönetimi (CRUD)
- Sipariş takibi
- Stok hareketleri
- Ürün galeri yönetimi
- Yazdırılabilir sipariş fişi

## Demo Ürünler

- Brezilya Santos Koyu
- Etiyopya Yirgacheffe  
- Kolombiya Supremo
- Guatemala Antigua
- Kenya AA
- Sumatra Mandheling

---

Made with  by [mahmutt44](https://github.com/mahmutt44)
