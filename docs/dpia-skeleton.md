# Data Protection Impact Assessment (DPIA) — skeleton

*Status: **skeleton for the production product**, not the demo. The running demo processes
**synthetic data only** (Invariant 3), so no DPIA is legally required for it today. This document
exists because a DPIA is **mandatory** for the real product and is the single highest-leverage
artifact for a procurement/safeguarding audience. Framework: UK GDPR + DPA 2018, ICO Children's
Code, Caldicott Principles. Owner: (to appoint) DPO / Caldicott Guardian. Version: draft 0.1.*

> A DPIA is required under **UK GDPR Art 35** because the processing involves **(a) large-scale
> special-category data** (Art 9 — mental health, safeguarding), **(b) vulnerable data subjects**
> (children / young people 16–24), and **(c) innovative technology** (LLM-assisted casework). Any
> one triggers a DPIA; this hits all three.

## 1. Describe the processing

- **What:** an AI augmentation layer for frontline keyworkers re-engaging NEET young people. It
  synthesises case history into a pre-meeting brief, drafts case notes / follow-up messages in the
  worker's voice, and surfaces risk signals — **all as editable proposals a human authors and
  commits** (propose ≠ dispose).
- **Personal data:** identifiers (name, age, contact), education/employment history, casework notes,
  and **Art 9 special-category data**: safeguarding concerns, mental-health indicators, exploitation
  risk.
- **Data subjects:** young people (incl. under-18s); secondarily keyworkers (authorship/audit).
- **Data flow:** source records → (open-weight) inference for drafting/synthesis → human edits and
  disposes → append-only decision log. The model **only generates text; it never persists, sends,
  or decides** (structurally enforced — the project's core control).
- **Volume/scale:** potentially large-scale across a charity/LA caseload → engages the "large-scale"
  Art 35 trigger.

## 2. Necessity & proportionality

- **Lawful basis (Art 6):** likely *public task* / *legitimate interests* for the charity-LA context
  — to confirm per deployment.
- **Art 9 condition:** likely *substantial public interest — safeguarding of children/individuals at
  risk* (DPA 2018 Sch 1). Must be documented **before any real data**, with an Appropriate Policy
  Document.
- **Purpose limitation (Art 5):** the tool does paperwork and surfaces context; it must not be
  repurposed for automated decision-making about a young person (see §4, Art 22).
- **Data minimisation (Art 5(1)(c)):** *gap to close* — generation currently sends all records to the
  model; production should send the minimum necessary per task (see Remediation).

## 3. Consultation

- Data subjects / advocates, frontline keyworkers, the safeguarding lead, and the DPO/Caldicott
  Guardian. The ICO may need consultation if high residual risk remains (Art 36).

## 4. Risks to individuals and mitigations

| Risk | Likelihood/severity | Mitigation (status) |
|---|---|---|
| Automated decision-making with legal/significant effect (Art 22) | High if misused | **Mitigated by design** — propose ≠ dispose; the machine never commits, sends, denies or escalates autonomously (Invariants 1, 2, 6). No solely-automated decisions. |
| Special-category data sent to a third-country processor (LLM) | High (real data) | Sovereign self-hosted open-weight model is the **default** for any non-synthetic deployment; OpenRouter is a synthetic-only cost stand-in (D-002). Allowlist blocks closed models in code. *Make sovereign the enforced default — Remediation.* |
| AI fabrication / mis-attribution feeding a casework decision | Medium | Brief enforces source attribution and **drops unattributable statements** (Invariant 7); decision log records the exact AI proposal + human disposition with tamper-evident provenance (A08 fix). |
| The machine becomes the bearer of a denial to a young person | Medium | Invariant 2 + denial-language guard on outbound drafts; refusals are routed to a named human with a reason and alternative. |
| Unauthorised access to safeguarding records | High (real data) | *Production gap* — needs authenticated sessions, RBAC, row-level caseload scoping, access auditing (audit A01/A09). Demo uses a single identity + HTTP Basic gate. |
| Inaccurate/biased model output affecting vulnerable subjects | Medium | Human-in-the-loop on every output; NIST AI RMF (Measure) bias testing to adopt; explainability built in. |
| Right to erasure vs immutable log (Art 17) | Design tension | Resolved by design — see [`erasure-and-immutability.md`](./erasure-and-immutability.md). |
| Re-identification / excessive retention | Medium | Documented retention schedule + minimisation (to define); synthetic demo carries none. |

## 5. Children's Code (ICO) — specific checks

Default-high privacy, data minimisation, best-interests-of-the-child, transparency appropriate to
age. The **no-denial** and **human-disposition** invariants are genuinely aligned with "best
interests"; reflect this in access-auditing and in age-appropriate transparency to the young person
about how their data is used.

## 6. Caldicott Principles

Justify the purpose (P1); minimum necessary (P4 — see minimisation gap); duty to share can be as
important as the duty to protect (P7 — the human-owned escalation routing embodies this). Appoint a
named **Caldicott Guardian**.

## 7. Outcome & sign-off

- Residual risk: *to assess after the production-path mitigations above.*
- Sign-off: DPO / Caldicott Guardian / SIRO — **before any real personal data is processed.**
- Review: on any material change to data flows, model, or hosting.

*This skeleton is a starting point for the real DPIA, not a completed assessment. It maps the
processing, the lawful bases to confirm, and the risks — several already mitigated by the product's
core design — and points to the production-path work that must precede live deployment.*
