# C33 — Identifier-Scheme Consolidation Audit (cross-cutting)

**Date**: 2026-06-05
**Auditor**: autonomous web4 session (legion, slot `120000`)
**Type**: Cross-cutting primitive-clustered RE-audit (not single-file). Consolidates the open identifier carries from C28 (web4-handshake), C29 (data-formats), and C30 (errors).
**Method**: Multi-agent adversarial-verify workflow — 5 lens-finders (one per identifier sub-primitive) → refute-by-default verifier per finding → hand-verification against live files before write. 43 candidate findings → 39 confirmed, 4 refuted; verifier corrected 13 severities/dispositions (both up and down).
**Scope**: READ-ONLY. The canonical-form **choice** is intentionally NOT decided here — it is the operator's design decision. This audit consolidates the scattered evidence into one decidable picture.

---

## 0. Why this audit exists (the consolidation rationale)

First-pass per-file core-spec normative coverage is complete (C1–C32). The single largest residual backlog — carried across C28/C29/C30 — is the **identifier scheme**: which prefix is canonical for a Web4 entity, how the LCT identifier relates to it, and how pairwise pseudonymous identifiers are derived. A scheme-coherence contradiction *structurally cannot* be surfaced by a single-file audit, because the divergence lives in the gaps *between* files. This audit clusters on the identifier primitive across the whole corpus + SDK + conformance vectors.

**Corpus census** (verified): `did:web4:` 83 occ · `w4id:` 16 occ · `lct:web4:` 635 occ · `web4://` 36 occ.

**The core observation**: the divergence is *already known and documented* — `core-protocol.md` §4 explicitly states the W4ID prefix form is "subject to an open repo-wide identifier-scheme decision and is intentionally not resolved here." But the "intentionally unresolved" framing now **understates** the situation: while the prose has deferred, **three independent executable artifacts have each silently resolved it differently**, and the divergence has spread from one primitive (entity-id) to four (entity-id, LCT-id, pairwise-id, resource-locator). Non-decision is no longer free — it is accreting concrete, mutually-incompatible commitments. This audit's job is to make that cost legible so the operator can decide.

---

## 1. The canonical-form decision matrix (the consolidation deliverable)

Every artifact that commits to an **entity-identifier** surface form, and what it actually chose:

| Artifact | Authority class | Entity-id form it commits to | Anchor |
|----------|-----------------|------------------------------|--------|
| `data-formats.md` §1 ABNF | **Normative SSOT** | `did:web4:` *method* `:` *id* | data-formats.md:19 |
| `architecture/grammar_and_notation.md` §4.2 | Normative (architecture) | `did:web4:` — labelled "**RECOMMENDED**" | grammar_and_notation.md:50 |
| `submission/web4-rfc.md` §3.1 / embedded data-formats | Normative (submission) | mixed: `w4id:` short form (L219) **and** `did:web4:` ABNF (L344) | web4-rfc.md:219,344 |
| `core-protocol.md` §4.1 | Orientation (defers to SSOT) | `w4id:` "illustrative form" (explicitly non-normative) | core-protocol.md:103-105 |
| `data-formats.md` §4 pairwise fn | **Normative SSOT** | `w4id:pair:` (for pairwise) | data-formats.md:91 |
| `test-vectors/protocol/core-protocol.json` | **Conformance vector (authority)** | `w4id:key:` / `w4id:web:` | core-protocol.json:10,14,25,29,40,44,55,59 |
| SDK `generate.py` | **Reference impl** | `lct:web4:{type}:` (entity fields) | generate.py:56,109,110,243,293 |
| SDK `security.py` `derive_pairwise_w4id` | **Reference impl** | `did:web4:key:` (for pairwise) | security.py:254-263 |

**Reading**: the *prose* specifications lean clearly toward `did:web4:` (the SSOT ABNF mandates it; the architecture doc calls it "RECOMMENDED"). The *executable artifacts* have each diverged: the conformance vector to `w4id:`, the normative pairwise function to `w4id:pair:`, and the SDK to `lct:web4:`. **No two executable artifacts agree.** Because conformance vectors are test-authority, this is a genuine HIGH-severity standing contradiction, not a cosmetic one.

---

## 2. Findings

