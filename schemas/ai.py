from typing import Any

from pydantic import BaseModel, Field


class GeneratePatchRequest(BaseModel):
    prompt: str = Field(..., min_length=1, example="Warm analog bass with soft attack")

    # Id du modèle tel que renvoyé par GET /ai/models (ex: "charter_v1").
    # Absent ou "latest" = dernier modèle déployé.
    model_name: str | None = Field(default=None, example="charter_v1")

    # Ancien champ, gardé pour ne pas casser les plugins déjà déployés.
    # Le serveur IA l'ignore si model_name est fourni.
    model_id: int | str | None = Field(default=None, example=None)

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


class CurrentPresetSchema(BaseModel):
    """Preset courant envoyé par le plugin (seul `parameters` est utilisé)."""

    metadata: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, float]


class RefinePresetRequest(BaseModel):
    prompt: str = Field(..., min_length=1, example="Make it brighter")

    current_preset: CurrentPresetSchema

    locked_params: list[str] = Field(default_factory=list, example=["lfo_to_pitch"])

    model_name: str | None = Field(default=None, example="charter_v1")

    model_id: int | str | None = Field(default=None, example=None)


class AIModelSchema(BaseModel):
    id: str
    name: str
    is_latest: bool = False
    model_version: str = "unknown"
    model_hash: str = "unknown"


class AIModelListSchema(BaseModel):
    count: int
    models: list[AIModelSchema]