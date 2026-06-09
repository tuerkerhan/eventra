# Eventra — Ürün Tanımı, Modül Planı ve Satış Stratejisi

## 1. Ürün Tanımı

**Eventra**, düğün salonları, davet mekanları, kır bahçeleri, oteller ve organizasyon şirketleri için geliştirilecek dikey bir işletme yönetim yazılımıdır.

Ürün; rezervasyon, müşteri ilişkileri, teklif, sözleşme, ödeme, takvim, müşteri portalı, görev yönetimi, tedarikçi koordinasyonu ve etkinlik günü operasyonlarını tek sistemde toplar.

Kısa tanım:

> **Eventra, etkinlik ve davet işletmeleri için rezervasyondan organizasyon gününe kadar tüm süreci yöneten modern operasyon platformudur.**

Satışta kullanılacak ana kategori:

> **Düğün salonu ve organizasyon yönetim sistemi**

Teknik/kurumsal kategoriler:

- Etkinlik yönetim yazılımı
- Düğün salonu CRM sistemi
- Davet mekanı rezervasyon sistemi
- Organizasyon operasyon yönetim platformu
- Dikey SaaS
- Hafif ERP / işletme yönetim sistemi

## 2. Marka Mimarisi

Ana şirket:

**Global Minima**

Ürün markası:

**Eventra**

Kullanım:

**Eventra by Global Minima**

Ürün ailesi:

- **Eventra Core**
- **Eventra Pro**
- **Eventra Flow**
- **Eventra Suite**

Modül isimleri:

- **Venue** — salon, mekan, takvim ve rezervasyon
- **CRM** — müşteri, satış süreci ve teklif takibi
- **Portal** — müşteriye özel dış sayfa
- **Docs** — sözleşme, teklif ve belge otomasyonu
- **Finance** — kapora, ödeme, taksit, kasa ve raporlar
- **Flow** — organizasyon operasyonu, görevler, timeline, tedarikçiler
- **Admin** — kullanıcı, yetki, paket, işletme ve sistem ayarları

## 3. Hedef Müşteriler

### 3.1 Birincil Hedef

Tek veya birkaç salon işleten düğün/davet salonları.

Örnek:
- düğün salonları
- nişan/kına salonları
- kır bahçeleri
- davet mekanları
- belediye sosyal tesisleri
- yemekli organizasyon salonları

Temel ihtiyaçları:
- rezervasyon çakışmasını engellemek
- kapora ve kalan ödemeyi takip etmek
- sözleşme çıkarmak
- müşteri bilgilerini düzenli tutmak
- yaklaşan organizasyonları görmek
- çalışanların aynı takvimi kullanması
- eski yazılım yerine daha modern ve erişilebilir sistem kullanmak

### 3.2 İkincil Hedef

Organizasyon şirketleri.

Örnek:
- düğün organizasyon firmaları
- event ajansları
- süsleme firmaları
- kurumsal etkinlik firmaları
- dış mekan organizasyon ekipleri

Temel ihtiyaçları:
- her etkinlik için görev listesi oluşturmak
- ekip ve dış tedarikçi atamak
- gün akışını planlamak
- müşteriden onay almak
- çiçekçi, fotoğrafçı, müzik, pasta gibi tedarikçileri yönetmek
- WhatsApp üzerinden hızlı teyit almak
- etkinlik günü operasyonu kontrol etmek

### 3.3 Üst Segment Hedef

Çok salonlu mekanlar, oteller ve büyük davet merkezleri.

Temel ihtiyaçları:
- çoklu salon takvimi
- çoklu kullanıcı ve yetki
- danışman performansı
- merkezi raporlama
- yüksek hacimli rezervasyon yönetimi
- departmanlar arası koordinasyon
- gelişmiş operasyon takibi

## 4. Ürün Yapısı

Eventra iki ana eksenden oluşur:

### 4.1 Venue Ekseni

Salon/mekan merkezli kullanım.

Ana akış:

1. Müşteri adayı gelir.
2. CRM’e kaydedilir.
3. Tarih ve salon kontrol edilir.
4. Teklif oluşturulur.
5. Ön rezervasyon yapılır.
6. Kapora alınır.
7. Rezervasyon kesinleşir.
8. Sözleşme üretilir.
9. Müşteri portalı üzerinden bilgiler tamamlanır.
10. Etkinlik yaklaşırken hatırlatmalar gider.
11. Etkinlik tamamlanır.
12. Ödeme ve kapanış yapılır.

### 4.2 Flow Ekseni

Organizasyon operasyonu merkezli kullanım.

Ana akış:

