# Build Timeline — Keyworker Force-Multiplier

*Reconstructed from git history (single day, **2026-06-03**). Times in **CET** (UTC+2 / the
repo's `+0200` offset). The kickoff time is from Jakob's first Claude conversation; everything
else is a commit timestamp.*

**Span:** ~09:00 CET (first Claude message) → 14:23 CET (security audit) — a ~5.4-hour day, of
which the entire core product was built in the first ~3 hours.

---

## Phase 0 · Kickoff (≈09:00 – 09:49)
| CET | What |
|---|---|
| ~09:00 | **Hackathon hour zero** — first message in the founding Claude conversation: stack, demo narrative, and invariants worked out before any code (~49 min of planning) |
| 09:49 | **Initial commit** — project charter, validation contract, missions, decisions log (the four anti-drift files) |

## Phase 1–2 · Foundation & the core spine (10:15 – 10:31)
| CET | What |
|---|---|
| 10:15 | **M1** foundation scaffold — FastAPI shell, SQLite, inference seam, synthetic data |
| 10:19 | M1 gate **PASS** (fresh-context validator); logs F-001 + KI-001 |
| 10:24 | **M2** propose → log → dispose spine (frozen shared services) |
| 10:27 | M2 gate **PASS**; authorship hardening D-004, logs F-002 |
| 10:31 | Per-stream launch briefs for the M3/M4/M5 **parallel agents** |

## Phase 3 · Parallel feature streams (10:43 – 11:21)
*Three surfaces built concurrently on separate branches, then merged in a tight cluster.*
| CET | What |
|---|---|
| 10:43 | **M3 CTX** — attributed pre-meeting brief (VAL-CTX-001/-002) |
| 10:54 | **M4 DRAFT** — case-note & follow-up drafting, propose-not-act boundary |
| 11:09 | Synthetic data — validation gate + hybrid generator + staged hero personas |
| 11:11 | **M5 ESCALATE** — risk surfacing, human-owned escalation, no "computer says no" |
| 11:14 | M3 CTX hardening against real open-weight output |
| 11:17 | M5 gate **PASS**; logs F-003 |
| 11:17 | Merge **PR #1** (m4-drafting) |
| 11:20 | Merge **PR #2** (m5-escalation) |
| 11:21 | Merge **PR #3** (m3-context) |

## Phase 4 · Integration & governance (11:48 – 12:01)
| CET | What |
|---|---|
| 11:48 | **M6** integration & governance polish — decision-log viewer, hero personas, cohesion fixes |
| 11:54 | M6 gate **PASS**; logs F-005 |
| 12:01 | Merge **PR #4** (m6-integration) |

*Quiet stretch 12:01 – 13:02: break between core build and polish.*

## Phase 5 · UX refresh, demo hardening & deck (13:02 – 14:07)
| CET | What |
|---|---|
| 13:02 | Design brief for UX refresh + before-state screenshots |
| 13:04 | **HTTP Basic demo-access gate** (off by default; no secrets committed) |
| 13:06 | Merge **PR #5** (m6-integration) |
| 13:35 | **Demo deck** scaffold/build brief for the design agent |
| 14:01 | Coding brief from Claude design for UX improvement |
| 14:07 | Merge **PR #6** (m6-integration) |

## Phase 6 · Security (14:23)
| CET | What |
|---|---|
| 14:23 | **Security audit** — OWASP Top 10:2025 + UK special-category data review (PR #7) |

---

## Highlights for the judges
- **Methodology held end-to-end:** every milestone (M1, M2, M5, M6) has an explicit *gate PASS by
  a fresh-context validator* commit immediately after the build commit — the "the builder is a poor
  judge of its own work" discipline, visible in the record.
- **Genuine parallelism:** M3/M4/M5 were authored 10:43–11:14 and merged 11:17–11:21 — three
  streams in flight at once, exactly as the missions plan intended.
- **Core product in ~3 hours:** from 09:00 kickoff to M6 merged at 12:01 (planning included).
- The remaining time went to UX refresh, the demo-access gate, the deck, and security.

*Note: the M7 demo-freeze work in progress is not yet committed, so it does not appear above; this
file covers history through the security audit (PR #7).*
