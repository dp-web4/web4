# C330: `inter-society-protocol.md` (ISP) 8th-delta RE-Audit

**Date**: 2026-08-07
**Track**: web4 (Legion autonomous session, slot `web4-20260807-060000`)
**Instrument**: C-series delta RE-audit; **8th delta** on `inter-society-protocol.md`
**Lineage** (located by reading the oldest pass's line-1 header, not by globbing `C*-<slug>*` — the
C326 rule): **C6** (`inter-society-protocol-internal-consistency-2026-05-21.md`, self-identifying as
`# C6:`) → C25 → **C62** → remediation **C63** (#341) → C102 → C136 → **C174** → C212 → C250 →
**C290** → this pass. **10 documents.**
**Source**: `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2 DRAFT, **384 lines**, blob
`22bf6c1d`, last edited `0405f331` 2026-06-16 — **BYTE-FROZEN 52 days**)
**Window**: `030d1681..HEAD` (C290 snapshot → `89251abc`) = **55 commits, 57 files**

**Result headline**: **0 net-new defects against the spec (9th consecutive clean ISP delta). ZERO
mutation. The pass's own spine was REFUTED by the rate test it pre-registered against itself. What
survives is one reach-escalation of an existing carry — delivered by the previous pass's deferral row —
and one LOW correction to that carry's stated basis. An adversarial verification then corrected four of
this pass's own claims, including the strength of its headline refutation; all four corrections are
published in place rather than quietly absorbed.**

---

## Summary

| Severity | NEW (C330) |
|----------|-----------:|
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | **1** (N1 — correction to C290's stated freeze-basis for C174-N1; conclusion unaffected) |
| INFO | **1** (N2 — decision-input loss, narrowed to a claim C90 does not already cover) |
| **Total NEW distinct defects vs. the spec** | **0** |
| Hypotheses REFUTED by pre-registered rule | **2** (the spine and its successor) |
| Carries reach-escalated | 1 (C174-N1 — third *documentation* surface, at the published npm boundary) |
| Deferrals discharged with a row | **5 of 5** — 4 negative (§C.2–C.5), 1 payout (§C.1) |
| Own instrument errors caught pre-write and published | **2** |
| Own claims corrected by adversarial verification, published in place | **4** (§B.3, §B.5, §C.1, §E) |

---

## §A. Freeze + carry verification at live HEAD

`git diff 0405f331 HEAD -- web4-standard/core-spec/inter-society-protocol.md` = **empty**.

**All six cited siblings unmoved since the C290 snapshot ⇒ 3rd CONSECUTIVE zero-mover delta**, so every
C212/C250 DISJOINT adjudication carries verbatim and nothing is re-litigated:

| Sibling | Last commit | Moved in window? |
|---|---|---|
| `atp-adp-cycle.md` | `256ab51d` 2026-07-07 | no |
| `mcp-protocol.md` | `3e765345` 2026-07-13 | no |
| `web4-society-authority-law.md` (SAL) | `1354e4c2` 2026-07-14 | no |
| `SOCIETY_SPECIFICATION.md` | `87377c38` 2026-07-14 | no |
| `society-roles.md` | `1354e4c2` 2026-07-14 | no |
| `LCT-linked-context-token.md` | `d89595e8` 2026-07-16 | no |

### A.1 — C63 remediations re-verified **by content**, not by line number

On a byte-frozen target these hold by construction, but each anchor was matched against a content
needle rather than read off a line number (v11):

| C62 ID | Line | Content needle matched | Status |
|---|---|---|---|
| B4 | L108 | `MAY update their own LCTs` | **HELD** |
| B5 | L239 | ``atp-adp-cycle.md` §2.1–§2.2`` | **HELD** |
| B3a | L368 | `MCP is the inter-society action protocol` | **HELD** |
| B3b | L377 | `architecture Normative` | **HELD** |
| B6 | L75 | ``≥3 required per `LCT-linked-context-token.md``` | **HELD** |
| B7 | L252 | `schemas/attestation-envelope-jsonld.schema.json` | **HELD** |
| B8 | L362 | `SAL §` | **HELD** |
| B9 | L115 | `formation events` | **HELD** |
| B14 | L45 | `Eurozone` | **HELD** |
| B16 | L369 | `society-roles.md` | **HELD** |
| B2-interim | L150 | `mcp-pro` | **HELD** |

**11/11 verified by content, 0 regressed.** `&#|&amp;|&lt;|&gt;` sweep on ISP: **0 hits, CLEAN.**

> **Own instrument error #1, caught pre-write and published.** The first run of this table displayed
> each line through `cut -c1-120` and reported **B5 and B7 as MISSING** — L239's `§2.1–§2.2` citation
> sits at ~column 250 and L252's schema path at ~column 240. A truncating *display* had become a
> *matcher*, and it very nearly manufactured a two-cell regression charge against a byte-frozen file.
> This is the same family the corpus already tracks — a predicate whose unit is not the claim's unit.
> Re-run with content matching: 11/11.

### A.2 — Anchor correction published in the current pass (never by rewriting C290)

C290 §C N1 and §D item 1 anchor ISP's semantic criteria at **"§6.2 items 1–2 L333"**. At HEAD
(and at C290's own snapshot — the file has not moved) item 1 is **L332** and item 2 is **L333**.

**Corrected anchor: ISP §6.1 L322 (exact, no change) + §6.2 items 1–2 L332–333.**

### A.3 — Standing carries re-verified

| ID | Status at C330 | Basis |
|---|---|---|
| B1, B2-full, B10, B11, B15 | **STAND** (operator DESIGN-Q) | target byte-frozen |
| B13 (→ SAL C58-B1) | **STANDS** | SAL frozen since 2026-07-14 |
| **B12 / C174-N1** (two-language `validate_minimum_viable`) | **HELD — but reach-escalated (§C.1) and its stated basis corrected (N1)** | see below |
| C174-N2 (`secede()`/`join_federation()` as bare field mutations) | **HELD** | `society.rs:264-278` frozen `fe96aad0` 2026-07-09 |
| C212-I1 | **RESOLVED at C250** (#538) | do not re-open |
| C25-H1 | **RESOLVED downstream (C51)** | §8 attributions intact |
| C6-L2 (Gesellian framing) | **deferred-carry persists** (expected) | §4.1 L197 informational |
| C60-B1 (vectors with <3 witnesses) | **CONFIRMED**, LCT-track carry | ownership unchanged |
| **C290-N1** (closure recommendation → C60-B14) | **STANDS, unconsumed** | see §B.4 |

---

## §B. SPINE — the hypothesis this pass was built on, and its refutation

### B.1 — What was hypothesised, and why

C290's only net-new output was **N1 (INFO)** — a *closure recommendation* for the LCT lineage's
`C60-B14` anti-collusion DESIGN-Q (open since 2026-06-15), arguing that ISP's own §6.1/§6.2 already
supply the structural-vs-semantic distinction B14 asks for. It was routed to the operator and
explicitly **not** self-applied.

Measured at HEAD: **`grep -rn "C290-N1"` over the whole repo, both audit trees, `.git` excluded =
0 files.** Eight days later **C328** (the LCT lineage's own 8th delta) re-listed `C60-B14-req` as an
open operator DESIGN-Q. The pass hypothesised a mechanism: **cross-lineage routed outputs are orphaned
at a higher rate than findings generally**, because routing is written into the *originating* pass's
§D while the owning lineage reads only its own documents.

### B.2 — The pre-registered rule (written into the approved scope before the instrument ran)

Let `n` = size of the cross-lineage set, `k` = how many are orphaned, `r = k/n`, `r0` = the corpus null.

- **`r ≤ r0` ⇒ REFUTED**, regardless of `n`; file the refutation as the pass's headline negative.
- `r > r0` but `n < 5` ⇒ LOW (underpowered).
- `n ≥ 5` **and** `r ≥ 0.50` ⇒ MEDIUM.
- otherwise ⇒ LOW.

**Discriminator, mechanical and re-runnable** (no auditor judgment): build a lineage map
`C### → slug` from `docs/audits/` filenames, **normalizing `-remediation-<date>` and
`-<n>th-delta-<date>` suffixes to the base slug** (without this, C109→`security-framework-remediation`
and C108→`security-framework` score as different lineages and inflate `n` with pure artifact). A
finding `C<N>-N<k>` is **cross-lineage** iff its body names at least one carry id `C<M>-<X>` where
`map[M] != map[N]`.

**Scope**: both audit trees (`docs/audits/` + `web4-standard/docs/audits/`); findings = headings
matching `^#{2,4}\s+\**(N\d+)\b` in docs named `C<N>-*`; **orphan** = the qualified id appears in
**0 other files**.

### B.3 — What it returned: **REFUTED, and pointing the other way**

| Quantity | Value |
|---|---|
| findings filed under an `N<k>` heading, both trees | **65** |
| `r0_all` — overall orphan rate | **0.400** (26/65) |
| **`r0_complement`** — orphan rate among findings **not** flagged cross-lineage | **0.415** (22/53) |
| `r_cross` — orphan rate among cross-lineage findings | **0.333** (4/12) |
| **delta vs the complement** | **−0.082** |

`r_cross (0.333) < r0_complement (0.415)` ⇒ **branch 1 fires. The hypothesis is REFUTED.** The
complement is the correct denominator precisely because the full-corpus null contains the tested subset
inside itself and biases the comparison toward "no difference"; both are published above.

**How strongly refuted: not very, and the honest statement is "underpowered, consistent with no
effect."** An adversarial verification of this section (commissioned against the pass's own best
finding) reproduced all four cells exactly and then attacked the inference, successfully:

- **Fisher exact, two-sided, `4/12` vs `22/53`: p = 0.749.** Wilson 95% CI on `r_cross` is
  **[0.138, 0.609]** — it contains `r0_complement = 0.415` comfortably. The delta is **0.54 SE**.
- **The sign is not robust to a free parameter the rule failed to fix.** §B.2 specifies the
  discriminator but never defines the *body window* over which carry-ids are counted. Varying only
  that: heading-only `−0.070` · heading+2 `0.000` · 6 lines `−0.019` · **12 lines `+0.065`** ·
  to-next-heading `−0.119`. **At a 12-line window the delta points the way the hypothesis
  predicted.** The pass's `n=12` is not reproducible under any single window the verifier tried.
- The successor (self-labelling) test is weaker still: **Fisher p = 1.000**.

**So the correct claim is the weaker one: the data do not support the hypothesis, and are equally
consistent with no effect in either direction.** The pre-registered rule was followed exactly — and
that is the point worth keeping: the rule fired against the pass, but a rule that leaves a free
parameter unfixed lets the *magnitude* float even when the *procedure* is clean. **Method carry
for the next pass: pre-register the window, not just the matcher.**

**Denominator caveat (publish-condition 3, and worse than the condition anticipated).** The heading
regex captures **65 of ~155** findings across the two trees. Widening to the bullet-qualified,
bullet-bare and heading-qualified conventions gives union `n=155, orphans 63, rate 0.406`, and the
**90 missed** findings orphan at `0.411` — **so the ~40% baseline is robust and this attack fails.**
But the regex misses *the entire modern era*: **0** findings from C280/C286/C288/C294/C296/C298/C300/
C312/C320/C322 are in the denominator, and **`C174-N1` — the carry at the centre of §C.1 and §E N1 —
is not a member of the population this section measured.** The rates are sound; the sample is not the
corpus, and no claim here should be read as one about the corpus's recent practice.

**Stated limitation of the discriminator** (publish-condition 3, as required): it flags findings that
*name* another lineage's carry id, which is broader than findings *routed to* another lineage. C290-N1
is a routed output; a finding merely citing a sibling carry as context is not, yet both score
cross-lineage. Tightening this is the next fire's to do, not this one's to assume.

**A successor hypothesis was tested and also refuted.** `C290-N1` is not even a member of the
discriminated orphan set — because **C290 never writes the string `C290-N1` at all** (`grep -c "C290-"`
on its own doc = **0**); it labels its finding `### N1` and refers to it as "N1 (INFO)". The successor
hypothesis was that findings whose own doc never writes the qualified id are more likely to be orphaned.

| | orphan rate |
|---|---|
| self-labelled (doc writes its own `C<N>-N<k>`) | 0.375 (3/8) |
| **not** self-labelled | 0.404 (23/57) |

A 2.9-point gap on `n=8` in the self-labelled arm. **Refuted.**

**Therefore `C290-N1` is a modal member of a corpus-wide ~40% baseline, not an exception.** The pass's
seed observation was true and unremarkable.

### B.4 — N2 (INFO): what survives, narrowed to a claim C90 does not already cover

**C90 is prior art and is cited as such.** `feedback_cross_doc_carry_inbound` (born C90) already holds
this mechanism: *read the sibling's own interval audit docs — carries routed back at this file live
outside it.* This pass discovered nothing about that mechanism.

The delta claimed, and nothing more: **the C90 discipline is stated as an obligation on the *reader*,
with no corresponding obligation on the *writer*.** A lineage cannot know which sibling passes happened
to name its carries, so "read your siblings' docs" is unbounded in practice; the cheap fix is on the
writing side, where the routing pass knows exactly which lineage it is addressing.

**C328 was CORRECT to re-list `C60-B14-req` as open, and correct to call it TRUE at HEAD.** C290-N1 is
a *recommendation*; C290 itself writes "Auditor MUST NOT self-apply — closing a design-Q is an operator
act." The operator never ruled, so the anti-collusion requirement is still absent from the spec — which
is exactly what C328's row asserts. No error is charged against C328, and none exists.

The surviving claim is only this: **the operator's decision queue lost an input.** An operator reading
C328 §F.2 sees `C60-B14-req` presented as an open question with no indication that a sibling lineage has
argued ISP §6.1 L322 + §6.2 L332–333 settles it. Nobody was wrong; the recommendation had no path.

**Withdrawn as false**: an earlier draft said the recommendation "survives only in this track's private
memory." It does not — C290 §C N1 and §D item 1 are **in the repo** at
`docs/audits/C290-inter-society-protocol-7th-delta-2026-07-30.md`. What is absent is any *pointer from
the LCT lineage's reading path* to that text.

**Routing**: ledger act, not a spec edit, and not this pass's to apply. Recorded in §E for the next LCT
delta (~C368) and for the operator alongside C60-B14.

### B.5 — Clustering: real, and then deflated by the pass that found it

The orphan set is not spread evenly; it clusters by document.

| Document | filed | orphaned | P(≥k \| p₀=0.40) |
|---|---:|---:|---:|
| `C80-multi-device-lct-binding-delta-audit-2026-06-21.md` | 8 | **7** | **0.0085** |
| `C90-mrh-tensors-2nd-delta-2026-06-24.md` | 4 | **4** | **0.0256** |
| `C302-web4-lct-7th-delta-2026-07-31.md` | 4 | 3 | 0.179 |
| `C36-multi-device-lct-binding-audit-2026-06-07.md` | 11 | 3 | 0.881 |

**Two deflations, both of which the pass applies to its own result:**

1. **These documents were selected by looking at the data, and the per-document p-values above are
   therefore illegitimate as cited.** **24** documents were scanned, not 7. Bonferroni-corrected:
   **C80 → 0.205, C90 → 0.614. Neither individual document survives**, and the two p-values must be
   read as a *ranking*, not as significance.

   **But the conclusion survives on a test this pass should have run instead, and did not.** At the
   family level: expected documents hitting p ≤ 0.05 by chance = **0.18**, observed = **2**, Poisson
   **P(≥2) = 0.0147**; over-dispersion **χ² = 40.11 on df = 24, p = 0.0208**. So *clustering exists*
   is supported; *C80 and C90 specifically are the clusters* is not established at the individual
   level. The distinction matters for §F.5's routing, which is why it is drawn here rather than
   quietly rounded off. (Found by the adversarial verification, not by the pass.)
2. **The instrument measures one channel among several, and demonstrably misses the others.** C90 —
   4 of 4 findings orphaned by id-citation — is the origin of `feedback_cross_doc_carry_inbound`, one of
   the most-applied method carries this track holds; its content propagated, its ids did not.
   `C158-N4` is tracked by name in this track's carry ledger while having **0** id-citations in either
   audit tree. **Orphaned-by-id ≠ unconsumed.**

Routed as a **forward guard, not a finding**: the C348 multi-device delta should check whether C80's
seven findings were consumed through some other channel or genuinely dropped. This pass does not claim
they were dropped.

---

## §C. Discharge of C290's five deferred artifacts (method carry v25)

C290's deferral row named five. **All five are discharged here with a row each, including the
NEGATIVEs, and each is discharged as written.** Matcher published once and used unchanged:

```
M = first.contact|secess|dissol|birth.witness|constituent|minimum.viable|inter-society|cross-society|federation|citizenship
scope: grep -rniE "$M" <dir>, excluding **/target/
```

### C.1 — `web4-trust-core/` → **M1-PASS, M2-PASS. THE PAYOUT: C174-N1 reaches the published npm boundary.**

**8 hits / 36 files.** `Cargo.toml` **and** `pyproject.toml` present ⇒ M2-PASS (a packaged, published
crate, not a script tree).

`web4-trust-core/src/bindings/wasm.rs` carries ISP subject matter to the **WASM/JS boundary**:

| Anchor | Surface | Kind |
|---|---|---|
| `wasm.rs:601-603` | `#[wasm_bindgen(js_name = validateMinimumViable)]` → `self.inner.validate_minimum_viable()` | **exported method** |
| `wasm.rs:647-648` | `"isFederation"` → `self.inner.is_federation()` | key inside the `summary()` object |
| `wasm.rs:652-653` | `"isConstituent"` → `self.inner.is_constituent()` | key inside the `summary()` object |

**Precision, because the first draft over-claimed**: only `validateMinimumViable` is a
`#[wasm_bindgen]`-exported *method*. `isFederation`/`isConstituent` are **keys inside the `JsValue`
that `summary()` returns** — JS-reachable, but only via `summary()`, not as bindings in their own
right. Backing impls: `web4-core/src/society.rs:225`, `:282`, `:287`. Python half:
`web4-standard/implementation/sdk/web4/role.py:341` (whose `:354` declares "Cross-language parity with
`web4-core/src/society.rs::validate_minimum_viable()`").

**Not dead code — verified at the shipped artifact, not the source.** `Cargo.toml` gates the `wasm`
feature off by default (`default = ["file-store"]`), so source presence proves nothing. The built
artifact settles it:

```
web4-trust-core/pkg/web4_trust_core.d.ts:315        validateMinimumViable(): any;
web4-trust-core/pkg/web4_trust_core_bg.wasm.d.ts:82 export const wasmsociety_validateMinimumViable
docs/proof/PUBLISHED.md:58                          npm install web4-trust-core
```

Compiled into the checked-in `.wasm`, typed in the shipped `.d.ts`, published to npm at 0.2.0.

**Routing, pre-registered before the run: REACH-ESCALATION of the existing carry C174-N1, NOT
net-new.** Adjudicate with C174-N1; do not re-file.

**What kind of face this is — narrowed.** Calling it a third *implementation* would be double-counting:
`wasm.rs` is a delegating shim with zero independent logic over `society.rs`. It escalates on **reach**,
and specifically on **documentation reach**: C174-N1's surviving content is a documentation gap, and
`pkg/web4_trust_core.d.ts:311-315` reproduces the bare Rust doc-comment verbatim at the npm boundary.
So it is a genuine third *documentation* surface — which is exactly the surface C174-N1's open remedy
(a docstring note on every parity site) is about.

Same shape as C328's `wasm.rs` finding on C288-N2: the same file is now the escalation surface for a
second lineage.

### C.2 — `ledgers/reference/typescript/lct-document.ts` → **discharged AS WRITTEN: not ISP's.**

8 hits, and reading them settles it: `:120`, `:410-414`, `:532`, `:682` are all `birth_witnesses`
(LCT birth-certificate shape — **C60-B1 territory, LCT-track**), and `:472` is `'lct:web4:society:federation'`
inside a doc-comment example string. C290 deferred this as "LCT-track surface per C288"; that ruling is
**confirmed by content, not inherited**. M2-FAIL (no `package.json`). **No ISP defect. Not re-filed.**

### C.3 — `web4-policy/` → **NEGATIVE gate for ISP.**

M2-PASS (`Cargo.toml`). **3 hits / 4 files, and all three are doc-comments about a different spec:**

```
web4-policy/src/lib.rs:161  /// citizenship suspend/terminate, LCT revocation, CRISIS halt) so law can cite
web4-policy/src/lib.rs:182  /// Kinetic: citizenship suspension (SOCIETY_SPECIFICATION §4.2).
web4-policy/src/lib.rs:186  /// Kinetic: citizenship termination (SOCIETY_SPECIFICATION §4.2).
```

All three cite **SOCIETY_SPECIFICATION §4.2**, i.e. SAL/society-lifecycle subject matter, not
inter-society protocol. Zero hits on `first.contact`, `secess`, `dissol`, `birth.witness`,
`constituent`, `minimum.viable`, `inter-society`, `cross-society`, `federation`.
**NEGATIVE, paths and matcher published above.** (C328 independently gated this crate NEGATIVE for the
LCT lineage; the two negatives are on different matchers and neither implies the other.)

### C.4 — Whitepaper surfaces → **evidence-not-mirror. No gate.**

64 hits across `whitepaper/` + `docs/whitepaper-web/`, but the distribution disqualifies it as a mirror:
**8 of 12 matching files are `whitepaper/archive/sections-2026-07-09-pre-rewrite/` or
`whitepaper/build/` derivatives**; the live normative-adjacent hits are two sections (`04-mcp`,
`05-rdf`) plus `PUBLISHER_CONTEXT.md`. The whitepaper is explanatory and makes no normative claim ISP
could contradict. **In-window touches: 1** (`PUBLISHER_CONTEXT.md`) — note this is *this* window;
C290's "29 file-touches" figure was for its own. **Admitted as evidence, excluded as a mirror.**

### C.5 — `ledgers/act-chain/bridge/genesis_crypto.py` + `ledgers/reference/` → **M2-EXCLUSION stands, with one correction.**

- `genesis_crypto.py`: **1 hit.** Nothing to gate. C290's `ledgers/act-chain/bridge/` M2-EXCLUSION
  (no `pyproject.toml`/`setup.py`, script-style relative imports) **re-confirmed** — verified, not
  inherited. Its ATP-genesis divergence remains **chronology-declined**; not re-charged.
- `ledgers/reference/`: 66 hits over 4 files. No `pyproject.toml`, `setup.py`, `Cargo.toml` or
  `package.json` at the tree root ⇒ M2-FAIL for the Python and TypeScript arms.
- **Correction to the exclusion's reach**: `ledgers/reference/go/go.mod` **exists**, so
  `ledgers/reference/go/lct/document.go` (3 subject-matter hits) is a *packaged* Go implementation and
  **passes C290's own M2 criterion**. The ISP lineage has never read it (`ledgers/reference/go` appears
  in 3 documents across both audit trees, none of them ISP's). **Not gated this pass** — it is named
  into the fresh C370 deferral row rather than silently dropped.

---

## §D. Re-running C290's `hub/` M1-exclusion at a tree that moved

C290 published the `hub/` exclusion as a **dated negative** (2026-07-30). **26 hub files moved in the
window**, so the measurement — not the ruling — was re-run.

**Routing pre-registered before the run**: if `hub/` now hits, that is reach-escalation of the existing
exclusion and re-dates it; it is **not** a net-new finding and **not** a reversal into a charge.

| C290's published matcher | C290 | C330 (HEAD) |
|---|---:|---:|
| `first.contact` | 0 | **0** |
| `secess` | 0 | **0** |
| `dissol` | 0 | **0** |
| `birth.witness` | 0 | **0** |
| `constituent` | 0 | **0** |
| `minimum.viable` | 1 | **1** (`.rs` scope — see below) |

**All five zero-hit greps still return 0. The M1 exclusion re-confirms on its own published matcher and
is re-dated 2026-08-07.**

> **Own instrument error #2, caught pre-write and published.** A first run widened the scope to
> `*.rs`, `*.md`, `*.toml` and returned `minimum.viable` = **4**, which was about to be published as
> "C290's cell changed, 1 → 4." Re-running the *same widened matcher at C290's own snapshot*
> (`git grep -ilE "minimum.viable" 030d1681 -- 'hub/*.rs' 'hub/*.md' 'hub/*.toml'`) also returns **4**;
> `.rs`-only returns **1** at both ends. **The count never changed — the scope did.** All four hits are
> one marketing tagline ("minimum-viable Web4 society for a community chapter") replicated across
> `Cargo.toml:11`, `README.md:3`, `docs/PRD.md:36`, `main.rs:33`, so C290's *ruling* (a doc-comment
> tagline, not an implementation of §6.2) is exactly right either way. This is the C326 rider paying
> out: a **named** matcher is not a **reproducible** one, and the fix is to re-run the disputed matcher
> at the prior snapshot before conceding — or charging — a cell.
>
> Anchor drift noted for the record: C290 cites the tagline at `main.rs:32`; at HEAD it is `main.rs:33`.

---

## §E. Findings

### N1 — LOW: C290's stated freeze-basis for C174-N1 names two files that are not loci, and omits the one that is

**The conclusion is unaffected. The basis is wrong, and it is wrong in a way the same document
disproves two sections earlier.**

C290 §C carry table:

> | B12 / C174-N1 (LOW, two-language `validate_minimum_viable` bundle) | **HELD by construction** |
> | `federation.py` frozen 2026-04-17; `society.rs`/`role.rs` frozen `fe96aad0` pre-C174; 0 in-window SDK commits |

Measured at HEAD, `grep -rn "validate_minimum_viable" --include=*.rs --include=*.py --include=*.ts`:

| File C290 cites as the basis | Is it a locus? |
|---|---|
| `web4-standard/implementation/sdk/web4/federation.py` | **No** — 0 occurrences |
| `web4-core/src/role.rs` | **No** — 0 occurrences |
| `web4-core/src/society.rs` | **Yes** — `:225` |
| `web4-standard/implementation/sdk/web4/role.py` | **Yes — `:341`, and C290 never names it** |

C290's own §B′ G3 published `minimum_viable` = **0** for `federation.py`. So the pass measured zero
occurrences of the mechanism in the file it then cited, two sections later, as the basis for holding
the carry.

**The carry is still HELD**, and this pass re-derives that independently rather than repairing the
citation and moving on: `role.py` frozen `d155b6a6` **2026-05-15**, `society.rs` frozen `fe96aad0`
**2026-07-09** — both predate C174 (2026-07-11), and neither moved in the window.

**"Plausibly a typo for `role.py`" was this pass's own first mitigation, and it is REFUTED.** Two
independent grounds:

1. **C290 attached the correct commit hash *for `role.rs`*.** `fe96aad0` (2026-07-09) is
   `web4-core/src/role.rs`'s actual commit, and was its HEAD at C290's date. A keystroke slip does not
   carry the right hash for the wrong file.
2. **The pairing is traceably inherited.** `C250:101` already tabulates
   ``society.rs` (`bootstrap`/…/`validate_minimum_viable`); `role.rs`` as a **mirror-artifact** row.
   C290 carried that row forward into a **locus** claim.

So this is a **mirror-set conflated with a locus-set, propagating across two passes** — not a typo.

**And the origin pass had it right.** `C62:163` names the cross-reference as *"SDK `role.py`
`validate_minimum_viable`"*. The correct Python locus was on the record at C62 and was lost by C290 —
the same forwarding-pointer decay this rotation has now filed five times over (v18/v24), here reaching
a *file path* rather than a carry id.

**Severity argued both ways.** *Up*: a freeze argument is only as good as the files it names; this one
names a 2-of-4 wrong set, the correct locus was available in the lineage's own origin pass, and a
future pass inheriting it re-verifies the wrong files and gets a true answer for a false reason.
*Down*: the conclusion is correct, and `society.rs` — the file C290 does name correctly — carries the
Rust half. With the typo mitigation gone the *down* leg rests on the conclusion alone. **LOW is still
correct** (nothing downstream acted on the wrong basis), but it is a thinner LOW than the first draft
claimed. Correction published here; C290 is **not** rewritten.

**First crack in the inherited basis, recorded now rather than when it bites**: C290's clause "0
in-window SDK commits" **has expired for one of the files it names** — `web4-core/src/role.rs` moved
in this window (`d43964e2`, 2026-08-05, *"a role's trust must accumulate per occupant"*). Harmless
here, because `role.rs` is not a locus of `validate_minimum_viable` (that is the finding). But four
passes have now re-inherited this freeze basis, and one of its named files is no longer frozen.

### N2 — INFO: the operator's decision queue lost an input (§B.4)

Filed at INFO, narrowed to the writer-side asymmetry that C90 does not cover, with C328 explicitly
exonerated. Full statement in §B.4. **Ledger act, not a spec edit; not self-applied.**

### Declined — routed as corroboration, NOT charged

Both `society.rs:225-262` and `role.py:341-392` implement ISP §6.2 items **1 and 2** plus
base-mandatory role completeness, and **not** item 3 (`ISP:336`, "Reified resource grounded
externally"). Both also test §6.2 item 2 by **role existence** (a `Witness` or `Auditor` role is
assigned), whereas §6.2 item 2 (`ISP:333`) requires *"independent judgment … Witnessing by an
identical-twin keypair does not satisfy this"* — **cardinality standing in for independence**, the
same equivocation that killed C290's flagship.

**This is not charged. The first draft gave the wrong reason, and the reason is corrected here rather
than dropped.**

- **Draft rationale, WITHDRAWN**: *"the implementations implement the structural half and say so."*
  **False for two of the three surfaces.** Only `role.py:349-352` discloses its partiality. The Rust
  carries no disclaimer at all — its entire doc comment is `/// Validate minimum viable society
  requirements.`, with no §6.2 citation — and its inline `// 1. / // 2. / // 3.` numbering manufactures
  a false 1:1 correspondence with §6.2's items, where the Rust's `// 3.` is a **different requirement**
  (SOCIETY_SPEC role completeness). The shipped `pkg/web4_trust_core.d.ts:311-315` inherits the bare
  comment verbatim. The Rust is the **published-crate** half and the one reached through npm, so the
  Python docstring cannot exonerate it.
- **Actual reason it is not charged**: it is **already carried**, twice. `C62-B12` states it verbatim —
  *"the SDK approximates item 2 as mere presence of a Witness/Auditor role — dropping the
  authority-difference and independent-judgment discriminators"* — and `C174:122` records the `// 3.`
  collision explicitly (*"a SOCIETY_SPEC §1.2 structural check, not an ISP §6.2 semantic one"*).
  **C174-N1's open remedy is "a docstring note on both parity sites"** — i.e. the missing Rust-side
  note *is* the remedy, not a new defect. `B12`/`C174-N1` is kept **OPEN and HELD** in §A.3 and §F.2.
- **And C62 already rejected the docstring defense this pass tried to use.** `C62` weighed
  `role.py`'s self-scoping and filed anyway: *"the SDK docstring also scopes itself to 'the
  role-structural side'. **Still** a documented spec↔SDK semantic gap worth a docstring note."*
  Re-running that defense two years of passes later, without naming C62-B12, would have quietly
  reversed an adjudication.

**Routing**: corroboration for C290-N1's closure recommendation on C60-B14 (a third implementer
converging on ISP §6.1's structural/semantic split), and a **reach note on C62-B12 / C174-N1** — the
gap now reaches the npm `.d.ts`. Not a new finding; do not re-file.

*(Every point in this passage came from the adversarial verification of the pass's own draft. The
draft's disposition was right and its argument was wrong, which is the failure mode a refuter catches
and a self-review does not.)*

---

## §F. Carry ledger for the ISP 9th delta (~C370)

### F.1 — Net-new this pass

| ID | Sev | Disposition |
|---|---|---|
| **C330-N1** | LOW | C290's C174-N1 freeze-basis correction. Conclusion HELD; basis corrected here. |
| **C330-N2** | INFO | Decision-input loss; C90 cited as prior art, writer-side asymmetry only. → operator, with C60-B14. |

*(Both ids are written in their qualified `C330-N<k>` form deliberately — §B.3 measured that 57 of 65
corpus findings are not, and that this does **not** predict orphaning. Self-labelling is done here
because it costs nothing and makes the row greppable, not because the pass claims it matters.)*

### F.2 — Carries STANDING, by name (v24: membership, not just a row)

`B1` · `B2-full` · `B10` · `B11` · `B15` (operator DESIGN-Q) · `B13` (→ SAL C58-B1) ·
**`B12`/`C174-N1`** (HELD, **reach-escalated to a third face**, basis corrected — §C.1, §E N1) ·
`C174-N2` (HELD) · `C6-L2` (deferred-carry, expected) · `C60-B1` (LCT-track) ·
**`C290-N1`** (STANDS, unconsumed — §B.4).
**Closed/resolved, do not re-open:** `C212-I1` (at C250) · `C25-H1` (at C51).
**Row count: 11 standing + 2 closed.**

### F.3 — Swept clean this pass; check only whether they CHANGED, do not re-derive

- `hub/` M1-exclusion — **re-dated 2026-08-07**, all five published greps still 0 (§D).
- `web4-policy/` — **NEGATIVE for ISP**, matcher and paths published (§C.3).
- `ledgers/reference/typescript/lct-document.ts` — LCT-track, confirmed by content (§C.2).
- `ledgers/act-chain/bridge/` — M2-EXCLUSION re-confirmed; ATP-genesis divergence still
  chronology-declined (§C.5).
- Whitepaper surfaces — evidence-not-mirror (§C.4).
- `constellation.rs` — **not** an ISP mirror (C290). Do not re-propose.
- The birth-witness **distinctness** charge — **REFUTED at C290.** Do not resurrect.

### F.4 — FRESH DEFERRAL ROW, pre-registered for C370

C330 discharged all five of C290's deferrals, which would leave the 9th delta's highest-yield instrument
empty. Named in advance, not backfilled:

1. **`ledgers/reference/go/lct/document.go`** — packaged (`ledgers/reference/go/go.mod` exists ⇒ passes
   C290's own M2 criterion), 3 subject-matter hits, **never read by this lineage**; appears in 3 docs
   across both audit trees, none of them ISP's. The highest-value member.
2. **`web4-trust-core/` beyond `wasm.rs`** — 36 files; only the bindings module was gated here (§C.1).
3. **`ledgers/reference/python/governance_audit.py`** and **`go/lct/document_test.go`** — inside the
   M2-FAIL Python arm and the M2-PASS Go arm respectively; the split needs a per-arm ruling, not a
   tree-level one.
4. **ISP's own published non-prose artifacts beyond the one schema C290 machine-validated** — the
   lineage has validated `schemas/attestation-envelope-jsonld.schema.json` and nothing else.
5. **`web4-standard/test-vectors/federation/sal-governance.json`** — executed once, by C326, from the
   SAL lineage. Never read from the ISP side despite `federation/` naming.
6. **The finding-id census, re-run over the UNION convention** — §B.3's heading regex captured **65 of
   ~155** findings and misses every finding filed by C280–C322. Any future claim about corpus-wide
   citation practice must run on the union (`n=155`), not on this pass's sample.

**Cap that produced this list**: this pass gated one group (`web4-trust-core/src/bindings/`) at depth
and characterised the other four by matcher only. That is the truncation, stated rather than implied.

### F.5 — Cross-track / operator routing

- **`#641` = STANDING BLOCK DESPITE TOOL-CLEAR.** `private-context/tools/pr_standing_blocks.py web4
  641` reports `CLEAR` because the block comment predates the current head. **The block's three asks are
  unaddressed**: `git diff 2ada8bb8..8c6a8438 --stat` = `whitepaper/PUBLISHER_CONTEXT.md | 17 +++++++`
  — **17 insertions, 0 deletions**, and a zero-deletion diff cannot have *corrected* an existing cell;
  `git grep "9 loci\|markup-blind\|14-references:67\|10-composed-architecture:22"` at the new head =
  **0 hits**. Recorded here so the next fire's step 0.5 is not misled by its own instrument.
  **Not fixed here** — #641 is the CBP Publisher track's in-flight branch.
- **Tool defect → operator.** `pr_standing_blocks.py`'s staleness rule (block older than head ⇒
  informational) is correct for *rebased/amended* heads and wrong for *appended* ones. This is the
  **third** failure of block-surfacing and the **first in the purpose-built tool**: `reviewDecision`
  hid #589/#590, then hid #641, and this tool was built as the answer to both. The fix needs a design
  decision about what a stale block should report; not taken as an audit-fire side effect.
- **C174-N1 reach-escalation** (§C.1) → adjudicate with the existing carry; `wasm.rs` is now the
  escalation surface for **two** lineages (this one and C288-N2 via C328).
- **C330-N2 + C290-N1** → operator, alongside C60-B14.
- **C348 (multi-device)** → forward guard: check whether C80's 7 orphaned-by-id findings were consumed
  through another channel (§B.5). This pass does **not** claim they were dropped — and per §B.5, C80's
  individual p-value does **not** survive Bonferroni (0.205). What survives is *clustering exists*
  (family-level p ≈ 0.015), not *C80 is a cluster*. Route accordingly.
- **`web4-core/src/role.rs` moved in-window** (`d43964e2`, 2026-08-05), so C290's "0 in-window SDK
  commits" clause has expired for one file it names (§E N1). Not a defect here; a freeze basis four
  passes have re-inherited now has one unfrozen member.
- **C62-B12 gains reach, does not gain truth** — the structural-for-semantic substitution C62 filed
  now reaches the published npm `.d.ts` (§E "Declined"). Adjudicate with C174-N1, whose open remedy
  already covers it.

---

## §G. Post-write re-runs at a different scope (v17)

Every count above was re-run after the prose was written, at a scope different from the drafting scope.

| Cell | Draft scope | Re-run scope | Agreed? |
|---|---|---|---|
| orphan census (65 / 26 / 0.400) | `docs/audits/` | both trees unified | **yes** |
| `r_cross` 4/12 | pre-normalization slug map | with `-remediation-`/`-Nth-delta-` normalization | **yes** (normalization changed the map, not this cell) |
| `hub/` five greps | `hub/**` `.rs .md .toml` | `git grep` at `030d1681` **and** HEAD, `.rs`-only | **no → §D instrument error #2** |
| C63 anchors | `sed` + `cut -c1-120` | content-needle match | **no → §A instrument error #1** |
| `validate_minimum_viable` loci | `--include=*.rs` | `*.rs *.py *.ts`, whole repo | **yes** |

**Two of five disagreed, and both disagreements were real instrument failures rather than real
findings.** Both are published in place rather than silently corrected. This is the ratio the method
predicts and the reason the re-run is not optional.

**Row-count check (v21):** §F.2 names **11 standing + 2 closed = 13** ids; C290's carry table carried
**8 rows** covering the same set plus the two this pass adds. No id present in C290 is absent here.

---

## §H. Lessons

- **A pre-registered rule is only worth writing if it can fire against you, and this one did — twice.**
  The spine was refuted on the correct denominator, and the successor hypothesis raised to replace it
  was refuted too. The honest output of this pass is a negative result about the corpus: **orphaning by
  id-citation runs at ~40% baseline and is not explained by cross-lineage routing or by self-labelling.**
  The reviewer's demand that the null be computed over the *complement* rather than the full corpus is
  what made the test sharp; against `r0_all` the delta would have been −0.067 and against
  `r0_complement` it is −0.082, but the reasoning only becomes valid on the complement.
- **NEW METHOD CARRY — pre-register the WINDOW, not just the matcher.** §B.2 fixed the discriminator
  and the severity thresholds and still left one free parameter unnamed: the *body* over which
  carry-ids are counted. Sweeping only that parameter moves the headline delta from `−0.119` to
  `+0.065` — **the sign flips**, and with it the pass's entire verdict. A pre-registration that fixes
  the rule but not the window is a pre-registration of the *procedure* with the *result* still free.
  Every future rate test on this track states its window in the same breath as its matcher.
- **The refuter's job is the argument, not the arithmetic.** All four of §B.3's cells reproduced
  exactly; every correction the adversarial pass landed was to an *inference* built on correct
  numbers — "not narrowly" on p = 0.749, two post-hoc binomials over 24 scanned documents, "and say
  so" for a disclaimer only one of three surfaces carries, and a typo mitigation refuted by a commit
  hash. **A pass that checks its numbers and not its reasoning will pass its own review every time.**
- **The measurement that kills your hypothesis often hands you the real one.** `C290-N1` was absent
  from the orphan set not because it was cited but because **the id was never written**. That produced
  the successor hypothesis — which then also failed. Both failures are more informative than the
  finding would have been.
- **`grep -c` on a directory is a claim about a scope, and the scope is the part that drifts.** §D's
  `minimum.viable` "1 → 4" was entirely a scope widening; re-running the *same widened matcher at the
  prior snapshot* returned 4 there too. Re-run the disputed matcher at the prior commit before charging
  or conceding a cell.
- **A truncating display is a matcher.** `cut -c1-120` nearly produced a two-cell regression charge
  against a byte-frozen file whose relevant content sat at column ~250.
- **v25's deferral row paid out for the second consecutive pass, and in the same file.**
  `web4-trust-core/src/bindings/wasm.rs` was deferred ungated by C290, and it is where this pass's only
  substantive carry movement was. C328 found its own escalation in the same file **earlier the same
  morning** (`89251abc`, 04:09 — this branch's own parent commit, from the LCT lineage, on C288-N2).
  **A file that two lineages
  independently escalate into on the same day is worth the operator's attention more than either
  escalation is on its own** — and neither pass could have seen the other's, which is the same
  writer-side blindness §B.4 files at INFO.

---

## Review-gate block

```
surface: C330 audit document (docs/audits/)   act: publish audit findings + carry ledger; no state mutation
S: low/reversible [construct: markdown document, zero executable surface, zero spec bytes changed]
R: n/a [construct: no caller-driven path created]      W: n/a [construct: no identity or authority asserted]
O: pass [construct: policy review APPROVED before any write; pre-registered severity rule + §D flip-routing
   both written into the approved scope BEFORE the instruments ran]
A: pass [construct: every count published with its matcher, scope and commit; both instrument failures
   published in place (§A.1, §D) rather than silently corrected; §G re-run table commits with the findings]
V: present [construct: pre-registered branch 1 (r <= r0 => REFUTED) fired against the pass's own spine;
   adversarial refutation commissioned against every surviving row]
verdict: PASS
```