Severity rubric: HIGH = contradicts a conformance vector or the SDK (test-vectors-as-authority), or a security-relevant divergence · MEDIUM = cross-spec prose divergence · LOW = intra-file wording/naming · INFO = confirmation/negative-result.
Disposition: **DESIGN-Q** = requires operator to choose a canonical form (NOT autonomously fixable) · **AUTONOMOUS** = a remediator can fix without a canonical-form decision · **CROSS-TRACK** = fix spans SDK / vectors / multiple specs.

### Cluster A — Entity W4ID canonical prefix

**A-H1 (HIGH, DESIGN-Q) — FLAGSHIP. The canonical entity-identifier prefix is unresolved, and three executable artifacts have de-facto diverged.**
`data-formats.md` §1 (L19) normatively defines `w4id = "did:web4:" method-name ":" method-specific-id`. `core-protocol.md` §4 (L99) explicitly acknowledges the prefix form is an "open repo-wide identifier-scheme decision … intentionally not resolved." Meanwhile the conformance vector commits to `w4id:` (core-protocol.json:10,14,25…), the SSOT's own §4 pairwise function emits `w4id:pair:` (data-formats.md:91), and the SDK emits `lct:web4:` (generate.py:109-110). See §1 matrix.
**Decision required**: pick the canonical entity-id prefix — `did:web4:` (prose/SSOT/RECOMMENDED lean) vs `w4id:` (vector/short-form lean). Every downstream finding (A, C-prefix, D-embedded) resolves from this one choice. *This audit does not recommend a winner.*

### Cluster B — LCT identifier scheme (`lct:web4:`)

**B-H1 (HIGH, DESIGN-Q) — The `lct:web4:` LCT-id scheme is the most-used identifier in the corpus (635 occ) yet is undefined in the format SSOT and has two incompatible canonical forms.**
`data-formats.md` (the format SSOT) defines W4ID and pairwise derivation but **never mentions `lct:web4:`** (grep-confirmed). The scheme is introduced only by example in `LCT-linked-context-token.md` (L64) and `web4-lct.md` (L56). Worse, the live spec shows **two incompatible forms**: `lct:web4:mb32:...` (multibase-hash method, LCT-token.md:64) vs `lct:web4:{entity_type}:...` (`society`/`role`/`witness`/`human`/`agent`, LCT-token.md:76-82 and SDK generate.py). One treats the segment after `lct:web4:` as a *method* (`mb32`), the other as an *entity-type* (`society`). (Interacts with the C24 LCT-ID 4-way divergence carry.)
**Decision required**: is `lct:web4:` (a) a distinct namespace from the entity W4ID, (b) defined in `data-formats.md` as a sibling scheme, and (c) `lct:web4:mb32:<hash>` or `lct:web4:<type>:<id>`?

**B-M1 (MEDIUM, AUTONOMOUS) — No spec text states that `lct:web4:` is a scheme distinct from `did:web4:`.**
Both schemes are used as if obviously different (LCT id vs entity/subject id), but no sentence anywhere says so. A remediator can add a one-line clarifier in `data-formats.md` ("`lct:web4:` identifies an LCT instance and is distinct from the entity W4ID `did:web4:` of the LCT's subject") **without** resolving B-H1's form question. (data-formats.md:11-31, LCT-token.md:7-9,42.) This is the constructive residue that inoculates a future auditor against re-litigating the distinction.

### Cluster C — Pairwise / pseudonymous W4IDp derivation

**C-H1 (HIGH, DESIGN-Q) — Pairwise W4IDp derivation is specified FOUR mutually-incompatible ways; the salt-model divergence is security-relevant.**
The two specs that define the algorithm and the SDK that implements it disagree on every parameter:

| Source | KDF | Salt model | `info` string | Output form |
|--------|-----|-----------|---------------|-------------|
| `data-formats.md` §4 (L82-91) | HKDF | **derived from peer identifier** | `"web4-pairwise-id"` | `w4id:pair:` + base32(key[:16]) |
| `web4-handshake.md` §4.1 (L34-44) | HKDF-Extract-then-Expand | **128-bit random, MUST NOT derive from stable id** | `"W4IDp:v1"` | bare `w4idp` = MB32(...) |
| SDK `security.py` (L254-263) | **plain double-SHA256 (no HKDF)** | `sha256(peer_id)` (deterministic) | — | `did:web4:key:` |
| `grammar_and_notation.md` §4.1 | — | — | — | `web4://` authority = `w4-`+base32 |

