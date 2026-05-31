# C24: LCT-linked-context-token.md Internal Consistency RE-Audit

**Date**: 2026-05-31
**Auditor**: Autonomous session (legion-web4-20260531-060057)
**Document**: `web4-standard/core-spec/LCT-linked-context-token.md` (665 lines, HEAD `4eb691e8`)
**Prior audit**: C9 (`docs/audits/lct-internal-consistency-2026-05-22.md`, 2026-05-22, 8 findings, all remediated by PR #225 `2088a88b`)
**Spec mutations since C9**: 1 (PR #225 = the C9 remediation itself; no new content sections added since)

**Framing**: This is a **delta re-audit**, not a fresh first-pass audit. Unlike C23 (where 8 of 12 C16 findings remained unresolved at audit time), **all 8 C9 findings were properly resolved by PR #225** — §A "C9-carried" block is therefore **empty** by re-verification (re-confirmed line-by-line below). NET-NEW C24 IDs reflect: (a) issues that did not appear in C9 because C9 explicitly scoped out SDK-alignment, (b) cross-doc tensions only visible after C16-C23 audited sister specs, (c) fresh-eye review against the SDK and test vectors per BC#14 + BC#14's vector-corpus extension.

**Counts**:
- **C24 new IDs**: 12 (1 HIGH + 6 MEDIUM + 4 LOW + 1 INFO)
- **C9 carried (re-verified)**: 0 (PR #225 clean sweep)
- **Cross-track cite-only**: 1 (C23-H1)
- **DEMOTED**: 2 (considered but not issued)

Per BC-C23-5 (anti-padding): 12 NEW reflects honest delta. The empty §A C9-carry block means there is NO inflation from prior unresolved findings; 12 vs C20=13 / C21=16 / C22=11 / C18=11 / C19=13 lands inside the established envelope and reflects actual fresh issues surfaced by fresh-eye + SDK + vector cross-reference (which C9 explicitly excluded from scope).

---

## Authority hierarchy used for this audit

| Claim class | Authority | File(s) |
|-------------|-----------|---------|
| Spec internal coherence | spec | `web4-standard/core-spec/LCT-linked-context-token.md` (HEAD `4eb691e8`) |
| Canonical wire shape / dataclass | SDK | `web4-standard/implementation/sdk/web4/lct.py` (`@dataclass` defs, `to_jsonld()`, `from_jsonld()`) |
| Cross-language interop reality | test vectors | `web4-standard/test-vectors/lct/` (5 vector files: `interop-human-full.json`, `interop-minimal-interop.json`, `interop-revoked-agent.json`, `lct-jsonld-vectors.json`, `valid-birth-certificate.json`) |
| Cross-spec consistency | sister specs | `entity-types.md` (C8/C16 cluster), `lct-capability-levels.md` (C20), `web4-society-authority-law.md` (C16/C23), `SOCIETY_SPECIFICATION.md` (C22), `SOCIETY_METABOLIC_STATES.md` (C21) |
| Birth-certificate 3-way shape | (cross-track) | already captured as C23-H1 — cite-only per BC-C23-1 firewall |
| Subordinate ontology | (cluster carry) | `web4-standard/ontology/web4-core-ontology.ttl` L219 — already in C16-M8 cluster / C23-D2 — DEMOTED here to prevent BC-C23-3 cap violation |

Every cited line was re-read against the live file at HEAD `4eb691e8` before the finding text was written, per BC#2/BC#3.

---

## Summary

| Severity | Count | Theme |
|----------|-------|-------|
| HIGH (new) | 1 | H1: **LCT-ID format 4-way divergence** across §2.3 example, §3.3 binding-algorithm pseudocode, SDK `LCT.create()`, and test vectors — every leg produces a different canonical primitive shape for the foundational identifier of the spec |
| MEDIUM (new) | 6 | M1: §3.3 binding-algorithm return signature contradicts §2.3 (binding_proof inside vs outside binding object); M2: SDK `LCT.create()` does NOT add `birth_witnesses` to `mrh.witnessing` per §3.1 step 5 (behavioral-shape gap); M3: SDK `LCT.create()` does NOT create attestations from `birth_witnesses` per §4.2 item 3 (behavioral-shape gap); M4: spec doesn't enumerate `revocation.status` values — SDK has `SUSPENDED` (behaviorally exercised by vector `lct-jsonld-008`) with no spec definition; M5: §2.3 canonical-example `composite_score` numerical values don't reproduce from documented root tensor values under arithmetic mean OR SDK weighting; **M6: §7.3 ↔ §7.4 ↔ SDK rotation "superseded" status-vs-reason tri-document inconsistency** |
| LOW (new) | 4 | L1: §11.1 `validate_lct` references undefined helpers (`validate_t3_tensor` / `validate_v3_tensor` / `verify_binding_proof`); L2: §13 References omits `entity-types.md` (cited normatively §1.2) and `lct-capability-levels.md` (cited §10.3); L3: §6.2 V3 valuation `0.0+` (unbounded) vs composite_score `0.0-1.0` (capped) — composite-of-mixed-range semantics unspecified; **L4: §2.3 canonical-example raw JSON has NO `@context` / `@type` fields but SDK and 10/10 vectors include them** |
| INFO (new) | 1 | INFO1: Spec dates `October 1, 2025` (L4 + L663) are 8 months stale; per BC#13 INFO (no normative date-dependency); per BC#15 bumpable in this audit's own remediation |
| DEMOTED | 2 | D1: ontology L219 dangling `web4:Web4BirthCertificate` reference — already in C16-M8 cluster / C23-D2 (subordinate-ontology cluster is BC-C23-3 protected at 7 audits; D1 demotes to prevent count→8). D2: §1.2 prose "AI" (English acronym) vs §2.3 wire enum `ai` (JSON identifier) — typographic difference reflects different purposes (English vs wire format), NOT a defect |
| Cross-track CARRY | 1 | C23-H1 BirthCertificate 3-way shape drift — LCT spec is leg (b) of C23-H1's divergence; cited cross-track per BC-C23-1 firewall, NOT re-issued |

**Severity calibration anchored to C12-C23 precedent**:
- **HIGH** = wire-breaking divergence affecting a normative example, OR spec-vs-spec contradiction on a primitive shape across multiple sources. C24-H1 qualifies because the LCT identifier format diverges across **four** sources (§2.3 + §3.3 + SDK + vectors) for the FUNDAMENTAL canonical primitive of the spec (every LCT identity).
- **MEDIUM** = field/enum rename or shape divergence converging on a normative MUST (M1, M5, M6), OR behavioral-shape SDK gap on a spec-MUST step (M2, M3), OR enum value used by behavior but unspecified in spec (M4).
- **LOW** = doc-hygiene / cross-reference omission / range-semantics underspecification (L1, L2, L3), OR JSON-LD framing omission with no wire/behavior break (L4).
- **INFO** = date staleness with no normative date-dependency (I1) per BC#13.

**Subordinate-ontology cluster status** (BC-C23-3 hard stop): C24 does **NOT** surface a new ontology gap as a new C24 ID. D1 (the L219 dangling reference) is **demoted** into the existing C16-M8 / C23-D2 cluster carry rather than incrementing the cluster count to 8. Cluster remains at **7 audits** (C16-M8 + C17-M1 + C18-M6 + C19-M5 + C20-M5 + C21-M7 + C22-M4+I4), still operator-engagement-class per BC#7.

---

## §A. Still-Unresolved from C9 (re-verified at HEAD `4eb691e8`)

**EMPTY.** All 8 C9 findings were properly resolved by PR #225 (`2088a88b`). Spot-check verification:

| C9 ID | Subject | Current line @ `4eb691e8` | Resolution evidence |
|-------|---------|---------------------------|---------------------|
| H1 | §10.3 phantom V3 `energy_balance` dim | L553 | "ATP/ADP balance MAY be tracked via a context-specific `energy_balance` sub-dimension (see `lct-capability-levels.md`)" — exact remediation text from C9 audit applied |
| H2 | §1.2 ↔ §2.3 entity-type list mismatch (10 vs 12 vs 15) | L28 (§1.2), L66 (§2.3) | Both sites now list all 15 canonical types matching `entity-types.md` §2.1 |
| M1 | §11.1 incorrect birth-certificate validation pseudocode | L585-588 | Pseudocode now uses `any(p["pairing_type"] == "birth_certificate" and p["permanent"] for p in lct["mrh"]["paired"])` (corrected pattern from C9 M1) |
| M2 | Missing RFC 2119 notation section | L11-13 | Notation section present immediately after Status header |
| M3 | §4.2 `genesis_block_hash` normative ambiguity (MUST + "if applicable" + Recommended) | L282 | "`genesis_block_hash`: Blockchain anchor for temporal proof (RECOMMENDED; omit if no blockchain anchor is available)" — RECOMMENDED qualifier applied |
| M4 | §3.2 step 5 `birth_certificate.issuing_society = null` | L226 | Step 5 now reads "Omit `birth_certificate` section (self-issued LCTs are Regular LCTs per §4.3)" |
| L1 | `birth_context` field undocumented | L281 | §4.2 item 1 now defines `birth_context`: "Society type classification — one of `nation`, `platform`, `network`, `organization`, `ecosystem` (RECOMMENDED)" |
| L2 | §5.2 unnumbered sub-headings | L318, L324, L331 | Numbered as §5.2.1, §5.2.2, §5.2.3 |

**Re-verification evidence (BC#2/BC#3 — each line re-read at HEAD)**:
```
$ grep -n "energy_balance" web4-standard/core-spec/LCT-linked-context-token.md
553:- **V3 tensor**: ATP/ADP balance MAY be tracked via a context-specific `energy_balance` sub-dimension (see `lct-capability-levels.md`)

$ grep -n "5\.2\.1\|5\.2\.2\|5\.2\.3" web4-standard/core-spec/LCT-linked-context-token.md
318:#### 5.2.1 Binding Relationships (`mrh.bound`)
324:#### 5.2.2 Pairing Relationships (`mrh.paired`)
331:#### 5.2.3 Witnessing Relationships (`mrh.witnessing`)

$ grep -nB1 -A1 "Notation" web4-standard/core-spec/LCT-linked-context-token.md | head -8
11-## Notation
12-
13:Key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in this document are to be interpreted as described in RFC 2119.
```

All eight C9 findings verifiably resolved. PR #225 was a clean 8/8 sweep — the first C-series RE-audit with **zero carry** (cf. C23 carried 8/12 from C16). This is the disciplined-remediation outcome the C-series cadence was designed to produce.

---

## C24 NEW Findings

### H1 (NEW): LCT-ID format FOUR-WAY divergence across §2.3 example, §3.3 binding algorithm, SDK `LCT.create()`, and test vectors

**Severity**: HIGH (wire-breaking divergence on the canonical primitive identifier of the spec; four distinct shapes across four authoritative sources)

**Why this was missed in C9**: C9 explicitly scoped SDK-alignment OUT (per C9 audit L7: *"SDK alignment: Not in scope for this audit"*). The four-way nature of the divergence — visible only when §2.3, §3.3, the SDK, AND the test vector corpus are all checked together — was therefore systematically out of scope for the prior audit.

**Locations** (each re-read at the cited line):

**(a)** §2.3 L62 — Canonical example LCT ID:
```json
"lct_id": "lct:web4:mb32:...",
```
**Shape**: `lct:web4:mb32:<hash>` — three colon-separated segments, with the literal string `mb32` as a type-tag segment between `web4` and the encoded hash. (Also at §2.3 L174 for lineage parent.)

**(b)** §3.3 L256 — Binding algorithm pseudocode output:
```python
lct_id = "lct:web4:" + multibase32_encode(sha256(binding_proof))
```
**Shape**: `lct:web4:<multibase32-encoded-hash>` — **only two segments**, NO `mb32` literal. The algorithm in the same spec does NOT produce the `mb32` type-tag the example shows.

**(c)** SDK `lct.py:286-289` — `LCT.create()` ID generation:
```python
if lct_id is None:
    raw = f"{entity_type.value}:{public_key}:{ts}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:16]
    lct_id = f"lct:web4:{entity_type.value}:{h}"
```
**Shape**: `lct:web4:<entity_type>:<sha256-hex-prefix-16-chars>` — entity-type tag (not `mb32`), and hex encoding (not multibase32). Hash is over `entity_type:public_key:timestamp` (not over `binding_proof` per §3.3 step 4).

**(d)** Test vectors at `web4-standard/test-vectors/lct/`:
- `interop-minimal-interop.json:22`: `"lct:web4:ai:test0000deadbeef"` — SDK shape
- `interop-revoked-agent.json:22`: `"lct:web4:ai:revoked-agent-999"` — SDK shape
- `lct-jsonld-vectors.json:19`: `"lct:web4:ai:minimal001"` — SDK shape
- `lct-jsonld-vectors.json:88`: `"lct:web4:human:full002"` — SDK shape
- `lct-jsonld-vectors.json:112`: `"lct:web4:org:acme"` — SDK shape (also: `org` is not in EntityType enum — would FAIL `EntityType("org")`)
- `valid-birth-certificate.json:11`: `"lct:web4:mb32_hashed_value"` — neither spec nor SDK shape (literal-string placeholder using `mb32_` as a name prefix with underscore separator, not the `:` segment separator the spec example shows)

**Four-way divergence map**:

| Source | Format | Segments | Encoding | Hash input |
|--------|--------|----------|----------|------------|
| §2.3 example (a) | `lct:web4:mb32:<x>` | 4 | implicit multibase32 | unspecified |
| §3.3 pseudocode (b) | `lct:web4:<x>` | 3 | `multibase32_encode` | `sha256(binding_proof)` |
| SDK (c) | `lct:web4:<entity>:<x>` | 4 | `sha256().hexdigest()[:16]` (hex, NOT multibase32) | `sha256(entity_type:public_key:timestamp)` (NOT binding_proof) |
| vectors (d) | mostly SDK shape; one outlier | varies | varies | N/A (literal strings) |

**Impact**:
1. A spec-§2.3-conformant LCT ID `lct:web4:mb32:<x>` would FAIL the SDK's `EntityType` lookup if `mb32` were treated as the entity-type segment (no enum value `mb32`). SDK's ID-parsing is not strict (lct_id is a plain `str` field, not parsed into segments) — so this masks the divergence at the SDK boundary but introduces wire ambiguity for any downstream parser.
2. A §3.3-pseudocode-conformant LCT ID `lct:web4:<encoded_hash>` (no entity-type segment) would NOT match the SDK's generation pattern, and would not match 4 of 5 test vectors.
3. The SDK uses hex encoding, but §3.3 explicitly says `multibase32_encode`. These are different alphabets (hex = 16 chars 0-9a-f; multibase32 = `b` prefix + RFC 4648 base32). Outputs are not even compatible character sets.
4. The vector at `valid-birth-certificate.json:11` (`"lct:web4:mb32_hashed_value"`) uses `mb32_` with an underscore — neither colon (spec) nor matches SDK shape. It's a literal placeholder, but it's the only vector that follows neither spec nor SDK convention, suggesting the vector author was confused by the four-way state.
5. Cross-language implementers reading §2.3 will produce IDs that don't roundtrip through the SDK or match published vectors. The fundamental identifier of the spec is unspecified at the wire level.

**Remediation classification**: **DESIGN-Q** (out of scope for this audit). Requires a normative decision: (i) is the canonical LCT-ID `lct:web4:<entity_type>:<hash>` (SDK), `lct:web4:mb32:<hash>` (spec example), or `lct:web4:<hash>` (spec algorithm)? (ii) is the encoding hex or multibase32? (iii) is the hash input `binding_proof` or `entity_type:public_key:timestamp`? Cannot be auto-resolved because all four sources have live consumers and the SDK's choice is reflected in 4 of 5 published vectors.

**Test-vector note**: `lct-jsonld-vectors.json:112` uses `"lct:web4:org:acme"` where `org` is NOT in the SDK `EntityType` enum (which has `organization`, not `org`). This is a separate vector hygiene issue (not part of H1 directly) — surfaced here to flag for vector-corpus follow-up.

---

### M1 (NEW): §3.3 binding-algorithm pseudocode returns `binding_proof` as separate variable, contradicting §2.3 where `binding_proof` is a FIELD INSIDE the binding object

**Severity**: MEDIUM (spec-internal contradiction on the binding object's shape; SDK matches §2.3, so §3.3 pseudocode is the deviant)

**Locations** (re-read):

§3.3 L235-258 — algorithm signature and return:
```python
def create_lct_binding(entity_type, private_key, hardware_anchor=None):
    """
    Create cryptographic binding for LCT.

    Returns: (lct_id, binding_object, binding_proof)
    """
    # 1. Create canonical binding structure
    binding = {
        "entity_type": entity_type,
        "public_key": multibase_encode(cose_key(private_key.public_key)),
        "hardware_anchor": hardware_anchor,
        "created_at": utc_now()
    }
    # ... (steps 2-4) ...
    return lct_id, binding, binding_proof
```

The `binding` dict has **4 fields** (no `binding_proof`); the algorithm returns `binding_proof` as the THIRD return value, separate from `binding`.

§2.3 L65-71 — canonical structure:
```json
"binding": {
    "entity_type": "...",
    "public_key": "...",
    "hardware_anchor": "...",
    "created_at": "...",
    "binding_proof": "cose:Sig_structure"
}
```

The §2.3 `binding` object has **5 fields**, with `binding_proof` as a FIELD INSIDE it.

SDK `lct.py:80-99` — `Binding` dataclass:
```python
@dataclass(frozen=True)
class Binding:
    entity_type: EntityType
    public_key: str
    created_at: str
    binding_proof: str = ""
    hardware_anchor: Optional[str] = None
```

SDK matches §2.3 (binding_proof inside Binding dataclass) — confirming §3.3's pseudocode is the deviant source.

**Impact**: An implementer following §3.3 literally would produce a Binding object missing `binding_proof`, then have a separate variable holding the proof. Serializing such an object would NOT match §2.3's canonical structure or the SDK's `Binding.to_dict()` output.

**Remediation classification**: **Autonomous-actionable** — rewrite §3.3 step 3 + step 4 + return signature to assign `binding["binding_proof"] = binding_proof` before returning, and change the return signature to `return lct_id, binding`. Single-section edit. Matches SDK; matches §2.3.

---

### M2 (NEW): SDK `LCT.create()` does NOT add `birth_witnesses` to `mrh.witnessing` per §3.1 step 5

**Severity**: MEDIUM (behavioral-shape gap; spec MUST step omitted in SDK reference implementation)

**Locations** (re-read):

§3.1 L194-213 — Genesis sequence:
```
5. Society initializes MRH:
   - Adds birth_witnesses to mrh.witnessing
   - Adds citizen_role to mrh.paired (permanent)
   - Adds hardware binding to mrh.bound
```

Three explicit MRH initialization sub-steps, ALL named after birth_witnesses/citizen_role/hardware_anchor.

SDK `lct.py:303-323` — `LCT.create()`:
```python
birth_cert = BirthCertificate(
    issuing_society=society,
    citizen_role=citizen_role,
    birth_timestamp=ts,
    birth_witnesses=list(witnesses),     # witnesses go INTO birth_certificate
    birth_context=context,
)

mrh = MRH(
    paired=[
        MRHPairing(
            lct_id=citizen_role,         # citizen_role added to paired ✓
            pairing_type="birth_certificate",
            permanent=True,
            ts=ts,
        )
    ],
    horizon_depth=3,
    last_updated=ts,
)
# witnesses NEVER added to mrh.witnessing
# hardware_anchor NEVER added to mrh.bound (no hardware_anchor param)
```

SDK satisfies sub-step 2 ("Adds citizen_role to mrh.paired (permanent)") — see `pairing_type="birth_certificate"`, `permanent=True`.
SDK does NOT satisfy sub-step 1 ("Adds birth_witnesses to mrh.witnessing").
SDK cannot satisfy sub-step 3 either ("Adds hardware binding to mrh.bound") because `create()` has no `hardware_anchor` parameter.

**Cross-check against vectors**: in `lct-jsonld-vectors.json` vector 002 (L88-200, "Human LCT — full feature"), `mrh.witnessing` (L155-178) is populated with witness LCT objects, but those entries are added MANUALLY by the test fixture, not via `LCT.create()`. SDK callers must populate `mrh.witnessing` themselves.

**Impact**:
1. A consumer relying on §3.1 step 5 will assume `LCT.create()` initializes `mrh.witnessing` with the passed `witnesses` list; the SDK silently leaves it empty.
2. The `birth_certificate.birth_witnesses` and `mrh.witnessing` are then divergent at creation time — the former populated, the latter empty.
3. Spec §11.1's `validate_lct()` does NOT check this invariant (it only verifies `birth_witnesses` length ≥3), so the gap is silent.

**Remediation classification**: **Cross-track (SDK)** — SDK-side fix needed: extend `LCT.create()` to add witness LCT IDs to `mrh.witnessing` (and optionally accept a `hardware_anchor` param to satisfy sub-step 3). NOT autonomous-actionable from this audit alone because it changes SDK behavior shape; should be reviewed at SDK-track sprint planning.

---

### M3 (NEW): SDK `LCT.create()` does NOT create attestations from `birth_witnesses` per §4.2 item 3

**Severity**: MEDIUM (behavioral-shape gap parallel to M2; spec MUST requirement omitted in SDK reference implementation)

**Locations** (re-read):

§4.2 item 3 L294-297:
> 3. **Be attested by birth witnesses** in `attestations`:
>    - Each witness MUST sign existence attestation
>    - Minimum quorum: 3 witnesses
>    - Witnesses MUST be members of issuing society

SDK `lct.py:259, 303-336` — `LCT.create()` returns an LCT with `attestations=[]` (default empty list); no logic creates attestation entries from `witnesses`.

**Cross-check**: SDK's `add_attestation()` method (L361-373) exists and can add attestations post-hoc, but `LCT.create()` itself does not invoke it. The `validate_birth_certificate()` function in spec §11.2 L626-627 says `assert witness_attested(lct, witness)` — calling a helper `witness_attested(lct, witness)` that the SDK does not implement; SDK has no attestation-verification function.

**Impact**:
1. An LCT created via `LCT.create()` with 3 witnesses has `birth_certificate.birth_witnesses = [w1, w2, w3]` but `attestations = []` — failing spec §4.2 item 3.
2. Calling spec §11.2 `validate_birth_certificate()` on an SDK-created LCT would fail at the `assert witness_attested(...)` step (assuming a faithful implementation of the spec validator).
3. Vector `lct-jsonld-vectors.json:140-178` (vector 002) manually populates `attestations` for witnesses — confirming that the fixture authors knew the SDK does not auto-create them.

**Remediation classification**: **Cross-track (SDK)** — SDK-side fix needed: extend `LCT.create()` to populate `attestations` with existence-type entries for each witness (signature placeholder is acceptable, mirroring `binding_proof="cose:signature_placeholder"` at L300). Should be bundled with M2 in SDK-track sprint planning since both concern `LCT.create()` MRH/attestation initialization.

---

### M4 (NEW): Spec doesn't enumerate `revocation.status` values; SDK `RevocationStatus.SUSPENDED` is spec-unspecified BUT behaviorally exercised by published test vector

**Severity**: MEDIUM (spec under-specification on a vocabulary that the published cross-language test corpus depends on)

**Locations** (re-read):

§2.3 L180-184 — `revocation` example object:
```json
"revocation": {
    "status": "active",
    "ts": null,
    "reason": null
}
```
Shows `"status": "active"` as one example value. No enumeration of allowed values.

§7.4 L470-478 — Revocation block:
```
Reasons:
  - compromise: Keys compromised
  - superseded: Rotated to new LCT
  - expired: Time-bounded LCT ended
  - violation: Policy violation

Effect:
  - status = "revoked"
```

§7.4 enumerates four REASONS (`compromise|superseded|expired|violation`) and mentions `status = "revoked"` as the EFFECT. So spec implies a two-value status enum: `{active, revoked}` — but never declares it normatively.

SDK `lct.py:71-74` — `RevocationStatus` enum:
```python
class RevocationStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    SUSPENDED = "suspended"   # ← spec-unspecified
```

Three-value enum. `SUSPENDED` appears NOWHERE in the LCT spec (corpus-sweep verified).

Test vector `lct-jsonld-vectors.json:616-674` (vector 008, "Hybrid LCT with suspended status"):
```json
{
  "description": "Hybrid LCT with suspended status",
  ...
  "revocation": {
    "status": "suspended",
    "ts": "2025-10-05T08:00:00Z",
    "reason": "investigation_pending"
  }
}
```

**The full picture**:
- Spec example: `"active"` (1 value mentioned)
- Spec §7.4 prose: `"revoked"` (1 additional value, implied as effect of revocation)
- SDK enum: `active|revoked|suspended` (3 values, suspended absent from spec)
- Test corpus: actually USES `"suspended"` in published vector 008

So `SUSPENDED` isn't unused enum dead code — it's a BEHAVIORALLY-REQUIRED value in the published cross-language test corpus. An implementation that follows the spec literally would reject vector 008.

**Impact**:
1. Cross-language implementers reading only the spec will not know `suspended` is a valid `revocation.status` value, will not implement it, and will fail vector 008.
2. The spec has no documentation of when an LCT is `suspended` vs `revoked` (`suspended` may imply temporary/recoverable while `revoked` is permanent — but this distinction is implementation-dependent without normative text).
3. `reason: "investigation_pending"` in vector 008 introduces a fifth REASON value (not in §7.4's four-value list) — independent issue but related.

**Remediation classification**: **DESIGN-Q** (out of scope). Requires a normative decision: (i) is `suspended` a deliberate intermediate state between active and revoked? (ii) what are the transition rules? (iii) is the reason taxonomy in §7.4 closed or open?

**Coupling note**: M4 + M6 form a "Revocation taxonomy underspecification" sub-cluster; treat together when prioritizing for operator-engagement.

---

### M5 (NEW): §2.3 canonical-example `composite_score` values don't reproduce from root tensor values under arithmetic mean OR documented weighting

**Severity**: MEDIUM (normative example is numerically unverifiable; readers cannot validate either the example or any implementation)

**Locations** (re-read):

§2.3 L129-142 — T3 tensor example:
```json
"t3_tensor": {
    "talent": 0.85,
    "training": 0.92,
    "temperament": 0.78,
    "sub_dimensions": { "talent": { ... } },
    "composite_score": 0.84,
    "last_computed": "2025-10-01T00:00:00Z",
    "computation_witnesses": ["lct:web4:oracle:trust:..."]
}
```

Roots: 0.85, 0.92, 0.78. Arithmetic mean: (0.85 + 0.92 + 0.78) / 3 = **0.850**. Example shows **0.84**.

§2.3 L144-157 — V3 tensor example:
```json
"v3_tensor": {
    "valuation": 0.89,
    "veracity": 0.91,
    "validity": 0.76,
    "sub_dimensions": { "veracity": { ... } },
    "composite_score": 0.81,
    ...
}
```

Roots: 0.89, 0.91, 0.76. Arithmetic mean: (0.89 + 0.91 + 0.76) / 3 = **0.853**. Example shows **0.81**.

§6.1 L369: `"composite_score": 0.0-1.0,           // Weighted average of roots`
§6.2 L398: same comment.

**Weighting is asserted but never specified**. There is no normative weight table.

**SDK check** (BC#14): `web4-standard/implementation/sdk/web4/trust.py` (search-verified): T3 `composite` property uses weights `0.4 * talent + 0.3 * training + 0.3 * temperament`; V3 `composite` uses `0.3 * valuation + 0.35 * veracity + 0.35 * validity`. Applying SDK weights:
- T3: `0.4 * 0.85 + 0.3 * 0.92 + 0.3 * 0.78 = 0.340 + 0.276 + 0.234 = 0.850` — still **0.850**, not 0.84.
- V3: `0.3 * 0.89 + 0.35 * 0.91 + 0.35 * 0.76 = 0.267 + 0.3185 + 0.266 = 0.8515` — **~0.852**, not 0.81.

**Neither arithmetic mean nor SDK weighted average reproduces the example values.** Either:
1. The example values are wrong (typo/copy-paste error in §2.3), OR
2. The composite is computed via sub-dimensions, not roots (the §2.3 sub_dimensions object would then influence the score — but §6.1 says "Weighted average of **roots**", not "Weighted average of leaves"), OR
3. There is an undocumented decay/aggregation factor.

**Impact**:
1. A reader cannot verify the example values are correct — undermines the canonical example's role as a reference.
2. A reader cannot derive the composite from the roots without additional information not in the spec.
3. Implementations cannot be conformance-tested against the example (every implementation would produce a different number based on its weighting choice).
4. The SDK's own weight choice (T3: 0.4/0.3/0.3; V3: 0.3/0.35/0.35) is undocumented in the spec — three weight values per tensor are normative implementation details encoded only in SDK code.

**Remediation classification**: **Autonomous-actionable** — at minimum, add a §6.x normative weighting formula matching the SDK's values (T3: 0.4/0.3/0.3 over talent/training/temperament; V3: 0.3/0.35/0.35 over valuation/veracity/validity), AND fix the §2.3 example values to reproduce from those weights (or replace with values that DO reproduce arithmetically: e.g. T3 roots 0.84/0.84/0.84 → composite 0.84). Single-section additive change in §6.1/§6.2 + corrected §2.3 example numbers. No SDK change required (SDK weights become normative).

**Note**: this also resolves the cross-spec gap with `lct-capability-levels.md` (C20-audited), which discusses tensor scoring at different capability levels — having a normative weight formula gives lct-capability-levels.md a stable referent.

---

### M6 (NEW): §7.3 ↔ §7.4 ↔ SDK `RevocationStatus` — "superseded" is a STATUS in §7.3, a REASON in §7.4, and absent from SDK

**Severity**: MEDIUM (spec self-contradicts on status-vs-reason taxonomy; SDK doesn't recognize either framing of "superseded")

**Locations** (re-read):

§7.3 Rotation L459-461:
```
Society: Retire parent LCT
  - Mark as "superseded"
  - Update lineage in new LCT
```

"Mark as `superseded`" reads as a STATUS assignment — the parent LCT's status becomes `"superseded"` after rotation.

§7.4 Revocation L470:
```
Reasons:
  - compromise: Keys compromised
  - superseded: Rotated to new LCT
  - expired: Time-bounded LCT ended
  - violation: Policy violation
```

Here `superseded` is enumerated as one of four REASONS, with §7.4 L475 making status take the value `"revoked"`. So under §7.4, a rotated LCT has `status = "revoked"` and `reason = "superseded"`.

These two framings of "superseded" are **mutually exclusive**:
- §7.3 says rotation → `status = "superseded"`
- §7.4 says rotation → `status = "revoked"`, `reason = "superseded"`

A rotated parent LCT cannot have both `status = "superseded"` AND `status = "revoked"`. The two sections contradict.

SDK `lct.py:71-74` — `RevocationStatus` enum:
```python
class RevocationStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    SUSPENDED = "suspended"
```

No `SUPERSEDED` value. SDK cannot represent the §7.3 framing at all. SDK `revoke()` method (L342-347) sets `revocation_status = REVOKED` and accepts a free-form `reason` string — supports §7.4 framing only.

**The full picture**:
| Framing | Source | Rotated parent LCT status | Rotation reason |
|---------|--------|---------------------------|-----------------|
| §7.3 prose | spec | `"superseded"` | (none — it's the status itself) |
| §7.4 enumeration | spec | `"revoked"` | `"superseded"` |
| SDK | impl | `"revoked"` | free-form string |

**Impact**:
1. An implementer reading §7.3 produces LCTs with `status = "superseded"`; an implementer reading §7.4 produces LCTs with `status = "revoked"` + `reason = "superseded"`. These are wire-divergent.
2. SDK CAN produce the §7.4 framing (via `revoke(reason="superseded")`) but CANNOT produce the §7.3 framing (no enum value).
3. Combined with M4 (SUSPENDED unspecified in spec), the entire revocation state machine is underspecified: spec lacks a normative enumeration of `revocation.status` values, has internal contradiction on "superseded" semantics, and the SDK adds one extra value (`suspended`) while omitting one referenced by spec (`superseded`).

**Remediation classification**: **DESIGN-Q** (out of scope). Requires a normative decision: (i) is `superseded` a status (matching §7.3) or a reason (matching §7.4)? (ii) what is the full enumeration of `revocation.status` values? Aligning all sources requires either (a) updating §7.3 to say "Mark with `status='revoked'`, `reason='superseded'`" — matches §7.4 + SDK, OR (b) updating §7.4 to remove `superseded` from reasons and adding `SUPERSEDED` to the status enum — matches §7.3.

**Coupling note**: M6 + M4 form a "Revocation taxonomy underspecification" sub-cluster; resolution should be coherent across status enum + reason enum + rotation semantics.

---

### L1 (NEW): §11.1 `validate_lct` pseudocode references three undefined helpers

**Severity**: LOW (pseudocode coherence; reader cannot trace helper definitions)

**Locations** (re-read):

§11.1 L591-595 — final lines of `validate_lct()` pseudocode:
```python
    # Tensor validation
    validate_t3_tensor(lct["t3_tensor"])
    validate_v3_tensor(lct["v3_tensor"])

    # Binding proof verification
    verify_binding_proof(lct["binding"], lct["binding"]["binding_proof"])
```

Three function calls — `validate_t3_tensor`, `validate_v3_tensor`, `verify_binding_proof` — that are not defined anywhere in the LCT spec. Spec corpus-sweep:
```
$ grep -n "validate_t3_tensor\|validate_v3_tensor\|verify_binding_proof" web4-standard/core-spec/LCT-linked-context-token.md
591:    validate_t3_tensor(lct["t3_tensor"])
592:    validate_v3_tensor(lct["v3_tensor"])
595:    verify_binding_proof(lct["binding"], lct["binding"]["binding_proof"])
```

(Only the call sites; no definitions.) SDK has `T3.composite` and `V3.composite` properties but no `validate_t3_tensor` / `validate_v3_tensor` functions matching these names.

**Impact**: An implementer reading §11.1 cannot trace what these helpers should do. Calls appear authoritative but reference nothing.

**Remediation classification**: **Autonomous-actionable** — either (a) add a brief stub-paragraph after §11.1 listing the expected semantics of each helper (`validate_t3_tensor` MUST check root dimensions are in `[0.0, 1.0]` and `composite_score` is in range; etc.), OR (b) inline the checks into the pseudocode (`assert 0 <= lct["t3_tensor"]["talent"] <= 1.0`, etc.), OR (c) mark the calls as `# implementation-defined`. Option (c) is the smallest delta.

---

### L2 (NEW): §13 References omits two specs that are cited normatively within the document

**Severity**: LOW (doc hygiene; cross-references incomplete)

**Locations** (re-read):

§1.2 L28 — Entity definition:
> see `entity-types.md` §2.1 for the canonical 15-type taxonomy

§10.3 L553 — V3 ATP/ADP:
> ATP/ADP balance MAY be tracked via a context-specific `energy_balance` sub-dimension (see `lct-capability-levels.md`)

§13 References (L651-657):
```
- **Web4 Core Protocol**: `core-spec/core-protocol.md`
- **MRH Specification**: `core-spec/mrh-tensors.md`
- **T3/V3 Tensors**: `core-spec/t3-v3-tensors.md`
- **R6 Framework**: `core-spec/r6-framework.md`
- **SAL Specification**: `core-spec/web4-society-authority-law.md`
- **ATP/ADP Cycle**: `core-spec/atp-adp-cycle.md`
- **LCT Protocol Details**: `protocols/web4-lct.md`
```

`entity-types.md` and `lct-capability-levels.md` are both cited normatively in the document body but absent from the References list. Both exist as files in `web4-standard/core-spec/`.

**Impact**: A reader navigating from the References list cannot find these two cited specs. Both citations are normative (§1.2 says "canonical taxonomy"; §10.3 explicitly delegates V3 sub-dimension specification).

**Remediation classification**: **Autonomous-actionable** — add two lines to §13:
```
- **Entity Types**: `core-spec/entity-types.md`
- **LCT Capability Levels**: `core-spec/lct-capability-levels.md`
```

Single-section additive edit.

---

### L3 (NEW): §6.2 V3 `valuation` range `0.0+` (unbounded above) but `composite_score` range `0.0-1.0` — composite-of-mixed-range semantics unspecified

**Severity**: LOW (range-arithmetic underspecification; edge-case behavior undefined)

**Locations** (re-read):

§6.2 L394-398 — V3 tensor:
```json
"v3_tensor": {
    "valuation": 0.0+,                    // Subjective worth (can exceed 1.0)
    "veracity": 0.0-1.0,                  // Truthfulness/accuracy (root aggregate)
    "validity": 0.0-1.0,                  // Soundness of reasoning (root aggregate)
    "sub_dimensions": {},
    "composite_score": 0.0-1.0,
    ...
}
```

`valuation` is documented as `0.0+` (allowed to exceed 1.0, comment confirms "can exceed 1.0"). `composite_score` is documented as `0.0-1.0` (capped at 1.0).

If valuation = 5.0 (allowed per range) and veracity = validity = 0.5, then under SDK weighting (0.3 * 5.0 + 0.35 * 0.5 + 0.35 * 0.5 = 1.5 + 0.175 + 0.175 = 1.85) the composite EXCEEDS its stated 1.0 cap.

The spec provides no rule for: clamp at 1.0? rescale valuation to [0,1] first? exclude valuation from composite? Compute composite over a different formula?

**Impact**:
1. Composite scores computed from high-valuation V3 tensors may exceed the stated range, violating §6.2's own bounds.
2. Implementations will choose ad-hoc resolution rules; cross-language interop on V3 composite breaks.
3. Vectors in `lct-jsonld-vectors.json` use valuation values ≤ 1.0 (sweep-verified), so the issue is masked by vector design choices but is a latent gap.

**Remediation classification**: **DESIGN-Q** (out of scope). Requires a normative decision: (i) clamp composite to [0, 1.0]? (ii) rescale valuation to [0, 1.0] before composite? (iii) restrict valuation to [0, 1.0] (overriding the "can exceed 1.0" allowance)? (iv) extend composite range to [0, ∞) and document?

---

### L4 (NEW): §2.3 canonical-example raw JSON has no `@context` / `@type` fields, but SDK `to_jsonld()` emits both and 10/10 published vectors include both

**Severity**: LOW (doc/implementation/vector gap; JSON-LD framing missing from spec example; no wire/behavior break since the example is not consumed by validators)

**Locations** (re-read):

§2.3 L60-72 — canonical-example opening:
```json
{
  "lct_id": "lct:web4:mb32:...",
  "subject": "did:web4:key:z6Mk...",

  "binding": { ... },
  ...
}
```

No `@context` or `@type` field at any level of the example.

SDK `lct.py:543-548` — `to_jsonld()`:
```python
doc: Dict[str, Any] = {
    "@context": [LCT_JSONLD_CONTEXT],
    "@type": "web4:LinkedContextToken",
    "lct_id": self.lct_id,
    "subject": self.subject,
}
```

Where `LCT_JSONLD_CONTEXT = "https://web4.io/contexts/lct.jsonld"` (L45).

Test vectors `lct-jsonld-vectors.json` contain 10 vector documents. ALL 10 include both `@context` and `@type`:
- vector 001 L15+L18, vector 002 L84+L87, vector 003 L206+L209, vector 004 L276+L279, vector 005 L374+L377, vector 006 L460+L463, vector 007 L550+L553, vector 008 L618+L621, vector 009 L686+L689, vector 010 L757+L760.

Vector file `meta.spec_reference` field (head of file) cites "section 2.3" — but the actual §2.3 example would fail JSON-LD validation (no `@context`).

**Impact**:
1. A reader following §2.3 verbatim produces non-JSON-LD documents that fail validation by any JSON-LD-aware consumer.
2. The vector file is internally inconsistent: claims `spec_reference: "section 2.3"` while every vector includes `@context`/`@type` that §2.3 omits.
3. Spec §1 abstract calls LCTs "verifiable digital presence certificate[s]" without mentioning JSON-LD; spec §2.3 example reinforces a non-JSON-LD format; but SDK and vectors require JSON-LD framing.

**Remediation classification**: **Autonomous-actionable** — add `@context` (array with `"https://web4.io/contexts/lct.jsonld"`) and `@type` (`"web4:LinkedContextToken"`) to the §2.3 canonical-example opening, matching SDK + vector convention. Single-example edit (~2 lines added). Parallels M2/M3 (spec text vs SDK behavior vs vector corpus) but is doc-only.

---

### INFO1 (NEW): Spec dates `October 1, 2025` (header L4 + footer L663) are 8.0 months stale

**Severity**: INFO (per BC#13: date staleness alone is INFO unless coupled with a normative date-dependency; LCT spec has no normative date-dependency)

**Locations**:

- L4: `**Date**: October 1, 2025`
- L663: `**Last Updated**: October 1, 2025`

Current date: 2026-05-31. Last substantive content edit: PR #225 (`2088a88b`, 2026-05-22) which applied all 8 C9 remediations but did not bump dates.

Per BC#15: bumpable in this audit's own remediation cycle (this IS the LCT spec's RE-audit, so the LCT spec is a substantively-edited file in the remediation PR for C24 — date bump is in scope).

**Remediation classification**: **Autonomous-actionable** — bump L4 and L663 to the remediation PR's commit date in the next exit.

---

## §B. Cross-Track CARRY (cite-only, NOT re-issued per BC-C23-1)

### C23-H1: BirthCertificate THREE-WAY shape drift (SAL §2.2 vs LCT-spec inline vs SDK `lct.py::BirthCertificate`)

**Status**: Already captured as DESIGN-Q in C23 audit (`docs/audits/C23-society-authority-law-audit-2026-05-30.md` §"C23 NEW Findings > H1").

**LCT-spec involvement**: The LCT spec's `birth_certificate` inline-field shape (§2.3 L73-84 + §4.2 L274-297) is **leg (b)** of C23-H1's three-way divergence. The full divergence map (re-quoting from C23-H1) is:
- **(a)** SAL §2.2: `Web4BirthCertificate` JSON-LD standalone object with camelCase fields (`citizenRole`, `birthTimestamp`, `lawOracle`, etc.) and `rights`/`obligations` fields
- **(b)** LCT spec §2.3 + §4.2: `birth_certificate` inline field with snake_case (`citizen_role`, `birth_timestamp`, `birth_witnesses`) and `birth_context` enum
- **(c)** SDK `lct.py:144-164`: `BirthCertificate` dataclass matching leg (b)

Per BC-C23-1 firewall, this audit does NOT re-issue the divergence as a new C24 ID. Operator-engagement bundle for any LCT-spec remediation should reference C23-H1 as the canonical capture and coordinate any §2.3 / §4.2 changes with whichever resolution C23-H1 receives.

---

## §C. Considered but NOT issued (DEMOTED)

### D1 (DEMOTED): `web4-core-ontology.ttl` L219 dangling reference to `web4:Web4BirthCertificate`

**Why considered**: Searched the ontology TTL while doing the C24 BirthCertificate cross-check. Found at L219:
```
rdfs:range web4:Web4BirthCertificate ;
rdfs:comment "Links an entity to its birth certificate establishing initial presence. References Web4BirthCertificate class from SAL ontology." .
```

`web4:Web4BirthCertificate` is referenced but not defined in `web4-core-ontology.ttl`; the comment says "from SAL ontology" but `sal-ontology.ttl` does not exist as a file (C16-M8 / C23-D2 carry).

**Why demoted**:
1. **Already in subordinate-ontology cluster**: this is the SAME L219 site referenced in C23-D2 (and originally surfaced under C16-M8's broader "RDF vocabulary in non-canonical location / missing `sal-ontology.ttl`" framing).
2. **BC-C23-3 hard cap**: subordinate-ontology cluster is at 7 audits (C16-M8 + C17-M1 + C18-M6 + C19-M5 + C20-M5 + C21-M7 + C22-M4+I4). Issuing this as a new C24 finding would push the count to 8, violating the cap. Cluster remains operator-engagement-class per BC#7 and is not auto-resolvable from C24.
3. **No new information**: C24 surfaces no aspect of this issue that C16-M8 / C23-D2 did not already capture.

**Demoted into**: existing C16-M8 cluster carry; cluster count remains 7.

---

### D2 (DEMOTED): §1.2 prose "AI" (English acronym, uppercase) vs §2.3 wire enum `ai` (JSON identifier, lowercase)

**Why considered**: Spotted casing difference during the C9 H2 re-verification.

§1.2 L28: "human, AI, society, organization, role, task, ..."
§2.3 L66: "human|ai|society|organization|role|task|..."

§1.2 capitalizes the English acronym AI; §2.3 uses lowercase JSON identifier `ai`.

**Why demoted**: The typographic difference reflects **different purposes** — §1.2 is English-prose terminology (acronyms capitalize in English typography); §2.3 is a wire-format enum (JSON identifiers are conventionally lowercase). The SDK uses `EntityType.AI = "ai"` matching §2.3. The §1.2 entry explicitly delegates the canonical enumeration to `entity-types.md` ("see `entity-types.md` §2.1 for the canonical 15-type taxonomy"), making §1.2's role gloss-level English. No defect; surface convention difference is intentional.

**Not promoted** because: (i) no implementer could be confused — §1.2 says "see entity-types.md for canonical", (ii) no wire-format consumer reads §1.2 prose as an enum, (iii) the alternative (forcing §1.2 to use lowercase `ai` mid-sentence) would violate English typography rules.

---

## Remediation Classification Summary (for next-exit planning)

| ID | Severity | Class | One-line action |
|----|----------|-------|-----------------|
| H1 | HIGH | **DESIGN-Q** | Choose canonical LCT-ID format among 4 candidates |
| M1 | MEDIUM | **Autonomous-actionable** | Rewrite §3.3 to put binding_proof inside binding object |
| M2 | MEDIUM | Cross-track (SDK) | Extend `LCT.create()` to populate `mrh.witnessing` |
| M3 | MEDIUM | Cross-track (SDK) | Extend `LCT.create()` to populate `attestations` |
| M4 | MEDIUM | **DESIGN-Q** | Decide `SUSPENDED` status semantics + enumerate full status enum |
| M5 | MEDIUM | **Autonomous-actionable** | Add §6.x normative weight formula + fix §2.3 example numbers |
| M6 | MEDIUM | **DESIGN-Q** | Resolve `superseded` status-vs-reason between §7.3 / §7.4 / SDK |
| L1 | LOW | **Autonomous-actionable** | Mark §11.1 helper calls as `# implementation-defined` |
| L2 | LOW | **Autonomous-actionable** | Add 2 lines to §13 References |
| L3 | LOW | **DESIGN-Q** | Specify V3 composite computation under unbounded valuation |
| L4 | LOW | **Autonomous-actionable** | Add `@context` + `@type` to §2.3 canonical example |
| INFO1 | INFO | **Autonomous-actionable** | Bump L4 + L663 date strings to remediation-PR date (BC#15 lift) |

**Split**:
- **Autonomous-actionable**: 6 (M1 + M5 + L1 + L2 + L4 + INFO1) — recommended remediation PR for next exit
- **DESIGN-Q**: 4 (H1 + M4 + M6 + L3) — operator-engagement bundle (sub-cluster: M4+M6 form a coherent revocation-taxonomy decision)
- **Cross-track (SDK)**: 2 (M2 + M3) — SDK-track sprint planning

**Coupling notes**:
- M4 + M6: should be resolved together as one revocation-taxonomy decision (status enum + reason enum + rotation semantics in one design pass)
- M1 + H1: M1 (binding-algorithm shape) is independent of H1 (ID format) — can be remediated separately, but the §3.3 rewrite should consider both
- L4 + C23-H1: §2.3 birth_certificate inline example is affected by both C23-H1 (shape decision) AND L4 (JSON-LD framing) — coordinate

---

## Cross-Reference to Prior Audits

| Audit | Spec | Findings | Remediated |
|-------|------|----------|------------|
| C9 | LCT-linked-context-token.md (FIRST) | 8 (2H, 4M, 2L) | PR #225 (8/8 — clean sweep) |
| C16 | web4-society-authority-law.md | 12 (3H, 5M, 4L) | PR #240 (5/12, partial) |
| C17 | dictionary-entities.md | 10 (1H, 4M, 5L) | PR #242 (7/10) |
| C18 | acp-framework.md | 11 (3H, 5M, 3L) | PR #244 (6/11) |
| C19 | multi-device-lct-binding.md | 13 (3H, 6M, 4L) | PR #246 (6/13) |
| C20 | lct-capability-levels.md | 13 (3H, 7M, 3L) | PR #248 (7/13) |
| C21 | SOCIETY_METABOLIC_STATES.md | 16 (3H, 9M, 4L) | PR #250 (8/16) |
| C22 | SOCIETY_SPECIFICATION.md | 11 (3H, 6M, 2L) | PR #252 (8/11) |
| C23 | web4-society-authority-law.md (RE-AUDIT) | 7 NEW + 8 C16-carried (1H, 3M, 2L, 1INFO new) | PR #254 (3/7, autonomous subset) |
| **C24** | **LCT-linked-context-token.md (RE-AUDIT)** | **12 NEW + 0 C9-carried** (1H, 6M, 4L, 1INFO new) | **Pending** |

---

## Notes

**Clean C9-remediation outcome**: All 8 C9 findings RESOLVED by PR #225 — first C-series RE-audit with **zero carry**. This is the disciplined-remediation outcome the C-series cadence was designed to produce; contrast with C23 (re-audited SAL after PR #240 carried 7 of 12 unresolved). Suggests the C9 audit + PR #225 cycle was a particularly clean execution worth pattern-matching for future audits.

**SDK + vector corpus expanded scope**: 5 of the 12 new C24 findings (H1, M2, M3, M4, L4) involve SDK or test-vector evidence that C9 explicitly scoped out. The expanded BC#14 + BC#14-vector-extension behavioral-shape verification surfaces findings that pure spec-text reading does not. Confirms the audit-instrument complementarity principle (cf. memory exit #82) — fresh-eye + SDK + vectors find different surface gaps.

**Cluster discipline**: D1 (ontology) and C23-H1 (BirthCertificate cross-track) are both correctly excluded from new C24 IDs — preserving BC-C23-3 cluster cap and BC-C23-1 cross-doc firewall. Demoted-list explicitly enumerates them so the firewall is visible to remediators.

**Revocation taxonomy sub-cluster**: M4 + M6 form a coherent sub-cluster. Treating them as one design decision in operator-engagement keeps the resolution coherent across all three sources (spec §7.x + SDK enum + test vector 008).

---

*"An LCT is not an identity. It is a presence — witnessed, contextualized, and witness-hardened."* — and now, with C24, more clearly specified across its four canonical authorities.
