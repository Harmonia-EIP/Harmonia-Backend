import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from database.connection import check_db_connection, db_is_healthy
from exceptions.exception_handlers import register_exception_handlers
from routes.ai import router as ai_router
from routes.auth import router as auth_router
from routes.profile import router as profile_router
from services.avatar_service import UPLOAD_DIR
from utils.jwt_handler import get_jwt_secret

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("harmonia")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # On refuse de démarrer avec une configuration dangereuse ou cassée.
    get_jwt_secret()
    check_db_connection()
    logger.info("Harmonia API started")
    yield


app = FastAPI(
    title="Harmonia API",
    description="Backend API for Harmonia audio plugin (auth, AI, profile)",
    version="1.4.0",
    contact={"name": "Pereira Noé", "email": "noe.pereira@epitech.eu"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_favicon_url="/static/icon.ico",
    swagger_ui_parameters={
        "syntaxHighlight": False,
        "syntaxHighlightTheme": "obsidian",
    },
    lifespan=lifespan,
)

# Origines autorisées à appeler l'API depuis un navigateur (séparées par des virgules)
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["Retry-After"],
)

register_exception_handlers(app)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Avatars envoyés par les utilisateurs (dossier à monter en volume Docker)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(profile_router, prefix="/profile", tags=["Profiles"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])

WELCOME_PAGE = Path("docs/swagger_welcome_page.html")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    return HTMLResponse(content=WELCOME_PAGE.read_text(encoding="utf-8"))


@app.get("/health", tags=["Health"])
def health():
    """Utilisé par le HEALTHCHECK Docker : 503 si la base ne répond pas."""
    if not db_is_healthy():
        return JSONResponse(status_code=503, content={"status": "degraded"})
    return {"status": "ok"}
