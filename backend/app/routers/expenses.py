import calendar as _cal
from datetime import date as _date, timedelta

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


def _next_due(d: _date, recurrence: str, custom_days: int | None) -> _date:
    if recurrence == "weekly":
        return d + timedelta(days=7)
    if recurrence == "monthly":
        month = d.month % 12 + 1
        year = d.year + (d.month // 12)
        return d.replace(year=year, month=month, day=min(d.day, _cal.monthrange(year, month)[1]))
    if recurrence == "yearly":
        try:
            return d.replace(year=d.year + 1)
        except ValueError:
            return d.replace(year=d.year + 1, day=28)
    if recurrence == "custom" and custom_days:
        return d + timedelta(days=custom_days)
    return d


@router.get("", response_model=list[ExpenseOut])
def list_expenses(db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    return [_out(e) for e in db.query(Expense).filter(Expense.salon_id == user.salon_id).order_by(Expense.due_date).all()]


@router.post("", response_model=ExpenseOut)
def create_expense(body: ExpenseIn, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    data = body.model_dump()
    data.pop("is_paid", None)
    is_approved = body.amount_type == "fixed"

    start = _date.fromisoformat(body.due_date)
    today_d = _date.today()

    # Geçmiş tekrarlayan giderler için tüm geçmiş dönemleri otomatik oluştur
    if body.recurrence != "once" and start < today_d:
        due_dates: list[str] = []
        d = start
        while d <= today_d:
            due_dates.append(d.isoformat())
            d = _next_due(d, body.recurrence, body.custom_period_days)
        due_dates.append(d.isoformat())  # sonraki gelecek dönem
    else:
        due_dates = [body.due_date]

    last: Expense | None = None
    for due_str in due_dates:
        exp = Expense(
            salon_id=user.salon_id,
            is_approved=is_approved,
            **{**data, "due_date": due_str},
        )
        db.add(exp)
        last = exp

    db.commit()
    db.refresh(last)  # type: ignore[arg-type]
    return _out(last)  # type: ignore[arg-type]


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
