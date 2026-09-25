from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _no_bcrypt_hash():
    with patch("services.auth_service.pwd_context.hash", return_value="HASHED"):
        yield
