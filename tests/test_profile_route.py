from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from exceptions.custom_exceptions import (
    ErrorCode,
    NoPermissionException,
    TokenMissingException,
)
from models.user_params import DEFAULT_PALETTE, build_palette
from routes.profile import router as profile_router
from schemas.profile import ProfileDetailsSchema, ProfileSchema
from schemas.user_params import UserParamsResponse
from tests.helpers import assert_error

HEADERS = {"Authorization": "Bearer tok"}
NOW = datetime.now(timezone.utc)


@pytest.fixture()
def client(make_client):
    return make_client(profile_router, prefix="/profile")


@pytest.fixture()
def service():
    with patch("routes.profile.ProfileService") as cls:
        svc = cls.return_value
        svc.get_current_user.return_value = SimpleNamespace(id=1, role_id=1)
        yield svc


def profile_schema():
    return ProfileSchema(
        id=1,
        first_name="John",
        last_name="Doe",
        username="johndoe",
        email="test@test.com",
        created_at=NOW,
        palette=build_palette(*DEFAULT_PALETTE),
        last_color_id=1,
    )


def details_schema(**overrides):
    data = dict(
        id=2,
        first_name="John",
        last_name="Doe",
        username="johndoe",
        email="test@test.com",
        created_at=NOW,
        is_active=True,
        role="USER",
        palette=build_palette(*DEFAULT_PALETTE),
        last_color_id=1,
    )
    data.update(overrides)
    return ProfileDetailsSchema(**data)


# ---------- GET /me ----------


def test_get_me(client, service):
    service.get_profile.return_value = profile_schema()

    res = client.get("/profile/me", headers=HEADERS)

    assert res.status_code == 200
    assert res.json()["username"] == "johndoe"
    service.get_current_user.assert_called_once_with("Bearer tok")


def test_get_me_without_header_passes_none(client, service):
    service.get_current_user.side_effect = TokenMissingException()

    res = client.get("/profile/me")

    assert_error(res, 401, ErrorCode.TOKEN_MISSING, "Missing token.")
    service.get_current_user.assert_called_once_with(None)


# ---------- GET /{id} ----------


def test_get_user_profile_admin(client, service):
    service.get_profile_by_id.return_value = details_schema()

    res = client.get("/profile/2", headers=HEADERS)

    assert res.status_code == 200
    assert res.json()["role"] == "USER"
    service.ensure_admin.assert_called_once()
    service.get_profile_by_id.assert_called_once_with(2)


def test_get_user_profile_non_admin_forbidden(client, service):
    service.ensure_admin.side_effect = NoPermissionException("Admin role required")

    res = client.get("/profile/2", headers=HEADERS)

    assert_error(res, 403, ErrorCode.NO_PERMISSION, "Admin role required")
    service.get_profile_by_id.assert_not_called()


def test_get_user_profile_invalid_id_is_422(client, service):
    res = client.get("/profile/abc", headers=HEADERS)

    assert_error(res, 422, ErrorCode.VALIDATION_ERROR)


# ---------- PUT /{id}/role ----------


def test_update_role(client, service):
    service.get_profile_by_id.return_value = details_schema(role="STAFF")

    res = client.put("/profile/2/role", json={"role": "STAFF"}, headers=HEADERS)

    assert res.status_code == 200
    assert res.json()["role"] == "STAFF"
    service.update_user_role.assert_called_once_with(2, "STAFF")
    service.ensure_admin.assert_called_once()


def test_update_role_forbidden(client, service):
    service.ensure_admin.side_effect = NoPermissionException("nope")

    res = client.put("/profile/2/role", json={"role": "STAFF"}, headers=HEADERS)

    assert_error(res, 403, ErrorCode.NO_PERMISSION, "nope")
    service.update_user_role.assert_not_called()


def test_update_role_missing_body_is_422(client, service):
    res = client.put("/profile/2/role", json={}, headers=HEADERS)

    assert_error(res, 422, ErrorCode.VALIDATION_ERROR)


# ---------- PUT /{id}/active ----------


@pytest.mark.parametrize("active", [True, False])
def test_update_active(client, service, active):
    service.update_user_active_status.return_value = details_schema(is_active=active)

    res = client.put("/profile/2/active", json={"is_active": active}, headers=HEADERS)

    assert res.status_code == 200
    assert res.json()["is_active"] is active
    service.update_user_active_status.assert_called_once_with(2, active)


def test_update_active_forbidden(client, service):
    service.ensure_admin.side_effect = NoPermissionException("nope")

    res = client.put("/profile/2/active", json={"is_active": False}, headers=HEADERS)

    assert_error(res, 403, ErrorCode.NO_PERMISSION, "nope")
    service.update_user_active_status.assert_not_called()


def test_update_active_missing_body_is_422(client, service):
    res = client.put("/profile/2/active", json={}, headers=HEADERS)

    assert_error(res, 422, ErrorCode.VALIDATION_ERROR)


# ---------- PUT /{id}/palette ----------


def test_update_palette(client, service):
    service.update_palette.return_value = UserParamsResponse(
        user_id=1, palette=build_palette(*DEFAULT_PALETTE), last_color_id=2
    )

    res = client.put(
        "/profile/1/palette",
        json={"colors": [{"id": 1, "color": "#FF0000"}], "last_color_id": 2},
        headers=HEADERS,
    )

    assert res.status_code == 200
    assert res.json()["last_color_id"] == 2
    current, user_id, payload = service.update_palette.call_args.args
    assert user_id == 1
    assert payload.last_color_id == 2
    assert payload.colors[0].color.upper() == "#FF0000"


def test_update_palette_forbidden(client, service):
    service.update_palette.side_effect = NoPermissionException("only yours")

    res = client.put("/profile/9/palette", json={"last_color_id": 1}, headers=HEADERS)

    assert_error(res, 403, ErrorCode.NO_PERMISSION, "only yours")


@pytest.mark.parametrize(
    "body",
    [
        {},  # au moins un champ requis
        {"last_color_id": 99},  # id hors 1..3
        {"colors": [{"id": 1, "color": "not-a-hex"}]},
        {"colors": [{"id": 7, "color": "#FFFFFF"}]},
    ],
)
def test_update_palette_invalid_body_is_422(client, service, body):
    res = client.put("/profile/1/palette", json=body, headers=HEADERS)

    assert_error(res, 422, ErrorCode.VALIDATION_ERROR)
    service.update_palette.assert_not_called()
