from typing import Annotated

from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import User
from services.profile_service import ProfileService

# Déclare le schéma Bearer dans OpenAPI (bouton "Authorize" de Swagger).
# auto_error=False : c'est ProfileService qui produit nos erreurs
# (TOKEN_MISSING, TOKEN_INVALID...) au format habituel.
_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    request: Request,
    db: DbSession,
    _credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(_bearer)
    ] = None,
) -> User:
    """Utilisateur connecté et actif. On relit le header brut pour accepter
    aussi un token sans préfixe "Bearer " (anciens clients)."""
    return ProfileService(db).get_current_user(request.headers.get("Authorization"))


def get_current_admin(
    user: Annotated[User, Depends(get_current_user)], db: DbSession
) -> User:
    ProfileService(db).ensure_admin(user)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