The salt-model contradiction is not cosmetic: `data-formats.md` makes the salt a deterministic function of the peer identifier, while `web4-handshake.md` **MUST**-requires it to be 128-bit random and explicitly forbids deriving it from a stable identifier — a direct, security-relevant privacy-model contradiction (deterministic salts permit the cross-peer correlation pairwise IDs exist to prevent). The KDF difference (HKDF vs plain SHA256) means no two of these implementations interoperate. No cross-reference exists between the two specs (data-formats §4 ↔ handshake §4.1).
**Decision required**: one canonical pairwise derivation (KDF, salt model, info string, output prefix), then align the other two sources + add a conformance vector (none currently exercises it).

**C-M1 (MEDIUM, AUTONOMOUS) — `base32_encode` / multibase encoding for pairwise output is underspecified for interop.**
`data-formats.md` §4 calls `base32_encode(pairwise_key[:16])` without specifying alphabet/padding; `web4-handshake.md` says "MB32 … without padding"; grammar says `base32nopad`. A remediator can normalize the encoding wording to "multibase base32, no padding" across the three **once C-H1 picks the canonical output** — so this is AUTONOMOUS-but-coupled (apply after C-H1, or as a pure-wording alignment if the operator confirms base32nopad regardless of prefix).

### Cluster D — `web4://` resource locator

**D-H1 (HIGH, AUTONOMOUS) — `web4://` is defined in three places with no single SSOT and no cross-references, across 21 files that use it.**
Independent grammar definitions exist in `core-protocol.md` §6.1 (L183, `web4://<w4id>/<path>`), `architecture/grammar_and_notation.md` §4.1 (L44-47, `web4-URI = "web4://" w4-authority …` with `w4-authority = w4id-label / hostname`), and the form is exercised by `core-protocol.json`. None references the others; there is no SSOT designation in `data-formats.md`. **Autonomous fix** (no canonical-form decision needed): designate one normative home (most consistent with the C29/C30 SSOT pattern: a `web4://` section in `data-formats.md`), and convert the other two to orientation cross-refs. The *embedded identifier form* (`<w4id>` vs `w4id-label`) is deferred to D-M1.

**D-M1 (MEDIUM, DESIGN-Q) — The identifier embedded in a `web4://` authority inherits the unresolved Cluster-A form.**
`core-protocol.md` §6.1 embeds `<w4id>` (full identifier); `grammar_and_notation.md` §4.1 embeds `w4id-label = "w4-" base32nopad` (a *base32-of-pairwise-W4ID* label); the vector shows `web4://w4id:key:abc123/`. These are three different embedded forms. Resolves once A-H1 (and the pairwise output form C-H1) are decided.

### Cluster E — Undocumented `lct://` scheme (NEW — beyond the carried backlog)

**E-M1 (MEDIUM, CROSS-TRACK) — An `lct://` URI scheme appears in the SDK and attestation vectors but is defined in NO spec.**
`generate.py` (L75, `lct://web4:example@active`) and `test-vectors/attestation/attestation-vectors.json` (L13, `lct://sage:legion:agent@raising`) use an `lct://` authority-style locator. Grep confirms `lct://` appears in **zero** files under `core-spec/`, `protocols/`, or `architecture/` — it is entirely undocumented. Note this is a distinct surface from the colon-form `lct:web4:` (Cluster B): `lct://` is a double-slash URI authority (`lct://<authority>@<state>`), `lct:web4:` is a hierarchical identifier. This is a *fifth* identifier surface (entity `did:web4:`, LCT `lct:web4:`, pairwise `w4id:pair:`, resource `web4://`, and now `lct://`). Surface it for the operator; the fix (define or remove) spans SDK + vectors + spec.

### Low / informative

**L-1 (LOW, AUTONOMOUS) — `grammar_and_notation.md` §4.2 labels `did:web4` "RECOMMENDED"** — an architecture-doc preference that, while consistent with the SSOT ABNF, is itself a (mild) normative statement on the A-H1 question made *outside* the SSOT. Worth folding into the A-H1 decision record as evidence of the prose lean, and (post-decision) reconciling its "RECOMMENDED" hedge with whatever §1 mandates.

