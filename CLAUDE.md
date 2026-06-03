# CLAUDE.md — Keyworker Force-Multiplier (Hackathon Build)

*This file is the operating manual for this project. It is read by Claude Code as standing instructions and renders as a readable note in Obsidian. Re-read the "North Star" and "Hard Invariants" sections at the start of every milestone — they are the anchor against drift.*

---

## What we are building (North Star)

An **AI augmentation layer for the frontline keyworkers who re-engage NEET young people** — charity caseworkers, supported-employment coaches, FE pastoral staff. The tool synthesises a young person's history into pre-meeting context, drafts case notes and follow-ups *in the worker's own voice*, and surfaces risk and follow-up signals — **always as editable proposals the human authors and commits, never as autonomous actions or decisions.**

The honest value proposition, which everything serves: **"we do the paperwork so you can do the youth work."**

### What this demo is *for*

This is an open-weight hackathon (ADA Ventures involved). The goal is **credibility and validation in front of judges, not feature coverage.** Optimise every hour toward a crisp, believable demonstration of the *core insight* — that the AI proposes and the human disposes, running on sovereign infrastructure with no real personal data — over breadth of features. A narrow thing that works and tells the story beats a broad thing that half-works. When in doubt, cut scope, not polish.

---

## Hard Invariants (never violate, regardless of time pressure)

These are not features to be traded off. If a shortcut would break one of these, the shortcut is wrong.

1. **AI proposes, humans dispose.** Every AI output is an editable draft or a surfaced option. The system never commits a record, sends a message, or makes a recommendation autonomously. There is no path in the code where the machine takes an irreversible or consequential action without an explicit human action in between.

2. **The system is never the bearer of a denial.** Nothing in the UI ever tells a young person (or about a young person) "no" on the machine's authority. The AI surfaces options and context; humans own refusals, with reasons and alternatives. No "computer says no," anywhere.

