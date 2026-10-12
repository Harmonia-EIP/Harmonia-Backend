from typing import Any

from pydantic import BaseModel, Field


class GeneratePatchRequest(BaseModel):
    prompt: str = Field(..., min_length=1, example="Warm analog bass with soft attack")

    model_id: int = Field(..., ge=1, le=2, example=1)

    model_name: str = Field(..., min_length=1, example="model-1")


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


class CurrentPresetSchema(BaseModel):
    """Preset courant envoyé par le plugin (seul `parameters` est utilisé)."""

    metadata: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, float]


class RefinePresetRequest(BaseModel):
    prompt: str = Field(..., min_length=1, example="Make it brighter")

    current_preset: CurrentPresetSchema

    locked_params: list[str] = Field(default_factory=list, example=["lfo_to_pitch"])

    model_id: int = Field(..., ge=1, le=2, example=1)

    model_name: str = Field(..., min_length=1, example="model-1")