import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from exceptions.custom_exceptions import (
    NoPermissionException,
    TokenInvalidException,
    UserNotFoundException,
)

from routes.profile import router as profile_router


def make_app():
    app = FastAPI()
    app.include_router(profile_router, prefix="/profile")
    return app


@pytest.fixture()
def client(monkeypatch):
    def fake_get_db():
        return MagicMock()

    monkeypatch.setattr("routes.profile.get_db", fake_get_db)
    return TestClient(make_app())


# =========================
# GET /profile/me
# =========================

def test_get_me_success(client, monkeypatch):
    fake_user = MagicMock(id=1)

    def fake_get_current_user(self, token):
        return fake_user

    def fake_get_profile(self, user):
        return {
            "id": 1,
            "first_name": "Peyo",
            "last_name": "Artigala",
            "username": "peyo",
            "email": "peyo@test.com",
            "created_at": "2026-01-01T00:00:00"
        }

    monkeypatch.setattr(
        "services.profile_service.ProfileService.get_current_user",
        fake_get_current_user
    )
    monkeypatch.setattr(
        "services.profile_service.ProfileService.get_profile",
        fake_get_profile
    )

    r = client.get("/profile/me", headers={"Authorization": "Bearer ok"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 1
    assert body["username"] == "peyo"


def test_get_me_missing_token(client):
    r = client.get("/profile/me")
    assert r.status_code == 401


def test_get_me_invalid_token(client, monkeypatch):
    def fake_get_current_user(self, token):
        raise TokenInvalidException()

    monkeypatch.setattr(
        "services.profile_service.ProfileService.get_current_user",
        fake_get_current_user
    )

    r = client.get("/profile/me", headers={"Authorization": "Bearer bad"})
    assert r.status_code == 401


def test_get_me_user_not_found(client, monkeypatch):
    def fake_get_current_user(self, token):
        raise UserNotFoundException()

    monkeypatch.setattr(
        "services.profile_service.ProfileService.get_current_user",
        fake_get_current_user
    )

    r = client.get("/profile/me", headers={"Authorization": "Bearer ok"})
    assert r.status_code == 404


# =========================
# GET /profile/{id}
# =========================

def test_get_user_profile_forbidden_if_not_admin(client, monkeypatch):
    fake_user = MagicMock(id=1)

    monkeypatch.setattr(
        "services.profile_service.ProfileService.get_current_user",
        lambda self, token: fake_user
    )

    def fake_ensure_admin(self, user):
        raise NoPermissionException("Admin role required")

    monkeypatch.setattr(
        "services.profile_service.ProfileService.ensure_admin",
        fake_ensure_admin
    )

    r = client.get("/profile/2", headers={"Authorization": "Bearer ok"})
    assert r.status_code == 403


def test_get_user_profile_success(client, monkeypatch):
    fake_user = MagicMock(id=1)

    monkeypatch.setattr(
        "services.profile_service.ProfileService.get_current_user",
        lambda self, token: fake_user
    )

    monkeypatch.setattr(
        "services.profile_service.ProfileService.ensure_admin",
        lambda self, user: True
    )

    monkeypatch.setattr(
        "services.profile_service.ProfileService.get_profile_by_id",
        lambda self, user_id: {
            "id": user_id,
            "username": "test",
            "email": "test@test.com",
            "first_name": "A",
            "last_name": "B",
            "created_at": "2026-01-01T00:00:00",
            "is_active": True,
            "role": "USER",
        }
    )

    r = client.get("/profile/2", headers={"Authorization": "Bearer ok"})
    assert r.status_code == 200
    assert r.json()["id"] == 2


# =========================
# PUT /profile/{id}/active
# =========================

def test_update_active_success(client, monkeypatch):
    fake_user = MagicMock(id=1)

    monkeypatch.setattr(
        "services.profile_service.ProfileService.get_current_user",
        lambda self, token: fake_user
    )
    monkeypatch.setattr(
        "services.profile_service.ProfileService.ensure_admin",
        lambda self, user: True
    )

    def fake_update_active_status(self, user_id, is_active):
        return {
            "id": user_id,
            "first_name": "A",
            "last_name": "B",
            "username": "u",
            "email": "e@e.com",
            "created_at": "2026-01-01T00:00:00",
            "is_active": is_active,
            "role": "USER",
        }

    monkeypatch.setattr(
        "services.profile_service.ProfileService.update_user_active_status",
        fake_update_active_status
    )

    r = client.put(
        "/profile/5/active",
        headers={"Authorization": "Bearer ok"},
        json={"is_active": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 5
    assert body["is_active"] is False


def test_update_active_forbidden(client, monkeypatch):
    fake_user = MagicMock(id=1)

    monkeypatch.setattr(
        "services.profile_service.ProfileService.get_current_user",
        lambda self, token: fake_user
    )

    def fake_ensure_admin(self, user):
        raise NoPermissionException()

    monkeypatch.setattr(
        "services.profile_service.ProfileService.ensure_admin",
        fake_ensure_admin
    )

    r = client.put(
        "/profile/5/active",
        headers={"Authorization": "Bearer ok"},
        json={"is_active": False},
    )

    assert r.status_code == 403


def test_update_active_user_not_found(client, monkeypatch):
    fake_user = MagicMock(id=1)

    monkeypatch.setattr(
        "services.profile_service.ProfileService.get_current_user",
        lambda self, token: fake_user
    )

    monkeypatch.setattr(
        "services.profile_service.ProfileService.ensure_admin",
        lambda self, user: True
    )

    def fake_update(self, user_id, is_active):
        raise UserNotFoundException()

    monkeypatch.setattr(
        "services.profile_service.ProfileService.update_user_active_status",
        fake_update
    )

    r = client.put(
        "/profile/5/active",
        headers={"Authorization": "Bearer ok"},
        json={"is_active": False},
    )

    assert r.status_code == 404


def test_update_active_invalid_body(client, monkeypatch):
    fake_user = MagicMock(id=1)

    monkeypatch.setattr(
        "services.profile_service.ProfileService.get_current_user",
        lambda self, token: fake_user
    )

    monkeypatch.setattr(
        "services.profile_service.ProfileService.ensure_admin",
        lambda self, user: True
    )

    r = client.put(
        "/profile/5/active",
        headers={"Authorization": "Bearer ok"},
        json={},
    )

    assert r.status_code == 422