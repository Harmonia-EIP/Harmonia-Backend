from fastapi import FastAPI
from routes.auth import router as auth_router
from routes.profile import router as profile_router
from routes.ai import router as ai_router
from database.connection import check_db_connection
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(
    title="Harmonia API",
    description="Backend API for Harmonia audio plugin (auth, AI, profile)",
    version="1.0.0",
    contact={
        "name": "Pereira Noé",
        "email": "noe.pereira@epitech.eu"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_favicon_url="/static/harmonia-icon.ico",
    swagger_ui_parameters={"syntaxHighlight": False, "syntaxHighlightTheme": "obsidian"},
)

check_db_connection()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(profile_router, prefix="/profile", tags=["Profiles"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])


@app.get("/", response_class=HTMLResponse)
def root():
    html_path = Path("docs/swagger_welcome_page.html")
    return HTMLResponse(content=html_path.read_text(), status_code=200)


