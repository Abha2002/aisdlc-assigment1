"""Layer 3 - semantic/quality scoring against ground truth. Heuristic, no LLM judge.

Per-case semantic score = mean of the applicable components, each in [0, 1]:
  intent   : 1 if output intent is in expect.intent_any_of else 0 (then score is just 0)
  datetime : 1 if within tolerance (default 120 s) of expect.datetime (compared as instants),
             0.5 if same calendar date in the expected zone, else 0; or window membership
  title    : token-set F1 vs expect.title (stop words removed) or keyword hit (title_keywords_any)
  recurrence, target, snooze_minutes : exact match
  clarification : 1 if the question contains any of expect.clarification_keywords_any
"""
import re
from datetime import timedelta

from schema_eval import parse_aware

STOP = {"to", "the", "my", "a", "an", "me", "remind", "that", "about", "for", "of", "and", "i", "need"}


def tokens(text):
    return {t for t in re.findall(r"\w+", (text or "").lower()) if t not in STOP}


def title_f1(expected, got):
    exp, out = tokens(expected), tokens(got)
    if not exp or not out:
        return 0.0
    hit = len(exp & out)
    if hit == 0:
        return 0.0
    p, r = hit / len(out), hit / len(exp)
    return 2 * p * r / (p + r)


def datetime_score(expected_iso, got_iso, tolerance_s):
    if got_iso is None:
        return 0.0
    exp, got = parse_aware(expected_iso), parse_aware(got_iso)
    if abs(exp - got) <= timedelta(seconds=tolerance_s):
        return 1.0
    return 0.5 if got.astimezone(exp.tzinfo).date() == exp.date() else 0.0


def window_score(window, got_iso):
    if got_iso is None:
        return 0.0
    return 1.0 if parse_aware(window["start"]) <= parse_aware(got_iso) <= parse_aware(window["end"]) else 0.0


def _create_components(exp, out):
    comps = {}
    if "datetime" in exp:
        comps["datetime"] = datetime_score(exp["datetime"], out["datetime"], exp.get("datetime_tolerance_s", 120))
    if "datetime_window" in exp:
        comps["datetime"] = window_score(exp["datetime_window"], out["datetime"])
    if "title" in exp:
        comps["title"] = title_f1(exp["title"], out["title"])
    if "title_keywords_any" in exp:
        low = (out["title"] or "").lower()
        comps["title"] = 1.0 if any(k.lower() in low for k in exp["title_keywords_any"]) else 0.0
    if "recurrence" in exp:
        comps["recurrence"] = 1.0 if out["recurrence"] == exp["recurrence"] else 0.0
    return comps


def _other_components(exp, out):
    comps = {}
    intent = out["intent"]
    if intent == "reschedule":
        if "datetime" in exp:
            comps["datetime"] = datetime_score(exp["datetime"], out["datetime"], exp.get("datetime_tolerance_s", 120))
        if "target_reminder_id" in exp:
            comps["target"] = 1.0 if out["target_reminder_id"] == exp["target_reminder_id"] else 0.0
    elif intent == "snooze":
        if "snooze_minutes" in exp:
            comps["snooze_minutes"] = 1.0 if out["snooze_minutes"] == exp["snooze_minutes"] else 0.0
        if "target_reminder_id" in exp:
            comps["target"] = 1.0 if out["target_reminder_id"] == exp["target_reminder_id"] else 0.0
    elif intent == "clarify" and "clarification_keywords_any" in exp:
        q = (out["clarification_question"] or "").lower()
        comps["clarification"] = 1.0 if any(k.lower() in q for k in exp["clarification_keywords_any"]) else 0.0
    return comps


def score(expect, out):
    """Return {'components': {...}, 'semantic': float}. `out` must be structurally valid."""
    intent_ok = out["intent"] in expect["intent_any_of"]
    comps = {"intent": 1.0 if intent_ok else 0.0}
    if intent_ok:
        extra = _create_components(expect, out) if out["intent"] == "create" else _other_components(expect, out)
        comps.update(extra)
    return {"components": comps, "semantic": sum(comps.values()) / len(comps)}
