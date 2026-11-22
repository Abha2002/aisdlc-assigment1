"""Unit tests for the evaluator layers and for dataset integrity (human-owned oracle tests)."""
import json
from collections import Counter
from pathlib import Path

import property_eval
import pytest
import quality_eval
import schema_eval

ROOT = Path(__file__).resolve().parents[1]
NOW = schema_eval.parse_aware("2026-11-21T10:00:00+05:30")


def good(**over):
    base = {"intent": "create", "title": "call mom", "datetime": "2026-11-22T18:00:00+05:30",
            "timezone": "Asia/Kolkata", "recurrence": "none", "snooze_minutes": None,
            "target_reminder_id": None, "clarification_question": None, "refusal_reason": None}
    base.update(over)
    return base


def rules(violations):
    return {v["rule"] for v in violations}


# ------------------------------------------------------------ structural (OSC-1)
def test_valid_output_passes_schema():
    assert schema_eval.validate(good()) == []


@pytest.mark.parametrize("bad", [
    "not a dict", None, [],
    good(intent="delete_all"),
    good(extra="x"),
    good(snooze_minutes=0),
    good(snooze_minutes=True),
    good(recurrence="hourly"),
    good(datetime="2026-11-22T18:00:00"),       # no offset
    good(datetime="tomorrow evening"),
    good(timezone="Mars/Base"),
    good(title="x" * 201),
])
def test_osc1_schema_rejects(bad):
    assert rules(schema_eval.validate(bad)) == {"OSC-1"}


def test_osc1_missing_field_rejected():
    out = good()
    del out["recurrence"]
    assert schema_eval.validate(out)


# ------------------------------------------------------------------ invariants
def inv(out, ids=()):
    return rules(property_eval.check_invariants(out, NOW, ids))


def test_valid_create_has_no_violations():
    assert inv(good()) == set()


def test_inv1_create_needs_title_and_datetime():
    assert "INV-1" in inv(good(title="  "))
    assert "INV-1" in inv(good(datetime=None, timezone=None))


def test_inv2_datetime_must_be_future_and_within_horizon():
    assert "INV-2" in inv(good(datetime="2026-11-21T09:00:00+05:30"))
    assert "INV-2" in inv(good(datetime="2026-11-21T10:00:00+05:30"))
    assert "INV-2" in inv(good(datetime="2040-01-01T09:00:00+05:30"))


def test_inv3_clarify_needs_question_and_no_datetime():
    ok = good(intent="clarify", title=None, datetime=None, timezone=None, clarification_question="When?")
    assert inv(ok) == set()
    assert "INV-3" in inv({**ok, "clarification_question": ""})
    assert "INV-3" in inv({**ok, "datetime": "2026-11-22T18:00:00+05:30", "timezone": "Asia/Kolkata"})


def test_inv4_snooze_rules():
    ok = good(intent="snooze", title=None, datetime=None, timezone=None, snooze_minutes=15,
              target_reminder_id="r-1")
    assert inv(ok, ["r-1"]) == set()
    assert "INV-4" in inv(ok, ["r-2"])
    assert "INV-4" in inv({**ok, "snooze_minutes": None}, ["r-1"])


def test_inv5_reschedule_rules():
    ok = good(intent="reschedule", target_reminder_id="r-1")
    assert inv(ok, ["r-1"]) == set()
    assert "INV-5" in inv(ok, [])


def test_inv6_create_must_not_target_existing():
    assert "INV-6" in inv(good(target_reminder_id="r-1"), ["r-1"])


def test_inv7_refuse_needs_reason():
    ok = good(intent="refuse", title=None, datetime=None, timezone=None, refusal_reason="Unsupported")
    assert inv(ok) == set()
    assert "INV-7" in inv({**ok, "refusal_reason": None})


def test_inv8_stray_fields():
    assert "INV-8" in inv(good(snooze_minutes=5))
    clar = good(intent="clarify", title=None, datetime=None, timezone=None,
                clarification_question="?", recurrence="daily")
    assert "INV-8" in inv(clar)


def test_inv9_offset_must_match_zone():
    assert "INV-9" in inv(good(datetime="2026-11-22T18:00:00-05:00"))
    assert "INV-9" in inv(good(timezone=None))
    assert inv(good(datetime="2026-11-22T21:00:00-05:00", timezone="America/New_York")) == set()


