from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from exceptions.custom_exceptions import (
    NoPermissionException,
    TokenInvalidException,
    TokenMissingException,
    UserNotFoundException,
)
from models.user_params import DEFAULT_PALETTE, build_palette
from services.profile_service import (
    ROLE_ADMIN_ID,
    ROLE_STAFF_ID,
    ROLE_USER_ID,
    ProfileService,
)

# =========================
# HELPERS
# =========================


def make_user(user_id=1, role_id=ROLE_ADMIN_ID, is_active=True):
    return SimpleNamespace(
        id=user_id,
        email="test@test.com",
        created_at=datetime.now(timezone.utc),
        is_active=is_active,
        role_id=role_id,
    )


def make_info(username="johndoe"):
    return SimpleNamespace(
        user_id=1, first_name="John", last_name="Doe", username=username
    )


def make_params(last_color_id=2):
    p = MagicMock()
    p.palette = build_palette(*DEFAULT_PALETTE)
    p.last_color_id = last_color_id
    return p


def make_db(user=None, info=None, params=None):
    db = MagicMock()
    mapping = {"User": user, "UserInfo": info, "UserParams": params}

    def query_side_effect(model):
        q = MagicMock()
        q.filter.return_value.first.return_value = mapping.get(model.__name__)
        return q

    db.query.side_effect = query_side_effect
    return db


# =========================
# get_current_user
# =========================


@pytest.mark.parametrize("token", [None, ""])
def test_get_current_user_missing_token(token):
    with pytest.raises(TokenMissingException):
        ProfileService(make_db()).get_current_user(token)


@patch("services.profile_service.decode_jwt_token", return_value=None)
def test_get_current_user_invalid_token(mock_decode):
    with pytest.raises(TokenInvalidException):
        ProfileService(make_db()).get_current_user("garbage")


@pytest.mark.parametrize("payload", [{}, {"sub": None}, {"sub": 0}, {"sub": ""}])
@patch("services.profile_service.decode_jwt_token")
def test_get_current_user_payload_without_sub(mock_decode, payload):
    mock_decode.return_value = payload
    with pytest.raises(TokenInvalidException):
        ProfileService(make_db()).get_current_user("tok")


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 1})
def test_get_current_user_user_not_found(mock_decode):
    with pytest.raises(UserNotFoundException):
        ProfileService(make_db(user=None)).get_current_user("tok")


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 1})
def test_get_current_user_success_strips_bearer(mock_decode):
    user = make_user()
    result = ProfileService(make_db(user=user)).get_current_user("Bearer abc.def")
    assert result is user
    mock_decode.assert_called_once_with("abc.def")


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 1})
def test_get_current_user_raw_token(mock_decode):
    user = make_user()
    assert ProfileService(make_db(user=user)).get_current_user("abc") is user
    mock_decode.assert_called_once_with("abc")


# =========================
# _get_or_create_params
# =========================


def test_get_or_create_params_returns_existing():
    params = make_params()
    db = make_db(params=params)
    assert ProfileService(db)._get_or_create_params(1) is params
    assert not db.add.called
    assert not db.commit.called


def test_get_or_create_params_creates_default():
    db = make_db(params=None)
    result = ProfileService(db)._get_or_create_params(5)

    assert result.user_id == 5
    assert result.last_color_id == 1
    db.add.assert_called_once_with(result)
    assert db.commit.called
    db.refresh.assert_called_once_with(result)


# =========================
# get_profile
# =========================


def test_get_profile_success():
    user = make_user()
    db = make_db(user=user, info=make_info(), params=make_params(last_color_id=3))

    result = ProfileService(db).get_profile(user)

    assert result.id == 1
    assert result.first_name == "John"
    assert result.last_name == "Doe"
    assert result.username == "johndoe"
    assert result.email == "test@test.com"
    assert result.last_color_id == 3
    assert result.palette is not None
    assert isinstance(result.created_at, datetime)


def test_get_profile_without_params_creates_them():
    user = make_user()
    db = make_db(user=user, info=make_info(), params=None)

    result = ProfileService(db).get_profile(user)

    assert result.id == 1
    assert result.last_color_id == 1
    assert db.add.called
    assert db.commit.called


