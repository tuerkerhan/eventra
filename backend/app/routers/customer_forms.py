from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..database import get_db
from ..models import CustomerFormType, CustomerFormTypeField, SalonUser
from ..schemas import CustomerFormTypeFieldIn, CustomerFormTypeFieldOut, CustomerFormTypeIn, CustomerFormTypeOut

router = APIRouter(prefix="/customer-forms", tags=["customer-forms"])


@router.get("/types", response_model=list[CustomerFormTypeOut])
def list_types(db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    return db.query(CustomerFormType).filter(CustomerFormType.salon_id == user.salon_id).all()


@router.post("/types", response_model=CustomerFormTypeOut)
def create_type(body: CustomerFormTypeIn, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    t = CustomerFormType(salon_id=user.salon_id, **body.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/types/{type_id}", status_code=204)
def delete_type(type_id: str, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    t = db.query(CustomerFormType).filter(CustomerFormType.id == type_id, CustomerFormType.salon_id == user.salon_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Form tipi bulunamadı")
    db.delete(t)
    db.commit()


@router.get("/fields", response_model=list[CustomerFormTypeFieldOut])
def list_fields(type_id: str, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    return (
        db.query(CustomerFormTypeField)
        .filter(CustomerFormTypeField.salon_id == user.salon_id, CustomerFormTypeField.customer_form_type_id == type_id)
        .order_by(CustomerFormTypeField.sort_order)
        .all()
    )


@router.post("/fields", response_model=CustomerFormTypeFieldOut)
def create_field(body: CustomerFormTypeFieldIn, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    # verify the form type belongs to this salon
    t = db.query(CustomerFormType).filter(CustomerFormType.id == body.customer_form_type_id, CustomerFormType.salon_id == user.salon_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Form tipi bulunamadı")
    f = CustomerFormTypeField(salon_id=user.salon_id, **body.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.delete("/fields/{field_id}", status_code=204)
def delete_field(field_id: str, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    f = db.query(CustomerFormTypeField).filter(CustomerFormTypeField.id == field_id, CustomerFormTypeField.salon_id == user.salon_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")
    db.delete(f)
    db.commit()
