import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..core.deps import get_current_user
from ..database import get_db
from ..email_utils import send_email
from ..models import Customer, Event, EventCustomField, EventLayoutReservation, EventType, PaymentInstallment, Salon, SalonUser, VenueLayout
from ..models import PortalFormSubmission
from ..notify import notify
from ..schemas import (
    EventCustomFieldIn,
    EventIn,
    EventLayoutReservationOut,
    EventOut,
    EventTypeIn,
    EventTypeOut,
    EventUpdate,
    PaymentInstallmentIn,
    PaymentInstallmentOut,
    PortalFormSubmissionOut,
    SendCustomerMailIn,
)

router = APIRouter(prefix="/events", tags=["events"])


def _sync_payment(event: Event) -> None:
    if event.total_fee > 0 and event.total_paid >= event.total_fee:
        event.payment_complete = True


def _build_event_out(event: Event) -> EventOut:
    data = EventOut.model_validate(event)
    data.reserved_layout_ids = [r.layout_id for r in (event.layout_reservations or [])]
    return data


def _sync_portal_token(event: Event) -> None:
    if event.portal_enabled and not event.portal_token:
        event.portal_token = str(uuid.uuid4())
    elif not event.portal_enabled:
        event.portal_token = None


def _sync_layout_reservations(event: Event, layout_ids: list[str], db: Session) -> None:
    db.query(EventLayoutReservation).filter(EventLayoutReservation.event_id == event.id).delete()
    db.flush()
    for lid in layout_ids:
        layout = db.query(VenueLayout).filter(VenueLayout.id == lid, VenueLayout.salon_id == event.salon_id).first()
        if layout:
            db.add(EventLayoutReservation(event_id=event.id, layout_id=lid))


def _validate_layouts(salon_id: str, layout_id: str | None, reserved_layout_ids: list[str], db: Session) -> None:
    ids = {lid for lid in ([layout_id] if layout_id else []) + reserved_layout_ids if lid}
    if not ids:
        return
    existing = {
        row[0]
        for row in db.query(VenueLayout.id)
        .filter(VenueLayout.salon_id == salon_id, VenueLayout.id.in_(ids))
        .all()
    }
    missing = ids - existing
    if missing:
        raise HTTPException(status_code=400, detail="Seçili salon geçersiz veya artık mevcut değil")


# ─── Event Types ─────────────────────────────────────────────────────────────

