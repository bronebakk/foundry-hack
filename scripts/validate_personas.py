"""The synthetic-data gate — validate persona JSON against the project's data contract.

This is both a quality tool and a GOVERNANCE asset (Invariant 3): every persona used in
the demo or in tests is checked to be *visibly synthetic*, *internally consistent*, and
*traceable*. A risk flag with no rationale fails the gate (Invariant 7 — no unexplained
flag); a record without ``synthetic: true`` on its persona fails the gate (Invariant 3).

Run:
    python -m scripts.validate_personas app/data/personas app/data/personas_staged
    python -m scripts.validate_personas tests/fixtures/personas
Exits non-zero if any ERROR is found (warnings don't fail the gate).
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

# Anchor/URL safety: persona ids land in URL paths and record ids become HTML id="..."
# anchors that the CTX brief links to (href="#<id>"). Anything outside this set could
# break the source-linking that VAL-CTX-002 depends on.
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_AGE_MIN, _AGE_MAX = 13, 30  # NEET re-engagement cohort; outside this is suspicious data


@dataclass(frozen=True)
class Issue:
    level: str  # "error" | "warning"
    persona_id: str
    where: str
    message: str

    def __str__(self) -> str:
        tag = "ERROR" if self.level == "error" else "warn "
        return f"[{tag}] {self.persona_id} · {self.where}: {self.message}"


def _is_iso_date(s: str) -> bool:
    try:
        date.fromisoformat(s)
        return True
    except (ValueError, TypeError):
        return False


def validate_persona_dict(d: dict) -> list[Issue]:
    """Validate one persona mapping. Returns all issues found (errors + warnings)."""
    pid = str(d.get("id", "<missing-id>"))
    issues: list[Issue] = []

    def err(where: str, msg: str) -> None:
        issues.append(Issue("error", pid, where, msg))

    def warn(where: str, msg: str) -> None:
        issues.append(Issue("warning", pid, where, msg))

    # --- Identity ---
    if not d.get("id") or not _ID_RE.match(str(d.get("id", ""))):
        err("id", "missing or not anchor-safe (lowercase alnum / -/_ , no spaces)")
    if not str(d.get("name", "")).strip():
        err("name", "missing")
    age = d.get("age")
    if not isinstance(age, int) or isinstance(age, bool):
        err("age", "missing or not an integer")
    elif not (_AGE_MIN <= age <= _AGE_MAX):
        warn("age", f"{age} is outside the expected {_AGE_MIN}–{_AGE_MAX} cohort")

    # --- Invariant 3: visibly synthetic. This is a hard gate, not a warning. ---
    if d.get("synthetic") is not True:
        err("synthetic", "must be exactly true — no real-data persona may enter the system")
    if not str(d.get("demo_note", "")).strip():
        warn("demo_note", "no demo_note — every persona should carry a 'fictional / synthetic' note")
    if not str(d.get("summary_line", "")).strip():
        warn("summary_line", "empty — the caseload list and brief header read this")

    # --- Records ---
    records = d.get("records")
    if not isinstance(records, list):
        err("records", "missing or not a list")
        return issues
    if not records:
        warn("records", "no records — a persona with no history can't be synthesised (ok for edge tests)")

    seen_ids: set[str] = set()
    for i, r in enumerate(records):
        where = f"records[{i}]"
        if not isinstance(r, dict):
            err(where, "not an object")
            continue
        rid = str(r.get("id", ""))
        if not rid or not _ID_RE.match(rid):
            err(f"{where}.id", f"'{rid}' missing or not anchor-safe (it becomes an HTML #anchor)")
        elif rid in seen_ids:
            err(f"{where}.id", f"duplicate record id '{rid}' — anchors and citations must be unique")
        else:
            seen_ids.add(rid)
        if not _is_iso_date(str(r.get("date", ""))):
            err(f"{where}.date", f"'{r.get('date')}' is not an ISO date (YYYY-MM-DD)")
        for field in ("source", "author", "type"):
            if not str(r.get(field, "")).strip():
                warn(f"{where}.{field}", "empty — provenance is weaker without it")
        if not str(r.get("text", "")).strip():
            err(f"{where}.text", "empty — a record with no text carries no information")

        # --- Invariant 7: a risk flag must be explainable, and only risk records carry rationale. ---
        if r.get("risk_indicator") is True:
            if not str(r.get("risk_category", "")).strip():
                err(f"{where}.risk_category", "risk_indicator is true but no risk_category given")
            if not str(r.get("risk_rationale", "")).strip():
                err(
                    f"{where}.risk_rationale",
                    "risk_indicator is true but no rationale — every flag must trace to a reason (Invariant 7)",
                )
        else:
            for field in ("risk_category", "risk_rationale"):
                if r.get(field):
                    warn(f"{where}.{field}", "set on a non-risk record — likely a mistake")

    return issues


def validate_file(path: Path) -> list[Issue]:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [Issue("error", path.stem, "file", f"could not parse JSON: {exc}")]
    if not isinstance(d, dict):
        return [Issue("error", path.stem, "file", "top-level JSON is not an object")]
    return validate_persona_dict(d)


def validate_dir(path: Path) -> dict[str, list[Issue]]:
    return {p.name: validate_file(p) for p in sorted(path.glob("*.json"))}


def has_errors(issues: list[Issue]) -> bool:
    return any(i.level == "error" for i in issues)


def main(argv: list[str]) -> int:
    targets = argv or ["app/data/personas"]
    total_errors = 0
    total_files = 0
    for target in targets:
        p = Path(target)
        files = {p.name: validate_file(p)} if p.is_file() else validate_dir(p)
        if not files:
            print(f"(no persona JSON found in {target})")
            continue
        for name, issues in files.items():
            total_files += 1
            errs = [i for i in issues if i.level == "error"]
            warns = [i for i in issues if i.level == "warning"]
            total_errors += len(errs)
            status = "FAIL" if errs else ("warn" if warns else "PASS")
            print(f"{status}  {target}/{name}")
            for issue in errs + warns:
                print(f"      {issue}")
    print(f"\n{total_files} persona(s) checked · {total_errors} error(s).")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
