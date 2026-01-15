import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# ------------------------------------------------------------
# Import robuste du router auth (sans deviner votre arborescence)
# ------------------------------------------------------------
auth_router = None
_import_errors = []

for mod_path in (
    "auth",           # auth.py à la racine
    "routes.auth",    # routes/auth.py
    "routers.auth",   # routers/auth.py
    "api.auth",       # api/auth.py
    "app.auth",       # app/auth.py
    "app.routes.auth" # app/routes/auth.py
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
        "Impossible d'importer le router auth. Essais effectués:\n" +
        "\n".join([f"- {m}: {err}" for m, err in _import_errors])
    )


@pytest.fixture()
def client(monkeypatch):
    app = FastAPI()

    # override get_db dans le module qui contient le router
    def fake_get_db():
        return MagicMock()

    monkeypatch.setattr(f"{AUTH_MODULE_PATH}.get_db", fake_get_db)

    app.include_router(auth_router, prefix="/auth")
    return TestClient(app)


def test_route_signup_ok(client, monkeypatch):
    def fake_signup(self, payload):
        return {"message": "Utilisateur créé avec succès", "user_id": 1, "token": "T"}

    monkeypatch.setattr("services.auth_service.AuthService.signup", fake_signup)

    r = client.post(
        "/auth/signup",
        json={
            "first_name": "Peyo",
            "last_name": "Artigala",
            "username": "peyo",
            "email": "peyo@test.com",
            "password": "1234",
        },
    )
    assert r.status_code == 200
    assert r.json()["token"] == "T"


def test_route_signin_ok(client, monkeypatch):
    def fake_signin(self, payload):
        return {
            "message": "Connexion réussie",
            "user_id": 1,
            "username": "peyo",
            "email": "peyo@test.com",
            "token": "T",
        }

    monkeypatch.setattr("services.auth_service.AuthService.signin", fake_signin)

    r = client.post(
        "/auth/signin",
        json={"identifier": "peyo@test.com", "password": "1234"},
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Connexion réussie"
