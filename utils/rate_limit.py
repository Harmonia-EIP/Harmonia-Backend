"""Limitation de débit en mémoire (fenêtre glissante).

Suffisant pour un seul process uvicorn (c'est le cas en production). Avec
plusieurs workers ou plusieurs conteneurs, il faudrait un stockage partagé
(Redis) : chaque process aurait sinon ses propres compteurs.

L'IP du client vient de request.client.host : derrière un reverse proxy,
uvicorn doit tourner avec --proxy-headers (voir entrypoint.sh).
"""

import math
import os
import threading
import time
from collections import deque

from fastapi import Request

from exceptions.custom_exceptions import RateLimitedException

RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1").lower() not in (
    "0",
    "false",
    "no",
)

# (nombre de requêtes, fenêtre en secondes)
LIMITS = {
    "signin_ip": (20, 60),
    "signin_identifier": (10, 300),
    "signup_ip": (10, 3600),
    "credentials_ip": (10, 900),  # changement d'email / mot de passe
    "ai_ip": (30, 60),
    "ai_models_ip": (60, 60),
}

_SWEEP_EVERY = 1000
_MAX_WINDOW = max(window for _, window in LIMITS.values())


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()
        self._calls = 0

    def hit(self, key: str, limit: int, window: int) -> None:
        """Compte une requête pour `key`. Lève RateLimitedException si la
        limite est dépassée sur la fenêtre (la requête refusée ne compte pas)."""
        if not RATE_LIMIT_ENABLED:
            return

        now = time.monotonic()
        with self._lock:
            self._calls += 1
            if self._calls % _SWEEP_EVERY == 0:
                self._sweep(now)

            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - window:
                hits.popleft()

            if len(hits) >= limit:
                retry_after = max(1, math.ceil(hits[0] + window - now))
                raise RateLimitedException(retry_after)

            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
            self._calls = 0

    def _sweep(self, now: float) -> None:
        """Oublie les clés inactives pour que la mémoire ne grossisse pas."""
        stale = [
            k for k, d in self._hits.items() if not d or d[-1] <= now - _MAX_WINDOW
        ]
        for k in stale:
            del self._hits[k]


limiter = RateLimiter()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def check_limit(name: str, key: str) -> None:
    limit, window = LIMITS[name]
    limiter.hit(f"{name}:{key}", limit, window)


def rate_limit(name: str):
    """Dépendance FastAPI : limite par IP selon LIMITS[name]."""

    def dependency(request: Request) -> None:
        check_limit(name, client_ip(request))

    return dependency
