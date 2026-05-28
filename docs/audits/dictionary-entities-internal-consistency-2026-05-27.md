# C17: dictionary-entities.md Internal Consistency Audit

**Date**: 2026-05-27
**Auditor**: Autonomous session (legion-web4-20260527-193809)
**Document**: `web4-standard/core-spec/dictionary-entities.md` (589 lines)

**Authority hierarchy used for this audit** (each cross-reference re-read at the cited line):

| Claim class | Authority | File(s) |
|-------------|-----------|---------|
| Role taxonomy (`roleLCT` vs `roleType`, canonical roles) | spec + SDK | `web4-standard/core-spec/r6-framework.md` (C14 H1 anchor); `web4-standard/core-spec/society-roles.md`; `web4-standard/implementation/sdk/web4/role.py` (`SocietyRole` enum) |
| LCT id construction | spec | `web4-standard/core-spec/LCT-linked-context-token.md:256` (canonical hash-based construction); corpus-wide LCT example survey |
| R6/R7 action structure (`role.roleLCT`, request shape) | spec | `web4-standard/core-spec/r6-framework.md` (C12 anchor); `web4-standard/core-spec/r7-framework.md` (C14 anchor) |
| Witness field shape (`witness_attestation` vs `witnesses` array) | spec + SDK schemas | `web4-standard/core-spec/mcp-protocol.md:183`; `web4-standard/implementation/sdk/web4/schema_registry.json:2949` (`witness_attestation` $def); `web4-standard/schemas/r7-action-jsonld.schema.json` |
| Error code taxonomy (`W4_ERR_*`) | spec + SDK | `web4-standard/core-spec/errors.md`; `web4-standard/implementation/sdk/web4/errors.py` |
| RDF vocabulary | ontology TTL | `web4-standard/ontology/web4-core-ontology.ttl`; `web4-standard/ontology/t3v3-ontology.ttl` |
| Stake field naming (`stake_required` vs `atp_stake`) | spec | `web4-standard/core-spec/entity-types.md:561` (LCT-config); `web4-standard/core-spec/mcp-protocol.md:82,132` + `presence-protocol.md:179` + `r7-framework.md:651` (per-request) |
| Dictionary SDK implementation | SDK | `web4-standard/implementation/sdk/web4/` — **no Dictionary dataclass exists** (see INFO1) |

Where divergence is **spec-vs-spec** rather than spec-vs-SDK, the finding labels it as such and does not silently promote one spec over the other.

---

## Summary

| Severity | Count | Theme |
|----------|-------|-------|
| HIGH | 2 | §6.1 SPARQL typo `web4:sourceDomai` breaks discovery query; §7.1 R6 example uses stale `roleType` field + non-canonical role `web4:Translator` |
| MEDIUM | 6 | §6.1 all `web4:*` predicates absent from canonical ontology; §4.3 `witness_attestation` key holds wrong shape (array vs object per canonical schema); §2.2 vs §4.1 same key `trust_requirements` with incompatible inner schemas; §4.2 pseudocode exceptions not in W4_ERR_* taxonomy; §2.2 L48 LCT id has redundant `:v2` suffix + non-canonical format; confidence/fidelity thresholds inconsistent across §2.2/§4.1/§4.2 |
| LOW | 2 | §4.2/§5.1 pseudocode `threshold` undefined; §10.1 vs §4.3 translation-chain schema represented two different ways |

