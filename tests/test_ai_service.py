from unittest.mock import MagicMock, patch

import pytest
import requests

from exceptions.custom_exceptions import (
    AiBadStatusException,
    AiInvalidJsonException,
    AiInvalidResponseException,
    AiNetworkException,
    NoUrlForAIConfiguredException,
)
from services import ai_service
from services.ai_service import AiService, _build_ai_url

BASE = "http://fake.local"

VALID_RESPONSE = {
    "metadata": {
        "name": "Warm Analog Pad",
        "prompt": "Warm analog pad",
        "generated_by": "Harmonia-AI",
        "model_version": "1.0.0",
        "model_hash": "abcdef1234567890",
    },
    "parameters": {
        "osc_1_waveform": 0.66,
        "filter_cutoff": 0.24,
        "reverb_mix": 0.57,
    },
}


def make_response(ok=True, status_code=200, json_data=None, json_raises=False):
    r = MagicMock()
    r.ok = ok
    r.status_code = status_code
    if json_raises:
        r.json.side_effect = ValueError("bad json")
    else:
        r.json.return_value = json_data if json_data is not None else {}
    return r


def valid_copy():
    import copy

    return copy.deepcopy(VALID_RESPONSE)


@pytest.fixture(autouse=True)
def ai_url(monkeypatch):
    monkeypatch.setattr("services.ai_service.AI_URL", BASE)


@pytest.fixture()
def service():
    return AiService(MagicMock())


# ----------------------------------------------------------------------
# _build_ai_url
# ----------------------------------------------------------------------


@pytest.mark.parametrize("value", [None, "", "   "])
def test_build_url_missing_or_blank(monkeypatch, value):
    monkeypatch.setattr("services.ai_service.AI_URL", value)
    with pytest.raises(NoUrlForAIConfiguredException):
        _build_ai_url("generate-preset")


@pytest.mark.parametrize(
    "configured",
    [
        "http://host:5000",
        "http://host:5000/",
        "  http://host:5000  ",
        "http://host:5000/generate-preset",
        "http://host:5000/refine-preset",
        "http://host:5000/generate-preset/",
    ],
)
@pytest.mark.parametrize("path", ["generate-preset", "refine-preset"])
def test_build_url_normalises(monkeypatch, configured, path):
    monkeypatch.setattr("services.ai_service.AI_URL", configured)
    assert _build_ai_url(path) == f"http://host:5000/{path}"


def test_build_url_keeps_sub_path(monkeypatch):
    monkeypatch.setattr("services.ai_service.AI_URL", "http://host/api/v1")
    assert _build_ai_url("refine-preset") == "http://host/api/v1/refine-preset"


def test_service_builds_profile_service():
    db = MagicMock()
    svc = AiService(db)
    assert svc.db is db
    assert svc.profile_service.db is db


# ----------------------------------------------------------------------
# generate_preset_from_prompt
# ----------------------------------------------------------------------


def test_generate_url_missing(monkeypatch, service):
    monkeypatch.setattr("services.ai_service.AI_URL", None)
    with pytest.raises(NoUrlForAIConfiguredException):
        service.generate_preset_from_prompt("hello", 1, "Serum")


@patch("services.ai_service.requests.post")
def test_generate_network_error(mock_post, service):
    mock_post.side_effect = requests.RequestException("boom")
    with pytest.raises(AiNetworkException):
        service.generate_preset_from_prompt("hello", 1, "Serum")


@patch("services.ai_service.requests.post")
def test_generate_timeout_is_network_error(mock_post, service):
    mock_post.side_effect = requests.Timeout("slow")
    with pytest.raises(AiNetworkException):
        service.generate_preset_from_prompt("hello", 1, "Serum")


@pytest.mark.parametrize("status", [400, 401, 404, 500, 503])
@patch("services.ai_service.requests.post")
def test_generate_bad_status(mock_post, status, service):
    mock_post.return_value = make_response(ok=False, status_code=status)
    with pytest.raises(AiBadStatusException):
        service.generate_preset_from_prompt("hello", 1, "Serum")


@patch("services.ai_service.requests.post")
def test_generate_invalid_json(mock_post, service):
    mock_post.return_value = make_response(json_raises=True)
    with pytest.raises(AiInvalidJsonException):
        service.generate_preset_from_prompt("hello", 1, "Serum")


@pytest.mark.parametrize(
    "payload",
    [
        {"nope": 1},
        {"metadata": VALID_RESPONSE["metadata"]},
        {"parameters": VALID_RESPONSE["parameters"]},
        ["not", "a", "dict"],
        "string",
    ],
)
@patch("services.ai_service.requests.post")
def test_generate_invalid_response_shape(mock_post, payload, service):
    mock_post.return_value = make_response(json_data=payload)
    with pytest.raises(AiInvalidResponseException):
        service.generate_preset_from_prompt("hello", 1, "Serum")


@patch("services.ai_service.requests.post")
def test_generate_schema_validation_failure(mock_post, service):
    data = valid_copy()
    data["parameters"] = "not-a-dict"
    mock_post.return_value = make_response(json_data=data)
    with pytest.raises(AiInvalidResponseException):
        service.generate_preset_from_prompt("hello", 1, "Serum")


