import uuid
from typing import List, Optional, Tuple

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.settings import settings
from app.models import Document, Project, ProjectMember, Role, User
from app.schemas.projects import ProjectCreate, ProjectUpdate
from app.utils.s3 import delete_file
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
        logger.info(f"Project created with ID {project_db.id} by user {user_id}")
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
            logger.warning(f"Failed to update project {project_id}: not found")
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        project.version += 1
        db.commit()
        db.refresh(project)
        logger.info(f"Project {project_id} updated to version {project.version}")
        return project

    @staticmethod
    def delete_project(
        db: Session, project_id: int, background_tasks: BackgroundTasks
    ) -> bool:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.warning(f"Failed to delete project {project_id}: not found")
            return False

        s3_key_docs = [doc.s3_key for doc in project.documents]

        background_tasks.add_task(ProjectService.__batch_delete, s3_key_docs)

        db.delete(project)
        db.commit()
        logger.info(f"Project {project_id} deleted successfully")
        return True

    @staticmethod
    def invite_user(db: Session, project_id: int, user_login: str) -> Tuple[bool, str]:
        user = db.query(User).filter(User.login == user_login).first()
        if not user:
            logger.warning(
                f"Failed to invite user {user_login} "
                f"to project {project_id}: user not found"
            )
            return False, "User not found"

        member = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user.id,
            )
            .first()
        )
        if member:
            logger.warning(
                f"User {user.id} is already " f"a member of project {project_id}"
            )
            return False, "User is already a member"

        project_memb = ProjectMember(
            role=Role.PARTICIPANT,
            project_id=project_id,
            user_id=user.id,
        )
        db.add(project_memb)
        db.commit()
        logger.info(
            f"User {user.id} invited to project "
            f"{project_id} with role {Role.PARTICIPANT}"
        )
        return True, "Successfully invited"

    @staticmethod
    def upload_document(db: Session, project_id: int, file: UploadFile) -> Document:
        project = db.query(Project).filter(Project.id == project_id).with_for_update().first()

        if project.total_size + file.size > settings.MAX_PROJECT_SIZE_BYTES:
            logger.warning(f"Upload failed: project {project_id} size limit exceeded")
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
        try:
            db.commit()
            db.refresh(doc)
            db.refresh(project)
        except Exception as e:
            db.rollback()
            delete_file(s3_key)
            logger.error(f"Failed to save document {file.filename} to database: {e}")
            raise e
        logger.info(f"Document {doc.id} uploaded to project {project_id}")
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
        return doc

    @staticmethod
    def get_documents(
        db: Session, project_id: int, limit: int, skip: int
    ) -> List[Document]:
        docs = (
            db.query(Document)
            .filter(Document.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
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
        project = db.query(Project).filter(Project.id == project_id).with_for_update().first()

        prev_size = document.size

        if (
            project.total_size - prev_size
        ) + file.size > settings.MAX_PROJECT_SIZE_BYTES:
            logger.warning(f"Update failed: project {project_id} size limit exceeded")
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

        try:
            db.commit()
            db.refresh(document)
            db.refresh(project)
        except Exception as e:
            db.rollback()
            delete_file(s3_key)
            logger.error(f"Failed to update document {document_id} in database: {e}")
            raise e
        logger.info(f"Document {document_id} in project {project_id} updated")
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
        project = db.query(Project).filter(Project.id == project_id).with_for_update().first()

        project.total_size -= document.size
        background_tasks.add_task(ProjectService.__batch_delete, [document.s3_key])

        db.delete(document)
        db.commit()
        db.refresh(project)
        logger.info(f"Document {document_id} deleted from project {project_id}")
        return True

    @staticmethod
    def __batch_delete(keys):
        for key in keys:
            delete_file(key)
