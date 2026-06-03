"""ESCALATE surface — risk surfacing, human-owned escalation, no 'computer says no'.
OWNED BY MISSION M5.

The bright line this module holds (Invariants 2 & 6):

  * A risk indicator in the synthetic record is **surfaced** to the worker, traceable to
    its source. It is NEVER acted on automatically — no code path here notifies, refers, or
    escalates *because a flag exists*. Escalation happens ONLY when a human clicks (the POST
    handlers below), and the author of record is always set server-side from
    ``config.DEMO_WORKER`` (D-004), never the AI and never a client field.
  * The machine never **resolves** an escalation (the inbox is a human-owned queue) and never
    **denies** anything to a young person. Where an option can't currently proceed, we surface
    options + context and route the decision to a human — no machine 'no', anywhere.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from app import config
from app.models import Proposal, Surface, ProposalType, Disposition
from app.services import data, decision_log, integrity, safety
from app.services.inference import provider, InferenceError
from app.templating import render

# The server-built handoff note for the "no computer says no" path. Built (and signed) server-side
# so its recorded proposal text can't be forged at /refer (A08).
def _refer_context(persona) -> str:
    return (
        f"{persona.name} asked (own words) about an option that isn't open on its usual route. "
        "Routing the decision to a keyworker to review the alternatives on file and come back "
        "with a route and a reason."
    )

router = APIRouter(prefix="/escalation", tags=["escalation"])


# --- The escalation draft: a worker-editable note grounded in the synthetic record ----------
#
# The risk indicator itself lives in the data (data.py) — the model does NOT decide it is a
# risk. If inference is configured we use it ONLY to *summarise* the documented concern into a
# neutral note the worker edits and owns; offline we fall back to a record-derived draft. Either
# way the underlying source record is shown alongside, so the signal stays explainable.

@dataclass(frozen=True)
class EscalationDraft:
    text: str
    model: str | None  # the open-weight model that drafted it, or None if offline-derived


def _build_escalation_draft(persona, record) -> EscalationDraft:
    """A starting note for the worker to edit before escalating. Never autonomous: producing
    this text persists nothing and triggers nothing — it is only a draft."""
    fallback = (
        f"Raising a safeguarding concern about {persona.name} (synthetic persona, age "
        f"{persona.age}).\n\n"
        f"Category: {record.risk_category}.\n"
        f"Why flagged: {record.risk_rationale}\n\n"
        f"Source: {record.source} — {record.date} ({record.author}). Documented observation: "
        f"\"{record.text}\"\n\n"
        f"I am escalating this to the safeguarding lead for review. No automatic action has "
        f"been taken; this is my decision to refer."
    )
    if not provider.configured:
        return EscalationDraft(text=fallback, model=None)

    system = (
        "You draft a neutral, factual safeguarding escalation note FOR A HUMAN KEYWORKER TO "
        "EDIT and own. The risk indicator already exists in the case record — do NOT decide, "
        "diagnose, or assert that a young person IS being harmed. Summarise the documented "
        "concern in plain, careful language, grounded ONLY in the provided record. Keep it to "
        "a few sentences. The keyworker will edit this and is the author of record. "
        + safety.FENCE_INSTRUCTION
    )
    prompt = (
        f"Young person: {persona.name} (synthetic, age {persona.age}).\n"
        f"Recorded concern category: {record.risk_category}.\n"
        f"Rationale already on file: {record.risk_rationale}\n\n"
        f"Source record ({record.source}, {record.date}):\n{safety.fence(record.text)}\n\n"
        "Draft a short escalation note the keyworker can edit before sending to the "
        "safeguarding lead."
    )
    try:
        completion = provider.complete(prompt, system=system, temperature=0.2, max_tokens=400)
        text = (completion.text or "").strip() or fallback
        return EscalationDraft(text=text, model=completion.model)
    except InferenceError:
        # Degrade gracefully (Invariant 4 / offline demo): use the record-derived draft.
        return EscalationDraft(text=fallback, model=None)


# --- Surfaces -------------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def escalation_home(request: Request):
    """Overview: which (synthetic) young people have a safeguarding signal in their records.
    Surfacing them here acts on nothing — it is a list for the worker's judgement."""
    personas = data.list_personas()
    flagged = [p for p in personas if p.has_risk_indicator]
    open_escalations = [
        e for e in decision_log.list_entries() if e.disposition == Disposition.ESCALATE.value
    ]
    return render(
        request,
        "escalation/index.html",
        flagged=flagged,
        inbox_count=len(open_escalations),
    )


@router.get("/inbox", response_class=HTMLResponse)
def safeguarding_inbox(request: Request):
    """The human-owned escalation surface. Items appear here ONLY because a worker chose to
    send them (Disposition.ESCALATE). The machine puts nothing here automatically and marks
    nothing 'resolved' — a designated human owns and resolves these off-system."""
    entries = [
        e for e in decision_log.list_entries() if e.disposition == Disposition.ESCALATE.value
    ]
    items = []
    for e in entries:
        persona = data.get_persona(e.persona_id) if e.persona_id else None
        items.append(
            {
                "entry": e,
                "persona_name": persona.name if persona else (e.persona_id or "—"),
                "is_safeguarding": e.proposal_type == ProposalType.RISK_FLAG.value,
            }
        )
    return render(request, "escalation/inbox.html", items=items)