@patch("services.ai_service.requests.post")
def test_generate_success(mock_post, service):
    mock_post.return_value = make_response(json_data=valid_copy())

    result = service.generate_preset_from_prompt("hello", 1, "Serum")

    assert result.metadata.generated_by == "Harmonia-AI"
    assert result.metadata.name == "Warm Analog Pad"
    assert result.parameters["osc_1_waveform"] == 0.66
    assert result.parameters["filter_cutoff"] == 0.24
    assert result.parameters["reverb_mix"] == 0.57


@patch("services.ai_service.requests.post")
def test_generate_forwards_body_and_url(mock_post, service):
    mock_post.return_value = make_response(json_data=valid_copy())

    service.generate_preset_from_prompt("hello", 2, "charter_v1")

    args, kwargs = mock_post.call_args
    assert args[0] == f"{BASE}/generate-preset"
    assert kwargs["json"] == {
        "prompt": "hello",
        "model_id": 2,
        "model_name": "charter_v1",
    }
    assert kwargs["timeout"] == 30


# ----------------------------------------------------------------------
# refine_preset_from_prompt
# ----------------------------------------------------------------------


@patch("services.ai_service.requests.post")
def test_refine_forwards_body_and_url(mock_post, service):
    mock_post.return_value = make_response(json_data=valid_copy())
    current = {"filter_cutoff": 0.5}

    service.refine_preset_from_prompt("brighter", current, ["filter_cutoff"], 3, "m")

    args, kwargs = mock_post.call_args
    assert args[0] == f"{BASE}/refine-preset"
    assert kwargs["json"] == {
        "prompt": "brighter",
        "parameters": current,
        "locked_params": ["filter_cutoff"],
        "model_id": 3,
        "model_name": "m",
    }


@patch("services.ai_service.requests.post")
def test_refine_restores_locked_params(mock_post, service):
    data = valid_copy()
    data["parameters"] = {"a": 0.9, "b": 0.5}
    mock_post.return_value = make_response(json_data=data)

    result = service.refine_preset_from_prompt("x", {"a": 0.1, "b": 0.2}, ["a"], 1, "m")

    assert result.parameters["a"] == 0.1  # verrouillé -> valeur d'origine
    assert result.parameters["b"] == 0.5  # libre -> valeur de l'IA


@patch("services.ai_service.requests.post")
def test_refine_locked_param_unknown_in_current_is_ignored(mock_post, service):
    data = valid_copy()
    data["parameters"] = {"a": 0.9}
    mock_post.return_value = make_response(json_data=data)

    result = service.refine_preset_from_prompt("x", {"a": 0.1}, ["ghost"], 1, "m")

    assert result.parameters["a"] == 0.9
    assert "ghost" not in result.parameters


@patch("services.ai_service.requests.post")
def test_refine_locked_param_missing_from_ai_response_is_added(mock_post, service):
    data = valid_copy()
    data["parameters"] = {"b": 0.5}
    mock_post.return_value = make_response(json_data=data)

    result = service.refine_preset_from_prompt("x", {"a": 0.1, "b": 0.2}, ["a"], 1, "m")

    assert result.parameters["a"] == 0.1


@patch("services.ai_service.requests.post")
def test_refine_no_locked_params_keeps_ai_values(mock_post, service):
    data = valid_copy()
    data["parameters"] = {"a": 0.9}
    mock_post.return_value = make_response(json_data=data)

    result = service.refine_preset_from_prompt("x", {"a": 0.1}, [], 1, "m")

    assert result.parameters["a"] == 0.9


@patch("services.ai_service.requests.post")
def test_refine_invalid_response(mock_post, service):
    mock_post.return_value = make_response(json_data={"nope": 1})
    with pytest.raises(AiInvalidResponseException):
        service.refine_preset_from_prompt("x", {"a": 0.1}, ["a"], 1, "m")


@patch("services.ai_service.requests.post")
def test_refine_non_dict_parameters_do_not_crash_before_validation(mock_post, service):
    data = valid_copy()
    data["parameters"] = "oops"
    mock_post.return_value = make_response(json_data=data)
    with pytest.raises(AiInvalidResponseException):
        service.refine_preset_from_prompt("x", {"a": 0.1}, ["a"], 1, "m")


@patch("services.ai_service.requests.post")
def test_refine_network_and_status_errors(mock_post, service):
    mock_post.side_effect = requests.RequestException("down")
    with pytest.raises(AiNetworkException):
        service.refine_preset_from_prompt("x", {}, [], 1, "m")

    mock_post.side_effect = None
    mock_post.return_value = make_response(ok=False, status_code=500)
    with pytest.raises(AiBadStatusException):
        service.refine_preset_from_prompt("x", {}, [], 1, "m")

    mock_post.return_value = make_response(json_raises=True)
    with pytest.raises(AiInvalidJsonException):
        service.refine_preset_from_prompt("x", {}, [], 1, "m")


def test_constants():
    assert ai_service.GENERATE_PATH == "generate-preset"
    assert ai_service.REFINE_PATH == "refine-preset"
