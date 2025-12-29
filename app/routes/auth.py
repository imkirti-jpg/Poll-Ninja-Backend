from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app import models, schema
from app.utils import auth
from datetime import timedelta


router = APIRouter()

# Register
@router.post("/register", response_model=schema.UserOut)
def register(user: schema.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    hashed = auth.hash_password(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Login

@router.post("/login", response_model=schema.Token)
def login(form_data: schema.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.email).first()

    if not user or not auth.verify_password(form_data.password,  str(user.hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = auth.create_access_token(
        data={"user_id": str(user.id), "username": user.username, "role": user.role},
        expires_delta=timedelta(hours=1)
    )

    return {
        "access_token": access_token,
        "username": user.username,
        "token_type": "bearer"
    }