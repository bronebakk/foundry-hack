# Right to erasure vs the immutable decision log — design note

*Resolves the tension the security audit flagged (A06 / UK GDPR Art 17). Production design;
the synthetic demo has no real personal data to erase. Date: 2026-06-03.*

## The tension

Two things that are both load-bearing appear to conflict:

- **The append-only decision log (Invariant 1, VAL-GOV-003).** Its credibility *is* that it cannot
  be silently altered — enforced at the DB layer (UPDATE/DELETE triggers) and the service layer (no
  mutation API), and now with tamper-evident proposal provenance (A08). This is the procurement
  centrepiece.
- **The right to erasure (UK GDPR Art 17).** A real young person can request erasure of their
  personal data. An immutable store that holds special-category content would be a compliance
  liability.

If the log stores special-category *content* immutably, erasure and immutability collide head-on.

## The resolution: separate the immutable *decision* from the erasable *content*

The governance value lives in the **fact and shape of each decision** — that on a date, an AI
proposed X, a named human disposed of it as Y. That metadata must be immutable. The **personal-data
content** inside it (the proposal text, the worker's note, the young person's identifiers) need not
live in the immutable store at all.

Design — **crypto-shredding + content/decision split:**

1. **Immutable decision record** (append-only, retained): timestamp, surface, proposal type,
   disposition, **human author of record**, open-weight model id, and *references* (a content id +
   the provenance signature) — but **no special-category free text**.
2. **Erasable content store** (mutable, encrypted at rest, per-subject keys): the actual
   `proposal_text` / `final_text` / record content, encrypted with a **per-subject key**.
3. **Erasure = destroy the subject's key (crypto-shredding).** The ciphertext becomes
   irrecoverable, satisfying Art 17, while the immutable decision record — now pointing at
   unrecoverable content — remains intact and still proves *that a governed decision happened*, its
   shape, and its human author. The audit trail's integrity survives; the personal data is gone.

This keeps both guarantees: **the decision log stays append-only and provably un-tampered; the
content is genuinely erasable.**

## What changes vs today

The demo keeps everything in one append-only table (fine — synthetic data, nothing to erase). The
production change is structural, not a rewrite of the model:

- Split `decision_log` into an immutable `decision` table (metadata + content-ref + signature) and
  an encrypted `content` store keyed per subject.
- Add key management (per-subject keys, a KMS) and a documented **retention schedule** (how long
  decisions are kept; when content is erased absent a request).
- Erasure endpoint = key destruction + tombstone, recorded itself as a governed event.

## Caveats and residual considerations

- **Lawful-basis exemptions:** some safeguarding records have retention obligations or legal-claim
  exemptions to Art 17; the retention schedule must encode these per record type (a destroyed key is
  irreversible, so policy must precede erasure).
- **Backups:** crypto-shredding must cover backups too (destroy keys, not hunt ciphertext in
  archives) — a benefit of the key-based approach.
- **Signatures:** the A08 provenance signature is over content; once content is shredded the
  signature is retained as an integrity tombstone proving the decision's shape, not the (now-erased)
  text.

*Decision: adopt the content/decision split with crypto-shredding for the production product;
log this as a standing design constraint. The demo stays single-table by design.*
