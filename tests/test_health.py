import pytest

from tests.conftest import get_client


def test_health_check(get_client):
    response = get_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
