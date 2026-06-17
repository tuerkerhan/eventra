from sqlalchemy.orm import Session

from .models import Notification


def notify(db: Session, salon_id: str, type_: str, title: str, message: str, event_id: str | None = None) -> Notification:
    n = Notification(salon_id=salon_id, event_id=event_id, type=type_, title=title, message=message)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n
