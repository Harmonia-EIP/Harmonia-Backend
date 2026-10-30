"""Tests de l'intégration historique dans AiService (_save_history,
generate_preset_from_prompt, refine_preset_from_prompt), y compris
l'enregistrement du modèle IA utilisé (model_id / model_name)."""

import copy
import logging
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from exceptions.custom_exceptions import AiNetworkException
from services.ai_service import AiService

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

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


def fake_preset(name="Warm Pad", parameters=None):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name),
        parameters=parameters if parameters is not None else {"cutoff": 0.5},
    )


def fake_entry(
    type_="generate",
    name="Warm Pad",
    id_=3,
    model_id=None,
    model_name=None,
):
    return SimpleNamespace(
        id=id_,
        name=name,
        type=type_,
        model_id=model_id,
        model_name=model_name,
        created_at=NOW,
        last_used_at=NOW,
    )


@pytest.fixture()
def svc():
    with (
        patch("services.ai_service.ProfileService"),
        patch("services.ai_service.HistoryService") as history_cls,
        patch("services.ai_service.AI_URL", "http://ai:5000"),
    ):
        db = MagicMock()
        yield AiService(db), db, history_cls.return_value


# =========================
# _save_history
# =========================


def test_save_history_without_user_returns_none(svc):
    service, _, history = svc

    res = service._save_history(None, "generate", "prompt", fake_preset())

    assert res is None
    history.add.assert_not_called()


def test_save_history_calls_history_service(svc):
    service, _, history = svc
    history.add.return_value = fake_entry()
    preset = fake_preset(name="Warm Pad", parameters={"cutoff": 0.5})

    service._save_history(7, "generate", "warm pad", preset)

    history.add.assert_called_once_with(
        7, "Warm Pad", "generate", {"cutoff": 0.5}, model_id=None, model_name=None
    )


def test_save_history_passes_model_to_history_service(svc):
    service, _, history = svc
    history.add.return_value = fake_entry(model_id="1", model_name="Serum")

    service._save_history(7, "generate", "warm pad", fake_preset(), 1, "Serum")

    kwargs = history.add.call_args.kwargs
    assert kwargs == {"model_id": 1, "model_name": "Serum"}


def test_save_history_returns_entry_reference(svc):
    service, _, history = svc
    history.add.return_value = fake_entry(type_="refine", name="Brighter", id_=12)

    res = service._save_history(7, "refine", "brighter", fake_preset("Brighter"))

    assert res.id == 12
    assert res.name == "Brighter"
    assert res.type == "refine"
    assert res.created_at == NOW
    assert res.last_used_at == NOW


def test_save_history_reference_exposes_model(svc):
    service, _, history = svc
    history.add.return_value = fake_entry(model_id="1", model_name="Serum")

    res = service._save_history(7, "generate", "p", fake_preset(), 1, "Serum")

    assert res.model_id == "1"
    assert res.model_name == "Serum"


def test_save_history_reference_model_is_none_when_not_provided(svc):
    service, _, history = svc
    history.add.return_value = fake_entry()

    res = service._save_history(7, "generate", "p", fake_preset())

    assert res.model_id is None
    assert res.model_name is None


@pytest.mark.parametrize("empty_name", ["", None])
def test_save_history_falls_back_to_stripped_prompt(svc, empty_name):
    service, _, history = svc
    history.add.return_value = fake_entry()

    service._save_history(7, "generate", "  my prompt  ", fake_preset(empty_name))

    assert history.add.call_args.args[1] == "my prompt"


def test_save_history_passes_a_copy_of_parameters(svc):
    service, _, history = svc
    history.add.return_value = fake_entry()
    params = {"cutoff": 0.5}

    service._save_history(7, "generate", "p", fake_preset(parameters=params))

    sent = history.add.call_args.args[3]
    assert sent == params
    assert sent is not params


def test_save_history_failure_is_swallowed_and_rolled_back(svc, caplog):
    service, db, history = svc
    history.add.side_effect = RuntimeError("db down")

    with caplog.at_level(logging.ERROR):
        res = service._save_history(7, "generate", "p", fake_preset())

    assert res is None
    db.rollback.assert_called_once()
    assert any("historique" in r.getMessage() for r in caplog.records)


# =========================
# generate_preset_from_prompt
# =========================


@patch.object(AiService, "_post_to_ai")
def test_generate_attaches_history_entry(mock_post, svc):
    service, _, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)
    history.add.return_value = fake_entry(id_=3, model_id="1", model_name="Serum")

    preset = service.generate_preset_from_prompt("warm pad", 1, "Serum", user_id=7)

    assert preset.history_entry.id == 3
    history.add.assert_called_once_with(
        7,
        "Warm Analog Pad",
        "generate",
        PRESET["parameters"],
        model_id=1,
        model_name="Serum",
    )


@patch.object(AiService, "_post_to_ai")
def test_generate_stores_model_in_history(mock_post, svc):
    service, _, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)
    history.add.return_value = fake_entry(model_id="1", model_name="Serum")

    preset = service.generate_preset_from_prompt("warm pad", 1, "Serum", user_id=7)

    assert history.add.call_args.kwargs == {"model_id": 1, "model_name": "Serum"}
    assert preset.history_entry.model_id == "1"
    assert preset.history_entry.model_name == "Serum"


