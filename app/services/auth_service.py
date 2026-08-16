from typing import Optional

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import create_access_token, hashed_password, verify
from app.models import User
from app.schemas.auth import RegisterForm


class AuthService:
    @staticmethod
    def register_user(db: Session, form: RegisterForm) -> Optional[User]:
        has_user = db.query(User).filter(User.login == form.login).first()
        if has_user:
            logger.warning(f"Registration failed: user {form.login} already exists")
            return None

        hashed = hashed_password(form.password)
        user = User(login=form.login, hashed_password=hashed)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"User registered successfully: {user.login} (ID: {user.id})")
        return user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[str]:
        user = db.query(User).filter(User.login == username).first()
        if user and verify(password, user.hashed_password):
            logger.info(f"User authenticated successfully: {username}")
            return create_access_token(user)

        logger.warning(f"Failed authentication attempt for username: {username}")
        return None
