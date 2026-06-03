"""DRAFT surface — drafting, authorship & the propose-not-act boundary. OWNED BY MISSION M4.

This is the most-watched surface for the core demo primitive: "AI proposes, human disposes."
A keyworker requests a case-note draft and a follow-up message; both arrive as editable
drafts in the worker's own voice. Generation writes NOTHING — the only write is an explicit
human disposition routed through the frozen ``decision_log`` (the single append-only spine).

Load-bearing rules enforced here:
  * No write on generation (Invariant 1 / VAL-PROPOSE-001) — ``/generate`` only builds an
    in-memory ``Proposal`` and renders it; ``/dispose`` is the only path that records.
  * Author is server-side from ``config.DEMO_WORKER`` (D-004) — never read from the form,
    so a spoofed hidden ``author`` field is ignored; the AI is never the author (Invariant 5).
  * No autonomous send (VAL-PROPOSE-002) — a follow-up counts as "sent" only on an explicit
    SEND disposition, reflected in the per-persona outbound log.
"""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from app import config
from app.models import Disposition, Proposal, ProposalType, Surface
from app.services import data, decision_log
from app.services.inference import InferenceError, provider
from app.templating import render

router = APIRouter(prefix="/drafting", tags=["drafting"])


# --- Prompting (prompt-level voice preservation only — see missions out-of-scope) ---

_CASE_NOTE_SYSTEM = (
    "You are a drafting assistant for a UK youth-work keyworker. You draft case notes in the "
    "FIRST PERSON as the keyworker, in their own plain, professional voice. Write a concise, "
    "factual case note for a meeting just held with a young person, suitable for a charity "
    "keyworker case record. Use only the context and the worker's meeting notes provided — do "
    "not invent facts. Do not make decisions or refusals on the worker's behalf. "
    "Output only the note text, no preamble."
)
_FOLLOW_UP_SYSTEM = (
    "You are a drafting assistant for a UK youth-work keyworker. You draft a short, warm "
    "follow-up MESSAGE addressed directly to the young person, in the keyworker's own voice. "
    "Keep it brief, encouraging, and concrete about the next step. Never deliver a refusal or "
    "a 'no' in this message — if something cannot happen, that is for the worker to handle in "
    "person, not for this message to announce. Output only the message text, no preamble."
)

# Per-proposal-type config: which system prompt, the human label, and the disposition actions.
_DRAFT_KINDS = {
    ProposalType.CASE_NOTE: {
        "system": _CASE_NOTE_SYSTEM,
        "label": "Case note",
        "actions": [
            {"value": "commit", "label": "Commit as my note", "class": ""},
            {"value": "discard", "label": "Discard", "class": "secondary outline"},
        ],
    },
    ProposalType.FOLLOW_UP: {
        "system": _FOLLOW_UP_SYSTEM,
        "label": "Follow-up message",
        "actions": [
            {"value": "send", "label": "Send message", "class": ""},
            {"value": "discard", "label": "Discard", "class": "secondary outline"},
        ],
    },
}


def _persona_context(persona) -> str:
    """The (synthetic) source material the draft draws from — fed to the model verbatim."""
    lines = [f"Young person: {persona.name}, age {persona.age}.", f"Summary: {persona.summary_line}", "", "Records on file:"]
    for r in persona.records:
        lines.append(f"- [{r.date}] {r.source} ({r.author}): {r.text}")
    return "\n".join(lines)


def _canned_draft(persona, kind: ProposalType, meeting_notes: str) -> str:
    """Clearly-marked placeholder used when inference is not configured, so the
    propose→dispose boundary is still demonstrable offline (KI-001). Marked in the UI, not
    buried in the text — the worker still edits and owns whatever they commit."""
    if kind is ProposalType.CASE_NOTE:
        note = (
            f"Met with {persona.name} today. "
            + (f"{meeting_notes.strip()} " if meeting_notes.strip() else "")
            + "Talked through how things are going and what support would help next. "
            "Agreed to follow up shortly and keep the next step small and concrete."
        )
        return note
    return (
        f"Hi {persona.name.split()[0]}, really good to catch up today. I'll sort out the next "
        "step we talked about and come back to you this week. Anything you need before then, "
        "just message me. — Sam"
    )


def _ledger(persona_id: str):
    """The per-persona record of truth: what was actually committed / sent (newest first).
    Read-only — proves generation produced nothing here until an explicit human action."""
    entries = decision_log.list_entries(persona_id)
    committed = [e for e in entries if e.disposition == Disposition.COMMIT.value
                 and e.proposal_type == ProposalType.CASE_NOTE.value]
    sent = [e for e in entries if e.disposition == Disposition.SEND.value
            and e.proposal_type == ProposalType.FOLLOW_UP.value]
    return committed, sent


