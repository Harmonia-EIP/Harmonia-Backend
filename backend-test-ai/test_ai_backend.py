# test_ai_backend.py

from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI()


class AiRequest(BaseModel):
    prompt: str


def rand():
    return round(random.uniform(0.0, 1.0), 4)


@app.post("/generate_patch")
def generate_patch(body: AiRequest):
    """
    Fake Harmonia AI backend.

    Retourne un preset compatible avec le frontend JUCE.
    Toutes les valeurs sont normalisées entre 0.0 et 1.0.
    """

    waveform_values = [0.0, 0.33, 0.66, 1.0]
    filter_values = [0.0, 0.5, 1.0]

    return {
        "metadata": {
            "prompt": body.prompt,
            "generated_by": "Harmonia-Test-AI",
            "model_version": "1.0.0-test",
            "model_hash": "debug-build"
        },

        "parameters": {
            "osc_1_waveform": random.choice(waveform_values),
            "osc_2_waveform": random.choice(waveform_values),

            "osc_mix": rand(),
            "osc_2_detune": rand(),
            "noise_level": rand(),

            "filter_cutoff": rand(),
            "filter_resonance": rand(),
            "filter_type": random.choice(filter_values),

            "amp_attack": rand(),
            "amp_decay": rand(),
            "amp_sustain": rand(),
            "amp_release": rand(),

            "filter_env_amount": rand(),
            "filter_env_decay": rand(),

            "lfo_rate": rand(),
            "lfo_to_pitch": rand(),
            "lfo_to_cutoff": rand(),

            "velocity_to_filter": rand(),

            "distortion_mix": rand(),
            "reverb_mix": rand()
        }
    }