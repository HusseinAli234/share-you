from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func
from datetime import datetime

from app.db.base import Base
from app.db.base import TimestampMixin

class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str] = mapped_column()