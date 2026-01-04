from pydantic import BaseModel


class GeneratePatchRequest(BaseModel):
    prompt: str


class SynthPatchSchema(BaseModel):
    waveform: str
    frequency: float
    volume: float
    attack: float
    decay: float
    sustain: float
    release: float
    filterType: str
    cutoff: float
    resonance: float
