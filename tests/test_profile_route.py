import pytest
import sys
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.profile import router as profile_router

mock_connection = MagicMock()
mock_connection.get_db = lambda: MagicMock()
sys.modules["database.connection"] = mock_connection


def make_app():
    app = FastAPI()
    app.include_router(profile_router, prefix="/profile")
    return app


@pytest.fixture()
def client():
    return TestClient(make_app())
