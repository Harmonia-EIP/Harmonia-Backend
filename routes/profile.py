from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from database.connection import get_db
from services.profile_service import ProfileService
from schemas.profile import ProfileSchema, ProfileDetailsSchema, UpdateRoleSchema, UpdateActiveSchema   

router = APIRouter()

@router.get("/me", response_model=ProfileSchema)
def get_my_profile(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    service = ProfileService(db)

    current_user = service.get_current_user(authorization)

    return service.get_profile(current_user)

@router.get("/{user_id}", response_model=ProfileDetailsSchema)
def get_user_profile(
    user_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    service = ProfileService(db)

    current_user = service.get_current_user(authorization)
    service.ensure_admin(current_user)

    return service.update_user_active_status(user_id, payload.is_active)
