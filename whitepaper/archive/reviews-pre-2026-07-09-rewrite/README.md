# Pre-Rewrite Whitepaper Reviews (superseded)

These documents review the **pre-2026-07-09 whitepaper**, which no longer exists. They are kept for
provenance, not as open work. The paper they audit was replaced by the 2026-07-09 fresh rewrite (dp:
"the paper has drifted too far and needs a fresh rewrite"); its sections are preserved next door at
`../sections-2026-07-09-pre-rewrite/`.

| Document | Date | Status |
|---|---|---|
| `WHITEPAPER_DISCREPANCIES.md` | 2025-11-12 | Superseded |
| `WHITEPAPER_REVIEW_SUMMARY.md` | 2025-11-12 | Superseded |
| `WHITEPAPER_REVIEW_2026-01-26.json` | 2026-01-26 | Superseded |

## Why they were moved out of `whitepaper/`

They cite section paths that are gone (`03-part1-defining-web4/`, `08-part6-blockchain-typology/`,
`09-part7-implementation-details/`), and they close on:

> **Awaiting User Decision On:** 1. Whitepaper purpose and audience — 2. How to handle vision vs
> implementation gap …

Those questions were **already answered** by the 07-09 rewrite directive, which resolved the scope
question (the paper is now a scoped technical introduction to the canonical standard) and cut the
vision/implementation-gap material as drift. Sitting at the top level of `whitepaper/`, they read as
*live open items* against the current paper and invite a future agent to act on superseded
instructions — reintroducing exactly the drift the rewrite removed.

**Still live, and deliberately NOT archived:** `../../WHITEPAPER_STRUCTURE_REVIEW_2026-07-09.md` — the
posture review that *drove* the current structure. It remains standing guidance (cited by
`log/CHANGELOG.md` and by the Posture Invariants in `PUBLISHER_CONTEXT.md` §2).

*Archived 2026-07-14 by the Publisher pass. Nothing was deleted; `git mv` only.*
