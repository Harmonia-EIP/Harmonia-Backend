import sys
from unittest.mock import MagicMock

# ✅ MOCK GLOBAL AVANT IMPORT (CRITIQUE)
mock_connection = MagicMock()
mock_connection.get_db = lambda: MagicMock()
sys.modules["database.connection"] = mock_connection


import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError


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
def client():
    from exceptions.handlers import (
        request_validation_exception_handler,
        invalid_email_exception_handler,
    )
    from exceptions.custom_exceptions import InvalidEmailException

    app = FastAPI()

    # ✅ handlers
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(InvalidEmailException, invalid_email_exception_handler)

    app.include_router(auth_router, prefix="/auth")

    return TestClient(app)