@router.get("/types", response_model=list[EventTypeOut])
def list_event_types(user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(EventType).filter(EventType.salon_id == user.salon_id).all()


@router.post("/types", response_model=EventTypeOut)
def create_event_type(body: EventTypeIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    et = EventType(salon_id=user.salon_id, **body.model_dump())
    db.add(et)
    db.commit()
    db.refresh(et)
    return et


@router.put("/types/{type_id}", response_model=EventTypeOut)
def update_event_type(
    type_id: str, body: EventTypeIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    et = db.query(EventType).filter(EventType.id == type_id, EventType.salon_id == user.salon_id).first()
    if not et:
        raise HTTPException(status_code=404, detail="Tip bulunamadı")
    et.name = body.name
    et.color = body.color
    db.commit()
    db.refresh(et)
    return et


@router.delete("/types/{type_id}", status_code=204)
def delete_event_type(type_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    et = db.query(EventType).filter(EventType.id == type_id, EventType.salon_id == user.salon_id).first()
    if not et:
        raise HTTPException(status_code=404, detail="Tip bulunamadı")
    db.delete(et)
    db.commit()


# ─── Events ──────────────────────────────────────────────────────────────────

@router.get("", response_model=list[EventOut])
def list_events(
    month: str | None = Query(None, description="YYYY-MM formatında filtre"),
    date: str | None = Query(None, description="YYYY-MM-DD formatında filtre"),
    appointment_no: int | None = Query(None, description="Randevu ID ile ara"),
    layout_id: str | None = Query(None, description="Salon (oda) id ile filtrele"),
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(Event)
        .options(
            joinedload(Event.event_type),
            joinedload(Event.custom_fields),
            joinedload(Event.layout_reservations),
        )
        .filter(Event.salon_id == user.salon_id)
    )
    if month:
        q = q.filter(Event.event_date.like(f"{month}%"))
    if date:
        q = q.filter(Event.event_date == date)
    if appointment_no is not None:
        q = q.filter(Event.appointment_no == appointment_no)
    if layout_id:
        q = q.filter(Event.layout_id == layout_id)
    return [_build_event_out(e) for e in q.order_by(Event.event_date).all()]


def _next_appointment_no(salon_id: str, db: Session) -> int:
    max_no = db.query(func.max(Event.appointment_no)).filter(Event.salon_id == salon_id).scalar()
    return (max_no or 0) + 1


@router.post("", response_model=EventOut)
def create_event(body: EventIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    data = body.model_dump(exclude={"custom_fields", "reserved_layout_ids"})
    _validate_layouts(user.salon_id, data.get("layout_id"), body.reserved_layout_ids, db)
    if not data.get("contract_date"):
        data["contract_date"] = datetime.utcnow().strftime("%Y-%m-%d")
    event = Event(salon_id=user.salon_id, **data)
    event.appointment_no = _next_appointment_no(user.salon_id, db)
    _sync_payment(event)
    _sync_portal_token(event)
    db.add(event)
    db.flush()
    for i, cf in enumerate(body.custom_fields):
        db.add(EventCustomField(event_id=event.id, **{**cf.model_dump(), 'sort_order': i}))
    _sync_layout_reservations(event, body.reserved_layout_ids, db)
    db.commit()
    db.refresh(event)
    return _build_event_out(event)


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    event = (
        db.query(Event)
        .options(
            joinedload(Event.event_type),
            joinedload(Event.custom_fields),
            joinedload(Event.layout_reservations),
        )
        .filter(Event.id == event_id, Event.salon_id == user.salon_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")
    return _build_event_out(event)


@router.patch("/{event_id}", response_model=EventOut)
def update_event(
    event_id: str, body: EventUpdate, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    event = (
        db.query(Event)
        .options(
            joinedload(Event.custom_fields),
            joinedload(Event.layout_reservations),
        )
        .filter(Event.id == event_id, Event.salon_id == user.salon_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")

    previous_status = event.reservation_status
    data = body.model_dump(exclude_none=True, exclude={"custom_fields", "reserved_layout_ids"})
    _validate_layouts(user.salon_id, data.get("layout_id", event.layout_id), body.reserved_layout_ids or [], db)
    for field, val in data.items():
        setattr(event, field, val)

    if event.reservation_status == "Kesin Rezervasyon" and previous_status != "Kesin Rezervasyon":
        event.contract_date = datetime.utcnow().strftime("%Y-%m-%d")

    _sync_payment(event)
    _sync_portal_token(event)

    if body.custom_fields is not None:
        for cf in event.custom_fields:
            db.delete(cf)
        db.flush()
        for i, cf in enumerate(body.custom_fields):
            db.add(EventCustomField(event_id=event.id, **{**cf.model_dump(), 'sort_order': i}))

    if body.reserved_layout_ids is not None:
        _sync_layout_reservations(event, body.reserved_layout_ids, db)

    db.commit()
    db.refresh(event)
    return _build_event_out(event)


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.salon_id == user.salon_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")
    db.delete(event)
    db.commit()


@router.get("/{event_id}/portal-submissions", response_model=list[PortalFormSubmissionOut])
def list_portal_submissions(event_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.salon_id == user.salon_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")
    return db.query(PortalFormSubmission).filter(PortalFormSubmission.event_id == event_id).order_by(PortalFormSubmission.submitted_at.desc()).all()


@router.get("/{event_id}/payments", response_model=list[PaymentInstallmentOut])
def list_payments(event_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.salon_id == user.salon_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")
    return (
        db.query(PaymentInstallment)
        .filter(PaymentInstallment.event_id == event_id)
        .order_by(PaymentInstallment.created_at)
        .all()
    )


@router.post("/{event_id}/payments", response_model=EventOut)
def add_payment(
    event_id: str, body: PaymentInstallmentIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    event = (
        db.query(Event)
        .options(joinedload(Event.custom_fields), joinedload(Event.layout_reservations))
        .filter(Event.id == event_id, Event.salon_id == user.salon_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Tutar sıfırdan büyük olmalı")

    db.add(PaymentInstallment(
        event_id=event.id, amount=body.amount, added_by_user_id=user.id, added_by_name=user.username,
    ))
    event.total_paid = (event.total_paid or 0) + body.amount
    _sync_payment(event)
    db.commit()
    db.refresh(event)
    return _build_event_out(event)


def _resolve_customer_email(event: Event, db: Session) -> str:
    if event.email:
        return event.email
    if event.customer_id:
        customer = db.query(Customer).filter(Customer.id == event.customer_id).first()
        if customer and customer.email:
            return customer.email
    return ""


# ─── Payment confirm & customer mail ──────────────────────────────────────────

@router.post("/{event_id}/confirm-payment", response_model=EventOut)
def confirm_payment(event_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    event = (
        db.query(Event)
        .options(joinedload(Event.custom_fields), joinedload(Event.layout_reservations))
        .filter(Event.id == event_id, Event.salon_id == user.salon_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")

    event.payment_complete = True
    db.commit()
    db.refresh(event)

    name = event.full_name or event.bride_groom or event.title or "Müşteri"
    appt = f"#{event.appointment_no}" if event.appointment_no else ""
    notify(db, user.salon_id, "payment_confirmed", "Ödeme onaylandı", f"{name} için randevu {appt} ödemesi onaylandı.", event_id=event.id)

    target_email = _resolve_customer_email(event, db)
    if target_email:
        salon = db.query(Salon).filter(Salon.id == user.salon_id).first()
        subject = "Ödemeniz Onaylandı"
        body = f"Merhaba {name},\n\nRandevu {appt} için ödemeniz onaylanmıştır. Teşekkür ederiz."
        ok, detail = send_email(salon, target_email, subject, body)
        if not ok:
            notify(db, user.salon_id, "email_failed", "Mail gönderilemedi", f"Ödeme onay maili gönderilemedi: {detail}", event_id=event.id)

    return _build_event_out(event)


@router.post("/send-mail")
def send_customer_mail(body: SendCustomerMailIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(Event).filter(
        Event.appointment_no == body.appointment_no, Event.salon_id == user.salon_id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Bu randevu numarasına ait davet bulunamadı")

    target_email = _resolve_customer_email(event, db)
    if not target_email:
        raise HTTPException(status_code=400, detail="Müşteri maili bulunamadı")

    salon = db.query(Salon).filter(Salon.id == user.salon_id).first()
    ok, detail = send_email(salon, target_email, body.subject, body.body)

    if ok:
        notify(db, user.salon_id, "email_sent", "Mail gönderildi", f"#{body.appointment_no} randevusuna mail gönderildi.", event_id=event.id)
        if salon and salon.notification_email:
            send_email(
                salon, salon.notification_email, "Eventra: Müşteriye mail gönderildi",
                f"#{body.appointment_no} numaralı randevuya '{body.subject}' konulu mail gönderildi."
            )
    else:
        notify(db, user.salon_id, "email_failed", "Mail gönderilemedi", f"#{body.appointment_no} randevusuna mail gönderilemedi: {detail}", event_id=event.id)
        if salon and salon.notification_email:
            send_email(
                salon, salon.notification_email, "Eventra: Mail gönderimi başarısız",
                f"#{body.appointment_no} numaralı randevuya mail gönderimi başarısız oldu: {detail}"
            )

    return {"ok": ok, "detail": detail}
