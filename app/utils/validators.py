from fastapi import Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.projects import ProjectMember, Role
from app.models.users import User

file_types = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


def validate_file(file: UploadFile = File(...)):
    if file.content_type in file_types:
        return file
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format!")


def validate_projects_member(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = (
        db.query(ProjectMember.user_id)
        .filter(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user.id
        )
        .scalar()
    )
    if not user_id:
        raise HTTPException(status_code=403, detail="Forbidden!")
    return user


def validate_project_owner(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = (
        db.query(ProjectMember.user_id)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
            ProjectMember.role == Role.OWNER,
        )
        .scalar()
    )
    if not user_id:
        raise HTTPException(status_code=403, detail="Forbidden!")
    return user