def test_get_profile_user_info_missing():
    user = make_user()
    with pytest.raises(UserNotFoundException):
        ProfileService(make_db(user=user, info=None)).get_profile(user)


def test_get_profile_handles_partial_data_should_fail():
    user = make_user()
    db = make_db(user=user, info=make_info(username=None), params=make_params())
    with pytest.raises(ValueError):  # pydantic.ValidationError hérite de ValueError
        ProfileService(db).get_profile(user)


# =========================
# update_palette
# =========================


def palette_data(colors=None, last_color_id=None):
    return SimpleNamespace(colors=colors, last_color_id=last_color_id)


def test_update_palette_self_colors_and_last_color():
    current = make_user(user_id=2, role_id=ROLE_USER_ID)
    params = make_params()
    db = make_db(user=current, params=params)
    data = palette_data(
        colors=[
            SimpleNamespace(id=1, color="#FF0000"),
            SimpleNamespace(id=3, color="#00FF00"),
        ],
        last_color_id=3,
    )

    result = ProfileService(db).update_palette(current, 2, data)

    params.set_color.assert_any_call(1, "#FF0000")
    params.set_color.assert_any_call(3, "#00FF00")
    assert params.set_color.call_count == 2
    assert params.last_color_id == 3
    assert db.commit.called
    db.refresh.assert_called_once_with(params)
    assert result.user_id == 2
    assert result.last_color_id == 3


def test_update_palette_only_last_color():
    current = make_user(user_id=2, role_id=ROLE_USER_ID)
    params = make_params(last_color_id=1)
    db = make_db(user=current, params=params)

    ProfileService(db).update_palette(current, 2, palette_data(last_color_id=2))

    assert not params.set_color.called
    assert params.last_color_id == 2


def test_update_palette_only_colors_keeps_last_color():
    current = make_user(user_id=2, role_id=ROLE_USER_ID)
    params = make_params(last_color_id=2)
    db = make_db(user=current, params=params)

    ProfileService(db).update_palette(
        current, 2, palette_data(colors=[SimpleNamespace(id=2, color="#123456")])
    )

    params.set_color.assert_called_once_with(2, "#123456")
    assert params.last_color_id == 2


def test_update_palette_admin_on_other_user():
    admin = make_user(user_id=1, role_id=ROLE_ADMIN_ID)
    target = make_user(user_id=9, role_id=ROLE_USER_ID)
    params = make_params()
    db = make_db(user=target, params=params)

    result = ProfileService(db).update_palette(admin, 9, palette_data(last_color_id=1))

    assert result.user_id == 9


@pytest.mark.parametrize("role", [ROLE_STAFF_ID, ROLE_USER_ID])
def test_update_palette_forbidden_for_other_user(role):
    current = make_user(user_id=2, role_id=role)
    db = make_db(user=make_user(user_id=9))
    with pytest.raises(NoPermissionException):
        ProfileService(db).update_palette(current, 9, palette_data(last_color_id=1))
    assert not db.commit.called


def test_update_palette_target_not_found():
    admin = make_user(role_id=ROLE_ADMIN_ID)
    with pytest.raises(UserNotFoundException):
        ProfileService(make_db(user=None)).update_palette(
            admin, 99, palette_data(last_color_id=1)
        )


# =========================
# ensure_admin / ensure_staff_or_admin
# =========================


def test_ensure_admin():
    svc = ProfileService(make_db())
    assert svc.ensure_admin(make_user(role_id=ROLE_ADMIN_ID)) is True
    for role in (ROLE_STAFF_ID, ROLE_USER_ID):
        with pytest.raises(NoPermissionException):
            svc.ensure_admin(make_user(role_id=role))


def test_ensure_staff_or_admin():
    svc = ProfileService(make_db())
    assert svc.ensure_staff_or_admin(make_user(role_id=ROLE_ADMIN_ID)) is True
    assert svc.ensure_staff_or_admin(make_user(role_id=ROLE_STAFF_ID)) is True
    with pytest.raises(NoPermissionException):
        svc.ensure_staff_or_admin(make_user(role_id=ROLE_USER_ID))


# =========================
# role code <-> id
# =========================


