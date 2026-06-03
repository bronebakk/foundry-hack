# Shared preamble — read this before any stream brief

*This applies to all three parallel streams (M3, M4, M5). Each stream's own brief
(`m3-context.md`, `m4-drafting.md`, `m5-escalation.md`) is a copy-pasteable launch prompt
for one remote agent. The preamble below is duplicated into each brief so they're
self-contained.*

## Orient first (do this before writing any code)
1. Read **`CLAUDE.md`** — the North Star and the 7 Hard Invariants are non-negotiable.
2. Read **`missions.md`** — especially the **Parallel-safety rules** and your milestone.
3. Skim **`decisions.md`** — note **D-001/D-002** (stack + open-weight-only inference) and
   **D-004** (authorship rule, below).
4. Read **`validation-contract.md`** — your definition of done is the `VAL-` assertions named in your brief.

## Branch off the frozen base
The foundation (M1) and the propose→log→dispose spine (M2) are done and pushed.
Branch from `main` (commit with M2 in it). Name your branch exactly as your brief says.

## FROZEN files — call them, never edit them
M1/M2 froze the shared layer so the three streams can't collide. Do **not** modify:
`app/main.py`, `app/db.py`, `app/models.py`, `app/config.py`, `app/services/data.py`,
`app/services/decision_log.py`, `app/services/inference.py`, `app/templating.py`,
`app/templates/base.html`, `app/templates/_nav.html`, `app/templates/_proposal.html`,
`app/static/base.css`, `app/data/personas/*`.
Your router stub is already registered in `main.py` — you only fill in your own files.
If you think you genuinely need to change a frozen file, **stop and log it in `decisions.md`**
as a coordination point for the M6 integration step — do not edit it.

## The frozen API you build on
```python
# Synthetic data (read-only)
from app.services import data
data.list_personas() -> list[Persona]
data.get_persona(persona_id) -> Persona | None
# Persona: .id .name .age .synthetic .summary_line .records (tuple[Record]) .demo_note
#          .record_count .has_risk_indicator  .get_record(record_id)
# Record:  .id .date .source .author .type .text
#          .risk_indicator .risk_category .risk_rationale

# Open-weight inference (generates text only — persists nothing)
from app.services.inference import provider
provider.configured                         # False if no OPENROUTER_API_KEY
provider.complete(prompt, system=None, model=None, temperature=0.3, max_tokens=1024)
#   -> Completion(text: str, model: str)    # raises InferenceError if no key

# The decision log — the ONLY write path (append-only)
from app.services import decision_log
decision_log.record(proposal, disposition, author, final_text=None) -> DecisionLogEntry
decision_log.list_entries(persona_id=None) -> list[DecisionLogEntry]   # newest first

# Domain types
from app.models import Proposal, Surface, ProposalType, Disposition
# Surface.CONTEXT | DRAFTING | ESCALATION
# ProposalType.BRIEF | CASE_NOTE | FOLLOW_UP | RISK_FLAG
# Disposition.COMMIT | DISCARD | SEND | ESCALATE
Proposal(persona_id, surface, proposal_type, proposal_text, model=None)  # in-memory; writes nothing

# Rendering
from app.templating import render
render(request, "your_stream/template.html", **ctx)   # injects the synthetic banner + worker
```

## The shared proposal partial — reuse it, don't reinvent it
Every AI output must be framed as an uncommitted, editable draft with human-owned actions.
Use `{% include "_proposal.html" %}` with this context:
```jinja
{% include "_proposal.html" with context %}
{#  proposal            : a Proposal object
    action_url          : your POST endpoint that records the human disposition
    actions             : [{"value": "commit", "label": "Commit as my note", "class": ""},
                           {"value": "discard", "label": "Discard", "class": "secondary outline"}]
    editable            : true (default) — worker can edit before disposing
    proposal_type_label : optional human label, e.g. "Case note"  #}
```

## 🔑 The one rule everyone must follow (D-004)
When your POST endpoint records a disposition, set the **author server-side** from
`config.DEMO_WORKER`. **Never** read the author from a client form field — hidden fields
can be spoofed, and the AI must never be the author of record (Invariant 5).
`decision_log.record` will reject an empty author or a model id, but it cannot know which
human you mean — so you must supply `config.DEMO_WORKER`.
```python
from app import config
decision_log.record(proposal, Disposition.COMMIT, author=config.DEMO_WORKER, final_text=form_final_text)
```

## Run / test / self-validate
```powershell
# from project root; a venv exists at .\.venv
.\.venv\Scripts\python.exe -m pytest -q                 # keep all existing tests green
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000   # serve at http://localhost:8000
```
- Add tests for your own load-bearing logic under `tests/` (name them `test_m3_*` etc.).
- Without an API key, `provider.complete` raises `InferenceError`. Handle it gracefully in
  the UI (show "inference not configured" rather than a 500) so the surface is demoable offline.
- Before you call yourself done: run the whole suite, boot the app, and walk your surface as
  a user against your `VAL-` assertions. Capture evidence (HTML snippets / screenshots).

## Definition of done
Your `VAL-` assertions pass when a fresh reviewer exercises the running app; all existing
tests still pass; you touched only your owned files; and you committed on your branch.
Do **not** merge to `main` — the M6 integration step does the merge and the cross-surface gate.
