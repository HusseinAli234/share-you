from unittest.mock import MagicMock, patch

import pytest

from app.core.security import get_current_user
from app.main import app
from app.models import Document, Project, User
from app.utils.validators import (
    validate_file,
    validate_project_owner,
    validate_projects_member,
)


@pytest.fixture
def override_dependencies():
    user = User(id=1, login="testuser")
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[validate_projects_member] = lambda: user
    app.dependency_overrides[validate_project_owner] = lambda: user
    # file validator returns a dummy UploadFile
    dummy_file = MagicMock()
    app.dependency_overrides[validate_file] = lambda: dummy_file

    yield

    app.dependency_overrides.clear()


@patch("app.routers.projects.ProjectService.create_project")
def test_create_project(mock_create, get_client, override_dependencies):
    mock_create.return_value = Project(
        id=1, name="Test Project", description="Desc", version=1, total_size=0
    )

    response = get_client.post(
        "/projects/", json={"name": "Test Project", "description": "Desc"}
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"
    mock_create.assert_called_once()


@patch("app.routers.projects.ProjectService.get_user_projects")
def test_get_user_projects(mock_get_projects, get_client, override_dependencies):
    mock_get_projects.return_value = [
        Project(id=1, name="Proj 1", version=1, total_size=0)
    ]

    response = get_client.get("/projects/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Proj 1"
    mock_get_projects.assert_called_once()


@patch("app.routers.projects.ProjectService.get_project_by_id")
def test_get_project_by_id(mock_get_project, get_client, override_dependencies):
    mock_get_project.return_value = Project(
        id=1, name="Proj 1", version=1, total_size=0
    )

    response = get_client.get("/projects/1")

    assert response.status_code == 200
    assert response.json()["name"] == "Proj 1"
    mock_get_project.assert_called_once()


@patch("app.routers.projects.ProjectService.get_project_by_id")
def test_get_project_by_id_not_found(
    mock_get_project, get_client, override_dependencies
):
    mock_get_project.return_value = None

    response = get_client.get("/projects/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"


@patch("app.routers.projects.ProjectService.update_project")
def test_update_project(mock_update, get_client, override_dependencies):
    mock_update.return_value = Project(id=1, name="Updated", version=1, total_size=0)

    response = get_client.put("/projects/1", json={"name": "Updated"})

    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


@patch("app.routers.projects.ProjectService.update_project")
def test_update_project_not_found(mock_update, get_client, override_dependencies):
    mock_update.return_value = None

    response = get_client.put("/projects/999", json={"name": "Updated"})

    assert response.status_code == 404


@patch("app.routers.projects.ProjectService.delete_project")
def test_delete_project(mock_delete, get_client, override_dependencies):
    mock_delete.return_value = True

    response = get_client.delete("/projects/1")

    assert response.status_code == 204


@patch("app.routers.projects.ProjectService.delete_project")
def test_delete_project_not_found(mock_delete, get_client, override_dependencies):
    mock_delete.return_value = False

    response = get_client.delete("/projects/999")

    assert response.status_code == 404


@patch("app.routers.projects.ProjectService.invite_user")
def test_send_invite(mock_invite, get_client, override_dependencies):
    mock_invite.return_value = (True, "Successfully invited")

    response = get_client.post(
        "/projects/1/invite/", json={"user_id": 2, "role": "participant"}
    )

    assert response.status_code == 200
    assert response.json() == "Successfully invited"


@patch("app.routers.projects.ProjectService.invite_user")
def test_send_invite_not_found(mock_invite, get_client, override_dependencies):
    mock_invite.return_value = (False, "User not found")

    response = get_client.post(
        "/projects/1/invite/", json={"user_id": 99, "role": "participant"}
    )

    assert response.status_code == 404


@patch("app.routers.projects.ProjectService.invite_user")
def test_send_invite_already_member(mock_invite, get_client, override_dependencies):
    mock_invite.return_value = (False, "User is already a member")

    response = get_client.post(
        "/projects/1/invite/", json={"user_id": 2, "role": "participant"}
    )

    assert response.status_code == 400


@patch("app.routers.projects.ProjectService.upload_document")
def test_upload_file(mock_upload, get_client, override_dependencies):
    mock_upload.return_value = Document(
        id=1, name="test.txt", size=10, doc_type="text/plain"
    )

    response = get_client.post(
        "/projects/1/documents", files={"file": ("test.txt", b"content", "text/plain")}
    )

    assert response.status_code == 201
    assert response.json()["name"] == "test.txt"


@patch("app.routers.projects.ProjectService.upload_document")
def test_upload_file_limit_exceeded(mock_upload, get_client, override_dependencies):
    mock_upload.side_effect = ValueError("Limited size of project")

    response = get_client.post(
        "/projects/1/documents", files={"file": ("test.txt", b"content", "text/plain")}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Limited size of project"


@patch("app.routers.projects.ProjectService.get_document")
def test_get_document(mock_get, get_client, override_dependencies):
    mock_get.return_value = Document(
        id=1, name="test.txt", size=10, doc_type="text/plain"
    )

    response = get_client.get("/projects/1/documents/1")

    assert response.status_code == 200
    assert response.json()["name"] == "test.txt"


@patch("app.routers.projects.ProjectService.get_document")
def test_get_document_not_found(mock_get, get_client, override_dependencies):
    mock_get.return_value = None

    response = get_client.get("/projects/1/documents/99")

    assert response.status_code == 404


@patch("app.routers.projects.ProjectService.get_documents")
def test_get_documents(mock_get_all, get_client, override_dependencies):
    mock_get_all.return_value = [
        Document(id=1, name="test.txt", size=10, doc_type="text/plain")
    ]

    response = get_client.get("/projects/1/documents")

    assert response.status_code == 200
    assert len(response.json()) == 1


@patch("app.routers.projects.ProjectService.update_document")
def test_update_document(mock_update, get_client, override_dependencies):
    mock_update.return_value = Document(
        id=1, name="test2.txt", size=10, doc_type="text/plain"
    )

    response = get_client.put(
        "/projects/1/documents/1",
        files={"file": ("test2.txt", b"content", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "test2.txt"


@patch("app.routers.projects.ProjectService.update_document")
def test_update_document_limit_exceeded(mock_update, get_client, override_dependencies):
    mock_update.side_effect = ValueError("Limited size of project")

    response = get_client.put(
        "/projects/1/documents/1",
        files={"file": ("test2.txt", b"content", "text/plain")},
    )

    assert response.status_code == 403


@patch("app.routers.projects.ProjectService.update_document")
def test_update_document_not_found(mock_update, get_client, override_dependencies):
    mock_update.return_value = None

    response = get_client.put(
        "/projects/1/documents/99",
        files={"file": ("test2.txt", b"content", "text/plain")},
    )

    assert response.status_code == 404


@patch("app.routers.projects.ProjectService.delete_document")
def test_delete_document(mock_delete, get_client, override_dependencies):
    mock_delete.return_value = True

    response = get_client.delete("/projects/1/documents/1")

    assert response.status_code == 204


@patch("app.routers.projects.ProjectService.delete_document")
def test_delete_document_not_found(mock_delete, get_client, override_dependencies):
    mock_delete.return_value = False

    response = get_client.delete("/projects/1/documents/99")

    assert response.status_code == 404
