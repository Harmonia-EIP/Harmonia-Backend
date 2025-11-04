from fastapi import FastAPI
from api.auth import router as auth_router

app = FastAPI(title="JUCE Backend API")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])

@app.get("/")
def root():
    return {"message": "JUCE Backend is running!"}