def test_guardrail_forbidden_substrings_case_insensitive():
    assert property_eval.check_guardrails(good(title="send_EMAIL now"), ["send_email"])
    assert not property_eval.check_guardrails(good(), ["send_email"])


# ---------------------------------------------------------------------- quality
def test_title_f1_ignores_wording_and_stopwords():
    assert quality_eval.title_f1("call mom", "Call Mom") == 1.0
    assert quality_eval.title_f1("submit assignment", "submit the assignment") == 1.0
    assert 0 < quality_eval.title_f1("call mom", "call mom about dinner") < 1
    assert quality_eval.title_f1("call mom", "buy milk") == 0.0


def test_datetime_score_levels():
    exp = "2026-11-22T18:00:00+05:30"
    assert quality_eval.datetime_score(exp, "2026-11-22T12:30:00+00:00", 120) == 1.0   # same instant
    assert quality_eval.datetime_score(exp, "2026-11-22T09:00:00+05:30", 120) == 0.5   # same date
    assert quality_eval.datetime_score(exp, "2026-11-23T18:00:00+05:30", 120) == 0.0
    assert quality_eval.datetime_score(exp, None, 120) == 0.0


def test_score_wrong_intent_is_zero():
    exp = {"intent_any_of": ["clarify"], "clarification_keywords_any": ["when"]}
    assert quality_eval.score(exp, good())["semantic"] == 0.0


def test_score_create_components():
    exp = {"intent_any_of": ["create"], "datetime": "2026-11-22T18:00:00+05:30", "title": "call mom"}
    s = quality_eval.score(exp, good())
    assert s["semantic"] == 1.0
    assert set(s["components"]) == {"intent", "datetime", "title"}
    assert quality_eval.score(exp, good(title="buy milk"))["semantic"] < 1.0


def test_score_clarification_keywords():
    exp = {"intent_any_of": ["clarify"], "clarification_keywords_any": ["when", "time"]}
    out = good(intent="clarify", title=None, datetime=None, timezone=None, clarification_question="At what time?")
    assert quality_eval.score(exp, out)["semantic"] == 1.0
    out["clarification_question"] = "Please elaborate."
    assert quality_eval.score(exp, out)["semantic"] == 0.5


# -------------------------------------------------------------- dataset integrity
@pytest.fixture(scope="module")
def dataset():
    return json.loads((ROOT / "evals" / "dataset.json").read_text(encoding="utf-8"))["cases"]


def test_dataset_has_at_least_15_unique_cases(dataset):
    assert len(dataset) >= 15
    assert len({c["id"] for c in dataset}) == len(dataset)
    assert len({c["input"]["text"] for c in dataset}) == len(dataset)


def test_dataset_covers_required_categories(dataset):
    cats = Counter(c["category"] for c in dataset)
    for needed in ("normal", "boundary", "ambiguous", "missing_info", "malformed", "adversarial", "guardrail"):
        assert cats[needed] >= 1, needed


def test_every_case_has_ground_truth_and_valid_traceability(dataset):
    reqs = json.loads((ROOT / "evals" / "requirements.json").read_text(encoding="utf-8"))
    for c in dataset:
        assert c["expect"]["intent_any_of"], c["id"]
        assert c["requirements"] and set(c["requirements"]) <= set(reqs), c["id"]
        schema_eval.parse_aware(c["input"]["now"])
        for key in ("datetime",):
            if key in c["expect"]:
                schema_eval.parse_aware(c["expect"][key])


def test_every_requirement_is_exercised_by_some_case(dataset):
    reqs = set(json.loads((ROOT / "evals" / "requirements.json").read_text(encoding="utf-8")))
    used = {r for c in dataset for r in c["requirements"]}
    assert (reqs - {"EVAL-1"}) <= used, sorted(reqs - used)


def test_thresholds_declared():
    th = json.loads((ROOT / "evals" / "thresholds.json").read_text(encoding="utf-8"))
    for key in ("aggregate_score_min", "structural_pass_rate_min", "invariant_pass_rate_min",
                "guardrail_pass_rate_min", "case_semantic_min"):
        assert 0 < th[key] <= 1
