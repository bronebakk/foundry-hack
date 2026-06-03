# Stream brief — M3 · CTX (pre-meeting context synthesis)

> Paste this whole file to the remote agent as its task. It is self-contained.
> **Branch:** `m3-context` (off `main`). **You own only:** `app/routers/context.py`,
> `app/templates/context/`, `app/static/context.*`. Everything else is frozen — see the
> preamble. Read `CLAUDE.md`, `missions.md`, `decisions.md`, `validation-contract.md` first.

---

## Your goal
A keyworker opens a synthetic young person before a meeting and gets a **concise,
glanceable synthesised brief** of their history — where **every claim traces back to the
specific source record it came from.** The brief is a *proposal*, not a committed record.

This is the "walks in with context instead of cold" surface. It must read like something a
busy worker would actually trust in 60 seconds — and a worker is personally accountable, so
an unexplainable statement is a liability, not a feature.

## Your assertions (definition of done)
- **VAL-CTX-001** — Opening a persona shows a concise brief that synthesises their history
  across the available records into something readable at a glance. Evidence: the brief
  rendered alongside the source records it draws from.
- **VAL-CTX-002** *(anchors Invariant 7 — explainability)* — Every statement in the brief is
  traceable: clicking/hovering a claim reveals the originating record or passage. No claim
  is unattributable. Evidence: a brief claim linked back to its specific source passage.

## What to build
1. **`GET /context/`** — list the personas (the M1 scaffold already does a basic version;
   improve it if you like, but keep it in your files).
2. **`GET /context/{persona_id}`** — the main surface:
   - Show the persona header (name, age, the `synthetic` marker — keep the synthetic framing).
   - **Generate the brief** from `persona.records` via `provider.complete(...)`. Prompt the
     open-weight model to produce a short brief (a few crisp bullets: who they are, where
     they're at, barriers, what's worked, suggested focus for the meeting) **and to cite,
     for each statement, the `id` of the record(s) it is based on.** A reliable approach:
     ask for structured output (e.g. JSON: a list of `{statement, source_record_ids}`), then
     render it yourself so you control the source-linking. Keep the model honest — instruct
     it to only state what the records support, and to attach a source id to every line.
   - **Render each brief statement with its source link**: clicking/hovering a statement
     reveals or scrolls to the source record (which you also render on the page, each with an
     `id` anchor — the M1 `context/persona.html` already renders records with `id="{{ r.id }}"`).
     HTMX or a simple anchor/details disclosure is fine; no heavy JS.
   - Frame the brief as a **proposal** (it's an AI synthesis, not a record of truth). You can
     reuse `_proposal.html` or use the `.proposal` CSS framing — but a brief is *read*
     context, so a full commit/discard form is optional. At minimum it must be visibly an AI
     draft, not presented as settled fact.

## Explainability is the hard part — get it right
VAL-CTX-002 is the point of this stream. Do **not** generate a free-text blob with no
provenance. Every line the worker sees must answer "says who?" by pointing at a record.
If the model can't attribute a statement to a record, don't show that statement.

## Inference details
- Models are open-weight only; just use the defaults (`provider.complete` picks
  `gpt-oss-120b` with a Llama fallback). Don't pass closed model ids — they're refused.
- If `provider.configured` is False (no key), render a clear "inference not configured —
  set OPENROUTER_API_KEY" state instead of a 500, and still show the raw source records so
  the surface is demoable offline.
- Cache or generate-on-load is fine for a demo; keep latency reasonable (small `max_tokens`).

## Tests to add (`tests/test_m3_context.py`)
- The source-linking renderer: given a fake brief with `source_record_ids`, every rendered
  statement carries a link/anchor to an existing record id (no dangling/unattributable lines).
- The `/context/{id}` route returns 200 and contains the synthetic marker and the source records.
- A graceful-degradation test: with inference unavailable, the page still renders records and
  a clear "not configured" notice (no 500).
- Keep all existing tests green.

## Don'ts
- Don't write to the decision log just for viewing a brief (viewing isn't a disposition).
  If you add a "save this brief to the record" action, that's a disposition → use
  `decision_log.record(..., author=config.DEMO_WORKER)` (D-004) with `ProposalType.BRIEF`.
- Don't edit frozen files. Don't merge to `main`.
