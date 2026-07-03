from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from database.connection import get_db
from services.ai_service import AiService
from services.profile_service import ProfileService

from schemas.ai import GeneratePatchRequest, PresetCharterSchema


router = APIRouter()


@router.post("/generate-preset", response_model=PresetCharterSchema)
def generate_preset(
    payload: GeneratePatchRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    profile_service = ProfileService(db)

    profile_service.ensure_active_user_from_token(authorization)

    ai = AiService(db)

    print(f"Generating preset with model_id: {payload.model_id}, model_name: {payload.model_name}, prompt: {payload.prompt}")
    return ai.call_ai_and_get_patch(
        prompt=payload.prompt,
        model_id=payload.model_id,
        model_name=payload.model_name
    )
