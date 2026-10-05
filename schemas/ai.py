from typing import Any

from pydantic import BaseModel, Field


class GeneratePatchRequest(BaseModel):
    prompt: str = Field(..., min_length=3, example="Warm analog bass with soft attack")

    model_id: int = Field(..., ge=1, le=3, example=1)

    model_name: str = Field(..., min_length=1, example="model-1")

    # harmonia_v2 only: 0 (or absent) returns the best preset, other values alternatives.
    variation: int | None = Field(None, ge=0, example=0)


class PresetMetadataSchema(BaseModel):
    name: str
    generated_by: str | None = None
    model_version: str | None = None
    model_hash: str | None = None
    charter_version: str | None = None


class PresetCharterSchema(BaseModel):
    """Format charter renvoyé tel quel au VST (consommé par PresetLoader)."""

    metadata: PresetMetadataSchema
    parameters: dict[str, float]
    values: list[float] | None = None
    charter: list[dict[str, Any]] | None = None
