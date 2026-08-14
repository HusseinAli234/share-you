from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hashed_password, verify
from app.models import User
from app.schemas.auth import RegisterForm


class AuthService:
    @staticmethod
    def register_user(db: Session, form: RegisterForm) -> Optional[User]:
        has_user = db.query(User).filter(User.login == form.login).first()
        if has_user:
            return None

        hashed = hashed_password(form.password)
        user = User(login=form.login, hashed_password=hashed)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[str]:
        user = db.query(User).filter(User.login == username).first()
        if user and verify(password, user.hashed_password):
            return create_access_token(user)
        return None
