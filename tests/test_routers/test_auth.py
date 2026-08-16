from unittest.mock import MagicMock, patch

import pytest

from app.core.security import get_current_user
from app.main import app
from app.models import User


@pytest.fixture
def override_get_current_user():
    user = User(id=1, login="testuser")
    app.dependency_overrides[get_current_user] = lambda: user
    yield
    app.dependency_overrides.clear()


@patch("app.routers.auth.AuthService.register_user")
def test_register(mock_register, get_client):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_register.return_value = mock_user

    response = get_client.post(
        "/auth/register",
        json={
            "login": "newuser",
            "password": "password123",
            "repeat_password": "password123",
        },
    )

    assert response.status_code == 201
    assert response.json() == {"message": "Succesefully created!", "id": 1}
    mock_register.assert_called_once()


@patch("app.routers.auth.AuthService.register_user")
def test_register_already_exists(mock_register, get_client):
    mock_register.return_value = None

    response = get_client.post(
        "/auth/register",
        json={
            "login": "newuser",
            "password": "password123",
            "repeat_password": "password123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "User with this login already exist!"


@patch("app.routers.auth.AuthService.authenticate_user")
def test_login(mock_authenticate, get_client):
    mock_authenticate.return_value = "fake-jwt-token"

    response = get_client.post(
        "/auth/login", data={"username": "testuser", "password": "password123"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "fake-jwt-token",
        "token_type": "bearer",
        "message": "Successfully sign in",
    }


@patch("app.routers.auth.AuthService.authenticate_user")
def test_login_invalid(mock_authenticate, get_client):
    mock_authenticate.return_value = None

    response = get_client.post(
        "/auth/login", data={"username": "testuser", "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid sign in"


def test_get_user_me(get_client, override_get_current_user):
    response = get_client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["login"] == "testuser"
