from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))

    project: Mapped["Project"] = relationship(back_populates="documents")
