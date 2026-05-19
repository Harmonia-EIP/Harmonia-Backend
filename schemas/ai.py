from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GeneratePatchRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=3,
        example="Warm analog bass with soft attack"
    )


class PresetMetadataSchema(BaseModel):
    name: str
    generated_by: Optional[str] = None
    model_version: Optional[str] = None
    model_hash: Optional[str] = None
    charter_version: Optional[str] = None


class PresetCharterSchema(BaseModel):
    """Format charter renvoyé tel quel au VST (consommé par PresetLoader)."""
    metadata: PresetMetadataSchema
    parameters: Dict[str, float]
    values: Optional[List[float]] = None
    charter: Optional[List[Dict[str, Any]]] = None
