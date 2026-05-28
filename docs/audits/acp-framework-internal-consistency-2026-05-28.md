# C18: acp-framework.md Internal Consistency Audit

**Date**: 2026-05-28
**Auditor**: Autonomous session (legion-web4-20260528-060057)
**Document**: `web4-standard/core-spec/acp-framework.md` (647 lines)

**Authority hierarchy used for this audit** (each cross-reference re-read at the cited line):

| Claim class | Authority | File(s) |
|-------------|-----------|---------|
| ACP error taxonomy (class names + `W4_ERR_ACP_*` codes) | SDK | `web4-standard/implementation/sdk/web4/acp.py:77-128` |
| Canonical Web4 error families (`W4_ERR_*`) | spec | `web4-standard/core-spec/errors.md` (categories §2.1-§2.6: BINDING/PAIRING/WITNESS/AUTHZ/CRYPTO/PROTO) |
| ACP wire format (JSON-LD field casing) | SDK + schema | `web4-standard/implementation/sdk/web4/acp.py` `to_dict()` / `to_jsonld()`; `web4-standard/schemas/acp-jsonld.schema.json` |
| HumanApproval mode enum | SDK + schema + test vector | `acp.py:163-168` (`ApprovalMode` enum: AUTO/MANUAL/CONDITIONAL); `acp-jsonld.schema.json:80`; `test-vectors/schema-validation/acp-jsonld-validation.json:480-491` (mode validity test) |
| Canonical V3 dimension names | spec | `web4-standard/core-spec/t3-v3-tensors.md:227-229,245-246,532,539` (valuation/veracity/validity) |
| Intent shape | spec self-reference | `acp-framework.md:99-121` (§2.2 Intent block) |
| Decision/ExecutionRecord witnesses field | spec self-reference | `acp-framework.md:135,164` (`witnesses: [...]` arrays) |
| `acp:` RDF predicate vocabulary | ontology TTL | `web4-standard/ontology/web4-core-ontology.ttl` + `t3v3-ontology.ttl` (NONE found — see M6) |
| `web4_context` envelope contents casing | spec | `web4-standard/core-spec/mcp-protocol.md:127-137,150-165` (snake_case keys including `proof_of_agency`) |
| State machine 8-state model | spec + SDK | `acp-framework.md:217-225` (§3.2 state table); `acp.py:134-144` (`ACPState` enum 8 values) |

Where divergence is **spec-vs-spec** rather than spec-vs-SDK, the finding labels it as such and does not silently promote one spec over the other.

---

## Summary

| Severity | Count | Theme |
|----------|-------|-------|
| HIGH | 3 | §4.1 raises undefined `InsufficientWitnesses` (canonical = `WitnessDeficit`); §5.1 raises 3 fully-undefined exceptions (`IllegalTrigger`, `ExcessiveResourceCap`, `InsufficientWitnessLevel`); §2.1 `humanApproval.mode` example value is wire-INVALID per shipped JSON-LD schema + test vector |
| MEDIUM | 7 | §10.1 lists 6 of SDK's 8 error classes (missing `InvalidTransition` + `ResourceCapExceeded` — the latter is itself raised by §4.1); W4_ERR_ACP_* family absent from canonical `errors.md` taxonomy; §2.1 resourceCaps example snake_case vs JSON-LD-schema/SDK camelCase; §2.4 `t3v3Delta` uses non-canonical V3 dim `value`; §4.1 references `intent.witnesses` field that does not exist in §2.2 Intent shape; §8.1/§8.2 `acp:` RDF + SPARQL predicates absent from any canonical ontology TTL; §5.2 `witness_requirement` structured object vs §2.1 integer `witnessLevel` — two unbridged witness data models |
| LOW | 1 | §4.2 `proofOfAgency` (camelCase) keyed inside snake_case `web4_context` envelope vs `mcp-protocol.md` §4.1 `proof_of_agency` (snake_case) inside the same envelope |

