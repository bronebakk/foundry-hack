# Deployment security checklist

*A checked gate for any deployment beyond a local run. The demo is synthetic-data only, but a
**public** deployment must still not be open to the world. Items marked 🔴 are blocking for a public
demo; 🟠 are required before any **real personal data**.*

## Public demo deployment (synthetic data)

- 🔴 **`DEMO_AUTH=1`** is set — the HTTP Basic gate is **off by default**; a public bind without it
  leaves the app open. Confirm: an un-credentialed request returns `401`.
- 🔴 **`demo_auth.json` present** (mode `600`, gitignored), with the intended users as PBKDF2 hashes.
  The gate **fails closed** if it is missing, so verify logins actually work after deploy.
- 🔴 **TLS terminated in front** of the app. HTTP Basic sends reversible base64 credentials every
  request; never expose Basic over plain HTTP on an untrusted network. HSTS is already sent (active
  once behind TLS).
- 🔴 **Not `--reload`.** Run a production server (no `--reload`, no debug). Tracebacks must not leak
  (FastAPI `debug` is unset — keep it so).
- 🟢 **Security headers** verified present (CSP, `frame-ancestors 'none'`, `nosniff`,
  `Referrer-Policy: no-referrer`) — automatic via middleware; confirm with `curl -I`.
- 🟢 **Front-end is self-hosted** (no CDN `<script>`/`<link>`) — already true; keep it for the
  sovereign posture.
- 🟢 **`OPENROUTER_API_KEY` via env only** — never committed; rotate if exposed.
- 🟢 **`PROPOSAL_SIGNING_KEY`** set if running **multiple workers** (so A08 provenance signatures
  verify across workers). Single worker may omit it.
- 🟢 **Rate limit** appropriate for expected traffic (`app/ratelimit.py` defaults: 30 generations /
  min / client).
- 🟢 **Monitor `app.security` logs** for repeated `failed login` / `401`s.

## Before any real personal data (production)

- 🟠 **Lawful basis + Art 9 condition** documented; Appropriate Policy Document in place.
- 🟠 **DPIA completed and signed off** (DPO / Caldicott Guardian / SIRO) — see
  [`dpia-skeleton.md`](./dpia-skeleton.md).
- 🟠 **Sovereign inference is the default** — `OPENROUTER_BASE_URL` points at a self-hosted vLLM, not
  a third-country API; verify no real record can be sent off-prem.
- 🟠 **Real authn/z** — authenticated sessions, RBAC (keyworker / safeguarding lead / admin),
  row-level caseload scoping. Replace the single `DEMO_WORKER` identity.
- 🟠 **Encryption at rest + KMS**, with the content/decision split and crypto-shredding for erasure —
  see [`erasure-and-immutability.md`](./erasure-and-immutability.md).
- 🟠 **Access auditing** (who *viewed* which young person), distinct from the governance log.
- 🟠 **Data minimisation** — send only the records a given draft needs to the model.
- 🟠 **Dependency/CVE scanning** (Dependabot / `pip-audit`) and a hash-pinned lockfile.
- 🟠 **MFA** for the safeguarding-lead role; anti-bruteforce lockout.

## Quick verification commands

```bash
# auth gate on (expect 401, then 200 with a valid login)
curl -s -o /dev/null -w "%{http_code}\n" https://HOST/
curl -s -o /dev/null -w "%{http_code}\n" -u user:pass https://HOST/

# security headers present
curl -sI -u user:pass https://HOST/ | grep -iE "content-security-policy|x-frame-options|referrer-policy|x-content-type-options"

# cross-origin write refused (expect 403)
curl -s -o /dev/null -w "%{http_code}\n" -u user:pass -H "Origin: http://evil.example" \
  -X POST https://HOST/drafting/leah-sumner/generate -d proposal_type=case_note
```
