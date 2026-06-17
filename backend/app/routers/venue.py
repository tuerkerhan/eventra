from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..core.deps import get_current_user
from ..database import get_db
from ..models import GuestSeating, SalonUser, VenueLayout, VenueTable
from ..schemas import GuestSeatIn, GuestSeatOut, VenueLayoutIn, VenueLayoutOut, VenueTableOut

router = APIRouter(prefix="/venue", tags=["venue"])


@router.get("/layouts", response_model=list[VenueLayoutOut])
def list_layouts(user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(VenueLayout)
        .options(joinedload(VenueLayout.tables))
        .filter(VenueLayout.salon_id == user.salon_id)
        .all()
    )


MAX_LAYOUTS_PER_SALON = 3


@router.post("/layouts", response_model=VenueLayoutOut)
def create_layout(body: VenueLayoutIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_count = db.query(VenueLayout).filter(VenueLayout.salon_id == user.salon_id).count()
    if existing_count >= MAX_LAYOUTS_PER_SALON:
        raise HTTPException(status_code=400, detail=f"En fazla {MAX_LAYOUTS_PER_SALON} salon oluşturulabilir")

    layout = VenueLayout(
        salon_id=user.salon_id,
        name=body.name,
        canvas_width=body.canvas_width,
        canvas_height=body.canvas_height,
        stage=body.stage,
        walls=body.walls,
    )
    db.add(layout)
    db.flush()

    for t in body.tables:
        db.add(VenueTable(layout_id=layout.id, **t.model_dump()))

    db.commit()
    db.refresh(layout)
    return layout


@router.get("/layouts/{layout_id}", response_model=VenueLayoutOut)
def get_layout(layout_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    layout = (
        db.query(VenueLayout)
        .options(joinedload(VenueLayout.tables))
        .filter(VenueLayout.id == layout_id, VenueLayout.salon_id == user.salon_id)
        .first()
    )
    if not layout:
        raise HTTPException(status_code=404, detail="Layout bulunamadı")
    return layout


@router.put("/layouts/{layout_id}", response_model=VenueLayoutOut)
def save_layout(
    layout_id: str, body: VenueLayoutIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    layout = (
        db.query(VenueLayout)
        .options(joinedload(VenueLayout.tables))
        .filter(VenueLayout.id == layout_id, VenueLayout.salon_id == user.salon_id)
        .first()
    )
    if not layout:
        raise HTTPException(status_code=404, detail="Layout bulunamadı")

    layout.name = body.name
    layout.canvas_width = body.canvas_width
    layout.canvas_height = body.canvas_height
    layout.stage = body.stage
    layout.walls = body.walls

    # Replace tables
    for t in layout.tables:
        db.delete(t)
    db.flush()
    for t in body.tables:
        db.add(VenueTable(layout_id=layout.id, **t.model_dump()))

    db.commit()
    db.refresh(layout)
    return layout


@router.delete("/layouts/{layout_id}", status_code=204)
def delete_layout(layout_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    layout = db.query(VenueLayout).filter(VenueLayout.id == layout_id, VenueLayout.salon_id == user.salon_id).first()
    if not layout:
        raise HTTPException(status_code=404, detail="Layout bulunamadı")
    db.delete(layout)
    db.commit()


# ─── Guest seating (per event) ────────────────────────────────────────────────

@router.get("/events/{event_id}/seatings", response_model=list[GuestSeatOut])
def list_seatings(event_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(GuestSeating).filter(GuestSeating.event_id == event_id).all()


@router.put("/events/{event_id}/seatings", response_model=list[GuestSeatOut])
def save_seatings(
    event_id: str,
    body: list[GuestSeatIn],
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(GuestSeating).filter(GuestSeating.event_id == event_id).delete()
    db.flush()
    rows = [GuestSeating(event_id=event_id, **s.model_dump()) for s in body]
    db.add_all(rows)
    db.commit()
    return rows
