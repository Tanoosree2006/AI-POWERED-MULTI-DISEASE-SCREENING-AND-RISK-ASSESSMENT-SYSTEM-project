from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import current_user, rate_limit
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services import crud

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201, dependencies=[Depends(rate_limit)])
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if crud.get_user_by_username(db, body.username):
        raise HTTPException(status_code=409, detail="Username already taken")
    try:
        user = crud.create_user(db, body.username, hash_password(body.password))  # role is always 'user'
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already taken")
    crud.add_audit(db, "user_registered", user.id)
    return user


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit)])
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, body.username)
    ok = verify_password(body.password, user.password_hash if user else None)
    if not user or not ok or not user.is_active:
        crud.add_audit(db, "login_failed", user.id if user else None)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    crud.add_audit(db, "login_success", user.id)
    token, expires = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, expires_in=expires)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