@patch.object(AiService, "_post_to_ai")
def test_generate_without_model_stores_none(mock_post, svc):
    service, _, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)
    history.add.return_value = fake_entry()

    preset = service.generate_preset_from_prompt("warm pad", None, None, user_id=7)

    assert history.add.call_args.kwargs == {"model_id": None, "model_name": None}
    assert preset.history_entry.model_id is None
    assert preset.history_entry.model_name is None


@patch.object(AiService, "_post_to_ai")
def test_generate_sends_expected_request_to_ai(mock_post, svc):
    service, _, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)
    history.add.return_value = fake_entry()

    service.generate_preset_from_prompt("warm pad", 1, "Serum", user_id=7)

    url, body = mock_post.call_args.args
    assert url == "http://ai:5000/generate-preset"
    assert body == {"prompt": "warm pad", "model_id": 1, "model_name": "Serum"}


@patch.object(AiService, "_post_to_ai")
def test_generate_without_user_id_skips_history(mock_post, svc):
    service, _, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)

    preset = service.generate_preset_from_prompt("warm pad", 1, "Serum")

    assert preset.history_entry is None
    history.add.assert_not_called()


@patch.object(AiService, "_post_to_ai")
def test_generate_survives_history_failure(mock_post, svc):
    service, db, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)
    history.add.side_effect = RuntimeError("db down")

    preset = service.generate_preset_from_prompt("warm pad", 1, "Serum", user_id=7)

    assert preset.metadata.name == "Warm Analog Pad"
    assert preset.history_entry is None
    db.rollback.assert_called_once()


@patch.object(AiService, "_post_to_ai", side_effect=AiNetworkException())
def test_generate_ai_error_does_not_write_history(_mock_post, svc):
    service, _, history = svc

    with pytest.raises(AiNetworkException):
        service.generate_preset_from_prompt("warm pad", 1, "Serum", user_id=7)

    history.add.assert_not_called()


# =========================
# refine_preset_from_prompt
# =========================


@patch.object(AiService, "_post_to_ai")
def test_refine_attaches_history_entry_with_refine_type(mock_post, svc):
    service, _, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)
    history.add.return_value = fake_entry(type_="refine", id_=9)

    preset = service.refine_preset_from_prompt(
        "brighter",
        {"filter_cutoff": 0.1, "reverb_mix": 0.9},
        [],
        1,
        "Serum",
        user_id=7,
    )

    assert preset.history_entry.id == 9
    assert history.add.call_args.args[0] == 7
    assert history.add.call_args.args[2] == "refine"


@patch.object(AiService, "_post_to_ai")
def test_refine_stores_model_in_history(mock_post, svc):
    service, _, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)
    history.add.return_value = fake_entry(
        type_="refine", model_id="1", model_name="Serum"
    )

    preset = service.refine_preset_from_prompt(
        "brighter", {"filter_cutoff": 0.1}, [], 1, "Serum", user_id=7
    )

    assert history.add.call_args.kwargs == {"model_id": 1, "model_name": "Serum"}
    assert preset.history_entry.model_id == "1"
    assert preset.history_entry.model_name == "Serum"


@patch.object(AiService, "_post_to_ai")
def test_refine_restores_locked_params_before_saving_history(mock_post, svc):
    service, _, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)  # l'IA renvoie reverb_mix = 0.57
    history.add.return_value = fake_entry(type_="refine")

    preset = service.refine_preset_from_prompt(
        "brighter",
        {"filter_cutoff": 0.1, "reverb_mix": 0.9},
        ["reverb_mix"],
        1,
        "Serum",
        user_id=7,
    )

    assert preset.parameters["reverb_mix"] == 0.9
    assert preset.parameters["filter_cutoff"] == 0.24
    saved_params = history.add.call_args.args[3]
    assert saved_params["reverb_mix"] == 0.9


@patch.object(AiService, "_post_to_ai")
def test_refine_ignores_locked_param_absent_from_current_parameters(mock_post, svc):
    service, _, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)
    history.add.return_value = fake_entry(type_="refine")

    preset = service.refine_preset_from_prompt(
        "brighter", {"filter_cutoff": 0.1}, ["unknown_param"], 1, "Serum", user_id=7
    )

    assert "unknown_param" not in preset.parameters


@patch.object(AiService, "_post_to_ai")
def test_refine_sends_expected_request_to_ai(mock_post, svc):
    service, _, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)
    history.add.return_value = fake_entry(type_="refine")

    service.refine_preset_from_prompt(
        "brighter", {"filter_cutoff": 0.1}, ["filter_cutoff"], 1, "Serum", user_id=7
    )

    url, body = mock_post.call_args.args
    assert url == "http://ai:5000/refine-preset"
    assert body == {
        "prompt": "brighter",
        "parameters": {"filter_cutoff": 0.1},
        "locked_params": ["filter_cutoff"],
        "model_id": 1,
        "model_name": "Serum",
    }


@patch.object(AiService, "_post_to_ai")
def test_refine_without_user_id_skips_history(mock_post, svc):
    service, _, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)

    preset = service.refine_preset_from_prompt("brighter", {}, [], 1, "Serum")

    assert preset.history_entry is None
    history.add.assert_not_called()


@patch.object(AiService, "_post_to_ai")
def test_refine_survives_history_failure(mock_post, svc):
    service, db, history = svc
    mock_post.return_value = copy.deepcopy(PRESET)
    history.add.side_effect = RuntimeError("db down")

    preset = service.refine_preset_from_prompt(
        "brighter", {}, [], 1, "Serum", user_id=7
    )

    assert preset.history_entry is None
    db.rollback.assert_called_once()