# C23: web4-society-authority-law.md (SAL) Internal Consistency RE-Audit

**Date**: 2026-05-30
**Auditor**: Autonomous session (legion-web4-20260530-180057)
**Document**: `web4-standard/core-spec/web4-society-authority-law.md` (396 lines, HEAD `252e77bd`)
**Prior audit**: C16 (`docs/audits/sal-internal-consistency-2026-05-27.md`, 2026-05-27)
**Spec mutations since C16**: 2
  - C16 remediation `3e152e02` (PR #240): 5 of 12 C16 findings resolved (M7, L2, M2, H2, H1-partial)
  - C21 remediation `f142fcdb` (PR #250): inserted new §3.6 Metabolic State Considerations (9 lines)

**Framing**: This is a **delta re-audit**, not a fresh first-pass audit. The 8 still-unresolved C16 findings are consolidated in §A below with re-verified line numbers; they are NOT re-issued as new C23 IDs. NET-NEW C23 IDs are reserved for findings that did not appear in C16, including: (a) the new §3.6 section that has never been audited, (b) cross-doc tensions only visible after C17-C22 audited sister specs, (c) the four pre-identified candidates from exit #136's cross-coherence reading.

**Counts**:
- **C23 new IDs**: 7 (1 HIGH + 3 MEDIUM + 2 LOW + 1 INFO)
- **C16 carried (re-verified line numbers)**: 8 (H1-remainder, M1, M3, M4, M5, M6, M8, L1-revised)

Per BC-C23-5 (anti-padding): the 7-net-new count reflects honest delta from C16, not padding to match prior C-series distributions.

---

## Authority hierarchy used for this audit

| Claim class | Authority | File(s) |
|-------------|-----------|---------|
| Runtime / wire-JSON / federation primitives | SDK | `web4-standard/implementation/sdk/web4/federation.py` (module docstring: *"Canonical implementation per web4-society-authority-law.md and SOCIETY_SPECIFICATION.md"*) |
| Society orchestration / metabolic gating | SDK | `web4-standard/implementation/sdk/web4/society.py`; `web4-standard/implementation/sdk/web4/metabolic.py` |
| LCT shape / birth-certificate inline wire | SDK | `web4-standard/implementation/sdk/web4/lct.py` (BirthCertificate dataclass at L144-164) |
| Metabolic-state semantics | spec + SDK | `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` (C21-audited); `metabolic.py::accepts_new_citizens` (L410-413) |
| Society-spec cross-coherence | spec | `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (C22-audited; §1.2.5 cross-refs SAL §3.1) |
| LCT spec cross-coherence | spec | `web4-standard/core-spec/LCT-linked-context-token.md` (L73-84 `birth_certificate` inline shape) |
| Entity-types cross-coherence | spec | `web4-standard/core-spec/entity-types.md` (L141-158 Birth Certificate Structure) |
| Role taxonomy | spec + SDK | `society-roles.md` (7+2); `federation.py::RoleType` (5); `role.py::SocietyRole` (9) |
| Error code taxonomy | spec + SDK | `errors.md`; `errors.py` |
| RDF vocabulary | ontology TTL | `web4-standard/ontology/web4-core-ontology.ttl` (refers to missing `sal-ontology.ttl`) |

Every cited line was re-read against the live file at HEAD `252e77bd` before the finding text was written, per BC#2/BC#3.

---

## Summary

| Severity | Count | Theme |
|----------|-------|-------|
| HIGH (new) | 1 | H1: Birth-certificate THREE-WAY shape drift (SAL §2.2 vs LCT-spec inline vs SDK `lct.py::BirthCertificate`) — C16 missed the cross-spec/SDK-lct.py dimension entirely; revises and supersedes C16-L1's "SDK lacks BirthCertificate type" framing |
| MEDIUM (new) | 3 | M1: `entity-types.md` L153-154 still uses `initialRights`/`initialResponsibilities` already-deprecated by C16-rem — sister-doc corpus-sweep leftover; M2: §3.1 (3-component "society topology") vs §3.4 (4th MUST not in §3.1 enumeration) — internal framing tension; M3: §3.6 vs SDK `accepts_new_citizens` vs `SOCIETY_METABOLIC_STATES.md §2.2` three-way drift on Rest-state citizenship behavior (queue vs refuse) |
| LOW (new) | 2 | L1: Asymmetric metabolic-state cross-references — SOCIETY_SPEC §1.4 and SAL §3.6 are parallel sections with no mutual cross-link; SOCIETY_SPEC §1.2.5 cites SAL §3.1 with no reciprocal back-link from SAL §3.1; L2: §3.4 ledger-event categories (6 SAL-specific) vs SOCIETY_SPEC §1.2.2 (5 general) vs SDK `LedgerEventType` enum (5) three-way taxonomy divergence |
| INFO (new) | 1 | I1: Date header `2025-09-15 11:50:10` (L3) is 8.5 months stale; per BC#13 classified INFO because no normative date-dependency exists in SAL; bumpable under BC#15 since this IS SAL's own audit |
| DEMOTED | 2 | D1: federation.py:88/91 docstring "Citizenship Lifecycle (SOCIETY_SPECIFICATION §2.3)" — SDK-side defect (SAL §2.3 is "Canonicalization & Signatures", not lifecycle); OUT OF SCOPE for SAL audit. D2: ontology L219 dangling reference to `web4:Web4BirthCertificate` class undefined in canonical ontology — this is a specific instance of existing C16-M8 cluster carry, NOT a new finding |
| C16-carried (§A) | 8 | H1-remainder (3 missing error codes), M1 (5-role vs 7+2 taxonomy), M3 (`r6Bindings` missing from SDK), M4 (Ledger Interface ops), M5 (event-topic naming), M6 (cool-down MUST missing from SDK), M8 (RDF vocabulary in non-canonical location), L1-revised (re-framed by C23-H1) |

**Severity calibration anchored to C12-C22 precedent**:
- **HIGH** = wire-breaking divergence affecting a normative example, OR spec-vs-spec contradiction across multiple sister docs on a primitive shape (the C23-H1 birth-cert finding is the latter — three different shapes in three different sources for the same conceptual object).
- **MEDIUM** = field/enum rename or shape divergence converging on a normative MUST (anchored to C12-C15 M-series), OR internal framing inconsistency (M2), OR cross-doc/SDK 3-way drift on a SHOULD-tier behavior (M3).
- **LOW** = doc-hygiene / asymmetric cross-reference / taxonomy-naming divergence that doesn't break a wire (L1, L2).
- **INFO** = date staleness with no normative dependency (I1) per BC#13.

**Subordinate-ontology cluster status** (BC-C23-3 hard stop): C23 does **NOT** surface a new ontology gap as a new C23 ID. The L219 `web4:Web4BirthCertificate` dangling reference is **demoted** (D2) into the existing C16-M8 cluster carry rather than incrementing the cluster count to 8. Cluster remains at **7 audits** (C16-M8 + C17-M1 + C18-M6 + C19-M5 + C20-M5 + C21-M7 + C22-M4+I4), still operator-engagement-class per BC#7.

---

## §A. Still-Unresolved from C16 (line numbers re-verified at HEAD `252e77bd`)

Eight C16 findings remain in the live SAL spec after C16-remediation `3e152e02`. They are NOT re-issued as new C23 IDs (BC-C23-1 firewall). Each is listed here with its current line number and a one-line drift assessment. Any operator-engagement bundle on SAL should treat these 8 as the baseline carry plus the C23 new findings as the delta.

| C16 ID | C16-cited line | Current line at HEAD `252e77bd` | Drift assessment | Status |
|--------|---------------|--------------------------------|------------------|--------|
| H1-remainder (3 codes) | §9 L299-301 | §9 **L308-310** | line drift +9 (due to §3.6 insertion of 9 lines after §3.5) — citations re-verified `W4_ERR_LEDGER_WRITE` L308, `W4_ERR_AUDIT_EVIDENCE` L309, `W4_ERR_LAW_CONFLICT` L310 | still accurate, line drift only |
| M1 (role taxonomy) | §5 heading L166 + §§5.1-5.5 L166-219 | §5 heading **L175** + §§5.1-5.5 **L175-228** | line drift +9 | still accurate, line drift only — DESIGN-Q (5-role vs 7+2-role taxonomy) |
| M3 (`r6Bindings` missing from SDK) | §4.1 L156 | §4.1 **L165** | line drift +9 | still accurate, line drift only — DESIGN-Q (add to SDK vs remove from spec) |
| M4 (Ledger Interface ops) | §3.4 L110-118 | §3.4 **L110-118** (UNCHANGED) | no drift — §3.4 precedes §3.6 insertion | still accurate — DESIGN-Q (SDK extension vs spec scoping) |
| M5 (event-topic naming) | §3.4 L108 | §3.4 **L108** (UNCHANGED) | no drift | still accurate — DESIGN-Q (rename SDK enum vs revise spec example) + missing AUDIT topic |
| M6 (cool-down period MUST missing from SDK) | §5.5 L208 | §5.5 **L218** | line drift +10 (insertion + intra-§3 prose adjustments) | still accurate — SDK-side change needed |
| M8 (RDF vocabulary + `sal-ontology.ttl` missing) | §3.3 L81-101 | §3.3 **L81-101** (UNCHANGED) | no drift | still accurate — operator-engagement-class per BC#7 |
| L1-revised (BirthCertificate) | §2.2 L44-60 | §2.2 **L44-60** (UNCHANGED) | no drift, BUT original C16-L1 framing ("SDK lacks BirthCertificate type") is partially incorrect — SDK *does* have a `BirthCertificate` in `lct.py:144`, just with a different shape than SAL §2.2 specifies. **SUPERSEDED by C23-H1**, which captures the 3-way shape drift. C16-L1 should be retired in favor of C23-H1. |

**Re-verification grep evidence (BC-C23-4)**:

```
grep -n "W4_ERR_LEDGER_WRITE\|W4_ERR_AUDIT_EVIDENCE\|W4_ERR_LAW_CONFLICT" web4-standard/core-spec/web4-society-authority-law.md
308:| Ledger write failed | W4_ERR_LEDGER_WRITE | Retry with backoff; degrade to escrow buffer |
309:| Audit evidence insufficient | W4_ERR_AUDIT_EVIDENCE | Reject adjustment; request stronger proofs |
310:| Law inheritance conflict | W4_ERR_LAW_CONFLICT | Invoke conflictPolicy; request parent/child oracle mediation |
```

```
grep -n "cool-down" web4-standard/core-spec/web4-society-authority-law.md
218:- Negative adjustments **MUST** include **appeal path** and **cool-down period**.
```

```
grep -n "r6Bindings" web4-standard/core-spec/web4-society-authority-law.md
165:  "r6Bindings": ["web4://schemas/r6-rules-v1"]
```

All eight C16 findings remain in the live spec. None has been re-remediated since C16-rem `3e152e02`.

---

## C23 NEW Findings

### H1 (NEW): Birth-certificate THREE-WAY shape drift across SAL §2.2, `LCT-linked-context-token.md`, and SDK `lct.py::BirthCertificate`

**Severity**: HIGH (wire-breaking; spec-vs-spec on a primitive shape; supersedes C16-L1's framing)

**Why this was missed in C16**: C16 cross-referenced SAL §2.2 only against `federation.py` (where no `BirthCertificate` class exists) and concluded "SDK lacks BirthCertificate type" (C16-L1). It did NOT cross-reference the LCT spec's `birth_certificate` inline field shape, nor `lct.py::BirthCertificate` (which is the actual canonical wire shape in test-vectors and demos). The C-series only began making cross-doc multi-file findings (BC#1) systematic at C21+; C16 used a single-cross-reference pattern that missed the third leg.

**Locations** (each re-read at the cited line):

**(a)** SAL §2.2 L44-60 — `Web4BirthCertificate` (JSON-LD top-level, standalone object):
```json
{
  "@context": ["https://web4.io/contexts/sal.jsonld"],
  "type": "Web4BirthCertificate",
  "entity": "lct:web4:entity:...",
  "citizenRole": "lct:web4:role:citizen:...",
  "society": "lct:web4:society:...",
  "lawOracle": "lct:web4:oracle:law:...",
  "lawVersion": "v1.2.0",
  "birthTimestamp": "2025-09-14T12:00:00Z",
  "witnesses": ["lct:web4:witness1", "lct:web4:witness2"],
  "genesisBlock": "block:12345",
  "rights": ["exist", "interact", "accumulate_reputation"],
  "obligations": ["abide_law", "respect_quorum"]
}
```

**(b)** `LCT-linked-context-token.md` L73-84 — `birth_certificate` (INLINE field within an LCT):
```json
"birth_certificate": {
  "issuing_society": "lct:web4:society:...",
  "citizen_role": "lct:web4:role:citizen:...",
  "birth_timestamp": "2025-10-01T00:00:00Z",
  "birth_witnesses": ["lct:web4:witness:1...", "lct:web4:witness:2...", "lct:web4:witness:3..."],
  "genesis_block_hash": "0x...",
  "birth_context": "nation|platform|network|organization|ecosystem"
}
```

**(c)** SDK `lct.py:144-164` — `BirthCertificate` dataclass (canonical wire shape per test-vectors and `validate_schemas.py:106`):
```python
@dataclass(frozen=True)
class BirthCertificate:
    issuing_society: str
    citizen_role: str
    birth_timestamp: str
    birth_witnesses: List[str] = field(default_factory=list)
    birth_context: str = "platform"
    genesis_block_hash: Optional[str] = None
```

**Field-by-field divergence map**:

| Concept | SAL §2.2 (a) | LCT spec (b) | SDK `lct.py` (c) | Verdict |
|---------|--------------|--------------|------------------|---------|
| top-level type | `"type": "Web4BirthCertificate"` (PascalCase JSON-LD) | (none — embedded inside LCT) | (none — embedded inside LCT) | a is standalone JSON-LD doc; b/c are inline fields |
| @context | `@context` array | (none) | (none — added by LCT-level to_jsonld) | a only |
| citizen entity ref | `entity` | (none — implicit from LCT subject) | (none — implicit from LCT subject) | a only |
| citizen role LCT | `citizenRole` (camelCase) | `citizen_role` (snake_case) | `citizen_role` | a renamed |
| issuing society | `society` | `issuing_society` (semantic rename + snake_case) | `issuing_society` | a uses different name |
| law oracle ref | `lawOracle` | (none) | (none) | a only |
| law version | `lawVersion` | (none) | (none) | a only |
| birth timestamp | `birthTimestamp` (camelCase) | `birth_timestamp` (snake_case) | `birth_timestamp` | a renamed |
| witnesses | `witnesses` | `birth_witnesses` (renamed) | `birth_witnesses` | a uses different name |
| genesis-block ref | `genesisBlock` (string) | `genesis_block_hash` (different semantics: hash vs ID) | `genesis_block_hash` | a uses different name and semantics |
| birth context | (none) | `birth_context` (enum: nation/platform/network/organization/ecosystem) | `birth_context` | a missing |
| rights | `rights` | (none — moved to CitizenshipRecord) | (none — on `CitizenshipRecord` in `federation.py`, not on cert) | a only |
| obligations | `obligations` | (none — moved to CitizenshipRecord) | (none) | a only |

**Impact**:
1. A SAL-spec-conformant `Web4BirthCertificate` JSON-LD document does NOT roundtrip through the SDK's `BirthCertificate.from_dict()` (would fail on every required field name).
2. An LCT spec-conformant `birth_certificate` inline field DOES roundtrip through the SDK, BUT a consumer reading SAL §2.2 will produce neither.
3. The two specs describe what appears to be the same conceptual object using genuinely different field names, semantics, and shapes — not just stylistic variance.
4. Cross-language implementers reading SAL §2.2 will produce wire that the SDK rejects; implementers reading LCT-spec will produce wire that ignores SAL's `lawOracle`/`lawVersion`/`rights`/`obligations` provenance bindings.

**Remediation classification**: **DESIGN-Q** (out of scope for this audit). Requires a normative decision: (i) is the canonical birth certificate the SAL §2.2 standalone JSON-LD doc, or the LCT inline field? (ii) which fields are required: SAL's law-binding provenance (`lawOracle`, `lawVersion`, `rights`, `obligations`) or LCT-spec's context-typing (`birth_context`, `genesis_block_hash` semantics)? (iii) how do `rights`/`obligations` relate to `CitizenshipRecord` vs the birth certificate itself? Cannot be auto-resolved because both shapes have live consumers (SAL JSON-LD example vs SDK + 7+ test-vectors + 4+ demos).

**Note on C16-L1 supersession**: C16-L1's recommendation ("Add `BirthCertificate` dataclass to `federation.py`") would produce a *fourth* shape if implemented now, compounding the divergence. The fix here is reconciliation, not addition.

---

### M1 (NEW): `entity-types.md` L153-154 still uses `initialRights`/`initialResponsibilities` that C16-remediation `3e152e02` already renamed in SAL §2.2

**Severity**: MEDIUM (sister-doc corpus-sweep leftover — C16-rem missed the parallel example in entity-types.md)

**Locations** (re-read):

SAL §2.2 (current HEAD `252e77bd`, post C16-rem):
```json
"rights": ["exist", "interact", "accumulate_reputation"],
"obligations": ["abide_law", "respect_quorum"]
```
(L57-58 in current SAL — already renamed in C16-rem.)

`entity-types.md` §3.1 "Birth Certificate Structure (SAL-compliant)" L141-158 (re-read at L153-154):
```json
"initialRights": ["exist", "interact", "accumulate_reputation"],
"initialResponsibilities": ["abide_law", "respect_quorum"],
```

The entity-types.md example **explicitly claims to be "SAL-compliant"** (L140 section header) but uses the pre-C16-rem field names. C16-rem `3e152e02` renamed SAL §2.2 from `initialRights`/`initialResponsibilities` to `rights`/`obligations` (matching `federation.py::CitizenshipRecord.rights`/`obligations` defaults at federation.py:128-129) — but did not propagate the rename to `entity-types.md`.

**Grep evidence (BC#5 corpus sweep)**:
```
grep -rn "initialRights\|initialResponsibilities" web4-standard/core-spec/
web4-standard/core-spec/entity-types.md:153:  "initialRights": ["exist", "interact", "accumulate_reputation"],
web4-standard/core-spec/entity-types.md:154:  "initialResponsibilities": ["abide_law", "respect_quorum"],
```
Only `entity-types.md` retains the deprecated names within `core-spec/`. SAL has been cleaned; archive/reference-implementations contain the deprecated names (out-of-scope — those are pre-C16 archived prototypes).

**Impact**: An implementer following entity-types.md's "SAL-compliant" example will produce wire that does not match the current SAL §2.2 spec or the SDK's `CitizenshipRecord` defaults. The "SAL-compliant" claim in the entity-types.md section header is technically false post-C16-rem.

**Remediation classification**: **Autonomous-actionable** (single sister-doc rename, BC#1 multi-file framing — one finding, one fix-vehicle: rename `initialRights` → `rights`, `initialResponsibilities` → `obligations` at `entity-types.md` L153-154 to match SAL §2.2's post-C16-rem shape). Note: this finding INTERACTS with C23-H1: if H1's remediation reverses or revises the SAL §2.2 shape, M1's target rename direction may need to change. Recommendation: defer M1 until H1 has a design decision, then apply M1 in whichever direction H1 settles on.

---

### M2 (NEW): §3.1 "Society Topology" lists 3 components, but §3.4 makes a 4th component MUST (Immutable Record) without back-reference

**Severity**: MEDIUM (internal framing inconsistency on "what must a society have")

**Locations** (re-read):

SAL §3.1 L70-74:
> A **Society** is a delegative entity with:
> - An **Authority Role** LCT (root of delegation tree).
> - A **Law Oracle** LCT (publishes machine-readable law and interpretations).
> - A **Quorum Policy** (witness/attestation requirements per action type).

Exactly **3 components** in the topology enumeration.

SAL §3.4 L104-106:
> Each society **MUST** operate or bind to an **Immutable Record** service (blockchain or append-only ledger) that:
> - Stores **Birth Certificates**, **role pairings**, **delegations**, **law dataset digests**, **witness attestations**, and **auditor adjustments**.

§3.4 imposes a 4th MUST that is **not part of §3.1's "society is a delegative entity with..." enumeration**. A reader who treats §3.1 as the authoritative "minimum society" enumeration will under-count by 1 (missing the Immutable Record / ledger requirement).

**Cross-doc reinforcement**: `SOCIETY_SPECIFICATION.md` §1.2 (re-read post-C22) lists FOUR minimum requirements: Law Oracle (§1.2.1), Ledger (§1.2.2), Treasury (§1.2.3), Society LCT (§1.2.4). SOCIETY_SPEC §1.2.5 (added in C22-rem) explicitly cross-refs SAL §3.1 as a "refinement" along the role-structural axis. The SOCIETY_SPEC §1.2 frame includes the ledger (§1.2.2); SAL §3.1 does not. This is a real definitional drift on "what does a society MUST have."

**Impact**: An implementer building a society from SAL §3.1 alone will not provision a ledger and will hit §3.4 MUST as a surprise late in implementation. The C22-added cross-ref in SOCIETY_SPEC §1.2.5 partially compensates, but only one-way.

**Remediation classification**: **Autonomous-actionable** — extend SAL §3.1 to include "An **Immutable Record** binding (per §3.4)" as a 4th bullet, making the §3.4 MUST visible at the topology-enumeration site. Single-section edit, no SDK impact.

---

### M3 (NEW): §3.6 vs SDK `accepts_new_citizens` vs `SOCIETY_METABOLIC_STATES.md §2.2` — three-way drift on Rest-state citizenship behavior (queue vs refuse)

**Severity**: MEDIUM (cross-spec/SDK 3-way drift on a SHOULD-tier behavior; the new §3.6 — never audited before — is the most-recent leg of the drift)

**Locations** (re-read):

SAL §3.6 (added in C21-rem `f142fcdb`) L138:
> **Citizenship issuance** (§2.1 Birth Certificate) is sensitive to `accepts_new_citizens` per state — Active SHOULD accept immediately; **Rest MAY queue**; dormant states SHOULD defer.

`SOCIETY_METABOLIC_STATES.md` §2.2 Rest State L59:
> - **New citizens queued for active period**

SDK `metabolic.py:410-413`:
```python
def accepts_new_citizens(state: MetabolicState) -> bool:
    """Check if a society in this state accepts new citizenship applications."""
    # Active: yes. Rest: queued. All others: no or queued.
    return state == MetabolicState.ACTIVE
```

SDK `society.py:435` (gates citizenship admission on this function):
```python
if not accepts_new_citizens(state.metabolic_state):
    return False
```

**The drift**:
- **SOCIETY_METABOLIC_STATES.md §2.2** prose: "New citizens queued for active period" (queue, not refuse)
- **SAL §3.6** prose: "Rest MAY queue" (consistent with sister doc)
- **SDK `accepts_new_citizens(Rest)`** returns **False** (boolean predicate; no queue semantics)
- **SDK `add_citizen`**: on `accepts_new_citizens` returning False, the function returns False — citizenship is **refused**, NOT queued. There is no queue infrastructure in the SDK for deferred-acceptance.

So per the two specs, Rest → queue; per the SDK, Rest → refuse. The SDK's docstring at metabolic.py:412 even admits the gap (*"Rest: queued"* in the comment, but the code returns False — predicate semantics don't admit queuing).

**Impact**:
1. An implementer reading SAL §3.6 expects Rest-state citizenship applications to be queued; the SDK refuses them outright.
2. SOCIETY_METABOLIC_STATES.md §2.2 explicitly promises Rest queueing as a state characteristic; the SDK delivers refusal.
3. The new §3.6 (never audited) made the divergence visible by being the first SAL section to directly couple SAL semantics to `accepts_new_citizens`-shaped behavior.

**Remediation classification**: **DESIGN-Q** (out of scope). Three options: (i) extend SDK with a queue/defer mechanism for Rest state (changes `accepts_new_citizens` from boolean predicate to enum: `accept`/`queue`/`refuse`); (ii) revise SAL §3.6 + SOCIETY_METABOLIC_STATES.md §2.2 to say "Rest MAY refuse" (matching SDK); (iii) make this a separate SDK API (`citizenship_disposition(state) → Accept|Queue|Refuse`) and keep `accepts_new_citizens` as a strict-yes predicate. (i) is closest to spec intent; (ii) preserves SDK simplicity; (iii) is the cleanest factoring.

---

### L1 (NEW): Asymmetric metabolic-state and minimum-viable cross-references between SAL and SOCIETY_SPECIFICATION

**Severity**: LOW (cross-doc discoverability gap; no semantic divergence)

**Locations** (re-read at HEAD):

Direction (a) — SOCIETY_SPEC → SAL (present, one-way):
- `SOCIETY_SPECIFICATION.md` §1.2.5 L55-62 (added in C22-rem) explicitly cites SAL §3.1 as refining §1.2's minimum-viable society.
- SAL §3.1 (L70-74) has **no reciprocal back-link** to SOCIETY_SPEC §1.2 or §1.2.5.

Direction (b) — SOCIETY_SPEC ↔ SAL metabolic-state cross-references (parallel sections, no mutual link):
- `SOCIETY_SPECIFICATION.md` §1.4 L83-87 (added in C21-rem) describes operational modes / metabolic states.
- SAL §3.6 L134-141 (added in C21-rem) describes metabolic-state considerations for SAL actions.
- Both were added by the same C21 remediation (commit `f142fcdb`). **Neither cross-references the other**, despite covering parallel topics.

Direction (c) — both → SOCIETY_METABOLIC_STATES.md (present, both):
- SOCIETY_SPEC §1.4 → SOCIETY_METABOLIC_STATES.md ✓
- SAL §3.6 → SOCIETY_METABOLIC_STATES.md (§2.8) ✓

So the cross-ref graph is asymmetric: both link UP to SOCIETY_METABOLIC_STATES.md but not SIDEWAYS to each other, and SOCIETY_SPEC §1.2.5 links to SAL §3.1 but SAL §3.1 doesn't link back.

**Impact**: Readers of SAL §3.1 or §3.6 won't discover the parallel-section context in SOCIETY_SPEC without already knowing to look. C22-rem made the cross-ref-direction explicit one-way; C23-L1 surfaces the missing reciprocals.

**Remediation classification**: **Autonomous-actionable** — add two short cross-reference lines: (i) in SAL §3.1, append "See also: `SOCIETY_SPECIFICATION.md` §1.2 for the conceptual-minimum view that §3.1 refines along the role-structural axis."; (ii) in SAL §3.6 intro, append "See also: `SOCIETY_SPECIFICATION.md` §1.4 for the parallel society-spec framing of operational modes." Two-line addition; no SDK impact.

---

### L2 (NEW): §3.4 ledger-event categories (6 SAL-specific) vs `SOCIETY_SPECIFICATION.md §1.2.2` (5 general) vs SDK `LedgerEventType` (5) — three-way taxonomy divergence

**Severity**: LOW (taxonomy-naming divergence; §3.4 is illustrative prose, not enum-bearing)

**Locations** (re-read):

SAL §3.4 L106:
> Stores **Birth Certificates**, **role pairings**, **delegations**, **law dataset digests**, **witness attestations**, and **auditor adjustments**.
> (6 categories, SAL-domain-specific)

SOCIETY_SPECIFICATION.md §1.2.2 L34-38:
> - Citizenship events (join/leave/suspend/reinstate)
> - Law changes (proposal/ratification/amendment)
> - Economic events (treasury deposits/allocations/reclaims)
> - Metabolic state transitions (per `SOCIETY_METABOLIC_STATES.md`)
> - Formation events (genesis/bootstrap/operational/incorporation)
> (5 categories, general)

SDK `society.py:89-96` `LedgerEventType` enum:
```python
CITIZENSHIP = "citizenship"
LAW_CHANGE = "law_change"
ECONOMIC = "economic"
METABOLIC = "metabolic"
FORMATION = "formation"
```
(5 enum values, matches SOCIETY_SPEC §1.2.2 exactly per BC#14 verification at exit #136.)

**Mapping**:

| SAL §3.4 (6) | SOCIETY_SPEC §1.2.2 (5) / SDK enum |
|---|---|
| Birth Certificates | CITIZENSHIP (subset: birth subevent) |
| role pairings | CITIZENSHIP (subset: role bind subevent) |
| delegations | CITIZENSHIP or LAW_CHANGE (no clean home) |
| law dataset digests | LAW_CHANGE |
| witness attestations | (none — witnesses are per-entry, not a separate event type, per SOCIETY_SPEC §1.2.2 explicit Note at L39) |
| auditor adjustments | (none — no AUDIT category in SDK enum; C16-M5 carries this forward) |

SOCIETY_SPEC §1.2.2's explicit note at L39 says *"Witnesses participate in every recorded event via the per-entry `witnesses` field; they are participants, not a separate event category."* This directly contradicts SAL §3.4's listing of "witness attestations" as a ledger-stored category.

**Impact**: An implementer choosing a ledger event-category enum from SAL §3.4 will land on 6 SAL-named categories; from SOCIETY_SPEC §1.2.2 / SDK enum, on 5 general-named categories. The two taxonomies overlap but are not a 1:1 mapping. SAL §3.4's "witness attestations" category contradicts SOCIETY_SPEC's per-entry-witness framing.

**Remediation classification**: **DESIGN-Q** (out of scope). Two options: (i) revise SAL §3.4 to use the SDK enum names and add a Note pointing at SOCIETY_SPEC §1.2.2 as canonical for the event-type taxonomy; (ii) accept the divergence and treat SAL §3.4 as illustrative-only (add "(illustrative; canonical event-type set is given in `SOCIETY_SPECIFICATION.md §1.2.2`)" disclaimer). The witness-as-event-category contradiction must be resolved either way.

---

### I1 (NEW INFO): Date header `2025-09-15 11:50:10` is 8.5 months stale (HEAD `252e77bd`)

**Severity**: INFO (BC#13: date alone is INFO unless coupled with normative date-dependency; SAL has no date-dependent normative claim — all dates in prose are example values e.g. `birthTimestamp": "2025-09-14T12:00:00Z"`, not normative dependencies)

**Location**:

SAL L3:
> **Status:** Draft • **Last Updated:** 2025-09-15 11:50:10 • **Applies to:** Web4 Core Protocol and Ecosystem

The doc has been edited twice since this header date: by C16-rem `3e152e02` (2026-05-27) and C21-rem `f142fcdb` (2026-05-30). Header is 8 months 15 days stale.

**Impact**: Cosmetic/hygiene. Readers may infer the doc has been frozen since Sept 2025 when in fact it has had two recent normative edits. Does NOT affect any wire shape or normative claim.

**BC#15 status**: This audit IS the SAL audit (BC#15 reservation lifted). The date is bumpable as an "in-scope hygiene refresh" if any C23 remediation makes substantive edits to SAL. If C23 remediation only addresses cross-doc / sister-doc findings (M1 is sister-doc only; H1 is design-Q deferred), the date refresh may stand alone — which BC#15 also permits as a "pure-date refresh in scope."

**Remediation classification**: **Autonomous-actionable** — bump L3 date to remediation-day timestamp when any C23-remediation PR ships.

---

## Demoted Candidates (with rationale per BC#9 overcall-discipline)

### D1: `federation.py:88,91` docstring "Citizenship Lifecycle (SOCIETY_SPECIFICATION §2.3)" is wrong — SOCIETY_SPEC §2.3 is "Citizenship Properties (Multi-Society)", not lifecycle

**Why demoted**: This is an **SDK-side docstring defect**, not a SAL spec defect. SAL §2.3 is "Canonicalization & Signatures" (not citizenship lifecycle); SOCIETY_SPEC §2.3 (post-C22) is "Citizenship Lifecycle" — actually the correct reference. The SDK comment matches reality. **Re-verification**: re-read SOCIETY_SPECIFICATION.md §2.3 — yes, it does cover citizenship lifecycle (APPLIED → PROVISIONAL → ACTIVE → SUSPENDED → TERMINATED). False alarm; comment is accurate. Demoted to nothing — no defect.

### D2: `web4-core-ontology.ttl:219` declares `rdfs:range web4:Web4BirthCertificate` but `Web4BirthCertificate` class is undefined in canonical ontology

**Why demoted**: This IS a real ontology gap, but it is a **specific instance of the existing C16-M8 cluster** (RDF vocabulary not formalized in canonical ontology; `sal-ontology.ttl` references the missing file at `web4-core-ontology.ttl:195`). Per BC-C23-3, this audit does NOT extend the subordinate-ontology cluster count to 8; the cluster remains at 7 (C16-M8 + C17-M1 + C18-M6 + C19-M5 + C20-M5 + C21-M7 + C22-M4+I4). The `Web4BirthCertificate` class undefinedness is added evidence under the existing C16-M8 carry, not a new C23 finding. Operator-engagement-class per BC#7.

---

## Verification Hygiene Appendix (BC-C23-4)

### (i) BC#3 off-by-one citation sweep

All cited line numbers were re-read against the live file at HEAD `252e77bd`. **0 corrections** made during writing. The 8 C16-carried items in §A have been verified to have either +9/+10 line drift (due to §3.6 insertion) or no drift (sections preceding §3.6). The 7 C23-new findings cite current-HEAD lines:
- H1: SAL L44-60 (no drift, pre-§3.6); LCT-spec L73-84; lct.py:144-164 ✓
- M1: entity-types.md L153-154 ✓
- M2: SAL L70-74 (§3.1), L104-106 (§3.4) — both pre-§3.6, no drift ✓
- M3: SAL L138 (within new §3.6); SOCIETY_METABOLIC_STATES.md L59; metabolic.py:410-413; society.py:435 ✓
- L1: SOCIETY_SPECIFICATION.md L55-62 (§1.2.5), L83-87 (§1.4); SAL L70-74 (§3.1), L134-141 (§3.6) ✓
- L2: SAL L106 (§3.4); SOCIETY_SPECIFICATION.md L34-39; society.py:89-96 ✓
- I1: SAL L3 ✓

### (ii) BC#5 corpus-sweep for terms proposed for change

Terms whose change is proposed (M1, L1, M2 reframings):
- `initialRights`, `initialResponsibilities`: only `entity-types.md` L153-154 within `web4-standard/core-spec/` (verified above). Out-of-tree sweep: forum/nova/web4-sal-bundle (pre-C16 draft material), archive/reference-implementations (archived prototypes) — both out of scope. **No undiscovered defect sites.**
- Cross-reference patches (M2 §3.1 extension, L1 reciprocal links): textual additions only, no rename — corpus sweep N/A for inserts.

### (iii) BC#12 vector-count recount

No test-vector counts cited in C23 net-new findings. The C16 audit cited federation-vectors but C23 does not add vector-count-bearing findings. **BC#12 N/A for this audit; no recount required.**

### (iv) BC#14 SDK enum verification

C23-L2 cites `society.py:89-96 LedgerEventType` enum with 5 values (CITIZENSHIP, LAW_CHANGE, ECONOMIC, METABOLIC, FORMATION). Re-verified at HEAD `252e77bd` — enum unchanged since #136's BC#14 verification.

### (v) BC-C23-5 anti-padding justification

New-finding count of 7 (1H+3M+2L+1I) is below the C16-C22 envelope mid-line (C16 had 12, C17 had 10, C18 had 11, C19 had 13, C20 had 13, C21 had 16, C22 had 11) but appropriately reflects honest delta. The 8-item C16 carry brings effective coverage to 15 items, on-envelope. **Not padded to match prior distributions** — H1 alone justifies the 7-count via its 3-way scope; the remaining 6 are real cross-doc / framing findings that did not exist when C16 ran (M1 only became a leftover after C16-rem; M3 only became visible after §3.6 was added by C21-rem; L1 only became visible after C22-rem added the one-way cross-ref; M2 was hiding in plain sight but C16 missed it).

---

## Autonomous / Design-Q / Cross-Track Split

Per the C-series partial-remediation pattern (established at exit #124):

**Autonomous-actionable (3)**:
- **M1** — `entity-types.md` L153-154 rename (single sister-doc edit; defer until H1 design Q resolved, see M1 note)
- **M2** — SAL §3.1 add 4th bullet for Immutable Record binding
- **L1** — SAL §3.1 and §3.6 reciprocal cross-references to SOCIETY_SPEC §1.2 and §1.4
- **I1** — date header bump (in-scope hygiene refresh, ships with any C23-rem)

(4 if I1 counted separately; 3 substantive + 1 hygiene.)

**Design-Q / operator-engagement (3)**:
- **H1** — Birth-certificate 3-way shape drift; requires normative decision on canonical shape
- **M3** — Rest-state queue-vs-refuse drift; requires API-shape decision (boolean predicate vs disposition enum)
- **L2** — §3.4 ledger event categories vs SOCIETY_SPEC §1.2.2 vs SDK enum; requires taxonomy reconciliation

**Cross-track (deferred to existing carry clusters)**:
- **D2** under existing C16-M8 (subordinate-ontology cluster, 7 audits, BC#7-protected)
- **C16-H1-remainder, C16-M1, C16-M3, C16-M4, C16-M5, C16-M6, C16-M8, C16-L1 (revised)** — see §A; the 8-item C16 carry should be bundled into the same operator-engagement engagement as C23-H1/M3/L2

---

## Audit Methodology (BC discipline)

- **BC#1** (multi-file findings under one ID): H1 covers 3 sources (SAL + LCT-spec + SDK lct.py) under one ID; M3 covers 3 sources (SAL + SMS + SDK metabolic.py) under one ID; L1 covers 4 sites under one ID. All multi-file findings are single-ID per BC#1.
- **BC#2/BC#3**: every cited line re-read at the cited line before writing the finding; 0 off-by-one corrections required.
- **BC#5**: corpus sweep performed for all rename-proposed terms; entry in Verification Hygiene §(ii).
- **BC#7**: subordinate-ontology cluster gap (D2) demoted, not surfaced as new C23 ID; cluster count NOT extended.
- **BC#9** (overcall discipline): 2 candidate findings demoted (D1 = false alarm on SDK docstring; D2 = absorbed by existing cluster).
- **BC#12**: not applicable to this audit (no vector counts in findings).
- **BC#13**: I1 classified as INFO per the "date alone unless coupled with normative date-dependency" rule.
- **BC#14**: SDK enum re-verified for L2 (LedgerEventType at society.py:89-96, unchanged since #136).
- **BC#15**: SAL date refresh permitted in I1's scope (this IS the SAL audit; reservation lifted).
- **BC-C23-1**: 8 C16 items consolidated in §A with re-verified line numbers, NOT re-issued as new C23 IDs. Counts disclosed: `C23 new IDs: 7`, `C16 carried: 8`.
- **BC-C23-2**: §3.6 audited — M3 is the explicit finding on §3.6; cross-references to SOCIETY_METABOLIC_STATES.md §2.8 in §3.6 L137 verified accurate.
- **BC-C23-3**: D2 demoted; cluster count not extended.
- **BC-C23-4**: Verification Hygiene appendix present.
- **BC-C23-5**: anti-padding justification statement included in Verification Hygiene §(v).

**No remediation patches** in this audit per BC#7. Findings only.

---

*End of C23 audit.*
