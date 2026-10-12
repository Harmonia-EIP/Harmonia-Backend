"""Configuration commune des tests.

On injecte un faux module `database.connection` AVANT l'import des routes :
le vrai module tente de se connecter à la base au chargement.
"""

import sys
import types
from unittest.mock import MagicMock

try:
    import database  # noqa: F401
except ImportError:
    _pkg = types.ModuleType("database")
    _pkg.__path__ = []
    sys.modules["database"] = _pkg

if "database.connection" not in sys.modules:
    _fake = types.ModuleType("database.connection")

    def get_db():
        yield MagicMock()

    _fake.get_db = get_db
    sys.modules["database.connection"] = _fake

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from database.connection import get_db  # noqa: E402
from exceptions.exception_handlers import register_exception_handlers  # noqa: E402


@pytest.fixture()
def make_client():
    """Fabrique un TestClient pour un router, avec get_db surchargé
    et les mêmes exception handlers que l'app réelle."""

    def _make(router, prefix=""):
        app = FastAPI()
        app.include_router(router, prefix=prefix)
        app.dependency_overrides[get_db] = lambda: MagicMock()
        register_exception_handlers(app)
        return TestClient(app)

    return _make
