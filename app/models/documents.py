from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Document(TimestampMixin, Base):
    __tablename__ = "documents"
    

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    size: Mapped[int] = mapped_column()
    s3_key: Mapped[str] = mapped_column(nullable=False)
    doc_type: Mapped[str] = mapped_column()
    
    
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    project: Mapped["Project"] = relationship(back_populates="documents")