@pytest.mark.parametrize(
    "role_id,code",
    [(1, "ADMIN"), (2, "STAFF"), (3, "USER"), (99, None), (None, None)],
)
def test_role_code_from_id(role_id, code):
    assert ProfileService(make_db())._role_code_from_id(role_id) == code


@pytest.mark.parametrize(
    "code,role_id",
    [
        ("ADMIN", 1),
        ("admin", 1),
        ("  Staff ", 2),
        ("USER", 3),
        ("nope", None),
        ("", None),
        (None, None),
    ],
)
def test_role_id_from_code(code, role_id):
    assert ProfileService(make_db())._role_id_from_code(code) == role_id


# =========================
# get_profile_by_id
# =========================


def test_get_profile_by_id_success():
    user = make_user(role_id=ROLE_STAFF_ID)
    db = make_db(user=user, info=make_info(), params=make_params())

    result = ProfileService(db).get_profile_by_id(1)

    assert result.id == 1
    assert result.role == "STAFF"
    assert result.is_active is True
    assert result.username == "johndoe"


def test_get_profile_by_id_user_not_found():
    with pytest.raises(UserNotFoundException):
        ProfileService(make_db(user=None)).get_profile_by_id(1)


def test_get_profile_by_id_info_missing():
    with pytest.raises(UserNotFoundException):
        ProfileService(make_db(user=make_user(), info=None)).get_profile_by_id(1)


# =========================
# update_user_role
# =========================


def test_update_user_role_success():
    user = make_user(role_id=ROLE_USER_ID)
    db = make_db(user=user, info=make_info(), params=make_params())

    result = ProfileService(db).update_user_role(1, "staff")

    assert user.role_id == ROLE_STAFF_ID
    assert result.role == "STAFF"
    assert db.commit.called
    db.refresh.assert_called_with(user)


def test_update_user_role_invalid_code():
    user = make_user(role_id=ROLE_USER_ID)
    db = make_db(user=user, info=make_info(), params=make_params())
    with pytest.raises(ValueError):
        ProfileService(db).update_user_role(1, "king")
    assert user.role_id == ROLE_USER_ID
    assert not db.commit.called


def test_update_user_role_user_not_found():
    with pytest.raises(UserNotFoundException):
        ProfileService(make_db(user=None)).update_user_role(1, "ADMIN")


# =========================
# update_user_active_status
# =========================


@pytest.mark.parametrize("active", [True, False])
def test_update_user_active_status(active):
    user = make_user(is_active=not active)
    db = make_db(user=user, info=make_info(), params=make_params())

    result = ProfileService(db).update_user_active_status(1, active)

    assert user.is_active is active
    assert result.is_active is active
    assert db.commit.called


def test_update_user_active_not_found():
    with pytest.raises(UserNotFoundException):
        ProfileService(make_db(user=None)).update_user_active_status(1, False)


# =========================
# ensure_active_user_from_token
# =========================


@pytest.mark.parametrize("token", [None, ""])
def test_ensure_active_missing_token(token):
    with pytest.raises(TokenMissingException):
        ProfileService(make_db()).ensure_active_user_from_token(token)


@patch("services.profile_service.decode_jwt_token", return_value=None)
def test_ensure_active_invalid_token(mock_decode):
    with pytest.raises(TokenInvalidException):
        ProfileService(make_db()).ensure_active_user_from_token("bad")


@patch("services.profile_service.decode_jwt_token", return_value={})
def test_ensure_active_payload_without_sub(mock_decode):
    with pytest.raises(TokenInvalidException):
        ProfileService(make_db()).ensure_active_user_from_token("tok")


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 1})
def test_ensure_active_user_not_found(mock_decode):
    with pytest.raises(UserNotFoundException):
        ProfileService(make_db(user=None)).ensure_active_user_from_token("tok")


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 1})
def test_ensure_active_inactive_user(mock_decode):
    db = make_db(user=make_user(is_active=False))
    with pytest.raises(NoPermissionException):
        ProfileService(db).ensure_active_user_from_token("Bearer tok")


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 1})
def test_ensure_active_success(mock_decode):
    user = make_user()

    result = ProfileService(make_db(user=user)).ensure_active_user_from_token(
        "Bearer tok"
    )

    assert result is user
    mock_decode.assert_called_once_with("tok")
