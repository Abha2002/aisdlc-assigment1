"""HUMAN-ONLY: lock the evaluation oracle (dataset, thresholds, evaluators, tests, config).

Run once after reviewing them and BEFORE /speckit.implement. Re-run only for a legitimate,
documented specification revision. The coding agent must never run or edit this.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = Path(__file__).with_name("lock.json")


def locked_files():
    files = [ROOT / "pyproject.toml", ROOT / "requirements.txt", ROOT / "requirements-dev.txt"]
    files += sorted((ROOT / "evals").glob("*.json"))
    files += sorted((ROOT / "tests").rglob("*.py"))
    files += sorted(Path(__file__).parent.glob("*.py"))
    return [f for f in files if f.is_file()]


def current():
    return {str(f.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in locked_files()}


def verify():
    if not LOCK.exists():
        return ["lock.json missing - human must run `python .harness/lock.py` first"]
    expected, actual = json.loads(LOCK.read_text(encoding="utf-8")), current()
    problems = [f"MODIFIED: {k}" for k in expected if k in actual and actual[k] != expected[k]]
    problems += [f"MISSING: {k}" for k in expected if k not in actual]
    problems += [f"ADDED (unlocked): {k}" for k in actual if k not in expected]
    return problems


if __name__ == "__main__":
    LOCK.write_text(json.dumps(current(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"locked {len(current())} files -> {LOCK}")
