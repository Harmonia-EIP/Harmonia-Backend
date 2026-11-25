from fastapi import APIRouter, Depends

from routes.dependencies import CurrentUser, DbSession
from schemas.ai import (
    AIModelListSchema,
    GeneratePatchRequest,
    PresetCharterSchema,
    RefinePresetRequest,
)
from services.ai_service import AiService
from utils.rate_limit import rate_limit

router = APIRouter()


@router.get(
    "/models",
    response_model=AIModelListSchema,
    dependencies=[Depends(rate_limit("ai_models_ip"))],
)
def list_models(user: CurrentUser, db: DbSession):
    return AiService(db).list_models()


@router.post(
    "/generate-preset",
    response_model=PresetCharterSchema,
    dependencies=[Depends(rate_limit("ai_ip"))],
)
def generate_preset(payload: GeneratePatchRequest, user: CurrentUser, db: DbSession):
    return AiService(db).generate_preset_from_prompt(
        prompt=payload.prompt,
        model_id=payload.model_id,
        model_name=payload.model_name,
        variation=payload.variation,
        user_id=user.id,
    )


@router.post(
    "/refine-preset",
    response_model=PresetCharterSchema,
    dependencies=[Depends(rate_limit("ai_ip"))],
)
def refine_preset(payload: RefinePresetRequest, user: CurrentUser, db: DbSession):
    return AiService(db).refine_preset_from_prompt(
        prompt=payload.prompt,
        current_parameters=payload.current_preset.parameters,
        locked_params=payload.locked_params,
        model_id=payload.model_id,
        model_name=payload.model_name,
        user_id=user.id,
    )
