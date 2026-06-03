# missions.md — Keyworker Force-Multiplier (Hackathon)

*The plan: time-boxed milestones, each ending in a demoable slice and a validator gate. Mapped to the `VAL-` assertions in `validation-contract.md`. Also holds the **out-of-scope list** and the **parking lot**. Re-read the North Star + Hard Invariants (CLAUDE.md) at the start of every milestone — drift check.*

*Demo narrative this all serves: **worker walks in with AI-synthesised context → drafts a note in their own voice → a risk signal surfaces and routes to a human-owned escalation → nothing is ever committed or denied by the machine.***

---

## Dependency graph (parallelism)

```
  M1 ──► M2 ──┬──► M3 (CTX)      ─┐
              ├──► M4 (DRAFT)    ─┼──► M6 ──► M7
              └──► M5 (ESCALATE) ─┘
   sequence      ── parallel ──     sequence
```

- **M1 → M2 in sequence.** Foundation, then the propose→log→dispose spine. Everything depends on both.
- **M3, M4, M5 in parallel.** Three independent vertical slices on top of the *frozen* shared services from M1/M2. Safe to run as three branches / agents at once (see "Parallel-safety rules" below).
- **M6 → M7 in sequence.** Integrate the three slices into one narrative + governance polish, then freeze and run the full contract.

> The whole reason 3–5 can run in parallel is that **M1 and M2 freeze the shared interfaces and pre-create empty router/template stubs.** A parallel stream fills in *its own* stub files and only *calls* the frozen services — it never edits another stream's files, and (ideally) never edits `main.py`.

---

## Parallel-safety rules (read before branching M3–M5)

**Frozen after M1/M2 — parallel streams may CALL but not EDIT:**
`app/main.py` (router registration), `app/db.py`, `app/models.py`, `app/services/inference.py`, `app/services/data.py`, `app/services/decision_log.py`, `app/templates/base.html`, `app/templates/_nav.html`, `app/static/base.css`, `app/data/personas/*` (read-only).

**Each stream OWNS (only it edits these):**

| Stream | Router | Templates | Static |
|---|---|---|---|
| M3 CTX | `app/routers/context.py` | `app/templates/context/` | `app/static/context.*` |
| M4 DRAFT | `app/routers/drafting.py` | `app/templates/drafting/` | `app/static/drafting.*` |
| M5 ESCALATE | `app/routers/escalation.py` | `app/templates/escalation/` | `app/static/escalation.*` |

- M1 pre-creates the three router files as **empty stubs already registered in `main.py`**, so streams never touch `main.py` and never collide there.
- Branch per stream off the post-M2 commit (`git init` happens in M1). Merge order into the integration branch is irrelevant because file ownership is disjoint.
- If a stream discovers it needs a change to a *frozen* file, that's a coordination point: log it in `decisions.md` and make the change in the integration step (M6), not mid-stream.

---

## Milestones

### M1 — Foundation & scaffold *(sequence)*
**Goal**: A running FastAPI app at http://localhost:8000 with the shell, storage, synthetic data, and the inference abstraction — nothing AI yet, but everything the streams stand on.
**Scope (in)**:
- `git init`; project skeleton per the layout below.
- FastAPI + uvicorn boots; `base.html` + `_nav.html` + Pico.css shell renders; nav links to the three (stub) stream surfaces + the (stub) decision log.
- `db.py`: SQLite schema incl. the **append-only `decision_log` table** (no UPDATE/DELETE path).
- `services/inference.py`: `InferenceProvider` (OpenAI-compatible) pointed at OpenRouter via `OPENROUTER_API_KEY`, model `openai/gpt-oss-120b`, fallback `meta-llama/llama-3.3-70b-instruct`. One smoke-test call confirms it answers.
- `data/personas/`: **2–3 synthetic personas** with fragmented multi-source records (so CTX has something to synthesise) — at least one carrying a **risk indicator** for M5. Every persona/record carries a visible **synthetic/demo marker**.
- Pre-create empty registered router stubs for context / drafting / escalation / governance.
**VAL fulfilled (built here, validated later)**: groundwork for VAL-GOV-001 (synthetic markers), VAL-GOV-002 (open-weight provider).
**Depends on**: nothing.
**Gate**: Validator confirms the app boots, the shell renders, the inference smoke test returns from an open-weight model, and synthetic markers are present on the seed data.
**Time-box**: ~75 min.