1. Yeni event workspace oluşturulur.
2. Organizasyon türü seçilir.
3. Hazır şablondan görevler oluşturulur.
4. Timeline çıkarılır.
5. Ekip rolleri atanır.
6. Dış tedarikçiler eklenir.
7. WhatsApp/SMS ile teyitler gönderilir.
8. Müşteri onayları alınır.
9. Etkinlik günü operasyon ekranı kullanılır.
10. Etkinlik sonrası kontrol ve kapanış yapılır.

## 5. URL ve Tenant Yapısı

Başlangıç domain yapısı:

- `eventra.global-minima.com`
- `app.eventra.global-minima.com`
- `api.eventra.global-minima.com`

İleride ayrı domain alınırsa:

- `eventra.app`
- `eventra.com.tr`
- `eventra.io`

Önerilen URL yapısı:

```text
app.eventra.global-minima.com/login
app.eventra.global-minima.com/o/{organization_slug}/dashboard
app.eventra.global-minima.com/o/{organization_slug}/calendar
app.eventra.global-minima.com/o/{organization_slug}/reservations
app.eventra.global-minima.com/o/{organization_slug}/customers
app.eventra.global-minima.com/o/{organization_slug}/events
app.eventra.global-minima.com/o/{organization_slug}/finance
app.eventra.global-minima.com/o/{organization_slug}/settings
```

Müşteri portalı URL yapısı:

```text
portal.eventra.global-minima.com/{organization_slug}/{access_token}
```

veya daha temiz:

```text
eventra.global-minima.com/p/{organization_slug}/{access_token}
```

Örnek:

```text
eventra.global-minima.com/p/inci-davet/X7K2Q9
```

Public teklif/sözleşme görüntüleme:

```text
eventra.global-minima.com/doc/{public_document_token}
```

Tedarikçi teyit linki:

```text
eventra.global-minima.com/c/{confirmation_token}
```

## 6. Paketler

## 6.1 Eventra Core

Hedef:

Tek salonlu ve temel takibe ihtiyacı olan düğün/davet salonları.

Tahmini fiyat:

**8.900 TL / yıl lansman fiyatı**

Normal fiyat hedefi:

**11.900 TL / yıl**

Dahil:

- 1 işletme
- 1 salon
- 2 kullanıcı
- takvim
- rezervasyon yönetimi
- müşteri kaydı
- kapora ve kalan ödeme takibi
- menü/paket tanımları
- basit sözleşme çıktısı
- temel raporlar
- Excel dışa aktarım
- temel WhatsApp/SMS mesaj şablonları

Amaç:

Eski salon programlarının direkt yerine geçmek.

## 6.2 Eventra Pro

Hedef:

Daha profesyonel çalışan salonlar, kır bahçeleri ve davet merkezleri.

Tahmini fiyat:

**14.900 TL / yıl**

Dahil:

- Core’daki her şey
- 2 salon
- 5 kullanıcı
- CRM pipeline
- müşteri portalı
- Word şablondan PDF sözleşme
- teklif yönetimi
- ödeme hatırlatmaları
- gelişmiş raporlar
- veri taşıma desteği
- danışman/satış temsilcisi takibi

Amaç:

Asıl satılması istenen ana paket.

## 6.3 Eventra Flow

Hedef:

Organizasyon şirketleri ve operasyonu karmaşık olan salonlar.

Bağımsız fiyat:

**14.900 TL / yıl**

Pro üstüne ek modül:

**+12.000 TL / yıl**

Dahil:

- event workspace
- görev panosu
- organizasyon şablonları
- timeline
- ekip ve rol atama
- tedarikçi yönetimi
- WhatsApp teyit akışı
- müşteri onay görevleri
- etkinlik günü operasyon ekranı
- etkinlik sonrası kapanış listesi

Amaç:

Trello/Confluence benzeri genel araçları organizasyon sektörüne özel hale getirmek.

## 6.4 Eventra Suite

Hedef:

Çok salonlu işletmeler, oteller, büyük davet merkezleri ve zincir yapılar.

Başlangıç fiyatı:

**24.900 TL / yıl**

Dahil:

- Pro + Flow
- 3 salon
- 8 kullanıcı
- gelişmiş yetkilendirme
- yönetici dashboard
- çoklu salon raporları
- danışman performans raporu
- detaylı finans raporu
- öncelikli destek
- kurulum ve eğitim desteği

Ek ücretler:

