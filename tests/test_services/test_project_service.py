from unittest.mock import MagicMock, patch

from fastapi import UploadFile

from app.models import Document, Project, ProjectMember, User
from app.schemas.projects import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService


def test_create_project(mock_db_session):
    project_data = ProjectCreate(name="Test Project", description="Desc")
    user_id = 1

    project = ProjectService.create_project(mock_db_session, project_data, user_id)

    assert project.name == "Test Project"
    assert project.description == "Desc"
    assert project.owner_id == user_id
    assert mock_db_session.add.call_count == 2
    mock_db_session.flush.assert_called_once()
    mock_db_session.commit.assert_called_once()


def test_get_user_projects(mock_db_session):
    user_id = 1
    expected_projects = [Project(name="Test Project")]

    mock_filter = mock_db_session.query.return_value.join.return_value.filter
    mock_filter.return_value.all.return_value = expected_projects

    projects = ProjectService.get_user_projects(mock_db_session, user_id)
    assert projects == expected_projects


def test_get_project_by_id(mock_db_session):
    project_id = 1
    expected_project = Project(id=1, name="Test Project")

    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        expected_project
    )

    project = ProjectService.get_project_by_id(mock_db_session, project_id)
    assert project == expected_project


def test_update_project(mock_db_session):
    project_id = 1
    update_data = ProjectUpdate(name="Updated", description="Updated Desc")
    existing_project = Project(id=1, name="Old", description="Old Desc", version=1)

    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        existing_project
    )

    project = ProjectService.update_project(mock_db_session, project_id, update_data)

    assert project.name == "Updated"
    assert project.description == "Updated Desc"
    assert project.version == 2
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(existing_project)


def test_update_project_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    project = ProjectService.update_project(
        mock_db_session, 1, ProjectUpdate(name="Updated")
    )
    assert project is None


def test_delete_project(mock_db_session):
    mock_bg_tasks = MagicMock()
    existing_project = Project(id=1)
    doc = Document(s3_key="some_key")
    existing_project.documents = [doc]

    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        existing_project
    )

    result = ProjectService.delete_project(mock_db_session, 1, mock_bg_tasks)

    assert result is True
    mock_bg_tasks.add_task.assert_called_once()
    mock_db_session.delete.assert_called_once_with(existing_project)
    mock_db_session.commit.assert_called_once()


def test_delete_project_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    result = ProjectService.delete_project(mock_db_session, 1, MagicMock())
    assert result is False


def test_invite_user(mock_db_session):
    mock_user = User(id=1, login="test_user")
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_user,
        None,
    ]

    result, msg = ProjectService.invite_user(mock_db_session, 1, "test_user")

    assert result is True
    assert msg == "Successfully invited"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


def test_invite_user_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    success, msg = ProjectService.invite_user(mock_db_session, 1, "notfound")
    assert success is False
    assert msg == "User not found"


def test_invite_user_already_member(mock_db_session):
    user = User(id=2)
    member = ProjectMember(user_id=2, project_id=1)

    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        user,
        member,
    ]

    success, msg = ProjectService.invite_user(mock_db_session, 1, "test_user")

    assert success is False
    assert msg == "User is already a member"


@patch("app.services.project_service.s3_upload_file")
@patch("app.services.project_service.uuid.uuid4")
def test_upload_document(mock_uuid, mock_s3_upload, mock_db_session):
    mock_uuid.return_value = "fake-uuid"
    mock_s3_upload.return_value = "fake-s3-key"

    project = Project(id=1, total_size=0)
    mock_db_session.query.return_value.filter.return_value.first.return_value = project

    fake_file = MagicMock(spec=UploadFile)
    fake_file.size = 100
    fake_file.filename = "test.txt"
    fake_file.content_type = "text/plain"
    fake_file.file = MagicMock()

    doc = ProjectService.upload_document(mock_db_session, 1, fake_file)

    assert doc.name == "test.txt"
    assert doc.s3_key == "fake-s3-key"
    assert project.total_size == 100
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


def test_get_document(mock_db_session):
    doc = Document(id=1, s3_key="fake-key")
    mock_db_session.query.return_value.filter.return_value.first.return_value = doc

    result = ProjectService.get_document(mock_db_session, 1, 1)

    assert result == doc


def test_get_document_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    result = ProjectService.get_document(mock_db_session, 1, 1)
    assert result is None


def test_get_documents(mock_db_session):
    docs = [Document(id=1, s3_key="fake-key")]

    mock_query = mock_db_session.query.return_value.filter.return_value
    mock_query.offset.return_value.limit.return_value.all.return_value = docs

    results = ProjectService.get_documents(mock_db_session, 1, limit=10, skip=0)

    assert results == docs


@patch("app.services.project_service.s3_upload_file")
@patch("app.services.project_service.uuid.uuid4")
def test_update_document(mock_uuid, mock_s3_upload, mock_db_session):
    mock_uuid.return_value = "fake-uuid2"
    mock_s3_upload.return_value = "fake-s3-key2"

    doc = Document(id=1, size=50, s3_key="old-key")
    project = Project(id=1, total_size=50)
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        doc,
        project,
    ]

    fake_file = MagicMock(spec=UploadFile)
    fake_file.size = 100
    fake_file.filename = "test2.txt"
    fake_file.content_type = "text/plain"
    fake_file.file = MagicMock()

    mock_bg_tasks = MagicMock()

    result = ProjectService.update_document(
        mock_db_session, 1, 1, fake_file, mock_bg_tasks
    )

    assert result.name == "test2.txt"
    assert result.s3_key == "fake-s3-key2"
    assert project.total_size == 100
    mock_bg_tasks.add_task.assert_called_once()
    mock_db_session.commit.assert_called_once()


def test_delete_document(mock_db_session):
    doc = Document(id=1, size=50, s3_key="old-key")
    project = Project(id=1, total_size=50)
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        doc,
        project,
    ]

    mock_bg_tasks = MagicMock()

    result = ProjectService.delete_document(mock_db_session, 1, 1, mock_bg_tasks)

    assert result is True
    assert project.total_size == 0
    mock_bg_tasks.add_task.assert_called_once()
    mock_db_session.delete.assert_called_once_with(doc)
    mock_db_session.commit.assert_called_once()
