from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Document, Project, ProjectMember, Role, User
from app.schemas.documents import DocumentOut
from app.schemas.projects import ProjectCreate, ProjectInvite, ProjectOut, ProjectUpdate
from app.utils.s3 import get_url
from app.utils.s3 import upload_file as s3_upload_file
from app.utils.validators import (
    validate_file,
    validate_project_owner,
    validate_projects_member,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "/",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="This endpoint for creating project",
    response_description="The created project",
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project_db = Project(
        name=project.name, description=project.description, owner_id=user.id
    )
    db.add(project_db)
    db.flush()

    project_member = ProjectMember(
        user_id=user.id, project_id=project_db.id, role=Role.OWNER
    )
    db.add(project_member)
    db.commit()
    return project_db


@router.get(
    "/",
    response_model=List[ProjectOut],
    status_code=status.HTTP_200_OK,
    summary="This endpoint for getting projects by user",
    response_description="Projects by user",
)
def get_user_projects(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    projects = (
        db.query(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .filter(ProjectMember.user_id == user.id)
        .all()
    )
    return projects


@router.get(
    "/{project_id}",
    response_model=ProjectOut,
    status_code=status.HTTP_200_OK,
    summary="This endpoint for getting project by id",
    response_description="Project by user",
)
def get_project_by_id(
    project_id: int,
    user: User = Depends(validate_projects_member),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    return project


@router.put(
    "/{project_id}",
    response_model=ProjectOut,
    status_code=status.HTTP_200_OK,
    summary="This endpoint for updating project by id",
    response_description="Updated project by user",
)
def update_project(
    data: ProjectUpdate,
    project_id: int,
    user: User = Depends(validate_project_owner),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Not found")

    data = data.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(project, field, value)

    project.version += 1
    db.commit()
    db.refresh(project)
    return project


@router.post(
    "/{project_id}/invite",
    response_model=str,
    status_code=status.HTTP_200_OK,
    summary="This endpoint for invite user to project",
    response_description="Successfully sent invite",
)
def send_invite(
    project_inv: ProjectInvite,
    project_id: int,
    user: User = Depends(validate_project_owner),
    db: Session = Depends(get_db),
):
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == project_inv.user_id,
        )
        .first()
    )

    us = db.query(User).filter(User.id == project_inv.user_id).first()

    if not us:
        raise HTTPException(status_code=404, detail="Not found")

    if member:
        raise HTTPException(status_code=400, detail="Bad request!")

    project_memb = ProjectMember(
        role=project_inv.role, project_id=project_id, user_id=project_inv.user_id
    )
    db.add(project_memb)
    db.commit()

    return "Successfully invited"


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="This endpoint for deleting project by id",
)
def delete_project(
    project_id: int,
    user: User = Depends(validate_project_owner),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(project)
    db.commit()
    return


@router.post(
    "/{project_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="This endpoint for upload file to project",
    response_description="The created document",
)
def upload_file(
    project_id: int,
    file: UploadFile = Depends(validate_file),
    db: Session = Depends(get_db),
    user: User = Depends(validate_projects_member),
):
    s3_key = s3_upload_file(file.file, file.filename, f"projects/{project_id}")

    doc = Document(
        name=file.filename,
        doc_type=file.content_type,
        size=file.size,
        project_id=project_id,
        s3_key=s3_key,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get(
    "/{project_id}/documents/{document_id}",
    response_model=DocumentOut,
    status_code=status.HTTP_200_OK,
    summary="This endpoint for getting document",
    response_description="The document",
)
def get_document(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(validate_projects_member),
):
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.project_id == project_id)
        .first()
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Not Found!")

    url = get_url(doc.s3_key)
    doc.download_url = url
    return doc


@router.get(
    "/{project_id}/documents",
    response_model=List[DocumentOut],
    status_code=status.HTTP_200_OK,
    summary="This endpoint for getting documents",
    response_description="The documents",
)
def get_documents(
    project_id: int,
    user: User = Depends(validate_projects_member),
    db: Session = Depends(get_db),
):
    docs = db.query(Document).filter(Document.project_id == project_id).all()

    if len(docs) == 0:
        return docs

    for doc in docs:
        doc.download_url = get_url(doc.s3_key)

    return docs
