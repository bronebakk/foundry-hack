# Product Briefing — Option 1: Keyworker Force-Multiplier

**An AI augmentation layer for the frontline workers who re-engage NEET young people.**

*Working frame: the AI rides inside an existing trusted, often mandated, human relationship — it does not ask the most detached young people in the country to behave like motivated consumers.*

---

## 1. The problem this addresses

Over one million 16–24-year-olds in the UK are NEET (≈1,012,000, Jan–Mar 2026), the highest level in over a decade. Critically, the composition has shifted: roughly 60% (≈580,000) are now economically *inactive* rather than unemployed — not looking for work, increasingly due to ill health. Mental health conditions and autism account for around two-thirds of NEET young people who cite a health barrier, and the share of NEET young people reporting a work-limiting health condition rose from 26% to 44% between 2015 and 2025.

The Milburn Review interim report (2026) diagnosed the *system* as much as the individuals: responsibility is split across "a bewildering number of organisations," data is not shared, and the architecture itself is the problem. A telling figure: more than half of 16–24s on benefits are still on them 15 years later. The system, in Milburn's words, pays for what people can't do rather than helping them develop.

**The underserving mechanism this product targets.** The people who actually reach disengaged youth — charity keyworkers, supported-employment coaches, FE pastoral staff, Jobcentre work coaches — carry impossible caseloads, drown in admin, and cannot see a young person's history across fragmented agency records. The binding constraint on re-engagement is *caseworker capacity and context*, not a missing app for the young person. A direct-to-individual tool would sit on the same side of the barrier as every careers website that already fails this cohort. This product instead multiplies the reach of the trusted humans who already have access and earned trust.

## 2. The product concept

An AI workbench for the keyworker that:

- **Synthesises** a young person's history across the (single-controller) records the worker can lawfully see, so the worker walks into a meeting with context instead of cold.
- **Drafts** case notes, follow-up messages, referral letters, and reports in the worker's own voice — every output an editable draft the worker authors and owns.
- **Surfaces** follow-ups, deadlines, and risk indicators — never acting on them autonomously, always routing through a human-owned decision.
- **Reduces** the administrative load that currently crowds out the relational work these professionals trained for and value.

The honest one-line value proposition: *we do the paperwork so you can do the youth work.*

## 3. Fit with the Ada Ventures framework

- **Primary fit — Area 3, Frontline Worker AI.** The framework notes deskless/frontline workers are most of the global workforce yet chronically under-equipped (only ~a fifth have the tech they need). This product reframes "frontline worker" as the keyworker who reaches the NEET cohort — exactly the shift-level support and admin-collapsing intelligence the thesis describes.
- **Secondary fit — Area 6, Guardrails & Safety.** The human-in-the-loop and decision-log architecture is itself a guardrail story, and a procurement enabler.
- **Inclusive alpha.** Returns accrue *by* widening access to re-engagement support for the hardest-to-reach — the thesis's core test. The impact is real but *indirect* (mediated through the worker), which is a narrative challenge to manage, not a weakness.

## 4. Product requirements by stakeholder

### Angle 1 — The keyworker (primary user)

These are low-paid, low-status, vocation-driven roles. People enter them believing in a relational craft. Three forces shape every requirement:

1. **Professional pride.** Any tool implying the relationship reduces to data fields attacks their identity.
2. **Job insecurity.** After years of austerity, an "efficiency tool" can read as the business case for making them redundant.
3. **Earned skepticism of IT.** They've inherited a graveyard of failed government case-management systems.

**Requirements:**

- **Surface, never decide.** Every output is an editable draft the worker authors and commits. The AI never writes the record or makes the recommendation autonomously.
- **Authorship integrity.** Drafted notes preserve the worker's own voice and phrasing. Pride is a feature, not a nicety.
- **Admin offload as the real ROI.** The value that happens to valorise the relational work they resent losing to bureaucracy. Lean on this alignment — it is rare.
- **Explainability is a safeguarding requirement.** The worker is *personally accountable*. An unexplainable flag is a professional liability, not a feature. Every surfaced signal must be traceable to its source.
- **Designed escalation path.** The tool will surface risk indicators (self-harm, abuse, exploitation). It must neither act autonomously nor bury the signal — a human-owned, designed escalation is core, not an edge case.

### Angle 2 — Procurement (LA commissioner / charity COO / DWP / FE governance)

The hardest cell. The data is special-category under UK GDPR: mental health, safeguarding, often criminal-justice involvement, children's data. A DPIA is mandatory; you operate as a *processor* under the authority's controllership; the information-governance review is where deals die.

**Privacy & governance:**

