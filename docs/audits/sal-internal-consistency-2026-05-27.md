# C16: web4-society-authority-law.md (SAL) Internal Consistency Audit

**Date**: 2026-05-27
**Auditor**: Autonomous session (legion-web4-20260527-060014)
**Document**: `web4-standard/core-spec/web4-society-authority-law.md` (387 lines)

**Authority hierarchy used for this audit** (each cross-reference re-read at the cited line):

| Claim class | Authority | File(s) |
|-------------|-----------|---------|
| Runtime / wire-JSON / data structures | SDK | `web4-standard/implementation/sdk/web4/federation.py` (837 L — module docstring: *"Canonical implementation per web4-standard/core-spec/web4-society-authority-law.md and SOCIETY_SPECIFICATION.md"*) |
| Society orchestration / lifecycle / ledger | SDK | `web4-standard/implementation/sdk/web4/society.py` (825 L) |
| Role taxonomy | spec + SDK | `web4-standard/core-spec/society-roles.md` (canonical 7-base + 2-context); `web4-standard/implementation/sdk/web4/role.py` |
| Error code taxonomy | spec + SDK | `web4-standard/core-spec/errors.md`; `web4-standard/implementation/sdk/web4/errors.py` |
| RDF vocabulary | ontology TTL | `web4-standard/ontology/web4-core-ontology.ttl` |

Where divergence is **spec-vs-spec** rather than spec-vs-SDK, the finding labels it as such and does not silently promote one spec over the other.

---

## Summary

| Severity | Count | Theme |
|----------|-------|-------|
| HIGH | 2 | §9 references 4 error codes that don't exist in canonical taxonomy + internal duplication; §5.5 `AuditRequest` JSON uses `basis` for evidence vs SDK `evidence` |
| MEDIUM | 8 | §5 role taxonomy is the older 5-role set (SDK `federation.py` matches) but contradicts the newer 7-base + 2-context taxonomy in society-roles.md and `role.py`; norm/procedure/interpretation JSON key `id` vs SDK `*_id`; `r6Bindings` field missing from SDK `LawDataset`; ledger interface ops divergent; event-topic names divergent; `cool-down period` MUST missing from SDK; birth-certificate `initialRights`/`initialResponsibilities` vs SDK `rights`/`obligations`; RDF vocabulary not in canonical ontology directory |
| LOW | 2 | SDK lacks distinct `BirthCertificate` type — fields conflated into `CitizenshipRecord`; `Web4LawDataset` top-level `id` field absent from SDK |

