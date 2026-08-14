from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, UploadFile

from app.models.users import User
from app.utils.validators import (
    validate_file,
    validate_project_owner,
    validate_projects_member,
)


def test_validate_file_valid():
    file = MagicMock(spec=UploadFile)
    file.content_type = "application/pdf"

    result = validate_file(file)
    assert result == file


def test_validate_file_invalid():
    file = MagicMock(spec=UploadFile)
    file.content_type = "image/png"

    with pytest.raises(HTTPException) as exc:
        validate_file(file)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Unsupported file format!"


def test_validate_projects_member_valid(mock_db_session):
    user = User(id=1)
    mock_db_session.query.return_value.filter.return_value.scalar.return_value = 1

    result = validate_projects_member(project_id=1, user=user, db=mock_db_session)
    assert result == user


def test_validate_projects_member_invalid(mock_db_session):
    user = User(id=1)
    mock_db_session.query.return_value.filter.return_value.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        validate_projects_member(project_id=1, user=user, db=mock_db_session)

    assert exc.value.status_code == 403


def test_validate_project_owner_valid(mock_db_session):
    user = User(id=1)
    mock_db_session.query.return_value.filter.return_value.scalar.return_value = 1

    result = validate_project_owner(project_id=1, user=user, db=mock_db_session)
    assert result == user


def test_validate_project_owner_invalid(mock_db_session):
    user = User(id=1)
    mock_db_session.query.return_value.filter.return_value.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        validate_project_owner(project_id=1, user=user, db=mock_db_session)

    assert exc.value.status_code == 403
