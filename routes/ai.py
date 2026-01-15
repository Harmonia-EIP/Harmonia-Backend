from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from database.connection import get_db
from services.ai_service import AiService
from services.profile_service import ProfileService

from schemas.ai import GeneratePatchRequest, SynthPatchSchema


router = APIRouter()


@router.post("/generate-preset", response_model=SynthPatchSchema)
def generate_preset(
    payload: GeneratePatchRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    profile_service = ProfileService(db)

    current_user = profile_service.ensure_active_user_from_token(authorization)

    ai = AiService(db)

    patch = ai.call_ai_and_get_patch(payload.prompt)

    return patch
