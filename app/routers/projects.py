from typing import List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.documents import DocumentOut
from app.schemas.projects import (
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
)
from app.services.project_service import ProjectService
from app.utils.s3 import get_url
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
    return ProjectService.create_project(db=db, project_data=project, user_id=user.id)


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
    return ProjectService.get_user_projects(db=db, user_id=user.id)


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
    project = ProjectService.get_project_by_id(db=db, project_id=project_id)
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
    project_id: int,
    data: ProjectUpdate,
    user: User = Depends(validate_projects_member),
    db: Session = Depends(get_db),
):
    project = ProjectService.update_project(db=db, project_id=project_id, data=data)
    if not project:
        raise HTTPException(status_code=404, detail="Not found")
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="This endpoint for deleting project by id",
)
def delete_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(validate_project_owner),
    db: Session = Depends(get_db),
):
    is_deleted = ProjectService.delete_project(
        db=db, project_id=project_id, background_tasks=background_tasks
    )
    if not is_deleted:
        raise HTTPException(status_code=404, detail="Not found")
    return


@router.post(
    "/{project_id}/invite",
    response_model=str,
    status_code=status.HTTP_200_OK,
    summary="This endpoint for invite user to project",
    response_description="Successfully sent invite",
)
def send_invite(
    project_id: int,
    user: str,
    current_user: User = Depends(validate_project_owner),
    db: Session = Depends(get_db),
):
    success, message = ProjectService.invite_user(
        db=db, project_id=project_id, user_login=user
    )

    if not success:
        if message == "User not found":
            raise HTTPException(status_code=404, detail="Not found")
        elif message == "User is already a member":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User is already a member"
            )

    return message


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
    try:
        return ProjectService.upload_document(db=db, project_id=project_id, file=file)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Limited size of project",
        )


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
    doc = ProjectService.get_document(
        db=db, project_id=project_id, document_id=document_id
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Not Found!")

    doc_out = DocumentOut.model_validate(doc)

    doc_out.download_url = get_url(doc.s3_key)
    return doc_out


@router.get(
    "/{project_id}/documents",
    response_model=List[DocumentOut],
    status_code=status.HTTP_200_OK,
    summary="This endpoint for getting documents",
    response_description="The documents",
)
def get_documents(
    project_id: int,
    skip: int = 0,
    limit: int = 10,
    user: User = Depends(validate_projects_member),
    db: Session = Depends(get_db),
):
    docs = ProjectService.get_documents(
        db=db, project_id=project_id, limit=limit, skip=skip
    )
    docs_out = [DocumentOut.model_validate(doc) for doc in docs]
    for doc_out, doc in zip(docs_out, docs):
        doc_out.download_url = get_url(doc.s3_key)
    return docs_out


@router.put(
    "/{project_id}/documents/{document_id}",
    response_model=DocumentOut,
    status_code=status.HTTP_200_OK,
    summary="This endpoint for updating document by id",
    response_description="Updated document by user",
)
def update_document(
    project_id: int,
    document_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(validate_projects_member),
    db: Session = Depends(get_db),
    file: UploadFile = Depends(validate_file),
):
    try:
        document = ProjectService.update_document(
            db=db,
            document_id=document_id,
            project_id=project_id,
            file=file,
            background_tasks=background_tasks,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Limited size of project",
        )
    if not document:
        raise HTTPException(status_code=404, detail="Not found")
    return document


@router.delete(
    "/{project_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="",
)
def delete_document(
    document_id: int,
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(validate_project_owner),
):
    is_deleted = ProjectService.delete_document(
        db, document_id, project_id, background_tasks
    )
    if not is_deleted:
        raise HTTPException(status_code=404, detail="Not found")
    return
