from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..database import get_db
from ..models import AdminNotification, AdminSettings, AdminUser, SalonUser, SupportTicket
from ..schemas import SupportTicketIn, SupportTicketOut, SupportTicketUpdateIn

router = APIRouter(prefix="/support", tags=["support"])


def _notify_admin(db: Session, ticket: SupportTicket) -> None:
    db.add(AdminNotification(
        type="ticket_new",
        title=f"Yeni Destek Talebi: {ticket.title}",
        message=f"Müşteri: {ticket.salon.name if ticket.salon else ''} | Aciliyet: {ticket.urgency} | {ticket.description[:120]}",
        salon_id=ticket.salon_id,
        ref_id=ticket.id,
    ))


@router.get("", response_model=list[SupportTicketOut])
def list_my_tickets(user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    tickets = db.query(SupportTicket).filter(SupportTicket.salon_id == user.salon_id).order_by(SupportTicket.created_at.desc()).all()
    out = []
    for t in tickets:
        d = SupportTicketOut.model_validate(t)
        d.salon_name = t.salon.name if t.salon else ""
        out.append(d)
    return out


@router.post("", response_model=SupportTicketOut)
def create_ticket(body: SupportTicketIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = SupportTicket(
        salon_id=user.salon_id,
        user_id=user.id,
        **body.model_dump(),
    )
    db.add(ticket)
    db.flush()
    db.refresh(ticket)
    _notify_admin(db, ticket)
    db.commit()
    db.refresh(ticket)
    d = SupportTicketOut.model_validate(ticket)
    d.salon_name = ticket.salon.name if ticket.salon else ""
    return d


@router.patch("/{ticket_id}/close", response_model=SupportTicketOut)
def close_ticket(ticket_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id, SupportTicket.salon_id == user.salon_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket bulunamadı")
    ticket.status = "closed"
    db.commit()
    db.refresh(ticket)
    d = SupportTicketOut.model_validate(ticket)
    d.salon_name = ticket.salon.name if ticket.salon else ""
    return d


@router.get("/admin-info")
def get_admin_info(user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns support phone and booking link from admin settings."""
    cfg = db.query(AdminSettings).first()
    return {
        "support_phone": cfg.support_phone if cfg else "",
        "booking_link": cfg.booking_link if cfg else "",
    }
