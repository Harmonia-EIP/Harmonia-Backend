import pytest
from unittest.mock import MagicMock, patch

from services.ai_service import AiService
from exceptions.custom_exceptions import (
    AiNetworkException,
    AiBadStatusException,
    AiInvalidJsonException,
    AiInvalidResponseException,
)


def make_db():
    return MagicMock()


def make_response(
    ok=True,
    status_code=200,
    json_data=None,
    json_raises=False,
    text="ERR"
):
    r = MagicMock()

    r.ok = ok
    r.status_code = status_code
    r.text = text

    if json_raises:
        r.json.side_effect = ValueError("bad json")
    else:
        r.json.return_value = json_data if json_data is not None else {}

    return r


def test_ai_url_missing(monkeypatch):
    monkeypatch.setattr(
        "services.ai_service.AI_URL",
        None
    )

    service = AiService(make_db())

    with pytest.raises(AiInvalidResponseException):
        service.call_ai_and_get_patch("hello")


@patch("services.ai_service.requests.post")
def test_ai_network_error(mock_post, monkeypatch):
    monkeypatch.setattr(
        "services.ai_service.AI_URL",
        "http://fake.local"
    )

    import requests

    mock_post.side_effect = requests.RequestException("boom")

    service = AiService(make_db())

    with pytest.raises(AiNetworkException):
        service.call_ai_and_get_patch("hello")


@patch("services.ai_service.requests.post")
def test_ai_bad_status(mock_post, monkeypatch):
    monkeypatch.setattr(
        "services.ai_service.AI_URL",
        "http://fake.local"
    )

    mock_post.return_value = make_response(
        ok=False,
        status_code=503,
        text="down"
    )

    service = AiService(make_db())

    with pytest.raises(AiBadStatusException):
        service.call_ai_and_get_patch("hello")


@patch("services.ai_service.requests.post")
def test_ai_invalid_json(mock_post, monkeypatch):
    monkeypatch.setattr(
        "services.ai_service.AI_URL",
        "http://fake.local"
    )

    mock_post.return_value = make_response(
        ok=True,
        json_raises=True
    )

    service = AiService(make_db())

    with pytest.raises(AiInvalidJsonException):
        service.call_ai_and_get_patch("hello")


@patch("services.ai_service.requests.post")
def test_ai_invalid_response_missing_parameters(
    mock_post,
    monkeypatch
):
    monkeypatch.setattr(
        "services.ai_service.AI_URL",
        "http://fake.local"
    )

    mock_post.return_value = make_response(
        ok=True,
        json_data={"nope": 1}
    )

    service = AiService(make_db())

    with pytest.raises(AiInvalidResponseException):
        service.call_ai_and_get_patch("hello")


@patch("services.ai_service.requests.post")
def test_ai_success_returns_raw_json(
    mock_post,
    monkeypatch
):
    monkeypatch.setattr(
        "services.ai_service.AI_URL",
        "http://fake.local"
    )

    fake_response = {
        "metadata": {
            "prompt": "Warm analog pad",
            "generated_by": "Harmonia-AI",
            "model_version": "1.0.0",
            "model_hash": "abcdef1234567890"
        },

        "parameters": {
            "osc_1_waveform": 0.66,
            "osc_2_waveform": 0.33,

            "osc_mix": 0.58,
            "osc_2_detune": 0.18,
            "noise_level": 0.07,

            "filter_cutoff": 0.24,
            "filter_resonance": 0.31,
            "filter_type": 0.0,

            "amp_attack": 0.72,
            "amp_decay": 0.44,
            "amp_sustain": 0.81,
            "amp_release": 0.76,

            "filter_env_amount": 0.37,
            "filter_env_decay": 0.41,

            "lfo_rate": 0.12,
            "lfo_to_pitch": 0.04,
            "lfo_to_cutoff": 0.19,

            "velocity_to_filter": 0.43,

            "distortion_mix": 0.02,
            "reverb_mix": 0.57
        }
    }

    mock_post.return_value = make_response(
        ok=True,
        json_data=fake_response
    )

    service = AiService(make_db())

    result = service.call_ai_and_get_patch(
        "hello"
    )

    assert isinstance(result, dict)

    assert "metadata" in result
    assert "parameters" in result

    assert (
        result["metadata"]["generated_by"]
        == "Harmonia-AI"
    )

    assert (
        result["parameters"]["osc_1_waveform"]
        == 0.66
    )

    assert (
        result["parameters"]["filter_cutoff"]
        == 0.24
    )

    assert (
        result["parameters"]["reverb_mix"]
        == 0.57
    )