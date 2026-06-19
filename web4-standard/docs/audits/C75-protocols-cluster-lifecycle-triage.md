# C75 — `protocols/` Cluster Lifecycle Triage

**Type**: Read-only cluster triage (NOT a per-finding audit, NOT a remediation)
**Date**: 2026-06-19
**Author**: autonomous web4 session (legion slot `060047`)
**Scope**: All 8 documents in `web4-standard/protocols/`
**Status**: ADVISORY — every supersede/maintain call below is an **operator decision presented with evidence**, not a settled outcome. Nothing in this document edits, deprecates, or supersedes any file.

---

## 0. Why this document exists

The C74 audit of `protocols/web4-lct.md` (PR #363, `d9b856a9`) surfaced flagship design-Q **D0**: is `protocols/web4-lct.md` a maintained sister-doc, or is it superseded by the canonical `core-spec/LCT-linked-context-token.md`? C74's carry GATED the C75 remediation on that decision and noted the `protocols/` cluster holds **6 more never-audited frozen sister-docs**, recommending the operator make **one cluster lifecycle decision** rather than discovering the same flagship 6 more times across 6 sequential deep audits.

This triage is the evidence packet for that single decision. It does NOT make the call. It partitions the cluster and shows the data behind each partition, so D0 can be resolved in its proper cluster context instead of as an isolated one-doc question.

## 1. Counting method (binding — reproducible)

Two prior independent greps produced different "inbound ref" counts (e.g. web4-lct: 4 vs 7). To make this artifact self-verifying, all counts below use this exact method:

```
grep -rl --include="*.md" "<basename>.md" web4-standard
  | grep -v "protocols/<basename>.md"   # exclude the doc's own file
```

Counts are then **classified by referrer type**, because a mention in `README.md` or an audit log is not a normative consumer:
- **NAV** = `README.md` navigation listing
- **STATUS** = `INTEGRATION_STATUS.md`, `NOVA_REVIEW_SUMMARY.md` (status/review docs)
- **AUDIT** = `docs/audits/*` (this audit program's own history)
- **NORM** = a spec doc that cites it as part of its normative content
- **SISTER** = another doc inside `protocols/` (intra-cluster, not external)

"last commit" = `git log -1 --format=%ci -- <path>` (date only).

## 2. The cluster at a glance

| `protocols/` doc | last commit | NAV? | external NORM consumers | canonical `core-spec/` counterpart | counterpart last commit |
|---|---|---|---|---|---|
| web4-r6-framework.md | 2025-09-11 | ✗ (orphan) | 0 (1 SISTER: entity-relationships) | **r6-framework.md** | 2026-06-11 |
| web4-dictionary-entities.md | 2025-09-11 | ✗ (orphan) | 0 | **dictionary-entities.md** | 2026-06-13 |
| web4-witness.md | 2025-09-11 | ✗ (orphan) | 0 | none (witness concept is scattered) | — |
| web4-witnessing.md | 2025-09-14 | ✗ (orphan) | 0 (1 STATUS) | none (scattered) | — |
| web4-lct.md | 2026-02-17 | ✓ | 1 NORM (the canonical LCT doc cites it!) | **LCT-linked-context-token.md** | 2026-06-15 |
| web4-entity-relationships.md | 2026-02-17 | ✓ | 0 (2 STATUS/NAV) | none (entity-types.md adjacent) | — |
| web4-metering.md | 2026-04-29 | ✓ | 1 NORM (`errors.md`) | none | — |
| web4-handshake.md | 2026-06-18 | ✓ | 2 NORM (`security-framework.md`, `extensions.md`) | none (adjacent to core-protocol §5) | — |

Full referrer lists are in §6 (Appendix) for verification.

## 3. The two structural defects this exposes

### 3.1 SSOT inversion at the navigation layer
`README.md` lists `protocols/` and `core-spec/` docs **mixed together under the same topical headings**, with no marker distinguishing canonical from draft/parallel. Consequences:
- Under **"Identity & Context"**, README links `protocols/web4-lct.md` as "*Linked Context Token specification*." The canonical `core-spec/LCT-linked-context-token.md` is linked **zero times in the entire README** (`grep -c` = 0). A reader navigating the README is sent to the **frozen sister** as the LCT spec and is never pointed at the live canonical doc at all.
- Same for `protocols/web4-entity-relationships.md`, `protocols/web4-handshake.md`, `protocols/web4-metering.md`.
- Conversely, for **r6** and **dictionary**, README links the canonical `core-spec/` docs and the `protocols/` sisters are **invisible** (0 NAV) — orphaned.

So the same directory contains both "README-promoted-as-canonical" docs and "README-invisible orphans," with no consistent rule.

### 3.2 Canonical-defers-to-frozen (the sharp D0 case)
`core-spec/LCT-linked-context-token.md:689` ends with:
> `**LCT Protocol Details**: protocols/web4-lct.md`

The canonical, actively-maintained LCT spec (last touched 2026-06-15) **points at the frozen sister (2026-02-17) as the source of "protocol details."** This is the inversion in its purest form: the live doc treats the stale parallel doc as authoritative for detail. C74 already documented that the sister's normative content (7-role/12-type model, malformed §1 JSON, etc.) diverges from canonical — so this pointer routes readers from correct to incorrect.

## 4. Proposed partition (ADVISORY — operator decides each row)

The cluster is **not uniform**. It splits three ways. The recommendation column is the session's read of the evidence; the operator owns the call.

### Group A — Orphaned duplicates of an actively-maintained canonical doc
**→ recommend: SUPERSEDE (archive with a deprecation/SSOT-pointer banner).**

| doc | evidence | rec |
|---|---|---|
| web4-r6-framework.md | 0 NAV, 0 external NORM, frozen 2025-09-11; canonical `core-spec/r6-framework.md` is live (2026-06-11) and has its own 3-cycle audit history (C12/C48/C49). 9 months stale. | SUPERSEDE |
| web4-dictionary-entities.md | 0 NAV, 0 NORM, frozen 2025-09-11; canonical `core-spec/dictionary-entities.md` live (2026-06-13), audited C17/C52/C53. 9 months stale. | SUPERSEDE |

These two carry no inbound weight, are 9 months behind a canonical doc that has been audited three times each, and would cost real tokens to "sync." Archiving them removes a divergence surface at zero consumer cost.

### Group B — Frozen parallel spec that ALSO has a live canonical (this is D0)
**→ recommend: SUPERSEDE, with the canonical's deferral pointer (`:689`) removed.**

| doc | evidence | rec |
|---|---|---|
| web4-lct.md | NAV-promoted as "the LCT spec," but canonical `core-spec/LCT-linked-context-token.md` is live (2026-06-15) and C-audited (C9/C24/C60/C61). Sister frozen 2026-02-17, predates the C60/C61 canonical fixes (C74: none reflected). Canonical **defers to** the sister at `:689` — SSOT inversion. | SUPERSEDE |

D0 resolved as SUPERSEDE means C75 ≈ (a) add a deprecation/SSOT-pointer banner to `protocols/web4-lct.md`, (b) fix README "Identity & Context" to link the canonical doc, (c) delete the `:689` deferral pointer in the canonical doc. It does **not** mean applying C74's ~9 sync line-items — those become moot. If instead D0 resolves as MAINTAIN, C75 = the ~9 autonomous C74 edits (see PR #363 / C74 §C). **Either way, the gate is real and the operator picks.**

### Group C — Sole home for their concept (no canonical counterpart)
**→ recommend: MAINTAIN + schedule each for its own first audit (do NOT supersede).**

| doc | evidence | rec |
|---|---|---|
| web4-metering.md | NAV-listed, 1 real NORM consumer (`errors.md`), no `core-spec/` equivalent — this is the only ATP/ADP-resource-exchange wire spec. Updated 2026-04-29. | MAINTAIN → audit |
| web4-entity-relationships.md | NAV-listed, no `core-spec/` equivalent (`entity-types.md` is adjacent, not a duplicate). The only binding/pairing/witnessing/broadcast spec. 2026-02-17. | MAINTAIN → audit |
| web4-handshake.md | NAV-listed, 2 NORM consumers, actively maintained (2026-06-18), already in an audit cycle (C28/C72/C73). | MAINTAIN (in cycle) |

### Group D — Intra-cluster duplicate pair (special case)
**→ recommend: operator picks ONE; supersede the other; then audit the survivor.**

| docs | evidence | rec |
|---|---|---|
| web4-witness.md **and** web4-witnessing.md | BOTH frozen 2025-09, BOTH 0 NAV, BOTH 0 external NORM. Overlapping scope: `web4-witness.md` ("unified witness framework, normalizing witness classes/headers/attestation formats") has §Witness Role/Classes/Attestation Format/Security/IANA; `web4-witnessing.md` has §Roles/Envelope Format/Interop Vectors/IANA/Security. There is **no** dedicated `core-spec/` witness doc — the witness concept is scattered across ~10 core-spec docs (SAL, acp, mrh, presence-protocol, …). So one of these two MAY be worth promoting to canonical, but maintaining BOTH is the defect. | pick one → supersede other → audit survivor |

## 5. Recommended operator decision (single call, advisory)

A clean way to settle the whole cluster in one decision:

1. **SUPERSEDE** Group A (r6, dictionary) and Group B (lct) — all three are stale duplicates of a live, audited canonical `core-spec/` doc. Apply deprecation banners + fix README/`:689` SSOT inversions. This is the C75 remediation IF the operator agrees.
2. **MAINTAIN** Group C (metering, entity-relationships; handshake already in cycle) and queue each for a first C-series audit on a future remediation/audit turn.
3. **Resolve Group D** (witness vs witnessing) by choosing a survivor; supersede the other; queue the survivor for audit.

If the operator prefers MAINTAIN for any Group A/B doc, that doc instead gets its normal autonomous remediation (C74 §C line-items for lct; first audits for r6/dictionary). The point of this triage is that the operator now sees that the choice is **the same choice four times**, with the evidence to make it once.

**Process recommendation**: a follow-up session should NOT auto-apply any of the above. The next web4 turn after this triage should either (a) execute whichever option the operator selects, or (b) if D0 is still unanswered, idle-and-wait per the gate — NOT re-audit the cluster.

## 6. Appendix — full referrer lists (verification)

```
web4-r6-framework.md        ← protocols/web4-entity-relationships.md            [SISTER]
web4-dictionary-entities.md ← (none)
web4-lct.md                 ← README.md [NAV], INTEGRATION_STATUS.md [STATUS],
                              docs/audits/C33-...md [AUDIT],
                              core-spec/LCT-linked-context-token.md [NORM ← the :689 deferral]
web4-handshake.md           ← README.md [NAV], docs/audits/C33-...md [AUDIT],
                              INTEGRATION_STATUS.md [STATUS],
                              core-spec/security-framework.md [NORM], registries/extensions.md [NORM]
web4-entity-relationships.md← README.md [NAV], INTEGRATION_STATUS.md [STATUS]
web4-metering.md            ← README.md [NAV], core-spec/errors.md [NORM], INTEGRATION_STATUS.md [STATUS]
web4-witnessing.md          ← NOVA_REVIEW_SUMMARY.md [STATUS]
web4-witness.md             ← (none)
```

Last-commit dates (`protocols/` vs canonical counterpart):
```
web4-r6-framework.md        2025-09-11   |  core-spec/r6-framework.md          2026-06-11
web4-dictionary-entities.md 2025-09-11   |  core-spec/dictionary-entities.md   2026-06-13
web4-lct.md                 2026-02-17   |  core-spec/LCT-linked-context-token  2026-06-15
web4-entity-relationships.md2026-02-17   |  (none)
web4-metering.md            2026-04-29   |  (none)
web4-witnessing.md          2025-09-14   |  (none)
web4-witness.md             2025-09-11   |  (none)
web4-handshake.md           2026-06-18   |  (none; in C28/C72/C73 cycle)
```

---

*C75 is a triage, not an audit or a remediation. It makes no edits and settles no design question. It exists so the operator can resolve D0 — and the six sister-docs behind it — with one informed decision instead of six sequential discoveries of the same problem.*
