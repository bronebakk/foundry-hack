# foundry-hack — Keyworker Force-Multiplier

An **AI augmentation layer for the frontline keyworkers who re-engage NEET young people**. The tool synthesises a young person's history into pre-meeting context, drafts case notes and follow-ups *in the worker's own voice*, and surfaces risk and follow-up signals — **always as editable proposals the human authors and commits, never as autonomous actions or decisions.**

> *"We do the paperwork so you can do the youth work."*

Hackathon build (open-weight, ADA Ventures). Optimised for a credible demo of one core insight — **the AI proposes, the human disposes** — on sovereign-style infrastructure with **synthetic data only**.

## 🚦 Start here (for any agent or contributor)

**Read [`CLAUDE.md`](CLAUDE.md) first — it is the operating manual and its Hard Invariants are non-negotiable.** Then:

| File | What it is |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Operating manual, Hard Invariants, methodology, **Run & Config** (stack + model). |
| [`validation-contract.md`](validation-contract.md) | Definition of done — 14 pass/fail assertions. The contract does not move to match the code. |
| [`missions.md`](missions.md) | The plan: milestones M1–M7, the parallelism graph, **parallel-safety rules**, out-of-scope list, parking lot. |
| [`decisions.md`](decisions.md) | Append-only decision log (D-001…). Log anything you'd be annoyed to re-decide. |
| [`Option-1-…-Briefing.md`](Option-1-Keyworker-Force-Multiplier-Briefing.md) | Product briefing — problem, stakeholders, risks. |

## Hard Invariants (never violate)

1. AI proposes, humans dispose. 2. The system is never the bearer of a denial. 3. Synthetic data only. 4. Open-weight, self-hostable. 5. Authorship integrity. 6. Safeguarding escalation is human-owned. 7. Explainability. *(Full text in `CLAUDE.md`.)*

## Stack

Python 3.11+ · FastAPI + uvicorn · Jinja2 · HTMX · SQLite · Pico.css. Inference via an OpenAI-compatible `InferenceProvider` → **OpenRouter** (a cost stand-in for self-hosted vLLM), **open-weight models only**: `openai/gpt-oss-120b` (primary), `meta-llama/llama-3.3-70b-instruct` (fallback).

```bash
# once the app exists (M1+):
export OPENROUTER_API_KEY=...        # never commit this
uvicorn app.main:app --reload --port 8000   # http://localhost:8000
```

## Working in parallel

Missions **M3, M4, M5 are designed to run concurrently** on separate branches. Before branching, read the **Parallel-safety rules** in [`missions.md`](missions.md): M1/M2 freeze the shared services; each stream owns a disjoint set of files (its own router + template subfolder) and only *calls* the frozen services. Don't edit another stream's files or the frozen ones mid-stream.

---

*All personas and records in this repo are entirely fictional. No real NEET data, no scraped data, no real client material — by design (Invariant 3).*
