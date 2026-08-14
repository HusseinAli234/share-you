from unittest.mock import MagicMock, patch

import pytest

from app.models import User
from app.schemas.auth import RegisterForm
from app.services.auth_service import AuthService


@patch("app.services.auth_service.hashed_password")
def test_register_user_success(mock_hash, mock_db_session):
    mock_hash.return_value = "hashed_pw"
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    form = RegisterForm(
        login="newuser", password="password123", repeat_password="password123"
    )
    user = AuthService.register_user(mock_db_session, form)

    assert user is not None
    assert user.login == "newuser"
    assert user.hashed_password == "hashed_pw"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(user)


def test_register_user_already_exists(mock_db_session):
    existing_user = User(login="newuser")
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        existing_user
    )

    form = RegisterForm(
        login="newuser", password="password123", repeat_password="password123"
    )
    user = AuthService.register_user(mock_db_session, form)

    assert user is None
    mock_db_session.add.assert_not_called()


@patch("app.services.auth_service.verify")
@patch("app.services.auth_service.create_access_token")
def test_authenticate_user_success(mock_create_token, mock_verify, mock_db_session):
    mock_verify.return_value = True
    mock_create_token.return_value = "fake-jwt-token"

    user = User(login="testuser", hashed_password="hashed_pw")
    mock_db_session.query.return_value.filter.return_value.first.return_value = user

    token = AuthService.authenticate_user(mock_db_session, "testuser", "password123")

    assert token == "fake-jwt-token"
    mock_verify.assert_called_once_with("password123", "hashed_pw")
    mock_create_token.assert_called_once_with(user)


@patch("app.services.auth_service.verify")
def test_authenticate_user_invalid_password(mock_verify, mock_db_session):
    mock_verify.return_value = False

    user = User(login="testuser", hashed_password="hashed_pw")
    mock_db_session.query.return_value.filter.return_value.first.return_value = user

    token = AuthService.authenticate_user(mock_db_session, "testuser", "wrongpassword")

    assert token is None


def test_authenticate_user_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    token = AuthService.authenticate_user(mock_db_session, "testuser", "password123")
    assert token is None
