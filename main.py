import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from database.connection import check_db_connection
from exceptions.custom_exceptions import AppException
from exceptions.exception_handlers import (
    app_exception_handler,
    request_validation_exception_handler,
)
from routes.ai import router as ai_router
from routes.auth import router as auth_router
from routes.profile import router as profile_router
from services.avatar_service import UPLOAD_DIR

app = FastAPI(
    title="Harmonia API",
    description="Backend API for Harmonia audio plugin (auth, AI, profile)",
    version="1.0.0",
    contact={"name": "Pereira Noé", "email": "noe.pereira@epitech.eu"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_favicon_url="/static/harmonia-icon.ico",
    swagger_ui_parameters={
        "syntaxHighlight": False,
        "syntaxHighlightTheme": "obsidian",
    },
)

check_db_connection()

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
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Avatars envoyés par les utilisateurs (dossier à monter en volume Docker)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(profile_router, prefix="/profile", tags=["Profiles"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])


@app.get("/", response_class=HTMLResponse)
def root():
    html_path = Path("docs/swagger_welcome_page.html")
    return HTMLResponse(content=html_path.read_text(), status_code=200)