# C14: r7-framework.md Internal Consistency Audit

**Date**: 2026-05-24
**Auditor**: Autonomous session (legion-web4-20260524-180000)
**Document**: `web4-standard/core-spec/r7-framework.md` (925 lines)
**Cross-references verified**:
- `web4-standard/core-spec/r6-framework.md` §1.2, §5 (the C12 audit target — PR #231 in-flight)
- `web4-standard/implementation/sdk/web4/r6.py` (the SDK's R7 implementation: `R7Action`, `Role`, `ReputationDelta`, `ActionStatus`)
- `web4-standard/core-spec/t3-v3-tensors.md` §3.1 (canonical V3 dimensions)

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| HIGH | 1 | Role examples use `roleType` (class URI) instead of the normative `roleLCT` |
| MEDIUM | 5 | Reputation examples drop role context; V3 dimension misnamed; `action_id` read before ledger write; undefined status enum; over-broad determinism claim |
| LOW | 4 | Python keyword in pseudocode; component-list/structure mismatch; auditor-adjust vs determinism; atomic-settlement vs non-transactional flow |

**Cross-audit note**: This audit reconciles with the C12 r6-framework audit (#229, remediation PR #231 open). It deliberately does **not** re-flag the R6→R7 "tensor updates moved from Result to Reputation" framing (§1.7 L231), which is consistent-by-design with r6 §1.6 — avoiding the C11-style cross-document overcall. Every cross-reference below was re-read against the live file at the cited line.

---

## HIGH Findings

### H1: §5 examples specify `role` via `roleType` (class URI) — contradicts the `roleLCT` model

**Location**: §5.1 line 568, §5.2 line 593, §5.4 line 700, §5.5 line 742
**Severity**: HIGH

Four of the five transaction examples encode the role as a bare type string:

```json
"role": {"roleType": "web4:Reader"}        // §5.1 L568
"role": {"roleType": "web4:Investigator"}  // §5.2 L593
"role": {"roleType": "web4:Authority"}     // §5.4 L700
"role": {"roleType": "web4:Agent", "actingFor": "lct:web4:client:..."}  // §5.5 L742
```

But §1.2 defines the Role structure with **`roleLCT`** (line 70) and states explicitly:
> Role is represented by a role LCT (fully flexible, domain-specific) (line 63)

and §1.7 Key Properties reinforces:
> **LCT-Based Roles**: Roles are LCTs, fully flexible and domain-specific (line 289)

`roleType: "web4:Reader"` is a *class/type URI*, not a role-LCT *instance*. Only §5.3 (lines 633–647) uses the normative full structure with `roleLCT`.

**SDK confirmation**: The SDK `Role` dataclass (`r6.py` line 234) has only `role_lct` (serialized as `roleLCT`, line 243) — there is **no `roleType` field**. `R7Action` validation (`r6.py` lines 766–767) requires `role.role_lct`.

**Impact**: Implementers copying the §5 examples would emit role objects the SDK cannot consume (the SDK reads `roleLCT`, not `roleType`). The examples contradict the spec's own normative role model in two places.

**Cross-audit reconciliation**: The C12 r6 audit flagged the inverse — r6 §1.2 carries *both* `roleType` and `roleLCT` (r6 L60–61) and the remediation (PR #231) standardizes on `roleLCT`. In r7, §1.2 is already correct (`roleLCT` only); it is the §5 examples that regressed to `roleType`. The r7 fix is therefore narrower than r6's: change the four `roleType` example values to `roleLCT` instances.

**Remediation**: Replace `roleType: "web4:X"` with `roleLCT: "lct:web4:role:..."` in §5.1, §5.2, §5.4, §5.5. (Optionally keep a `roleType`/class hint only if §1.2 is amended to define it — but that would contradict the SDK and should be coordinated with the C12 outcome.)

---

## MEDIUM Findings

### M1: §5 reputation examples omit `role_lct` — contradicts the role-contextualization principle

**Location**: §5.1 lines 576–584, §5.2 lines 607–624, §5.4 lines 713–733, §5.5 lines 771–791
**Severity**: MEDIUM

The reputation blocks in four of five examples carry `subject_lct` but **no `role_lct`** (and no `role_pairing_in_mrh`). Yet §1.7 states this is the defining property:

> **Critical Design Principle**: Reputation is **role-contextualized** … There is no global reputation—only reputation within specific role contexts. (line 233)

and lists **Role LCT** as a first-class reputation component (line 237). Only §5.3 (line 664) includes `role_lct`.

**SDK confirmation**: `ReputationDelta` (`r6.py` line 590) declares `role_lct: str` with **no default** — it is mandatory. A reputation object matching the §5.1/§5.2/§5.4/§5.5 examples cannot be constructed without it.

**Impact**: The examples model exactly the "global reputation" the spec says does not exist. They contradict both §1.7 and the SDK's required field.

**Remediation**: Add `role_lct` (and ideally `role_pairing_in_mrh`) to the reputation block of §5.1, §5.2, §5.4, §5.5, consistent with §5.3.

### M2: V3 dimension named `value` in `v3InRole` — canonical V3 dimension is `valuation`

**Location**: §1.2 line 80, §5.3 line 645
**Severity**: MEDIUM

The `v3InRole` structure lists three dimensions as `veracity`, `validity`, `value`:

```json
"v3InRole": { "veracity": 0.92, "validity": 0.88, "value": 0.85 }  // §1.2 L77-81
"v3InRole": { "veracity": 0.90, "validity": 0.92, "value": 0.88 }  // §5.3 L642-646
```

But the canonical V3 dimensions (`t3-v3-tensors.md` §3.1: **Valuation**, Veracity, Validity) and the SDK `V3` class use **`valuation`**, not `value`.

**SDK confirmation**: `r6.py` line 993 deserializes `v3InRole` via `valuation=v3d.get("valuation", 0.5)`. A spec-conformant `v3InRole` carrying `value` would **silently drop** the Valuation dimension to the 0.5 default — the SDK never reads `value`.

**Impact**: Silent data loss across the spec↔SDK boundary; naming divergence from the canonical V3 definition. (Note: the `v3_delta` examples never exercise this dimension at all — they only show veracity/validity — so the mismatch is masked in the delta examples but live in `v3InRole`.)

**Remediation**: Rename `value` → `valuation` in `v3InRole` at §1.2 and §5.3.

### M3: `action_id = result.ledgerProof.txHash` read before the ledger entry exists

**Location**: §2.3 line 397 vs §2.4 lines 491–506; contradicts §6 MUST #4 (line 801)
**Severity**: MEDIUM

`compute_reputation_delta` sets the reputation's `action_id` from the ledger transaction hash:

```python
action_id=result.ledgerProof.txHash   # §2.3 L397
```

But in the transaction flow `settle_r7_action` (§2.4), `compute_reputation_delta` is called at **line 492**, while the ledger entry is created and written only afterward at **lines 505–506** (`create_ledger_entry` → `write_to_ledger`). Moreover, `execute_r7_action` (§2.2) builds the result via `create_r7_result(status, output, resources)` (lines 355–359 / 363–367) and **never populates `ledgerProof`**. So `result.ledgerProof` is undefined at the point it is read.

This also collides with §6 MUST #4 (line 801): *"Failed actions MUST still produce valid R7 results with reputation."* The §2.2 failure branch (lines 363–367) produces a result with no `ledgerProof`, yet settlement would still call `compute_reputation_delta`, dereferencing `result.ledgerProof.txHash` → failure.

**SDK confirmation**: The SDK avoids this entirely — it sets `action_id=self.action_id` (`r6.py` line 850), using the action's own pre-assigned id, and `ReputationDelta.action_id` defaults to `""`.

**Impact**: The normative pseudocode is internally inconsistent (reads a field before it is produced) and contradicts the failed-action requirement.

**Remediation**: Source `action_id` from the action's own identifier (e.g., `r7_action.request.nonce` or a pre-assigned action id) rather than `result.ledgerProof.txHash`; OR reorder settlement so the ledger proof is written before reputation computation and explicitly handle the failure path.

### M4: Action `status` values are inconsistent and the enum is undefined

**Location**: §2.2 line 363 (`"failure"`) vs §7 line 852 (`"error"`) vs §1.6 line 196 ("Success/failure status")
**Severity**: MEDIUM

The spec uses three different `status` values without defining the allowed set:
- §2.2 execution sets `status="success"` (line 356) and `status="failure"` (line 363)
- §7 Error R7 Result shows `"status": "error"` (line 852)
- §1.6 describes the field as "Success/failure status" (line 196)

It is never stated whether `"failure"` and `"error"` are the same, distinct, or which applies when (e.g., validation rejection vs execution exception).

**SDK confirmation**: `ActionStatus` (`r6.py` lines 81–83) defines `SUCCESS`/`FAILURE`/`ERROR` **plus** `PENDING` and `VALIDATED` (used at lines 495, 509) — a five-value enum the spec never mentions.

**Impact**: Cross-language implementations cannot agree on the status vocabulary; a conformance test cannot know whether a failed action reports `failure` or `error`.

**Remediation**: Add a normative status enum to §1.6 (or a dedicated sub-section) enumerating the allowed values and their meanings, aligned with the SDK's `ActionStatus`.

### M5: Determinism is asserted for results that include non-deterministic fields

**Location**: §4.1 lines 543–544, §6 MUST #3 line 800, §9 line 916, §1.6 line 193
**Severity**: MEDIUM

The spec makes a strong, unscoped determinism guarantee:
> Given the same R7 inputs, the result and reputation must be identical across all valid implementations. (§4.1, line 544)

and §1.6 calls the Result "The **deterministic** outcome of the action execution" (line 193).

But the Result definition itself includes inherently non-deterministic fields — `resourceConsumed` with `cpu_seconds` and `memory_peak` (line 214) — and §5.3 trains an ML model (`train_model`, GPU hours, lines 648–661), an execution that cannot be bit-identical across implementations or runs. The reputation, computed from the result, inherits this non-determinism.

**Impact**: Taken literally, the guarantee is unsatisfiable for any metered/real-world action; it conflates the protocol's deterministic settlement/reputation *computation* (deterministic given a fixed Result) with the action *execution* (not deterministic).

**Remediation**: Scope the determinism property — e.g., "Given the same R7 inputs **and the same Result**, the reputation delta and settlement MUST be identical across implementations" — and acknowledge that action execution and measured resource consumption are not required to be deterministic.

---

## LOW Findings

### L1: §2.4 pseudocode uses `from=` — a reserved Python keyword

**Location**: §2.4 line 481
**Severity**: LOW

```python
transfer_atp(
    from=r7_action.role.actor,   # L481 — SyntaxError: 'from' is a keyword
    to=resource_providers,
    amount=final_cost
)
```

`from` is a reserved word in Python; this keyword argument is a literal syntax error. The surrounding pseudocode is otherwise valid Python, so the slip is conspicuous.

**Remediation**: Rename the parameter (e.g., `sender=`, `from_lct=`) or annotate the block as illustrative non-Python.

### L2: §1.7 Components list does not match the Reputation structure

**Location**: §1.7 Components (lines 235–244) vs Structure (lines 248–282)
**Severity**: LOW

The prose Components list says **"Net magnitude"** (line 244, singular), but the structure has two fields: `net_trust_change` and `net_value_change` (lines 278–279). The structure also carries `rule_triggered` (line 261) and `timestamp` (line 280) that the Components list does not enumerate.

**Remediation**: Reconcile the Components list with the actual structure (split "Net magnitude" into the two net-change fields; add `rule_triggered` and `timestamp`).

### L3: SAL table "Auditor can adjust [Result] based on evidence" tensions with determinism + immutability

**Location**: §3 line 538 vs §4.1 (line 544) and §4.2 (line 547)
**Severity**: LOW

The R7-SAL table entry for **Result** reads: *"Auditor can adjust based on evidence."* A post-hoc auditor adjustment of the Result is hard to reconcile with §4.1 Determinism (same inputs → identical result) and §4.2 Non-repudiation (actions recorded on the **immutable** ledger). The mechanism, timing, and effect on the recorded result/reputation are unspecified.

**Remediation**: Clarify whether auditor adjustments produce a *new* corrective R7 action (preserving immutability) rather than mutating the original Result, and reconcile the wording with §4.1/§4.2.

### L4: §4.5 "Atomic Settlement" vs the non-transactional `settle_r7_action` flow

**Location**: §4.5 lines 555–556 vs §2.4 lines 470–525
**Severity**: LOW

§4.5 promises: *"Resource transfers and tensor updates either fully complete or fully roll back."* But `settle_r7_action` performs ATP transfer (line 480) and escrow release (line 485) **before** reputation computation (line 492), tensor updates (lines 496–502), and the ledger write (line 506), with no transaction/rollback scaffolding shown. A failure after line 480 would leave ATP transferred without the corresponding tensor/ledger updates.

**Remediation**: Either show the atomic boundary (e.g., a transaction wrapper / two-phase commit) in §2.4, or soften §4.5 to describe the intended guarantee and where it is enforced.

---

## Structural Observations (Informational)

1. **Section numbering**: Consistent (§1–§9, sub-sections numbered correctly). No gaps or duplicates.

2. **R6↔R7 framing is consistent** (verified, not a finding): §1.7 (line 231) "In R6, tensor updates were buried in the Result" and §8 migration "Extracting tensor updates from Result into Reputation" (line 907) align with r6 §1.6, which genuinely lists tensor updates as an R6 Result. This is by design — flagged here explicitly to avoid the cross-document overcall pattern seen in earlier C-series audits.

3. **SDK alignment overall**: The SDK implements R7 in `r6.py` (module docstring: "Web4 R7 Action Framework"; "R7 is the current version of the R6 framework"). It is highly consistent with §1.2/§1.7's normative structures — and in three places (roleLCT-only role, required `role_lct` on reputation, `action_id` sourcing) it is *more* correct than the §5 examples and §2.x pseudocode, which is why H1/M1/M3 surface as example/pseudocode defects rather than design defects.

4. **The `roleType` regression is localized to §5 examples.** Unlike r6 (where `roleType` reaches into §1.2 and the settlement pseudocode), r7's normative body (§1.2, §2.x) and SDK are clean; only the illustrative examples drift. This makes H1 a low-risk, mechanical fix.

5. **Pseudocode vs structure drift**: M3, L1, L2, L4 all stem from the §2.x Python pseudocode having diverged from the §1.x JSON structures and the SDK. A single pass aligning the §2.x flow with the SDK's actual `settle()` logic would resolve all four.

---

## Cross-Audit Note

H1 (roleType) and M2 (V3 `value`) are the r7 instances of patterns the C-series has touched on the r6/tensor side. A remediation pass should:
1. Apply H1 in coordination with the C12 r6 remediation (PR #231) so r6 and r7 converge on `roleLCT` rather than diverging.
2. Treat M3/L1/L2/L4 as **one pseudocode-alignment cluster** (align §2.x with the SDK's `r6.py` settlement), not four independent edits.
3. Treat M2 and M1 as straightforward example/structure corrections that also close silent spec↔SDK divergences.

M5 (determinism scoping) is the only finding that touches normative *property* text rather than examples/pseudocode, and is the one most worth an explicit editorial decision.