### M2 — The propose → log → dispose spine *(sequence)*
**Goal**: The core primitive, built once, correctly: AI output is always a proposal; acting on it is an explicit human step; every human disposition is recorded immutably. This is the demo's spine — front-loaded deliberately.
**Scope (in)**:
- `models.py`: `Persona`, `Record`, `Proposal`, `DecisionLogEntry` (frozen after this milestone).
- `services/data.py`: read API for personas/records (frozen).
- `services/decision_log.py`: `record(proposal, disposition, author)` append-only API + a read API; **no edit/delete path in code** (frozen).
- Establish the boundary in code: **generation persists/sends nothing**; only an explicit human action calls `decision_log.record()` and/or commits. A shared "proposal" UI partial (draft styling, accept / edit / discard affordances) the streams reuse.
- Test-first on this load-bearing logic: a test proving generation alone writes no committed state, and that `decision_log` rejects mutation.
**VAL fulfilled**: **VAL-PROPOSE-001** (incl. its supplementary code-path check — *no path persists/sends on generation*); foundation of **VAL-PROPOSE-003** (proposal framing) and **VAL-GOV-003** (immutable log).
**Depends on**: M1.
**Gate**: Validator + code check confirm generation commits nothing, the decision log is append-only, and the shared proposal affordances exist. **This gate is the most important of the day — do not wave it through.**
**Time-box**: ~75 min.

### M3 — CTX: pre-meeting context synthesis *(parallel)*
**Goal**: Worker opens a synthetic persona and gets a concise, glanceable synthesised brief where **every claim traces to its source**.
**Scope (in)**:
- `routers/context.py` + `templates/context/`: persona list → persona view with an AI-synthesised brief.
- Brief generated via `InferenceProvider` from `data.py` records; rendered as a proposal (not a committed record).
- **Explainability**: each statement in the brief links/hovers back to the specific source passage it draws from.
**VAL fulfilled**: **VAL-CTX-001** (synthesised brief), **VAL-CTX-002** (every claim traces to source — anchors Invariant 7).
**Depends on**: M2 (uses `data.py`, `inference.py`, proposal partial). Independent of M4, M5.
**Gate**: Fresh-context validator: brief appears alongside its source records; a clicked claim reveals its originating passage.
**Time-box**: ~2.5 h wall (parallel).

### M4 — DRAFT: drafting, authorship & the propose-not-act boundary *(parallel)*
**Goal**: Worker requests a case-note draft and a follow-up message; both are editable drafts the worker authors and commits; nothing is committed or sent autonomously.
**Scope (in)**:
- `routers/drafting.py` + `templates/drafting/`: "draft a case note" + "draft a follow-up message to the young person".
- Draft appears in an editable field, **clearly marked uncommitted**. Worker edits → commit writes the record **attributed to the worker** (not "generated by AI") and logs the disposition via `decision_log`.
- The follow-up message has a **separate explicit send** action; until clicked, the outbound log shows nothing sent. Every output carries **accept / edit / discard**.
**VAL fulfilled**: **VAL-DRAFT-001**, **VAL-DRAFT-002** (authorship — Invariant 5), **VAL-PROPOSE-001/-002/-003** (Invariant 1).
**Depends on**: M2. Independent of M3, M5.
**Gate**: Validator: no record on generation; committed record shows worker edits + worker authorship; no send until explicit click; discard option visible.
**Time-box**: ~2.5 h wall (parallel).

