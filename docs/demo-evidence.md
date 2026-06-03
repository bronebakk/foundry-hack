# M7 Demo-lock evidence pack

*Final fresh-context validation gate for the demo, run against `main` with live open-weight
inference (`openai/gpt-oss-120b`). The validator did not see implementation history; it exercised
the running app as a skeptical user and recorded evidence per assertion. Date: 2026-06-03.*

**Result: GATE PASS** — all 13 `VAL-*` assertions across 6 areas pass. Test suite: **90 passed, 0
failed**. The three-stakeholder narrative (caseload → context brief with attributed sources →
editable draft in the worker's voice → risk surfaced not acted on → human escalates to the
human-owned inbox → immutable governance log showing the full AI→human chain) ran clean end to end.

---

## CTX — Pre-meeting context synthesis
- **VAL-CTX-001 — PASS.** `/context/amara-okafor` (live) renders a `⬩ Brief` proposal frame
  "drafted by open-weight model (openai/gpt-oss-120b)" with attributed bullets; framed
  "Pre-meeting synthesis — not a record of truth". Log count unchanged (1→1) — generation writes
  nothing.
- **VAL-CTX-002 — PASS.** Every statement carries a "Says who?" link to a real record; cited ids
  (`amara-r1..r4`) all resolve to on-page anchors; `attributable_statements()` drops any
  unattributable statement in code before render. Leah's brief: 8 source links, all resolved.

## DRAFT — Drafting & authorship
- **VAL-DRAFT-001 — PASS.** `/drafting/kofi-mensah/generate` returns `data-uncommitted="true"`,
  "Case note · not committed, nothing sent", an editable `final_text` textarea. Log unchanged (1→1).
- **VAL-DRAFT-002 — PASS.** After a worker edit + commit, log entry shows `author='Sam Ellison
  (keyworker)'` (server-side), `model='openai/gpt-oss-120b'` (separate field), `final_text` = the
  worker's edited words ≠ the AI's `proposal_text`. UI: "this is your note… the AI was the drafting
  assistant, never the author of record."

## PROPOSE — The propose-not-act boundary
- **VAL-PROPOSE-001 — PASS.** Viewing context and generating a draft both leave the log count
  unchanged; only `/dispose` increments it (1→2). Code-path check: `generate_draft()` makes no
  `decision_log.record()` call; `context.py` does not import `decision_log`.
- **VAL-PROPOSE-002 — PASS.** A follow-up renders with a `send` button; no `send` entry exists
  until an explicit human send disposition.
- **VAL-PROPOSE-003 — PASS.** Drafting, escalation and context surfaces all frame output as an
  uncommitted proposal with a visible discard/"Not now"; footer "The AI proposes; the worker
  disposes."

## DENY — No "computer says no"
- **VAL-DENY-001 — PASS.** `/escalation/marcus-fielding`: "The system isn't telling Marcus Fielding
  'no'. It can't — and it won't." Real alternatives shown from his records (Advanced Learner Loan,
  bursary, apprenticeship) + a `/refer` human-delivery path. Adversarial grep for machine-refusal
  phrasing across templates: zero hits.

## ESCALATE — Safeguarding
- **VAL-ESCALATE-001 — PASS.** `/escalation/leah-sumner` surfaces the CSE/CCE signal traceable to
  `leah-r2` under "No automatic action has been or will be taken… You decide what happens next.";
  viewing leaves the log count unchanged (2→2).
- **VAL-ESCALATE-002 — PASS.** A human escalation (POST with the server-signed `proposal_sig`)
  writes one entry and lands in the human-owned inbox ("a person decides and resolves this — the
  system will not"; "the machine marks nothing 'resolved'").

## GOV — Governance & demo credibility
- **VAL-GOV-001 — PASS.** Persistent synthetic banner on every page; `tag-synthetic` on every
  persona; all 6 persona JSON carry `synthetic: true` + demo note.
- **VAL-GOV-002 — PASS.** Only `openai/gpt-oss-120b` / `meta-llama/llama-3.3-70b-instruct` in the
  allowlist; grep for `gpt-4`/`claude`/`gemini`/`davinci` in `app/` and templates → zero hits;
  `_guard_open_weight()` refuses a non-allowlisted model before any network call; single swap point
  (`OPENROUTER_BASE_URL`). Live call to `gpt-oss-120b` succeeded.
- **VAL-GOV-003 — PASS.** The decision log shows each entry as AI proposal → human disposition →
  worker of record. Append-only proven: DB triggers reject UPDATE/DELETE; HTTP PUT/DELETE → 405; no
  edit/delete route exists. Adversarial: a forged `proposal_text` with a valid signature is rejected
  ("couldn't be verified", count unchanged); a spoofed `author` field is ignored (stored author =
  `Sam Ellison (keyworker)`).

---

## Notes carried forward (non-blocking)
- **Test DB isolation** — fixed at demo-lock: `test_m1_foundation.py` now isolates its DB, so
  running the suite no longer seeds a `test-worker` row into the real `foundry.db`. (A full suite run
  now leaves 0 real-DB entries.)
- **Single-worker signing key** — `integrity.py` uses a per-process key unless
  `PROPOSAL_SIGNING_KEY` is set; fine for the single-process demo (documented in
  `security-checklist.md`).

**GATE: PASS — the demo is locked.**
