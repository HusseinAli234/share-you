import pytest
from project.security import verify_password
@pytest
test_create_user():
    raw_password = "my_secret_password"
    user = create_user(login="test_user", password=raw_password)
    assert user.login == "test_user"
    assert user.hashed_password != raw_password
    assert verify_password(raw_password, user.hashed_password) is True