from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from exceptions.custom_exceptions import (
    InvalidCredentialsException,
    NoPermissionException,
    TokenInvalidException,
    TokenMissingException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from models.user_params import DEFAULT_PALETTE, build_palette
from models.role import ROLE_ADMIN_ID, ROLE_STAFF_ID, ROLE_USER_ID
from services.profile_service import ProfileService
from utils.jwt_handler import decode_jwt_token

AVATAR_URL = "https://api.test/uploads/avatars/1-abc.png"

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
        token_version=0,
    )


def make_info(username="johndoe", avatar_url=None):
    return SimpleNamespace(
        user_id=1,
        first_name="John",
        last_name="Doe",
        username=username,
        avatar_url=avatar_url,
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


def make_db_seq(*results):
    """db.query(...).filter(...).first() renvoie les résultats dans l'ordre."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = list(results)
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
# get_or_create_params
# =========================


def test_get_or_create_params_returns_existing():
    params = make_params()
    db = make_db(params=params)
    assert ProfileService(db).get_or_create_params(1) is params
    assert not db.add.called
    assert not db.commit.called


def test_get_or_create_params_creates_default():
    db = make_db(params=None)
    result = ProfileService(db).get_or_create_params(5)

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
    info = make_info(avatar_url=AVATAR_URL)
    db = make_db(user=user, info=info, params=make_params(last_color_id=3))

    result = ProfileService(db).get_profile(user)

    assert result.id == 1
    assert result.first_name == "John"
    assert result.last_name == "Doe"
    assert result.username == "johndoe"
    assert result.email == "test@test.com"
    assert result.avatar_url == AVATAR_URL
    assert result.last_color_id == 3
    assert result.palette is not None
    assert isinstance(result.created_at, datetime)


def test_get_profile_without_avatar_is_none():
    user = make_user()
    db = make_db(user=user, info=make_info(avatar_url=None), params=make_params())

    result = ProfileService(db).get_profile(user)

    assert result.avatar_url is None


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


def make_history_entry(entry_id=1, model_id=None, model_name=None):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=entry_id,
        name="Sunset vibes",
        type="generate",
        parameters={"gain": 0.5},
        model_id=model_id,
        model_name=model_name,
        created_at=now,
        last_used_at=now,
    )


@patch("services.profile_service.HistoryService")
def test_get_profile_history_includes_model(history_cls):
    user = make_user()
    db = make_db(user=user, info=make_info(), params=make_params())
    history_cls.return_value.list_for_user.return_value = [
        make_history_entry(1, model_id="3", model_name="Mistral 7B"),
        make_history_entry(2),  # entrée antérieure à la migration
    ]

    result = ProfileService(db).get_profile(user)

    history_cls.return_value.list_for_user.assert_called_once_with(user.id)
    assert [h.id for h in result.history] == [1, 2]
    assert result.history[0].model_id == "3"
    assert result.history[0].model_name == "Mistral 7B"
    assert result.history[1].model_id is None
    assert result.history[1].model_name is None


@patch("services.profile_service.HistoryService")
def test_get_profile_history_model_in_json(history_cls):
    user = make_user()
    db = make_db(user=user, info=make_info(), params=make_params())
    history_cls.return_value.list_for_user.return_value = [
        make_history_entry(1, model_id="3", model_name="Mistral 7B"),
    ]

    data = ProfileService(db).get_profile(user).model_dump(mode="json")

    assert data["history"][0]["model_id"] == "3"
    assert data["history"][0]["model_name"] == "Mistral 7B"


def test_get_profile_handles_partial_data_should_fail():
    user = make_user()
    db = make_db(user=user, info=make_info(username=None), params=make_params())
    with pytest.raises(ValueError):  # pydantic.ValidationError hérite de ValueError
        ProfileService(db).get_profile(user)


# =========================
# update_profile
# =========================


def changes_schema(**changes):
    return SimpleNamespace(model_dump=lambda exclude_unset=True: changes)


def test_update_profile_info_missing():
    db = make_db_seq(None)
    with pytest.raises(UserNotFoundException):
        ProfileService(db).update_profile(make_user(), changes_schema(first_name="A"))


def test_update_profile_applies_only_sent_fields():
    info = make_info()
    db = make_db_seq(info)
    svc = ProfileService(db)

    with patch.object(svc, "get_profile", return_value="PROFILE") as gp:
        result = svc.update_profile(make_user(), changes_schema(first_name="Alice"))

    assert info.first_name == "Alice"
    assert info.last_name == "Doe"  # inchangé
    assert db.commit.called
    db.refresh.assert_called_once_with(info)
    assert result == "PROFILE"
    gp.assert_called_once()


def test_update_profile_username_taken():
    db = make_db_seq(make_info(), SimpleNamespace(user_id=2))
    with pytest.raises(UserAlreadyExistsException):
        ProfileService(db).update_profile(make_user(), changes_schema(username="taken"))
    assert not db.commit.called


def test_update_profile_username_free():
    info = make_info()
    db = make_db_seq(info, None)
    svc = ProfileService(db)

    with patch.object(svc, "get_profile"):
        svc.update_profile(make_user(), changes_schema(username="newname"))

    assert info.username == "newname"


def test_update_profile_same_username_skips_uniqueness_check():
    info = make_info(username="johndoe")
    db = make_db_seq(info)  # une seule requête : pas de contrôle d'unicité
    svc = ProfileService(db)

    with patch.object(svc, "get_profile"):
        svc.update_profile(make_user(), changes_schema(username="johndoe"))

    assert db.query.call_count == 1


# =========================
# update_email
# =========================


def make_account(email="old@test.com"):
    return SimpleNamespace(id=1, email=email, password_hash="hash", token_version=0)


@patch("services.profile_service.verify_password", return_value=False)
def test_update_email_wrong_password(mock_verify):
    db = make_db()
    with pytest.raises(InvalidCredentialsException):
        ProfileService(db).update_email(
            make_account(),
            SimpleNamespace(current_password="bad", new_email="new@test.com"),
        )
    assert not db.commit.called


@patch("services.profile_service.verify_password", return_value=True)
def test_update_email_already_used(mock_verify):
    db = make_db_seq(SimpleNamespace(id=2))
    user = make_account()
    with pytest.raises(UserAlreadyExistsException):
        ProfileService(db).update_email(
            user, SimpleNamespace(current_password="ok", new_email="used@test.com")
        )
    assert user.email == "old@test.com"
    assert not db.commit.called


@patch("services.profile_service.verify_password", return_value=True)
def test_update_email_success(mock_verify):
    db = make_db_seq(None)
    user = make_account()
    svc = ProfileService(db)

    with patch.object(svc, "get_profile", return_value="PROFILE"):
        result = svc.update_email(
            user, SimpleNamespace(current_password="ok", new_email="new@test.com")
        )

    assert user.email == "new@test.com"
    assert db.commit.called
    db.refresh.assert_called_once_with(user)
    assert result == "PROFILE"


@patch("services.profile_service.verify_password", return_value=True)
def test_update_email_same_email_is_noop(mock_verify):
    db = make_db()
    user = make_account(email="same@test.com")
    svc = ProfileService(db)

    with patch.object(svc, "get_profile", return_value="PROFILE"):
        svc.update_email(
            user, SimpleNamespace(current_password="ok", new_email="same@test.com")
        )

    assert not db.commit.called


# =========================
# update_password
# =========================


@patch("services.profile_service.verify_password", return_value=False)
def test_update_password_wrong_current(mock_verify):
    db = make_db()
    user = make_account()
    with pytest.raises(InvalidCredentialsException):
        ProfileService(db).update_password(
            user, SimpleNamespace(current_password="bad", new_password="newpass123")
        )
    assert user.password_hash == "hash"
    assert not db.commit.called


@patch("services.profile_service.hash_password", return_value="NEWHASH")
@patch("services.profile_service.verify_password", return_value=True)
def test_update_password_success(mock_verify, mock_hash):
    db = make_db()
    user = make_account()

    token = ProfileService(db).update_password(
        user, SimpleNamespace(current_password="ok", new_password="newpass123")
    )

    mock_hash.assert_called_once_with("newpass123")
    assert user.password_hash == "NEWHASH"
    assert db.commit.called
    # anciens tokens révoqués, le nouveau porte la nouvelle version
    assert user.token_version == 1
    payload = decode_jwt_token(token)
    assert payload["sub"] == "1"
    assert payload["ver"] == 1


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
# ensure_admin
# =========================


def test_ensure_admin():
    svc = ProfileService(make_db())
    svc.ensure_admin(make_user(role_id=ROLE_ADMIN_ID))  # ne lève rien
    for role in (ROLE_STAFF_ID, ROLE_USER_ID):
        with pytest.raises(NoPermissionException):
            svc.ensure_admin(make_user(role_id=role))


# =========================
# get_profile_by_id
# =========================


def test_get_profile_by_id_success():
    user = make_user(role_id=ROLE_STAFF_ID)
    db = make_db(user=user, info=make_info(avatar_url=AVATAR_URL), params=make_params())

    result = ProfileService(db).get_profile_by_id(1)

    assert result.id == 1
    assert result.role == "STAFF"
    assert result.is_active is True
    assert result.username == "johndoe"
    assert result.avatar_url == AVATAR_URL


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
    admin = make_user(user_id=1, role_id=ROLE_ADMIN_ID)
    user = make_user(user_id=5, role_id=ROLE_USER_ID)
    db = make_db(user=user, info=make_info(), params=make_params())

    result = ProfileService(db).update_user_role(admin, 5, "STAFF")

    assert user.role_id == ROLE_STAFF_ID
    assert result.role == "STAFF"
    assert db.commit.called
    db.refresh.assert_called_with(user)


def test_update_user_role_on_self_is_forbidden():
    admin = make_user(user_id=1, role_id=ROLE_ADMIN_ID)
    db = make_db(user=admin)
    with pytest.raises(NoPermissionException):
        ProfileService(db).update_user_role(admin, 1, "USER")
    assert admin.role_id == ROLE_ADMIN_ID
    assert not db.commit.called


def test_update_user_role_user_not_found():
    admin = make_user(user_id=1)
    with pytest.raises(UserNotFoundException):
        ProfileService(make_db(user=None)).update_user_role(admin, 5, "ADMIN")


# =========================
# update_user_active_status
# =========================


@pytest.mark.parametrize("active", [True, False])
def test_update_user_active_status(active):
    admin = make_user(user_id=1)
    user = make_user(user_id=5, is_active=not active)
    db = make_db(user=user, info=make_info(), params=make_params())

    result = ProfileService(db).update_user_active_status(admin, 5, active)

    assert user.is_active is active
    assert result.is_active is active
    assert db.commit.called


def test_update_user_active_on_self_is_forbidden():
    admin = make_user(user_id=1)
    db = make_db(user=admin)
    with pytest.raises(NoPermissionException):
        ProfileService(db).update_user_active_status(admin, 1, False)
    assert admin.is_active is True
    assert not db.commit.called


def test_update_user_active_not_found():
    admin = make_user(user_id=1)
    with pytest.raises(UserNotFoundException):
        ProfileService(make_db(user=None)).update_user_active_status(admin, 5, False)


# =========================
# get_current_user : comptes désactivés et tokens révoqués
# =========================


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 1})
def test_get_current_user_inactive_user_is_rejected(mock_decode):
    db = make_db(user=make_user(is_active=False))
    with pytest.raises(NoPermissionException):
        ProfileService(db).get_current_user("Bearer tok")


@pytest.mark.parametrize("payload_ver", [0, None])
@patch("services.profile_service.decode_jwt_token")
def test_get_current_user_revoked_token(mock_decode, payload_ver):
    """Token émis avant un changement de mot de passe (version plus ancienne)."""
    mock_decode.return_value = (
        {"sub": 1} if payload_ver is None else {"sub": 1, "ver": payload_ver}
    )
    user = make_user()
    user.token_version = 2
    with pytest.raises(TokenInvalidException):
        ProfileService(make_db(user=user)).get_current_user("tok")


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 1, "ver": 3})
def test_get_current_user_current_token_version(mock_decode):
    user = make_user()
    user.token_version = 3
    assert ProfileService(make_db(user=user)).get_current_user("tok") is user


@patch("services.profile_service.decode_jwt_token", return_value={"sub": 1})
def test_get_current_user_legacy_token_without_version(mock_decode):
    """Les tokens émis avant l'ajout de "ver" restent valides (version 0)."""
    user = make_user()
    assert ProfileService(make_db(user=user)).get_current_user("tok") is user
