from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.ai import (
    AIModelListSchema,
    GeneratePatchRequest,
    PresetCharterSchema,
    RefinePresetRequest,
)
from services.ai_service import AiService
from services.profile_service import ProfileService

router = APIRouter()


@router.get("/models", response_model=AIModelListSchema)
def list_models(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    ProfileService(db).ensure_active_user_from_token(authorization)

    return AiService(db).list_models()


@router.post("/generate-preset", response_model=PresetCharterSchema)
def generate_preset(
    payload: GeneratePatchRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    user = ProfileService(db).ensure_active_user_from_token(authorization)

    return AiService(db).generate_preset_from_prompt(
        prompt=payload.prompt,
        model_id=payload.model_id,
        model_name=payload.model_name,
        user_id=user.id,
    )


@router.post("/refine-preset", response_model=PresetCharterSchema)
def refine_preset(
    payload: RefinePresetRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    user = ProfileService(db).ensure_active_user_from_token(authorization)

    return AiService(db).refine_preset_from_prompt(
        prompt=payload.prompt,
        current_parameters=payload.current_preset.parameters,
        locked_params=payload.locked_params,
        model_id=payload.model_id,
        model_name=payload.model_name,
        user_id=user.id,
    )