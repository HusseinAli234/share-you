from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.projects import Role


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    version: int


class ProjectInvite(BaseModel):
    user_id: int
    role: Role = Role.PARTICIPANT