| Kalem | Fiyat |
|---|---:|
| Ek salon | 3.000–5.000 TL / yıl |
| Ek kullanıcı | 1.000–1.500 TL / yıl |
| Kurulum ve eğitim | 3.000–7.500 TL tek sefer |
| Veri taşıma | 2.500–10.000 TL |
| WhatsApp/SMS | sağlayıcı maliyeti ayrı |
| Özel entegrasyon | teklif usulü |

## 7. Modül Detayları

# 7.1 Venue Modülü

Venue modülü salon, mekan, takvim ve rezervasyon yönetiminin merkezidir.

## Ana Ekranlar

- Dashboard
- Takvim
- Rezervasyonlar
- Salonlar
- Organizasyon türleri
- Menü ve paketler
- Rezervasyon detay sayfası

## Takvim Özellikleri

- günlük görünüm
- haftalık görünüm
- aylık görünüm
- yıllık görünüm
- salon bazlı filtre
- durum bazlı filtre
- sürükle-bırak tarih değiştirme
- çakışma kontrolü
- ön rezervasyon süresi
- kesin rezervasyon
- iptal
- tamamlandı
- ödeme bekleniyor
- kapora alındı
- yaklaşan etkinlikler
- renkli durum göstergeleri

## Rezervasyon Alanları

Genel bilgiler:

- organizasyon tarihi
- başlangıç saati
- bitiş saati
- salon
- organizasyon türü
- rezervasyon durumu
- sözleşme tarihi
- sözleşme numarası
- satış temsilcisi
- açıklama

Müşteri bilgileri:

- ad soyad
- telefon
- ikinci telefon
- e-posta
- adres
- T.C. kimlik no
- yakın kişi
- müşteri notu

Etkinlik bilgileri:

- gelin/damat bilgisi
- davetli sayısı
- çocuk davetli sayısı
- masa düzeni
- menü
- paket
- özel istekler
- iç notlar

Finans bilgileri:

- toplam ücret
- indirim
- kapora
- alınan ödeme
- kalan ödeme
- ödeme yöntemi
- taksit planı
- ödeme notları

## 7.2 CRM Modülü

CRM modülü müşteri adaylarını, satış görüşmelerini ve teklif sürecini yönetir.

## Ana Ekranlar

- Lead listesi
- Pipeline board
- Müşteri detay sayfası
- Görüşme geçmişi
- Teklifler
- Kaybedilen müşteriler
- Hatırlatmalar

## Pipeline Aşamaları

- Yeni talep
- Aranacak
- Görüşme planlandı
- Teklif gönderildi
- Ön rezervasyon
- Kapora bekleniyor
- Kesin rezervasyon
- Kaybedildi
- İptal

## CRM Alanları

- müşteri adı
- telefon
- e-posta
- talep edilen tarih
- talep edilen salon
- tahmini davetli sayısı
- bütçe
- kaynak
- ilgilenen temsilci
- son görüşme tarihi
- sonraki aksiyon
- kaybedilme sebebi

## CRM Otomasyonları

- yeni müşteri adayı geldiğinde görev oluşturma
- teklif sonrası hatırlatma
- opsiyon süresi dolmadan uyarı
- kapora bekleyen müşteri uyarısı
- kaybedilen müşteri sebebi raporu

## 7.3 Portal Modülü

Portal modülü müşterinin kendi bilgilerini doldurmasını sağlar.

## Portal Akışı

1. Salon çalışanı rezervasyon veya teklif oluşturur.
2. Sistem müşteriye özel güvenli link üretir.
3. Link WhatsApp/SMS/e-posta ile gönderilir.
4. Müşteri sayfaya girer.
5. Gerekirse SMS koduyla doğrulama yapar.
6. Kendi bilgilerini tamamlar.
7. Menü, davetli sayısı ve özel istekleri girer.
8. Belgeleri görüntüler.
9. Onay gereken alanları onaylar.
10. Salon panelinde bilgiler otomatik güncellenir.

## Portal Sayfaları

- müşteri giriş sayfası
- bilgi formu
- organizasyon detayları
- menü seçimi
- özel istekler
- ödeme planı
- sözleşmeler ve belgeler
- onaylar
- iletişim

## Portal Güvenliği

- tahmin edilemeyen access token
- link süre sınırı
- isteğe bağlı SMS doğrulama
- müşteri tarafında sınırlı veri görünümü
- her değişiklik için audit log
- belge görüntüleme logu

## Portalda Olacak Alanlar

- müşteri adı
- telefon
- e-posta
- gelin/damat bilgileri
- davetli sayısı
- özel istekler
- menü tercihi
- masa düzeni notları
- müzik notları
- giriş saati
- fotoğraf/video notları
- ödeme planı görüntüleme
- sözleşme görüntüleme

## 7.4 Docs Modülü

