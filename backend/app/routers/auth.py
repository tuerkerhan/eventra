from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..core.security import create_access_token, verify_password
from ..database import get_db
from ..models import AdminUser, SalonUser
from ..schemas import LoginIn, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    # Try salon user first
    user = db.query(SalonUser).filter(SalonUser.email == body.email, SalonUser.is_active == True).first()
    if user and verify_password(body.password, user.hashed_password):
        token = create_access_token(user.id, {"role": "salon_user", "salon_id": user.salon_id})
        return TokenOut(access_token=token, role=user.role, salon_id=user.salon_id, username=user.username)

    # Try admin
    admin = db.query(AdminUser).filter(AdminUser.email == body.email).first()
    if admin and verify_password(body.password, admin.hashed_password):
        token = create_access_token(admin.id, {"role": "admin"})
        return TokenOut(access_token=token, role="admin")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-posta veya şifre hatalı")


@router.get("/me")
def me(current_user: SalonUser = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role,
        "salon_id": current_user.salon_id,
    }
