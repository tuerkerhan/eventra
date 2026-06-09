### Epic 1: Design & Planning

* [ ] Database schema ve ERD (Entity-Relationship Diagram) çizimi.
* [ ] State Machine Diagram hazırlığı (`ReservationStatus` ve `OperationStatus` akışları için).
* [ ] Temel UI mockup'larının çizilmesi (Dashboard, Calendar, Reservation Form).
* [ ] Pilot test yapılacak salonla görüşülüp eski datalarının (Excel, defter vb.) formatının incelenmesi.

### Epic 2: Infrastructure & Setup

* [ ] Monorepo veya ayrı repository'lerin oluşturulması (SvelteKit + FastAPI).
* [ ] Docker Compose setup'ının yazılması (PostgreSQL, Redis, Backend, Frontend).
* [ ] Database migration altyapısının (Alembic) kurulması ve ilk init işleminin yapılması.
* [ ] Staging/Production için CI/CD pipeline (GitHub Actions/GitLab CI) kurulumu.

### Epic 3: Auth & Tenant Core

* [ ] `Organization`, `User` ve `Role` database modellerinin oluşturulması.
* [ ] JWT tabanlı Authentication ve Authorization endpoint'lerinin yazılması.
* [ ] Backend tarafında tenant izolasyonu (`organization_id` kontrolü) için Middleware yazılması.
* [ ] SvelteKit tarafında Login UI kodlaması.
* [ ] SvelteKit tarafında protected route yapısı ve auth state management kurulumu.

### Epic 4: Venue & Calendar

* [ ] `Venue`, `Hall` ve `EventType` database modellerinin yazılması.
* [ ] `Venue` ve `EventType` için CRUD endpoint'lerinin oluşturulması.
* [ ] SvelteKit tarafına FullCalendar (veya muadili bir kütüphane) entegrasyonu.
* [ ] Takvim UI'ında `EventType` renklerinin ve test dummy data'larının render edilmesi.

### Epic 5: Reservation Flow

* [ ] `Customer` ve `Reservation` database modellerinin yazılması.
* [ ] Rezervasyon oluşturma endpoint'inin yazılması (Tarih/saat çakışma validation logic'i dahil).
* [ ] Takvim üzerinden tıklayarak açılan yeni rezervasyon form UI'ının kodlanması.
* [ ] Form submit edildiğinde Backend ile entegrasyonun sağlanması.
* [ ] Rezervasyon detay sayfası ve Customer profil UI'ının yapılması.

### Epic 6: Finance & Basic Docs

* [ ] `Payment` database modelinin (Kapora, kalan bakiye, total tutar) oluşturulması.
* [ ] Rezervasyon detay sayfasına ödeme ekleme/düzenleme endpoint ve UI entegrasyonu.
* [ ] Backend'de temel HTML-to-PDF generation endpoint'inin yazılması (Basit sözleşme/makbuz çıktısı için).
* [ ] PDF çıktısının UI üzerinden indirilmesini sağlayan butonun bağlanması.
* [ ] Customer ve Reservation listeleri için Excel export endpoint'inin yazılması.

### Epic 7: Dashboard & Pilot Deployment

* [ ] Dashboard UI kodlaması (Bugünkü organizasyonlar, kapora bekleyenler, yaklaşan etkinlikler).
* [ ] Pilot müşteri ortamı için VPS (Ubuntu, Nginx, Docker) kurulumu ve SSL ayarları.
* [ ] Uygulamanın Production ortamına ilk deploy'unun atılması.
* [ ] Pilot müşterinin eski datalarını sisteme basacak import script'inin yazılması ve çalıştırılması.
* [ ] Pilot müşterinin yanına gidip ilk 2 gün operasyonu Shadow Testing (birlikte kullanarak) ile canlı test etme.
* [ ] Müşteriden gelen kritik UI/UX feedback'lerinin toplanıp bug-fix yapılması.