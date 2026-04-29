from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import (
    hash_password, verify_password, create_access_token, require_auth,
)

router = APIRouter(prefix="/api/auth", tags=["Autenticacao"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str = ""
    institution: str = "UFRN"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username ja existe")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email ja cadastrado")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        institution=data.institution,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "full_name": user.full_name, "email": user.email},
    }


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciais invalidas")

    token = create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "full_name": user.full_name, "email": user.email},
    }


@router.get("/me")
def me(user: User = Depends(require_auth)):
    return {"id": user.id, "username": user.username, "full_name": user.full_name, "email": user.email, "institution": user.institution}
