from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Role(str, Enum):
    OWNER = "owner"
    PARTICIPANT = "participant"


class ProjectMember(TimestampMixin, Base):
    __tablename__ = "project_members"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"), primary_key=True)

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    project: Mapped["Project"] = relationship(back_populates="project_members")
    user: Mapped["User"] = relationship(back_populates="project_members")
    role: Mapped[Role] = mapped_column(SQLEnum(Role))


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column()
    version: Mapped[int] = mapped_column(default=1)
    project_members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project",cascade="all, delete-orphan",passive_deletes=True
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="project",cascade="all, delete-orphan",passive_deletes=True)