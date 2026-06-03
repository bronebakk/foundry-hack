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

### D-004 — Authorship enforced at the service layer; streams must supply server-side worker identity
**Date**: 2026-06-03 · **By**: M2 build + validator finding · **Status**: Active · **Touches**: Invariant 5, all streams (M3/M4/M5)

The M2 validator found that `decision_log.record(author=...)` originally stored whatever author string it was handed — worker-authorship was caller convention, not a service guarantee. Hardened before freezing: `decision_log.record` now rejects an empty author and rejects any author that is a model id in `ALLOWED_MODELS` (the AI can never be the author of record). The service guarantees *not-the-AI*; it cannot know *which* human — so:

**Standing rule for M3/M4/M5:** when wiring a disposition endpoint, set `author` server-side from `config.DEMO_WORKER` (or a real session identity in production). **Never** take the author from a client-supplied form field — hidden fields can be spoofed. The shared `_proposal.html` partial deliberately carries no author field; inject it in the router.

### D-005 — Synthetic data: hybrid generator + an automated synthetic-data gate; new hero personas staged for M6
**Date**: 2026-06-03 · **By**: Jakob (chose hybrid / separate-dirs / opt-in LLM) · **Status**: Active · **Touches**: Invariant 3, Invariant 7, VAL-GOV-001, demo data for all surfaces

We have no real users/data, so demo + test data is synthetic by construction. Approach (built on branch `m3-context`, in new files only — no frozen files touched):
- **Gate** `scripts/validate_personas.py` — every persona must pass: `synthetic: true` required (Invariant 3), risk flags must carry `risk_category` + `risk_rationale` (Invariant 7), ids URL/`#anchor`-safe (protects VAL-CTX-002 source-linking), ISO dates, non-empty text. Also a governance demo asset.
- **Generator** `scripts/generate_personas.py` — hybrid: deterministic+seedable by default (no key; bulk + a fixed edge-case set), open-weight LLM opt-in (`--llm`, gpt-oss-120b, gated before write — Invariant 4). Committed deterministic fixtures live in `tests/fixtures/personas/`.
- **New hero personas STAGED in `app/data/personas_staged/`**, NOT added to the live `app/data/personas/` yet. Reason: that dir is frozen/shared and `test_m1_foundation.py` asserts exactly 3 personas — adding now would break the live M3/M4/M5 streams. **Coordination point: merge staged → live at M6 and update the count assertion then.** Staged set fills demo gaps: `noah-bennett` (DRAFT — meeting just held), `marcus-fielding` (DENY — option unavailable, routed to a human), `ivy-castellano` (ESCALATE — wellbeing/self-harm cue, distinct from Leah's exploitation example).

### D-006 — OpenRouter key sourced from gitignored `orkey.txt`; never committed
**Date**: 2026-06-03 · **By**: Jakob (provided key in `orkey.txt`) · **Status**: Active · **Touches**: D-002, secret hygiene

The key lives in `orkey.txt` at the repo root, added to `.gitignore` (alongside the existing `.env`/`*.key` rules) so it is never committed. App + tooling read `OPENROUTER_API_KEY` from the environment; `generate_personas.py` falls back to reading `orkey.txt` (before importing the provider, which captures the key at construction). For the running app: `export OPENROUTER_API_KEY="$(cat orkey.txt)"`. Config stays frozen — the key is supplied via env, swap to sovereign infra remains a base-URL+key change (D-002).

---

## Discovered facts

### F-002 — M2 (propose→log→dispose spine) gate PASSED-WITH-NOTES
**Date**: 2026-06-03 · Fresh-context validator, adversarial pass. Spine sound: constructing a Proposal writes nothing (count stays 0); the inference layer has no persistence path (AST-verified — no `sqlite3`/`app.db`/`decision_log` import, no write-SQL); `record()` is the sole INSERT site in `app/`; append-only holds at both service (no mutation API) and DB (triggers reject UPDATE/DELETE) layers; original proposal preserved alongside human-edited final text. No live path commits or sends without a human action. The one note (author trusted from caller) was resolved in-milestone → see D-004. 15/15 tests pass.

### F-001 — M1 (Foundation) gate PASSED
**Date**: 2026-06-03 · Fresh-context validator, no blocking issues. All 6 M1 deliverables + 3 GOV groundwork checks PASS. The two load-bearing guarantees were verified by live execution, not just code reading: (1) `decision_log` UPDATE/DELETE actually aborted by DB triggers; (2) `InferenceProvider` actually refused `openai/gpt-4o` before any network call. 7/7 tests pass. Env: Python 3.13.7, deps in `.venv`.

---

## Known / deferred issues

### KI-001 — Live inference path (VAL-GOV-002 network leg) unverified until a key is set
**Date**: 2026-06-03 · **Severity**: low (expected) · **Status**: RESOLVED 2026-06-03
~~`OPENROUTER_API_KEY` is not set in the dev environment, so no real open-weight model call has been made end-to-end.~~ **Resolved**: key supplied (D-006); `python -m scripts.smoke_inference` returned `[OK] Model openai/gpt-oss-120b replied: 'INFERENCE OK'`. Live open-weight round-trip confirmed; the M3 CTX brief and the LLM generator mode both exercise it. Guards (open-weight allowlist + closed-model refusal) remain verified by execution.
