from unittest.mock import MagicMock
from app.main import app
from app.db.session import get_db

def fake_add(user):
    user.id = 1

def test_user_successful_registration(get_client):
    mock_db = MagicMock()
    
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    mock_db.add.side_effect = fake_add


    response = get_client.post("/auth/register", json={
        "login": "user",
        "password": "12345678",
        "repeat_password": "12345678"
    })
    assert response.json() == {"message": "Succesefully created!","id": 1}

    app.dependency_overrides.clear()