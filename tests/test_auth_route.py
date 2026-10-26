from unittest.mock import patch

import pytest

from exceptions.custom_exceptions import (
    ErrorCode,
    InvalidCredentialsException,
    MissingParamException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from routes.auth import router as auth_router
from tests.helpers import assert_error


@pytest.fixture()
def client(make_client):
    return make_client(auth_router, prefix="/auth")


SIGNUP_BODY = {
    "first_name": "Jane",
    "last_name": "Doe",
    "username": "jane",
    "email": "jane@test.com",
    "password": "securepassword",
}
SIGNIN_BODY = {"identifier": "jane", "password": "securepassword"}


# ---------------- succès ----------------


@patch("routes.auth.AuthService")
def test_signup_route_ok(mock_cls, client):
    mock_cls.return_value.signup.return_value = {"message": "User created successfully"}

    res = client.post("/auth/signup", json=SIGNUP_BODY)

    assert res.status_code == 200
    assert res.json() == {"message": "User created successfully"}
    payload = mock_cls.return_value.signup.call_args.args[0]
    assert payload.username == "jane"
    assert payload.email == "jane@test.com"


@patch("routes.auth.AuthService")
def test_signin_route_ok(mock_cls, client):
    mock_cls.return_value.signin.return_value = {
        "message": "Login successful",
        "token": "T",
    }

    res = client.post("/auth/signin", json=SIGNIN_BODY)

    assert res.status_code == 200
    assert res.json()["token"] == "T"
    payload = mock_cls.return_value.signin.call_args.args[0]
    assert payload.identifier == "jane"


# ---------------- validation (422 / 400) ----------------


@patch("routes.auth.AuthService")
def test_signup_route_missing_field_is_422(mock_cls, client):
    body = dict(SIGNUP_BODY)
    del body["email"]

    res = client.post("/auth/signup", json=body)

    assert_error(res, 422, ErrorCode.VALIDATION_ERROR)
    assert "email" in res.json()["detail"]
    mock_cls.return_value.signup.assert_not_called()


@patch("routes.auth.AuthService")
def test_signup_route_invalid_email_is_400(mock_cls, client):
    res = client.post("/auth/signup", json={**SIGNUP_BODY, "email": "not-an-email"})

    assert_error(res, 400, ErrorCode.INVALID_EMAIL, "Invalid email.")
    mock_cls.return_value.signup.assert_not_called()


@patch("routes.auth.AuthService")
def test_signin_route_missing_password_is_422(mock_cls, client):
    res = client.post("/auth/signin", json={"identifier": "jane"})

    assert_error(res, 422, ErrorCode.VALIDATION_ERROR)
    mock_cls.return_value.signin.assert_not_called()


def test_signup_route_empty_body_is_422(client):
    res = client.post("/auth/signup", json={})

    assert_error(res, 422, ErrorCode.VALIDATION_ERROR)


# ---------------- erreurs FastAPI natives (format inchangé) ----------------


def test_unknown_route_is_404(client):
    assert client.get("/auth/nope").status_code == 404


def test_signup_wrong_method_is_405(client):
    assert client.get("/auth/signup").status_code == 405


# ---------------- erreurs métier propagées par le service ----------------


@pytest.mark.parametrize(
    "exc, status_code, code, detail",
    [
        (
            UserAlreadyExistsException(),
            409,
            ErrorCode.USER_ALREADY_EXISTS,
            "This user already exists.",
        ),
        (
            MissingParamException("username"),
            400,
            ErrorCode.MISSING_PARAM,
            "Parameter 'username' is missing.",
        ),
    ],
)
@patch("routes.auth.AuthService")
def test_signup_route_propagates_service_errors(
    mock_cls, client, exc, status_code, code, detail
):
    mock_cls.return_value.signup.side_effect = exc

    res = client.post("/auth/signup", json=SIGNUP_BODY)

    assert_error(res, status_code, code, detail)


@pytest.mark.parametrize(
    "exc, status_code, code, detail",
    [
        (
            InvalidCredentialsException(),
            401,
            ErrorCode.INVALID_CREDENTIALS,
            "Invalid credentials.",
        ),
        (
            UserNotFoundException(),
            404,
            ErrorCode.USER_NOT_FOUND,
            "User not found.",
        ),
    ],
)
@patch("routes.auth.AuthService")
def test_signin_route_propagates_service_errors(
    mock_cls, client, exc, status_code, code, detail
):
    mock_cls.return_value.signin.side_effect = exc

    res = client.post("/auth/signin", json=SIGNIN_BODY)

    assert_error(res, status_code, code, detail)
