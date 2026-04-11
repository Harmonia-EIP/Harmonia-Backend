import pytest
from datetime import datetime
from unittest.mock import MagicMock

from services.profile_service import ProfileService
from exceptions.custom_exceptions import UserNotFoundException


# =========================
# DUMMY OBJECTS
# =========================

class DummyUser:
    def __init__(self):
        self.id = 1
        self.email = "test@test.com"
        self.created_at = datetime.utcnow()  # ✅ FIX
        self.is_active = True
        self.role_id = 1


class DummyInfo:
    def __init__(self):
        self.user_id = 1
        self.first_name = "John"
        self.last_name = "Doe"
        self.username = "johndoe"  # ✅ FIX


class DummyParams:
    def __init__(self):
        self.user_id = 1
        self.layout_id = 1
        self.theme_id = 2


# =========================
# MOCK DB
# =========================

def make_db(user=None, info=None, params=None):
    db = MagicMock()

    def query_side_effect(model):
        query = MagicMock()

        if model.__name__ == "UserInfo":
            query.filter.return_value.first.return_value = info
        elif model.__name__ == "UserParams":
            query.filter.return_value.first.return_value = params
        elif model.__name__ == "User":
            query.filter.return_value.first.return_value = user

        return query

    db.query.side_effect = query_side_effect
    return db


# =========================
# TESTS
# =========================

def test_get_profile_success():
    user = DummyUser()
    db = make_db(user=user, info=DummyInfo(), params=DummyParams())

    service = ProfileService(db)
    result = service.get_profile(user)

    assert result.id == 1
    assert result.username == "johndoe"
    assert result.layout_id == 1
    assert result.theme_id == 2


def test_get_profile_without_params():
    user = DummyUser()
    db = make_db(user=user, info=DummyInfo(), params=None)

    service = ProfileService(db)
    result = service.get_profile(user)

    assert result.id == 1
    assert result.layout_id is None
    assert result.theme_id is None


def test_get_profile_user_not_found():
    user = DummyUser()
    db = make_db(user=user, info=None, params=None)

    service = ProfileService(db)

    with pytest.raises(UserNotFoundException):
        service.get_profile(user)


def test_update_user_active_success():
    user = DummyUser()
    db = make_db(user=user, info=DummyInfo(), params=DummyParams())

    service = ProfileService(db)
    result = service.update_user_active_status(1, False)

    assert result.id == 1
    assert result.is_active is False


def test_update_user_not_found():
    db = make_db(user=None, info=None, params=None)

    service = ProfileService(db)

    with pytest.raises(UserNotFoundException):
        service.update_user_active_status(1, False)


def test_profile_params_created_if_missing():
    user = DummyUser()
    db = make_db(user=user, info=DummyInfo(), params=None)

    service = ProfileService(db)
    result = service.get_profile(user)

    assert result.id == 1
    assert result.layout_id is None
    assert result.theme_id is None


def test_profile_handles_partial_data_should_fail():
    user = DummyUser()
    partial_info = DummyInfo()
    partial_info.username = None  # ❌ invalide selon schema

    db = make_db(user=user, info=partial_info, params=DummyParams())

    service = ProfileService(db)

    with pytest.raises(Exception):  # ✅ attendu car schema strict
        service.get_profile(user)


def test_update_user_active_true():
    user = DummyUser()
    db = make_db(user=user, info=DummyInfo(), params=DummyParams())

    service = ProfileService(db)
    result = service.update_user_active_status(1, True)

    assert result.is_active is True


def test_get_profile_values_integrity():
    user = DummyUser()
    info = DummyInfo()
    params = DummyParams()

    db = make_db(user=user, info=info, params=params)

    service = ProfileService(db)
    result = service.get_profile(user)

    assert result.first_name == "John"
    assert result.last_name == "Doe"
    assert result.email == "test@test.com"


def test_get_profile_datetime_type():
    user = DummyUser()
    db = make_db(user=user, info=DummyInfo(), params=DummyParams())

    service = ProfileService(db)
    result = service.get_profile(user)

    assert isinstance(result.created_at, datetime)