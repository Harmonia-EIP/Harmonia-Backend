import sys
from unittest.mock import MagicMock

# ✅ MOCK GLOBAL AVANT IMPORT
mock_connection = MagicMock()
mock_connection.get_db = lambda: MagicMock()
sys.modules["database.connection"] = mock_connection


import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from exceptions.custom_exceptions import (
    NoPermissionException,
    TokenInvalidException,
    UserNotFoundException,
)

from routes.profile import router as profile_router


def make_app():
    app = FastAPI()
    app.include_router(profile_router, prefix="/profile")
    return app


@pytest.fixture()
def client():
    return TestClient(make_app())