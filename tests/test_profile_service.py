import pytest
from unittest.mock import MagicMock, patch

from services.profile_service import ProfileService
from exceptions.custom_exceptions import (
    TokenMissingException,
    TokenInvalidException,
    UserNotFoundException,
    NoPermissionException,
)


class DummyUser:
    def __init__(self, user_id=1, email="a@b.com", is_active=True, created_at=None):
        self.id = user_id
        self.email = email
        self.is_active = is_active
        self.created_at = created_at


class DummyRole:
    def __init__(self, code="USER"):
        self.code = code


def make_db_user(user_or_none):
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.first.return_value = user_or_none
    return db


def make_db_role(role_or_none):
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.join.return_value = q
    q.filter.return_value = q
    q.first.return_value = role_or_none
    return db


@patch("services.profile_service.decode_jwt_token", return_value=None)
def test_get_current_user_invalid_token(mock_decode):
    db = make_db_user(DummyUser())
    service = ProfileService(db)

    with pytest.raises(TokenInvalidException):
        service.get_current_user("Bearer bad")


def test_get_current_user_missing_token():
    db = make_db_user(DummyUser())
    service = ProfileService(db)

    with pytest.raises(TokenMissingException):
        service.get_current_user(None)


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 123})
def test_get_current_user_user_not_found(mock_decode):
    db = make_db_user(None)
    service = ProfileService(db)

    with pytest.raises(UserNotFoundException):
        service.get_current_user("Bearer ok")


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 123})
def test_get_current_user_success(mock_decode):
    user = DummyUser(user_id=123, email="x@y.com")
    db = make_db_user(user)
    service = ProfileService(db)

    res = service.get_current_user("Bearer ok")
    assert res.id == 123
    assert res.email == "x@y.com"


def test_ensure_admin_denied():
    db = make_db_role(DummyRole(code="USER"))
    service = ProfileService(db)
    user = DummyUser(user_id=1)

    with pytest.raises(NoPermissionException):
        service.ensure_admin(user)


def test_ensure_admin_success():
    db = make_db_role(DummyRole(code="ADMIN"))
    service = ProfileService(db)
    user = DummyUser(user_id=1)

    assert service.ensure_admin(user) is True


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 10})
def test_ensure_active_user_from_token_inactive(mock_decode):
    user = DummyUser(user_id=10, is_active=False)
    db = make_db_user(user)
    service = ProfileService(db)

    with pytest.raises(NoPermissionException):
        service.ensure_active_user_from_token("Bearer ok")


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 10})
def test_ensure_active_user_from_token_success(mock_decode):
    user = DummyUser(user_id=10, is_active=True)
    db = make_db_user(user)
    service = ProfileService(db)

    res = service.ensure_active_user_from_token("Bearer ok")
    assert res.id == 10
    assert res.is_active is True