**Cross-audit calibration note**: This audit follows C12 (r6, #229/#231), C13 (t3-v3, #230/#232), C14 (r7, #233/#234), C15 (reputation-computation, #236/#237). Severity calibration:
- **HIGH** = wire-breaking divergence (matches C14 H1 `roleType`→`roleLCT`) or normative claim referencing non-existent infrastructure (the 4-error-code finding is *worse* than a single rename — it points at 4 codes that don't exist, plus an intra-§9 duplication).
- **MEDIUM** = field/enum rename converging spec→SDK (matches C12/C13/C14/C15 M-series) or missing field with normative MUST.
- **LOW** = doc-hygiene / under-implementation that doesn't break the wire.

**Demoted candidate findings** (overcall-discipline value-add — three candidates explicitly *not* recorded as findings):

1. **SAL §2.1 + society.py `create_society` minimum-founders mismatch** — SAL §2.1 says LCT creation pairs entity with Citizen role at genesis (no founder-count constraint); `society.py:317` requires `len(founders) >= 2`. **Demoted**: this is a `SOCIETY_SPECIFICATION.md` / `create_society` constraint, not a SAL §2.1 constraint. The SAL spec is silent on minimum founders; `role.py:291-335` `bootstrap_society_roles()` already provides solo-founder genesis. Cross-spec issue, not a SAL defect.

2. **society.py `_register_citizen` (L408) overrides federation.py `CitizenshipRecord` defaults** — `_register_citizen` writes `rights=["vote", "propose", "allocate"]` / `obligations=["abide_law", "witness"]`, contradicting the matching-SAL `federation.py:128-129` defaults (`["exist", "interact", "accumulate_reputation"]` / `["abide_law", "respect_quorum"]`). **Demoted**: this is an SDK-internal inconsistency between `federation.py` and `society.py`, not a SAL-vs-SDK divergence. `federation.py` defaults *do* match SAL §2.2. Flagged as I3 for downstream SDK cleanup, not a SAL audit finding.

3. **r6-framework.md L604 References cites `SOCIETY_SPECIFICATION.md — Society-Authority-Law (SAL) governance framework`** — this is wrong; SAL is `web4-society-authority-law.md`, while `SOCIETY_SPECIFICATION.md` is a different spec (lifecycle/treasury). **Demoted**: defect is in `r6-framework.md`, not in SAL. Flagged in this audit's PR body for downstream coordination, not as a SAL finding.

Every cross-reference below was re-read against the live file at the cited line.

---

## HIGH Findings

### H1: §9 references four error codes absent from canonical taxonomy, plus intra-§9 duplication of the witness-quorum condition

**Location (SAL)**: §9 Error Conditions table lines 290–301. Specifically:
- L294 `W4_ERR_WITNESS_QUORUM` — exists in taxonomy
- L298 `W4_ERR_WITNESS_DEFICIT` — **does not exist** in `errors.md` or `errors.py`
- L299 `W4_ERR_LEDGER_WRITE` — **does not exist**
- L300 `W4_ERR_AUDIT_EVIDENCE` — **does not exist**
- L301 `W4_ERR_LAW_CONFLICT` — **does not exist** (the related `W4_ERR_CROSS_SOCIETY_LAW_CONFLICT` exists in `errors.py:104` but is a *different* code scoped to cross-society exchange)
- Plus: L294 ("Quorum not met") and L298 ("Missing witness quorum") describe the **same condition** with **two different codes** — internal duplication within one §9 table.

**Severity**: HIGH

**Canonical-taxonomy confirmation** (re-read at cited lines):

```
errors.md L38:  W4_ERR_BINDING_INVALID      ✓ (matches SAL L292)
errors.md L39:  W4_ERR_BINDING_REVOKED      ✓ (matches SAL L296)
errors.md L58:  W4_ERR_WITNESS_QUORUM       ✓ (matches SAL L294)
errors.md L66:  W4_ERR_AUTHZ_SCOPE          ✓ (matches SAL L295)
errors.md L85:  W4_ERR_PROTO_DOWNGRADE      ✓ (matches SAL L293)
```

`grep -nE "WITNESS_DEFICIT|LEDGER_WRITE|AUDIT_EVIDENCE|LAW_CONFLICT" errors.md` → no matches.
`grep -nE "WITNESS_DEFICIT|LEDGER_WRITE|AUDIT_EVIDENCE|LAW_CONFLICT" errors.py` → only `CROSS_SOCIETY_LAW_CONFLICT` (distinct code, distinct condition).

**Impact**: An implementer following SAL §9 to map SAL error conditions to canonical error codes will fail to find four of the nine codes in `errors.md` or `errors.py`. Wire-breaking for any code that emits these as canonical codes. The intra-§9 duplication (WITNESS_QUORUM vs WITNESS_DEFICIT) is also internally incoherent — same condition, two codes.

**Remediation** (out of scope for this audit, but the design call is clear):
- Either **add** `W4_ERR_WITNESS_DEFICIT`, `W4_ERR_LEDGER_WRITE`, `W4_ERR_AUDIT_EVIDENCE`, `W4_ERR_LAW_CONFLICT` to `errors.md` taxonomy and `errors.py` enum (with HTTP status mappings), **or** consolidate to existing codes:
  - WITNESS_DEFICIT → fold into existing `W4_ERR_WITNESS_QUORUM` (same condition, the SAL §9 second row is a duplicate)
  - LAW_CONFLICT → could subsume into `W4_ERR_CROSS_SOCIETY_LAW_CONFLICT` if scope matches, otherwise add a same-society variant
  - LEDGER_WRITE / AUDIT_EVIDENCE → new codes needed (no existing close match)
- Either way, eliminate the duplicate row at L298.

---

### H2: §5.5 `AuditRequest` canonical-extract JSON uses `basis` for evidence; SDK uses `evidence`

**Location**:
- SAL §5.5 L200: `"basis": ["hash:...","hash:..."]` in `Web4AuditRequest` JSON example
- SDK `federation.py:226`: `evidence: List[str] = field(default_factory=list)` in `AuditRequest` dataclass; field name is **`evidence`**

**Severity**: HIGH

**Re-verification**:

SAL §5.5 L193–203 (re-read):
```json
{
  "type": "Web4AuditRequest",
  "society": "lct:web4:society:...",
  "targets": ["lct:web4:citizen:..."],
  "scope": ["context:data_analysis"],
  "basis": ["hash:...","hash:..."],
  "proposed": {"t3":{"temperament":-0.02}, "v3":{"veracity":-0.03}}
}
```

SDK `federation.py:212–233` (re-read):
```python
@dataclass
class AuditRequest:
    """ ... Request to adjust T3/V3 tensors via auditor role (§5.5). ... """
    audit_id: str
    society_id: str
    auditor_lct: str
    targets: List[str]
    scope: List[str]
    evidence: List[str]          # ← named `evidence`, not `basis`
    proposed_t3_deltas: Dict[str, float] = field(default_factory=dict)
    proposed_v3_deltas: Dict[str, float] = field(default_factory=dict)
    timestamp: str = ""
```

Note also that the SDK's `AuditRequest.proposed_t3_deltas` / `proposed_v3_deltas` are *two flat top-level fields*, whereas SAL §5.5 L201 nests them: `"proposed": {"t3": ..., "v3": ...}`. That is a second wire-shape divergence under the same finding.

**Impact**: A cross-language implementer consuming the SAL §5.5 JSON-format example will emit `basis` (and a nested `proposed`); the Python SDK will reject both. Calibration: this is the same severity class as C14's `roleType`→`roleLCT` (HIGH for wire-JSON divergence of a normative example).

**Remediation** (out of scope): change SAL §5.5 L200 example to use `"evidence":` and either (a) flatten `"proposed":` into `"proposed_t3_deltas":` / `"proposed_v3_deltas":`, or (b) keep the nested shape and update the SDK serializer to match. SDK is authority for runtime behavior; spec example should track SDK unless a deliberate redesign is intended.

---

## MEDIUM Findings

### M1: §5 role taxonomy (5 roles) contradicts the canonical society-roles.md taxonomy (7 base-mandatory + 2 context-mandatory)

**Location (SAL)**: §5 heading line 166 (*"Roles: Citizen, Authority, Oracle"*) + subsections §5.1 Citizen, §5.2 Authority, §5.3 Law Oracle, §5.4 Witness, §5.5 Auditor (lines 166–219).

**Severity**: MEDIUM (spec-vs-spec — SDK has parallel dual taxonomies, so this is the rare case where two SDK modules disagree along the same spec-vs-spec divergence)

**Re-verification**:

- SAL §5 lists **5 roles**: Citizen / Authority / Law Oracle / Witness / Auditor.
- `federation.py:78–85` (re-read) `RoleType` enum has **5 values matching SAL**: `CITIZEN`, `AUTHORITY`, `LAW_ORACLE`, `WITNESS`, `AUDITOR`. Module docstring at L4 says it implements "web4-society-authority-law.md and SOCIETY_SPECIFICATION.md".
- `society-roles.md:51` (re-read) — *"Every Web4-compliant society MUST have these seven roles filled"* — and §2.1–§2.7 enumerate **Sovereign, LawOracle, PolicyEntity, Treasurer, Administrator, Archivist, Citizen** (7 base-mandatory), with **Witness** and **Auditor** as context-mandatory (§3).
- `role.py:43–91` (re-read) `SocietyRole` enum has **9 values matching society-roles.md**: `SOVEREIGN`, `LAW_ORACLE`, `POLICY_ENTITY`, `TREASURER`, `ADMINISTRATOR`, `ARCHIVIST`, `CITIZEN`, `WITNESS`, `AUDITOR`.

So the SDK carries **two parallel role enums** along the same spec-vs-spec line: `federation.py::RoleType` (5 values, matches SAL §5) and `role.py::SocietyRole` (9 values, matches society-roles.md). Both modules are imported by `society.py` (`federation` directly; `role` via the `__init__.py` surface). Of particular note: SAL's "Authority" is a **role** in SAL §5.2; society-roles.md does NOT include Authority as a role — in the newer model, "authority" is a *delegation* concept (cf. `federation.py::Delegation` and society-roles.md's separate `Authority scope` sections within each base role's definition).

**Impact**: An implementer reading SAL §5 to enumerate the roles a society must fill will under-count by 4 (missing Sovereign, PolicyEntity, Treasurer, Administrator, Archivist) and mis-include "Authority" as a role rather than as a delegation primitive. Severity is MEDIUM rather than HIGH because both taxonomies are simultaneously supported by SDK code (parallel `RoleType` + `SocietyRole`), so it is not a runtime contradiction — but it is a normative-content contradiction between two `core-spec/` documents.

**Remediation** (out of scope, design Q): the authoritative position has to be set externally — either SAL §5 is amended to align with the newer society-roles.md 7+2 taxonomy (and `federation.py::RoleType` is deprecated in favor of `role.py::SocietyRole`), or society-roles.md narrows to acknowledge SAL §5 as the canonical role enum (and `role.py::SocietyRole` is demoted to "non-normative role-naming convention"). Tag: **`DESIGN-Q`** — needs operator/cross-model decision (parallel to the C15 H1 averaging-vs-accumulating reputation question).

---

### M2: §4.1 `LawDataset` JSON uses key `id` for norms/procedures/interpretations; SDK serializes `norm_id` / `procedure_id` / `interpretation_id`

**Location**:
- SAL §4.1 L153: `"norms": [{"id":"LAW-ATP-LIMIT","selector":"r6.resource.atp","op":"<=","value":100}]`
- SAL §4.1 L154: `"procedures": [{"id":"PROC-WIT-3","requiresWitnesses":3}]`
- SAL §4.1 L155: `"interpretations": [{"id":"INT-42","replaces":"INT-41","reason":"edge case fix"}]`
- SDK `federation.py:709` (re-read): `norm_to_dict` emits `"norm_id"` as the key (not `"id"`)
- SDK `federation.py:733` (re-read): `procedure_to_dict` emits `"procedure_id"` (not `"id"`)
- SDK `federation.py:753` (re-read): `interpretation_to_dict` emits `"interpretation_id"` (not `"id"`)

**Severity**: MEDIUM (wire-JSON naming divergence — three keys)

**Re-verification**: `federation.py:707–717`:
```python
def norm_to_dict(norm: Norm) -> dict[str, Any]:
    d: dict[str, Any] = {
        "norm_id": norm.norm_id,
        "selector": norm.selector,
        "op": norm.op,
        "value": norm.value,
    }
    ...
```

Plus: SAL L154 uses **camelCase** `requiresWitnesses`; SDK `procedure_to_dict` emits **snake_case** `requires_witnesses` (federation.py:735). Same divergence as the `id` case — one more wire-naming difference under this same finding.

**Impact**: Cross-language clients deserializing the SAL §4.1 JSON example into the SDK will need a translation layer for at least 4 key renames (norms.`id`→`norm_id`, procedures.`id`→`procedure_id`, procedures.`requiresWitnesses`→`requires_witnesses`, interpretations.`id`→`interpretation_id`).

**Remediation** (out of scope): SDK is authority for wire serialization. Update SAL §4.1 example to use `norm_id` / `procedure_id` / `requires_witnesses` / `interpretation_id`, OR change SDK `*_to_dict` functions to use `"id"` and `"requiresWitnesses"` if the SAL camelCase + `id` convention is the intended wire format. Pick one.

---

### M3: §4.1 `LawDataset` includes `r6Bindings` field; SDK `LawDataset` has no `r6_bindings` field

**Location**:
- SAL §4.1 L156 (re-read): `"r6Bindings": ["web4://schemas/r6-rules-v1"]` — last field in the JSON-LD structure.
- SDK `federation.py:331–346` (re-read) `LawDataset` dataclass: fields are `law_id`, `version`, `society_id`, `norms`, `procedures`, `interpretations`, `timestamp`. **No `r6_bindings` field.**
- SDK `federation.py:770–780` `law_dataset_to_dict` serializes `law_id`, `version`, `society_id`, `norms`, `procedures`, `interpretations`, `hash`. **No `r6_bindings` key in wire JSON.**

**Severity**: MEDIUM (missing field for a normative R6-mapping primitive)

**Impact**: SAL §6 (R6 ↔ SAL mapping table) describes R6 `Rules = Law Oracle norms + procedures` with `lawHash` pinning at action time. `r6Bindings` in §4.1 is the field that names the R6-rules-schema URI the law dataset complies with. Without a corresponding SDK field, R6 execution engines (cf. `r6.py`) have no way to discover which R6 rules schema a given law dataset binds to.

**Remediation** (out of scope): Add `r6_bindings: List[str] = field(default_factory=list)` to `LawDataset` and to `law_dataset_to_dict` / `law_dataset_from_dict`. Cross-coordinate with `r6.py` to confirm whether anything currently consumes this field — if not, this is documentation-of-intent vs ratified primitive.

---

### M4: §3.4 Ledger Interface defines `append / get / prove / events`; SDK `SocietyLedger` provides `append / query / get_entry / amend` — two ops missing, two ops renamed

**Location**:
- SAL §3.4 L110–118 (re-read): Ledger Interface (minimum):
  ```json
  {
    "append": {"object": "<bytes|CBOR>", "topic": "sal.event", "parent": "hash|null"},
    "get":    {"hash": "sha256-..."},
    "prove":  {"hash": "sha256-..."},
    "events": {"topic": "sal.*", "from": "block:height"}
  }
  ```
- SDK `society.py:121–192` (re-read) `SocietyLedger` provides: `append(entry)` (L131), `query(event_type, action)` (L135), `get_entry(entry_id)` (L148), `amend(original_id, amendment)` (L155), plus `active_entries` property and `entry_count`. **No `prove`** (no inclusion-proof API). **No `events`** (no topic subscription / from-height stream). **`get` is renamed `get_entry` and takes an entry_id (not a hash)**.

**Severity**: MEDIUM (interface-shape divergence with normative "MUST" backing in §3.4 L104)

**Impact**: §3.4 declares the four-op interface as **MUST** (line 104 *"Each society MUST operate or bind to an Immutable Record service ..."*). An SDK-only implementer cannot offer the `prove` (inclusion proof) and `events` (topic subscription) operations the spec mandates. The `get(hash)` vs `get_entry(entry_id)` divergence is a content-addressing-vs-id-keying philosophical difference — content-addressed objects (per SAL §3.4 L107 *"content-addressed objects (hash-linked) with inclusion proofs"*) cannot be cleanly recovered from the SDK's id-keyed `get_entry`.

**Remediation** (out of scope): EITHER add `prove(hash) → inclusion_proof` and `events(topic, from_height) → stream` methods to `SocietyLedger` (and add a content-addressed `get(hash)` accessor), OR revise SAL §3.4 to scope the "MUST" to the operations the SDK actually implements. The first option preserves SAL §3.4 normative intent; the second pares the spec back to what is implemented.

---

### M5: §3.4 event-topic names (`sal.birth`, `sal.role.bind`, `sal.law.update`, `sal.audit.adjust`) diverge from SDK `LedgerEventType` enum

**Location**:
- SAL §3.4 L108 (re-read): *"Emits **event topics** for SAL-relevant updates (e.g., `sal.birth`, `sal.role.bind`, `sal.law.update`, `sal.audit.adjust`)."*
- SDK `society.py:89–96` (re-read) `LedgerEventType` enum:
  ```python
  CITIZENSHIP = "citizenship"   # join/leave/suspend/reinstate
  LAW_CHANGE  = "law_change"    # propose/ratify/amend/repeal
  ECONOMIC    = "economic"      # allocate/deposit/reclaim
  METABOLIC   = "metabolic"     # state transitions
  FORMATION   = "formation"     # phase transitions, incorporation
  ```

**Severity**: MEDIUM (wire-event naming divergence + missing AUDIT event type)

**Re-verification**:
- SAL `sal.birth` ↔ SDK `CITIZENSHIP` action="grant" (cf. `society.py:462`) — different naming/shape.
- SAL `sal.role.bind` ↔ SDK **no equivalent** (role binding isn't a LedgerEventType — it would go under CITIZENSHIP or FORMATION).
- SAL `sal.law.update` ↔ SDK `LAW_CHANGE`.
- SAL `sal.audit.adjust` ↔ SDK **no equivalent** (no `AUDIT` LedgerEventType; auditor adjustments don't have a dedicated event topic).

**Impact**: A cross-implementation event subscriber following the SAL §3.4 example will look for `sal.audit.adjust` topics that the SDK never emits, and will miss `ECONOMIC` / `METABOLIC` / `FORMATION` events the SDK *does* emit. The 1:1 mapping between spec example and SDK is roughly half-coverage.

**Remediation** (out of scope): Reconcile the two naming systems — either prefix SDK `LedgerEventType` values with `sal.` and rename to dot-namespaced form (matching SAL), or update SAL §3.4 to list the SDK names as the canonical topic set and explain that `sal.*` was an illustrative scheme. Add an AUDIT event type to the SDK to cover `sal.audit.adjust` if that is intended to be a distinct topic.

---

### M6: §5.5 Adjustment Policy **MUST** include cool-down period; SDK `AuditAdjustment` has no `cool_down_period` field

**Location**:
- SAL §5.5 L208 (re-read): *"Negative adjustments **MUST** include **appeal path** and **cool-down period**."*
- SDK `federation.py:236–268` (re-read) `AuditAdjustment` dataclass: fields are `audit_id`, `target_lct`, `applied_t3_deltas`, `applied_v3_deltas`, `witnesses`, `appeal_path` (L250), `timestamp`. **No `cool_down_period` field.**
- SDK `AuditAdjustment.is_valid()` (L264) only checks `appeal_path` presence on negative adjustments; **does not check cool-down period.**

**Severity**: MEDIUM (missing field for a normative MUST)

**Impact**: An implementer cannot represent or validate the SAL §5.5 cool-down requirement using `AuditAdjustment` as-is. `is_valid()` returns True for negative adjustments that have an appeal path but no cool-down period — violating the SAL MUST.

**Remediation** (out of scope): Add `cool_down_period: Optional[str] = None` (ISO 8601 duration) or `cool_down_until: Optional[str] = None` (ISO timestamp) to `AuditAdjustment`; update `is_valid()` to require this on negative adjustments alongside `appeal_path`.

---

### M7: §2.2 Birth Certificate uses `initialRights` / `initialResponsibilities`; SDK `CitizenshipRecord` uses `rights` / `obligations`

**Location**:
- SAL §2.2 L57–58 (re-read): `"initialRights": [...]`, `"initialResponsibilities": [...]`
- SDK `federation.py:128–129` (re-read):
  ```python
  rights: List[str] = field(default_factory=lambda: ["exist", "interact", "accumulate_reputation"])
  obligations: List[str] = field(default_factory=lambda: ["abide_law", "respect_quorum"])
  ```

**Severity**: MEDIUM (wire-naming divergence; *default values* match SAL exactly — only the field names differ, plus `responsibilities` vs `obligations` is a semantic-synonym variance)

**Re-verification**:
- SAL `initialRights` defaults: `["exist", "interact", "accumulate_reputation"]`
- SDK `CitizenshipRecord.rights` default: `["exist", "interact", "accumulate_reputation"]` ✓ values match exactly
- SAL `initialResponsibilities` defaults: `["abide_law", "respect_quorum"]`
- SDK `CitizenshipRecord.obligations` default: `["abide_law", "respect_quorum"]` ✓ values match exactly

So this finding is purely about the **field-name keys** (and the synonym `responsibilities` vs `obligations`). The `initial` prefix in SAL emphasizes that the birth-certificate values are *frozen at genesis* (immutable starting state) while SDK `CitizenshipRecord` fields are mutable per-record state — that semantic difference also explains why the SDK chose to drop the `initial` prefix.

**Impact**: Wire-JSON for a `Web4BirthCertificate` (SAL) cannot be round-tripped through `CitizenshipRecord` without a key-rename layer.

**Remediation** (out of scope): Pick one terminology and align. SDK is authority for runtime; spec wire-shape is informational unless a separate `BirthCertificate` type is added (see L1 finding below).

---

### M8: §3.3 MRH (RDF) Edges declare a turtle vocabulary not formalized in the canonical ontology directory; canonical ontology references a missing `sal-ontology.ttl`

**Location**:
- SAL §3.3 L81–101 (re-read) declares normative turtle edges:
  ```turtle
  lct:entity web4:pairedWith lct:roleCitizen .
  lct:entity web4:memberOf   lct:societyRoot .
  lct:societyRoot web4:hasAuthority lct:authorityRole .
  lct:societyRoot web4:hasLawOracle lct:lawOracle .
  lct:lawOracle   web4:publishes    lct:lawDatasetV120 .
  lct:authorityRole web4:delegatesTo lct:subAuthorityRole .
  ```
  followed by normative **"Implementations MUST expose these edges for SPARQL queries"** (L101).

- Canonical ontology `web4-standard/ontology/web4-core-ontology.ttl`:
  - L97 declares `web4:pairedWithRole` (note: **`pairedWithRole`**, with `Role` suffix) — domain `web4:Pairing`, range `rdfs:Resource`. NOT the same as SAL's `web4:pairedWith` (no suffix) with entity-as-subject / role-as-object.
  - L195 comment (re-read): *"web4:delegatesTo is defined in sal-ontology.ttl (AuthorityRole → AuthorityRole)."*
  - **`sal-ontology.ttl` does NOT exist in `web4-standard/ontology/`.** A file by that name exists only at `forum/nova/web4-sal-bundle/sal-ontology.ttl` (a non-canonical draft location).
  - Canonical ontology defines none of: `web4:memberOf`, `web4:hasAuthority`, `web4:hasLawOracle`, `web4:publishes`, `web4:hasWitness`, `web4:hasAuditor`, `web4:recordsOn`, `web4:attestedBy`, `web4:adjustedBy`.

- Forum-draft ontology `forum/nova/web4-sal-bundle/sal-ontology.ttl` (re-read in full): DOES define `web4:pairedWith` (no suffix), `web4:memberOf`, `web4:hasAuthority`, `web4:hasLawOracle`, `web4:publishes`, `web4:delegatesTo`, `web4:hasWitness`, `web4:hasAuditor`, `web4:recordsOn`, `web4:attestedBy`, `web4:adjustedBy` — matching SAL §3.3 + §7.1.1 vocabulary. But this file is in `forum/nova/`, not in the canonical ontology directory, so it is not authoritative.

**Severity**: MEDIUM (normative MUST claim references RDF vocabulary not formalized in the canonical ontology directory; canonical ontology references a file that doesn't exist there)

**Sub-issue (kept as part of M8, not split out)**: The forum-draft `sal-ontology.ttl` declares `web4:pairedWith` with **domain=`web4:Society`** and **range=`web4:CitizenRole`** (Society as subject). SAL §3.3 L88 uses it as `lct:entity web4:pairedWith lct:roleCitizen` (**entity as subject**). Even within the forum-draft view, the spec example and the (draft) ontology disagree on the predicate's domain. Either the spec example should read `lct:societyRoot web4:pairedWith lct:roleCitizen` (Society subject), or the draft ontology should change its domain to `rdfs:Resource` (entity subject). This is internal to the SAL/forum-draft pair and resolves whichever direction the M8 remediation takes.

**Impact**: An implementer trying to comply with SAL §3.3 L101's MUST faces a vocabulary-resolution problem: (a) canonical ontology lacks the SAL predicates; (b) canonical ontology refers them to `sal-ontology.ttl` which isn't in the canonical location; (c) only the forum-draft file actually defines them, and it disagrees with SAL on `pairedWith` domain. Trust-propagation and SPARQL-validation implementations cannot pick a single authoritative vocabulary.

**Remediation** (out of scope): Promote `forum/nova/web4-sal-bundle/sal-ontology.ttl` (or a revised version) into `web4-standard/ontology/sal-ontology.ttl` as the canonical SAL ontology; reconcile the `pairedWith` domain with SAL §3.3 usage; cross-reference from `web4-core-ontology.ttl:195` to confirm the now-canonical location. Coordination needed with the `web4-core-ontology.ttl` maintainers.

---

## LOW Findings

### L1: SDK has no distinct `BirthCertificate` type; SAL §2.2 BirthCertificate fields are partly conflated into `CitizenshipRecord`

**Location**:
- SAL §2.2 L44–60 specifies a `Web4BirthCertificate` JSON-LD object with fields: `@context`, `type`, `entity`, `citizenRole`, `society`, `lawOracle`, `lawVersion`, `birthTimestamp`, `witnesses`, `genesisBlock`, `initialRights`, `initialResponsibilities`.
- SDK has **no `BirthCertificate` class** (grep `federation.py`, `society.py`, `__init__.py` — no match for `BirthCertificate`). The closest analog is `CitizenshipRecord` (`federation.py:116–155`) which carries: `entity_lct`, `society_id`, `status`, `rights`, `obligations`, `witnesses`, `granted_at`, `suspended_at`, `terminated_at`.
- Missing from `CitizenshipRecord`: `citizenRole` (the role LCT ID); `lawOracle`; `lawVersion`; `genesisBlock` (the genesis-block reference for ledger anchoring).

**Severity**: LOW (under-implementation; not wire-breaking because the SDK never emits a `Web4BirthCertificate` object, so there's no divergence to expose — just a missing object type)

**Impact**: An implementation following SAL §2.2's `MUST` to "Record a Birth Certificate object" (L41) cannot do so via the SDK alone — would need an external object type. The provenance fields (`lawOracle`, `lawVersion`, `genesisBlock`) tying a citizen's birth to a specific law version + ledger block aren't preserved by `CitizenshipRecord`.

**Remediation** (out of scope): Add `BirthCertificate` dataclass to `federation.py` (or to a new `birth.py`) with the SAL §2.2 field set. Cross-link `CitizenshipRecord` to point at its `BirthCertificate` via certificate id.

---

### L2: SAL §4.1 `Web4LawDataset` has top-level field `id`; SDK `LawDataset` uses `law_id`

**Location**:
- SAL §4.1 L151 (re-read): `"id": "web4://law/society/1.2.0"` — top-level field.
- SDK `federation.py:340` (re-read): `law_id: str` field, serialized as `"law_id"` (federation.py:773).

**Severity**: LOW (one more wire-naming divergence to file alongside M2; kept separate because M2 is about *list-element* `id` keys while this is the *top-level* `id`)

**Impact**: Cross-language consumers see four total `id`→`*_id` renames across the `Web4LawDataset` JSON (top-level + 3 list elements per M2). Calls for a coordinated rename decision.

**Remediation** (out of scope): part of the same alignment decision as M2.

---

## Informational (not findings — flagged for downstream coordination)

**I1 — `r6-framework.md` References section misnames SAL**: `r6-framework.md` L604 cites `SOCIETY_SPECIFICATION.md` with the parenthetical *"Society-Authority-Law (SAL) governance framework"*. SAL is `web4-society-authority-law.md`; `SOCIETY_SPECIFICATION.md` is a *different* spec covering society lifecycle and treasury. This is a defect in **r6-framework.md**, NOT SAL, so it is out of scope for this audit; flagged here so a future r6/r7 audit cycle can pick it up.

**I2 — society.py `_register_citizen` overrides federation.py CitizenshipRecord defaults**: `society.py:408` writes `rights=["vote", "propose", "allocate"]` and `obligations=["abide_law", "witness"]`; `federation.py:128–129` defaults are `rights=["exist", "interact", "accumulate_reputation"]` and `obligations=["abide_law", "respect_quorum"]`. The federation.py defaults match SAL §2.2; the society.py override does not. **SDK-internal inconsistency**, not SAL-vs-SDK. Out of scope.

**I3 — `create_society` minimum-founders constraint**: `society.py:317` requires `len(founders) >= 2`; SAL §2.1 is silent on minimum founders; `role.py::bootstrap_society_roles` already supports solo-founder. The minimum-founders constraint is a SOCIETY_SPECIFICATION concern, not SAL §2.1. Out of scope.

---

## Audit Methodology

- **Authority-hierarchy preamble** explicit per BC#1.
- **Each finding's spec citation re-read at the cited line before writing the finding text** per BC#2 (the C-series guardrail).
- **Every "spec Y has/lacks Z" claim was backed by direct `Grep`** over the cited spec per BC#3 (the #105 L1 canonical failure mode).
- **Every "SDK does X" claim was backed by re-`Read` of the SDK function** per BC#4 (the C11 M2/M6 canonical failure mode).
- **Severity calibration anchored to C12-C15 precedent** per BC#5 — HIGH for wire-breaking; MEDIUM for field/enum renames matching SDK authority; LOW for doc-hygiene / under-implementation.
- **3 candidate findings were demoted to non-defects** with explicit rationale (the SOCIETY_SPECIFICATION minimum-founders mismatch; the society.py-vs-federation.py default-rights inconsistency; the r6-framework.md SOCIETY_SPECIFICATION misnaming) — the overcall-discipline value-add per BC#9.
- **No remediation patches** in this audit per BC#7. Findings only.
- **M1 + H1 second-half tagged `DESIGN-Q`** because remediation requires an external decision (5-role vs 7+2-role canonical; consolidate vs add error codes).
