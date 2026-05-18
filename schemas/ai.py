from typing import Dict, Optional
from pydantic import BaseModel, Field


class GeneratePatchRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=3,
        example="Warm analog bass with soft attack"
    )


class ParameterValueSchema(BaseModel):
    value: float
    range: Optional[list[float]] = None
    mapping: Optional[dict[str, str]] = None
    description: Optional[str] = None


class PatchMetadataSchema(BaseModel):
    prompt: str
    generated_by: str
    model_version: str
    model_hash: str


class SynthPatchSchema(BaseModel):
    metadata: PatchMetadataSchema
    parameters: Dict[str, float]