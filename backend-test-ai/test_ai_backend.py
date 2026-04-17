# test_ai_backend.py
from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI()


class AiRequest(BaseModel):
    prompt: str


@app.post("/generate_patch")
def generate_patch(body: AiRequest):
    """
    Fake IA: ignore (ou utilise un peu) le prompt
    et renvoie un patch déterministe ou semi-aléatoire.
    """

    waveforms = ["Sine", "Square", "Triangle", "Saw"]
    filters = ["Low Pass", "High Pass", "Band Pass", "Notch"]

    return { "parameters": {
        "waveform": random.choice(waveforms),
        "frequency": 2597.84,
        "volume": 0.1,
        "attack": 0.2,
        "decay": 0.3,
        "sustain": 0.4,
        "release": 0.8555,
        "filterType": random.choice(filters),
        "cutoff": 1222.0,
        "resonance": 1000.0,
        "prompt": body.prompt,
    }
    }
