from fastapi import FastAPI
from routes.auth import router as auth_router
# from routes.profile import router as profile_router
from database.connection import check_db_connection

app = FastAPI(title="JUCE Backend API")

check_db_connection()

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
# app.include_router(profile_router, prefix="/profiles", tags=["Profiles"])

@app.get("/")
def root():
    return {"message": "JUCE Backend is running!"}
