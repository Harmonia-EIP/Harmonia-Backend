import logging
import os

import requests
from sqlalchemy.orm import Session

from exceptions.custom_exceptions import (
    AiBadStatusException,
    AiInvalidJsonException,
    AiInvalidResponseException,
    AiNetworkException,
    NoUrlForAIConfiguredException,
)
from schemas.ai import AIModelListSchema, HistoryEntryRefSchema, PresetCharterSchema
from services.history_service import HistoryService
from services.profile_service import ProfileService

logger = logging.getLogger(__name__)

AI_URL = os.getenv("AI_URL")

GENERATE_PATH = "generate-preset"
REFINE_PATH = "refine-preset"
MODELS_PATH = "models"


def _build_ai_url(path: str) -> str:
    """Construit l'URL d'un endpoint IA à partir de AI_URL.

    Accepte une URL de base (http://host:5000) ou une URL qui se termine
    déjà par un des endpoints (http://host:5000/generate-preset).
    """
    if not AI_URL or not AI_URL.strip():
        raise NoUrlForAIConfiguredException()

    base = AI_URL.strip().rstrip("/")

    for known in (GENERATE_PATH, REFINE_PATH, MODELS_PATH):
        if base.endswith("/" + known):
            base = base[: -(len(known) + 1)]
            break

    return f"{base}/{path}"


class AiService:
    def __init__(self, db: Session):
        self.db = db
        self.profile_service = ProfileService(db)
        self.history_service = HistoryService(db)

    def list_models(self) -> AIModelListSchema:
        """Récupère la liste des modèles disponibles auprès du serveur IA."""
        data = self._get_from_ai(_build_ai_url(MODELS_PATH))
        try:
            return AIModelListSchema(**data)
        except Exception as exc:
            raise AiInvalidResponseException(str(exc)) from exc

    def generate_preset_from_prompt(
        self,
        prompt: str,
        model_id: int | str | None,
        model_name: str | None,
        user_id: int | None = None,
    ) -> PresetCharterSchema:
        """Génère un nouveau preset à partir d'un prompt."""

        data = self._post_to_ai(
            _build_ai_url(GENERATE_PATH),
            {"prompt": prompt, "model_id": model_id, "model_name": model_name},
        )
        preset = self._parse_preset(data)

        preset.history_entry = self._save_history(user_id, "generate", prompt, preset)
        return preset

    def refine_preset_from_prompt(
        self,
        prompt: str,
        current_parameters: dict[str, float],
        locked_params: list[str],
        model_id: int | str | None,
        model_name: str | None,
        user_id: int | None = None,
    ) -> PresetCharterSchema:
        """Affine un preset existant. Les paramètres verrouillés sont forcés
        à leur valeur d'origine, quelle que soit la réponse de l'IA."""

        data = self._post_to_ai(
            _build_ai_url(REFINE_PATH),
            {
                "prompt": prompt,
                "parameters": current_parameters,
                "locked_params": locked_params,
                "model_id": model_id,
                "model_name": model_name,
            },
        )

        # Filet de sécurité côté backend : on restaure les valeurs verrouillées
        # avant la validation du schéma.
        returned = data.get("parameters") if isinstance(data, dict) else None
        if isinstance(returned, dict):
            for name in locked_params:
                if name in current_parameters:
                    returned[name] = current_parameters[name]

        preset = self._parse_preset(data)

        preset.history_entry = self._save_history(user_id, "refine", prompt, preset)
        return preset

    # ------------------------------------------------------------------
    def _save_history(
        self,
        user_id: int | None,
        type_: str,
        prompt: str,
        preset: PresetCharterSchema,
    ) -> HistoryEntryRefSchema | None:
        """Enregistre le nom et les paramètres du preset dans l'historique et
        renvoie l'entrée créée (id inclus).

        L'historique ne doit jamais faire échouer une génération réussie :
        en cas d'erreur on logue, on renvoie None et on continue.
        """
        if user_id is None:
            return None

        try:
            name = preset.metadata.name or prompt.strip()
            entry = self.history_service.add(
                user_id, name, type_, dict(preset.parameters)
            )
            return HistoryEntryRefSchema(
                id=entry.id,
                name=entry.name,
                type=entry.type,
                created_at=entry.created_at,
                last_used_at=entry.last_used_at,
            )
        except Exception:
            self.db.rollback()
            logger.exception("Impossible d'enregistrer l'historique")
            return None

    @staticmethod
    def _get_from_ai(url: str):
        try:
            response = requests.get(url, timeout=10)
        except requests.RequestException as exc:
            raise AiNetworkException(str(exc)) from exc

        if not response.ok:
            raise AiBadStatusException(response.status_code)

        try:
            return response.json()
        except ValueError as exc:
            raise AiInvalidJsonException(str(exc)) from exc

    @staticmethod
    def _post_to_ai(url: str, body: dict):
        # On n'envoie pas les champs vides (model_id / model_name absents).
        body = {k: v for k, v in body.items() if v is not None}
        try:
            response = requests.post(url, json=body, timeout=30)
        except requests.RequestException as exc:
            raise AiNetworkException(str(exc)) from exc

        if not response.ok:
            raise AiBadStatusException(response.status_code)

        try:
            return response.json()
        except ValueError as exc:
            raise AiInvalidJsonException(str(exc)) from exc

    @staticmethod
    def _parse_preset(data) -> PresetCharterSchema:
        if (
            not isinstance(data, dict)
            or "parameters" not in data
            or "metadata" not in data
        ):
            raise AiInvalidResponseException(
                "Réponse IA invalide : 'metadata' ou 'parameters' manquant."
            )

        try:
            return PresetCharterSchema(**data)
        except Exception as exc:
            raise AiInvalidResponseException(str(exc)) from exc
