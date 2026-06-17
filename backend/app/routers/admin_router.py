import smtplib
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.deps import get_current_admin
from ..core.security import create_access_token, hash_password
from ..database import get_db
from ..models import (
    AdminNotification,
    AdminSettings,
    AdminUser,
    ContractTemplate,
    Customer,
    CustomerFieldDef,
    CustomerFieldValue,
    CustomerFormType,
    CustomerFormTypeField,
    Event,
    EventCustomField,
    EventFormFieldDef,
    EventLayoutReservation,
    EventNotificationSchedule,
    EventType,
    EventTypeFieldDef,
    Expense,
    GuestSeating,
    Notification,
    OrgTypeField,
    PaymentInstallment,
    PortalFormField,
    PortalFormSubmission,
    Salon,
    SalonNotificationTemplate,
    SalonUser,
    SupportTicket,
    VenueLayout,
    VenueTable,
)
from ..portal_uploads import delete_portal_salon_uploads
from ..schemas import (
    AdminBroadcastIn,
    AdminCreateIn,
    AdminNotificationOut,
    AdminSettingsIn,
    AdminSettingsOut,
    AdminTestMailIn,
    LoginIn,
    SalonCreateIn,
    SalonOut,
    SalonUpdateIn,
    SalonUserCreateIn,
    SalonUserOut,
    SupportTicketOut,
    SupportTicketUpdateIn,
    TokenOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])

DEFAULT_EVENT_TYPES = [
    ("Düğün", "#b45309"),
    ("Nişan", "#7c3aed"),
    ("Kına", "#be123c"),
    ("Kurumsal", "#0f766e"),
    ("Mezuniyet", "#2563eb"),
]


