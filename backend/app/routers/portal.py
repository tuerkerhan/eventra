from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..email_utils import send_email
from ..models import CustomerFormTypeField, Event, GuestSeating, OrgTypeField, PortalFormSubmission, Salon, VenueLayout, VenueTable
from ..notify import notify
from ..schemas import (
    GuestSeatOut,
    OrgTypeFieldOut,
    PortalEventInfo,
    PortalFormFieldOut,
    PortalFormSubmit,
    PortalLayoutInfo,
    PortalSeatSubmit,
    VenueLayoutOut,
)

router = APIRouter(prefix="/portal", tags=["portal"])


def _get_event_by_token(token: str, db: Session) -> Event:
    event = (
        db.query(Event)
        .options(joinedload(Event.layout_reservations), joinedload(Event.portal_org_type))
        .filter(Event.portal_token == token, Event.portal_enabled == True)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Portal bulunamadı veya devre dışı")
    return event


@router.get("/{token}", response_model=PortalEventInfo)
def get_portal_info(token: str, db: Session = Depends(get_db)):
    event = _get_event_by_token(token, db)
    salon = db.query(Salon).filter(Salon.id == event.salon_id).first()

    # Get form fields — prefer new CustomerFormType system over legacy OrgTypeField
    form_fields = []
    if event.portal_form_type_id:
        fields = (
            db.query(CustomerFormTypeField)
            .filter(
                CustomerFormTypeField.salon_id == event.salon_id,
                CustomerFormTypeField.customer_form_type_id == event.portal_form_type_id,
            )
            .order_by(CustomerFormTypeField.sort_order)
            .all()
        )
        form_fields = [
            PortalFormFieldOut(
                id=f.id, key=f.key, label=f.label, field_type=f.field_type,
                options=f.options or [], is_required=f.is_required, sort_order=f.sort_order
            )
            for f in fields
        ]
    elif event.portal_org_type_id:
        fields = (
            db.query(OrgTypeField)
            .filter(
                OrgTypeField.salon_id == event.salon_id,
                OrgTypeField.event_type_id == event.portal_org_type_id,
            )
            .order_by(OrgTypeField.sort_order)
            .all()
        )
        form_fields = [
            PortalFormFieldOut(
                id=f.id, key=f.key, label=f.label, field_type=f.field_type,
                options=f.options or [], is_required=f.is_required, sort_order=f.sort_order
            )
            for f in fields
        ]

    # Build reserved layouts list
    reserved_layouts = []
    if event.portal_layout_permission and event.layout_reservations:
        for res in event.layout_reservations:
            layout = db.query(VenueLayout).filter(VenueLayout.id == res.layout_id).first()
            if layout:
                reserved_layouts.append(PortalLayoutInfo(id=layout.id, name=layout.name))

    event_type_name = ""
    if event.portal_org_type:
        event_type_name = event.portal_org_type.name
    elif event.event_type:
        event_type_name = event.event_type.name

    return PortalEventInfo(
        salon_name=salon.name if salon else "",
        event_date=event.event_date,
        start_time=event.start_time,
        end_time=event.end_time,
        bride_groom=event.bride_groom,
        guest_count=event.guest_count,
        event_type_name=event_type_name,
        portal_title=event.portal_title or "Davetiniz",
        seating_enabled=event.seating_enabled,
        portal_layout_permission=event.portal_layout_permission,
        reserved_layouts=reserved_layouts,
        form_fields=form_fields,
        appointment_no=event.appointment_no,
        payment_enabled=bool(event.payment_enabled),
        payment_bank_name=salon.payment_bank_name if salon else "",
        payment_iban=salon.payment_iban if salon else "",
        payment_account_holder=salon.payment_account_holder if salon else "",
        payment_description=salon.payment_description if salon else "",
        payment_complete=event.payment_complete,
        customer_payment_claimed=bool(event.customer_payment_claimed),
        portal_message=event.portal_message or "",
    )


@router.post("/{token}/form")
def submit_form(token: str, body: PortalFormSubmit, db: Session = Depends(get_db)):
    event = _get_event_by_token(token, db)
    submission = PortalFormSubmission(event_id=event.id, data=body.data)
    db.add(submission)
    db.commit()
    return {"ok": True}


@router.post("/{token}/payment-claimed")
def claim_payment(token: str, db: Session = Depends(get_db)):
    event = _get_event_by_token(token, db)
    if event.payment_complete:
        return {"ok": True, "already_confirmed": True}
    event.customer_payment_claimed = True
    db.commit()

    salon = db.query(Salon).filter(Salon.id == event.salon_id).first()
    name = event.full_name or event.bride_groom or event.title or "Müşteri"
    appt = f"#{event.appointment_no}" if event.appointment_no else ""
    title = "Ödeme bildirimi"
    message = f"{name} isimli müşteri, randevu {appt} için ödeme yaptığını bildirdi. Sistemi kontrol edip onaylayınız."
    notify(db, event.salon_id, "payment_claimed", title, message, event_id=event.id)

    if salon and salon.notification_email:
        ok, detail = send_email(salon, salon.notification_email, f"Eventra: {title}", message)
        if not ok:
            notify(db, event.salon_id, "email_failed", "Mail gönderilemedi", f"Ödeme bildirimi maili gönderilemedi: {detail}", event_id=event.id)

    return {"ok": True}


@router.get("/{token}/layouts/{layout_id}", response_model=VenueLayoutOut | None)
def get_portal_layout(token: str, layout_id: str, db: Session = Depends(get_db)):
    event = _get_event_by_token(token, db)
    if not event.portal_layout_permission:
        raise HTTPException(status_code=403, detail="Salon düzeni erişimi yok")
    # Check that layout is in reserved layouts for this event
    allowed = [r.layout_id for r in (event.layout_reservations or [])]
    if layout_id not in allowed:
        raise HTTPException(status_code=403, detail="Bu salon bu davet için rezerve edilmemiş")
    layout = (
        db.query(VenueLayout)
        .options(joinedload(VenueLayout.tables))
        .filter(VenueLayout.id == layout_id, VenueLayout.salon_id == event.salon_id)
        .first()
    )
    return layout


@router.get("/{token}/layouts/{layout_id}/seatings", response_model=list[GuestSeatOut])
def get_portal_seatings(token: str, layout_id: str, db: Session = Depends(get_db)):
    event = _get_event_by_token(token, db)
    if not event.portal_layout_permission:
        raise HTTPException(status_code=403, detail="Salon düzeni erişimi yok")
    allowed = [r.layout_id for r in (event.layout_reservations or [])]
    if layout_id not in allowed:
        raise HTTPException(status_code=403, detail="Bu salon bu davet için rezerve edilmemiş")
    # Return seatings for tables in this layout
    table_ids = [t.id for t in db.query(VenueTable).filter(VenueTable.layout_id == layout_id).all()]
    return db.query(GuestSeating).filter(
        GuestSeating.event_id == event.id,
        GuestSeating.table_id.in_(table_ids)
    ).all()


@router.put("/{token}/layouts/{layout_id}/seatings", response_model=list[GuestSeatOut])
def save_portal_seatings(token: str, layout_id: str, body: PortalSeatSubmit, db: Session = Depends(get_db)):
    event = _get_event_by_token(token, db)
    if not event.portal_layout_permission:
        raise HTTPException(status_code=403, detail="Salon düzeni erişimi yok")
    allowed = [r.layout_id for r in (event.layout_reservations or [])]
    if layout_id not in allowed:
        raise HTTPException(status_code=403, detail="Bu salon bu davet için rezerve edilmemiş")

    table_ids = {t.id for t in db.query(VenueTable).filter(VenueTable.layout_id == layout_id).all()}

    # Delete only seatings for this layout's tables
    db.query(GuestSeating).filter(
        GuestSeating.event_id == event.id,
        GuestSeating.table_id.in_(table_ids)
    ).delete(synchronize_session=False)
    db.flush()

    rows = [
        GuestSeating(event_id=event.id, **s.model_dump())
        for s in body.seatings
        if s.table_id in table_ids
    ]
    db.add_all(rows)
    db.commit()
    return rows


# ─── Legacy customer-token endpoints (backward compat) ───────────────────────

@router.get("/{token}/layout", response_model=VenueLayoutOut | None)
def get_portal_layout_legacy(token: str, db: Session = Depends(get_db)):
    """Legacy: single layout via seating_enabled on event."""
    event = _get_event_by_token(token, db)
    if not event or not event.layout_id:
        return None
    layout = (
        db.query(VenueLayout)
        .options(joinedload(VenueLayout.tables))
        .filter(VenueLayout.id == event.layout_id, VenueLayout.salon_id == event.salon_id)
        .first()
    )
    return layout


@router.get("/{token}/seatings", response_model=list[GuestSeatOut])
def get_portal_seatings_legacy(token: str, db: Session = Depends(get_db)):
    event = _get_event_by_token(token, db)
    if not event.layout_id:
        return []
    table_ids = [t.id for t in db.query(VenueTable).filter(VenueTable.layout_id == event.layout_id).all()]
    return db.query(GuestSeating).filter(
        GuestSeating.event_id == event.id,
        GuestSeating.table_id.in_(table_ids),
    ).all()


@router.put("/{token}/seatings", response_model=list[GuestSeatOut])
def save_portal_seatings_legacy(token: str, body: PortalSeatSubmit, db: Session = Depends(get_db)):
    event = _get_event_by_token(token, db)
    if not event.layout_id:
        return []
    table_ids = {t.id for t in db.query(VenueTable).filter(VenueTable.layout_id == event.layout_id).all()}
    db.query(GuestSeating).filter(
        GuestSeating.event_id == event.id,
        GuestSeating.table_id.in_(table_ids),
    ).delete(synchronize_session=False)
    db.flush()
    rows = [
        GuestSeating(event_id=event.id, **s.model_dump())
        for s in body.seatings
        if s.table_id in table_ids
    ]
    db.add_all(rows)
    db.commit()
    return rows
