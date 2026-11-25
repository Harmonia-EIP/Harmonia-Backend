from fastapi import APIRouter, Depends

from routes.dependencies import DbSession
from schemas.auth import AuthResponseSchema, SignInSchema, SignUpSchema
from services.auth_service import AuthService
from utils.rate_limit import check_limit, rate_limit

router = APIRouter()


@router.post(
    "/signup",
    response_model=AuthResponseSchema,
    dependencies=[Depends(rate_limit("signup_ip"))],
)
def signup(payload: SignUpSchema, db: DbSession):
    return AuthService(db).signup(payload)


@router.post(
    "/signin",
    response_model=AuthResponseSchema,
    dependencies=[Depends(rate_limit("signin_ip"))],
)
def signin(payload: SignInSchema, db: DbSession):
    # Limite aussi par compte visé, même si l'attaquant change d'IP.
    check_limit("signin_identifier", payload.identifier.strip().lower())
    return AuthService(db).signin(payload)