**Cross-audit calibration note**: This audit follows C12 (r6, #229/#231), C13 (t3-v3, #230/#232), C14 (r7, #233/#234), C15 (reputation-computation, #236/#237), C16 (SAL, #239/#240). Severity calibration:
- **HIGH** = wire-breaking divergence (typo in SPARQL predicate = broken query; stale `roleType` matches the C14 H1 anchor severity) or normative example pointing at non-existent infrastructure.
- **MEDIUM** = same-key-different-schema (parser/codegen confusion), missing W4_ERR_* mapping, non-canonical id construction, threshold inconsistency.
- **LOW** = pseudocode hygiene, schema-representation duplication that doesn't break the wire.

**Demoted candidate findings** (overcall-discipline value-add — three candidates explicitly *not* recorded as findings):

1. **§2.2 L73 `stake_required: 100` vs §4.1 L192 `atp_stake: 50` (stake field naming)** — initial review flagged as a naming divergence. **Demoted** after cross-doc verification: `entity-types.md:561` ALSO uses `stake_required` at LCT-level (config), while `atp_stake` is used at request-level in `mcp-protocol.md:82,132`, `presence-protocol.md:179`, and `r7-framework.md:651`. These are TWO distinct fields at TWO distinct scopes (LCT-default-config vs per-request-override). Both names are canonical at their respective levels. Not a defect — corroborated convention.

2. **`entity-types.md` §10.2 vs `dictionary-entities.md` §2.2 LCT structure** — initial review considered listing as a cross-doc divergence. **Demoted**: `entity-types.md` §10.2 is a proper subset of `dictionary-entities.md` §2.2 (`version`, `relationships`, `drift_detection`, `mrh` are present only in the longer §2.2 form, but no key/value contradicts). Both consistent; the shorter form is a summary, not a competing source.

3. **§2.2 L62 `compression_profile.average_ratio: 12.5`** — initial flag was "out of range" relative to typical [0,1] T3/V3 scores. **Demoted**: the field is labeled "ratio" (compression ratio), not a score; values >1 are semantically valid for ratios. No defect.

Every cross-reference below was re-read against the live file at the cited line.

---

## HIGH Findings

### H1: §6.1 SPARQL discovery query has a one-character typo in a predicate that breaks the query

**Location (dictionary-entities)**: §6.1 Discovery via MRH, lines 363–380. Specifically:
- L366: `web4:sourceDomai "medical" ;` — typo, should be `web4:sourceDomain`

**Severity**: HIGH

**Re-verification**:

```
$ grep -n "sourceDomai\b" web4-standard/core-spec/dictionary-entities.md
366:              web4:sourceDomai "medical" ;
```

The very next predicate at L367 uses the correctly-spelled `web4:targetDomain`, making this an unambiguous typo (not a deliberate alternate spelling).

**Impact**: The §6.1 example is a normative SPARQL query showing implementers how to discover Dictionary entities via MRH. As written, the query will match zero results from any compliant graph because no Dictionary entity will have a `web4:sourceDomai` predicate — it will all be on `web4:sourceDomain` (or whatever the canonical predicate IRI turns out to be; see M1 — neither variant is actually defined in the ontology today). The query is broken on its face.

**Remediation direction**: One-character fix — `sourceDomai` → `sourceDomain` at L366. (Note: this is downstream of M1; the predicate itself does not exist in any canonical ontology file, so a complete fix also requires the M1 remediation.)

---

### H2: §7.1 R6 example uses stale `roleType` field name (C14 H1 established canonical `roleLCT`) and a non-canonical role value `web4:Translator`

**Location (dictionary-entities)**: §7.1 Translation as R6 Action, lines 407–441. Specifically:
- L418: `"roleType": "web4:Translator"` — both the field name `roleType` AND the role value `web4:Translator` are non-canonical.

**Severity**: HIGH (matches C14 H1 severity calibration — the canonical R6/R7 action shape is `role.roleLCT`, and an R6 example written with the wrong field name produces a non-conformant action that downstream code would silently reject or misroute).

**Re-verification**:

**Field name (`roleType` vs `roleLCT`)**:

```
$ grep -n "roleType\|roleLCT" web4-standard/core-spec/r6-framework.md
60:    "roleLCT": "lct:web4:role:analyst_financial_q4:abc123",
324:        role_lct=r6_action.role.roleLCT,
380:  "role": {"roleLCT": "lct:web4:role:reader:..."},
393:  "role": {"roleLCT": "lct:web4:role:investigator:..."},
413:  "role": {"roleLCT": "lct:web4:role:data_scientist:..."},
434:  "role": {"roleLCT": "lct:web4:role:authority:..."},
454:  "role": {"roleLCT": "lct:web4:role:agent:...", "actingFor": "lct:web4:client:..."},
```

```
$ grep -n "roleType\|roleLCT" web4-standard/core-spec/r7-framework.md
70:    "roleLCT": "lct:web4:role:analyst_financial_q4:abc123",
410:    role_lct = r7_action.role.roleLCT
598:  "role": {"roleLCT": "lct:web4:role:reader:..."},
[...all roleLCT, no roleType]
```

The canonical R6/R7 field is **`roleLCT`** (an LCT identifier, not a role-type label). Per r6-framework.md L76: *"The `roleLCT` encodes the domain-specific context (e.g., `analyst_financial_q4`) within the LCT identifier itself."* — that is, the role is referenced by LCT, not by a type-name string.

**Role value (`web4:Translator`)**:

```
$ grep -n "Translator\|translator" web4-standard/core-spec/society-roles.md \
                                    web4-standard/implementation/sdk/web4/role.py
(no matches)
```

```
$ grep -n "^class SocietyRole\|SocietyRole\." web4-standard/implementation/sdk/web4/role.py | head
43:class SocietyRole(str, Enum):
107:        SocietyRole.SOVEREIGN,
108:        SocietyRole.LAW_ORACLE,
109:        SocietyRole.POLICY_ENTITY,
110:        SocietyRole.TREASURER,
111:        SocietyRole.ADMINISTRATOR,
112:        SocietyRole.ARCHIVIST,
113:        SocietyRole.CITIZEN,
```

Canonical role taxonomy is the 7-base set above plus 2 context roles (`ORACLE`, `AGENT` — per society-roles.md). **`Translator` is not a canonical role** in either society-roles.md or the SDK `SocietyRole` enum.

**Impact**: An implementer building an R6 action for a translation will produce a JSON object that does not deserialize against the canonical R6 schema (the field is `roleType` not `roleLCT`, and the role value is a non-existent role IRI). Wire-breaking. This precisely matches the C14 H1 anchor finding in r7-framework.md (which was remediated to `roleLCT` in PR #234).

**Remediation direction** (deferred to next-session PR):
- Rename L418 field `roleType` → `roleLCT`
- Change the value from a role-name (`web4:Translator`) to an LCT identifier (e.g., `lct:web4:role:dictionary_translator:...`) — note that this requires a design decision on whether a `dictionary_translator` role is added to society-roles.md, or whether the example uses an existing canonical role. `entity-types.md:80` classifies Dictionary as a distinct R6-capable Responsive entity (peer to Oracle and Service); `entity-types.md:259` lists "Dictionary role" + "Policy-Entity (when policy involves semantic translation)" as the role-compatibility for Dictionary entities — neither is currently in the `SocietyRole` enum or society-roles.md, so promoting "Dictionary" / "Translator" to the canonical role taxonomy is a real design choice. This is a DESIGN-Q parallel to C16 M1 (role taxonomy reconciliation).
- See INFO3 below for a corpus-sweep observation that an identical `roleType` stale site exists at `mcp-protocol.md:306`.

---

## MEDIUM Findings

### M1: §6.1 SPARQL predicates `web4:Dictionary`, `web4:sourceDomain`, `web4:targetDomain`, `web4:trustScore`, `web4:coverage`, `web4:lastUpdated` are ALL absent from the canonical ontology

**Location (dictionary-entities)**: §6.1 SPARQL example, lines 363–380.

**Severity**: MEDIUM

**Re-verification**:

```
$ grep -rn "web4:Dictionary\b\|sourceDomain\|targetDomain\|web4:trustScore\|web4:coverage\|web4:lastUpdated" \
    web4-standard/ontology/
(no matches)

$ ls web4-standard/ontology/
r7-action.jsonld  t3v3.jsonld  t3v3-ontology.ttl  web4-core-ontology.ttl
```

None of the six `web4:*` predicates used in the §6.1 query are defined in any TTL file under `web4-standard/ontology/`. There is no `dictionary-ontology.ttl` or equivalent.

**Impact**: Even after fixing H1 (the `sourceDomai` typo), the §6.1 SPARQL query will return zero results against any compliant Web4 graph because the predicates it filters on simply do not exist in the canonical ontology. The example is aspirational, not operational.

This is structurally similar to C16 M8 (SAL §3.3 RDF turtle edges not formalized in canonical ontology), which was deferred as DESIGN-Q requiring operator + ontology-maintainer coordination.

**Remediation direction** (deferred to ontology-maintainer + operator coordination):
- Add a `dictionary-ontology.ttl` to `web4-standard/ontology/` defining `web4:Dictionary` class plus the predicates `sourceDomain`, `targetDomain`, `trustScore`, `coverage`, `lastUpdated` with appropriate domain/range; OR
- Add these to `web4-core-ontology.ttl` directly; OR
- Rewrite §6.1 to use only predicates that exist in the canonical ontology.

---

### M2: §4.3 `witness_attestation` field holds an array of LCT identifiers, but the canonical `witness_attestation` schema (mcp-protocol.md + schema_registry.json) defines it as an object

**Location**:
- dictionary-entities.md §4.3 L274: `"witness_attestation": ["lct:web4:witness:domain-expert"]` (array of LCT strings)
- mcp-protocol.md §"MCP servers as witnesses" L183: `"witness_attestation": { "witnessed_interaction": {...}, "witness": "...", "signature": "..." }` (single object)
- `web4-standard/implementation/sdk/web4/schema_registry.json:2949`: `"witness_attestation": {…}` — defines it as an object schema with required nested fields (`witnessed_interaction`, `witness`, `signature`)
- `web4-standard/schemas/r7-action-jsonld.schema.json:188,254`: `"items": { "$ref": "#/$defs/witness_attestation" }` — when used as an array, the schema requires *each item* to conform to the `witness_attestation` $def (i.e. an attestation object, not a bare LCT id)

**Severity**: MEDIUM

**Re-verification**:

```
$ grep -rn "witness_attestation\b" web4-standard/
(returns mcp-protocol.md:183 + r7-action-jsonld.schema.json:188,254 + schema_registry.json:2737,2833,2949,3025
 + protocols/web4-witness.md:239 [function name] + dictionary-entities.md:274 + test-vectors/mcp/mcp-protocol.json:207)
```

```
$ grep -n "\"witnesses\":" web4-standard/core-spec/*.md
acp-framework.md:135:   "witnesses": ["lct:web4:witness:A", "lct:web4:witness:B"],
atp-adp-cycle.md:52:    "witnesses": ["lct:web4:witness:auditor1", "lct:web4:witness:auditor2"]
entity-types.md:151:    "witnesses": ["lct:web4:witness1", "lct:web4:witness2"],
r6-framework.md:138:    "witnesses": [...]
r7-framework.md:148:    "witnesses": [...]
```

The corpus convention is:
- **`witnesses`** (plural) = array of LCT identifier strings (bare witness references). Used by acp/atp-adp/entity-types/r6/r7.
- **`witness_attestation`** (singular) = an attestation object containing the witnessed interaction, witness LCT, and signature. Used by mcp + r7-action-jsonld + schema_registry.

The dictionary-entities.md L274 use of `witness_attestation` as an array of bare LCT strings does **not** conform to either convention — it uses the singular `_attestation` key name (which canonically holds an object) to hold what should be a `witnesses` array.

**Impact**: An implementer or codegen tool that reads §4.3 and applies the canonical `witness_attestation` schema will fail validation. The field is shape-mismatched against the only normative schema for that key name in the repo.

**Remediation direction**:
- Rename §4.3 L274 `witness_attestation` → `witnesses` (matching the canonical array-of-LCT-refs convention); OR
- Restructure to hold an array of attestation objects (each conforming to the `witness_attestation` $def), e.g. `"witness_attestations": [{"witnessed_interaction": ..., "witness": ..., "signature": ...}]` — note the plural and the object-array shape.

---

### M3: §2.2 and §4.1 both use the key `trust_requirements` with incompatible inner schemas

**Location**:
- §2.2 L67–74: `"trust_requirements": { "minimum_t3": { "talent": ..., "training": ..., "temperament": ... }, "stake_required": ... }` — LCT-level configuration
- §4.1 L189–193: `"trust_requirements": { "minimum_fidelity": ..., "require_witness": ..., "atp_stake": ... }` — per-request override

**Severity**: MEDIUM

**Re-verification**:

```
$ sed -n '67,74p' web4-standard/core-spec/dictionary-entities.md
  "trust_requirements": {
    "minimum_t3": {
      "talent": 0.8,      // Domain expertise
      "training": 0.9,     // Translation accuracy
      "temperament": 0.85  // Consistency
    },
    "stake_required": 100  // ATP stake for high-risk translations
  },
```

```
$ sed -n '189,193p' web4-standard/core-spec/dictionary-entities.md
  "trust_requirements": {
    "minimum_fidelity": 0.95,
    "require_witness": true,
    "atp_stake": 50
  }
```

The two objects use the same outer key `trust_requirements` but share zero inner fields. §2.2 has `{minimum_t3, stake_required}`; §4.1 has `{minimum_fidelity, require_witness, atp_stake}`. The LCT-config-vs-request-override distinction is legitimate (see Demoted #1 on the `stake_required`/`atp_stake` field-pair), but the OUTER key being identical creates parser/codegen confusion: a tool that defines a `trust_requirements` schema must support two non-overlapping shapes under one name.

**Impact**: Generated JSON schemas, type-checked deserializers, or any code that keys on `trust_requirements` will mis-parse one of the two examples. An implementer reading §2.2 first will not anticipate the §4.1 shape; vice versa.

**Remediation direction**:
- Disambiguate by giving the two shapes distinct outer keys, e.g.
  - §2.2 LCT-config → `"dictionary_trust_config": { "minimum_t3": ..., "stake_required": ... }`
  - §4.1 request-override → `"trust_requirements": { "minimum_fidelity": ..., "require_witness": ..., "atp_stake": ... }`
  (keep `trust_requirements` as the per-request key, since that matches typical R6 request-shape conventions); OR
- Merge into a single canonical object containing all fields, with the LCT-config-vs-request distinction explained in prose.

---

### M4: §4.2 pseudocode raises `IncompetentDictionary()` and `InsufficientDictionaryTrust()` exceptions without mapping to the canonical `W4_ERR_*` taxonomy

**Location (dictionary-entities)**: §4.2 Translation Flow, lines 200–208. Specifically:
- L203: `raise IncompetentDictionary()`
- L207: `raise InsufficientDictionaryTrust()`

**Severity**: MEDIUM

**Re-verification**:

```
$ grep -rn "IncompetentDictionary\|InsufficientDictionaryTrust" web4-standard/
web4-standard/core-spec/dictionary-entities.md:203:        raise IncompetentDictionary()
web4-standard/core-spec/dictionary-entities.md:207:        raise InsufficientDictionaryTrust()
```

```
$ grep -n "W4_ERR" web4-standard/core-spec/errors.md | head -10
14:  "code": "W4_ERR_BINDING_EXISTS",
37:| W4_ERR_BINDING_EXISTS | ... |
[...standard taxonomy]
```

These exception names appear nowhere else in the corpus. There is no `W4_ERR_DICTIONARY_*` category in `errors.md` or `errors.py`.

**Impact**: The §4.2 pseudocode does not show implementers how to surface failures in a Web4-conformant way. RFC 9457 Problem Details responses require a `W4_ERR_*` code from the canonical taxonomy. Raising a bare Python-style exception in pseudocode without mapping (e.g. "raises `IncompetentDictionary` which serializes as `W4_ERR_AUTHZ_DENIED`") means an implementer copying this code will produce non-conformant errors.

This is structurally similar to C16 H1 (SAL §9 referenced 4 non-existent W4_ERR_* codes) but at LOW-MEDIUM severity here because the dictionary-entities exceptions are PSEUDOCODE-level (not normative error-table entries promising specific codes).

**Remediation direction** (DESIGN-Q + spec edit):
- Either map each pseudocode exception to an existing taxonomy code (e.g., `IncompetentDictionary` → `W4_ERR_AUTHZ_SCOPE` or a new `W4_ERR_DICT_DOMAIN_MISMATCH`; `InsufficientDictionaryTrust` → `W4_ERR_AUTHZ_DENIED` or new `W4_ERR_DICT_TRUST_DEFICIT`); OR
- Add a `W4_ERR_DICT_*` category to `errors.md` and `errors.py` with these codes; OR
- Rewrite the pseudocode to show conformant Problem Details responses inline.

---

### M5: §2.2 L48 LCT id example `lct:web4:dictionary:medical-legal:v2` has a redundant `:v2` version suffix and does not match canonical LCT id-construction or example patterns

**Location**:
- §2.2 L48: `"lct_id": "lct:web4:dictionary:medical-legal:v2",`
- §2.2 L54 (separately): `"version": "2.3.1",`

**Severity**: MEDIUM

**Re-verification**:

Canonical LCT id construction (LCT-linked-context-token.md):

```
$ sed -n '244,258p' web4-standard/core-spec/LCT-linked-context-token.md | grep -E "lct_id|multibase"
        "public_key": multibase_encode(cose_key(private_key.public_key)),
    lct_id = "lct:web4:" + multibase32_encode(sha256(binding_proof))
```

LCT id examples elsewhere in the corpus:

```
$ grep -E "lct:web4:[a-z]+:" web4-standard/core-spec/LCT-linked-context-token.md | head -10
"lct_id": "lct:web4:mb32:..."          (L62, canonical hash-based)
"lct:web4:role:citizen:..."             (L75, human-readable, NO version suffix)
"lct:web4:witness:1..."                 (L78, human-readable, NO version suffix)
"lct:web4:role:citizen:..."             (L97/287, same)
"lct:web4:hardware:..."                 (L89, same)
"lct:web4:oracle:trust:..."             (L141, same)
```

Two conventions are observable across the LCT spec's own examples:
1. **Canonical constructed form**: `lct:web4:mb32:<multibase32(sha256(binding_proof))>` (L62, L256)
2. **Human-readable example form** used throughout illustrations: `lct:web4:<type>:<descriptor>:...` (where `...` is a stand-in for the multibase tail)

In neither convention does an example carry an additional **`:v<N>` version suffix**. The dictionary-entities §2.2 L48 example is the only LCT id in the entire core-spec corpus that does so.

**Impact**:
1. The `:v2` suffix duplicates information already carried in the dedicated `version` field at §2.2 L54 (`"version": "2.3.1"` — already richer than `v2`). An implementer reading both could not tell whether the LCT id's version segment is normative or which value takes precedence.
2. The id format is divergent from every other LCT example in the corpus; any pattern-matching consumer of LCT ids will reject or misparse this one.

**Remediation direction**:
- Drop the `:v2` suffix at L48: `"lct_id": "lct:web4:dictionary:medical-legal"` — matching the corpus convention. The `version: "2.3.1"` field at L54 is sufficient for version expression.
- (Optional, stronger alignment) Use the canonical hash-based form: `"lct_id": "lct:web4:mb32:<sha256-of-binding-proof>"` per LCT spec L256.

---

### M6: Confidence/fidelity thresholds (0.95 / 0.95 / 0.9) inconsistent across §2.2, §4.1, and §4.2

**Location**:
- §2.2 L68–71: `minimum_t3.training: 0.9` (LCT-config; training-dimension minimum)
- §4.1 L190: `minimum_fidelity: 0.95` (per-request fidelity minimum)
- §4.2 L246: `witness_required: confidence < 0.95` (per-translation witnessing gate)

**Severity**: MEDIUM

**Re-verification**:

```
$ sed -n '68,71p' web4-standard/core-spec/dictionary-entities.md
      "talent": 0.8,      // Domain expertise
      "training": 0.9,     // Translation accuracy
      "temperament": 0.85  // Consistency
```

```
$ sed -n '190p' web4-standard/core-spec/dictionary-entities.md
    "minimum_fidelity": 0.95,
```

```
$ sed -n '246p' web4-standard/core-spec/dictionary-entities.md
        witness_required=confidence < 0.95
```

Three different fields use three different numeric thresholds with overlapping semantics:
- §2.2 `minimum_t3.training: 0.9` — minimum trust competence for translation accuracy
- §4.1 `minimum_fidelity: 0.95` — minimum acceptable translation fidelity
- §4.2 `witness_required: confidence < 0.95` — witnessing gate

It is not clear from the spec whether:
- The §4.2 gate (0.95) should match the §4.1 minimum (0.95) intentionally (consistent),
- The §2.2 trust threshold (0.9) is meant to be lower than the per-translation fidelity (0.95) by design (tier-graded), or
- These are accidental near-coincidences and the spec leaves the relationship undefined.

**Impact**: An implementer cannot determine the intended relationship between trust-competence thresholds (T3), fidelity thresholds (per-translation), and witnessing thresholds. The 0.95 ≡ 0.95 coincidence between §4.1 and §4.2 looks deliberate but is never declared. The 0.9 ≠ 0.95 gap between trust and fidelity needs explicit justification or alignment.

**Remediation direction**:
- Add a §"Threshold Semantics" subsection that explicitly defines the relationship between trust thresholds (T3 dimension minimums), fidelity thresholds (per-translation), and witnessing gates; OR
- Use named constants (e.g., `DICT_DEFAULT_FIDELITY = 0.95`, `DICT_WITNESS_GATE = DICT_DEFAULT_FIDELITY`) so the equality is intentional and trace-able; OR
- Reconcile the 0.9 vs 0.95 gap (e.g., harmonize training-T3 minimum to 0.95 to match the fidelity floor).

---

## LOW Findings

### L1: §4.2 and §5.1 pseudocode reference undefined `threshold` variables

**Location**:
- §4.2 L220: `if target_concepts.ambiguity > threshold:` — `threshold` undefined
- §5.1 L317: `if dictionary.changes > threshold:` — `threshold` undefined

**Severity**: LOW

**Re-verification**:

```
$ grep -n "threshold" web4-standard/core-spec/dictionary-entities.md
65:    "lossy_threshold": 0.02,
220:    if target_concepts.ambiguity > threshold:
317:    if dictionary.changes > threshold:
344:    "proposal_threshold": 10,  // Min reputation to propose
```

The bare `threshold` identifiers at L220 and L317 do not refer to either the named `lossy_threshold` (L65) or `proposal_threshold` (L344). They are unbound variables.

**Impact**: Pseudocode is meant to communicate algorithmic intent. A reader cannot determine the numeric value or its derivation for the ambiguity-handling branch (L220) or the version-bump branch (L317). Implementers must invent thresholds, which will diverge across implementations.

**Remediation direction**:
- Replace bare `threshold` at L220 with a named constant or parameter, e.g. `dictionary.ambiguity_threshold` (sourced from a dictionary field) or `AMBIGUITY_GATE = 0.3`; same for L317 → `VERSION_BUMP_DELTA`.
- Or surface the threshold as a configurable field in §2.2 LCT structure (next to `lossy_threshold`).

---

### L2: §10.1 and §4.3 represent a translation-chain in two incompatible schemas

**Location**:
- §4.3 L253–276: JSON object `{ "translation_chain": [{ "step": 1, "from": "...", "to": "...", "dictionary": "...", "confidence": ..., "degradation": ... }, {"step": 2, ...}], "cumulative_degradation": ..., "witness_attestation": [...] }`
- §10.1 L497–506: YAML object with keys `chain.source`, `chain.step1`, `chain.step2`, `chain.cumulative_confidence`, `chain.witnesses` — uses positional `stepN` keys with nested anonymous objects under each.

**Severity**: LOW

**Re-verification**:

```
$ sed -n '253,276p' web4-standard/core-spec/dictionary-entities.md
{
  "translation_chain": [
    {
      "step": 1,
      "from": "medical",
      ...
    },
    {
      "step": 2,
      ...
    }
  ],
  "cumulative_degradation": 0.126,
  ...
  "witness_attestation": ["lct:web4:witness:domain-expert"]
}
```

```
$ sed -n '497,506p' web4-standard/core-spec/dictionary-entities.md
chain:
  - source: "Patient diagnosed with moderate TBI following MVA"
  - step1: medical → insurance
    output: "Traumatic brain injury from vehicle accident requiring coverage"
  - step2: insurance → legal
    output: "Plaintiff sustained head trauma with cognitive impairment in collision"
  cumulative_confidence: 0.88
  witnesses: [medical_expert, insurance_adjuster, legal_clerk]
```

Two distinct schemas for the same conceptual structure:
- §4.3: array under `translation_chain`, each element has a `step: N` field, top-level `cumulative_degradation` + `witness_attestation` (array).
- §10.1: YAML keys `step1`/`step2` as positional, top-level `cumulative_confidence` (note: `confidence` not `degradation`) + `witnesses` (note: plural, consistent with corpus).

**Impact**: A consumer trying to handle "translation chain" outputs must support both shapes. Per-step fields differ (`from`/`to`/`dictionary`/`confidence`/`degradation` in §4.3 vs `step1: "medical → insurance"` + `output` in §10.1). Aggregate is `cumulative_degradation` vs `cumulative_confidence`. The witnesses field naming also differs (per M2 framing).

**Remediation direction**:
- Pick §4.3's array-of-step-objects as canonical (matches typical JSON/JSON-LD shapes); rewrite §10.1 to use the same shape (the §10 use-cases are illustrative and need not be normative, but should not introduce a competing schema).

---

## Informational (not findings)

**INFO1**: SDK (`web4-standard/implementation/sdk/web4/`) has NO Dictionary dataclass.

```
$ grep -l -i "class.*Dictionary\b" web4-standard/implementation/sdk/web4/*.py
(no matches — only generic Python "dictionary" docstring mentions)
```

All §9.1 MUST requirements (every Dictionary MUST have a valid LCT; MUST track confidence and degradation; MUST be witnessable; evolution MUST be versioned; critical translations MUST require ATP stake) are spec-only — no SDK enforcement exists. This is structurally similar to C16 M3 (`r6Bindings` field absent from SDK `LawDataset`), C16 M6 (`cool_down_period` absent), and C16 L1 (`BirthCertificate` dataclass absent). Out of scope for this internal-consistency audit; flagged for future SDK-track triage.

**INFO2**: §1.2 (Trust-Compression Duality) and §1.1 (the opening principle "All meaningful communication is compression plus trust...") are framing/motivational content, not normative statements. No defect, noted to forestall future audit attempts to score them.

**INFO3 (corpus sweep)**: An identical stale `roleType` site exists at `mcp-protocol.md:306` — `"roleType": "web4:Developer"`. This is outside the C17 scope (dictionary-entities only) but warrants a future MCP-spec audit; the H2 remediation pattern (rename to `roleLCT` + use a canonical role IRI) would apply directly. Pattern matches the C-series corpus-sweep value-add (exit #124 caught a similar adjacent site under SAL M2).

---

## Recommended Remediation Order (for the next-session PR)

Per the C-series cadence, the remediation PR (one file, `dictionary-entities.md`) should bundle the unambiguous spec-internal fixes and defer DESIGN-Q items (parallel to PR #240's structure for SAL):

**In-scope for a single remediation PR**:
- H1 (one-char typo `sourceDomai` → `sourceDomain`)
- H2 field rename (`roleType` → `roleLCT`); H2 role-value (DESIGN-Q — defer or pick `lct:web4:role:dictionary_oracle:...` with operator concurrence)
- M2 rename (`witness_attestation` → `witnesses`, array of LCT refs)
- M3 disambiguation (rename the §2.2 outer key to `dictionary_trust_config` or merge)
- M5 drop `:v2` suffix
- L1 named constants for thresholds
- L2 align §10.1 to §4.3 shape

**Deferred (DESIGN-Q / SDK / ontology)**:
- M1 (add `dictionary-ontology.ttl` — ontology-maintainer + operator coordination)
- M4 (add `W4_ERR_DICT_*` codes or map to existing — needs operator decision)
- M6 (threshold-semantics subsection — needs design clarification)
- H2 role-value reconciliation (DESIGN-Q on role taxonomy, parallel to C16 M1)
- INFO1 (SDK Dictionary dataclass — SDK-track work, separate authorization)

This split parallels the C16 partial-remediation pattern (PR #240): autonomous-actionable wire-level fixes ship in one PR; design questions surface as a documented deferral set.
