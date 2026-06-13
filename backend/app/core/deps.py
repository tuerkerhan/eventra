from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser, SalonUser
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> SalonUser:
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz kimlik bilgisi")
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub", "")
        role: str = payload.get("role", "")
    except JWTError:
        raise exc

    if role == "salon_user":
        user = db.query(SalonUser).filter(SalonUser.id == user_id, SalonUser.is_active == True).first()
    else:
        raise exc

    if not user:
        raise exc
    return user


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> AdminUser:
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin erişimi gerekli")
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub", "")
        role: str = payload.get("role", "")
    except JWTError:
        raise exc

    if role != "admin":
        raise exc

    admin = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not admin:
        raise exc
    return admin
