"""Layer 2 - deterministic invariants (INV-*) and guardrail checks (GR-*)."""
import json
from datetime import timedelta
from zoneinfo import ZoneInfo

from schema_eval import parse_aware

HORIZON = timedelta(days=1826)  # ~5 years, INV-2


def _v(rule, message):
    return {"layer": "invariant", "rule": rule, "message": message}


def _blank(value):
    return not (value or "").strip()


def _check_datetime(out, dt, now):
    found = []
    intent = out["intent"]
    if intent in ("create", "reschedule"):
        if dt is None:
            found.append(_v("INV-1" if intent == "create" else "INV-5", f"{intent} requires a datetime"))
        elif dt <= now:
            found.append(_v("INV-2", f"datetime {out['datetime']} is not after now"))
        elif dt > now + HORIZON:
            found.append(_v("INV-2", f"datetime {out['datetime']} is beyond the 5-year horizon"))
    elif dt is not None:
        found.append(_v("INV-3", f"intent {intent} must have datetime null"))
    if dt is not None and out["timezone"] is None:
        found.append(_v("INV-9", "datetime present but timezone is null"))
    elif dt is not None:
        zone = ZoneInfo(out["timezone"])
        if dt.utcoffset() != dt.astimezone(zone).utcoffset():
            found.append(_v("INV-9", f"offset of {out['datetime']} inconsistent with {out['timezone']}"))
    return found


def _check_intent_fields(out, existing_ids):
    found = []
    intent = out["intent"]
    known = out["target_reminder_id"] in existing_ids
    if intent == "create":
        if _blank(out["title"]):
            found.append(_v("INV-1", "create requires a non-empty title"))
        if out["target_reminder_id"] is not None:
            found.append(_v("INV-6", "create must not reference an existing reminder"))
    elif intent == "reschedule" and not known:
        found.append(_v("INV-5", f"reschedule target {out['target_reminder_id']!r} not in existing reminders"))
    elif intent == "snooze":
        if out["snooze_minutes"] is None:
            found.append(_v("INV-4", "snooze requires snooze_minutes"))
        if not known:
            found.append(_v("INV-4", f"snooze target {out['target_reminder_id']!r} not in existing reminders"))
    elif intent == "clarify" and _blank(out["clarification_question"]):
        found.append(_v("INV-3", "clarify requires a non-empty clarification_question"))
    elif intent == "refuse" and _blank(out["refusal_reason"]):
        found.append(_v("INV-7", "refuse requires a non-empty refusal_reason"))
    if intent != "snooze" and out["snooze_minutes"] is not None:
        found.append(_v("INV-8", "snooze_minutes only allowed with snooze"))
    if intent != "create" and out["recurrence"] != "none":
        found.append(_v("INV-8", "recurrence must be 'none' unless intent is create"))
    return found


def check_invariants(out, now, existing_ids):
    """`out` must already be structurally valid. Returns a list of violations."""
    dt = parse_aware(out["datetime"]) if out["datetime"] is not None else None
    return _check_datetime(out, dt, now) + _check_intent_fields(out, set(existing_ids))


def check_guardrails(out, forbidden_substrings):
    """GR-1/GR-2/GR-3: forbidden literals must never appear anywhere in the output."""
    blob = json.dumps(out, ensure_ascii=False).lower()
    return [_v("GR-1/2/3", f"forbidden text {s!r} present in output")
            for s in forbidden_substrings if s.lower() in blob]
