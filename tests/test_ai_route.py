from unittest.mock import patch

import pytest

from exceptions.custom_exceptions import (
    AiBadStatusException,
    AiInvalidJsonException,
    AiInvalidResponseException,
    AiNetworkException,
    ErrorCode,
    NoPermissionException,
    NoUrlForAIConfiguredException,
    TokenMissingException,
)
from routes.ai import router as ai_router
from schemas.ai import PresetCharterSchema
from tests.helpers import assert_error

HEADERS = {"Authorization": "Bearer tok"}

PRESET = {
    "metadata": {
        "name": "Warm Analog Pad",
        "prompt": "Warm analog pad",
        "generated_by": "Harmonia-AI",
        "model_version": "1.0.0",
        "model_hash": "abcdef1234567890",
    },
    "parameters": {"filter_cutoff": 0.24, "reverb_mix": 0.57},
}

GENERATE_BODY = {"prompt": "warm pad", "model_id": 1, "model_name": "Serum"}
REFINE_BODY = {
    "prompt": "brighter",
    "current_preset": {**PRESET},
    "locked_params": ["reverb_mix"],
    "model_id": 1,
    "model_name": "Serum",
}

# (exception levée par le service, status attendu, error_code attendu, detail attendu)
AI_ERRORS = [
    (
        NoUrlForAIConfiguredException(),
        500,
        ErrorCode.AI_URL_NOT_CONFIGURED,
        "No URL configured for AI service.",
    ),
    (
        AiNetworkException(),
        502,
        ErrorCode.AI_NETWORK_ERROR,
        "Network error while calling AI service.",
    ),
    (
        AiBadStatusException(503),
        502,
        ErrorCode.AI_BAD_STATUS,
        "AI service returned an invalid HTTP status (503).",
    ),
    (
        AiInvalidJsonException(),
        500,
        ErrorCode.AI_INVALID_JSON,
        "Invalid AI response (invalid JSON).",
    ),
    (
        AiInvalidResponseException(),
        500,
        ErrorCode.AI_INVALID_RESPONSE,
        "Invalid AI response structure.",
    ),
]
AI_ERRORS_IDS = [code.value for _, _, code, _ in AI_ERRORS]


@pytest.fixture()
def client(make_client):
    return make_client(ai_router)


@pytest.fixture()
def mocks():
    with (
        patch("routes.ai.ProfileService") as profile_cls,
        patch("routes.ai.AiService") as ai_cls,
    ):
        yield profile_cls.return_value, ai_cls.return_value


# ---------------- /generate-preset ----------------


def test_generate_preset_ok(client, mocks):
    profile, ai = mocks
    ai.generate_preset_from_prompt.return_value = PresetCharterSchema(**PRESET)

    res = client.post("/generate-preset", json=GENERATE_BODY, headers=HEADERS)

    assert res.status_code == 200
    assert res.json()["metadata"]["name"] == "Warm Analog Pad"
    profile.ensure_active_user_from_token.assert_called_once_with("Bearer tok")
    ai.generate_preset_from_prompt.assert_called_once_with(
        prompt="warm pad", model_id=1, model_name="Serum", variation=None
    )


def test_generate_preset_forwards_variation(client, mocks):
    _, ai = mocks
    ai.generate_preset_from_prompt.return_value = PresetCharterSchema(**PRESET)
    body = {"prompt": "porte qui claque", "model_name": "harmonia_v2", "variation": 2}

    res = client.post("/generate-preset", json=body, headers=HEADERS)

    assert res.status_code == 200
    kwargs = ai.generate_preset_from_prompt.call_args.kwargs
    assert kwargs["model_name"] == "harmonia_v2"
    assert kwargs["variation"] == 2


def test_generate_preset_rejects_negative_variation(client, mocks):
    _, ai = mocks

    res = client.post(
        "/generate-preset", json={**GENERATE_BODY, "variation": -1}, headers=HEADERS
    )

    assert_error(res, 422, ErrorCode.VALIDATION_ERROR)
    ai.generate_preset_from_prompt.assert_not_called()


def test_generate_preset_requires_auth(client, mocks):
    profile, ai = mocks
    profile.ensure_active_user_from_token.side_effect = TokenMissingException()

    res = client.post("/generate-preset", json=GENERATE_BODY)

    assert_error(res, 401, ErrorCode.TOKEN_MISSING, "Missing token.")
    profile.ensure_active_user_from_token.assert_called_once_with(None)
    ai.generate_preset_from_prompt.assert_not_called()


def test_generate_preset_inactive_user(client, mocks):
    profile, ai = mocks
    profile.ensure_active_user_from_token.side_effect = NoPermissionException(
        "inactive"
    )

    res = client.post("/generate-preset", json=GENERATE_BODY, headers=HEADERS)

    assert_error(res, 403, ErrorCode.NO_PERMISSION, "inactive")
    ai.generate_preset_from_prompt.assert_not_called()


@pytest.mark.parametrize("exc, status_code, code, detail", AI_ERRORS, ids=AI_ERRORS_IDS)
def test_generate_preset_propagates_ai_errors(
    client, mocks, exc, status_code, code, detail
):
    _, ai = mocks
    ai.generate_preset_from_prompt.side_effect = exc

    res = client.post("/generate-preset", json=GENERATE_BODY, headers=HEADERS)

    assert_error(res, status_code, code, detail)


def test_generate_preset_invalid_body_is_422(client, mocks):
    res = client.post("/generate-preset", json={}, headers=HEADERS)

    assert_error(res, 422, ErrorCode.VALIDATION_ERROR)


# ---------------- /refine-preset ----------------


def test_refine_preset_ok(client, mocks):
    profile, ai = mocks
    ai.refine_preset_from_prompt.return_value = PresetCharterSchema(**PRESET)

    res = client.post("/refine-preset", json=REFINE_BODY, headers=HEADERS)

    assert res.status_code == 200
    profile.ensure_active_user_from_token.assert_called_once_with("Bearer tok")
    kwargs = ai.refine_preset_from_prompt.call_args.kwargs
    assert kwargs["prompt"] == "brighter"
    assert kwargs["current_parameters"] == PRESET["parameters"]
    assert kwargs["locked_params"] == ["reverb_mix"]
    assert kwargs["model_id"] == 1
    assert kwargs["model_name"] == "Serum"


def test_refine_preset_requires_auth(client, mocks):
    profile, ai = mocks
    profile.ensure_active_user_from_token.side_effect = TokenMissingException()

    res = client.post("/refine-preset", json=REFINE_BODY)

    assert_error(res, 401, ErrorCode.TOKEN_MISSING, "Missing token.")
    ai.refine_preset_from_prompt.assert_not_called()


@pytest.mark.parametrize("exc, status_code, code, detail", AI_ERRORS, ids=AI_ERRORS_IDS)
def test_refine_preset_propagates_ai_errors(
    client, mocks, exc, status_code, code, detail
):
    _, ai = mocks
    ai.refine_preset_from_prompt.side_effect = exc

    res = client.post("/refine-preset", json=REFINE_BODY, headers=HEADERS)

    assert_error(res, status_code, code, detail)


def test_refine_preset_invalid_body_is_422(client, mocks):
    res = client.post("/refine-preset", json={"prompt": "x"}, headers=HEADERS)

    assert_error(res, 422, ErrorCode.VALIDATION_ERROR)
