from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import get_db
from app.models.user import User

secure_context = CryptContext(schemes=["argon2"])

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db)):

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == payload.get("sub")).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User not exist")

    return user


def hashed_password(raw_password: str):
    hashed = secure_context.hash(raw_password)
    return hashed


def verify(raw_password: str, hashed_password: str) -> bool:
    return secure_context.verify(raw_password, hashed_password)


def create_access_token(user):
    payload = {
        "sub": str(user.id),
        "exp": timedelta(minutes=settings.expire_time) + datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token
