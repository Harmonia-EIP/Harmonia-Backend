import os
import requests
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from schemas.ai import SynthPatchSchema
from services.profile_service import ProfileService
from exceptions.custom_exceptions import (
    AiNetworkException,
    AiBadStatusException,
    AiInvalidJsonException,
    AiInvalidResponseException,
)

AI_URL = os.getenv("AI_URL")


class AiService:
    def __init__(self, db: Session):
        self.db = db
        self.profile_service = ProfileService(db)

    def call_ai_and_get_patch(self, prompt: str) -> Optional[SynthPatchSchema]:
        """
        - Si l'URL IA n'est pas configurée : ne fait rien (return None)
        - Sinon : appelle l'IA et retourne un SynthPatchSchema
        """

        if not AI_URL or not AI_URL.strip():
            return None

        try:
            response = requests.post(
                AI_URL.strip(),
                json={"prompt": prompt},
                timeout=15
            )
        except requests.RequestException as exc:
            raise AiNetworkException(str(exc)) from exc

        if not response.ok:
            raise AiBadStatusException(response.status_code)

        try:
            data: Dict[str, Any] = response.json()
        except ValueError as exc:
            raise AiInvalidJsonException(str(exc)) from exc

        params = data.get("parameters")
        if not isinstance(params, dict):
            raise AiInvalidResponseException(
                "Le champ 'parameters' est manquant ou invalide."
            )

        return SynthPatchSchema(
            waveform=str(params.get("waveform", "sine")),
            frequency=float(params.get("frequency", 0.0)),
            volume=float(params.get("volume", 0.0)),
            attack=float(params.get("attack", 0.0)),
            decay=float(params.get("decay", 0.0)),
            sustain=float(params.get("sustain", 0.0)),
            release=float(params.get("release", 0.0)),
            filterType=str(params.get("filterType", "lowpass")),
            cutoff=float(params.get("cutoff", 0.0)),
            resonance=float(params.get("resonance", 0.0)),
        )