**INFO-1 (negative result) — Refuted overcall: "the conformance vector's `w4id:` contradicts the ABNF" is partly intentional.** `core-protocol.md` §4.1 explicitly designates `w4id:<method>:<id>` the "illustrative form" and defers to `data-formats.md` §1 as normative. So the vector's `w4id:` is an *acknowledged* short-form, not an accidental contradiction — BUT (per A-H1) it is a *concrete* commitment by a test-authority artifact, which is why A-H1 remains HIGH. The nuance: the contradiction is documented-and-deferred, not unknown.

**INFO-2 (negative result) — Refuted overcall: "the SDK uses `did:web4:` for entity ids."** False — the SDK uses `lct:web4:` in `principal`/`agent`/`actor`/`society` fields (generate.py:56,109-110,243,293). This is the B-cluster observation, not a did:web4 confirmation. Recorded so a future auditor does not re-manufacture the inverse claim.

**INFO-3 (negative result) — The pairwise derivation *algorithm prose* in `data-formats.md` §4.2 is reasonably complete** (master_secret, peer-derived salt, HKDF, base32 steps are all enumerated). The C-H1 problem is not under-specification *within* §4 — it is *cross-source* contradiction (handshake + SDK disagree). Recorded to keep C-H1 scoped to reconciliation, not rewriting §4.

---

## 3. Disposition summary

| ID | Sev | Disposition | One-line |
|----|-----|-------------|----------|
| A-H1 | HIGH | DESIGN-Q | Canonical entity-id prefix unresolved; 3 executable artifacts diverged (flagship) |
| B-H1 | HIGH | DESIGN-Q | `lct:web4:` (635 occ) undefined in SSOT + 2 incompatible forms |
| C-H1 | HIGH | DESIGN-Q | Pairwise W4IDp 4-way incompatible (KDF/salt/info/output); salt-model is security-relevant |
| D-H1 | HIGH | AUTONOMOUS | `web4://` 3 definitions, no SSOT/cross-refs across 21 files |
| B-M1 | MED | AUTONOMOUS | Add clarifier: `lct:web4:` ≠ `did:web4:` (no form decision needed) |
| C-M1 | MED | AUTONOMOUS* | Normalize pairwise base32/multibase wording (*couples to C-H1) |
| D-M1 | MED | DESIGN-Q | `web4://` embedded-id form inherits A-H1 |
| E-M1 | MED | CROSS-TRACK | Undocumented `lct://` scheme in SDK + attestation vectors |
| L-1 | LOW | AUTONOMOUS | grammar "RECOMMENDED did:web4" — fold into A-H1 decision record |
| INFO-1/2/3 | INFO | — | Negative results / refuted overcalls (constructive residue) |

**Autonomous-actionable now (no operator decision needed)**: D-H1 (designate `web4://` SSOT + cross-ref; do NOT change embedded form), B-M1 (distinctness clarifier), L-1 (decision-record note). These are the candidates for a future REMEDIATION alternation turn.
**Operator design decisions required (blocking)**: A-H1, B-H1, C-H1, D-M1 — these are ONE coupled decision cluster (the canonical-form choice cascades through all four). **This is the consolidation: the C28/C29/C30 identifier carries reduce to this single operator decision.**
**Cross-track**: C-H1 SDK-side (security.py uses plain SHA256 not HKDF), E-M1 (`lct://`), and adding a pairwise conformance vector (none exists).

---

## 4. Method note (adversarial-verify workflow)

5 lens-finders (entity-W4ID, LCT-id, pairwise, web4://, SDK+vector triangulation) → each candidate piped to a refute-by-default verifier → hand-verification of every cited anchor before write. 43 candidates → **39 confirmed, 4 refuted** (the 4 FALSE verdicts are recorded as INFO-1/2/3 negative results — they correctly deflated "vector contradicts ABNF" and "SDK uses did:web4:" overcalls). The verifier corrected 13 severities/dispositions in both directions, and the synthesis pass merged ~30 duplicate surfacings of the same 4 underlying contradictions into the clusters above. The flagship reframing — "intentionally unresolved" *understates* the cost because executable artifacts have already silently chosen — emerged only at synthesis, from the §1 decision matrix that no single lens assembled. Anti-padding: duplicates were merged, not counted; the negative results are reported as findings of equal weight.

---

*C33 consolidates carry-C28/C29/C30 (unified-identifier cluster). It does not decide the canonical form — that is the operator's. It makes the decision decidable by showing that one choice resolves A-H1 + B-H1 + C-H1 + D-M1 simultaneously.*
