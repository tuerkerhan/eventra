import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..core.deps import get_current_user
from ..database import get_db
from ..models import Event, EventCustomField, EventLayoutReservation, EventType, SalonUser, VenueLayout
from ..schemas import (
    EventCustomFieldIn,
    EventIn,
    EventLayoutReservationOut,
    EventOut,
    EventTypeIn,
    EventTypeOut,
    EventUpdate,
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
    return [_build_event_out(e) for e in q.order_by(Event.event_date).all()]


@router.post("", response_model=EventOut)
def create_event(body: EventIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    data = body.model_dump(exclude={"custom_fields", "reserved_layout_ids"})
    event = Event(salon_id=user.salon_id, **data)
    _sync_payment(event)
    _sync_portal_token(event)
    db.add(event)
    db.flush()
    for i, cf in enumerate(body.custom_fields):
        db.add(EventCustomField(event_id=event.id, sort_order=i, **cf.model_dump()))
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

    for field, val in body.model_dump(exclude_none=True, exclude={"custom_fields", "reserved_layout_ids"}).items():
        setattr(event, field, val)

    _sync_payment(event)
    _sync_portal_token(event)

    if body.custom_fields is not None:
        for cf in event.custom_fields:
            db.delete(cf)
        db.flush()
        for i, cf in enumerate(body.custom_fields):
            db.add(EventCustomField(event_id=event.id, sort_order=i, **cf.model_dump()))

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
