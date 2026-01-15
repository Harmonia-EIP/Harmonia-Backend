import pytest
from unittest.mock import MagicMock, patch

from services.ai_service import AiService
from exceptions.custom_exceptions import (
    AiNetworkException,
    AiBadStatusException,
    AiInvalidJsonException,
    AiInvalidResponseException,
)

# Si votre SynthPatchSchema est un Pydantic model, c'est ok.
# Sinon, adaptez les asserts.
from schemas.ai import SynthPatchSchema


def make_db():
    return MagicMock()


def make_response(ok=True, status_code=200, json_data=None, json_raises=False, text="ERR"):
    r = MagicMock()
    r.ok = ok
    r.status_code = status_code
    r.text = text

    if json_raises:
        r.json.side_effect = ValueError("bad json")
    else:
        r.json.return_value = json_data if json_data is not None else {}

    return r


def test_ai_url_missing_returns_none(monkeypatch):
    # AI_URL est lu au runtime via variable globale dans services.ai_service
    monkeypatch.setattr("services.ai_service.AI_URL", None)

    service = AiService(make_db())
    res = service.call_ai_and_get_patch("hello")
    assert res is None


@patch("services.ai_service.requests.post")
def test_ai_network_error(mock_post, monkeypatch):
    monkeypatch.setattr("services.ai_service.AI_URL", "http://fake.local")

    mock_post.side_effect = Exception("boom")  # requests.RequestException ou autre
    # votre code catch requests.RequestException; on simule précisément :
    import requests
    mock_post.side_effect = requests.RequestException("boom")

    service = AiService(make_db())
    with pytest.raises(AiNetworkException):
        service.call_ai_and_get_patch("hello")


@patch("services.ai_service.requests.post")
def test_ai_bad_status(mock_post, monkeypatch):
    monkeypatch.setattr("services.ai_service.AI_URL", "http://fake.local")

    mock_post.return_value = make_response(ok=False, status_code=503, text="down")
    service = AiService(make_db())

    with pytest.raises(AiBadStatusException):
        service.call_ai_and_get_patch("hello")


@patch("services.ai_service.requests.post")
def test_ai_invalid_json(mock_post, monkeypatch):
    monkeypatch.setattr("services.ai_service.AI_URL", "http://fake.local")

    mock_post.return_value = make_response(ok=True, json_raises=True)
    service = AiService(make_db())

    with pytest.raises(AiInvalidJsonException):
        service.call_ai_and_get_patch("hello")


@patch("services.ai_service.requests.post")
def test_ai_invalid_response_missing_parameters(mock_post, monkeypatch):
    monkeypatch.setattr("services.ai_service.AI_URL", "http://fake.local")

    mock_post.return_value = make_response(ok=True, json_data={"nope": 1})
    service = AiService(make_db())

    with pytest.raises(AiInvalidResponseException):
        service.call_ai_and_get_patch("hello")


@patch("services.ai_service.requests.post")
def test_ai_success_builds_patch(mock_post, monkeypatch):
    monkeypatch.setattr("services.ai_service.AI_URL", "http://fake.local")

    mock_post.return_value = make_response(
        ok=True,
        json_data={
            "parameters": {
                "waveform": "square",
                "frequency": 440,
                "volume": 0.5,
                "attack": 0.01,
                "decay": 0.2,
                "sustain": 0.7,
                "release": 0.4,
                "filterType": "lowpass",
                "cutoff": 1200,
                "resonance": 0.8,
            }
        },
    )

    service = AiService(make_db())
    patch_obj = service.call_ai_and_get_patch("hello")

    assert isinstance(patch_obj, SynthPatchSchema)
    assert patch_obj.waveform == "square"
    assert float(patch_obj.frequency) == 440.0
    assert float(patch_obj.volume) == 0.5
    assert float(patch_obj.cutoff) == 1200.0
    assert float(patch_obj.resonance) == 0.8