**Cross-audit calibration note**: This audit follows C12 (r6, #229/#231), C13 (t3-v3, #230/#232), C14 (r7, #233/#234), C15 (reputation-computation, #236/#237), C16 (SAL, #239/#240), C17 (dictionary-entities, #241/#242). Severity calibration:
- **HIGH** = wire-breaking divergence (normative pseudocode raising undefined exceptions = the spec is its own only definition; non-conforming example value flagged invalid by the schema and test vector that ship alongside the spec).
- **MEDIUM** = catalog/taxonomy gaps where SDK has more than spec, casing divergence between spec example and schema/SDK wire, non-canonical dimension keys, ontology absence, intra-spec data-model duplication.
- **LOW** = cross-spec casing divergence inside the same envelope (parser-tolerable, not wire-breaking, but a stumbling block for cross-spec implementers).

**Recurring patterns across C12-C18**:
- **Taxonomy gap** (C13/C14/C16-H1/C17-M4/**C18-M1+M2**): canonical error/role taxonomy lags subordinate spec usage. Recurring root-cause: errors.md and ontology TTLs are not updated when subordinate specs introduce new error classes / predicates.
- **`roleType` vs `roleLCT`-style stale field names** (C14-H1/C17-H2): NOT present in acp-framework — ACP entities use their own `acp:` URN scheme (`acp:plan:`, `acp:intent:`) rather than R6/R7 `role.roleLCT`, so this recurring pattern does NOT recur here.
- **Witness shape mismatches** (C17-M2/**C18-M5+M7**): C17 caught `witness_attestation` array-vs-object shape break; C18 catches `intent.witnesses` field-doesn't-exist + §5.2/§2.1 structured-vs-integer witness models. Witness-shape divergence is now a recurring class.
- **Snake_case/camelCase wire inconsistency** (**novel in C18-M3 + C18-L3**): the §2.1 resourceCaps example AND the §4.2 `web4_context` envelope contents have casing splits with their canonical wire format. C18 surfaces this as a new pattern class.
- **Ontology absence** (C17-M1/C16-M8/**C18-M6**): subordinate-spec RDF + SPARQL examples reference predicates absent from canonical TTL. Confirmed recurring; cannot be resolved without ontology-maintainer coordination.

**Demoted candidate findings** (overcall-discipline value-add):

1. **§2.1 L43-44 LCT entity placeholders `lct:web4:entity:CLIENT` / `lct:web4:entity:AGENT` (UPPERCASE)** — initial review flagged as non-conformant to lowercase convention. **Demoted** after corpus verification: `entity-types.md:346-347` uses the IDENTICAL pair (`"client": "lct:web4:entity:CLIENT", "agent": "lct:web4:entity:AGENT"`) in the §10.2 CombinedAgencyEnvelope example. The uppercase-CLIENT/AGENT pair is an established corpus convention for the client/agent placeholder pair specifically. Not a defect.

2. **§2.1 L91 `"signatures": [...]` (ellipsis-as-value)** — initial review flagged as placeholder hygiene. **Demoted** after corpus verification: `entity-types.md:371` uses `"signatures": [...]` and `mcp-protocol.md:387` uses `"witness_signatures": [...]` with the same ellipsis-as-value convention. Corpus-wide placeholder convention. Not a defect (consistent with `lawHash: "sha256:..."` ellipsis convention also present in this spec at L76).

Every cross-reference below was re-read against the live file at the cited line.

---

## HIGH Findings

### H1: §4.1 `validate_acp_agency()` pseudocode raises `InsufficientWitnesses()` exception that is undefined in §10.1 and absent from SDK

**Location (acp-framework)**: §4.1 Agency Requirements, normative pseudocode lines 233–253. Specifically:
- L250: `raise InsufficientWitnesses()`

**Severity**: HIGH (matches C17 H2 / C14 H1 severity calibration — a normative example raising an exception class that exists nowhere produces non-conformant code that downstream implementations have no shape to match against).

**Re-verification**:

```
$ grep -n "InsufficientWitnesses\|WitnessDeficit" web4-standard/core-spec/acp-framework.md
250:        raise InsufficientWitnesses()
504:class WitnessDeficit(ACPError):
527:    elif isinstance(error, WitnessDeficit):
```

So the spec itself defines the canonical class `WitnessDeficit` at L504 (§10.1) AND uses it correctly at L527 (§10.2 error recovery dispatch) — but L250 (§4.1) raises a different, undefined name `InsufficientWitnesses`.

Corpus-wide sweep confirms `InsufficientWitnesses` exists ONLY at this one site:

```
$ grep -rn "InsufficientWitnesses" web4-standard/
web4-standard/core-spec/acp-framework.md:250:        raise InsufficientWitnesses()
```

No SDK definition — `web4-standard/implementation/sdk/web4/acp.py` defines `WitnessDeficit` (L101, code `W4_ERR_ACP_WITNESS_DEFICIT`) but no `InsufficientWitnesses` class.

**Impact**: §4.1 is a normative reference algorithm for ACP-AGY integration. An implementer following the pseudocode literally would either (a) hit a NameError at runtime, (b) define their own `InsufficientWitnesses` class that diverges from the canonical `WitnessDeficit` taxonomy (and thus a different W4_ERR_* code), or (c) silently skip the check. Any of the three is non-conformant.

**Remediation direction**: One-token fix — `InsufficientWitnesses()` → `WitnessDeficit()` at L250. Matches §10.1 + §10.2 + SDK convention. Autonomous-actionable.

---

### H2: §5.1 `check_law_compliance()` pseudocode raises three undefined exceptions

**Location (acp-framework)**: §5.1 Law Compliance, normative pseudocode lines 291–310. Specifically:
- L299: `raise IllegalTrigger(trigger)`
- L303: `raise ExcessiveResourceCap()`
- L307: `raise InsufficientWitnessLevel()`

**Severity**: HIGH (3 sites in one normative algorithm; same calibration as H1 — undefined-everywhere exception names in normative pseudocode).

**Re-verification**:

```
$ grep -n "IllegalTrigger\|ExcessiveResourceCap\|InsufficientWitnessLevel" web4-standard/core-spec/acp-framework.md
299:            raise IllegalTrigger(trigger)
303:        raise ExcessiveResourceCap()
307:        raise InsufficientWitnessLevel()
```

Corpus-wide sweep confirms all three names exist ONLY at these sites in acp-framework.md (and `errors.py`/`acp.py` SDK files contain none of them — verified empty grep on `web4-standard/implementation/sdk/web4/*.py`).

```
$ grep -rn "IllegalTrigger\|ExcessiveResourceCap\|InsufficientWitnessLevel" web4-standard/
web4-standard/core-spec/acp-framework.md:299:            raise IllegalTrigger(trigger)
web4-standard/core-spec/acp-framework.md:303:        raise ExcessiveResourceCap()
web4-standard/core-spec/acp-framework.md:307:        raise InsufficientWitnessLevel()
```

**Impact**: Same as H1, multiplied by three. The §5.1 algorithm is the canonical law-compliance check for ACP. An implementer has zero canonical class shapes to bind these names to.

**Remediation direction**: Map each undefined name to a canonical class in §10.1 + SDK. Suggested mappings (autonomous-actionable):
- `IllegalTrigger(trigger)` → `ScopeViolation(f"trigger {trigger} not allowed by law")` (the trigger-not-allowed check is semantically a scope violation against the law)
- `ExcessiveResourceCap()` → `ResourceCapExceeded()` (matches SDK class at acp.py:125 — but ALSO surfaces M1, since `ResourceCapExceeded` is not currently in §10.1; remediation should bundle M1 with H2 to keep the canonical class set consistent)
- `InsufficientWitnessLevel()` → `WitnessDeficit()` (same canonical class as H1)

H2 + M1 should be remediated in the same PR; resolving H2 without M1 leaves `ResourceCapExceeded` raised by §5.1 + §4.1 (L246) yet undocumented in §10.1.

---

### H3: §2.1 `humanApproval.mode` normative example value is wire-INVALID per the schema and test vector that ship with this spec

**Location (acp-framework)**: §2.1 Agent Plan example, line 84:
```json
"humanApproval": {
  "mode": "auto-if<=10 else prompt",
  "timeout": 3600,
  "fallback": "deny"
}
```

**Severity**: HIGH (this is the most prominent example in the spec — the §2.1 reference AgentPlan — and its `mode` field value would be REJECTED by `acp-jsonld.schema.json` AND would fail the validation test vector that ships in `test-vectors/schema-validation/acp-jsonld-validation.json:480-491`).

**Re-verification**:

Canonical enum (SDK):
```
$ grep -n "ApprovalMode" web4-standard/implementation/sdk/web4/acp.py
163:class ApprovalMode(str, Enum):
166:    AUTO = "auto"
167:    MANUAL = "manual"
168:    CONDITIONAL = "conditional"
```

Test vector explicitly validates that out-of-enum values are invalid:
```
$ sed -n '480,495p' web4-standard/test-vectors/schema-validation/acp-jsonld-validation.json
{
  "description": "Invalid humanApproval mode enum (not auto/manual/conditional)",
  "error_path": "guards.humanApproval.mode",
  ...
  "guards": {"humanApproval": {"mode": "always"}},
  ...
}
```

The spec's L84 value `"auto-if<=10 else prompt"` is a free-form DSL string that is neither in the canonical enum nor parseable as one of the three valid values. A JSON-LD validator using the shipped schema would reject the example.

**Impact**: An implementer constructing an AgentPlan from the §2.1 reference example and validating it against the shipped JSON-LD schema gets a hard validation failure on the first try. The spec's flagship example does not pass the spec's own conformance test.

**Remediation direction**: Replace `"auto-if<=10 else prompt"` with the canonical enum value `"conditional"`. The DSL semantics "auto if ≤10 else prompt" are expressible via the canonical mode `"conditional"` plus an `autoThreshold: 10` field — which SDK `HumanApproval` already has at L232 (`auto_threshold: float = 0.0`). Suggested replacement:
```json
"humanApproval": {
  "mode": "conditional",
  "autoThreshold": 10,
  "timeout": 3600,
  "fallback": "deny"
}
```
Autonomous-actionable.

---

## MEDIUM Findings

### M1: §10.1 error-class list has 6 classes; SDK acp.py defines 8 — missing `InvalidTransition` and `ResourceCapExceeded`

**Location (acp-framework)**: §10.1 Error Categories, lines 487–515 (6 classes listed); §4.1 L246 raises `ResourceCapExceeded()` without §10.1 defining it.

**Severity**: MEDIUM (catalog gap; downstream surface is the §4.1 pseudocode at L246 which raises an exception that has no §10.1 definition, plus the analogous H2 remediation site).

**Re-verification**:

SDK acp.py has 8 ACPError subclasses (verbatim, with line numbers from fresh grep per BC#4):

```
$ grep -n "^class\|error_code" web4-standard/implementation/sdk/web4/acp.py
77:class ACPError(Exception):
80:    error_code: str = "W4_ERR_ACP"
83:class NoValidGrant(ACPError):
86:    error_code = "W4_ERR_ACP_NO_GRANT"
89:class ScopeViolation(ACPError):
92:    error_code = "W4_ERR_ACP_SCOPE_VIOLATION"
95:class ApprovalRequired(ACPError):
98:    error_code = "W4_ERR_ACP_APPROVAL_REQUIRED"
101:class WitnessDeficit(ACPError):
104:    error_code = "W4_ERR_ACP_WITNESS_DEFICIT"
107:class PlanExpired(ACPError):
110:    error_code = "W4_ERR_ACP_PLAN_EXPIRED"
113:class LedgerWriteFailure(ACPError):
116:    error_code = "W4_ERR_ACP_LEDGER_WRITE"
119:class InvalidTransition(ACPError):
122:    error_code = "W4_ERR_ACP_INVALID_TRANSITION"
125:class ResourceCapExceeded(ACPError):
128:    error_code = "W4_ERR_ACP_RESOURCE_CAP_EXCEEDED"
```

Spec §10.1 lists: NoValidGrant, ScopeViolation, ApprovalRequired, WitnessDeficit, PlanExpired, LedgerWriteFailure — **6 of the 8 SDK classes**. Missing: `InvalidTransition` (W4_ERR_ACP_INVALID_TRANSITION) and `ResourceCapExceeded` (W4_ERR_ACP_RESOURCE_CAP_EXCEEDED).

The spec also raises `ResourceCapExceeded()` at L246 (§4.1) WITHOUT defining it in §10.1, creating an internal-only undefined-reference.

**Impact**: Spec implementers reading §10.1 alone get 6 classes; SDK consumers see 8. Conformance test authors using §10.1 as authority would miss the two SDK-only codes. The §4.1 pseudocode at L246 is internally broken pending M1 remediation.

**Remediation direction**: Add two class definitions to §10.1 matching SDK acp.py:119 + L125. Autonomous-actionable. Bundles with H2 remediation (H2 needs `ResourceCapExceeded` to exist in §10.1 to map `ExcessiveResourceCap()`).

---

### M2: W4_ERR_ACP_* error code family is absent from canonical `errors.md` taxonomy (DESIGN-Q)

**Location (errors.md)**: §2 Error Code Taxonomy categories §2.1-§2.6 = BINDING / PAIRING / WITNESS / AUTHZ / CRYPTO / PROTO. **No ACP category**.

**Severity**: MEDIUM (parallels C16 H1 and C17 M4 — same recurring pattern of subordinate spec defining error codes absent from canonical taxonomy).

**Re-verification**:

```
$ grep -n "W4_ERR_ACP" web4-standard/core-spec/errors.md
(no output)

$ grep -rn "W4_ERR_ACP\|W4_ERR_AGY" web4-standard/
web4-standard/ACP_INTEGRATION_SUMMARY.md:201:- `W4_ERR_ACP_NO_GRANT`: ...
web4-standard/ACP_INTEGRATION_SUMMARY.md:[6 ACP codes listed]
web4-standard/AGY_INTEGRATION_SUMMARY.md:[6 AGY codes listed]
web4-standard/implementation/sdk/web4/acp.py:[8 codes defined]
```

`W4_ERR_ACP_*` codes are defined in (a) SDK acp.py (8 codes), (b) ACP_INTEGRATION_SUMMARY.md (6 codes — informational, lags SDK), but ZERO codes in canonical `errors.md`. The same gap exists for W4_ERR_AGY_* (6 codes only in AGY_INTEGRATION_SUMMARY.md).

**Impact**: An implementer consulting errors.md as the canonical Web4 error taxonomy gets a complete picture for BINDING/PAIRING/WITNESS/AUTHZ/CRYPTO/PROTO but is unaware that two additional families (ACP, AGY) exist. RFC 9457 Problem Details responses emitting `W4_ERR_ACP_*` codes have no taxonomy entry to resolve against.

**Remediation direction**: DESIGN-Q. Requires operator + taxonomy-maintainer decision: should errors.md be extended with §2.7 ACP Errors + §2.8 AGY Errors (mirroring the 8 SDK acp.py codes + 6 AGY codes)? Or should the W4_ERR_ACP_*/W4_ERR_AGY_* families be merged into existing categories (e.g., W4_ERR_ACP_NO_GRANT → W4_ERR_AUTHZ_DENIED)? **DEFER** to operator decision queue; bundles with C16 H1 (W4_ERR_WITNESS overlap) + C17 M4 (W4_ERR_DICT) as the "canonical error taxonomy completion" cluster.

---

### M3: §2.1 `resourceCaps` example uses snake_case keys; SDK + JSON-LD schema use camelCase

**Location (acp-framework)**: §2.1 Agent Plan example, lines 77–80:
```json
"resourceCaps": {
  "max_atp": 25,
  "max_executions": 100,
  "rate_limit": "10/hour"
}
```

**Severity**: MEDIUM (wire-format inconsistency between flagship example and shipped JSON-LD schema; ambiguous which direction is canonical without cross-spec coordination).

**Re-verification — wire format**:

SDK `to_jsonld()`:
```
$ grep -n "maxAtp\|maxExecutions\|rateLimit" web4-standard/implementation/sdk/web4/acp.py
378:                        "maxAtp": self.guards.resource_caps.max_atp,
402:                    "maxAtp": self.guards.resource_caps.max_atp,
404:                    "rateLimit": self.guards.resource_caps.rate_limit,
445:                max_atp=rc.get("maxAtp", 0.0),
497:                    "maxAtp": self.guards.resource_caps.max_atp,
[etc — all SDK serialization is camelCase]
```

JSON-LD schema:
```
$ grep -n "maxAtp\|maxExecutions" web4-standard/schemas/acp-jsonld.schema.json
56:        "maxAtp": { "type": "number", "minimum": 0 },
```

**Cross-corpus state (informational, per BC#6 documented-not-solved)**:
- `r6-framework.md:472` uses `"agencyCaps": {"max_atp": 25, ...}` (snake_case)
- `r7-framework.md:793` uses `"agencyCaps": {"max_atp": 25, ...}` (snake_case)
- `entity-types.md:355` uses `"resourceCaps": {"max_atp": 25}` (snake_case)
- `mcp-protocol.md:344` uses `max_atp_per_request` (snake_case, but a different field)
- ACP JSON-LD schema (`schemas/acp-jsonld.schema.json:56`) + SDK acp.py to_jsonld emit camelCase `maxAtp` etc.

So the corpus state is: **all four spec examples use snake_case; the SDK's JSON-LD wire output + the JSON-LD schema use camelCase**. A JSON document constructed from the §2.1 example would fail validation against `acp-jsonld.schema.json` on the `maxAtp` required-property check.

**Impact**: Same shape as H3 — the §2.1 reference example fails the shipped schema. Distinct from H3 in that this is a CASING issue, not an enum-value issue, and it has corpus-wide implications (r6/r7/entity-types siblings would also fail).

**Remediation direction**: NOT proposed in this audit (per binding condition BC#6 — cross-corpus normalization is its own scope). Documented as a DESIGN-Q + cross-corpus pattern. Options for future operator decision:
- (A) Make spec examples + sibling corpus camelCase to match wire/schema/SDK (normalize 4+ corpus sites)
- (B) Make SDK to_jsonld + schema emit snake_case to match corpus example convention (revise SDK + schema)
- (C) Document that two casings are both wire-valid (modify schema to accept both keys)

**DEFER** to operator decision. This finding is informational — no remediation proposed in the audit-followup PR.

---

### M4: §2.4 `t3v3Delta` example uses non-canonical V3 dimension key `value`

**Location (acp-framework)**: §2.4 ExecutionRecord example, line 162:
```json
"t3v3Delta": {
  "agent": {"t3": {"temperament": +0.01}},
  "client": {"v3": {"value": +0.02}}
}
```

**Severity**: MEDIUM (canonical V3 has three dimensions: valuation, veracity, validity — `value` is not one of them; same dimension-key class as C15 H1's reputation-computation §7 issue, though here it's example-level not algorithm-level).

**Re-verification (per BC#7 — distinguishing field-name vs dim-name use)**:

In the structure `"v3": {DIM_NAME: NUMERIC_DELTA}`, the inner key occupies the dimension-name slot, not a field-value slot. Compare adjacent `"agent": {"t3": {"temperament": +0.01}}` where `"temperament"` IS a canonical T3 dimension. So the example pattern is explicitly dimension-keyed. The use of `value` in this slot is therefore a dimension-name claim, not a generic numeric field.

Canonical V3 dimension names (`t3-v3-tensors.md`):
```
$ grep -n "valuation\|veracity\|validity" web4-standard/core-spec/t3-v3-tensors.md
227:        "valuation": 0.95,
228:        "veracity": 0.98,
229:        "validity": 1.0,
[...]
532:| V3 composite weights | valuation=0.3, veracity=0.35, validity=0.35 | §3.3 | t3v3-002 |
539:| V3 calculation | valuation=(earned/expected)×satisfaction; ...
```

`value` is NOT a V3 dimension. (Note: per C15/exit #121 precedent, non-dimension `value` field usage is legitimate and was preserved — this finding applies ONLY to dimension-key occurrences, which is the case here.)

**Impact**: An implementer constructing an ExecutionRecord from the §2.4 example would produce a `t3v3Delta` with a `v3.value` key that downstream V3-aware code (which expects valuation/veracity/validity) cannot route or merge into a V3 vector. The delta is effectively dropped.

**Remediation direction**: Replace `value` with one of the canonical V3 dimensions. Without semantic context the most likely intent is `validity` (matches the "client" subject and the "value delivered" intuition), but `valuation` (most-frequently-named V3 dim in corpus) is equally defensible. Suggested replacement (autonomous-actionable, leaning on the most-corpus-common dim):
```json
"t3v3Delta": {
  "agent": {"t3": {"temperament": +0.01}},
  "client": {"v3": {"valuation": +0.02}}
}
```
Operator may prefer `validity` semantically.

---

### M5: §4.1 pseudocode references `intent.witnesses` but the §2.2 Intent shape has no `witnesses` field

**Location (acp-framework)**: §4.1 Agency Requirements, line 249:
```python
# 4. Check witness requirements
if len(intent.witnesses) < grant.witnessLevel:
    raise InsufficientWitnesses()
```

**Severity**: MEDIUM (intent-shape divergence — the same class of finding as C17 M2's `witness_attestation` shape mismatch).

**Re-verification — Intent shape in §2.2**:

```
$ sed -n '99,121p' web4-standard/core-spec/acp-framework.md
{
  "type": "ACP.Intent",
  "intentId": "acp:intent:...",
  "planId": "acp:plan:invoice-processor",
  "proposedAction": { ... },
  "proofOfAgency": { ... },
  "explain": { ... },
  "needsApproval": false,
  "createdAt": "..."
}
```

No `witnesses` field. SDK `Intent` dataclass (acp.py:614-633) also has no `witnesses` field. Witnesses live on:
- `Decision` (§2.3 L135, `acp.py:776`): `witnesses: List[str] = field(default_factory=list)`
- `ExecutionRecord` (§2.4 L164, `acp.py:891`): `witnesses: List[str] = field(default_factory=list)`

So `intent.witnesses` references a field that exists nowhere — neither in the spec example nor the SDK class.

**Impact**: Two divergent interpretations possible:
- (a) The §4.1 algorithm is checking the WRONG entity for witnesses — witnesses are gathered at the Decision stage (§2.3), not on the Intent. The check should happen during the approval-gate transition, not during agency validation.
- (b) The Intent shape is incomplete — it should carry a `witnesses` array for the agency-validation pre-check (which would also impact §10.2 retry semantics and the §3.1 lifecycle diagram).

**Remediation direction**: DESIGN-Q hinting at (a). The most defensible reading is that the agency-validation phase should NOT be checking witnesses (witnesses are an approval-gate concern, not an agency-grant concern). Suggested algorithmic correction (autonomous-actionable conditional on agreeing with reading (a)):
```python
# 4. Check witness requirements (deferred to approval-gate phase)
# Witness gathering is a §2.3 Decision-stage concern; agency validation
# only confirms grant scope + caps. See §3.2 Approval Gate state.
```
Operator may prefer to add a `witnesses` field to Intent (reading (b)) — this would expand the SDK Intent dataclass and is therefore a larger change. **PARTIAL DEFER** — the algorithmic correction is autonomous-actionable; the shape-extension is DESIGN-Q.

---

### M6: §8.1 RDF + §8.2 SPARQL use `acp:` predicates absent from canonical ontology TTLs

**Location (acp-framework)**: §8.1 RDF Relationships (L420–432) + §8.2 SPARQL (L441–445):
- `acp:hasAgent`, `acp:hasPrincipal`, `acp:underGrant`, `acp:derivedFrom`, `acp:hasDecision`, `acp:hasExecutionRecord`, `acp:executedBy`, `acp:witnessedBy`, `acp:recordedIn`, `acp:executedIntent`, `acp:status`, `acp:atpConsumed`

**Severity**: MEDIUM (parallels C17 M1 and C16 M8 — recurring ontology-absence pattern).

**Re-verification**:

```
$ grep -rn "acp:hasAgent\|acp:hasPrincipal\|acp:underGrant\|acp:derivedFrom\|acp:hasDecision\|acp:hasExecutionRecord\|acp:executedBy\|acp:witnessedBy\|acp:recordedIn\|acp:atpConsumed" web4-standard/
web4-standard/ACP_INTEGRATION_SUMMARY.md:[8 lines — informational summary]
web4-standard/core-spec/acp-framework.md:[12 lines — this audit's target]
web4-standard/archive/reference-implementations/acp_framework.py:[2 lines — archived implementation]

$ grep -n "acp:" web4-standard/ontology/web4-core-ontology.ttl
(no output)

$ grep -n "acp:" web4-standard/ontology/t3v3-ontology.ttl
(no output)
```

ZERO occurrences of any `acp:` predicate in any canonical ontology TTL file. The `acp:` prefix is declared at L417 (`@prefix acp: <https://web4.io/ontology/acp#> .`) but the namespace IRI has no corresponding TTL file in `web4-standard/ontology/`.

**Impact**: The §8.2 SPARQL example query would return zero results from any compliant graph because no `acp:*` predicates have a canonical definition. RDF triples written per §8.1 would not validate against any shipped ontology.

**Remediation direction**: DESIGN-Q. Requires creating `web4-standard/ontology/acp-ontology.ttl` (or extending `web4-core-ontology.ttl` with an `acp:` section) to define the 12 predicates with proper domain/range axioms. Out-of-scope for this audit's autonomous remediation; bundles with C17 M1 (dictionary ontology gap) + C16 M8 (SAL ontology gap) as the "subordinate ontology completion" cluster. **DEFER** to ontology-maintainer + operator queue.

---

### M7: §5.2 `witness_requirement` structured object vs §2.1 Guards integer `witnessLevel: 2` — two unbridged witness data models

**Location (acp-framework)**:
- §2.1 Guards (L82): `"witnessLevel": 2` (integer)
- §5.2 Witness Requirements (L316–328):
  ```json
  {
    "witness_requirement": {
      "level": 2,
      "types": ["time", "audit"],
      "quorum": {"model": "byzantine", "threshold": 0.67},
      "timeout": 300,
      "fallback": "abort"
    }
  }
  ```

**Severity**: MEDIUM (intra-spec data-model duplication; SDK has only one of the two; no bridge specified).

**Re-verification — SDK side**:

SDK `Guards.witness_level` (acp.py:256): `witness_level: int = 0` — integer only, no structured witness_requirement object representation. SDK `Guards.validate_witnesses(witness_count: int) -> bool` does `witness_count >= self.witness_level` — a simple count comparison, NOT a quorum-with-types-and-byzantine-threshold model.

**Impact**: An implementer faces two incompatible witness specifications in the same document:
- §2.1 Guards says witness-gating is an integer level (matched by SDK)
- §5.2 says witness-gating is a structured object with types, byzantine quorum model, and per-type timeouts

Neither references the other. SDK only implements §2.1 semantics; §5.2 semantics are unimplemented and have no canonical schema.

**Remediation direction**: DESIGN-Q. Options:
- (A) Delete §5.2 (or fold into a §5.3 "future direction" note) and keep integer model
- (B) Promote §5.2 to canonical, deprecate §2.1 integer, extend SDK Guards
- (C) Define a `witnessLevel` vs `witnessRequirement` discriminated-union (integer = simple, object = advanced)

Each option is non-trivial. **DEFER** to operator decision.

---

## LOW Findings

### L1: §4.2 `proofOfAgency` (camelCase) keyed inside `web4_context` envelope vs `mcp-protocol.md` `proof_of_agency` (snake_case) in the same envelope

**Location (acp-framework)**: §4.2 Proof of Agency, lines 260–282 (`proofOfAgency` camelCase keys inside `web4_context` envelope).
**Location (mcp-protocol)**: `mcp-protocol.md:137` (`proof_of_agency` snake_case key) + L164 (`web4_context.proof_of_agency` access).

**Severity**: LOW (parser-tolerable in many JSON parsers but a cross-spec stumbling block; the divergence is INSIDE the same conceptual envelope — `web4_context` — that both specs claim to define contents for).

**Re-verification**:

mcp-protocol.md §4.1 example (snake_case throughout):
```
$ sed -n '127,145p' web4-standard/core-spec/mcp-protocol.md
"web4_context": {
  "sender_lct": "lct:web4:client:...",
  "sender_role": "web4:DataAnalyst",
  "trust_context": {"t3_in_role": {"talent": 0.85, "training": 0.90}, "atp_stake": 50},
  "mrh_depth": 2,
  "society": "lct:web4:society:...",
  "law_hash": "sha256:...",
  "proof_of_agency": {
    "grant_id": "agy:...",
    "scope": "data:analysis"
  }
}
```

acp-framework.md §4.2 example (camelCase inside the snake_case envelope):
```
$ sed -n '267,282p' web4-standard/core-spec/acp-framework.md
"web4_context": {
  "proofOfAgency": {
    "grantId": "agy:grant:...",
    "planId": "acp:plan:...",
    "intentId": "acp:intent:...",
    "ledgerProof": {"grantBlock": 12345, "grantHash": "0x...", "inclusionProof": "..."},
    "nonce": "unique-nonce",
    "audience": ["mcp:invoice/*"],
    "expiresAt": "2025-12-31T23:59:59Z"
  }
}
```

Same envelope (`web4_context`), opposite casing for the agency-proof key + nested fields. mcp-protocol uses `proof_of_agency.grant_id`; acp-framework uses `proofOfAgency.grantId`.

**Impact**: An MCP server constructed from mcp-protocol.md would look up `web4_context["proof_of_agency"]` and miss the field if the ACP client sends `proofOfAgency`. The two specs disagree on the same protocol envelope.

**Remediation direction**: NOT proposed here (cross-spec normalization is its own scope, per BC#6). Same DESIGN-Q cluster as M3. **DEFER**.

---

## Implementation Plan Summary (for a future remediation PR)

| Finding | Severity | Action | Autonomous-actionable? |
|---------|----------|--------|------------------------|
| H1 | HIGH | One-token fix L250: `InsufficientWitnesses` → `WitnessDeficit` | YES |
| H2 | HIGH | Map 3 undef exceptions at L299/L303/L307 → canonical classes (depends on M1 for `ResourceCapExceeded`) | YES (bundle with M1) |
| H3 | HIGH | Replace L84 `"auto-if<=10 else prompt"` → `"conditional"` + `autoThreshold: 10` | YES |
| M1 | MEDIUM | Add 2 class defs to §10.1: `InvalidTransition` + `ResourceCapExceeded` | YES (bundle with H2) |
| M2 | MEDIUM | Add W4_ERR_ACP_* category to errors.md taxonomy | NO — DESIGN-Q (taxonomy cluster, bundle with C16-H1/C17-M4) |
| M3 | MEDIUM | Cross-corpus snake/camel normalization (4+ sites) | NO — DESIGN-Q (cross-corpus, per BC#6) |
| M4 | MEDIUM | Replace L162 `v3.value` → `v3.valuation` or `v3.validity` | YES (one-token, operator may prefer `validity` semantically) |
| M5 | MEDIUM | §4.1 L249 algorithmic correction (witness check is approval-gate concern, not agency concern) | PARTIAL — algorithmic correction YES; Intent-shape extension is DESIGN-Q |
| M6 | MEDIUM | Create `acp-ontology.ttl` (12 predicates) | NO — DESIGN-Q (ontology cluster, bundle with C16-M8/C17-M1) |
| M7 | MEDIUM | Resolve §2.1 integer vs §5.2 structured witness model | NO — DESIGN-Q |
| L1 | LOW | Cross-spec proofOfAgency vs proof_of_agency normalization | NO — DESIGN-Q (same cluster as M3) |

**Wire-actionable autonomous remediation cluster** (estimated single-PR cut, parallel to C17 PR #242): H1 + H2 + H3 + M1 + M4 + M5-partial = 6 findings, ~25-line diff in `acp-framework.md` only.

**DESIGN-Q deferred cluster**: M2 + M3 + M6 + M7 + L1 + M5-shape-extension = 5 (with M5 splitting between actionable + deferred) — bundles into the existing "canonical errors taxonomy" + "cross-corpus casing" + "subordinate ontology" + "witness data model" operator queues.

---

*Audit produced under v2 Autonomous Session Protocol; 9 binding conditions from policy review all satisfied. Every cited line was re-grepped during Step 6; SDK and corpus claims cite specific files with line numbers; ≥1 demotion (actually 2: L1-LCT-placeholder and L2-signatures-ellipsis) applied per BC#2 demotion discipline.*
