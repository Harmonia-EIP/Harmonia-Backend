from typing import Annotated
from fastapi import APIRouter, Depends, File, Header, Request, Response, UploadFile
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.profile import (
    AvatarResponseSchema,
    ProfileDetailsSchema,
    ProfileSchema,
    UpdateActiveSchema,
    UpdateEmailSchema,
    UpdatePasswordSchema,
    UpdateProfileSchema,
    UpdateRoleSchema,
)
from schemas.user_params import (
    UpdatePaletteSchema,
    UserParamsResponse,
)
from services.avatar_service import AvatarService
from services.history_service import HistoryService
from services.profile_service import ProfileService

router = APIRouter()


@router.get("/me", response_model=ProfileSchema)
def get_my_profile(authorization: str = Header(None), db: Session = Depends(get_db)):
    service = ProfileService(db)
    current_user = service.get_current_user(authorization)
    return service.get_profile(current_user)


@router.patch("/me", response_model=ProfileSchema)
def update_my_profile(
    payload: UpdateProfileSchema,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Pseudo, prénom, nom (seuls les champs envoyés changent)."""
    service = ProfileService(db)
    current_user = service.get_current_user(authorization)
    return service.update_profile(current_user, payload)


@router.post("/me/avatar", response_model=AvatarResponseSchema)
def upload_my_avatar(
    request: Request,
    file: Annotated[UploadFile, File()],
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Envoi de l'avatar (PNG, JPEG, GIF ou WebP, 2 Mo max), champ multipart "file"."""
    current_user = ProfileService(db).get_current_user(authorization)
    url = AvatarService(db).set_avatar(
        current_user, file, str(request.base_url).rstrip("/")
    )
    return AvatarResponseSchema(avatar_url=url)


@router.delete("/me/avatar", status_code=204)
def delete_my_avatar(authorization: str = Header(None), db: Session = Depends(get_db)):
    current_user = ProfileService(db).get_current_user(authorization)
    AvatarService(db).remove_avatar(current_user)
    return Response(status_code=204)


@router.put("/me/email", response_model=ProfileSchema)
def update_my_email(
    payload: UpdateEmailSchema,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Changement d'email, avec le mot de passe actuel."""
    service = ProfileService(db)
    current_user = service.get_current_user(authorization)
    return service.update_email(current_user, payload)


@router.put("/me/password", status_code=204)
def update_my_password(
    payload: UpdatePasswordSchema,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Changement de mot de passe, avec l'ancien."""
    service = ProfileService(db)
    current_user = service.get_current_user(authorization)
    service.update_password(current_user, payload)
    return Response(status_code=204)


@router.post("/me/history/{entry_id}/touch", status_code=204)
def touch_history_entry(
    entry_id: int, authorization: str = Header(None), db: Session = Depends(get_db)
):
    current_user = ProfileService(db).get_current_user(authorization)
    HistoryService(db).touch(current_user.id, entry_id)
    return Response(status_code=204)


@router.delete("/me/history/{entry_id}", status_code=204)
def delete_history_entry(
    entry_id: int, authorization: str = Header(None), db: Session = Depends(get_db)
):
    current_user = ProfileService(db).get_current_user(authorization)
    HistoryService(db).delete_one(current_user.id, entry_id)
    return Response(status_code=204)


@router.delete("/me/history", status_code=204)
def clear_my_history(authorization: str = Header(None), db: Session = Depends(get_db)):
    current_user = ProfileService(db).get_current_user(authorization)
    HistoryService(db).clear(current_user.id)
    return Response(status_code=204)


@router.get("/{user_id}", response_model=ProfileDetailsSchema)
def get_user_profile(
    user_id: int, authorization: str = Header(None), db: Session = Depends(get_db)
):
    service = ProfileService(db)
    current_user = service.get_current_user(authorization)
    service.ensure_admin(current_user)
    return service.get_profile_by_id(user_id)


@router.put("/{user_id}/role", response_model=ProfileDetailsSchema)
def update_user_role(
    user_id: int,
    payload: UpdateRoleSchema,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    service = ProfileService(db)
    current_user = service.get_current_user(authorization)
    service.ensure_admin(current_user)
    service.update_user_role(user_id, payload.role)
    return service.get_profile_by_id(user_id)


@router.put("/{user_id}/active", response_model=ProfileDetailsSchema)
def update_user_active_status(
    user_id: int,
    payload: UpdateActiveSchema,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    service = ProfileService(db)
    current_user = service.get_current_user(authorization)
    service.ensure_admin(current_user)
    return service.update_user_active_status(user_id, payload.is_active)


@router.put("/{user_id}/palette", response_model=UserParamsResponse)
def update_palette(
    user_id: int,
    payload: UpdatePaletteSchema,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    service = ProfileService(db)
    current_user = service.get_current_user(authorization)
    return service.update_palette(current_user, user_id, payload)
