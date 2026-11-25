"""AuthService (signin / signup) et route /auth/signin : sécurité du login."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from exceptions.custom_exceptions import (
    ErrorCode,
    InvalidCredentialsException,
    UserAlreadyExistsException,
)
from routes.auth import router as auth_router
from schemas.auth import SignInSchema, SignUpSchema
from services.auth_service import AuthService
from tests.helpers import assert_error
from utils.jwt_handler import decode_jwt_token

SIGNUP = {
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "email": "john@test.com",
    "password": "secret123",
}


def make_user(is_active=True, token_version=0):
    return SimpleNamespace(
        id=1,
        email="john@test.com",
        password_hash="hash",
        is_active=is_active,
        token_version=token_version,
        info=SimpleNamespace(username="johndoe", avatar_url=None),
    )


def db_returning(user):
    """db.query(...)[.join(...)].filter(...).first() -> user"""
    db = MagicMock()
    q = db.query.return_value
    q.filter.return_value.first.return_value = user
    q.join.return_value.filter.return_value.first.return_value = user
    return db


def signin(db, identifier="john@test.com", password="secret123"):
    return AuthService(db).signin(
        SignInSchema(identifier=identifier, password=password)
    )


# ---------------- signin ----------------


@patch("services.auth_service.burn_password_check")
def test_signin_unknown_user_is_401_like_a_wrong_password(burn):
    with pytest.raises(InvalidCredentialsException) as unknown:
        signin(db_returning(None))

    with (
        patch("services.auth_service.verify_password", return_value=False),
        pytest.raises(InvalidCredentialsException) as wrong_pwd,
    ):
        signin(db_returning(make_user()))

    # Même status, même code, même message : impossible de savoir si le
    # compte existe.
    assert unknown.value.status_code == wrong_pwd.value.status_code == 401
    assert unknown.value.detail == wrong_pwd.value.detail == "Invalid credentials."
    # et le même coût bcrypt est payé
    burn.assert_called_once_with("secret123")


@patch("services.auth_service.ProfileService")
@patch("services.auth_service.verify_password", return_value=True)
def test_signin_success_returns_versioned_token(_verify, profile_cls):
    profile_cls.return_value.get_or_create_params.return_value = SimpleNamespace(
        palette=None, last_color_id=1
    )

    result = signin(db_returning(make_user(token_version=4)))

    payload = decode_jwt_token(result["token"])
    assert payload["sub"] == "1"
    assert payload["ver"] == 4


@patch("services.auth_service.verify_password", return_value=True)
def test_signin_disabled_account(_verify):
    with pytest.raises(InvalidCredentialsException) as exc:
        signin(db_returning(make_user(is_active=False)))
    assert exc.value.detail == "Account disabled."


@pytest.mark.parametrize(
    "identifier, joined",
    [("  John@Test.COM ", False), ("JohnDoe", True)],
)
@patch("services.auth_service.verify_password", return_value=False)
def test_signin_identifier_is_case_insensitive(_verify, identifier, joined):
    db = db_returning(make_user())

    with pytest.raises(InvalidCredentialsException):
        signin(db, identifier=identifier)

    q = db.query.return_value
    filt = (q.join.return_value if joined else q).filter
    (condition,) = filt.call_args.args
    # lower(colonne) = valeur déjà en minuscules
    assert "lower" in str(condition).lower()
    assert condition.right.value == identifier.strip().lower()


# ---------------- signup ----------------


@patch("services.auth_service.hash_password", return_value="HASH")
@patch("services.auth_service.ProfileService")
def test_signup_concurrent_duplicate_is_409_not_500(profile_cls, _hash):
    profile_cls.return_value.email_taken.return_value = False
    profile_cls.return_value.username_taken.return_value = False
    db = MagicMock()
    db.commit.side_effect = IntegrityError("INSERT", {}, Exception("duplicate"))

    with pytest.raises(UserAlreadyExistsException):
        AuthService(db).signup(SignUpSchema(**SIGNUP))

    db.rollback.assert_called_once()


@patch("services.auth_service.ProfileService")
def test_signup_email_taken(profile_cls):
    profile_cls.return_value.email_taken.return_value = True
    with pytest.raises(UserAlreadyExistsException):
        AuthService(MagicMock()).signup(SignUpSchema(**SIGNUP))


# ---------------- schémas d'inscription ----------------


def test_signup_schema_normalizes_email_and_strips_names():
    data = SignUpSchema(
        **{**SIGNUP, "email": "  John@Test.COM ", "first_name": "  John "}
    )
    assert data.email == "john@test.com"
    assert data.first_name == "John"


def test_signup_schema_keeps_password_untouched():
    assert SignUpSchema(**{**SIGNUP, "password": " pass word "}).password == (
        " pass word "
    )


@pytest.mark.parametrize(
    "field, value",
    [
        ("username", "a@b"),  # "@" : impossible de se connecter par pseudo
        ("username", "ab"),
        ("username", "x" * 31),
        ("first_name", "x" * 51),
        ("password", "12345"),
        ("password", "é" * 37),  # 74 octets > limite bcrypt
    ],
)
def test_signup_schema_rejects(field, value):
    with pytest.raises(ValueError):
        SignUpSchema(**{**SIGNUP, field: value})


# ---------------- route : limite de débit ----------------


@pytest.fixture()
def client(make_client):
    return make_client(auth_router, prefix="/auth")


@patch("routes.auth.AuthService")
def test_signin_is_rate_limited_per_account(auth_cls, client):
    auth_cls.return_value.signin.side_effect = InvalidCredentialsException()
    body = {"identifier": "victim@test.com", "password": "guess"}

    for _ in range(10):
        assert client.post("/auth/signin", json=body).status_code == 401

    # même compte, casse différente : toujours bloqué
    res = client.post("/auth/signin", json={**body, "identifier": "VICTIM@test.com"})
    assert_error(res, 429, ErrorCode.RATE_LIMITED)
    assert auth_cls.return_value.signin.call_count == 10

    # un autre compte n'est pas impacté
    other = client.post("/auth/signin", json={**body, "identifier": "other@test.com"})
    assert other.status_code == 401


@patch("routes.auth.AuthService")
def test_signup_is_rate_limited_per_ip(auth_cls, client):
    auth_cls.return_value.signup.side_effect = UserAlreadyExistsException()

    for _ in range(10):
        assert client.post("/auth/signup", json=SIGNUP).status_code == 409

    assert_error(client.post("/auth/signup", json=SIGNUP), 429, ErrorCode.RATE_LIMITED)
