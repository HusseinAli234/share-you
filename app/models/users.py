from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str] = mapped_column()
    project_members: Mapped[list["ProjectMember"]] = relationship(back_populates="user",cascade="all, delete-orphan",passive_deletes=True)
