from pydantic import BaseModel, Field


class GeneratePatchRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=3,
        example="Warm analog bass with soft attack"
    )


class SynthPatchSchema(BaseModel):
    waveform: str = Field(example="sine")
    frequency: float = Field(example=440.0)
    volume: float = Field(example=0.8)
    attack: float = Field(example=0.01)
    decay: float = Field(example=0.2)
    sustain: float = Field(example=0.7)
    release: float = Field(example=0.5)
    filterType: str = Field(example="lowpass")
    cutoff: float = Field(example=1200.0)
    resonance: float = Field(example=0.5)