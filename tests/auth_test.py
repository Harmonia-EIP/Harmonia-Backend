import pytest
from unittest.mock import MagicMock, patch

from services.auth_service import AuthService
from schemas.auth import SignInSchema
from exceptions.custom_exceptions import UserNotFoundException, InvalidCredentialsException

class DummyInfo:
    def __init__(self, username):
        self.username = username

class DummyUser:
    def __init__(self, user_id=1, email="a@b.com", password_hash="HASH", is_active=True, username="peyo"):
        self.id = user_id
        self.email = email
        self.password_hash = password_hash
        self.is_active = is_active
        self.info = DummyInfo(username)

def make_db_returning(user_or_none):
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.join.return_value = q
    q.first.return_value = user_or_none
    return db

@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_success(mock_verify, mock_jwt):
    db = make_db_returning(DummyUser(user_id=42, email="test@test.com", username="noe"))
    service = AuthService(db)

    payload = SignInSchema(identifier="test@test.com", password="1234")
    res = service.signin(payload)

    assert res["message"] == "Connexion réussie"
    assert res["user_id"] == 42
    assert res["email"] == "test@test.com"
    assert res["username"] == "noe"
    assert res["token"] == "TOKEN"

@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_user_not_found(mock_verify):
    db = make_db_returning(None)
    service = AuthService(db)

    payload = SignInSchema(identifier="test@test.com", password="1234")
    with pytest.raises(UserNotFoundException):
        service.signin(payload)

@patch("services.auth_service.pwd_context.verify", return_value=False)
def test_signin_invalid_password(mock_verify):
    db = make_db_returning(DummyUser())
    service = AuthService(db)

    payload = SignInSchema(identifier="test@test.com", password="bad")
    with pytest.raises(InvalidCredentialsException):
        service.signin(payload)
