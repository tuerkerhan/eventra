from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..database import get_db
from ..models import Expense, SalonUser
from ..schemas import ExpenseIn, ExpenseOut, ExpenseUpdate

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _out(e: Expense) -> ExpenseOut:
    out = ExpenseOut.model_validate(e)
    if e.event_id and e.event:
        out.event_title = e.event.title
    return out


@router.get("", response_model=list[ExpenseOut])
def list_expenses(db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    return [_out(e) for e in db.query(Expense).filter(Expense.salon_id == user.salon_id).order_by(Expense.due_date).all()]


@router.post("", response_model=ExpenseOut)
def create_expense(body: ExpenseIn, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    data = body.model_dump()
    is_approved = data.pop("is_paid", False) or body.amount_type == "fixed"
    expense = Expense(
        salon_id=user.salon_id,
        is_approved=body.amount_type == "fixed",
        **data,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return _out(expense)


@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: str,
    body: ExpenseUpdate,
    db: Session = Depends(get_db),
    user: SalonUser = Depends(get_current_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.salon_id == user.salon_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gider bulunamadı")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(expense, k, v)
    db.commit()
    db.refresh(expense)
    return _out(expense)


@router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: str, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.salon_id == user.salon_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gider bulunamadı")
    db.delete(expense)
    db.commit()
