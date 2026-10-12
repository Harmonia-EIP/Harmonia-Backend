import random

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class AiRequest(BaseModel):
    prompt: str


class RefineRequest(BaseModel):
    prompt: str
    parameters: dict[str, float]


def rand():
    return round(random.uniform(0.0, 1.0), 4)


PARAMETER_DEFINITIONS = {
    "osc_1_waveform": {
        "range": [0.0, 1.0],
        "mapping": {
            "0.0": "sine",
            "0.33": "triangle",
            "0.66": "saw",
            "1.0": "square",
        },
        "description": "Définit le corps principal du son",
    },
    "osc_2_waveform": {
        "range": [0.0, 1.0],
        "mapping": {
            "0.0": "sine",
            "0.33": "triangle",
            "0.66": "saw",
            "1.0": "square",
        },
        "description": "Couche harmonique secondaire pour épaissir",
    },
    "osc_mix": {
        "range": [0.0, 1.0],
        "description": "Balance de volume entre les deux oscillateurs",
    },
    "osc_2_detune": {
        "range": [0.0, 1.0],
        "description": "Crée de la largeur ou des battements",
    },
    "noise_level": {
        "range": [0.0, 1.0],
        "description": "Simule le souffle et l’impact",
    },
    "filter_cutoff": {
        "range": [0.0, 1.0],
        "description": "Définit la brillance du son",
    },
    "filter_resonance": {
        "range": [0.0, 1.0],
        "description": "Crée le côté acide ou siffleur",
    },
    "filter_type": {
        "range": [0.0, 1.0],
        "mapping": {
            "0.0": "lowpass",
            "0.5": "bandpass",
            "1.0": "highpass",
        },
        "description": "Type de filtre",
    },
    "amp_attack": {
        "range": [0.0, 1.0],
        "description": "Vitesse d'apparition",
    },
    "amp_decay": {
        "range": [0.0, 1.0],
        "description": "Temps de chute vers le niveau de sustain",
    },
    "amp_sustain": {
        "range": [0.0, 1.0],
        "description": "Niveau maintenu tant que la note est pressée",
    },
    "amp_release": {
        "range": [0.0, 1.0],
        "description": "Queue de résonance après relâchement",
    },
    "filter_env_amount": {
        "range": [0.0, 1.0],
        "description": "Intensité de l'enveloppe sur le filtre",
    },
    "filter_env_decay": {
        "range": [0.0, 1.0],
        "description": "Vitesse de fermeture du filtre",
    },
    "lfo_rate": {
        "range": [0.0, 1.0],
        "description": "Vitesse d'oscillation",
    },
    "lfo_to_pitch": {
        "range": [0.0, 1.0],
        "description": "Intensité du vibrato",
    },
    "lfo_to_cutoff": {
        "range": [0.0, 1.0],
        "description": "Création de mouvement sur le timbre",
    },
    "velocity_to_filter": {
        "range": [0.0, 1.0],
        "description": "Sensibilité à la frappe",
    },
    "distortion_mix": {
        "range": [0.0, 1.0],
        "description": "Apporte des harmoniques et salit le son",
    },
    "reverb_mix": {
        "range": [0.0, 1.0],
        "description": "Place le son dans un espace physique",
    },
}


def generate_parameters():
    parameters = {}
    for name in PARAMETER_DEFINITIONS:
        if name in ("osc_1_waveform", "osc_2_waveform"):
            parameters[name] = random.choice([0.0, 0.33, 0.66, 1.0])
        elif name == "filter_type":
            parameters[name] = random.choice([0.0, 0.5, 1.0])
        else:
            parameters[name] = rand()
    return parameters


@app.post("/generate-preset")
def generate_patch(body: AiRequest):
    return build_response(prompt=body.prompt, parameters=generate_parameters())


def build_response(prompt: str, parameters: dict[str, float]):
    """Construit une réponse Harmonia standardisée."""

    return {
        "metadata": {
            "name": prompt[:50],  # ou un nom généré
            "prompt": prompt,
            "generated_by": "Harmonia-AI",
            "model_version": "1.0.0",
            "model_hash": "abcdef1234567890",
        },
        "parameters": {
            name: parameters[name]
            for name in PARAMETER_DEFINITIONS
        },
    }



@app.post("/refine-preset")
def refine_patch(body: RefineRequest):
    """
    Affine un preset existant à partir d'un prompt.

    Pour le moment, le comportement est simulé :
    chaque paramètre existant est légèrement modifié.
    """

    refined_parameters = {}

    for name in PARAMETER_DEFINITIONS:
        current_value = body.parameters.get(name, rand())

        # Petite variation autour de la valeur actuelle
        variation = random.uniform(-0.1, 0.1)

        new_value = max(
            0.0,
            min(1.0, current_value + variation),
        )

        # Les paramètres discrets restent sur leurs valeurs valides.
        if name in ("osc_1_waveform", "osc_2_waveform"):
            new_value = min(
                [0.0, 0.33, 0.66, 1.0],
                key=lambda x: abs(x - new_value),
            )

        elif name == "filter_type":
            new_value = min(
                [0.0, 0.5, 1.0],
                key=lambda x: abs(x - new_value),
            )

        refined_parameters[name] = round(new_value, 4)

    return build_response(
        prompt=body.prompt,
        parameters=refined_parameters,
    )