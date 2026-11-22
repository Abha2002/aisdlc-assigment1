"""Deterministic harness runner for Part 1A.

Gates (all mandatory, run in this order, none can be skipped by flags):
  G0 integrity  - tests/, .harness/*.py, pyproject.toml unchanged since lock.py
  G1 lint       - ruff check src tests            (rules in pyproject.toml)
  G2 sast       - bandit -r src, fail on MEDIUM/HIGH
  G3 secrets    - regex scan of the repo for credentials / .env files
  G4 tests      - pytest + coverage >= 90% on src/todo

Usage:  python .harness/run_harness.py --label initial
Writes evidence/harness-results/<label>/ (never overwrites an existing label):
  summary.json, feedback.md, ruff.txt, bandit.json, secrets.txt, pytest.txt, junit.xml
Exit code: 0 = PASS, 1 = FAIL.
"""
import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import lock  # noqa: E402

COVERAGE_MIN = 90
TAIL = 4000
SECRET_PATTERNS = {
    "generic API key assignment": re.compile(
        r"""(?i)(api[_-]?key|secret|token|passwd|password)\s*[:=]\s*['"][^'"\s]{8,}['"]"""
    ),
    "Anthropic/OpenAI style key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".harness",
             "evidence", "node_modules", "speckit-prompts", ".specify"}


def sh(cmd):
    t0 = time.time()
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603
    return p.returncode, p.stdout, p.stderr, round(time.time() - t0, 2)


def tree_hash(path):
    h = hashlib.sha256()
    for f in sorted(path.rglob("*.py")):
        h.update(str(f.relative_to(path)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def gate_integrity(out):
    lock_file = HERE / "lock.json"
    if not lock_file.exists():
        msg = "lock.json missing - human must run `python .harness/lock.py` before implementation."
        return False, msg, "", 0
    expected = json.loads(lock_file.read_text(encoding="utf-8"))
    actual = lock.current()
    problems = [f"MODIFIED: {k}" for k in expected if k in actual and actual[k] != expected[k]]
    problems += [f"MISSING: {k}" for k in expected if k not in actual]
    problems += [f"ADDED (unlocked): {k}" for k in actual if k not in expected]
    text = "\n".join(problems) or "all locked files unchanged"
    (out / "integrity.txt").write_text(text + "\n", encoding="utf-8")
    return not problems, text, "", 0


def gate_lint(out):
    rc, so, se, dt = sh([sys.executable, "-m", "ruff", "check", "src", "tests", "--output-format", "concise"])
    (out / "ruff.txt").write_text(so + se, encoding="utf-8")
    return rc == 0, so, se, dt


def gate_sast(out):
    rc, so, se, dt = sh([sys.executable, "-m", "bandit", "-r", "src", "-f", "json", "-q"])
    (out / "bandit.json").write_text(so or se, encoding="utf-8")
    try:
        results = json.loads(so)["results"]
    except (ValueError, KeyError):
        return False, so, se or "bandit produced no parseable output", dt
    bad = [r for r in results if r["issue_severity"] in ("MEDIUM", "HIGH")]
    lines = [f"{r['filename']}:{r['line_number']} {r['test_id']} [{r['issue_severity']}] {r['issue_text']}"
             for r in bad]
    return not bad, "\n".join(lines) or "no MEDIUM/HIGH findings", se, dt


def gate_secrets(out):
    hits = []
    if (ROOT / ".env").exists():
        hits.append(".env file present in repository directory")
    for f in ROOT.rglob("*"):
        if not f.is_file() or SKIP_DIRS & set(f.relative_to(ROOT).parts) or f.stat().st_size > 1_000_000:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for name, pat in SECRET_PATTERNS.items():
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                hits.append(f"{f.relative_to(ROOT)}:{line} {name}")
    body = "\n".join(hits) or "no secrets found"
    (out / "secrets.txt").write_text(body + "\n", encoding="utf-8")
    return not hits, body, "", 0


def gate_tests(out):
    junit = out / "junit.xml"
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short", f"--junitxml={junit}",
           "--cov=todo", "--cov-report=term-missing", f"--cov-fail-under={COVERAGE_MIN}"]
    rc, so, se, dt = sh(cmd)
    (out / "pytest.txt").write_text(so + se, encoding="utf-8")
    return rc == 0, so, se, dt


def failed_testcases(junit):
    if not junit.exists():
        return []
    cases = []
    for tc in ET.parse(junit).getroot().iter("testcase"):
        for kind in ("failure", "error"):
            node = tc.find(kind)
            if node is not None:
                req = re.search(r"test_(fr\d+|nfr\d+)", tc.get("name", ""))
                cases.append({
                    "test": f"{tc.get('classname')}::{tc.get('name')}",
                    "requirement": req.group(1).upper() if req else "unknown",
                    "message": (node.get("message") or "")[:600],
                    "detail": (node.text or "")[-1200:],
                })
    return cases


def write_feedback(out, gates, cases):
    lines = [
        "# Harness failure evidence (feed this file to the coding agent)", "",
        "RULES FOR THE AGENT: fix the implementation in `src/` only. Do NOT edit `tests/`, "
        "`.harness/`, `pyproject.toml`, the spec or the constitution. Do NOT add lint/security "
        "suppressions (noqa, nosec) or lower any threshold. Then stop; the human re-runs the same harness.", "",
    ]
    for g in gates:
        if g["status"] == "PASS":
            continue
        lines += [f"## Gate {g['id']} {g['name']}: FAIL", f"Command output (tail):", "```", g["output"][-TAIL:], "```", ""]
    if cases:
        lines += ["## Failed tests (expected vs observed)", ""]
        for c in cases:
            lines += [f"### {c['test']}  (requirement {c['requirement']})", f"Message: {c['message']}",
                      "```", c["detail"], "```", ""]
    (out / "feedback.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default=datetime.now().strftime("run-%Y%m%d-%H%M%S"))
    args = ap.parse_args()
    out = ROOT / "evidence" / "harness-results" / args.label
    if out.exists():
        sys.exit(f"refusing to overwrite existing evidence: {out}")
    out.mkdir(parents=True)

    gates = []
    for gid, name, fn in (("G0", "integrity", gate_integrity), ("G1", "lint (ruff)", gate_lint),
                          ("G2", "sast (bandit)", gate_sast), ("G3", "secrets", gate_secrets),
                          ("G4", "tests+coverage (pytest)", gate_tests)):
        ok, so, se, dt = fn(out)
        gates.append({"id": gid, "name": name, "status": "PASS" if ok else "FAIL",
                      "seconds": dt, "output": (so + "\n" + se).strip()})
        print(f"{gid} {name:28s} {'PASS' if ok else 'FAIL'}")

    overall = "PASS" if all(g["status"] == "PASS" for g in gates) else "FAIL"
    src = ROOT / "src"
    summary = {
        "label": args.label, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "src_tree_sha256": tree_hash(src) if src.exists() else None,
        "overall": overall,
        "gates": [{k: v for k, v in g.items() if k != "output"} for g in gates],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if overall == "FAIL":
        write_feedback(out, gates, failed_testcases(out / "junit.xml"))
        print(f"feedback for the coding agent: {out / 'feedback.md'}")
    print(f"OVERALL: {overall}  ({out})")
    sys.exit(0 if overall == "PASS" else 1)


if __name__ == "__main__":
    main()