Docs modülü sözleşme, teklif, makbuz ve operasyon belgelerini otomatik üretir.

## Temel Mantık

Firma Word şablonu yükler. Şablon içerisinde değişken alanlar bulunur.

Örnek değişkenler:

```text
{{customer.full_name}}
{{event.date}}
{{event.start_time}}
{{venue.name}}
{{reservation.contract_no}}
{{finance.total_amount}}
{{finance.deposit_amount}}
{{finance.remaining_amount}}
{{event.guest_count}}
{{package.name}}
```

Sistem bu şablonu doldurur ve PDF üretir.

## Belge Türleri

- sözleşme
- teklif
- ödeme planı
- kapora makbuzu
- tahsilat makbuzu
- organizasyon bilgi formu
- menü formu
- gün akış planı
- tedarikçi görev formu

## Özellikler

- Word şablonu yükleme
- şablon önizleme
- değişken listesi
- otomatik PDF üretimi
- belge indirme
- müşteriye linkle gönderme
- WhatsApp/SMS ile paylaşma
- belge revizyon geçmişi
- belge görüntüleme geçmişi

## 7.5 Finance Modülü

Finance modülü salon içi tahsilat, kapora, taksit ve kasa takibini yönetir.

## Ana Ekranlar

- Kasa
- Ödemeler
- Taksitler
- Geciken ödemeler
- Rezervasyon finans detayı
- Gelir raporları
- Giderler
- Gün sonu raporu

## Özellikler

- kapora kaydı
- kısmi ödeme
- kalan bakiye
- taksit planı
- ödeme yöntemi
- nakit/kart/havale ayrımı
- günlük kasa
- tarih bazlı gelir
- salon bazlı gelir
- iptal/iade
- gider kaydı
- ödeme hatırlatmaları
- PDF/Excel rapor

## İlk Aşamada Yapılmayacaklar

- tam muhasebe
- e-fatura
- banka entegrasyonu
- stok muhasebesi
- vergi beyannamesi
- resmi muhasebe fişleri

## 7.6 Flow Modülü

Flow modülü organizasyon operasyonunun merkezidir.

## Ana Ekranlar

- Event workspace
- Görev panosu
- Timeline
- Ekip ve roller
- Tedarikçiler
- Dosyalar
- Müşteri onayları
- Gün içi operasyon ekranı
- Kapanış listesi

## Event Workspace

Her organizasyon için ayrı bir çalışma alanı oluşturulur.

İçerik:

- genel bilgiler
- müşteri bilgileri
- görevler
- timeline
- sorumlular
- tedarikçiler
- belgeler
- notlar
- operasyon durumu

## Görev Panosu

Varsayılan kolonlar:

- Yapılacak
- Devam ediyor
- Müşteri onayı bekliyor
- Tedarikçide
- Sorun var
- Tamamlandı

Görev kartı alanları:

- başlık
- açıklama
- sorumlu kişi
- rol
- son tarih
- öncelik
- müşteri onayı gerekiyor mu
- tedarikçi bağlantısı
- maliyet
- dosyalar
- yorumlar
- durum geçmişi

## Timeline

Etkinlik günü akış planı.

Örnek:

| Saat | Aksiyon | Sorumlu |
|---:|---|---|
| 17:00 | Salon hazırlık kontrolü | Salon şefi |
| 18:00 | Fotoğraf ekibi gelişi | Organizasyon sorumlusu |
| 19:30 | Misafir kabul | Karşılama ekibi |
| 20:30 | Gelin-damat giriş | DJ / organizasyon |
| 21:00 | Yemek servisi | Servis şefi |
| 22:00 | Pasta | Servis |
| 23:30 | Final kontrol | Organizasyon sorumlusu |

Timeline özellikleri:

- saat bazlı planlama
- sorumlu atama
- kritik aksiyon işaretleme
- çıktı alma
- müşteriye sınırlı görünüm
- ekip içi görünüm
- PDF gün akış planı

## Organizasyon Şablonları

Hazır şablonlar:

- düğün
- kına
- nişan
- sünnet
- kurumsal toplantı
- açılış
- gala
- kokteyl
- mezuniyet
- otel etkinliği

Her şablon:
- varsayılan görevler
- varsayılan timeline
- gerekli roller
- önerilen tedarikçi kategorileri
- kontrol listeleri içerir.

## Tedarikçi Yönetimi

Tedarikçi kategorileri:

- çiçekçi
- fotoğrafçı
- video ekibi
- pasta
- süsleme
- müzik
- DJ
- orkestra
- ışık/ses
- vale
- catering
- araç
- güvenlik

