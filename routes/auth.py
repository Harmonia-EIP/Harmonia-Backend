from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.auth import AuthResponseSchema, SignInSchema, SignUpSchema
from services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=AuthResponseSchema)
def signup(payload: SignUpSchema, db: Session = Depends(get_db)):
    return AuthService(db).signup(payload)


@router.post("/signin", response_model=AuthResponseSchema)
def signin(payload: SignInSchema, db: Session = Depends(get_db)):
    return AuthService(db).signin(payload)