@router.post("/setup", response_model=TokenOut, summary="İlk admin hesabı oluştur")
def create_admin(body: AdminCreateIn, db: Session = Depends(get_db)):
    if body.admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Geçersiz admin sırrı")
    if db.query(AdminUser).count() > 0:
        raise HTTPException(status_code=403, detail="Admin hesabı zaten mevcut")
    if db.query(AdminUser).filter(AdminUser.email == body.email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")
    admin = AdminUser(email=body.email, hashed_password=hash_password(body.password))
    db.add(admin)
    db.commit()
    db.refresh(admin)
    token = create_access_token(admin.id, {"role": "admin"})
    return TokenOut(access_token=token, role="admin")


@router.post("/salons", response_model=SalonOut)
def create_salon(body: SalonCreateIn, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    if db.query(SalonUser).filter(SalonUser.email == body.owner_email).first():
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kayıtlı")

    salon_count = max(1, min(body.salon_count, 5))
    max_users = max(1, min(body.max_users, 5))

    # Auto-generate contract number: count all existing salons + 1
    existing_count = db.query(Salon).count()
    salon = Salon(
        name=body.name,
        company_name=body.company_name,
        address=body.address,
        city=body.city,
        postal_code=body.postal_code,
        phone=body.phone,
        website=body.website,
        currency=body.currency,
        vat_rate=body.vat_rate,
        contract_prefix=body.contract_prefix,
        contract_no=existing_count + 1,
        reminder_days=body.reminder_days,
        salon_count=salon_count,
        max_users=max_users,
        subscription_start=body.subscription_start,
        subscription_end=body.subscription_end,
        notification_email=body.notification_email,
        created_by_admin=admin.id,
    )
    db.add(salon)
    db.flush()

    # Create default event types
    dugun_type = None
    for name, color in DEFAULT_EVENT_TYPES:
        et = EventType(salon_id=salon.id, name=name, color=color)
        db.add(et)
        if name == "Düğün":
            dugun_type = et
    db.flush()
    if dugun_type:
        db.add(EventTypeFieldDef(
            salon_id=salon.id, event_type_id=dugun_type.id,
            key="gelin_damat", label="Gelin ve Damat", field_type="text", sort_order=0,
        ))

    # Create default salons/rooms according to the account limit.
    for i in range(1, salon_count + 1):
        db.add(VenueLayout(salon_id=salon.id, name=f"Salon {i}"))

    # Create owner user
    owner = SalonUser(
        salon_id=salon.id,
        email=body.owner_email,
        username=body.owner_username,
        hashed_password=hash_password(body.owner_password),
        role="owner",
    )
    db.add(owner)
    db.commit()
    db.refresh(salon)
    return salon


@router.get("/salons", response_model=list[SalonOut])
def list_salons(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    return db.query(Salon).order_by(Salon.created_at.desc()).all()


@router.get("/salons/{salon_id}", response_model=SalonOut)
def get_salon(salon_id: str, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon bulunamadı")
    return salon


@router.get("/salons/{salon_id}/users", response_model=list[SalonUserOut])
def list_salon_users(salon_id: str, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    return db.query(SalonUser).filter(SalonUser.salon_id == salon_id).all()


@router.post("/salons/{salon_id}/users", response_model=SalonUserOut)
def add_salon_user(
    salon_id: str,
    body: SalonUserCreateIn,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon bulunamadı")

    current_count = db.query(SalonUser).filter(SalonUser.salon_id == salon_id).count()
    if current_count >= salon.max_users:
        raise HTTPException(
            status_code=400,
            detail=f"Bu salon için maksimum kullanıcı sayısına ({salon.max_users}) ulaşıldı",
        )

    if db.query(SalonUser).filter(SalonUser.email == body.email).first():
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kayıtlı")

    user = SalonUser(
        salon_id=salon_id,
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/salons/{salon_id}/users/{user_id}", status_code=204)
def remove_salon_user(
    salon_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    user = db.query(SalonUser).filter(SalonUser.id == user_id, SalonUser.salon_id == salon_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    db.delete(user)
    db.commit()


# ─── Salon update from admin ──────────────────────────────────────────────────

@router.patch("/salons/{salon_id}", response_model=SalonOut)
def update_salon(
    salon_id: str,
    body: SalonUpdateIn,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon bulunamadı")
    for k, v in body.model_dump(exclude_none=True).items():
        if k in {"salon_count", "max_users"}:
            v = max(1, min(v, 5))
        setattr(salon, k, v)
    db.commit()
    db.refresh(salon)
    return salon


@router.delete("/salons/{salon_id}", status_code=204)
def delete_salon(salon_id: str, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon bulunamadı")

    event_ids = [row[0] for row in db.query(Event.id).filter(Event.salon_id == salon_id).all()]
    event_type_ids = [row[0] for row in db.query(EventType.id).filter(EventType.salon_id == salon_id).all()]
    layout_ids = [row[0] for row in db.query(VenueLayout.id).filter(VenueLayout.salon_id == salon_id).all()]
    table_ids = [row[0] for row in db.query(VenueTable.id).filter(VenueTable.layout_id.in_(layout_ids)).all()] if layout_ids else []
    customer_ids = [row[0] for row in db.query(Customer.id).filter(Customer.salon_id == salon_id).all()]
    customer_field_ids = [row[0] for row in db.query(CustomerFieldDef.id).filter(CustomerFieldDef.salon_id == salon_id).all()]
    form_type_ids = [row[0] for row in db.query(CustomerFormType.id).filter(CustomerFormType.salon_id == salon_id).all()]

    if event_ids:
        db.query(PortalFormSubmission).filter(PortalFormSubmission.event_id.in_(event_ids)).delete(synchronize_session=False)
        db.query(EventLayoutReservation).filter(EventLayoutReservation.event_id.in_(event_ids)).delete(synchronize_session=False)
        db.query(EventNotificationSchedule).filter(EventNotificationSchedule.event_id.in_(event_ids)).delete(synchronize_session=False)
        db.query(EventCustomField).filter(EventCustomField.event_id.in_(event_ids)).delete(synchronize_session=False)
        db.query(PaymentInstallment).filter(PaymentInstallment.event_id.in_(event_ids)).delete(synchronize_session=False)
        db.query(GuestSeating).filter(GuestSeating.event_id.in_(event_ids)).delete(synchronize_session=False)
        db.query(Expense).filter(Expense.event_id.in_(event_ids)).delete(synchronize_session=False)
        db.query(Notification).filter(Notification.event_id.in_(event_ids)).delete(synchronize_session=False)

    if table_ids:
        db.query(GuestSeating).filter(GuestSeating.table_id.in_(table_ids)).delete(synchronize_session=False)

    if customer_ids:
        db.query(CustomerFieldValue).filter(CustomerFieldValue.customer_id.in_(customer_ids)).delete(synchronize_session=False)

    if customer_field_ids:
        db.query(CustomerFieldValue).filter(CustomerFieldValue.field_def_id.in_(customer_field_ids)).delete(synchronize_session=False)

    if form_type_ids:
        db.query(CustomerFormTypeField).filter(CustomerFormTypeField.customer_form_type_id.in_(form_type_ids)).delete(synchronize_session=False)

    if event_type_ids:
        db.query(EventTypeFieldDef).filter(EventTypeFieldDef.event_type_id.in_(event_type_ids)).delete(synchronize_session=False)
        db.query(OrgTypeField).filter(OrgTypeField.event_type_id.in_(event_type_ids)).delete(synchronize_session=False)
        db.query(SalonNotificationTemplate).filter(SalonNotificationTemplate.event_type_id.in_(event_type_ids)).delete(synchronize_session=False)

    db.query(Event).filter(Event.salon_id == salon_id).delete(synchronize_session=False)
    db.query(SupportTicket).filter(SupportTicket.salon_id == salon_id).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.salon_id == salon_id).delete(synchronize_session=False)
    db.query(EventNotificationSchedule).filter(EventNotificationSchedule.salon_id == salon_id).delete(synchronize_session=False)
    db.query(SalonNotificationTemplate).filter(SalonNotificationTemplate.salon_id == salon_id).delete(synchronize_session=False)
    db.query(Expense).filter(Expense.salon_id == salon_id).delete(synchronize_session=False)
    db.query(ContractTemplate).filter(ContractTemplate.salon_id == salon_id).delete(synchronize_session=False)
    db.query(EventTypeFieldDef).filter(EventTypeFieldDef.salon_id == salon_id).delete(synchronize_session=False)
    db.query(EventFormFieldDef).filter(EventFormFieldDef.salon_id == salon_id).delete(synchronize_session=False)
    db.query(OrgTypeField).filter(OrgTypeField.salon_id == salon_id).delete(synchronize_session=False)
    db.query(PortalFormField).filter(PortalFormField.salon_id == salon_id).delete(synchronize_session=False)
    db.query(CustomerFieldDef).filter(CustomerFieldDef.salon_id == salon_id).delete(synchronize_session=False)
    db.query(CustomerFormType).filter(CustomerFormType.salon_id == salon_id).delete(synchronize_session=False)
    db.query(Customer).filter(Customer.salon_id == salon_id).delete(synchronize_session=False)
    db.query(VenueTable).filter(VenueTable.layout_id.in_(layout_ids)).delete(synchronize_session=False) if layout_ids else None
    db.query(VenueLayout).filter(VenueLayout.salon_id == salon_id).delete(synchronize_session=False)
    db.query(EventType).filter(EventType.salon_id == salon_id).delete(synchronize_session=False)
    db.query(SalonUser).filter(SalonUser.salon_id == salon_id).delete(synchronize_session=False)
    db.query(AdminNotification).filter(AdminNotification.salon_id == salon_id).update(
        {AdminNotification.salon_id: None},
        synchronize_session=False,
    )

    db.query(Salon).filter(Salon.id == salon_id).delete(synchronize_session=False)
    db.commit()
    delete_portal_salon_uploads(salon_id)


# ─── Admin settings ───────────────────────────────────────────────────────────

def _get_or_create_settings(admin: AdminUser, db: Session) -> AdminSettings:
    s = db.query(AdminSettings).filter(AdminSettings.admin_id == admin.id).first()
    if not s:
        s = AdminSettings(admin_id=admin.id)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.get("/settings", response_model=AdminSettingsOut)
def get_admin_settings(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return _get_or_create_settings(admin, db)


@router.patch("/settings", response_model=AdminSettingsOut)
def update_admin_settings(body: AdminSettingsIn, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    s = _get_or_create_settings(admin, db)
    for k, v in body.model_dump().items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


@router.post("/settings/test-mail")
def test_admin_mail(body: AdminTestMailIn, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    s = _get_or_create_settings(admin, db)
    if not s.smtp_host or not s.smtp_username or not s.smtp_password:
        raise HTTPException(status_code=400, detail="SMTP ayarları eksik")
    try:
        msg = MIMEText("Eventra admin panelinden test maili. SMTP ayarlarınız doğru çalışıyor.", "plain", "utf-8")
        msg["Subject"] = "Eventra – Test Maili"
        msg["From"] = s.smtp_from_email or s.smtp_username
        msg["To"] = body.to_email
        with smtplib.SMTP(s.smtp_host, s.smtp_port or 587, timeout=10) as server:
            if s.smtp_use_tls:
                server.starttls()
            server.login(s.smtp_username, s.smtp_password)
            server.send_message(msg)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Admin notifications ──────────────────────────────────────────────────────

@router.get("/notifications", response_model=list[AdminNotificationOut])
def list_admin_notifications(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return db.query(AdminNotification).order_by(AdminNotification.created_at.desc()).limit(200).all()


@router.get("/notifications/unread-count")
def admin_unread_count(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    count = db.query(AdminNotification).filter(AdminNotification.is_read == False).count()
    return {"count": count}


@router.post("/notifications/{notification_id}/read", response_model=AdminNotificationOut)
def mark_admin_notification_read(notification_id: str, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    n = db.query(AdminNotification).filter(AdminNotification.id == notification_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Bildirim bulunamadı")
    n.is_read = True
    db.commit()
    db.refresh(n)
    return n


@router.post("/notifications/read-all")
def mark_all_admin_notifications_read(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    db.query(AdminNotification).filter(AdminNotification.is_read == False).update({"is_read": True})
    db.commit()
    return {"ok": True}


# ─── Broadcast to users ───────────────────────────────────────────────────────

@router.post("/broadcast")
def broadcast(body: AdminBroadcastIn, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    from ..email_utils import send_email
    from ..models import Notification

    q = db.query(Salon)
    if body.salon_ids:
        q = q.filter(Salon.id.in_(body.salon_ids))
    salons = q.all()

    admin_cfg = _get_or_create_settings(admin, db)
    sent = 0
    for salon in salons:
        if body.send_notification:
            db.add(Notification(
                salon_id=salon.id,
                type="admin_broadcast",
                title=body.subject,
                message=body.body,
            ))
        if body.send_email:
            to = salon.notification_email or ""
            if to and admin_cfg.smtp_host:
                try:
                    msg = MIMEText(body.body, "plain", "utf-8")
                    msg["Subject"] = body.subject
                    msg["From"] = admin_cfg.smtp_from_email or admin_cfg.smtp_username
                    msg["To"] = to
                    with smtplib.SMTP(admin_cfg.smtp_host, admin_cfg.smtp_port or 587, timeout=10) as srv:
                        if admin_cfg.smtp_use_tls:
                            srv.starttls()
                        srv.login(admin_cfg.smtp_username, admin_cfg.smtp_password)
                        srv.send_message(msg)
                    sent += 1
                except Exception:
                    pass
    db.commit()
    return {"sent": sent, "total": len(salons)}


# ─── Support tickets (admin view) ─────────────────────────────────────────────

@router.get("/tickets", response_model=list[SupportTicketOut])
def list_tickets(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    from ..models import SupportTicket
    tickets = db.query(SupportTicket).order_by(SupportTicket.created_at.desc()).all()
    out = []
    for t in tickets:
        d = SupportTicketOut.model_validate(t)
        d.salon_name = t.salon.name if t.salon else ""
        out.append(d)
    return out


@router.patch("/tickets/{ticket_id}", response_model=SupportTicketOut)
def update_ticket(ticket_id: str, body: SupportTicketUpdateIn, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    from ..models import SupportTicket
    t = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket bulunamadı")
    if body.status:
        t.status = body.status
    db.commit()
    db.refresh(t)
    d = SupportTicketOut.model_validate(t)
    d.salon_name = t.salon.name if t.salon else ""
    return d
