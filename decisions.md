# decisions.md — Keyworker Force-Multiplier (Hackathon)

*Append-only log of non-obvious decisions, discovered facts, and known/deferred issues. The memory that survives context compaction. Newest at the bottom of each section. Do not rewrite history — supersede with a new entry.*

---

## Decisions

### D-001 — App stack pinned: FastAPI + HTMX + Jinja2 + SQLite
**Date**: 2026-06-03 · **By**: Jakob (kickoff) · **Status**: Active

Stack: Python 3.11+ / FastAPI + uvicorn / Jinja2 server-side templates / HTMX (+ Alpine.js only if needed) / SQLite / Pico.css (CDN).

**Why**: Constraints favour "boring and robust" — auditability (legible Python, small dependency surface, no `node_modules` sprawl), a low-bandwidth Chromebook-grade client (no megabyte SPA bundle; HTMX is ~14kb; zero build step), and a single-day build. The immutable decision log (D-003) maps cleanly to an append-only SQLite table. Rejected a React/Next.js SPA (heavier client, larger dependency/audit surface, slower to stand up) and a Node/HTMX variant (Python's OpenAI SDK + readability edge suit the governance-heavy pitch better).

### D-002 — Inference: OpenRouter as stand-in for self-hosted vLLM; open-weight models only; VAL-GOV-002 revised
**Date**: 2026-06-03 · **By**: Jakob (kickoff, explicit sign-off) · **Status**: Active · **Touches**: Hard Invariant 4, VAL-GOV-002 (material contract change)

Inference is served via **OpenRouter** as a deliberate **cost stand-in** for the self-hosted vLLM the real product runs — instead of renting an expensive cloud GPU for the hackathon. Restricted to **open-weight models that comfortably fit a single 80GB H100**: primary **gpt-oss-120b** (`openai/gpt-oss-120b`), fallback **Llama 3.3 70B Instruct** (`meta-llama/llama-3.3-70b-instruct`). All calls go through an OpenAI-compatible `InferenceProvider` abstraction, so the production swap to sovereign infra is a base-URL + key change with no code change.

**Why / tension held**: OpenRouter is a cloud API call, so VAL-GOV-002 as originally written ("no outbound calls to a closed cloud LLM API… inference served by the self-hosted model") would FAIL. Invariant 4's *spirit* is open-weight + self-hostable + swap-by-config, which we fully preserve; its *letter* ("no cloud API in the demo path") we knowingly relax for cost. **VAL-GOV-002 revised** to prove *open-weight dependence and model portability* (no closed/proprietary model anywhere; swap is config-only) rather than literal on-prem hosting.

**Known risk to manage in the demo**: a judge may note "you're calling a US cloud right now." Honest answer: yes, as a GPU stand-in; only open weights are ever used; here is the one-line config that points it at our own vLLM. Keep that answer ready and unembarrassed.

### D-003 — Add VAL-GOV-003: immutable decision log gets a first-class assertion
**Date**: 2026-06-03 · **By**: Jakob (kickoff sign-off) · **Status**: Active · **Touches**: contract (addition)

The briefing makes the **immutable decision log** the central procurement-clearing proof and "the demoable spine" (propose → log → human-approve), but the original 13-assertion contract had no assertion for it. Added **VAL-GOV-003**: AI suggestions that inform a human action are recorded in an append-only, reproducible log with attribution. Nearly free under the D-001 stack (append-only SQLite table + a viewer). Contract now 14 assertions.

---

## Discovered facts

### F-001 — M1 (Foundation) gate PASSED
**Date**: 2026-06-03 · Fresh-context validator, no blocking issues. All 6 M1 deliverables + 3 GOV groundwork checks PASS. The two load-bearing guarantees were verified by live execution, not just code reading: (1) `decision_log` UPDATE/DELETE actually aborted by DB triggers; (2) `InferenceProvider` actually refused `openai/gpt-4o` before any network call. 7/7 tests pass. Env: Python 3.13.7, deps in `.venv`.

---

## Known / deferred issues

### KI-001 — Live inference path (VAL-GOV-002 network leg) unverified until a key is set
**Date**: 2026-06-03 · **Severity**: low (expected) · **Status**: open
`OPENROUTER_API_KEY` is not set in the dev environment, so no real open-weight model call has been made end-to-end. The *guards* (open-weight allowlist + closed-model refusal) are verified by execution; only the live round-trip is deferred. **Resolve by**: setting the key and running `python -m scripts.smoke_inference` (expect "INFERENCE OK"). Must be green before the M6/M7 governance validation and the demo.
