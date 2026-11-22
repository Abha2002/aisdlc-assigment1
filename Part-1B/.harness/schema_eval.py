"""Layer 1 - structural validation (OSC-1). Independent of the application code."""
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator

INTENTS = ["create", "reschedule", "snooze", "clarify", "refuse"]
FIELDS = ["intent", "title", "datetime", "timezone", "recurrence", "snooze_minutes",
          "target_reminder_id", "clarification_question", "refusal_reason"]

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": FIELDS,
    "properties": {
        "intent": {"enum": INTENTS},
        "title": {"type": ["string", "null"], "maxLength": 200},
        "datetime": {"type": ["string", "null"]},
        "timezone": {"type": ["string", "null"]},
        "recurrence": {"enum": ["none", "daily", "weekly", "monthly"]},
        "snooze_minutes": {"type": ["integer", "null"], "minimum": 1, "maximum": 1440},
        "target_reminder_id": {"type": ["string", "null"]},
        "clarification_question": {"type": ["string", "null"], "maxLength": 300},
        "refusal_reason": {"type": ["string", "null"], "maxLength": 300},
    },
}
_VALIDATOR = Draft202012Validator(SCHEMA)


def parse_aware(value):
    """Parse ISO-8601 with an explicit UTC offset; raise ValueError otherwise."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("datetime has no UTC offset")
    return dt


def _violation(rule, message):
    return {"layer": "structural", "rule": rule, "message": message}


def validate(output):
    """Return a list of structural violations (empty list == valid)."""
    if not isinstance(output, dict):
        return [_violation("OSC-1", f"output must be a JSON object, got {type(output).__name__}")]
    found = []
    for err in sorted(_VALIDATOR.iter_errors(output), key=lambda e: list(e.path)):
        where = ".".join(str(p) for p in err.path) or "(root)"
        found.append(_violation("OSC-1", f"{where}: {err.message}"))
    if found:
        return found
    if output["datetime"] is not None:
        try:
            parse_aware(output["datetime"])
        except ValueError as exc:
            found.append(_violation("OSC-1", f"datetime must be ISO-8601 with offset: {exc}"))
    if output["timezone"] is not None:
        try:
            ZoneInfo(output["timezone"])
        except (ZoneInfoNotFoundError, ValueError):
            found.append(_violation("OSC-1", f"timezone {output['timezone']!r} is not an IANA zone"))
    return found
