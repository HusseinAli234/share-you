from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def get_client():
    with patch("app.main.init_bucket"):
        with TestClient(app) as client:
            yield client


@pytest.fixture
def mock_db_session():
    return MagicMock()
