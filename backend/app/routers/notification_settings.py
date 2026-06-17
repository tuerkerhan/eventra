from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..database import get_db
from ..email_utils import send_email
from ..models import Event, EventNotificationSchedule, EventType, Notification, Salon, SalonNotificationTemplate, SalonUser
from ..schemas import EventNotificationScheduleOut, NotificationTemplateIn, NotificationTemplateOut

router = APIRouter(prefix="/notification-settings", tags=["notification-settings"])

DEFAULT_DAYS = [
    (25, "Sayın %full_name%, Randevu No: %randevu_no% - '%baslik%' etkinliğinize 25 gün kaldı. Detaylar için bizimle iletişime geçebilirsiniz."),
    (15, "Sayın %full_name%, Randevu No: %randevu_no% - '%baslik%' etkinliğinize 15 gün kaldı. Herhangi bir sorunuz varsa lütfen bize ulaşın."),
    (10, "Sayın %full_name%, Randevu No: %randevu_no% - '%baslik%' etkinliğinize 10 gün kaldı. Son hazırlıkları tamamlamak için bizi arayabilirsiniz."),
]


def ensure_defaults_for_type(salon_id: str, event_type_id: str, db: Session) -> None:
    existing = db.query(SalonNotificationTemplate).filter(
        SalonNotificationTemplate.salon_id == salon_id,
        SalonNotificationTemplate.event_type_id == event_type_id,
    ).count()
    if existing == 0:
        for days, msg in DEFAULT_DAYS:
            db.add(SalonNotificationTemplate(
                salon_id=salon_id,
                event_type_id=event_type_id,
                days_before=days,
                message_template=msg,
            ))
        db.commit()


def ensure_defaults(salon_id: str, db: Session) -> None:
    """Ensure defaults exist for all event types in the salon."""
    event_types = db.query(EventType).filter(EventType.salon_id == salon_id).all()
    for et in event_types:
        ensure_defaults_for_type(salon_id, et.id, db)


def _fill_placeholders(template: str, event: Event) -> str:
    return (
        template
        .replace("%randevu_no%", str(event.appointment_no or ""))
        .replace("%baslik%", event.title or "")
        .replace("%full_name%", event.full_name or "")
        .replace("%tarih%", event.event_date or "")
    )


def check_and_send_notifications(db: Session, salon_id: str | None = None) -> int:
    today_str = date.today().isoformat()
    q = db.query(EventNotificationSchedule).filter(
        EventNotificationSchedule.send_date <= today_str,
        EventNotificationSchedule.is_sent == False,
    )
    if salon_id:
        q = q.filter(EventNotificationSchedule.salon_id == salon_id)
    pending = q.all()
    sent = 0
    for schedule in pending:
        event = db.query(Event).filter(Event.id == schedule.event_id).first()
        if not event:
            schedule.is_sent = True
            schedule.sent_at = datetime.utcnow()
            db.commit()
            continue

        salon = db.query(Salon).filter(Salon.id == schedule.salon_id).first()
        message = _fill_placeholders(schedule.message, event)
        notification_message = (
            f"Randevu No {event.appointment_no}: {event.event_date} tarihli etkinliğe "
            f"{schedule.days_before} gün kaldı."
        )

        duplicate = db.query(Notification).filter(
            Notification.salon_id == schedule.salon_id,
            Notification.event_id == event.id,
            Notification.type == "event_reminder",
            Notification.message == notification_message,
        ).first()
        if duplicate:
            schedule.is_sent = True
            schedule.sent_at = datetime.utcnow()
            continue

        schedule.is_sent = True
        schedule.sent_at = datetime.utcnow()
        db.flush()

        to_email = event.email or (salon.notification_email if salon else None)
        if to_email and salon:
            send_email(
                salon,
                to_email,
                f"Etkinlik Hatırlatıcısı – {event.title} (Randevu No: {event.appointment_no})",
                message,
            )

        db.add(Notification(
            salon_id=schedule.salon_id,
            event_id=event.id,
            type="event_reminder",
            title=f"Hatırlatıcı: {event.title}",
            message=notification_message,
        ))
        sent += 1

    if pending:
        db.commit()
    return sent


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/templates", response_model=list[NotificationTemplateOut])
def list_templates(
    event_type_id: str | None = Query(None),
    user: SalonUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if event_type_id:
        ensure_defaults_for_type(user.salon_id, event_type_id, db)
        return (
            db.query(SalonNotificationTemplate)
            .filter(
                SalonNotificationTemplate.salon_id == user.salon_id,
                SalonNotificationTemplate.event_type_id == event_type_id,
            )
            .order_by(SalonNotificationTemplate.days_before.desc())
            .all()
        )
    ensure_defaults(user.salon_id, db)
    return (
        db.query(SalonNotificationTemplate)
        .filter(SalonNotificationTemplate.salon_id == user.salon_id)
        .order_by(SalonNotificationTemplate.days_before.desc())
        .all()
    )


@router.post("/templates", response_model=NotificationTemplateOut)
def create_template(body: NotificationTemplateIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    t = SalonNotificationTemplate(salon_id=user.salon_id, **body.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.patch("/templates/{template_id}", response_model=NotificationTemplateOut)
def update_template(template_id: str, body: NotificationTemplateIn, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.query(SalonNotificationTemplate).filter(
        SalonNotificationTemplate.id == template_id,
        SalonNotificationTemplate.salon_id == user.salon_id,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    for k, v in body.model_dump().items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(template_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.query(SalonNotificationTemplate).filter(
        SalonNotificationTemplate.id == template_id,
        SalonNotificationTemplate.salon_id == user.salon_id,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    db.delete(t)
    db.commit()


@router.get("/events/{event_id}/schedules", response_model=list[EventNotificationScheduleOut])
def list_event_schedules(event_id: str, user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(EventNotificationSchedule)
        .filter(
            EventNotificationSchedule.event_id == event_id,
            EventNotificationSchedule.salon_id == user.salon_id,
        )
        .order_by(EventNotificationSchedule.days_before.desc())
        .all()
    )


@router.post("/check-send")
def trigger_check_send(user: SalonUser = Depends(get_current_user), db: Session = Depends(get_db)):
    sent = check_and_send_notifications(db, salon_id=user.salon_id)
    return {"sent": sent}
