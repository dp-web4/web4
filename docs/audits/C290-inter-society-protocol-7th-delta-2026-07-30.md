# C290: `inter-society-protocol.md` (ISP) 7th-delta RE-Audit

**Date**: 2026-07-30
**Track**: web4 (Legion autonomous session, slot `web4-20260730-060011`)
**Instrument**: C-series delta RE-audit; **7th delta** on `inter-society-protocol.md`
(lineage C6 → C25 → **C62** → remediation **C63** (#341) → C102 → C136 → **C174** → **C212** → **C250** → **C290**)
**Source**: `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2 DRAFT, 384 lines, last edited
`0405f331` PR #341, 2026-06-16 — **BYTE-FROZEN 44 days**; `git diff 0405f331 HEAD` = empty; blob
`22bf6c1d`, unchanged since the C212 *and* C250 snapshots)
**Method**: §A prior-finding verification + `&#` sweep + bidirectional carry re-verification. §B
frozen-target corpus-delta over ISP's 6 cited siblings. **§B′ mirror-set RE-DERIVATION from the spec's
SUBJECT MATTER with M1/M2/M3 admission criteria pre-registered in writing before the sweep** and an
N=3 group cap with fixed ordering. §B″ machine-validation of the one non-prose artifact ISP cites by
path. Adversarial refute-by-default aimed at the pass's **flagship**, not its leftovers.

**Result headline**: **0 net-new defects against the spec (8th consecutive clean ISP delta on the
prose), 2 exclusion rulings, 1 machine-validation PASS (published negative), 1 net-new INFO that is a
CLOSURE RECOMMENDATION on a 45-day-old design-Q, and the pass's own flagship finding REFUTED by its own
target spec. ZERO mutation.**

---

## Summary

| Severity | NEW (C290) |
|----------|-----------:|
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| INFO | **1** (N1 — net-new, ISP-owned, routed as a *closure recommendation*) |
| **Total NEW distinct defects vs. the spec** | **0** |
| Candidates REFUTED | 1 (the flagship) |
| Exclusion rulings published | 2 (`hub/` at M1; `ledgers/act-chain/` at M2) |

**Why this pass exists at all.** Target byte-frozen 44 days AND all six cited siblings frozen ⇒ the
C288 **"0 net-new" TRAP shape**, not a clean bill. Per method carry v7 the remaining surface is (a)
directories the lineage has never read and (b) the standard's own published non-prose artifacts. The
pass found ISP's lineage had **never once read `hub/`** (`grep -ci 'hub/|hub-lib|constellation'` over
all 7 prior audit docs = **0 × 7**) and had never machine-validated the one schema ISP cites by path.
Both were gated here. Both came back **negative** — and the negatives are the deliverable.

---

## §A: Prior-Finding Verification

`git diff 0405f331 HEAD` on ISP = **empty**. On a byte-frozen target the C63 remediations are held *by
construction*; each was nonetheless re-read at its current line rather than assumed:

| C62 ID | Sev | C63 fix | Line | Status |
|--------|-----|---------|------|--------|
| **B4** | MED | §2.2 step 4 `SHALL`→`MAY` | L108 | **HELD** (verified: "MAY update their own LCTs") |
| **B5** | MED | §4.5 "mint ADP and charge it to ATP" + cite §2.1–§2.2 | L239 | **HELD** |
| **B3** | LOW | §8/§9 §7.7 architecture-Normative phrasing | L368 / L377 | **HELD** (both halves) |
| **B6** | LOW | §2.1 ≥3-witness placement | L75 | **HELD** |
| **B7** | LOW | §4.6 schema path fix | L252 | **HELD** — and *machine-checked* this pass (§B″) |
| **B8** | LOW | §8 `web4:memberOf` cite §3.3/§3.5 | L362 | **HELD** |
| **B9** | LOW | §2.2 SOCIETY_SPEC §4.2.1 formation-event cross-ref | L115 | **HELD** |
| **B14** | LOW | §1.3 demote Eurozone analogy to last | L45 | **HELD** |
| **B16** | LOW | §8 society-roles bidirectional dependency | L369 | **HELD** |
| **B2-interim** | ½ B2 | §3.2 forward-pointer to mcp §7.7.1 | L150 | **HELD** |

**10/10 HELD, 0 regressed.** `&#|&amp;|&lt;|&gt;` sweep on ISP: **0 hits, CLEAN.**
No remediation touched ISP since C63; no sibling edit introduced an ISP change. Carries C25-H1
(resolved downstream at C51) and C6-L2 (Gesellian framing, deferred) unchanged.

---

## §B: Corpus-Delta Surface — 2nd CONSECUTIVE ZERO-MOVER DELTA

All six cited siblings are byte-frozen at or before the C250 snapshot, so every C212/C250 DISJOINT
adjudication stands verbatim and nothing is re-litigated:

| Sibling | Last commit | Verdict carried |
|---------|-------------|-----------------|
| atp-adp-cycle | `256ab51d` 2026-07-07 | DISJOINT — B5/B10/B11 stand |
| mcp-protocol | `3e765345` 2026-07-13 | DISJOINT (§7.8 async mailbox) |
| SAL | `1354e4c2` 2026-07-14 | DISJOINT (§5.6 Effector) — B13 stands |
| SOCIETY_SPEC | `87377c38` 2026-07-14 | DISJOINT (§7.3) — B9 stands |
| society-roles | `1354e4c2` 2026-07-14 | DISJOINT (Effector row) — B16 stands |
| LCT | `d89595e8` 2026-07-16 | DISJOINT (§1.2 insert #531) |

**Premise correction (recorded because the first draft of this pass got it wrong).** The in-window
figure is **13 hub commits**, not 47. 52 is the whole-repo commit count since the C250 snapshot; the
"21 / 18 / 8" path figures are **file-touch counts, not commits**. The policy reviewer caught this —
the same `awk`-over-files error it caught at C286. An inflated in-window premise is how a pass talks
itself into an unbounded read.

**Gate 3 (method carry v6 — ontology mover) = NEGATIVE in one line.** `01f410db` reshaped
`t3v3-ontology.ttl` (`web4:Tensor` superclass, `rdfs:domain` widened T3Tensor→Tensor,
new `web4:observationCount`). ISP's **only** `web4:` token is `web4:memberOf`, and all 10 of its
T3/V3 mentions (L7, L83, L130, L181, L364–L367, L375–L376, L380) are **prose** — ISP emits **zero
tensor RDF** across its 14 fenced blocks. The domain/superclass fix cannot falsify an ISP example.

---

## §B′: Mirror-Set Re-Derivation — criteria PRE-REGISTERED, then applied

### The pre-registered admission criteria (written before the sweep, verbatim from the approved scope)

- **M1 — subject-matter reach.** Does the artifact implement or assert behaviour on one of ISP's
  *numbered-section mechanisms* (§2 genesis/≥3 birth witnesses, §3 first-contact three-option, §4 ATP
  reification sovereignty, §5 secession/dissolution, §6 minimum viable society, §7 ledger anchoring)?
  Tested by **behaviour grep, not ISP's prose nouns**. FAIL ⇒ declined, and **the zero-hit grep is
  itself the recorded result**.
- **M2 — genuine mirror vs. evidence-only.** Is it product-bearing (published package, shipped binary,
  or an artifact the standard itself publishes)? FAIL ⇒ may still be the **best evidence available**,
  routed as a *demonstrated upgrade to a standing carry*, **never as a net-new defect**.
  **M2c**: an artifact inside `web4-standard/` that the standard publishes is normative **by ROLE even
  if its PATH says test/reference**.
- **M3 — REACH, not verdict.** Does the divergence reach a consumer surface (caller, importer,
  published API, relying party)? Explicitly **not** "would it indict the spec" — that phrasing is
  self-sealing (C286) and would pre-judge the conclusion. Reach ⇒ routes **even when the spec is
  correct**; no reach ⇒ INFO.

**N=3 groups, fixed ordering, committed before evidence:** G1 `ledgers/` → G2 `web4-standard/schemas/`
→ G3 SDK federation cluster + `hub/` as an M1-tested candidate.
**Deferred beyond the cap and written into §C (not silently dropped):** `web4-trust-core/`,
`ledgers/reference/typescript/lct-document.ts`, `web4-policy/`, whitepaper surfaces.

### Pre-read prediction (recorded before G1 was opened, per the C286 precedent)

> G1 → M1-PASS / M2-FAIL. G2 → genuine coin-flip. G3 → `hub/` M1-FAIL; `federation.py` M1/M2-PASS with
> no net-new. *Any of these being wrong is the informative outcome and will be published as such.*

**Outcome: all three predictions held.** Recorded because C286's published prediction was *wrong* and
that was the more valuable result; a correct prediction is reported with no extra credit claimed.

### G1 — `ledgers/act-chain/bridge/` — **M1-PASS, M2-FAIL ⇒ EXCLUDED as a mirror**

Never read in **8** prior ISP passes (`ledgers/` = 0, `act-chain` = 0 across all 8 audit docs), while
**ISP §7 is literally titled "Ledger Anchoring (Cross-Reference)"**.

- **M1 = PASS, loudly.** `genesis_witness.py` (393L), `genesis_atp_adp_manager.py` (539L),
  `genesis_blockchain.py` (453L) sit on ISP §2 (genesis) + §4 (ATP reification) + §7 simultaneously.
- **M2 = FAIL.** No `pyproject.toml`/`setup.py` anywhere under `ledgers/`; script-style relative
  imports (`from genesis_witness import GenesisWitnessSystem`); the only repo-wide references are
  `archive/reference-implementations/act_settlement_protocol.py` and `simulations/attack_track_fx.py`.
  Its own README declares it a copy of `ACT/implementation/ledger/genesis_*.py`. Not product-bearing.
- **Divergence observed, and then DECLINED on chronology.** `create_initial_pool()` credits
  `initial_atp` **directly into `atp_balance`** for 8 genesis entities — i.e. genesis mints *charged
  ATP*, whereas `atp-adp-cycle.md` §2.1 states "Societies mint tokens in the discharged (ADP) state"
  and ISP §4.5 L239 says minting "creates tokens in the discharged ADP state; charging is the ADP→ATP
  transition". Its `TransactionType` also labels ADP→ATP "value created", where ISP §4.1 L198 insists
  charging is "recognizing resource contribution, **not** creating value".
  **CHRONOLOGY GUARD FIRES:** the file dates to `7fb0284f` **2026-02-08**; the §4.5 parenthetical was
  **added** by `0405f331` on **2026-06-16** (verified: the diff shows it as a `+` line). An
  implementation cannot be evidence about the ambiguity of text written four months after it.
  ⇒ **No finding. Spec CORRECT. Recorded, not charged.**

### G2 — `web4-standard/schemas/` — machine-validation **PASS** (published negative)

ISP L252 is the spec's **only** citation of a non-prose artifact: the `AttestationEnvelope` primitive
"(see `schemas/attestation-envelope-jsonld.schema.json` and the SDK's `web4/attestation.py`)".
Path resolution stated explicitly: L252's paths are relative to `web4-standard/`, so the SDK module is
`web4-standard/implementation/sdk/web4/attestation.py` — **there is no top-level `sdk/`**.

**Validator scope published** (per C163 — the verifier is itself a silent-failing hypothesis):
`jsonschema` 4.26.0, `Draft202012Validator` selected from the schema's own declared
`$schema: draft/2020-12` (**not** Draft7), `FormatChecker` enabled; schema self-check `check_schema()`
= VALID; 13 `required` properties, `additionalProperties: false`.

| Check | Result |
|-------|--------|
| Both cited artifacts exist at the resolved paths | **PASS** (5449 B schema, 18763 B SDK module) |
| The `@context` URI the SDK emits is a published artifact | **PASS** (`schemas/contexts/attestation-envelope.jsonld` exists) |
| SDK `to_jsonld()` canonical TPM2 envelope vs. the schema | **PASS** — 0 errors, all 13 required keys emitted |
| `anchor.type` / `proof.format` enums vs. SDK values | **PASS** (`tpm2`/`tpm2_quote` accepted) |
| Numeric types (`timestamp`, `challenge_ttl`, `trust_ceiling`) | **PASS** (schema `number` ↔ SDK `float`) |
| Examples in `docs/specs/attestation-envelope.md` | **NO SUBSTRATE — 6 fenced blocks, langs `typescript`/`python` only, 0 JSON envelope examples** |

**Verdict: ISP L252 is sound.** Unlike `lct.schema.json` (which C288-N1 caught inverting its own spec
and Draft7-failing every corpus LCT), the ISP-cited envelope schema and the SDK emitter it names
**agree**. Reported as a *published* negative with its scope stated, not as an absence of findings.
The 0-JSON-example result is likewise published as a scope fact: no doc example exists to falsify.

### G3 — SDK federation cluster + `hub/` (M1-tested candidate)

**`hub/` → M1-FAIL ⇒ EXCLUDED. The zero-hit greps ARE the result** (C282 precedent):

| ISP mechanism grep (`hub/ --include=*.rs`) | hits |
|---|---:|
| `first.contact`, `three.option`, `secess`, `dissol`, `birth.witness`, `foreign_society`, `constituent` | **0** each |
| `minimum.viable` | **1** — and it is a *doc-comment tagline* (`hub/hub-daemon/src/main.rs:32`: "Web4 Community Hub — minimum-viable Web4 society for a community chapter"), i.e. prose, not an implementation of §6.2's semantic-viability criteria |

**Correction to this pass's own first draft:** `hub/hub-lib/src/constellation.rs` (1313L, heavily moved
by #591/#592/#598) was proposed as the flagship lead and is **not an ISP mirror** —
`grep -ciE 'federation|constituent|secess|cross-society|inter-society|citizenship' constellation.rs`
= **0**. Its `foreign` vocabulary is owner-and-device-key provenance, not cross-society boundary. The
lead and the instrument that justified it were **disjoint** ([[feedback_enumeration_and_grep_hypotheses]]
— baseline your own instrument). Recorded so no future ISP delta re-derives it as a hot lead.
⇒ **`hub/` is a documented, dated, criterion-backed NEGATIVE for the ISP lineage** — the 8-pass blind
spot is now closed rather than merely unexamined. (It remains a live mirror for the *society-law*
lineage per C280/C286; this ruling is ISP-scoped.)

**`federation.py` → M2-PASS, M1-FAIL on the pinned mechanisms.** Exported via
`web4/__init__.py:115`, so product-bearing; but `secede|secession` 0, `dissol` 0, `first.contact` 0,
`constituent` 0, `minimum_viable|validate_minimum` 0 — only `requires_witnesses` (6) touches ISP
subject matter, and that is a generic procedure threshold. **Frozen since `759eaefa` 2026-04-17; 0
commits under `implementation/sdk/` in-window** ⇒ **C174-N1 (LOW) and C174-N2 (INFO) HELD by
construction**, not re-derived.

---

## §B‴: The flagship candidate — RAISED, then REFUTED by ISP's own text

Refute-by-default was pointed at the pass's **best** finding, per [[feedback_refute_your_best_finding]].

**The charge (candidate MED→HIGH):** `web4-core/src/attestation.rs:142-154` declares
`BIRTH_WITNESS_QUORUM = 3` as "The canon-required minimum witness quorum … (§4.2)", counts **distinct**
witnesses via a `BTreeSet`, and doc-comments "≥3 **distinct** birth witnesses. Distinctness matters —
three entries that are one witness are not a quorum", with a test asserting `["w1","w1","w1"]` fails.
But `LCT-linked-context-token.md:537` says "witness distinctness / anti-collusion **is not asserted**
by this property alone", added `9d1933f8` **2026-06-15** — whereas the Rust logic landed `e8f313e4`
(#527) **2026-07-15**, one month later. Python `capability.py:276` meanwhile uses bare
`len(bc.birth_witnesses) >= 3`. ⇒ apparent cross-language disagreement on certificate validity, with
the stricter side mis-attributing its strictness to the canon.

**VERDICT: REFUTED.** Four independent kills, each verified at file:line by me and not taken on the
refuter's word:

1. **The charge equivocated on "distinct" — fatal.** `git show 9d1933f8` proves the replaced line read
   "Birth requires multiple **independent** witnesses". L537's parenthetical therefore disclaims
   **independence / anti-collusion** (different *controllers*). Rust's `BTreeSet` checks **cardinality**
   (different *ids*) and claims nothing about controllers or keys. Two different properties, one word.
2. **ISP — this pass's own target — affirmatively reads ≥3 as ≥3 distinct identities, and draws
   exactly the line #527 implements.** §6.1 L322: "A single human with three **keypairs** can
   syntactically satisfy the ≥3 witness quorum." §6.2 item 1: "A founder + three **identical** worker
   keypairs does NOT differentiate." §6.2 item 2: "Witnessing by an **identical-twin keypair** does not
   satisfy this." Cardinality = structural and satisfiable under single control; independence =
   semantic and explicitly not satisfied by twins.
3. **No reach.** `quorum_structurally_ok` has **zero non-test callers repo-wide** (only its own
   `#[cfg(test)]` module at `:306/:312/:315`; `hub/` = 0). Fails M3.
4. **Zero instances, next to a booked axis with nine.** Machine-walked every
   `birth_witnesses` array in the corpus: **18 arrays, 0 with duplicates, 9 with fewer than 3** —
   including `test-vectors/lct/valid-birth-certificate.json` (2 witnesses), which is the **already-booked
   C60-B1** (re-confirmed and widened at C288 four days ago). The charge picked the axis with **zero**
   instances while a booked axis had nine.
   *Instrument note:* my first run globbed `web4-standard/testing/test-vectors/` and returned **0
   arrays**; the vectors live at `web4-standard/test-vectors/`. I treated the zero as instrument
   failure rather than absence and re-derived the scope from ground truth — the standing lesson
   working as intended.

Also **already ruled on twice post-L537** (book-once): C246 L69/L71 read `verify_quorum`, called it
"≥3 **distinct** Existence attestations", and held no SAL MUST violated; C248 L94 read both functions
and wrote "the birth-cert substance is a **genuine mirror** … **No additional finding**." Even had the
charge survived on merit, it would have been a **re-open, not net-new**.

**Do NOT resurrect this charge.** Direction of any future look: `verify_quorum`'s distinctness is
*arithmetic* (N signatures from one key is one signer, by set semantics), not an imported requirement —
and had `quorum_structurally_ok` *not* deduped, it would be a lax screen in front of a strict
authoritative check, admitting certs the real verifier rejects. The charge argued for the worse design.

---

## §C: Findings and Carry Ledger

### N1 — INFO, **net-new, ISP-owned**: ISP §6.1 already supplies the structural-vs-semantic line that the 45-day-old C60-B14 design-Q is asking for

Routed as a **closure recommendation**, not a defect. Surfaced as the *inversion* of the refuted charge
— the evidence pointed the opposite way from the accusation.

- **C60-B14** ("anti-collusion / distinctness requirement") has been an open operator DESIGN-Q since
  `9d1933f8` **2026-06-15** (C60 §D L174; re-confirmed **still open** in C248's carry list, L41).
  The C61 remediation deliberately *routed* it rather than resolving it — `9d1933f8`'s own body says
  "Out of scope (routed, NOT touched): design-Q (… B14-anti-collusion …)".
- **The distinction B14 needs already exists in ISP's own §6**: cardinality is *structural* (§6.1 L322,
  satisfiable by one human with three keypairs) and independence is *semantic* (§6.2 items 1–2 L333,
  explicitly **not** satisfied by identical-twin keypairs). ISP even names the failure mode B14 is
  about.
- **Corroborating impl datapoint**: `#527` (`e8f313e4`, 2026-07-15) implements precisely the structural
  half (cardinality, no independence claim), and `verify_quorum` adds signature-validity on top —
  i.e. an independent implementer converged on ISP §6.1's split without citing it.
- **Routing**: operator DESIGN-Q bundle (C60-B14), with ISP §6.1/§6.2 named as the resolving text.
  **Auditor MUST NOT self-apply** — closing a design-Q is an operator act.
- **Severity argued both directions**: *up* — it can retire a 45-day-old open question at zero spec
  cost, and it is ISP's own section doing the work. *down* — it changes no byte, enforces nothing, and
  the LCT prose at L537 is already accurate as written. **INFO is correct.**

### Carries re-verified and STANDING (do NOT re-open as net-new)

| ID | Status at C290 | Basis |
|----|----------------|-------|
| B1, B2-full, B10, B11, B15 | **STAND** (operator DESIGN-Q) | target byte-frozen |
| B13 (→ SAL C58-B1) | **STANDS** | SAL frozen since 2026-07-14 |
| B12 / C174-N1 (LOW, two-language `validate_minimum_viable` bundle) | **HELD by construction** | `federation.py` frozen 2026-04-17; `society.rs`/`role.rs` frozen `fe96aad0` pre-C174; 0 in-window SDK commits |
| C174-N2 (INFO, `secede()`/`join_federation()` as bare field mutations) | **HELD by construction** | same freeze |
| C212-I1 | **RESOLVED at C250** (#538 plural `citizenships`) | do not re-open |
| C25-H1 | **RESOLVED downstream (C51)**, re-confirmed | §8 attributions intact |
| C6-L2 (Gesellian framing) | **deferred-carry persists** (expected) | §4.1 L197 informational |
| C60-B1 (vectors with <3 witnesses) | **CONFIRMED, 9 instances measured** | LCT-track carry; measurement contributed, ownership unchanged |

### Admitted-but-DEFERRED artifacts (written IN, per the N=3 cap — a cap in prose alone is silent truncation)

- `web4-trust-core/` — not gated this pass.
- `ledgers/reference/typescript/lct-document.ts` — not gated (LCT-track surface per C288).
- `web4-policy/` — not gated.
- Whitepaper surfaces (`whitepaper/`, `docs/whitepaper-web/`) — 29 in-window file-touches, not gated.
- `ledgers/act-chain/bridge/genesis_crypto.py`, `ledgers/reference/` beyond the ATP/witness files —
  M1-untested this pass.

---

## §D: Operator Asks / Routing

1. **N1 (INFO) → operator DESIGN-Q bundle, item C60-B14.** Recommendation: close B14 by citing ISP
   §6.1 L322 + §6.2 items 1–2 L333 as the governing structural-vs-semantic distinction, and (optionally)
   add a one-line pointer from LCT §537's parenthetical to ISP §6.2 so the disclaimer names where the
   semantic requirement *is* stated. **Not self-applied.**
2. **No spec mutation is owed by this pass.** ISP is byte-correct at 384 lines on every axis examined.
3. **Standing per-file guard for the ISP 8th delta (~C330)** — do NOT re-derive these:
   `hub/` is **M1-EXCLUDED for the ISP lineage** (published zero-hit greps above); `constellation.rs`
   is **not** an ISP mirror (0 vocabulary hits) and must not be re-proposed as a lead;
   `ledgers/act-chain/bridge/` is **M2-EXCLUDED** (and its ATP-genesis divergence is
   chronology-declined — the impl predates the §4.5 text); the ISP-cited attestation-envelope schema
   **PASSES** machine-validation against the SDK emitter (re-check only if either artifact moves);
   the birth-witness **distinctness** charge is **REFUTED** — do not resurrect.
4. **Honest floor statement, per the reviewer's advance ruling.** This pass's substantive output is
   *two exclusion rulings + one machine-validation pass + one closure recommendation + one refuted
   flagship*. That is the result, not a padded §B. An M2-FAIL artifact was **not** inflated into a
   defect to make the pass look productive, and the pass's own best finding was killed by its own
   target spec.

---

## Method notes carried forward

- **The "0 net-new" trap held again, and the trap's own remedy under-performed its advertisement.**
  Method carry v7 says a frozen target + frozen mirrors means the live surface is unread directories
  and published non-prose artifacts. Both were gated. Both were **negative**. That is a *correct*
  application producing a *null* result — worth recording, because three consecutive passes (C280,
  C284, C288) found a defect this way and a fourth null result is evidence about the *corpus*
  (ISP's implementer surface is genuinely thin), not about the method failing.
- **Baseline your own instrument, twice over.** This pass's *lead* was disjoint from the grep that
  justified it (`constellation.rs` = 0 hits), and its *measurement* globbed the wrong directory and
  returned a false zero. Both were caught — the first by the policy reviewer, the second by treating a
  suspicious zero as instrument failure. → [[feedback_enumeration_and_grep_hypotheses]]
- **A one-word equivocation can manufacture a HIGH.** "Distinct" meant *cardinality* in the impl and
  *independence* in the spec. The charge was built entirely on sliding between them, and the target
  spec's own §6.1 was the refutation. → [[feedback_refute_your_best_finding]]
- **Pre-registration works, and must be written not promised.** The reviewer refused a scope that
  merely *promised* to pre-register M1/M2/M3. Writing them first is what let this pass decline `hub/`
  and `ledgers/` without either verdict looking reverse-engineered — and what let it record a
  *correct* prediction without claiming credit for it.
