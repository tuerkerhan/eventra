# Eventra Backend

FastAPI + PostgreSQL (peer auth, socket bağlantısı).

## Kurulum

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Tablolar ilk başlatmada otomatik oluşur (`Base.metadata.create_all`).

## Ortam Değişkenleri

| Değişken | Açıklama |
|----------|----------|
| `DATABASE_URL` | PostgreSQL bağlantı adresi (`postgresql://than@/eventra`) |
| `SECRET_KEY` | JWT imzalama anahtarı (32+ karakter) |
| `ALGORITHM` | JWT algoritması (varsayılan: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token ömrü (varsayılan: `10080` = 7 gün) |
| `ADMIN_SECRET` | İlk admin hesabı kurulum kodu |

## Router'lar

| Dosya | Prefix | Açıklama |
|-------|--------|----------|
| `auth.py` | `/auth` | JWT giriş |
| `events.py` | `/events` | Etkinlik CRUD |
| `customers.py` | `/customers` | Müşteri CRUD |
| `contracts.py` | `/contracts` | .docx/.odt şablon yükleme, sözleşme oluşturma |
| `event_form_fields.py` | `/event-form-fields` | Etkinlik formu alan tanımları (builtin + özel) |
| `expenses.py` | `/expenses` | Gider yönetimi |
| `venue.py` | `/venue` | Salon düzeni layout/masa CRUD |
| `portal.py` | `/portal` | Misafir portalı (token bazlı, auth yok) |
| `settings.py` | `/settings` | Salon ayarları, kullanıcı tercihleri (`ui_mode`) |
| `admin_router.py` | `/admin` | Admin: salon ve kullanıcı yönetimi |

## API Dokümantasyonu

Sunucu çalışırken: http://localhost:8000/docs

## Sözleşme Şablonları

Yüklenen `.docx` ve `.odt` dosyaları `uploads/<salon_id>/` klasörüne kaydedilir.  
`%etiket%` sözdizimi ile placeholder'lar etkinlik verisiyle doldurulur.  
ODT için LibreOffice'in XML'de span'lar arasına böldüğü placeholder'lar otomatik normalize edilir.
