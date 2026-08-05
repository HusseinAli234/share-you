from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func
from sqlalchemy import ForeignKey

from datetime import datetime
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.base import TimestampMixin


class Document(TimestampMixin,Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))

    project: Mapped["Project"] = relationship(back_populates="documents")