@router.get("/{persona_id}", response_class=HTMLResponse)
def escalation_persona(request: Request, persona_id: str):
    """Surface the risk flag(s) for one young person, each traceable to the exact source
    record, with an editable escalation draft the worker may (or may not) act on."""
    persona = data.get_persona(persona_id)
    if persona is None:
        return render(request, "escalation/index.html",
                      flagged=[p for p in data.list_personas() if p.has_risk_indicator],
                      inbox_count=0, error=f"No persona '{persona_id}'.")

    risk_items = []
    for record in persona.records:
        if not record.risk_indicator:
            continue
        draft = _build_escalation_draft(persona, record)
        proposal = Proposal(
            persona_id=persona.id,
            surface=Surface.ESCALATION,
            proposal_type=ProposalType.RISK_FLAG,
            proposal_text=draft.text,
            model=draft.model,
        )
        sig = integrity.sign(integrity.provenance(
            persona.id, Surface.ESCALATION.value, ProposalType.RISK_FLAG.value,
            draft.model, draft.text))
        risk_items.append({"record": record, "proposal": proposal, "sig": sig})

    # The "no computer says no" surface: an option the young person asked about (their own words
    # in a self-referral) that can't currently proceed on its usual route. We never refuse on the
    # machine's authority — we show their ask + the routes already noted on file + a human-delivered
    # path. Data-driven per persona (M6): the alternatives come from the records, never hardcoded,
    # so this reads correctly for whoever it surfaces (e.g. Leah's course, Marcus's funded place).
    aspiration_record = next(
        (r for r in persona.records if r.type == "self_referral"), None
    )
    support_types = {"admissions_note", "work_coach_note", "keyworker_note"}
    support_notes = [r for r in persona.records if r.type in support_types]

    # The refer ("no computer says no") handoff note — built and signed server-side (A08).
    refer_context = _refer_context(persona)
    refer_sig = integrity.sign(integrity.provenance(
        persona.id, Surface.ESCALATION.value, ProposalType.FOLLOW_UP.value, "", refer_context))

    return render(
        request,
        "escalation/persona.html",
        persona=persona,
        risk_items=risk_items,
        ai_available=provider.configured,
        aspiration_record=aspiration_record,
        support_notes=support_notes,
        refer_context=refer_context,
        refer_sig=refer_sig,
    )


# --- Human dispositions (the ONLY write paths) ----------------------------------------------

@router.post("/{persona_id}/escalate", response_class=HTMLResponse)
def escalate(
    request: Request,
    persona_id: str,
    disposition: str = Form(...),
    proposal_text: str = Form(""),
    final_text: str = Form(""),
    model: str = Form(""),
    proposal_sig: str = Form(""),
):
    """Record the worker's decision about a surfaced risk. This fires ONLY on a human click.
    Author is set server-side (D-004) — never trusted from the form. A08: the AI proposal text
    and model must carry the server's signature from when they were surfaced, so neither can be
    forged into the safeguarding log."""
    if not integrity.verify(
        integrity.provenance(persona_id, Surface.ESCALATION.value,
                             ProposalType.RISK_FLAG.value, model, proposal_text),
        proposal_sig,
    ):
        return render(request, "escalation/index.html",
                      flagged=[p for p in data.list_personas() if p.has_risk_indicator],
                      inbox_count=0,
                      error="That escalation couldn't be verified — nothing was recorded.")

    proposal = Proposal(
        persona_id=persona_id,
        surface=Surface.ESCALATION,
        proposal_type=ProposalType.RISK_FLAG,
        proposal_text=proposal_text,
        model=(model or None),
    )

    if disposition == Disposition.ESCALATE.value:
        entry = decision_log.record(
            proposal, Disposition.ESCALATE,
            author=config.DEMO_WORKER, final_text=final_text,
        )
        outcome = "escalated"
    elif disposition == Disposition.DISCARD.value:
        # The worker reviewed and chose not to escalate (yet). Logged for honest governance;
        # nothing is sent. final_text stays None — nothing was committed as an action.
        entry = decision_log.record(
            proposal, Disposition.DISCARD, author=config.DEMO_WORKER,
        )
        outcome = "reviewed_no_escalation"
    else:
        # Unknown disposition: write nothing, surface the page again.
        return render(request, "escalation/index.html",
                      flagged=[p for p in data.list_personas() if p.has_risk_indicator],
                      inbox_count=0, error="Unrecognised action — nothing was recorded.")

    persona = data.get_persona(persona_id)
    return render(
        request, "escalation/escalated.html",
        entry=entry, persona=persona, outcome=outcome,
    )


@router.post("/{persona_id}/refer", response_class=HTMLResponse)
def refer_to_human(
    request: Request,
    persona_id: str,
    context_text: str = Form(""),
    final_text: str = Form(""),
    proposal_sig: str = Form(""),
):
    """The 'no computer says no' path: where an option can't currently proceed, the worker
    routes the DECISION to a human rather than the machine issuing a refusal. Recorded as a
    human-initiated escalation (a decision a human must make and deliver). A08: the routed
    context is server-built and signed, so it can't be forged into the log."""
    if not integrity.verify(
        integrity.provenance(persona_id, Surface.ESCALATION.value,
                             ProposalType.FOLLOW_UP.value, "", context_text),
        proposal_sig,
    ):
        return render(request, "escalation/index.html",
                      flagged=[p for p in data.list_personas() if p.has_risk_indicator],
                      inbox_count=0,
                      error="That referral couldn't be verified — nothing was recorded.")

    proposal = Proposal(
        persona_id=persona_id,
        surface=Surface.ESCALATION,
        proposal_type=ProposalType.FOLLOW_UP,
        proposal_text=context_text,
        model=None,
    )
    entry = decision_log.record(
        proposal, Disposition.ESCALATE,
        author=config.DEMO_WORKER, final_text=final_text,
    )
    persona = data.get_persona(persona_id)
    return render(
        request, "escalation/escalated.html",
        entry=entry, persona=persona, outcome="referred",
    )
