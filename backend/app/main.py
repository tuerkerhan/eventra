from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .core.config import settings as app_settings
from .database import engine, SessionLocal
from .models import Base, EventType, EventTypeFieldDef, Salon, VenueLayout
from .routers import auth, customers, events, venue, portal, settings, admin_router, expenses, contracts, event_form_fields
from .routers import customer_forms, notifications, event_type_fields

Base.metadata.create_all(bind=engine)

# Column migrations for existing tables
with engine.connect() as _conn:
    _conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS portal_form_type_id TEXT"))
    _conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS portal_title TEXT DEFAULT 'Davetiniz'"))
    _conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS appointment_no INTEGER"))
    _conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS customer_payment_claimed BOOLEAN DEFAULT FALSE"))
    _conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS payment_enabled BOOLEAN DEFAULT FALSE"))
    _conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS payment_bank_name TEXT DEFAULT ''"))
    _conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS payment_iban TEXT DEFAULT ''"))
    _conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS payment_account_holder TEXT DEFAULT ''"))
    _conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS payment_description TEXT DEFAULT ''"))
    _conn.execute(text("ALTER TABLE salons DROP COLUMN IF EXISTS sms_api_provider"))
    _conn.execute(text("ALTER TABLE salons DROP COLUMN IF EXISTS sms_api_key"))
    _conn.execute(text("ALTER TABLE salons DROP COLUMN IF EXISTS sms_api_username"))
    _conn.execute(text("ALTER TABLE salons DROP COLUMN IF EXISTS sms_sender_name"))
    _conn.execute(text("ALTER TABLE salons DROP COLUMN IF EXISTS sms_business_phone"))
    _conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS smtp_host TEXT DEFAULT ''"))
    _conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS smtp_port INTEGER DEFAULT 587"))
    _conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS smtp_username TEXT DEFAULT ''"))
    _conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS smtp_password TEXT DEFAULT ''"))
    _conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS smtp_from_email TEXT DEFAULT ''"))
    _conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS smtp_use_tls BOOLEAN DEFAULT TRUE"))
    _conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS notification_email TEXT DEFAULT ''"))
    _conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS email TEXT DEFAULT ''"))
    _conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS portal_message TEXT DEFAULT ''"))
    _conn.execute(text("ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_event_id_fkey"))
    _conn.execute(text(
        "ALTER TABLE notifications ADD CONSTRAINT notifications_event_id_fkey "
        "FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL"
    ))
    _conn.commit()

# Seed default salons (rooms) "Salon A/B/C" for any tenant that has none yet
with SessionLocal() as _db:
    for _salon in _db.query(Salon).all():
        _has_layouts = _db.query(VenueLayout).filter(VenueLayout.salon_id == _salon.id).first()
        if not _has_layouts:
            for _name in ("Salon A", "Salon B", "Salon C"):
                _db.add(VenueLayout(salon_id=_salon.id, name=_name))

        _dugun = _db.query(EventType).filter(EventType.salon_id == _salon.id, EventType.name == "Düğün").first()
        if _dugun:
            _has_field = _db.query(EventTypeFieldDef).filter(EventTypeFieldDef.event_type_id == _dugun.id).first()
            if not _has_field:
                _db.add(EventTypeFieldDef(
                    salon_id=_salon.id, event_type_id=_dugun.id,
                    key="gelin_damat", label="Gelin ve Damat", field_type="text", sort_order=0,
                ))
    _db.commit()

app = FastAPI(title="Eventra API", version="1.0.0", docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(events.router)
app.include_router(venue.router)
app.include_router(portal.router)
app.include_router(settings.router)
app.include_router(admin_router.router)
app.include_router(expenses.router)
app.include_router(contracts.router)
app.include_router(event_form_fields.router)
app.include_router(customer_forms.router)
app.include_router(notifications.router)
app.include_router(event_type_fields.router)


@app.get("/health")
def health():
    return {"status": "ok"}
