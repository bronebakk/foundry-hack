"""CTX surface — pre-meeting context synthesis. OWNED BY MISSION M3.

A keyworker opens a synthetic young person before a meeting and gets a concise,
glanceable synthesised brief of their history — where **every claim traces back to the
specific source record it came from** (VAL-CTX-001, VAL-CTX-002 / Invariant 7).

Design notes:
  * The brief is generated on load from ``persona.records`` via the frozen open-weight
    ``provider`` (Invariant 4). It is a *proposal* — pure read context, nothing is
    committed or sent (Invariant 1). Viewing a brief is not a disposition, so this surface
    never writes to the decision log (see m3 brief "Don'ts").
  * Explainability is enforced in code, not hoped for: the model is asked for structured
    output ``[{statement, source_record_ids}]``; we then resolve every cited id against the
    real records and **drop any statement we cannot attribute** to an existing record. A
    free-text blob with no provenance is never shown.
  * Degrades gracefully: with no API key (or on an inference error) the page still renders
    the raw source records plus a clear notice — never a 500 — so the surface is demoable
    offline.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.models import Persona, Record
from app.services import data
from app.services.inference import InferenceError, provider
from app.templating import render

router = APIRouter(prefix="/context", tags=["context"])

# Keep latency demo-reasonable: a brief is a handful of bullets, not an essay.
_BRIEF_MAX_TOKENS = 700
_BRIEF_TEMPERATURE = 0.2

_SYSTEM_PROMPT = (
    "You are a careful drafting assistant for a frontline keyworker who re-engages young "
    "people. You synthesise a young person's case records into a short pre-meeting brief. "
    "You are PROPOSING context for a human to check — you never decide anything. "
    "Hard rules: (1) State ONLY what the supplied records support; never invent facts, "
    "names, dates, diagnoses, or outcomes. (2) Attach to EVERY statement the id(s) of the "
    "record(s) it is based on. If you cannot tie a statement to a specific record, do not "
    "write it. (3) Be concise and glanceable — a busy worker reads this in 60 seconds. "
    "(4) Do not deliver any refusal or denial about the young person; surface context only."
)


@dataclass(frozen=True)
class BriefStatement:
    """One synthesised line plus the real records it is attributed to. ``sources`` is
    guaranteed non-empty — an unattributable statement is never constructed."""

    text: str
    sources: tuple[Record, ...]


@dataclass(frozen=True)
class BriefResult:
    """Outcome of a synthesis attempt. ``status`` drives the template:
    ``ok`` (statements present), ``not_configured`` (no API key),
    ``error`` (inference/parse failure), ``empty`` (model returned nothing attributable).
    In every non-ok state the raw records are still rendered."""

    status: str
    statements: tuple[BriefStatement, ...] = ()
    model: str | None = None
    message: str | None = None


# --- Pure, testable synthesis helpers (no network) ---

def build_brief_prompt(persona: Persona) -> str:
    """Render the persona's records into a prompt that asks for attributed JSON output."""
    lines = [
        f"Young person: {persona.name}, age {persona.age} (SYNTHETIC demo persona).",
        f"Summary: {persona.summary_line}",
        "",
        "SOURCE RECORDS (cite these ids):",
    ]
    for r in persona.records:
        lines.append(
            f'- id="{r.id}" | {r.date} | {r.source} | {r.author} | type={r.type}\n'
            f"  {r.text}"
        )
    lines += [
        "",
        "Write a concise pre-meeting brief covering, where the records support it: who they "
        "are and where they're at now; barriers; what has worked or what they've asked for; "
        "and a suggested focus for the meeting.",
        "",
        "Return ONLY a JSON array, no prose, no markdown fences. Each element is "
        '{"statement": "<one short sentence>", "source_record_ids": ["<record id>", ...]}. '
        "Every statement MUST cite at least one real record id from the list above. "
        "Omit anything you cannot attribute.",
    ]
    return "\n".join(lines)


def parse_brief_json(text: str) -> list[dict]:
    """Tolerantly extract the JSON array of brief items from a model response. Handles
    ```json fences and leading/trailing prose by slicing to the outermost brackets.
    Returns [] if nothing parseable is found (caller treats that as 'empty')."""
    if not text:
        return []
    s = text.strip()
    if s.startswith("```"):
        # strip a ```json ... ``` fence
        s = s.split("```", 2)[1] if s.count("```") >= 2 else s.strip("`")
        if s.lstrip().lower().startswith("json"):
            s = s.lstrip()[4:]
    start, end = s.find("["), s.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []
    try:
        parsed = json.loads(s[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return []
    return [item for item in parsed if isinstance(item, dict)] if isinstance(parsed, list) else []


def attributable_statements(persona: Persona, items: list[dict]) -> list[BriefStatement]:
    """The explainability guard (VAL-CTX-002): keep only statements that (a) have text and
    (b) cite at least one id that resolves to a real record on this persona. Dangling or
    unattributable ids are dropped; a statement with no surviving source is dropped entirely.
    """
    out: list[BriefStatement] = []
    for item in items:
        text = str(item.get("statement", "")).strip()
        if not text:
            continue
        raw_ids = item.get("source_record_ids") or item.get("source_record_id") or []
        if isinstance(raw_ids, str):
            raw_ids = [raw_ids]
        seen: set[str] = set()
        sources: list[Record] = []
        for rid in raw_ids:
            rid = str(rid).strip()
            if rid in seen:
                continue
            rec = persona.get_record(rid)
            if rec is not None:
                seen.add(rid)
                sources.append(rec)
        if sources:  # unattributable statements never make it to the worker
            out.append(BriefStatement(text=text, sources=tuple(sources)))
    return out


def generate_brief(persona: Persona) -> BriefResult:
    """Synthesise an attributed brief for a persona. Pure-ish orchestration: never raises —
    inference failures and unconfigured keys become a degraded ``BriefResult``."""
    if not provider.configured:
        return BriefResult(
            status="not_configured",
            message="Inference not configured — set OPENROUTER_API_KEY to generate the brief.",
        )
    try:
        completion = provider.complete(
            build_brief_prompt(persona),
            system=_SYSTEM_PROMPT,
            temperature=_BRIEF_TEMPERATURE,
            max_tokens=_BRIEF_MAX_TOKENS,
        )
    except InferenceError as exc:
        return BriefResult(status="error", message=f"Inference unavailable: {exc}")

    statements = attributable_statements(persona, parse_brief_json(completion.text))
    if not statements:
        return BriefResult(
            status="empty",
            model=completion.model,
            message="The model returned no statement that could be traced to a source record, "
            "so nothing is shown. The raw records are below.",
        )
    return BriefResult(status="ok", statements=tuple(statements), model=completion.model)


# --- Routes ---

@router.get("/", response_class=HTMLResponse)
def context_home(request: Request):
    return render(request, "context/index.html", personas=data.list_personas())


@router.get("/{persona_id}", response_class=HTMLResponse)
def context_persona(request: Request, persona_id: str):
    persona = data.get_persona(persona_id)
    if persona is None:
        return render(request, "context/not_found.html", persona_id=persona_id)
    brief = generate_brief(persona)
    return render(request, "context/persona.html", persona=persona, brief=brief)
