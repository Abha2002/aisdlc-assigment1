"""Single non-deterministic evaluation harness (Part 1B).

Pipeline per case:  dataset -> reminder.agent.handle() -> schema -> invariants/guardrails -> semantic score
Then aggregate against evals/thresholds.json  ->  PASS / FAIL / INCONCLUSIVE.

Usage:   python .harness/run_eval.py --label initial [--runs 3] [--final]
Writes:  evidence/eval-runs/<label>/{eval-results.json, feedback.md}   (never overwrites a label)
         --final also writes evidence/eval-results.json
Exit:    0 PASS, 1 FAIL, 3 INCONCLUSIVE (model/service errors), 4 integrity failure, 5 app not importable
Model/service failures (reminder.errors.ModelServiceError) are reported separately and are NOT
counted as application failures; they make the run INCONCLUSIVE.
"""
import argparse
import hashlib
import json
import os
import platform
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE), str(ROOT / "src")]

import lock  # noqa: E402
import property_eval  # noqa: E402
import quality_eval  # noqa: E402
import schema_eval  # noqa: E402


def load_app():
    try:
        from reminder import agent
        from reminder.errors import ModelServiceError
    except Exception as exc:  # noqa: BLE001
        print(f"cannot import reminder.agent / reminder.errors: {exc!r}")
        sys.exit(5)
    return agent, ModelServiceError


def evaluate_sample(case, agent, service_error):
    inp, exp = case["input"], case["expect"]
    now = schema_eval.parse_aware(inp["now"])
    rec = {"status": "ok", "output": None, "structural": [], "invariants": [], "guardrails": [],
           "semantic": None, "sample_score": 0.0}
    try:
        out = agent.handle(inp["text"], inp["now"], inp["timezone"], inp["existing_reminders"])
    except service_error as exc:
        rec.update(status="service_error", error=f"{type(exc).__name__}: {exc}")
        return rec
    except Exception:  # noqa: BLE001
        rec.update(status="app_error", error=traceback.format_exc(limit=3))
        rec["structural"] = [{"layer": "structural", "rule": "OSC-1", "message": "handle() raised an exception"}]
        return rec
    rec["output"] = out
    rec["structural"] = schema_eval.validate(out)
    if rec["structural"]:
        return rec
    ids = [r["id"] for r in inp["existing_reminders"]]
    rec["invariants"] = property_eval.check_invariants(out, now, ids)
    rec["guardrails"] = property_eval.check_guardrails(out, case.get("forbidden_substrings", []))
    rec["semantic"] = quality_eval.score(exp, out)
    if not rec["invariants"] and not rec["guardrails"]:
        rec["sample_score"] = rec["semantic"]["semantic"]
    return rec


def run(dataset, runs, agent, service_error):
    results = []
    for case in dataset["cases"]:
        samples = [evaluate_sample(case, agent, service_error) for _ in range(runs)]
        scored = [s for s in samples if s["status"] != "service_error"]
        intents = [s["output"]["intent"] for s in scored if isinstance(s["output"], dict) and "intent" in s["output"]]
        results.append({
            "id": case["id"], "category": case["category"], "requirements": case["requirements"],
            "input": case["input"], "expect": case["expect"],
            "forbidden_substrings": case.get("forbidden_substrings", []),
            "samples": samples,
            "case_score": sum(s["sample_score"] for s in scored) / len(scored) if scored else None,
            "intent_consistency": (max(intents.count(i) for i in set(intents)) / len(intents)) if intents else None,
        })
    return results


def rate(flags):
    return sum(flags) / len(flags) if flags else 1.0


def aggregate(results, th):
    samples = [(r, s) for r in results for s in r["samples"] if s["status"] != "service_error"]
    n_service = sum(1 for r in results for s in r["samples"] if s["status"] == "service_error")
    struct = [not s["structural"] for _, s in samples]
    inv = [not s["structural"] and not s["invariants"] for _, s in samples]
    guard_cases = [(r, s) for r, s in samples if r["category"] in ("adversarial", "guardrail")]
    guard = [not s["structural"] and not s["invariants"] and not s["guardrails"]
             and s["semantic"]["components"]["intent"] == 1.0 for _, s in guard_cases]
    metrics = {
        "samples_scored": len(samples), "samples_service_error": n_service,
        "structural_pass_rate": rate(struct), "invariant_pass_rate": rate(inv),
        "guardrail_pass_rate": rate(guard),
        "mean_semantic_score": rate([s["semantic"]["semantic"] for _, s in samples if s["semantic"]]),
        "aggregate_score": rate([s["sample_score"] for _, s in samples]),
    }
    checks = {
        "aggregate_score": metrics["aggregate_score"] >= th["aggregate_score_min"],
        "structural_pass_rate": metrics["structural_pass_rate"] >= th["structural_pass_rate_min"],
        "invariant_pass_rate": metrics["invariant_pass_rate"] >= th["invariant_pass_rate_min"],
        "guardrail_pass_rate": metrics["guardrail_pass_rate"] >= th["guardrail_pass_rate_min"],
    }
    if n_service:
        decision = "INCONCLUSIVE"
    else:
        decision = "PASS" if all(checks.values()) else "FAIL"
    return metrics, checks, decision


