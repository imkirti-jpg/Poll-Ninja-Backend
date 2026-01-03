# app/utils/auth.py
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta
from jose import jwt
import os
from datetime import timezone
from typing import Optional
from fastapi import HTTPException, status
from jose import JWTError


# Secret key for JWT
# 🔐 Read from environment variables, with a fallback
SECRET_KEY = os.getenv("SECRET_KEY", "your_super_secret_key_here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


# ---------------------------
# Password hashing
# ---------------------------
def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pbkdf2_sha256.verify(password, hashed)


# ---------------------------
# JWT Token
# ---------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta]= None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(hours=1)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
