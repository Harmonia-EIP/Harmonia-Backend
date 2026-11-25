"""JWT, mots de passe et limitation de débit."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest

from exceptions.custom_exceptions import RateLimitedException, TokenExpiredException
from utils import jwt_handler
from utils.password import burn_password_check, hash_password, verify_password
from utils.rate_limit import RateLimiter

# ---------------- JWT ----------------


@pytest.mark.parametrize("secret", [None, "", "too-short-secret"])
def test_jwt_secret_missing_or_short_is_refused(monkeypatch, secret):
    if secret is None:
        monkeypatch.delenv("JWT_SECRET", raising=False)
    else:
        monkeypatch.setenv("JWT_SECRET", secret)

    with pytest.raises(RuntimeError):
        jwt_handler.get_jwt_secret()
    with pytest.raises(RuntimeError):
        jwt_handler.create_jwt_token({"sub": 1})


def test_jwt_roundtrip_keeps_sub_and_version():
    token = jwt_handler.create_jwt_token({"sub": 42, "ver": 3})
    payload = jwt_handler.decode_jwt_token(token)
    assert payload["sub"] == "42"
    assert payload["ver"] == 3
    assert "exp" in payload


def test_jwt_signed_with_another_key_is_invalid():
    forged = jwt.encode({"sub": "1"}, "x" * 40, algorithm="HS256")
    assert jwt_handler.decode_jwt_token(forged) is None


def test_jwt_garbage_is_invalid():
    assert jwt_handler.decode_jwt_token("not-a-token") is None


def test_jwt_none_algorithm_is_rejected():
    unsigned = jwt.encode({"sub": "1"}, key=None, algorithm="none")
    assert jwt_handler.decode_jwt_token(unsigned) is None


def test_jwt_expired_raises_token_expired():
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        jwt_handler.get_jwt_secret(),
        algorithm="HS256",
    )
    with pytest.raises(TokenExpiredException):
        jwt_handler.decode_jwt_token(expired)


# ---------------- mots de passe ----------------


def test_password_hash_and_verify():
    hashed = hash_password("secret123")
    assert hashed.startswith("$2b$")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_password_hash_from_passlib_still_verifies():
    """Hash produit par passlib (ancienne implémentation) : toujours valide."""
    legacy = "$2b$12$z75ySJzPlkGD683tIX/wju9tPigv75XcP5jhg69ZQR4w.z74Rep9m"
    assert verify_password("secret123", legacy)


@pytest.mark.parametrize("bad_hash", ["", "not-a-bcrypt-hash", None])
def test_verify_password_with_invalid_hash_is_false(bad_hash):
    assert verify_password("secret123", bad_hash) is False


def test_burn_password_check_does_a_bcrypt_round():
    with patch("utils.password.verify_password") as verify:
        burn_password_check("pwd")
    assert verify.call_args.args[0] == "pwd"


# ---------------- limitation de débit ----------------


def test_rate_limiter_blocks_after_limit_and_reports_retry_after():
    limiter = RateLimiter()
    for _ in range(3):
        limiter.hit("k", limit=3, window=60)

    with pytest.raises(RateLimitedException) as exc:
        limiter.hit("k", limit=3, window=60)

    assert exc.value.status_code == 429
    assert 1 <= int(exc.value.headers["Retry-After"]) <= 60


def test_rate_limiter_keys_are_independent():
    limiter = RateLimiter()
    limiter.hit("a", limit=1, window=60)
    limiter.hit("b", limit=1, window=60)  # ne lève pas


def test_rate_limiter_window_slides():
    limiter = RateLimiter()
    with patch("utils.rate_limit.time.monotonic", return_value=1000.0):
        limiter.hit("k", limit=1, window=10)
    with patch("utils.rate_limit.time.monotonic", return_value=1011.0):
        limiter.hit("k", limit=1, window=10)  # la première requête est sortie


def test_rate_limiter_reset():
    limiter = RateLimiter()
    limiter.hit("k", limit=1, window=60)
    limiter.reset()
    limiter.hit("k", limit=1, window=60)
