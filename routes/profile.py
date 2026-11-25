from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile

from routes.dependencies import CurrentAdmin, CurrentUser, DbSession
from schemas.profile import (
    AvatarResponseSchema,
    PasswordChangedSchema,
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
from utils.rate_limit import rate_limit

router = APIRouter()


@router.get("/me", response_model=ProfileSchema)
def get_my_profile(user: CurrentUser, db: DbSession):
    return ProfileService(db).get_profile(user)


@router.patch("/me", response_model=ProfileSchema)
def update_my_profile(payload: UpdateProfileSchema, user: CurrentUser, db: DbSession):
    """Pseudo, prénom, nom (seuls les champs envoyés changent)."""
    return ProfileService(db).update_profile(user, payload)


@router.post("/me/avatar", response_model=AvatarResponseSchema)
def upload_my_avatar(
    request: Request,
    file: Annotated[UploadFile, File()],
    user: CurrentUser,
    db: DbSession,
):
    """Envoi de l'avatar (PNG, JPEG, GIF ou WebP, 2 Mo max), champ multipart "file"."""
    url = AvatarService(db).set_avatar(user, file, str(request.base_url).rstrip("/"))
    return AvatarResponseSchema(avatar_url=url)


@router.delete("/me/avatar", status_code=204)
def delete_my_avatar(user: CurrentUser, db: DbSession):
    AvatarService(db).remove_avatar(user)
    return Response(status_code=204)


@router.put(
    "/me/email",
    response_model=ProfileSchema,
    dependencies=[Depends(rate_limit("credentials_ip"))],
)
def update_my_email(payload: UpdateEmailSchema, user: CurrentUser, db: DbSession):
    """Changement d'email, avec le mot de passe actuel."""
    return ProfileService(db).update_email(user, payload)


@router.put(
    "/me/password",
    response_model=PasswordChangedSchema,
    dependencies=[Depends(rate_limit("credentials_ip"))],
)
def update_my_password(payload: UpdatePasswordSchema, user: CurrentUser, db: DbSession):
    """Changement de mot de passe, avec l'ancien. Tous les anciens tokens
    sont révoqués : le client doit remplacer le sien par `token`."""
    token = ProfileService(db).update_password(user, payload)
    return PasswordChangedSchema(token=token)


@router.post("/me/history/{entry_id}/touch", status_code=204)
def touch_history_entry(entry_id: int, user: CurrentUser, db: DbSession):
    HistoryService(db).touch(user.id, entry_id)
    return Response(status_code=204)


@router.delete("/me/history/{entry_id}", status_code=204)
def delete_history_entry(entry_id: int, user: CurrentUser, db: DbSession):
    HistoryService(db).delete_one(user.id, entry_id)
    return Response(status_code=204)


@router.delete("/me/history", status_code=204)
def clear_my_history(user: CurrentUser, db: DbSession):
    HistoryService(db).clear(user.id)
    return Response(status_code=204)


@router.get("/{user_id}", response_model=ProfileDetailsSchema)
def get_user_profile(user_id: int, admin: CurrentAdmin, db: DbSession):
    return ProfileService(db).get_profile_by_id(user_id)


@router.put("/{user_id}/role", response_model=ProfileDetailsSchema)
def update_user_role(
    user_id: int, payload: UpdateRoleSchema, admin: CurrentAdmin, db: DbSession
):
    return ProfileService(db).update_user_role(admin, user_id, payload.role)


@router.put("/{user_id}/active", response_model=ProfileDetailsSchema)
def update_user_active_status(
    user_id: int, payload: UpdateActiveSchema, admin: CurrentAdmin, db: DbSession
):
    return ProfileService(db).update_user_active_status(
        admin, user_id, payload.is_active
    )


@router.put("/{user_id}/palette", response_model=UserParamsResponse)
def update_palette(
    user_id: int, payload: UpdatePaletteSchema, user: CurrentUser, db: DbSession
):
    return ProfileService(db).update_palette(user, user_id, payload)
