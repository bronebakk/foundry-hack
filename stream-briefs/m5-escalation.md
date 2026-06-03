# Stream brief — M5 · ESCALATE (risk surfacing, human-owned escalation, no "computer says no")

> Paste this whole file to the remote agent as its task. It is self-contained.
> **Branch:** `m5-escalation` (off `main`). **You own only:** `app/routers/escalation.py`,
> `app/templates/escalation/`, `app/static/escalation.*`. Everything else is frozen — see the
> preamble. Read `CLAUDE.md`, `missions.md`, `decisions.md`, `validation-contract.md` first.
> ⚠️ This surface touches safeguarding. Model the human-owned path carefully — never stub it
> into auto-action.

---

## Your goal
A risk indicator in a young person's records is **surfaced to the worker** (never acted on),
traceable to its source. The worker can **initiate** an escalation, which routes to a
**human-owned escalation surface** (a "safeguarding inbox"). The machine neither initiates
nor resolves it. And nowhere does any surface deliver a machine-authored **denial** about a
young person — refusals are routed to a human with a reason and an alternative.

Use persona **`leah-sumner`** — record `leah-r2` carries a synthetic CSE/CCE indicator with a
`risk_category` and `risk_rationale` already attached.

## Your assertions (definition of done)
- **VAL-ESCALATE-001** *(Invariant 6)* — A risk indicator is **surfaced** to the worker and
  **not acted upon**: no auto-notification, no auto-referral. Evidence: the surfaced flag +
  confirmation nothing was auto-triggered by the flag alone.
- **VAL-ESCALATE-002** *(Invariant 6)* — Escalation is **human-initiated** and routed to a
  **human-owned surface**; the machine neither initiates nor resolves it. Evidence: the
  human-initiated escalation arriving at the human-owned surface.
- **VAL-DENY-001** *(Invariant 2)* — Where something can't currently proceed for a young
  person, the system does **not** display a machine-authored "no". It surfaces options and
  context, and any actual refusal is routed to a human who delivers it with a reason and an
  alternative. Evidence: absence of a machine "no" + the path by which a refusal reaches a human.

## What to build
1. **`GET /escalation/` and/or `GET /escalation/{persona_id}`** — surface the risk flag(s):
   - Find records where `record.risk_indicator` is true (`persona.has_risk_indicator`,
     `record.risk_category`, `record.risk_rationale`).
   - Show the flag **with its source** — quote/link the exact record (`leah-r2`) and show the
     `risk_rationale` ("why flagged"). Explainability: a worker must see *what* triggered it.
   - Make it unmistakable that this is **surfaced for judgement, not acted on** — copy like
     "No automatic action has been or will be taken. You decide what happens next."
2. **Human-initiated escalation** — a button the **worker** clicks to escalate. On click,
   POST a disposition: `decision_log.record(proposal, Disposition.ESCALATE,
   author=config.DEMO_WORKER, final_text=<worker's note>)` with `ProposalType.RISK_FLAG`.
   The `proposal_text` can be the AI/record-derived risk summary; `final_text` is the
   worker's framing. **Author server-side (D-004).**
3. **A human-owned escalation surface** — a "Safeguarding inbox" view
   (`GET /escalation/inbox` or similar) that lists escalations that **a human initiated**
   (read them via `decision_log.list_entries()` filtered to `Disposition.ESCALATE`, or your
   own rendering). It must read as a queue a human owns and resolves — the machine does not
   mark anything "resolved". Show that the item arrived *because the worker sent it*, not
   automatically.
4. **No "computer says no"** — include at least one surface where an option is currently
   unavailable for the young person (e.g. a course/opportunity that's full or has a closed
   deadline). Instead of a machine refusal, show **options + context** and a clear path that
   **a human delivers the outcome** with a reason and an alternative. The young person (or a
   record about them) must never be told "no" on the machine's authority.

## The bright line (do not cross)
- The flag is **surfaced**, never **acted on**. No code path sends a notification, makes a
  referral, or escalates *because a flag exists*. Escalation happens **only** when the human
  clicks. Write a test that proves this.
- The machine never **resolves** an escalation and never **denies** anything to a young
  person. Humans own refusals and resolutions.

## Inference / offline
- The risk indicator itself is in the synthetic data — you do **not** need the model to
  detect it (and shouldn't claim the model "decided" it's a risk). If you use
  `provider.complete` to *summarise* the concern for the worker, keep it open-weight,
  degrade gracefully if `provider.configured` is False, and always show the underlying
  record so the signal is explainable and human-judged.

## Tests to add (`tests/test_m5_escalation.py`)
- **No auto-action:** loading/surfacing the flag creates **no** decision-log entry and
  triggers no notification/referral; `decision_log.list_entries()` count is unchanged after
  viewing. Only the human escalate POST creates a `Disposition.ESCALATE` entry.
- **Human-owned routing:** after the worker escalates, the safeguarding-inbox view shows the
  item, attributed to `config.DEMO_WORKER`; the machine sets no "resolved" state.
- **Explainability:** the surfaced flag page contains the source record text/id and the
  `risk_rationale`.
- **No machine denial:** the "unavailable option" surface contains no machine-authored "no";
  it presents options/alternatives and a human-delivered path. (Assert your copy, e.g. the
  page does not render a bare refusal and does render an alternative + a human handoff.)
- Keep all existing tests green.

## Don'ts
- No auto-notification, auto-referral, auto-resolution, or machine denial — anywhere.
- Don't trust a client-supplied author. Don't edit frozen files. Don't merge to `main`.
