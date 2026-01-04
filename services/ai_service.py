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
            data: Dict[str, Any] = response.json()
        except ValueError:
            raise RuntimeError("Réponse IA invalide (JSON non parsable)")

        return SynthPatchSchema(**data)
