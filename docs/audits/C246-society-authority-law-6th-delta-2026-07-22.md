# C246: web4-society-authority-law.md (SAL) — Sixth Delta Re-Audit

**Date**: 2026-07-22
**Auditor**: Autonomous session (legion-web4-20260722-000036)
**Document**: `web4-standard/core-spec/web4-society-authority-law.md` (SAL, 419 lines, blob `0849ebbe`)
**Prior audit**: C208 (`docs/audits/C208-society-authority-law-5th-delta-2026-07-17.md`, merged #536)
**Prior remediation**: C59 / PR #330 (`0d756773`).

**Lineage**: C16 → C21 → C23 → C58 → C98 → C134 → C170 → C208 → **C246**.

**Framing**: **SAL has returned to byte-frozen** after its one-time move at C208. It grew 408→419 via **PR #523** (`1354e4c2`, the W4IP N2 Effector registration) between C170 and C208; since then **zero commits have touched it** (`git diff 1354e4c2..HEAD -- <SAL>` = empty; blob `0849ebbe` verbatim at HEAD `5e921125`). So this delta re-inherits the frozen-target discipline: §A is a construction-verify of the C59 remediation and every standing carry, and §B is a **corpus-delta regression sweep** of the movers landed since the C208 audit (`fa1ced86..HEAD`) against the SAL surfaces they could disturb — read each mover's rationale, resolve every SAL citation at live HEAD, refute-by-default on the strongest candidate, re-derive the live SDK/consumer mirror (method guard — the mirror is not a fixed set).

**The delta (ground truth)**: `git diff 1354e4c2..HEAD -- <SAL>` = **empty**. SAL is byte-identical to its C208 snapshot. No hunks, no line moves, no encoding artifacts (`grep -nE '&#|&amp;|â€|Â ' <SAL>` = empty).

**Counts**:
- **§A**: C59-rem **10/10 HELD** by construction (SAL byte-frozen since #523; the diff read at C208 already earned the 10/10 against the additive mover, and nothing has moved since). 0 regressed, 0 encoding artifacts, `hasEffector`/`respondedBy` grep-count still = 1 each. All standing carries re-verified OPEN against live-HEAD referents.
- **§B**: **0 net-new defects on SAL — 5th consecutive fully-clean SAL delta** (C98 + C134 + C170 + C208 + C246). Five corpus movers landed in-window; each is **regression-CLEAN vs SAL**: `#541` (reputation §4 note) left SAL §5.6's cited anchors byte-unmoved; `4f76f110` (oracle-scope on `Scope`) is data-plane "oracle", disjoint from SAL's Law Oracle role and SAL's `web4:` triple family; `#544` (`authority_ratchet`) is a faithful LCT-layer assurance primitive beneath SAL §4's abstract "witness thresholds" (SAL has no ratchet concept — positive convergence + one forward-note, **C246-N1**); `#538` (citizenship/birth-cert) is faithful to SAL's ledger-resident model (§2.1 L42 / §3.4) and **refreshes the open C23-H1 birth-cert-shape design-Q** with a 4th representation leg + a dp ruling (carry update, NOT net-new). web4-policy / `society.rs` / `ledger.rs` are **frozen since C208** → the C208 §B.3 impl-convergence findings STAND.
- **§C**: **ZERO autonomous-actionable, ZERO SAL/spec mutation.** C170-N1 (the `CLAUDE.md` glossary-path fix) was applied and CLOSED at C208; no guidance-file defect surfaced this turn. C246-N1 (ratchet forward-note) and the C23-H1 refresh route to the standing operator memo; every DESIGN-Q / cross-track carry STANDS.

---

## §A. Prior-Finding Verification (live evidence at frozen HEAD `0849ebbe`)

### A.1 — C59 remediation #330 HELD (10/10) by construction

SAL is byte-frozen since #523 (`1354e4c2`); HEAD blob `0849ebbe` is byte-identical to the C208 snapshot. The C208 audit earned the 10/10 by reading the additive #523 diff and confirming every C59-remediated anchor sits outside both hunks and is byte-unchanged. Nothing has moved since, so the 10/10 holds by construction. Regression sweeps at live HEAD: `grep -nE '&#|&amp;|â€|Â '` → empty; `web4:hasEffector` and `web4:respondedBy` each grep-count = 1 (no duplication/malformation). The C98 site-table stands verbatim.

### A.2 — Standing carries re-verified OPEN against live referents

Every SAL-side section that any carry anchors to is byte-frozen since #523. The **live sides** were re-checked at HEAD:

| Carry | SAL side | Live-side re-check at HEAD | Verdict |
|---|---|---|---|
| **C58-B10 / B15** (§3.6 dormant-defer ↔ SMS §4.1 new_citizen wake) | §3.6 frozen | `SOCIETY_METABOLIC_STATES.md` **0 commits** in-window (frozen since C55); two-sided contradiction intact | **STANDS — do NOT re-open** (dual-anchored) |
| **B15** (law-composition: §3.5 child-override-ranked vs SOCIETY_SPEC §3.2.1 extend-not-contradict vs role-extension strictest-wins) | §3.5 frozen | `role-extension-schema.md` **0 commits** in-window | **STANDS** — three competing models, one operator answer |
| **C16-M8 / B6** (§7.2 `ontology#` hash vs `hub-law.ttl` `ontology/` slash; SAL triple-family ontology absence) | §7.2 frozen | see §B.2 — SAL §7.1/§7.1.1 triple family **still 100% absent** from the ontology set after `role-extension.ttl` moved (`4f76f110`); no `sal-ontology.ttl` | **STANDS** |
| **C23-H1** (birth-cert shape N-way divergence) | §2.2/§2.3 frozen | **premise changed** — `#538` adds a web4-core `BirthCertificate`/`CitizenshipRecord` struct; see §B.4 | **STANDS — carry REFRESHED** (was "no new struct in-window" at C208; now 4 legs + dp ledger/plural ruling) |
| **C33** (`lct:web4:` example strings, typed-path vs key-derived) | §2.2/§5.5/§14 frozen | `lct.rs` key-derived pick unchanged in-window on this facet | **STANDS** |
| all other C16/C23/C58 design-Q + cross-track | frozen | referents frozen | **STAND** per the C208 §A.2 table |

Zero mirror drift on the pre-existing surface; all C98/C134/C170/C208 convergence results stand.

---

## §B. Corpus-Delta Regression Sweep (`fa1ced86..HEAD`)

**Method**: the corpus-delta window since the C208 audit commit (`fa1ced86`) was enumerated over `web4-standard/`, `web4-core/`, `web4-policy/`, and the SDK. Five real movers touch a surface SAL cites or that could mirror SAL; each was read for rationale, then adjudicated spec-vs-impl (route off-spec, never unilateral SAL mutation — SAL is frozen and every open item is operator/W4IP-gated). The SDK/consumer mirror was re-derived at live HEAD (not treated as a fixed set).

### B.1 — `#541` reputation §4 note: SAL §5.6's cited anchors byte-unmoved — 0 net-new

SAL §5.6 (Effector) cites `reputation-computation.md §4` "Coercive/Extractive Behavior Rules" as the recognition-evidence source. `#541` (via C214, `2bc3bafb`) added a §4 note to `reputation-computation.md`. Re-grep at live HEAD: the heading `#### Coercive/Extractive Behavior Rules` is at **L339** and `…recognition-evidence that any *response* to a coercive act must` is at **L387** — the **exact line anchors C208 §B.1 cited**. The note landed elsewhere in §4 and did not displace either anchor. SAL §5.6's citation **resolves exactly**, unchanged from C208. Clean.

### B.2 — `4f76f110` oracle-scope on `RoleExtension::Scope`: data-plane oracle, disjoint — 0 net-new

`4f76f110` ("oracle consult/write sets on Scope — Piece B for oracle-scope gating") added `scope.oracle_consult_set` / `scope.oracle_write_set` to the Rust `RoleExtension::Scope` and `role:oracleConsultSet` / `role:oracleWriteSet` to `role-extension.ttl`. Two adjudications:
1. **Sense of "oracle" is data-plane, not SAL's Law Oracle.** The commit is explicit — "memory-as-oracles … the oracle plane", read/write **membrane** sets a role may consult/store-to, gated by static reputation-blind set membership. This is a *lexical collision* with SAL §5.3's **Law Oracle** governance role (publishes law datasets, signs interpretations) — the identical collision class already ledgered for `RoleExtension::Scope` at acp-C234 and metabolic-C244. No SAL Law Oracle referent is touched. `grep -inE 'effector|law.?oracle|hasEffector|authority-law|society-authority'` over the full `4f76f110` diff = **empty**.
2. **Ontology facet is disjoint from the SAL triple family.** `role-extension.ttl` gained `role:oracleConsultSet` / `role:oracleWriteSet` (domain `role:Scope`, `role:` namespace). These are NOT SAL `web4:` triples. The SAL §7.1/§7.1.1 triple family (`hasWitness … hasEffector`, `respondedBy`, `adjustedBy`, `recordsOn`, `attestedBy`, `hasLawOracle`, `hasAuthority`, `memberOf`) remains **100% absent** across the entire canonical ontology set (`grep -rnE` over `web4-standard/ontology/` = empty), and no `sal-ontology.ttl` exists (`hub-law.ttl`, `role-extension.ttl`, `t3v3-ontology.ttl`, `web4-core-ontology.ttl` only). The C16-M8/B6 ontology-absence facet **HOLDS unchanged** — `4f76f110` widened the *role-extension* vocabulary, not the SAL triple vocabulary. Disjoint.

### B.3 — `#544` `authority_ratchet`: faithful LCT-layer assurance primitive beneath SAL §4 — 0 net-new; forward-note C246-N1

`#544` (`2ec6ae09`) added `RoleReference.authority_ratchet: Option<RatchetRequirement>` to `web4-core/src/lct.rs` (field docs L173–180), backed by `web4-core/src/ratchet.rs`. Its subject overlaps SAL's domain — `ratchet.rs` describes "the monotone … requirement for exercising **sovereign authority** (amend law, confer birth cert…)". Adjudication:

- **SAL has no ratchet/sovereign-bar concept.** `grep -niE 'ratchet|sovereign'` over SAL = **empty**. SAL's authority model is a *role/law structure* (§3.1 Authority Role as delegation-tree root, §5.2 Authority scopes/delegation, §4.2 L173 "New law versions **MUST** be attested by quorum; roll-forward requires `hasAuthority` + witness thresholds"). It is deliberately abstract.
- **The ratchet is the assurance layer beneath that abstraction, not a mirror of it.** `RatchetRequirement` is a *bar an evaluator holds* (min distinct sovereign occupants, device/biometric assurance) — one concrete realization of SAL §4's abstract "witness thresholds"/assurance requirement. It is carried on the `role:sovereign` LCT as **"Inspectable evidence (LCT spec §1.2), never a verdict"** — i.e. it lives in the LCT/ratchet layer producing checkable evidence, exactly the LCT §1.2 discipline (do not encode a universal trust verdict). It neither restates nor contradicts any SAL MUST.
- **Verdict: positive convergence, not a defect.** The ratchet faithfully implements an assurance mechanism *under* SAL's abstract authority-amendment requirement — the same shape as C240's `web4-policy` finding (faithful impl corroborates the spec, not a divergence). **C246-N1 (LOW, forward-note, route — do NOT self-apply):** if the operator/W4IP wants SAL §5.2 (Authority) or §4.2 (law amendment) to eventually *name* the society ratchet as its assurance mechanism (making the sovereign-authority bar a first-class SAL concept rather than an unnamed "witness threshold"), that is a normative SAL extension for the W4IP track — analogous-but-inverted to C208 §B.3's "role-side obligations have no impl mirror yet" (there the spec led the impl; here an impl governance primitive has landed that the spec does not yet name). SAL is frozen and correct as an abstraction; no edit this turn.

### B.4 — `#538` citizenship/birth-cert: faithful to SAL ledger model; REFRESHES the open C23-H1 design-Q — 0 net-new

`#538` (`0e997079`, "citizenship as a tamper-evident ledger reference, plural") reshaped the birth-certificate schema in `web4-core` per dp's 2026-07-16 ruling: added `CitizenshipRecord { certificate: BirthCertificate, attestations: Vec<Attestation> }` (the authoritative **ledger** content) + `BirthCertificateRef { issuing_society, entry_id, entry_hash }` (the tamper-evident pointer carried on the LCT), with `content_hash()` and a fail-closed `verify_quorum()` (≥3 distinct `Existence` attestations; every declared witness must be present). Adjudication:

1. **Faithful to SAL, not contradictory.** dp's ruling ("the cert lives in the society's **LEDGER**, not on the LCT") *matches* SAL directly: §2.1 L42 already mandates "Store the pairing and certificate on the society's **ledger**", and §3.4 (Immutable Record — **MUST**) already stores Birth Certificates in the ledger. `verify_quorum()`'s ≥3-distinct-witness bar realizes SAL §2.3 / §5.4's "witness co-signatures meeting the society's quorum policy". `grep -inE 'society-authority|SAL|Citizen role|§5\.1|§3\.4|authority-law'` over the `#538` diff = empty (it cites no SAL section, but its behavior is SAL-consistent). No SAL MUST is violated.
2. **The C23-H1 carry premise has changed — refresh, not net-new.** C23-H1 is the deferred, operator-gated "canonical birth-cert shape" design-Q, whose divergence map at C58 held **three legs**: SAL §2.2 `Web4BirthCertificate` JSON-LD (camelCase), the LCT-spec leg (`birth_context`/`genesis_block_hash`, RECOMMENDED), and the SDK `lct.py` snake_case dataclass. C208 recorded C23-H1 as STANDS *specifically because there was "no new birth-cert struct in-window."* **That premise no longer holds** — `#538`/`#527` add a **4th representation leg**: the web4-core Rust `BirthCertificate`/`CitizenshipRecord`, plus two authoritative dp rulings (cert lives in the ledger; citizenship is **plural** for multi-society membership). This *widens* C23-H1's divergence map and adds decision-relevant data (the ledger-resident + plural rulings), but it does **not resolve** it — SAL §2.2 remains byte-frozen with the old inline shape, still un-reconciled with the Rust struct. Routed as a **C23-H1 carry REFRESH** to the operator memo; NOT net-new (the design-Q predates this window) and NOT self-applied (SAL frozen; normative reconciliation is operator/W4IP-gated).
3. **The ≥3-quorum-vs-§2.2-example facet re-surfaces, subsumed.** `BIRTH_WITNESS_QUORUM = 3` gives a concrete impl to the long-noted tension that SAL §2.2's example lists only **2** witnesses (`witness:1`, `witness:2`) — the `bc-example-two-witnesses-violates-quorum-3` facet the C58 audit already subsumed under C23-H1/B14. Refreshed by a concrete impl datapoint; still subsumed; not net-new.

### B.5 — SDK/consumer mirror re-derived at live HEAD: frozen — C208 §B.3 findings STAND

Per the method guard the mirror was re-derived, not assumed:
- **`web4-policy/src/lib.rs`**: **0 commits** in-window (frozen since #525/C208). The `Response` enum (`Notice|Quarantine|Correct|Rehabilitate` + kinetic `Slash|Suspend|Revoke|Terminate|Halt`, `consequence_class()`, parse-don't-enact contract, tests) that C208 §B.3 found faithfully deploys SAL §5.6's cited `hub-law-schema.md` vocabulary is byte-unchanged. **C208 §B.3 positive-convergence finding STANDS.**
- **`web4-core/src/society.rs`, `web4-core/src/ledger.rs`**: **0 commits** in-window. No new SAL-role/law mirror; no `Effector` role struct, RWOA+S+V+F gate, Enactment Transcript, or `hasEffector`/`respondedBy` triples have appeared. The C208 §B.3 role-side impl-lag note (Effector role-side obligations still have no impl mirror) **STANDS** — expected for a still-young W4IP role.

---

## §C. Autonomous / Design-Q / Cross-Track Split

**Autonomous-actionable — NONE this turn.** SAL and its spec siblings are clean; unlike C208 (which found and closed the `CLAUDE.md` glossary-path fix C170-N1), no guidance-file or non-normative defect surfaced. **Zero SAL / spec / guidance mutation.**

**Carry updates recorded this turn (all route to the standing operator memo; none self-applied):**
- **C246-N1 (NEW, LOW, forward-note)**: `#544` `authority_ratchet` is a faithful LCT-layer sovereign-authority assurance primitive with no named referent in SAL. Forward question for W4IP: should SAL §5.2 / §4.2 eventually name the society ratchet as the assurance mechanism for exercising/amending authority? SAL is correct as an abstraction today; route, do NOT self-apply.
- **C23-H1 REFRESH**: `#538`/`#527` add a 4th birth-cert representation leg (web4-core Rust `BirthCertificate`/`CitizenshipRecord`) + dp rulings (ledger-resident, plural). The design-Q is *widened and better-informed*, still OPEN, still un-reconciled with the frozen SAL §2.2 shape. The C208 "no new struct in-window" premise is retired.
- **C16-M8/B6**: SAL §7.1/§7.1.1 triple family still 100% absent from the ontology after `role-extension.ttl` moved (`4f76f110` added only `role:` predicates). Absence class unchanged; not incremented.
- **C58-B10/B15, B15 law-composition, C33**: all SAL-side sections frozen and all live referents frozen in-window; carries STAND verbatim (do NOT re-open the §3.6 dual-anchor — two-sided-open, SMS side frozen since C55).

**Cross-track / positive movements logged (route, no SAL action):**
- `#544` authority_ratchet → positive convergence (assurance layer beneath SAL §4); C246-N1 forward-note above.
- `#538` citizenship → faithful to SAL §2.1/§3.4 ledger model; C23-H1 refresh above.
- `#541`, `4f76f110`, web4-policy/society.rs/ledger.rs → clean/disjoint/frozen as adjudicated in §B.

---

## §D. Lessons

1. **A frozen target still owns its carries' *premises*, not just their anchors.** SAL didn't move, and its cited anchors didn't move — but C23-H1's standing status at C208 rested on an implicit premise ("no new birth-cert struct in-window") that a corpus mover (`#538`) silently invalidated. The delta's highest-value finding was not a defect but a **premise retirement**: the carry still STANDS, yet its divergence map and its "is this resolvable now?" calculus both changed. Re-audits must re-test each carry's *stated premise* against the window, not merely re-confirm its anchor is frozen. (Cf. the snapshot-presence guard and "is it NEW before is it TRUE".)
2. **"Impl has a governance primitive the spec doesn't name" is a forward-note, not a defect — and it is the inverse of C208's.** C208 §B.3 logged "the spec's new role has no impl mirror yet"; C246 §B.3 logs the mirror image — `authority_ratchet` is a governance primitive the impl has that SAL does not yet name. Both are routed cross-track notes, neither is a spec defect, because a spec correctly staying abstract (SAL §4 "witness thresholds") is not a gap merely because an implementation realized the abstraction concretely. The direction (does the abstraction *want* to name its realization?) is a W4IP call, not an auditor's edit.
3. **Re-derive the mirror even when you expect it frozen.** `web4-policy`, `society.rs`, and `ledger.rs` were all frozen — but confirming that at live HEAD (0 commits in-window) is what lets C208 §B.3's convergence/impl-lag findings be carried by evidence rather than by memory. The mirror being a fixed set this turn is a *result*, not an assumption.

---

*End of C246 audit. Zero SAL/spec/guidance mutation. SAL byte-frozen since #523 (`0849ebbe`, 419 lines); 5th consecutive fully-clean SAL delta (C98+C134+C170+C208+C246). New: C246-N1 (LOW, `#544` ratchet forward-note, route) + C23-H1 premise refresh (`#538` 4th birth-cert leg, route). All prior carries STAND. Next rotation target: +2 from SAL per the fixed order → **C248 = LCT-linked-context-token.md** (lineage C9→C24→C60→C100→C135→C172→C210→C248). SAL's next delta (~C284) re-checks whether the Effector/ratchet acquire a spec-named referent and whether `sal-ontology.ttl` ever lands.*
