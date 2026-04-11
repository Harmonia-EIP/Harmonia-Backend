import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from unittest.mock import MagicMock


auth_router = None
AUTH_MODULE_PATH = None
_import_errors = []

for mod_path in (
    "auth",
    "routes.auth",
    "routers.auth",
    "api.auth",
    "app.auth",
    "app.routes.auth",
):
    try:
        module = __import__(mod_path, fromlist=["router"])
        auth_router = getattr(module, "router")
        AUTH_MODULE_PATH = mod_path
        break
    except Exception as e:
        _import_errors.append((mod_path, repr(e)))

if auth_router is None:
    raise ImportError(
        "Impossible d'importer le router auth.\n"
        + "\n".join([f"- {m}: {err}" for m, err in _import_errors])
    )


@pytest.fixture()
def client(monkeypatch):
    from exceptions.handlers import (
        request_validation_exception_handler,
        invalid_email_exception_handler,
    )
    from exceptions.custom_exceptions import InvalidEmailException

    app = FastAPI()

    def fake_get_db():
        return MagicMock()

    monkeypatch.setattr(f"{AUTH_MODULE_PATH}.get_db", fake_get_db)

    # ✅ Ajout des handlers
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(InvalidEmailException, invalid_email_exception_handler)

    app.include_router(auth_router, prefix="/auth")

    return TestClient(app)


def test_signup_ok(client, monkeypatch):
    def fake_signup(self, payload):
        return {
            "message": "Utilisateur créé avec succès",
            "user_id": 1,
            "username": payload.username,
            "email": payload.email,
            "layout_id": 1,
            "theme_id": 1,
            "token": "T",
        }

    monkeypatch.setattr(f"{AUTH_MODULE_PATH}.AuthService.signup", fake_signup)

    r = client.post(
        "/auth/signup",
        json={
            "first_name": "Daniel",
            "last_name": "Chien",
            "username": "Dachien",
            "email": "daniel.chien@test.com",
            "password": "securepassword",
        },
    )

    assert r.status_code == 200
    data = r.json()
    assert data["message"] == "Utilisateur créé avec succès"
    assert data["user_id"] == 1
    assert data["username"] == "Dachien"
    assert data["email"] == "daniel.chien@test.com"
    assert data["layout_id"] == 1
    assert data["theme_id"] == 1
    assert data["token"] == "T"


def test_signin_ok(client, monkeypatch):
    def fake_signin(self, payload):
        return {
            "message": "Connexion réussie",
            "user_id": 1,
            "username": "Dachien",
            "email": "daniel.chien@test.com",
            "layout_id": 1,
            "theme_id": 1,
            "token": "T",
        }

    monkeypatch.setattr(f"{AUTH_MODULE_PATH}.AuthService.signin", fake_signin)

    r = client.post(
        "/auth/signin",
        json={
            "identifier": "daniel.chien@test.com",
            "password": "securepassword",
        },
    )

    assert r.status_code == 200
    data = r.json()
    assert data["message"] == "Connexion réussie"


def test_signup_missing_field(client):
    r = client.post(
        "/auth/signup",
        json={
            "first_name": "Daniel",
            # last_name manquant
            "username": "Dachien",
            "email": "test@test.com",
            "password": "securepassword",
        },
    )

    assert r.status_code == 422


def test_signup_short_password(client):
    r = client.post(
        "/auth/signup",
        json={
            "first_name": "Daniel",
            "last_name": "Chien",
            "username": "Dachien",
            "email": "test@test.com",
            "password": "123",
        },
    )

    assert r.status_code == 422


def test_signup_invalid_email(client):
    r = client.post(
        "/auth/signup",
        json={
            "first_name": "Daniel",
            "last_name": "Chien",
            "username": "Dachien",
            "email": "not-an-email",
            "password": "securepassword",
        },
    )

    assert r.status_code == 400
    assert r.json()["detail"] == "Email invalide."


def test_signin_missing_password(client):
    r = client.post(
        "/auth/signin",
        json={"identifier": "test@test.com"},
    )

    assert r.status_code == 422


def test_signin_empty_body(client):
    r = client.post("/auth/signin", json={})
    assert r.status_code == 422


def test_signup_user_already_exists(client, monkeypatch):
    from exceptions.custom_exceptions import UserAlreadyExistsException

    def fake_signup(self, payload):
        raise UserAlreadyExistsException("Email déjà utilisé")

    monkeypatch.setattr(f"{AUTH_MODULE_PATH}.AuthService.signup", fake_signup)

    r = client.post(
        "/auth/signup",
        json={
            "first_name": "Daniel",
            "last_name": "Chien",
            "username": "Dachien",
            "email": "test@test.com",
            "password": "securepassword",
        },
    )

    assert r.status_code == 409
    assert r.json()["detail"] == "Email déjà utilisé"


def test_signin_user_not_found(client, monkeypatch):
    from exceptions.custom_exceptions import UserNotFoundException

    def fake_signin(self, payload):
        raise UserNotFoundException()

    monkeypatch.setattr(f"{AUTH_MODULE_PATH}.AuthService.signin", fake_signin)

    r = client.post(
        "/auth/signin",
        json={
            "identifier": "unknown@test.com",
            "password": "securepassword",
        },
    )

    assert r.status_code == 404


def test_signin_invalid_credentials(client, monkeypatch):
    from exceptions.custom_exceptions import InvalidCredentialsException

    def fake_signin(self, payload):
        raise InvalidCredentialsException()

    monkeypatch.setattr(f"{AUTH_MODULE_PATH}.AuthService.signin", fake_signin)

    r = client.post(
        "/auth/signin",
        json={
            "identifier": "test@test.com",
            "password": "wrongpassword",
        },
    )

    assert r.status_code == 401