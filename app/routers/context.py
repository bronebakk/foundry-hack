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

# Headroom so the JSON array isn't truncated mid-object. parse_brief_json salvages a
# truncated tail too, but we'd rather not lose the last bullet. The prompt caps the bullet
# count so the brief stays glanceable (a transcription both bloats tokens and fails VAL-CTX-001).
_BRIEF_MAX_TOKENS = 1200
_BRIEF_TEMPERATURE = 0.2
# Open-weight sampling occasionally returns an unparseable/degenerate response; one cheap
# retry makes the demo path reliable without masking a genuine outage.
_BRIEF_ATTEMPTS = 2

_SYSTEM_PROMPT = (
    "You are a careful drafting assistant for a frontline keyworker who re-engages young "
    "people. You SYNTHESISE a young person's case records into a short pre-meeting brief. "
    "You are PROPOSING context for a human to check — you never decide anything. "
    "Hard rules: (1) State ONLY what the supplied records support; never invent facts, "
    "names, dates, diagnoses, or outcomes. (2) Attach to EVERY statement the id(s) of the "
    "record(s) it is based on. If you cannot tie a statement to a specific record, do not "
    "write it. (3) SYNTHESISE — group related facts into a few crisp lines; do NOT restate "
    "the records sentence by sentence. Aim for 5–7 glanceable bullets a busy worker reads in "
    "60 seconds. (4) Do not deliver any refusal or denial about the young person; surface "
    "context only."
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
        "Write a concise, SYNTHESISED pre-meeting brief (5–7 bullets max) covering, where the "
        "records support it: who they are and where they're at now; barriers; what has worked "
        "or what they've asked for; and a suggested focus for the meeting. Group related facts "
        "— do not echo each record sentence by sentence.",
        "",
        "Return ONLY a JSON array, no prose, no markdown fences. Each element is "
        '{"statement": "<one short synthesised sentence>", "source_record_ids": ["<record id>", ...]}. '
        "Every statement MUST cite at least one real record id from the list above. "
        "Omit anything you cannot attribute.",
    ]
    return "\n".join(lines)


def parse_brief_json(text: str) -> list[dict]:
    """Tolerantly extract the JSON array of brief items from a model response. Handles
    ```json fences and leading/trailing prose, and — crucially — *truncated* output: an
    open-weight model that hits the token cap mid-array would otherwise yield nothing, so we
    salvage every complete ``{...}`` object and drop only the cut-off tail. Returns [] if
    nothing parseable is found (caller treats that as 'empty')."""
    if not text:
        return []
    s = text.strip()
    if s.startswith("```"):
        # strip a ```json ... ``` fence
        s = s.split("```", 2)[1] if s.count("```") >= 2 else s.strip("`")
        if s.lstrip().lower().startswith("json"):
            s = s.lstrip()[4:]
    start = s.find("[")
    if start == -1:
        return []
    region = s[start:]

    # Fast path: a clean, complete array.
    end = region.rfind("]")
    if end != -1:
        try:
            parsed = json.loads(region[: end + 1])
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, dict)]
        except (json.JSONDecodeError, ValueError):
            pass

    # Salvage path: scan for balanced top-level objects (handles a truncated final element).
    objs: list[dict] = []
    depth = 0
    obj_start: int | None = None
    in_str = False
    escaped = False
    for i, ch in enumerate(region):
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                obj_start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and obj_start is not None:
                try:
                    obj = json.loads(region[obj_start : i + 1])
                    if isinstance(obj, dict):
                        objs.append(obj)
                except (json.JSONDecodeError, ValueError):
                    pass
                obj_start = None
    return objs


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
    prompt = build_brief_prompt(persona)
    last_model: str | None = None
    for _ in range(_BRIEF_ATTEMPTS):
        try:
            completion = provider.complete(
                prompt,
                system=_SYSTEM_PROMPT,
                temperature=_BRIEF_TEMPERATURE,
                max_tokens=_BRIEF_MAX_TOKENS,
            )
        except InferenceError as exc:
            return BriefResult(status="error", message=f"Inference unavailable: {exc}")
        last_model = completion.model
        statements = attributable_statements(persona, parse_brief_json(completion.text))
        if statements:
            return BriefResult(status="ok", statements=tuple(statements), model=completion.model)
    # Both attempts came back with nothing attributable — degrade to records-only.
    return BriefResult(
        status="empty",
        model=last_model,
        message="The model returned no statement that could be traced to a source record, "
        "so nothing is shown. The raw records are below.",
    )


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
