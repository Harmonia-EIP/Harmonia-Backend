from unittest.mock import patch

import pytest
from fastapi.exceptions import ResponseValidationError

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

PALETTE = [
    {"id": 1, "color": "#CBA6F7"},
    {"id": 2, "color": "#89B4FA"},
    {"id": 3, "color": "#A6E3A1"},
]

SIGNUP_RESPONSE = {
    "message": "User created successfully",
    "user_id": 1,
    "username": "jane",
    "email": "jane@test.com",
    "token": "T",
    "palette": PALETTE,
    "last_color_id": 2,
    "avatar_url": None,
}
SIGNIN_RESPONSE = {
    "message": "Login successful",
    "user_id": 1,
    "username": "jane",
    "email": "jane@test.com",
    "token": "T",
    "palette": PALETTE,
    "last_color_id": 2,
    "avatar_url": None,
}

# Ancien format (sans palette ni avatar) : doit rester accepté
LEGACY_RESPONSE = {
    "message": "ok",
    "user_id": 1,
    "username": "jane",
    "email": "jane@test.com",
    "token": "T",
}


# ---------------- succès ----------------


@patch("routes.auth.AuthService")
def test_signup_route_ok(mock_cls, client):
    mock_cls.return_value.signup.return_value = SIGNUP_RESPONSE

    res = client.post("/auth/signup", json=SIGNUP_BODY)

    assert res.status_code == 200
    assert res.json() == SIGNUP_RESPONSE
    payload = mock_cls.return_value.signup.call_args.args[0]
    assert payload.username == "jane"
    assert payload.email == "jane@test.com"


@patch("routes.auth.AuthService")
def test_signin_route_ok(mock_cls, client):
    mock_cls.return_value.signin.return_value = SIGNIN_RESPONSE

    res = client.post("/auth/signin", json=SIGNIN_BODY)

    assert res.status_code == 200
    assert res.json()["token"] == "T"
    payload = mock_cls.return_value.signin.call_args.args[0]
    assert payload.identifier == "jane"


# ---------------- palette et avatar dans la réponse ----------------


@pytest.mark.parametrize(
    "endpoint, method", [("signup", "signup"), ("signin", "signin")]
)
@patch("routes.auth.AuthService")
def test_auth_routes_return_palette_and_avatar(mock_cls, client, endpoint, method):
    response = {
        **SIGNIN_RESPONSE,
        "avatar_url": "https://api.test/uploads/avatars/1-abc.png",
    }
    getattr(mock_cls.return_value, method).return_value = response
    body = SIGNUP_BODY if endpoint == "signup" else SIGNIN_BODY

    res = client.post(f"/auth/{endpoint}", json=body)

    assert res.status_code == 200
    data = res.json()
    assert data["palette"] == PALETTE
    assert data["last_color_id"] == 2
    assert data["avatar_url"] == "https://api.test/uploads/avatars/1-abc.png"


@pytest.mark.parametrize(
    "endpoint, method", [("signup", "signup"), ("signin", "signin")]
)
@patch("routes.auth.AuthService")
def test_auth_routes_new_fields_default_to_null(mock_cls, client, endpoint, method):
    getattr(mock_cls.return_value, method).return_value = LEGACY_RESPONSE
    body = SIGNUP_BODY if endpoint == "signup" else SIGNIN_BODY

    res = client.post(f"/auth/{endpoint}", json=body)

    assert res.status_code == 200
    data = res.json()
    assert data["palette"] is None
    assert data["last_color_id"] is None
    assert data["avatar_url"] is None


@patch("routes.auth.AuthService")
def test_signin_route_rejects_invalid_palette_from_service(mock_cls, client):
    """Le schéma de sortie valide la palette (hex #RRGGBB, id 1..3)."""
    bad = {**SIGNIN_RESPONSE, "palette": [{"id": 1, "color": "red"}]}
    mock_cls.return_value.signin.return_value = bad

    # Le TestClient relève l'erreur de validation de la réponse (sinon : 500)
    with pytest.raises(ResponseValidationError):
        client.post("/auth/signin", json=SIGNIN_BODY)


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
