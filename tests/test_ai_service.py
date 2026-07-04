import pytest
from unittest.mock import MagicMock, patch

from services.ai_service import AiService
from exceptions.custom_exceptions import (
    AiNetworkException,
    AiInvalidJsonException,
    AiInvalidResponseException,
    AiBadStatusException,
    NoUrlForAIConfiguredException,
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


TEST_MODEL_ID = "serum-v1"
TEST_MODEL_NAME = "Serum"


def test_ai_url_missing(monkeypatch):
    monkeypatch.setattr("services.ai_service.AI_URL", None)

    service = AiService(make_db())

    with pytest.raises(NoUrlForAIConfiguredException):
        service.call_ai_and_get_patch(
            "hello",
            TEST_MODEL_ID,
            TEST_MODEL_NAME
        )


@patch("services.ai_service.requests.post")
def test_ai_network_error(mock_post, monkeypatch):
    monkeypatch.setattr("services.ai_service.AI_URL", "http://fake.local")

    import requests
    mock_post.side_effect = requests.RequestException("boom")

    service = AiService(make_db())

    with pytest.raises(AiNetworkException):
        service.call_ai_and_get_patch(
            "hello",
            TEST_MODEL_ID,
            TEST_MODEL_NAME
        )


@patch("services.ai_service.requests.post")
def test_ai_bad_status(mock_post, monkeypatch):
    monkeypatch.setattr("services.ai_service.AI_URL", "http://fake.local")

    mock_post.return_value = make_response(
        ok=False,
        status_code=503,
        text="down"
    )

    service = AiService(make_db())

    with pytest.raises(AiBadStatusException):
        service.call_ai_and_get_patch(
            "hello",
            TEST_MODEL_ID,
            TEST_MODEL_NAME
        )


@patch("services.ai_service.requests.post")
def test_ai_invalid_json(mock_post, monkeypatch):
    monkeypatch.setattr("services.ai_service.AI_URL", "http://fake.local")

    mock_post.return_value = make_response(
        ok=True,
        json_raises=True
    )

    service = AiService(make_db())

    with pytest.raises(AiInvalidJsonException):
        service.call_ai_and_get_patch(
            "hello",
            TEST_MODEL_ID,
            TEST_MODEL_NAME
        )


@patch("services.ai_service.requests.post")
def test_ai_invalid_response_missing_parameters(
    mock_post,
    monkeypatch
):
    monkeypatch.setattr("services.ai_service.AI_URL", "http://fake.local")

    mock_post.return_value = make_response(
        ok=True,
        json_data={"nope": 1}
    )

    service = AiService(make_db())

    with pytest.raises(AiInvalidResponseException):
        service.call_ai_and_get_patch(
            "hello",
            TEST_MODEL_ID,
            TEST_MODEL_NAME
        )


@patch("services.ai_service.requests.post")
def test_ai_success_returns_valid_schema(
    mock_post,
    monkeypatch
):
    monkeypatch.setattr("services.ai_service.AI_URL", "http://fake.local")

    fake_response = {
        "metadata": {
            "name": "Warm Analog Pad",
            "prompt": "Warm analog pad",
            "generated_by": "Harmonia-AI",
            "model_version": "1.0.0",
            "model_hash": "abcdef1234567890"
        },
        "parameters": {
            "osc_1_waveform": 0.66,
            "filter_cutoff": 0.24,
            "reverb_mix": 0.57
        }
    }

    mock_post.return_value = make_response(
        ok=True,
        json_data=fake_response
    )

    service = AiService(make_db())

    result = service.call_ai_and_get_patch(
        "hello",
        TEST_MODEL_ID,
        TEST_MODEL_NAME
    )

    assert result is not None
    assert result.metadata.generated_by == "Harmonia-AI"
    assert result.metadata.name == "Warm Analog Pad"

    assert result.parameters["osc_1_waveform"] == 0.66
    assert result.parameters["filter_cutoff"] == 0.24
    assert result.parameters["reverb_mix"] == 0.57