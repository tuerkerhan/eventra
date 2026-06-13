import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..core.deps import get_current_user
from ..database import get_db
from ..models import Customer, CustomerFieldDef, CustomerFieldValue, SalonUser
from ..schemas import CustomerFieldValueOut, CustomerIn, CustomerOut, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


def _build_out(customer: Customer) -> CustomerOut:
    custom = []
    for fv in customer.field_values:
        fd = fv.field_def
        custom.append(CustomerFieldValueOut(
            field_def_id=fd.id,
            key=fd.key,
            label=fd.label,
            field_type=fd.field_type,
            options=fd.options or [],
            value=fv.value,
        ))
    return CustomerOut(
        id=customer.id,
        name=customer.name,
        phone=customer.phone,
        email=customer.email,
        tc_no=customer.tc_no,
        address=customer.address,
        note=customer.note,
        portal_active=customer.portal_active,
        portal_token=customer.portal_token,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        custom_values=custom,
    )


@router.get("", response_model=list[CustomerOut])
def list_customers(
    q: str = Query(default="", description="İsim, telefon veya e-posta ara"),
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Customer)
        .options(joinedload(Customer.field_values).joinedload(CustomerFieldValue.field_def))
        .filter(Customer.salon_id == user.salon_id)
    )
    if q:
        q_lower = f"%{q.lower()}%"
        query = query.filter(
            Customer.name.ilike(q_lower)
            | Customer.phone.ilike(q_lower)
            | Customer.email.ilike(q_lower)
            | Customer.tc_no.ilike(q_lower)
        )
    customers = query.order_by(Customer.created_at.desc()).all()
    return [_build_out(c) for c in customers]


@router.post("", response_model=CustomerOut)
def create_customer(body: CustomerIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    token = str(uuid.uuid4()) if body.portal_active else None
    customer = Customer(
        salon_id=user.salon_id,
        name=body.name,
        phone=body.phone,
        email=body.email,
        tc_no=body.tc_no,
        address=body.address,
        note=body.note,
        portal_active=body.portal_active,
        portal_token=token,
    )
    db.add(customer)
    db.flush()

    for cv in body.custom_values:
        fd = db.query(CustomerFieldDef).filter(
            CustomerFieldDef.id == cv.field_def_id, CustomerFieldDef.salon_id == user.salon_id
        ).first()
        if fd:
            db.add(CustomerFieldValue(customer_id=customer.id, field_def_id=cv.field_def_id, value=cv.value))

    db.commit()
    db.refresh(customer)
    return _build_out(customer)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    customer = (
        db.query(Customer)
        .options(joinedload(Customer.field_values).joinedload(CustomerFieldValue.field_def))
        .filter(Customer.id == customer_id, Customer.salon_id == user.salon_id)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    return _build_out(customer)


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: str,
    body: CustomerUpdate,
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer = (
        db.query(Customer)
        .options(joinedload(Customer.field_values))
        .filter(Customer.id == customer_id, Customer.salon_id == user.salon_id)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")

    for field, val in body.model_dump(exclude_none=True, exclude={"custom_values"}).items():
        setattr(customer, field, val)

    # Handle portal token
    if body.portal_active is True and not customer.portal_token:
        customer.portal_token = str(uuid.uuid4())
    elif body.portal_active is False:
        customer.portal_token = None

    if body.custom_values is not None:
        for cv in body.custom_values:
            existing = next((fv for fv in customer.field_values if fv.field_def_id == cv.field_def_id), None)
            if existing:
                existing.value = cv.value
            else:
                fd = db.query(CustomerFieldDef).filter(
                    CustomerFieldDef.id == cv.field_def_id, CustomerFieldDef.salon_id == user.salon_id
                ).first()
                if fd:
                    db.add(CustomerFieldValue(customer_id=customer.id, field_def_id=cv.field_def_id, value=cv.value))

    db.commit()
    db.refresh(customer)
    return _build_out(customer)


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.salon_id == user.salon_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    db.delete(customer)
    db.commit()
