from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..database import get_db
from ..models import EventTypeFieldDef, SalonUser
from ..schemas import EventTypeFieldDefIn, EventTypeFieldDefOut

router = APIRouter(prefix="/event-type-fields", tags=["event-type-fields"])


@router.get("", response_model=list[EventTypeFieldDefOut])
def list_fields(
    type_id: str = Query(...),
    db: Session = Depends(get_db),
    user: SalonUser = Depends(get_current_user),
):
    return (
        db.query(EventTypeFieldDef)
        .filter(EventTypeFieldDef.salon_id == user.salon_id, EventTypeFieldDef.event_type_id == type_id)
        .order_by(EventTypeFieldDef.sort_order)
        .all()
    )


@router.post("", response_model=EventTypeFieldDefOut)
def add_field(body: EventTypeFieldDefIn, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    count = db.query(EventTypeFieldDef).filter(
        EventTypeFieldDef.salon_id == user.salon_id, EventTypeFieldDef.event_type_id == body.event_type_id
    ).count()
    f = EventTypeFieldDef(salon_id=user.salon_id, sort_order=body.sort_order or count, **body.model_dump(exclude={"sort_order"}))
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.delete("/{field_id}", status_code=204)
def delete_field(field_id: str, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    f = db.query(EventTypeFieldDef).filter(
        EventTypeFieldDef.id == field_id, EventTypeFieldDef.salon_id == user.salon_id
    ).first()
    if not f:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")
    db.delete(f)
    db.commit()