### M5 — ESCALATE: risk surfacing, human-owned escalation & no "computer says no" *(parallel)*
**Goal**: A risk indicator in a persona's record is surfaced to the worker (never acted on); the worker can route it to a human-owned escalation surface; and no surface ever delivers a machine-authored denial about a young person.
**Scope (in)**:
- `routers/escalation.py` + `templates/escalation/`: surface the risk flag on the persona, **traceable to its source record** (explainability), with **no auto-notification / auto-referral**.
- **Human-initiated** escalation → arrives at a designated **human-owned escalation surface** (e.g. a "safeguarding inbox" view). The machine neither initiates nor resolves it; the disposition is logged.
- A surface where an option is unavailable for the young person shows **options + context routed to a human**, never a machine "no".
**VAL fulfilled**: **VAL-ESCALATE-001**, **VAL-ESCALATE-002** (Invariant 6), **VAL-DENY-001** (Invariant 2).
**Depends on**: M2 (needs M1's risk-bearing persona). Independent of M3, M4.
**Gate**: Validator: flag surfaced with source, no auto-action; human-initiated escalation lands on the human-owned surface; no machine-authored denial anywhere.
**Time-box**: ~2.5 h wall (parallel).

### M6 — Integration & governance polish *(sequence)*
**Goal**: Stitch the three slices into the single three-stakeholder narrative and finish the governance story.
**Scope (in)**:
- Merge the three branches; wire the nav/flow so the demo runs as one arc end to end.
- `routers/governance.py` + `templates/governance/`: the **human-facing decision-log viewer** (shows AI proposal → human disposition → worker attribution; append-only, no edit/delete).
- Synthetic-marker sweep across every persona/record; confirm the open-weight `InferenceProvider` config is inspectable and contains only open-weight model IDs.
**VAL fulfilled**: **VAL-GOV-001** (synthetic markers — Invariant 3), **VAL-GOV-002** (open-weight/portability — Invariant 4), **VAL-GOV-003** (immutable decision log).
**Depends on**: M3, M4, M5.
**Gate**: Validator runs the full narrative; confirms GOV-001/-002/-003 and that the three slices cohere.
**Time-box**: ~90 min.

### M7 — Demo lock *(sequence)*
**Goal**: Freeze. Prove the whole thing once more against the whole contract. Last-minute building is how demos break on stage.
**Scope (in)**:
- **Stop building.** Run the full demo narrative end to end.
- Final fresh-context validator pass against **all 14 assertions**; record PASS/FAIL with evidence.
- Anything failing becomes a **known issue** in `decisions.md`, not a new build.
**VAL fulfilled**: full-contract regression.
**Depends on**: M6.
**Gate**: The demo narrative runs clean; the validator's evidence pack is captured for the judges' governance story.
**Time-box**: ~60 min.

---

## Proposed file layout (pin in M1)

```
app/
  main.py                  # FastAPI app; registers all routers (incl. M3–M5 stubs). Frozen after M1.
  db.py                    # SQLite connection + schema (append-only decision_log). M1/M2.
  models.py                # Persona, Record, Proposal, DecisionLogEntry. Frozen after M2.
  services/
    inference.py           # InferenceProvider → OpenRouter (open-weight only). Frozen after M1.
    data.py                # persona/record read API. Frozen after M2.
    decision_log.py        # append-only record()/read. Frozen after M2.
  routers/
    context.py             # M3 owns      drafting.py  # M4 owns
    escalation.py          # M5 owns      governance.py # M6 owns
  templates/
    base.html  _nav.html   # M1, frozen
    context/ drafting/ escalation/ governance/   # owned per-stream
  static/                  # base.css (M1) + per-stream namespaced files
  data/personas/           # synthetic personas + records (M1, read-only to streams)
tests/                     # M2 load-bearing tests
```

---

## Out-of-scope (scope freeze — do NOT build this for the demo)

- Real authentication / multi-user accounts / RBAC (single demo worker identity is fine).
- Cross-agency data fusion or any real data-sharing (briefing §4: single-controller scope only; v1 is manual cross-referencing).
- Actually self-hosting vLLM / standing up a GPU (OpenRouter stand-in per D-002).
- A young-person-facing app/portal (the demo is the keyworker workbench; DENY is shown within the worker surface).
- Bias-testing / DPIA tooling, PSED analytics (real-product governance, not demo-credible in a day — narrate it, don't build it).
- Email/SMS gateway integration (the "send" is a demonstrable in-app action + outbound log, not a real message).
- Mobile/responsive polish beyond "works on a low-spec browser"; offline/voice/plain-language access floor.
- Fine-tuning or voice-cloning for authorship (prompt-level voice preservation only).
- Payment/pricing, multi-tenant, deployment/CI.

## Parking lot (good ideas — captured so they don't derail the build)

*(empty — add `[date] idea — why it's tempting — why it waits` entries here as they come up)*

---

*Assertion coverage check: CTX-001/002 → M3 · DRAFT-001/002 + PROPOSE-001/002/003 → M4 (PROPOSE-001 code path established M2) · ESCALATE-001/002 + DENY-001 → M5 · GOV-001/002/003 → M6 (built M1/M2). All 14 assertions land.*
