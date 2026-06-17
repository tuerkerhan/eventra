from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..database import get_db
from ..email_utils import send_email
from ..models import CustomerFieldDef, OrgTypeField, PortalFormField, Salon, SalonUser
from ..schemas import (
    CustomerFieldDefIn,
    CustomerFieldDefOut,
    OrgTypeFieldIn,
    OrgTypeFieldOut,
    PortalFormFieldIn,
    PortalFormFieldOut,
    SalonOut,
    SalonUpdateIn,
    SmtpTestIn,
    UserPrefsOut,
    UserPrefsUpdate,
)

router = APIRouter(prefix="/settings", tags=["settings"])


def _get_salon(user: SalonUser, db: Session) -> Salon:
    salon = db.query(Salon).filter(Salon.id == user.salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon bulunamadı")
    return salon


@router.get("/me", response_model=UserPrefsOut)
def get_prefs(user: SalonUser = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserPrefsOut)
def update_prefs(body: UserPrefsUpdate, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.ui_mode is not None and body.ui_mode in ("full", "sade"):
        user.ui_mode = body.ui_mode
        db.commit()
        db.refresh(user)
    return user


@router.get("/salon", response_model=SalonOut)
def get_salon_settings(user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_salon(user, db)


@router.patch("/salon", response_model=SalonOut)
def update_salon_settings(
    body: SalonUpdateIn,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    salon = _get_salon(user, db)
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(salon, field, val)
    db.commit()
    db.refresh(salon)
    return salon


@router.post("/smtp-test")
def smtp_test(
    body: SmtpTestIn,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    salon = _get_salon(user, db)
    overrides = body.model_dump(exclude={"to_email"}, exclude_none=True)
    for k, v in overrides.items():
        setattr(salon, k, v)
    to_email = body.to_email or salon.notification_email
    ok, detail = send_email(salon, to_email, "Eventra SMTP Test", "Bu bir test mailidir. SMTP ayarlarınız çalışıyor.")
    return {"ok": ok, "detail": detail}


# ─── Customer field definitions ──────────────────────────────────────────────

@router.get("/customer-fields", response_model=list[CustomerFieldDefOut])
def get_customer_fields(user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(CustomerFieldDef)
        .filter(CustomerFieldDef.salon_id == user.salon_id)
        .order_by(CustomerFieldDef.sort_order)
        .all()
    )


@router.post("/customer-fields", response_model=CustomerFieldDefOut)
def create_customer_field(
    body: CustomerFieldDefIn,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    field = CustomerFieldDef(salon_id=user.salon_id, **body.model_dump())
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.put("/customer-fields/{field_id}", response_model=CustomerFieldDefOut)
def update_customer_field(
    field_id: str,
    body: CustomerFieldDefIn,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    field = db.query(CustomerFieldDef).filter(
        CustomerFieldDef.id == field_id, CustomerFieldDef.salon_id == user.salon_id
    ).first()
    if not field:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")
    for k, v in body.model_dump().items():
        setattr(field, k, v)
    db.commit()
    db.refresh(field)
    return field


@router.delete("/customer-fields/{field_id}", status_code=204)
def delete_customer_field(
    field_id: str,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    field = db.query(CustomerFieldDef).filter(
        CustomerFieldDef.id == field_id, CustomerFieldDef.salon_id == user.salon_id
    ).first()
    if not field:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")
    db.delete(field)
    db.commit()


# ─── Org type fields ─────────────────────────────────────────────────────────

@router.get("/org-type-fields", response_model=list[OrgTypeFieldOut])
def get_org_type_fields(
    event_type_id: str | None = Query(None),
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(OrgTypeField).filter(OrgTypeField.salon_id == user.salon_id)
    if event_type_id:
        q = q.filter(OrgTypeField.event_type_id == event_type_id)
    return q.order_by(OrgTypeField.sort_order).all()


@router.post("/org-type-fields", response_model=OrgTypeFieldOut)
def create_org_type_field(
    body: OrgTypeFieldIn,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    field = OrgTypeField(salon_id=user.salon_id, **body.model_dump())
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.put("/org-type-fields/{field_id}", response_model=OrgTypeFieldOut)
def update_org_type_field(
    field_id: str,
    body: OrgTypeFieldIn,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    field = db.query(OrgTypeField).filter(
        OrgTypeField.id == field_id, OrgTypeField.salon_id == user.salon_id
    ).first()
    if not field:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")
    for k, v in body.model_dump().items():
        setattr(field, k, v)
    db.commit()
    db.refresh(field)
    return field


@router.delete("/org-type-fields/{field_id}", status_code=204)
def delete_org_type_field(
    field_id: str,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    field = db.query(OrgTypeField).filter(
        OrgTypeField.id == field_id, OrgTypeField.salon_id == user.salon_id
    ).first()
    if not field:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")
    db.delete(field)
    db.commit()


# ─── Portal form fields (global, legacy) ─────────────────────────────────────

@router.get("/portal-fields", response_model=list[PortalFormFieldOut])
def get_portal_fields(user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(PortalFormField)
        .filter(PortalFormField.salon_id == user.salon_id)
        .order_by(PortalFormField.sort_order)
        .all()
    )


@router.post("/portal-fields", response_model=PortalFormFieldOut)
def create_portal_field(
    body: PortalFormFieldIn,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    field = PortalFormField(salon_id=user.salon_id, **body.model_dump())
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.put("/portal-fields/{field_id}", response_model=PortalFormFieldOut)
def update_portal_field(
    field_id: str,
    body: PortalFormFieldIn,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    field = db.query(PortalFormField).filter(
        PortalFormField.id == field_id, PortalFormField.salon_id == user.salon_id
    ).first()
    if not field:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")
    for k, v in body.model_dump().items():
        setattr(field, k, v)
    db.commit()
    db.refresh(field)
    return field


@router.delete("/portal-fields/{field_id}", status_code=204)
def delete_portal_field(
    field_id: str,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    field = db.query(PortalFormField).filter(
        PortalFormField.id == field_id, PortalFormField.salon_id == user.salon_id
    ).first()
    if not field:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")
    db.delete(field)
    db.commit()
