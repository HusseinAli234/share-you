import uuid
from typing import List, Optional, Tuple

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models import Document, Project, ProjectMember, Role, User
from app.schemas.projects import ProjectCreate, ProjectInvite, ProjectUpdate
from app.utils.s3 import delete_file, get_url
from app.utils.s3 import upload_file as s3_upload_file


class ProjectService:
    @staticmethod
    def create_project(
        db: Session, project_data: ProjectCreate, user_id: int
    ) -> Project:
        project_db = Project(
            name=project_data.name,
            description=project_data.description,
            owner_id=user_id,
        )
        db.add(project_db)
        db.flush()

        project_member = ProjectMember(
            user_id=user_id, project_id=project_db.id, role=Role.OWNER
        )
        db.add(project_member)
        db.commit()
        return project_db

    @staticmethod
    def get_user_projects(db: Session, user_id: int) -> List[Project]:
        return (
            db.query(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .filter(ProjectMember.user_id == user_id)
            .all()
        )

    @staticmethod
    def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def update_project(
        db: Session, project_id: int, data: ProjectUpdate
    ) -> Optional[Project]:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        project.version += 1
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(
        db: Session, project_id: int, background_tasks: BackgroundTasks
    ) -> bool:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        s3_key_docs = [doc.s3_key for doc in project.documents]

        background_tasks.add_task(ProjectService.__batch_delete, s3_key_docs)

        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def invite_user(
        db: Session, project_id: int, invite_data: ProjectInvite
    ) -> Tuple[bool, str]:
        user = db.query(User).filter(User.id == invite_data.user_id).first()
        if not user:
            return False, "User not found"

        member = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == invite_data.user_id,
            )
            .first()
        )
        if member:
            return False, "User is already a member"

        project_memb = ProjectMember(
            role=invite_data.role,
            project_id=project_id,
            user_id=invite_data.user_id,
        )
        db.add(project_memb)
        db.commit()
        return True, "Successfully invited"

    @staticmethod
    def upload_document(db: Session, project_id: int, file: UploadFile) -> Document:
        project = db.query(Project).filter(Project.id == project_id).first()

        if project.total_size + file.size > settings.MAX_PROJECT_SIZE_BYTES:
            raise ValueError("Limited size of project")

        doc_uuid = uuid.uuid4()
        s3_key = s3_upload_file(
            file.file,
            f"{str(doc_uuid)}-{file.filename}",
            f"projects/{project_id}",
        )

        project.total_size += file.size

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
        db.refresh(project)
        return doc

    @staticmethod
    def get_document(
        db: Session, project_id: int, document_id: int
    ) -> Optional[Document]:
        doc = (
            db.query(Document)
            .filter(Document.id == document_id, Document.project_id == project_id)
            .first()
        )
        if not doc:
            return None

        doc.download_url = get_url(doc.s3_key)
        return doc

    @staticmethod
    def get_documents(db: Session, project_id: int) -> List[Document]:
        docs = db.query(Document).filter(Document.project_id == project_id).all()
        for doc in docs:
            doc.download_url = get_url(doc.s3_key)
        return docs

    @staticmethod
    def update_document(
        db: Session,
        document_id: int,
        project_id: int,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ):
        document = (
            db.query(Document)
            .filter(Document.id == document_id, Document.project_id == project_id)
            .first()
        )
        if not document:
            return None
        project = db.query(Project).filter(Project.id == project_id).first()

        prev_size = document.size

        if (
            project.total_size - prev_size
        ) + file.size > settings.MAX_PROJECT_SIZE_BYTES:
            raise ValueError("Limited size of project")

        background_tasks.add_task(ProjectService.__batch_delete, [document.s3_key])
        doc_uuid = uuid.uuid4()
        s3_key = s3_upload_file(
            file.file,
            f"{str(doc_uuid)}-{file.filename}",
            f"projects/{project_id}",
        )
        document.name = file.filename
        document.doc_type = file.content_type
        document.size = file.size
        document.s3_key = s3_key

        project.total_size -= prev_size
        project.total_size += file.size
        db.commit()
        db.refresh(document)
        db.refresh(project)
        return document

    @staticmethod
    def delete_document(
        db: Session,
        document_id: int,
        project_id: int,
        background_tasks: BackgroundTasks,
    ) -> bool:
        document = (
            db.query(Document)
            .filter(Document.id == document_id, Document.project_id == project_id)
            .first()
        )
        if not document:
            return False
        project = db.query(Project).filter(Project.id == project_id).first()

        project.total_size -= document.size
        background_tasks.add_task(ProjectService.__batch_delete, [document.s3_key])

        db.delete(document)
        db.commit()
        db.refresh(project)
        return True

    @staticmethod
    def __batch_delete(keys):
        for key in keys:
            delete_file(key)
