# Eventra Backend

FastAPI + PostgreSQL

## Kurulum

```bash
cd backend

# Virtual environment oluştur
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyasını oluştur
cp .env.example .env
# .env dosyasını düzenle (DATABASE_URL, SECRET_KEY vb.)

# PostgreSQL'de veritabanı oluştur
createdb eventra

# Sunucuyu başlat (tablolar otomatik oluşur)
uvicorn app.main:app --reload
```

## API Dökümantasyonu

Sunucu çalışınca: http://localhost:8000/docs

## İlk Admin Hesabı

```bash
curl -X POST http://localhost:8000/admin/setup \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@salon.com","password":"güçlüşifre","admin_secret":"admin-setup-secret"}'
```

## Ortam Değişkenleri

| Değişken | Açıklama |
|----------|----------|
| `DATABASE_URL` | PostgreSQL bağlantı adresi |
| `SECRET_KEY` | JWT imzalama anahtarı (32+ karakter) |
| `ADMIN_SECRET` | İlk admin hesabı oluşturmak için gizli kod |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token geçerlilik süresi (varsayılan: 10080 = 7 gün) |