Tedarikçi alanları:

- firma adı
- kişi adı
- telefon
- e-posta
- kategori
- fiyat notları
- çalışma geçmişi
- performans notu
- uygunluk durumu
- son iletişim tarihi

## WhatsApp/SMS Teyit Akışı

İlk sürümde:

- mesaj şablonu oluşturma
- tedarikçiye tek tıkla mesaj gönderme
- teyit linki
- kabul/reddet butonu
- durumun sistemde güncellenmesi

İleri sürümde:

- WhatsApp Business API entegrasyonu
- EVET/HAYIR cevap algılama
- otomatik görev durumu güncelleme
- çoklu tedarikçiye fiyat isteme
- gelen cevaplara göre karşılaştırma ekranı

## 7.7 Admin Modülü

Admin modülü işletme, kullanıcı, yetki, paket ve sistem ayarlarını yönetir.

## Ana Ekranlar

- işletme ayarları
- salonlar
- kullanıcılar
- roller
- yetkiler
- paket ve abonelik
- belge şablonları
- mesaj şablonları
- entegrasyonlar
- audit log

## Roller

Varsayılan roller:

- işletme sahibi
- yönetici
- satış temsilcisi
- organizasyon sorumlusu
- kasa yetkilisi
- salon personeli
- dış tedarikçi
- sadece görüntüleyici

## Yetki Örnekleri

- rezervasyon görüntüleme
- rezervasyon oluşturma
- rezervasyon silme
- fiyat görme
- ödeme ekleme
- sözleşme oluşturma
- müşteri bilgisi düzenleme
- rapor görüntüleme
- kullanıcı yönetme
- portal linki oluşturma

## 8. Versiyon Planı

# 8.1 MVP / Pilot Sürüm

Hedef süre:

**2–4 hafta demo/pilot**

Kapsam:

- login
- işletme oluşturma
- kullanıcı rolleri
- salon tanımlama
- takvim
- rezervasyon oluşturma
- müşteri kaydı
- ödeme/kapora/kalan bakiye
- menü/paket tanımı
- sözleşme numarası
- basit PDF çıktısı
- temel CRM durumu
- Excel dışa aktarım
- dashboard
- manuel WhatsApp mesaj linki

Amaç:

İlk salonlara gösterilebilir ve pilot müşteride kullanılabilir seviye.

# 8.2 V1 — Satılabilir Core

Kapsam:

- sağlam takvim
- çakışma kontrolü
- ön rezervasyon/kesin rezervasyon
- gelişmiş rezervasyon formu
- müşteri detay sayfası
- ödeme/taksit planı
- Word şablondan PDF
- temel müşteri portalı
- temel raporlar
- yedekleme
- audit log
- kullanıcı yetkileri
- veri taşıma

Amaç:

SYS ve benzeri sistemlerin yerine satılabilir ürün.

# 8.3 V1.5 — Pro

Kapsam:

- CRM pipeline
- teklif yönetimi
- müşteri portalı gelişmiş formlar
- ödeme hatırlatma
- belge revizyonları
- gelişmiş raporlar
- danışman performansı
- çoklu salon
- mesaj şablonları

Amaç:

Daha yüksek fiyatlı ana paketi satmak.

# 8.4 V2 — Flow

Kapsam:

- event workspace
- görev panosu
- timeline
- organizasyon şablonları
- rol atama
- tedarikçi yönetimi
- teyit linkleri
- gün içi operasyon ekranı
- operasyon sonrası kapanış

Amaç:

Organizasyon şirketlerine bağımsız satış ve salonlara ek modül satışı.

# 8.5 V3 — Otomasyon ve AI

Kapsam:

- WhatsApp Business API
- otomatik cevap algılama
- AI destekli müşteri form doldurma
- AI destekli organizasyon plan önerisi
- AI destekli sözleşme kontrolü
- tedarikçi teklif karşılaştırma
- doğal dille rapor sorma
- akıllı risk uyarıları

Amaç:

Ürünü piyasadaki eski yazılımlardan net şekilde ayırmak.

## 9. Satış Stratejisi

## 9.1 Ana Satış Cümlesi

> **Eventra, düğün salonları ve organizasyon firmaları için rezervasyon, müşteri, sözleşme, ödeme ve organizasyon akışını tek sistemde yöneten modern platformdur.**

## 9.2 SYS Benzeri Program Kullananlara Satış

Vurgu:

