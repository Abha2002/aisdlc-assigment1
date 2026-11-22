"""Deterministic application contract tests that need no network and no API key."""
import pytest
import schema_eval

NOW = "2026-11-21T10:00:00+05:30"


@pytest.fixture(autouse=True)
def _no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_empty_input_is_clarified_without_calling_the_model(text):
    """BP-3/INV-3: blank input must be handled locally (no model call, so no key needed)."""
    from reminder.agent import handle

    out = handle(text, NOW, "Asia/Kolkata", [])
    assert schema_eval.validate(out) == []
    assert out["intent"] == "clarify"
    assert out["clarification_question"].strip()
    assert out["datetime"] is None


def test_missing_api_key_is_a_model_service_error_not_an_app_crash():
    """Service failures must be distinguishable from application failures."""
    from reminder.agent import handle
    from reminder.errors import ModelServiceError

    with pytest.raises(ModelServiceError):
        handle("Remind me to call mom tomorrow at 6pm", NOW, "Asia/Kolkata", [])
