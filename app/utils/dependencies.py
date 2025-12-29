from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db import get_db
from app import models
from app.utils.auth import decode_access_token

# HTTP Bearer security
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),
                     db: Session = Depends(get_db)) -> models.User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid auth token")

    user = db.query(models.User).filter(models.User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user