# --- Routes ---

@router.get("/", response_class=HTMLResponse)
def drafting_home(request: Request):
    """Reachable from the nav; pick a persona to draft for."""
    return render(request, "drafting/index.html", personas=data.list_personas())


@router.get("/{persona_id}", response_class=HTMLResponse)
def drafting_workbench(request: Request, persona_id: str):
    persona = data.get_persona(persona_id)
    if persona is None:
        return render(request, "drafting/not_found.html", persona_id=persona_id)
    committed, sent = _ledger(persona_id)
    return render(
        request,
        "drafting/workbench.html",
        persona=persona,
        committed=committed,
        sent=sent,
    )


@router.post("/{persona_id}/generate", response_class=HTMLResponse)
def generate_draft(
    request: Request,
    persona_id: str,
    proposal_type: str = Form(...),
    meeting_notes: str = Form(""),
):
    """Generate a draft. This builds an in-memory Proposal and renders it — it persists
    NOTHING (VAL-PROPOSE-001). Disposition happens only at ``/dispose``."""
    persona = data.get_persona(persona_id)
    if persona is None:
        return render(request, "drafting/not_found.html", persona_id=persona_id)

    try:
        kind = ProposalType(proposal_type)
    except ValueError:
        kind = ProposalType.CASE_NOTE
    if kind not in _DRAFT_KINDS:
        kind = ProposalType.CASE_NOTE
    cfg = _DRAFT_KINDS[kind]

    inference_note = None
    if provider.configured:
        prompt = _persona_context(persona)
        if kind is ProposalType.CASE_NOTE and meeting_notes.strip():
            prompt += f"\n\nWorker's notes from the meeting just held:\n{meeting_notes.strip()}"
        try:
            completion = provider.complete(prompt, system=cfg["system"], temperature=0.4, max_tokens=500)
            draft_text, model = completion.text.strip(), completion.model
        except InferenceError as exc:  # configured but the call failed — degrade, don't 500
            draft_text = _canned_draft(persona, kind, meeting_notes)
            model = "(canned demo — inference error)"
            inference_note = f"Inference call failed ({exc.__class__.__name__}); showing a canned placeholder draft."
    else:
        draft_text = _canned_draft(persona, kind, meeting_notes)
        model = "(canned demo — inference not configured)"
        inference_note = (
            "Inference is not configured (no OPENROUTER_API_KEY). This is a canned placeholder "
            "draft so the propose→dispose boundary is still demonstrable — set the key for live drafting."
        )

    proposal = Proposal(
        persona_id=persona_id,
        surface=Surface.DRAFTING,
        proposal_type=kind,
        proposal_text=draft_text,
        model=model,
    )
    return render(
        request,
        "drafting/_draft.html",
        proposal=proposal,
        action_url=f"/drafting/{persona_id}/dispose",
        actions=cfg["actions"],
        proposal_type_label=cfg["label"],
        inference_note=inference_note,
    )


@router.post("/{persona_id}/dispose", response_class=HTMLResponse)
def dispose_draft(
    request: Request,
    persona_id: str,
    surface: str = Form(...),
    proposal_type: str = Form(...),
    proposal_text: str = Form(...),
    model: str = Form(""),
    disposition: str = Form(...),
    final_text: str = Form(""),
):
    """The ONLY write path on this surface. Reconstruct the proposal from the posted fields,
    record the human disposition with a SERVER-SIDE author (D-004), and show the outcome.

    Note: there is deliberately no ``author`` parameter here — even if the form posts one, we
    ignore it. The author of record is always ``config.DEMO_WORKER`` (Invariant 5)."""
    persona = data.get_persona(persona_id)
    if persona is None:
        return render(request, "drafting/not_found.html", persona_id=persona_id)

    proposal = Proposal(
        persona_id=persona_id,
        surface=Surface(surface),
        proposal_type=ProposalType(proposal_type),
        proposal_text=proposal_text,
        model=model or None,
    )
    disp = Disposition(disposition)
    # final_text is the worker's edited, committed words; for a discard nothing is kept.
    kept_text = None if disp is Disposition.DISCARD else final_text

    entry = decision_log.record(
        proposal,
        disp,
        author=config.DEMO_WORKER,  # server-side; a client-supplied author is never trusted
        final_text=kept_text,
    )

    committed, sent = _ledger(persona_id)
    return render(
        request,
        "drafting/disposed.html",
        persona=persona,
        entry=entry,
        committed=committed,
        sent=sent,
    )
