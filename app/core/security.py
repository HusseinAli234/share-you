from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import get_db
from app.models.users import User

ph = PasswordHasher()

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == payload.get("sub")).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User not exist")

    return user


def hashed_password(raw_password: str) -> str:
    return ph.hash(raw_password)


def verify(raw_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, raw_password)
    except VerifyMismatchError:
        return False


def create_access_token(user):
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.expire_time)

    payload = {
        "sub": str(user.id),
        "exp": expire,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token
