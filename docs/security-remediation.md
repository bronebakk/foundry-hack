# Security remediation — status against the audit

*Companion to [`security-audit.md`](./security-audit.md). Tracks what the security-fixes pass
addressed. Date: 2026-06-03.*

The audit was explicit that **none of its findings is a live exploit against the synthetic-data
demo** — they are the gap between "a demo that tells the governance story" and "an architecture
that survives a procurement security review." This pass closed the demo-path code gaps and wrote
the production-path design artifacts. Severities are the audit's (production context).

## Fixed in code (this pass)

| Finding | Severity | What changed | Verified by |
|---|---|---|---|
| **A08 Data integrity** — forgeable AI-proposal text & model attribution | HIGH | Provenance (`proposal_text`, `model`) is HMAC-signed at generation (`app/services/integrity.py`) and re-verified at every disposition (`/dispose`, `/escalate`, `/refer`). A tampered proposal or a forged (even closed-model) attribution is rejected before it can enter the append-only log. The human still supplies only `final_text`; the author of record stays server-side. | `tests/test_security.py::test_a08_*` |
| **A01 CSRF** — cross-site writes via auto-attached Basic auth | HIGH | `app/security.py` rejects state-changing requests whose `Origin`/`Referer` is cross-origin. | `test_cross_origin_write_is_refused` |
| **A02 Missing security headers** | MEDIUM | Middleware sets CSP (`script-src 'self'`, `frame-ancestors 'none'`), `X-Frame-Options`, `nosniff`, `Referrer-Policy: no-referrer`, HSTS. | `test_security_headers_present_on_every_response` |
| **A03 Supply chain (CDN, no SRI)** | MEDIUM | Already resolved in the UX work: HTMX and the stylesheet are **self-hosted** (`app/static/vendor`, `app/static/fonts`); Pico/CDN removed. No external front-end dependency — also strengthens the sovereign story (Invariant 4). | n/a (no CDN `<script>`/`<link>` remain) |
| **A05 / LLM01 Prompt injection** | MEDIUM | Untrusted record text is wrapped in an explicit instruction/data fence in the drafting and escalation prompts (`app/services/safety.py::fence`), with a system instruction to ignore embedded instructions. | `test_untrusted_record_text_is_fenced_in_the_prompt` |
| **LLM02 Insecure output / Invariant 2** | MEDIUM | Denial-language guard flags any outbound draft that reads like a refusal, so the worker is warned before sending (never blocks — the human disposes). | `test_denial_guard_flags_an_outbound_draft` |
| **A07 Username timing oracle** | MEDIUM | Unknown usernames now run an equal PBKDF2 against a constant salt, so a valid username is not measurably faster. | `test_unknown_username_does_equal_pbkdf2_work` |
| **A06 / LLM10 Unbounded LLM consumption** | MEDIUM (part) | Per-client fixed-window rate limit on generation (`app/ratelimit.py`). | `test_generate_is_rate_limited` |
| **A09 No security event logging** | MEDIUM (part) | Structured `app.security` log for auth outcomes (failed logins, malformed/missing credentials), distinct from the governance log; never logs passwords or record content. | `test_auth_failure_is_logged` |

All existing behaviour and invariants preserved; **90 tests pass**.

## Addressed by documentation (this pass)

| Finding | Artifact |
|---|---|
| **A06 / UK GDPR — no DPIA** | [`dpia-skeleton.md`](./dpia-skeleton.md) — the highest-leverage procurement artifact. |
| **A06 / Art 17 — erasure vs immutability** | [`erasure-and-immutability.md`](./erasure-and-immutability.md) — the design resolution. |
| **A07 / A04 — `DEMO_AUTH=1` + TLS launch gate; no `--reload`** | [`security-checklist.md`](./security-checklist.md) — a checked deployment gate. |

## Deliberately out of scope (production-path; not demo-appropriate)

These are real and tracked, but are product features, not demo hardening. Building them now would
be gold-plating a synthetic-data demo:

- **A01 full authz** — authenticated sessions, RBAC (keyworker / safeguarding lead / admin),
  row-level caseload scoping. The demo's single `DEMO_WORKER` identity is honest about its scope.
- **A04 encryption at rest + KMS** — needed once real special-category data is stored; the demo's
  SQLite holds only synthetic data.
- **A09 access auditing** (who *viewed* which young person) — a production control (DSPT / Caldicott);
  needs a real identity model first.
- **LLM06 / international transfer** — make sovereign vLLM the *default* endpoint for any
  non-synthetic deployment; covered in the DPIA and `decisions.md` D-002.

## New environment knobs

- `PROPOSAL_SIGNING_KEY` — set to a stable secret for multi-worker deployments so provenance
  signatures survive across workers/restarts. Unset → a per-process key (fine for the single-worker
  demo; in-flight drafts simply re-generate after a restart).
- `DEMO_AUTH=1` — enables the HTTP Basic gate (off by default). **Required** for any public
  deployment — see the launch checklist.
