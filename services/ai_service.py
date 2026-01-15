import os
import requests
from sqlalchemy.orm import Session
from typing import Any, Dict

from schemas.ai import SynthPatchSchema
from services.profile_service import ProfileService
from exceptions.custom_exceptions import (
    NoUrlForAIConfiguredException
)

AI_URL = os.getenv("AI_URL", "http://127.0.0.1:9000/generate_patch")


class AiService:
    def __init__(self, db: Session):
        self.db = db
        self.profile_service = ProfileService(db)

    def call_ai_and_get_patch(self, prompt: str) -> SynthPatchSchema:
        if not AI_URL:
            raise NoUrlForAIConfiguredException("Veuillez configurer l'URL de l'IA.")

        try:
            response = requests.post(
                AI_URL,
                json={"prompt": prompt},
                timeout=15
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"Erreur réseau vers le service IA: {exc}")

        if not response.ok:
            raise RuntimeError(
                f"Service IA a renvoyé un statut {response.status_code}: {response.text}"
            )
        
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(f"Réponse IA invalide: {exc}")

        params = data.get("parameters")
        if not isinstance(params, dict):
            raise RuntimeError("Réponse IA invalide : 'parameters' manquant")
            
        return SynthPatchSchema(
            waveform=str(params.get("waveform", "sine")),
            frequency=float(params.get("frequency", 0.0)),
            volume=float(params.get("volume", 0.0)),
            attack=float(params.get("attack", 0.0)),
            decay=float(params.get("decay", 0.0)),
            sustain=float(params.get("sustain", 0.0)),
            release=float(params.get("release", 0.0)),
            filterType="lowpass",
            cutoff=float(params.get("cutoff", 0.0)),
            resonance=float(params.get("resonance", 0.0)),
        )
