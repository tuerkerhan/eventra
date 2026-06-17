import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.deps import get_current_admin
from ..core.security import create_access_token, hash_password, verify_password
from ..database import get_db
from ..models import AdminUser, EventType, EventTypeFieldDef, Salon, SalonUser, VenueLayout
from ..schemas import (
    AdminCreateIn,
    LoginIn,
    SalonCreateIn,
    SalonOut,
    SalonUserCreateIn,
    SalonUserOut,
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
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")

    salon = Salon(
        name=body.name,
        address=body.address,
        currency=body.currency,
        vat_rate=body.vat_rate,
        contract_prefix=body.contract_prefix,
        reminder_days=body.reminder_days,
        max_users=body.max_users,
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

    # Create default salons (rooms)
    for room_name in ("Salon A", "Salon B", "Salon C"):
        db.add(VenueLayout(salon_id=salon.id, name=room_name))

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
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")

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