- mevcut alışkanlıklarını tamamen bozmaz
- takvim ve rezervasyon mantığını korur
- daha modern ve hızlıdır
- bulut tabanlıdır
- müşteri bilgilerini müşteri kendisi doldurabilir
- sözleşmeler otomatik çıkar
- ödeme ve kapora takibi daha nettir
- eski veriler taşınabilir
- telefondan erişilebilir

Kullanılacak teklif:

> **Eski salon programınızdan Eventra’ya geçiş kampanyası: 8.900 TL / yıl**

## 9.3 Yeni veya Düzensiz Takip Yapan Salonlara Satış

Vurgu:

- defter/Excel/WhatsApp dağınıklığını bitirir
- rezervasyon çakışmasını engeller
- ödeme kaçırmayı azaltır
- müşteri bilgilerini düzenler
- sözleşme ve belge üretimini hızlandırır
- çalışanların aynı sistemden görmesini sağlar

Satış cümlesi:

> **Salonunuzun rezervasyon defteri, müşteri listesi, ödeme takibi ve sözleşmeleri tek yerde dursun.**

## 9.4 Organizasyon Şirketlerine Satış

Vurgu:

- Trello gibi genel araçlardan daha sektöre özel
- event bazlı workspace
- timeline
- görev ve rol atama
- tedarikçi teyidi
- WhatsApp akışları
- etkinlik günü operasyon ekranı

Satış cümlesi:

> **Her organizasyon için görevleri, ekibi, tedarikçileri ve gün akışını tek çalışma alanında yönetin.**

## 9.5 Büyük İşletmelere Satış

Vurgu:

- çoklu salon
- çoklu kullanıcı
- yetki sistemi
- yönetici dashboard
- gelir ve doluluk raporları
- danışman performansı
- operasyon standardizasyonu

Satış cümlesi:

> **Birden fazla salonu, ekibi ve operasyonu merkezi olarak yönetin.**

## 10. Demo Stratejisi

İlk demo akışı:

1. Dashboard açılır.
2. Yıllık/aylık takvim gösterilir.
3. Boş tarih seçilir.
4. Yeni rezervasyon oluşturulur.
5. Müşteri bilgisi girilir.
6. Kapora eklenir.
7. Sözleşme PDF üretilir.
8. Müşteri portal linki oluşturulur.
9. Müşteri formu gösterilir.
10. Rezervasyon kesinleşir.
11. Organizasyon workspace oluşturulur.
12. Timeline ve görevler gösterilir.
13. Tedarikçi teyit linki gösterilir.
14. Rapor ekranı gösterilir.

Demo için örnek işletme:

**İnci Davet**

Demo için örnek organizasyon:

**08.06.2026 — Ahmet & Elif Düğünü**

## 11. Teknik Mimari

## 11.1 Önerilen Stack

Frontend:

- SvelteKit
- TypeScript
- Tailwind CSS
- shadcn-svelte veya benzeri component yaklaşımı
- FullCalendar veya özel calendar component
- TanStack Table benzeri güçlü tablo yapısı

Backend:

- FastAPI
- Python
- SQLAlchemy veya SQLModel
- Alembic
- Pydantic
- JWT/session tabanlı auth
- Celery/RQ/Arq benzeri background job sistemi

Database:

- PostgreSQL

Cache / Queue:

- Redis

Dosya depolama:

- başlangıçta local/S3 uyumlu storage
- ileride S3, Cloudflare R2 veya MinIO

PDF/Belge:

- DOCX template engine
- LibreOffice headless veya benzeri converter
- PDF generation service
- HTML to PDF alternatifi: Playwright/WeasyPrint

Deployment:

- Docker Compose başlangıç
- Nginx/Caddy reverse proxy
- PostgreSQL managed veya VPS
- düzenli backup
- staging/prod ayrımı

## 11.2 Mimari Prensipler

- multi-tenant yapı
- organization_id her ana tabloda bulunmalı
- soft delete
- audit log
- role-based access control
- modül bazlı feature flag
- paket bazlı limitler
- background jobs
- dosya erişiminde signed URL
- portal erişiminde token bazlı güvenlik
- ödeme ve sözleşme işlemlerinde log zorunlu

## 11.3 Ana Backend Modülleri

```text
app/
  api/
    auth/
    organizations/
    users/
    venues/
    reservations/
    customers/
    crm/
    finance/
    documents/
    portal/
    flow/
    suppliers/
    reports/
    admin/
  core/
    config.py
    security.py
    permissions.py
    tenant.py
  models/
  schemas/
  services/
  repositories/
  jobs/
  templates/
  integrations/
```

## 11.4 Ana Veri Modelleri

Temel modeller:

- Organization
- User
- Role
- Permission
- Venue
- Hall
- Customer
- Lead
- Reservation
- ReservationStatus
- EventType
- Package
- Menu
- Payment
- PaymentPlan
- DocumentTemplate
- GeneratedDocument
- PortalAccess
- EventWorkspace
- Task
- TaskStatus
- TimelineItem
- Supplier
- SupplierCategory
- SupplierConfirmation
- MessageTemplate
- AuditLog
- SubscriptionPlan
- FeatureFlag

## 11.5 Multi-Tenant Yapı

Her işletme bir `Organization` olarak tutulur.

Her ana kayıt `organization_id` taşır.

Kullanıcı bir veya birden fazla organization’a bağlı olabilir.

Paket limitleri organization seviyesinde kontrol edilir:

- salon limiti
- kullanıcı limiti
- belge şablonu limiti
- portal aktif/pasif
- flow aktif/pasif
- rapor seviyesi
- SMS/WhatsApp entegrasyonu
- depolama limiti

## 11.6 Güvenlik

Zorunlu güvenlik konuları:

- şifre hashleme
- JWT/session güvenliği
- rate limit
- audit log
- yetki kontrolü
- portal token süresi
- belge erişim tokenı
- veri yedekleme
- kullanıcı işlem geçmişi
- kritik finans işlemlerinde silme yerine iptal kaydı
- müşteri kişisel verilerinde minimum veri politikası

## 11.7 Background Job İhtiyaçları

- yaklaşan rezervasyon hatırlatma
- ödeme tarihi hatırlatma
- opsiyon süresi dolan rezervasyon uyarısı
- PDF üretimi
- Word to PDF conversion
- WhatsApp/SMS gönderimi
- e-posta gönderimi
- backup
- rapor üretimi
- portal link süresi kontrolü

## 11.8 Entegrasyonlar

İlk aşama:

- WhatsApp deep link
- SMS sağlayıcısı
- e-posta SMTP
- PDF üretim

İleri aşama:

- WhatsApp Business API
- sanal POS
- Google Calendar / Outlook Calendar
- e-imza
- e-fatura
- muhasebe yazılımı entegrasyonu
- Instagram lead entegrasyonu

## 12. UI/UX Prensipleri

## 12.1 Genel Stil

- modern web uygulaması hissi
- hızlı açılan ekranlar
- masaüstü ve tablet odaklı
- mobilde operasyon ekranları güçlü
- az tıklama
- belirgin durum renkleri
- arama ve filtreler güçlü
- gereksiz süsleme yok
- salon çalışanı için sade
- yönetici için rapor odaklı

## 12.2 Kritik Ekranlar

Öncelikli tasarlanacak ekranlar:

1. Dashboard
2. Takvim
3. Rezervasyon detay
4. Yeni rezervasyon formu
5. Müşteri detay
6. CRM pipeline
7. Müşteri portalı
8. Sözleşme oluşturma
9. Ödeme ekranı
10. Event workspace
11. Timeline
12. Görev panosu

## 12.3 Dashboard

Dashboard kartları:

- bugünkü organizasyonlar
- yaklaşan organizasyonlar
- kapora bekleyenler
- ödeme tarihi yaklaşanlar
- bu ayki rezervasyon sayısı
- bu ayki tahmini gelir
- salon doluluk oranı
- görev gecikmeleri
- müşteri dönüş bekleyenler

## 12.4 Takvim

Takvimde gösterilecekler:

- salon adı
- müşteri adı
- organizasyon türü
- saat aralığı
- durum rengi
- ödeme durumu ikonu
- ön rezervasyon işareti
- yaklaşan uyarı
- hızlı aksiyon menüsü

## 13. Uygulama Önceliği

İlk yapılacaklar:

1. Organization/User/Auth
2. Venue/Hall modeli
3. Customer modeli
4. Reservation modeli
5. Calendar UI
6. Reservation form
7. Payment modeli
8. Package/Menu modeli
9. PDF çıktısı
10. Portal access token
11. Portal form
12. Basic CRM status
13. Dashboard
14. Excel import/export
15. Audit log
16. Deployment

Sonra:

1. Word template sistemi
2. gelişmiş CRM pipeline
3. gelişmiş raporlar
4. Flow workspace
5. görev panosu
6. timeline
7. supplier management
8. WhatsApp teyit linkleri
9. gelişmiş portal onayları
10. AI/otomasyon

## 14. Satış Kanalları

İlk satış kanalları:

- tanıdık salon sahipleri
- Bursa ve çevre illerde doğrudan ziyaret
- telefonla randevu
- WhatsApp demo videosu
- kartvizit
- kısa landing page
- Google arama reklamı
- “düğün salonu programı” SEO sayfası
- eski programdan geçiş kampanyası

