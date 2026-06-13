# Eventra

Düğün salonu yönetim sistemi. FastAPI backend + SvelteKit frontend'ler.

---

## Servisler

| Servis | URL | Port |
|--------|-----|------|
| Backend API | http://localhost:8000 | 8000 |
| API Dokümantasyonu | http://localhost:8000/docs | 8000 |
| Ana Uygulama | http://localhost:5173 | 5173 |
| Misafir Portalı | http://localhost:5174 | 5174 |
| Admin Paneli | http://localhost:5175 | 5175 |

---

## Kurulum (İlk Kez)

### 1. PostgreSQL

PostgreSQL kurulu ve çalışıyor olmalı. `than` rolü için:

```bash
sudo -u postgres psql -c "CREATE USER than WITH SUPERUSER LOGIN;"
sudo -u postgres createdb eventra
```

### 2. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`.env` dosyasını oluştur (zaten varsa atla):

```
DATABASE_URL=postgresql://than@/eventra
SECRET_KEY=eventra-secret-key-change-in-production-32chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
ADMIN_SECRET=admin-setup-secret
```

Tabloları oluştur ve backend'i başlat:

```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend'ler

Her biri için ayrı terminal:

```bash
cd app && npm install && npm run dev                  # port 5173
cd portal/app && npm install && npm run dev          # port 5174
cd admin/app && npm install && npm run dev           # port 5175
```

---

## Hepsini Birden Başlatma

Zaten kuruluysa (venv + node_modules mevcut):

```bash
# Terminal 1 — Backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2 — Ana Uygulama
cd app && npm run dev

# Terminal 3 — Misafir Portalı
cd portal/app && npm run dev

# Terminal 4 — Admin Paneli
cd admin/app && npm run dev
```

---

## Admin Hesabı Oluşturma

Backend çalışırken **bir kez** çalıştır:

```bash
curl -X POST http://localhost:8000/admin/setup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@eventra.com",
    "password": "Eventra2024!",
    "admin_secret": "admin-setup-secret"
  }'
```

Başarılıysa `access_token` döner. Bu hesap admin panelinde kullanılır.

**Varsayılan admin bilgileri:**

| Alan | Değer |
|------|-------|
| E-posta | admin@eventra.com |
| Şifre | Eventra2024! |
| Admin Secret | admin-setup-secret |

> `admin_secret` değeri `backend/.env` dosyasındaki `ADMIN_SECRET` ile eşleşmeli.

---

## Salon ve Kullanıcı Oluşturma

Admin token'ı aldıktan sonra salon oluştur:

```bash
curl -X POST http://localhost:8000/admin/salons \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "İnci Davet",
    "owner_email": "salon@eventra.com",
    "owner_username": "Salon Yöneticisi",
    "owner_password": "Salon2024!"
  }'
```

Salon oluşturulunca otomatik olarak Düğün, Nişan, Kına, Kurumsal, Mezuniyet etkinlik tipleri eklenir.

Salon kullanıcısı http://localhost:5173 adresinden giriş yapar.

---

## Örnek Salon (Hazır)

Veritabanında hazır örnek salon ve kullanıcı mevcuttur:

**Salon Bilgileri:**

| Alan | Değer |
|------|-------|
| Salon Adı | İnci Davet |
| Adres | Atatürk Cad. No:42, İstanbul |
| Sözleşme Öneki | IDS |
| KDV Oranı | %20 |
| Maks. Kullanıcı | 5 |

**Salon Kullanıcısı (Giriş için):**

| Alan | Değer |
|------|-------|
| E-posta | salon@eventra.com |
| Şifre | Salon2024! |
| Rol | owner |

Giriş adresi: http://localhost:5173/login

---

## Özellikler

### Ana Uygulama (port 5173)
- **Dashboard** — USD/EUR → TRY kur göstergesi (Frankfurter API), gelir özeti
- **Takvim** — etkinlik yönetimi, özelleştirilebilir form alanları (görünürlük kontrolü + sözleşme etiketleri)
- **Randevular** — müşteri yönetimi, özel alan tanımları
- **Salon Düzeni** — masa/koltuk düzeni tasarımı, SVG canvas
- **Sözleşmeler** — .docx/.odt şablon yükleme, `%etiket%` ile otomatik doldurma ve indirme
- **Ayarlar** — salon bilgileri, etkinlik formu alan yönetimi, sözleşme etiket eşleşmeleri
- **UI Modu** — Tam mod (ikonlar + crown animasyonu) / Sade mod (kompakt, ikonsuz); tercih backend'e kaydedilir

### Misafir Portalı (port 5174)
- Token tabanlı, her etkinlik için benzersiz URL
- Tek instance tüm salonlara hizmet eder (çok kiracılı)
- Organizasyon formu doldurma, salon oturma düzeni oluşturma

### Admin Paneli (port 5175)
- Salon oluşturma/yönetimi

---

## Proje Yapısı

```
eventra/
├── backend/          # FastAPI + PostgreSQL
│   ├── app/
│   │   ├── routers/
│   │   │   ├── auth.py            # JWT giriş
│   │   │   ├── events.py          # Etkinlik CRUD
│   │   │   ├── customers.py       # Müşteri CRUD
│   │   │   ├── contracts.py       # Şablon yükleme, sözleşme oluşturma
│   │   │   ├── event_form_fields.py  # Etkinlik form alan tanımları
│   │   │   ├── expenses.py        # Gider yönetimi
│   │   │   ├── venue.py           # Salon düzeni
│   │   │   ├── portal.py          # Misafir portalı endpoint'leri
│   │   │   ├── settings.py        # Salon ayarları, kullanıcı tercihleri
│   │   │   └── admin_router.py    # Admin işlemleri
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── main.py
│   ├── uploads/      # Yüklenen sözleşme şablonları (.docx / .odt)
│   └── requirements.txt
├── app/              # Ana uygulama (SvelteKit) — port 5173
├── portal/app/       # Misafir portalı (SvelteKit) — port 5174
└── admin/app/        # Admin paneli (SvelteKit) — port 5175
```