- **Self-hostable open-weight models are a commercial weapon.** A model running on UK/EEA-sovereign (or the authority's own) infrastructure kills the otherwise-fatal objection: "our citizens' safeguarding notes are being posted to a US LLM API." This is where containerised, self-hosted deployment competence becomes the procurement-clearing advantage rather than a constraint.
- **Immutable decision log.** Every AI suggestion that informed a decision logged and reproducible for complaints, tribunals, and inspection. (This is the governance-envelope pattern: propose → log → human-approve.)
- **Single-controller scope in v1.** The cross-agency data-sharing Milburn flagged is a genuine legal minefield — the lawful basis for sharing an individual's data across agencies is hard. v1 makes *manual* cross-referencing easier within one controller's data; it does not promise magic data fusion.
- **Public Sector Equality Duty.** If flags correlate with ethnicity or disability, that's a legal and reputational landmine. Demonstrable bias testing is required, not a claim.

**Capex / opex & business model:**

- Public sector is opex-preferring, capex-averse, framework-bound (G-Cloud / DPS), with 6–18 month sales cycles. Budget for this as a startup reality.
- Pricing: per-seat or per-caseload annual SaaS. Land in one service, expand across the authority.
- **The wrong-pocket problem is the central commercial obstacle.** The money saved is *lifetime fiscal cost* (Treasury, decades out — the scarring/earnings data from the Resolution Foundation sizes it). The budget you're paid from is one LA service this year. Saver ≠ buyer. Pitch the buyer's *actual* line item (caseworker time; the cost of an unfilled re-engagement target), not the seductive macro number.
- Outcomes-based / payment-by-results pricing aligns incentives and fits the impact story — but it's cash-flow death at seed stage (long attribution lag, disputes). A later option, not the go-to-market.

### Angle 3 — The NEET young person (often a secondhand beneficiary)

In the pure back-office case the young person may never touch the software; they experience it through a better-prepared, more-present worker. Requirements split accordingly.

**If non-facing:** the tool must not depersonalise the encounter. The worker should not be reading a screen mid-conversation; the young person must not feel *processed*.

**If there is any young-person-facing surface (shared plan, opportunities feed):**

- **The system is never the bearer of a denial.** If something can't happen, a *human* delivers it, with a reason and an alternative. The AI surfaces options; the human owns refusals. ("No computer says no.")
- **Surveillance smell is fatal.** These are people with low — often justifiably earned — institutional trust (care-experienced, justice-adjacent, sanctioned by the benefits system). "Nothing about me without me" must be visible and real.
- **Reversibility.** They can disengage and return without penalty.
- **They are blocked, not lazy.** The King's College twin study found NEET youth reported *higher* work commitment and more job-searching than peers. Any "motivational" framing that treats the deficit as effort rather than barriers will be correctly resented.
- **Access floor.** Cheap Android, patchy data, voice- and plain-language-tolerant.

## 5. The cross-cutting design principle

The two hardest stakeholder instincts — *augmentation not replacement* (keyworker pride) and *no computer says no* (young-person autonomy) — are the **same design primitive seen from opposite ends: the AI proposes, humans dispose.** Build that primitive once, correctly, and it satisfies the worker at one end of the interaction and the young person at the other. Violate it anywhere and you lose one or both. It belongs at the centre of the architecture.

## 6. Key risks and tensions to hold consciously

- **Contradictory buyer narratives.** The augmentation story you tell the keyworker ("this frees you to do real youth work") and the efficiency story you tell procurement ("do more with fewer staff-hours") are in direct conflict — to the worker, the second sounds like "we're planning to cut you." You will tell two contradictory stories to two buyers in the same building. Decide deliberately how you hold that; getting caught undermines the trust both depend on.
- **The equity paradox.** The more capable and resource-hungry the build, the more it risks excluding the target context (data-residency for the IG review, device/access floor for any facing surface). Self-hostable open-weight models plus a low-spec client resolve it — and align with an open-weight build constraint as genuinely correct architecture, not a compromise.
- **Indirect impact attribution.** Because the benefit is mediated through the worker, the impact metric is messier than a clean consumer number. Define the measurable proxy early (caseload capacity, contact frequency, time-to-re-engagement) so the impact story is defensible.
- **Safeguarding liability.** Surfacing risk indicators creates duty-of-care exposure. The escalation design is a first-class product surface and a legal one.

## 7. Build / MVP considerations (hackathon)

- The "AI proposes, human disposes" primitive plus an immutable decision log is the demoable spine and the most credible technical narrative for an open-weight audience.
- A self-hosted open-weight model on containerised infrastructure is the right MVP architecture and doubles as the procurement-clearing proof point.
- Strongest demo flow is the three-stakeholder arc: worker walks in with AI-synthesised context → drafts a note in their own voice → a risk signal surfaces and routes to a human-owned escalation → nothing is ever committed or denied by the machine.

---

*Sources informing this briefing: Milburn Review interim report (2026); Health Foundation analysis (2025–26); Resolution Foundation; Education Policy Institute; House of Commons Library; King's College London E-Risk twin study. Figures are early-2026 estimates and move quarter to quarter.*