3. **Synthetic data only — always.** The real product handles special-category data (mental health, safeguarding, children's data). For the hackathon we use **entirely fictional personas and synthetic records.** No real NEET data, no scraped data, no real client material. This is both an ethical hard line and a *demo asset* — it lets us tell the governance story cleanly to judges.

4. **Open-weight, self-hostable.** The model runs as an open-weight model on local/sovereign infrastructure (the hackathon constraint, and the real product's procurement-clearing advantage). No dependency on a closed cloud LLM API in the demo path. Treat "runs on our own infra" as a feature to show, not plumbing to hide.

5. **Authorship integrity.** Drafted notes preserve the worker's voice. The worker is always the author of record; the AI is a drafting assistant.

6. **Safeguarding escalation is human-owned.** If the system surfaces a risk indicator (self-harm, abuse, exploitation), it neither acts on it nor buries it — it routes to a clearly designed, human-owned escalation surface. Even in a demo, model this path; do not stub it into auto-action.

7. **Explainability.** Every surfaced signal traces to its source in the (synthetic) record. No unexplainable flags.

---

## The Methodology: "Hackathon Missions"

This is the **Missions Architecture compressed for a single day.** The full methodology's load-bearing idea is preserved: *agent context quality determines output quality, and the thing that builds something is a poor judge of it.* What changes is the ceremony, not the principle.

### What we keep, and why

| Discipline | Kept? | Hackathon form |
|---|---|---|
| Definition-of-done written **first** | **Fully kept** | A lean `validation-contract.md` (~8–15 assertions, demo-focused) written before any feature code. This is the primary anti-drift anchor and it's cheap. |
| Milestone gates | **Fully kept, time-boxed** | Milestones are hour-blocks across the day, each ending in a demoable slice and a validation check. |
| Durable decision log | **Fully kept** | `decisions.md` — every non-obvious choice logged, so context lost to compaction during a long session isn't re-litigated or quietly reversed. |
| Explicit scope freeze | **Fully kept** | An out-of-scope list + a parking lot. New ideas during the day go to the parking lot, not the build. |
| Implement ≠ validate | **Kept, compressed** | No standing three-role hierarchy. The main session implements; at each milestone gate it spawns a **fresh-context validator subagent** that has not seen the implementation reasoning and checks observed behaviour against the contract. |
| Test-first | **Selective** | Test-first only for the **load-bearing/risky logic** (the propose-not-act boundary, any data handling, the escalation path). UI/demo scaffolding does not need test-first. |
| Fix loop | **Single fast loop** | One time-boxed fix pass per gate. If it doesn't converge, **defer-and-log** as a known issue or escalate to Jakob — do not spiral. |

### Compressed roles

- **You (main Claude Code session) = Orchestrator + Worker.** Unlike the full methodology, you **may write deliverable code directly.** The strict no-implementation rule for the Orchestrator is dropped because spawning a worker per task is too slow for a day. But you still plan against the contract and work milestone by milestone.
- **Validator = a fresh subagent spawned at each milestone gate.** It receives only `validation-contract.md`, how to run the system, and the current milestone's scope — **not** your implementation history. It exercises the running system as a user would and reports PASS/FAIL with evidence. This preserves the anti-self-evaluation-bias guarantee at a fraction of the cost.

### Compressed shared state (four files, all at project root)

| File | Purpose |
|---|---|
| `CLAUDE.md` | This file. Operating manual + project constants + invariants. |
| `validation-contract.md` | The definition of done / demo-success assertions. Written first. Does not change without an explicit decision logged in `decisions.md`. |
| `missions.md` | The plan: time-boxed milestones, each with its features and which `VAL-` assertions it fulfils. Also holds the **out-of-scope list** and the **parking lot**. |
| `decisions.md` | Running log of decisions, discovered facts, and known/deferred issues. Append-only. |

Config (ports, model, startup commands) lives inline in this file under "Run & Config" rather than a separate `services.yaml` — the project is small enough.

---

## The Day's Lifecycle

### Phase 0 — Kickoff (do this first, ~20 min, with Jakob)
- Confirm the **tech stack** and record it under "Run & Config" below. (Stack is deliberately unset here — pin it at kickoff so this doc reflects reality. Constraint: Chromebook-grade, low-bandwidth browser client; open-weight self-hosted model.)
- Confirm the **single demo narrative**: the three-stakeholder arc we will show (worker walks in with AI-synthesised context → drafts a note in their own voice → a risk signal surfaces and routes to human-owned escalation → nothing is ever committed or denied by the machine).
- Resolve any ambiguity now. Do not start building with open questions.

### Phase 1 — Validation Contract (~20 min)
Write `validation-contract.md` **before any feature**. Lean and demo-focused. Each assertion: observable, atomic, pass/fail. Anchor several directly to the Hard Invariants (e.g. an assertion that proves no autonomous action is possible; an assertion that proves the escalation path is human-owned).

### Phase 2 — Milestone plan (~15 min)
Write `missions.md`. Decompose into **4–5 time-boxed milestones** for the day, each ending in something demoable. Front-load the milestone that proves the core primitive; back-load polish. Write the out-of-scope list now and keep it visible.

### Phases 3–N — Build, milestone by milestone
For each milestone:
1. **Re-read** the North Star, Hard Invariants, and this milestone's goal in `missions.md`. (Drift check.)
2. Build the features. Test-first on load-bearing logic only.
3. **Gate:** spawn a fresh-context validator subagent → run its checks against the contract → get PASS/FAIL with evidence.
4. **One fix pass** on blocking fails. If it converges, proceed. If not: defer-and-log or escalate.
5. Log decisions and any deferred issues in `decisions.md`.

### Final hour — Demo lock
Stop building. Freeze. Run the full demo narrative end to end against the validation contract once more. Anything not yet working is a known issue, not a last-minute build — last-minute building is how demos break on stage.

---

## Drift-Prevention Rituals (the whole point)

- **Re-read the anchor at every milestone start.** North Star + Hard Invariants + current milestone goal. Thirty seconds; prevents hours of wander.
- **Scope freeze is real.** A good idea at hour 4 is a parking-lot entry, not a new feature. The parking lot in `missions.md` is where good-but-out-of-scope ideas go to be safe without derailing the build.
- **Log it or lose it.** Any decision you'd be annoyed to re-make goes in `decisions.md` immediately. In a long session the context window will compact; the file is the memory that survives.
- **The contract doesn't move to match the code.** If you're tempted to edit an assertion to match what you built, stop — that's drift wearing a disguise. Changing the contract requires a logged decision and (for anything material) Jakob's say-so.

---

## Anti-Patterns (hackathon-specific)

- ❌ **Gold-plating** — polishing a feature past demo-credible while another part of the narrative is missing.
- ❌ **Scope creep via "while I'm here"** — adding unrequested capability mid-milestone.
- ❌ **Letting the core primitive get buried in breadth** — if a judge can't see "AI proposes, human disposes" in 60 seconds, breadth has cost you the point.
- ❌ **Any real or scraped personal data** — synthetic only, no exceptions.
- ❌ **Self-declaring done without the fresh-context validation pass.**
- ❌ **Spiralling on a failing milestone** — one fix pass, then defer-and-log or escalate.
- ❌ **Building in the final hour** — freeze and demo-lock instead.

---

## Escalation (fast, to Jakob)

Halt and ask Jakob when: a Hard Invariant is in tension with making the demo work; a milestone won't pass after one fix pass; or a Phase 0 ambiguity resurfaces. Give him: current state (what's working), the precise blocker, and the one decision you need. Keep it to a sentence or two — this is a hackathon, not a steering committee.

---

## Run & Config

*(Pinned at Phase 0 kickoff, 2026-06-03. See `decisions.md` D-001…D-003 for rationale.)*

- **Stack:** Python 3.11+ · **FastAPI** + **uvicorn** · **Jinja2** server-side templates · **HTMX** (+ Alpine.js only if needed) for interactivity · **SQLite** for storage (append-only table backs the immutable decision log) · **Pico.css** (classless, CDN) for styling. Chosen for auditability, low client bandwidth, and zero build step. No SPA framework.
- **Model (open-weight, single-H100):** **gpt-oss-120b** primary (open-weight MoE, MXFP4, fits one 80GB H100 by design); **Llama 3.3 70B Instruct** as swap-in fallback. Served via **OpenRouter** as a *cost stand-in* for self-hosted vLLM — accessed through an OpenAI-compatible `InferenceProvider` abstraction so the production swap to sovereign infra is a base-URL + key change. **Only open-weight models, ever** (Invariant 4). OpenRouter base URL: `https://openrouter.ai/api/v1`; key in `OPENROUTER_API_KEY` env var; model IDs `openai/gpt-oss-120b`, fallback `meta-llama/llama-3.3-70b-instruct`.
- **Start command(s):** `uvicorn app.main:app --reload --port 8000`
- **Ports / URLs:** http://localhost:8000
- **How to run the validator pass:** At each milestone gate, spawn a fresh-context validator subagent (Agent tool) given only `validation-contract.md`, the milestone's scope from `missions.md`, and "the app runs at http://localhost:8000 via `uvicorn app.main:app`." It exercises the running app as a user, returns PASS/FAIL with evidence per assertion, and does **not** see implementation history.

---

*Methodology adapted from the Missions Architecture (Factory.ai) — compressed for single-day time pressure while preserving its core insight: context quality determines output quality, and builders are poor judges of their own work. The four cheap drift-prevention disciplines are kept whole; the four expensive ceremonies are compressed, not cut.*
