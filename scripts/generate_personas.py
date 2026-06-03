"""Synthetic persona generator — bulk + edge test data, and (opt-in) LLM-drafted personas.

Hybrid by design (see decisions.md D-005):
  * DETERMINISTIC mode (default, no API key): a seedable assembler from curated component
    pools. Reproducible, fast, ideal for property/load tests and graceful-degradation runs.
    Also emits a fixed set of EDGE cases (zero-record, single-record, very long text,
    multi-risk, unicode, missing-optional-fields) — the inputs that break renderers.
  * LLM mode (``--llm``, opt-in): drafts richer, less-templated personas via the
    open-weight provider (gpt-oss-120b / Llama fallback — Invariant 4), then runs every
    one through the SAME synthetic-data gate before writing. Reinforces the governance
    story: even our fake data is made by the open-weight model on our own infra.

EVERY generated persona is marked ``synthetic: true`` with a clearly-fictional demo_note,
uses obviously-generated ids (``gen-…``), and must pass ``validate_personas`` before it is
written. Nothing here resembles, or is derived from, any real person or real record.

Run:
    python -m scripts.generate_personas --count 12 --seed 42 --out tests/fixtures/personas
    python -m scripts.generate_personas --edges --out tests/fixtures/personas
    python -m scripts.generate_personas --llm --count 3 --out app/data/personas_staged
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

# Make the generator importable as a module and also reuse the gate.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.validate_personas import has_errors, validate_persona_dict  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- Curated, obviously-fictional component pools (no real individuals) -------------------

_FIRST = [
    "Aiden", "Bea", "Caleb", "Dion", "Esme", "Femi", "Gracie", "Harun", "Iris", "Jaylen",
    "Kayla", "Liam", "Maya", "Noor", "Otis", "Priya", "Quinn", "Rhys", "Saoirse", "Tariq",
    "Uma", "Vince", "Willa", "Yusuf", "Zara",
]
_LAST = [
    "Ashby", "Brennan", "Calder", "Devlin", "Ellison", "Fenwick", "Grant", "Halloran",
    "Ingram", "Jarrett", "Keane", "Lomax", "Marsh", "Nuttall", "Okoro", "Pryor", "Quill",
    "Rivers", "Sefton", "Thorne",
]

# (barrier, summary fragment, the records that tell that story).
_ARCHETYPES = [
    {
        "barrier": "anxiety / low confidence",
        "summary": "left education early; anxiety the main barrier; engages warmly when it's low-pressure",
        "records": [
            ("College — Pastoral Support", "pastoral_note",
             "Attendance patchy on the Level 2 course; strong work when present. Says mornings and crowded rooms are hard."),
            ("NHS GP — Referral letter (copy on file)", "gp_referral",
             "Generalised anxiety, worse in social settings. Open to talking therapy; referred to IAPT, ~10 week wait."),
            ("Northgate Futures (charity) — Keyworker intake", "keyworker_note",
             "Warm and bright in person; very anxious about being 'behind'. The 'disengaged' label doesn't match who turned up. Next: low-pressure volunteering taster."),
        ],
    },
    {
        "barrier": "care-experienced; hands-on learner",
        "summary": "care-experienced; thrives in practical settings; misses office appointments but turns up for real work",
        "records": [
            ("Leaving Care Team — Personal Adviser note", "leaving_care_note",
             "Moved to semi-independent accommodation; settling unevenly. Disengages from formal review meetings and paperwork."),
            ("Riverside trades — Taster placement feedback", "employer_feedback",
             "Punctual, polite, picks things up fast. Would consider an apprenticeship with a Level 1 maths pass. One no-show with no message."),
            ("Northgate Futures — Contact log", "contact_log",
             "Missed a scheduled call; re-contacted via WhatsApp and replied within the hour, apologised, said he forgot."),
        ],
    },
    {
        "barrier": "caring responsibilities",
        "summary": "young carer; limited availability; motivated but time-poor and easily overcommitted",
        "records": [
            ("School — Education Welfare Officer", "ewo_note",
             "Frequent lateness tied to caring for a younger sibling before school. Bright; teachers describe as reliable when there."),
            ("Jobcentre Plus — Work Coach note", "work_coach_note",
             "Keen on part-time work that fits around home. Worried about losing flexibility. Marked as needing additional support."),
            ("Northgate Futures — Keyworker note", "keyworker_note",
             "Clear about wanting childcare or healthcare work. Needs hours that flex around caring; a rigid timetable will lose them."),
        ],
    },
    {
        "barrier": "housing instability",
        "summary": "recent housing disruption; engagement interrupted by moves; wants stability before training",
        "records": [
            ("Housing Options — Caseworker note", "housing_note",
             "Sofa-surfing after a family breakdown; temporary accommodation secured. Address has changed twice this term."),
            ("Northgate Futures — Keyworker intake", "keyworker_note",
             "Hard to reach during the moves; not disengaged, just displaced. Wants to sort housing before committing to a course."),
            ("Self-referral form (own words)", "self_referral",
             "Wrote: 'I want to get back into college once I know where I'm living. I'm not lazy, things have just been everywhere.'"),
        ],
    },
    {
        "barrier": "neurodiversity / SEND",
        "summary": "diagnosed ADHD; strong with structure and interest-led tasks; struggles with open-ended admin",
        "records": [
            ("College — SEND / Learning Support", "send_note",
             "EHCP in place; benefits from clear steps and short tasks. Disengages from long, unstructured sessions."),
            ("Employer — Work trial feedback", "employer_feedback",
             "Excellent on detailed, interest-led tasks; needed reminders for routine admin. Manager happy to accommodate with structure."),
            ("Northgate Futures — Keyworker note", "keyworker_note",
             "Sharp and curious when the task is concrete. Wants IT/digital work. One-page checklists work far better than emails."),
        ],
    },
    {
        "barrier": "low digital access",
        "summary": "patchy phone/data access makes contact unreliable; keen but easy to lose between appointments",
        "records": [
            ("Northgate Futures — Contact log", "contact_log",
             "Texts often don't land — phone frequently out of credit. WhatsApp on free wifi works best for reaching them."),
            ("Jobcentre Plus — Work Coach note", "work_coach_note",
             "Online job-search commitments hard to meet without reliable data. Agreed to use the centre's computers weekly."),
            ("Keyworker note", "keyworker_note",
             "Not avoidant — just hard to reach. Motivated about warehouse/logistics work. Needs a contact plan that assumes patchy signal."),
        ],
    },
]

_RISK_POOL = [
    ("Possible child criminal exploitation (CCE)",
     "Unexplained money and a new phone; travelling to an unfamiliar address to 'hold things' for an older associate — recognised indicators. Surfaced for the worker's judgement; not acted on automatically."),
    ("Low mood / possible self-harm",
     "Disclosed feeling 'numb' and mentioned old marks on their arm in passing; declined to say more. A welfare cue for the worker to follow up sensitively — surfaced, not acted on."),
    ("Possible mate-crime / financial exploitation",
     "An older 'friend' is holding their bank card and 'helping' with benefits; reports having no money days after payment. A safeguarding cue for the worker — surfaced for judgement, no automatic action."),
]


def _slug(s: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-")


def make_persona(index: int, rng: random.Random) -> dict:
    """Assemble one deterministic, schema-valid synthetic persona."""
    first = _FIRST[index % len(_FIRST)]
    last = _LAST[(index * 7 + 3) % len(_LAST)]
    name = f"{first} {last}"
    pid = f"gen-{_slug(name)}-{index:03d}"  # 'gen-' marks it as generated test data
    arch = _ARCHETYPES[index % len(_ARCHETYPES)]
    age = 16 + (index % 9)  # 16–24

    # 2–N records from the archetype, dated across recent months.
    n = 2 + (index % (len(arch["records"]) - 1) + 1) if len(arch["records"]) > 2 else len(arch["records"])
    n = min(n, len(arch["records"]))
    base_month = 1 + (index % 6)
    records = []
    for j, (source, rtype, text) in enumerate(arch["records"][:n]):
        month = min(12, base_month + j)
        records.append({
            "id": f"{pid}-r{j + 1}",
            "date": f"2026-{month:02d}-{(5 + j * 7) % 28 + 1:02d}",
            "source": source,
            "author": ["A. Marsh", "P. Nkomo", "S. Ellison (Keyworker)", "system", "T. Howells"][j % 5],
            "type": rtype,
            "text": text,
            "risk_indicator": False,
        })

    # Deterministically give ~1 in 4 a single, explained risk indicator (Invariant 7).
    if index % 4 == 0 and records:
        category, rationale = _RISK_POOL[index % len(_RISK_POOL)]
        flagged = records[-1]
        flagged["risk_indicator"] = True
        flagged["risk_category"] = category
        flagged["risk_rationale"] = rationale

    return {
        "id": pid,
        "name": name,
        "age": age,
        "synthetic": True,
        "demo_note": "Auto-generated fictional persona — synthetic test data only. Not a real person; no real records.",
        "summary_line": f"{age}, {arch['summary']}.",
        "records": records,
    }


def edge_cases() -> list[dict]:
    """A fixed set of unusual-but-VALID personas that stress the renderers and routes."""
    base = lambda pid, **kw: {  # noqa: E731
        "id": pid, "name": kw.get("name", "Edge Case"), "age": kw.get("age", 18),
        "synthetic": True,
        "demo_note": "Auto-generated EDGE-CASE fixture — synthetic test data only.",
        "summary_line": kw.get("summary", "edge-case fixture"),
        "records": kw.get("records", []),
    }
    rec = lambda i, text, **kw: {  # noqa: E731
        "id": f"edge-r{i}", "date": "2026-03-01", "source": "Test Source",
        "author": "system", "type": "test_note", "text": text, "risk_indicator": False, **kw,
    }
    return [
        base("gen-edge-zero-records", name="Zero Records", summary="persona with no history at all"),
        base("gen-edge-single-record", name="Single Record",
             records=[rec(1, "The only record on file — the brief must cope with one source.")]),
        base("gen-edge-long-text", name="Long Text",
             records=[rec(1, "Lorem context. " * 200)]),
        base("gen-edge-multi-risk", name="Multi Risk",
             records=[
                 rec(1, "First flagged concern.", risk_indicator=True,
                     risk_category=_RISK_POOL[0][0], risk_rationale=_RISK_POOL[0][1]),
                 rec(2, "Second, different concern.", risk_indicator=True,
                     risk_category=_RISK_POOL[2][0], risk_rationale=_RISK_POOL[2][1]),
             ]),
        base("gen-edge-unicode", name="Ünïcödé Náme — 日本語",
             records=[rec(1, "Record with açcented chars, emoji 🧪, and 日本語 to test rendering/escaping.")]),
        {  # missing optional fields (no demo_note carried at record level; minimal but valid)
            "id": "gen-edge-minimal", "name": "Minimal Fields", "age": 20, "synthetic": True,
            "demo_note": "Auto-generated EDGE-CASE fixture — minimal optional fields.",
            "summary_line": "minimal valid persona",
            "records": [{"id": "edge-r1", "date": "2026-02-02", "source": "S", "author": "A",
                         "type": "t", "text": "Minimal but valid record.", "risk_indicator": False}],
        },
    ]


# --- LLM mode (opt-in, open-weight only) --------------------------------------------------

def _bootstrap_key() -> None:
    """Honour decisions.md D-006: load OPENROUTER_API_KEY from env, else from a gitignored
    orkey.txt at the repo root. Must run BEFORE importing the provider (it captures the key
    at construction)."""
    if os.environ.get("OPENROUTER_API_KEY"):
        return
    for candidate in (REPO_ROOT / "orkey.txt", Path.cwd() / "orkey.txt"):
        if candidate.exists():
            os.environ["OPENROUTER_API_KEY"] = candidate.read_text(encoding="utf-8").strip()
            return


_LLM_SYSTEM = (
    "You generate ENTIRELY FICTIONAL synthetic personas for a keyworker demo that re-engages "
    "NEET young people. Never use real people. Output one JSON object only, no prose, no fences. "
    "Schema: {id (lowercase-kebab, prefix 'gen-'), name, age (16-24), synthetic:true, demo_note "
    "(state it is fictional/synthetic), summary_line, records:[{id,date(YYYY-MM-DD),source,author,"
    "type,text,risk_indicator(bool)}]}. Give 3-4 records from DIFFERENT sources (school/EWO, GP or "
    "CAMHS, Jobcentre work coach, charity keyworker, employer, self-referral in the young person's "
    "own words). Make records fragmented and slightly inconsistent so synthesis is worthwhile. "
    "At most one record may set risk_indicator:true, and if so it MUST also include risk_category "
    "and a risk_rationale explaining the cue (a flag without a reason is forbidden)."
)


def make_persona_llm(index: int) -> dict | None:
    """Draft one persona via the open-weight provider; return it only if it passes the gate."""
    from app.routers.context import parse_brief_json  # tolerant JSON extraction, reused
    from app.services.inference import InferenceError, provider

    if not provider.configured:
        print("[llm] OPENROUTER_API_KEY not set — skipping LLM mode.", file=sys.stderr)
        return None
    prompt = (
        f"Generate fictional synthetic persona #{index + 1}. Vary the barrier, age, and sources "
        "from a typical case. Remember: JSON object only."
    )
    try:
        completion = provider.complete(prompt, system=_LLM_SYSTEM, temperature=0.7, max_tokens=1300)
    except InferenceError as exc:
        print(f"[llm] inference failed: {exc}", file=sys.stderr)
        return None
    # The model may return an object or wrap it; reuse the tolerant array parser by bracket-scan.
    text = completion.text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        print("[llm] no JSON object in response — skipping.", file=sys.stderr)
        return None
    try:
        persona = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        print("[llm] unparseable JSON — skipping.", file=sys.stderr)
        return None
    persona["synthetic"] = True  # never trust the model to assert the governance flag
    persona.setdefault("demo_note", "LLM-drafted fictional persona (open-weight) — synthetic test data only.")
    issues = validate_persona_dict(persona)
    if has_errors(issues):
        print(f"[llm] generated persona failed the gate, skipping:", file=sys.stderr)
        for i in issues:
            if i.level == "error":
                print(f"       {i}", file=sys.stderr)
        return None
    return persona


# --- CLI ---------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate synthetic personas (deterministic or open-weight LLM).")
    ap.add_argument("--count", type=int, default=12, help="number of personas to generate")
    ap.add_argument("--seed", type=int, default=42, help="seed for deterministic mode")
    ap.add_argument("--out", default="tests/fixtures/personas", help="output directory")
    ap.add_argument("--edges", action="store_true", help="also write the fixed edge-case fixtures")
    ap.add_argument("--llm", action="store_true", help="use the open-weight LLM to draft personas")
    ap.add_argument("--dry-run", action="store_true", help="validate and report, write nothing")
    args = ap.parse_args(argv)

    out = Path(args.out)
    personas: list[dict] = []

    if args.llm:
        _bootstrap_key()
        for i in range(args.count):
            p = make_persona_llm(i)
            if p is not None:
                personas.append(p)
        print(f"[llm] {len(personas)}/{args.count} personas passed the gate.")
    else:
        rng = random.Random(args.seed)
        personas = [make_persona(i, rng) for i in range(args.count)]

    if args.edges:
        personas.extend(edge_cases())

    # Gate everything before writing — nothing invalid is ever emitted.
    bad = 0
    for p in personas:
        issues = validate_persona_dict(p)
        if has_errors(issues):
            bad += 1
            print(f"[gate] {p.get('id')} FAILED validation:", file=sys.stderr)
            for i in issues:
                if i.level == "error":
                    print(f"        {i}", file=sys.stderr)
    if bad:
        print(f"\n{bad} persona(s) failed the gate — refusing to write.", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[dry-run] {len(personas)} valid persona(s); nothing written.")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    for p in personas:
        (out / f"{p['id']}.json").write_text(json.dumps(p, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(personas)} persona(s) to {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