## 15. Landing Page İçeriği

Başlık:

> **Düğün salonunuzun rezervasyon, müşteri, sözleşme ve ödeme takibini tek sistemde yönetin.**

Alt başlık:

> **Eventra; düğün salonları, davet mekanları ve organizasyon firmaları için modern yönetim platformudur.**

Bölümler:

- Takvim ve rezervasyon
- Müşteri portalı
- Sözleşme ve belge otomasyonu
- Kapora ve ödeme takibi
- Organizasyon görevleri
- Tedarikçi yönetimi
- Raporlama
- Paketler
- Demo talep formu

CTA:

- Demo İste
- Geçiş Kampanyasını Gör
- WhatsApp’tan Yaz

## 16. İlk Müşteri Teklifi

İlk 10 müşteri için teklif:

**Eventra Pro — 8.900 TL / yıl**

Dahil:
- kurulum
- temel eğitim
- eski Excel/SYS verisi aktarımı
- 1 yıl kullanım
- 2 salon
- 5 kullanıcı
- müşteri portalı
- sözleşme şablonu kurulumu

Not:

Bu fiyat kalıcı liste fiyatı olarak değil, erken müşteri/pilot kampanyası olarak sunulacak.

## 17. Kritik Ürün Fikirleri

## 17.1 Müşteri Bilgi Toplama Linki

Salon çalışanı tüm bilgileri telefonda almak zorunda kalmamalı.

Müşteri link üzerinden bilgileri doldurur.

Sistem eksik alanları gösterir:

- telefon eksik
- davetli sayısı eksik
- menü seçilmedi
- ödeme planı onaylanmadı
- özel istek girilmedi
- sözleşme görüntülenmedi

## 17.2 Sözleşme Şablon Kütüphanesi

Her salon kendi sözleşmesini yükleyebilir.

Ayrıca sistem örnek şablon verebilir:

- düğün sözleşmesi
- kına sözleşmesi
- nişan sözleşmesi
- kurumsal etkinlik sözleşmesi
- kapora makbuzu
- ödeme planı

## 17.3 Rezervasyon Risk Uyarıları

Sistem riskli kayıtları işaretler:

- kapora alınmamış kesin rezervasyon
- sözleşmesi oluşturulmamış rezervasyon
- müşteri bilgileri eksik
- ödeme tarihi geçmiş
- aynı güne yakın saatli çakışma
- davetli sayısı netleşmemiş
- etkinliğe az kaldı ama menü seçilmemiş

## 17.4 Event Checklist

Her organizasyon türü için otomatik kontrol listesi.

Örnek düğün checklist:

- sözleşme tamamlandı
- kapora alındı
- menü seçildi
- davetli sayısı netleşti
- masa düzeni alındı
- gelin/damat giriş saati netleşti
- müzik listesi alındı
- fotoğrafçı teyit edildi
- süsleme teyit edildi
- pasta teyit edildi
- final ödeme kontrol edildi

## 17.5 Tedarikçi Teyit Linki

Tedarikçiye uygulama hesabı açtırmadan teyit alınır.

Örnek mesaj:

> 08.06.2026 tarihinde İnci Davet organizasyonu için fotoğraf/video hizmeti uygun musunuz? Onaylamak için linke tıklayın.

Tedarikçi linkte:

- kabul ediyorum
- uygun değilim
- not ekle

Sistem görevi otomatik günceller.

## 18. Yapılmayacaklar

İlk aşamada yapılmayacaklar:

- pazar yeri
- e-market
- evlilik portalı
- sosyal ağ
- tam muhasebe
- stok/depo
- e-fatura
- karmaşık yapay zeka botu
- her müşteriye özel sınırsız geliştirme
- mobil native uygulama
- franchise yönetimi
- karmaşık BI ekranları

## 19. Kapanış Kararı

Ürün adı:

**Eventra**

Ana şirket kullanımı:

**Eventra by Global Minima**

İlk ürün hedefi:

**Düğün salonu ve davet mekanı rezervasyon/CRM sistemi**

Ana farklılaştırıcılar:

- modern takvim
- müşteri portalı
- Word şablondan sözleşme/PDF
- ödeme ve kapora takibi
- CRM pipeline
- organizasyon Flow modülü
- tedarikçi teyitleri
- etkinlik günü operasyon ekranı

İlk satılacak paket:

**Eventra Pro**

İlk satış kampanyası:

**8.900 TL / yıl erken müşteri geçiş kampanyası**

Uzun vadeli ana ürün:

**Eventra Suite**
