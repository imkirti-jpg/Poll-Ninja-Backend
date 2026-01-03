from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db import get_db
from app import models
from app.utils.auth import decode_access_token
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from jose import JWTError
from uuid import UUID

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



def check_admin_role(
    token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    
    payload = decode_access_token(token.credentials)
    user_id = payload.get("user_id")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    
    try:
        user_id = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID in token")


    if str(user.role) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    return user