def failing_samples(results, th):
    bad = []
    for r in results:
        for i, s in enumerate(r["samples"]):
            weak = s["semantic"] is not None and s["semantic"]["semantic"] < th["case_semantic_min"]
            if s["status"] == "app_error" or s["structural"] or s["invariants"] or s["guardrails"] or weak:
                bad.append((r, i, s))
    return bad


def write_feedback(path, results, th, decision):
    lines = ["# Evaluation failure evidence (feed this file to the coding agent)", "",
             "RULES FOR THE AGENT: you may change `src/` and `prompts/` (application code, prompt construction, "
             "parsers, validators, guardrails). You must NOT edit `evals/`, `.harness/`, `tests/`, the specification "
             "or thresholds, remove cases, or disable a guardrail. Fix root causes; the human re-runs the same harness.",
             "", f"Decision: {decision}", ""]
    for r, i, s in failing_samples(results, th):
        lines += [f"## Case {r['id']} ({r['category']}) sample {i + 1}", f"Requirements: {', '.join(r['requirements'])}",
                  f"Input: {json.dumps(r['input'], ensure_ascii=False)}",
                  f"Expected: {json.dumps(r['expect'], ensure_ascii=False)}",
                  f"Generated output: {json.dumps(s['output'], ensure_ascii=False)}"]
        for key in ("structural", "invariants", "guardrails"):
            for v in s[key]:
                lines.append(f"- FAILED {v['rule']} ({v['layer']}): {v['message']}")
        if s["semantic"]:
            lines.append(f"- semantic components: {json.dumps(s['semantic']['components'])} "
                         f"(mean {s['semantic']['semantic']:.2f}, minimum {th['case_semantic_min']})")
        if s["status"] == "app_error":
            lines.append(f"- application error:\n```\n{s.get('error')}\n```")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default=datetime.now().strftime("run-%Y%m%d-%H%M%S"))
    ap.add_argument("--runs", type=int, default=1, help="samples per case (non-determinism)")
    ap.add_argument("--final", action="store_true", help="also write evidence/eval-results.json")
    args = ap.parse_args()

    problems = lock.verify()
    if problems:
        print("INTEGRITY FAIL - oracle changed since lock:\n  " + "\n  ".join(problems))
        sys.exit(4)
    out_dir = ROOT / "evidence" / "eval-runs" / args.label
    if out_dir.exists():
        sys.exit(f"refusing to overwrite existing evidence: {out_dir}")

    agent, service_error = load_app()
    ds_path, th_path = ROOT / "evals" / "dataset.json", ROOT / "evals" / "thresholds.json"
    dataset, th = json.loads(ds_path.read_text("utf-8")), json.loads(th_path.read_text("utf-8"))

    results = run(dataset, args.runs, agent, service_error)
    metrics, checks, decision = aggregate(results, th)
    report = {
        "label": args.label, "timestamp_utc": datetime.now(UTC).isoformat(), "decision": decision,
        "config": {"model": os.environ.get("REMINDER_MODEL") or getattr(agent, "MODEL_NAME", "(not reported)"),
                   "temperature": os.environ.get("REMINDER_TEMPERATURE", getattr(agent, "TEMPERATURE", "(not reported)")),
                   "runs_per_case": args.runs, "python": platform.python_version(),
                   "dataset_sha256": hashlib.sha256(ds_path.read_bytes()).hexdigest()},
        "thresholds": th, "metrics": metrics, "threshold_checks": checks,
        "by_category": {c: rate([r["case_score"] or 0 for r in results if r["category"] == c])
                        for c in sorted({r["category"] for r in results})},
        "cases": results,
    }
    out_dir.mkdir(parents=True)
    (out_dir / "eval-results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.final:
        (ROOT / "evidence" / "eval-results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if failing_samples(results, th):
        write_feedback(out_dir / "feedback.md", results, th, decision)

    for k, v in metrics.items():
        print(f"{k:24s} {v:.3f}" if isinstance(v, float) else f"{k:24s} {v}")
    print({k: ("ok" if v else "BELOW THRESHOLD") for k, v in checks.items()})
    print(f"DECISION: {decision}  ({out_dir})")
    sys.exit({"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 3}[decision])


if __name__ == "__main__":
    main()
