# `multi-device-lct-binding.md` — Fifth Delta Re-Audit (C268)

**Audited file**: `web4-standard/core-spec/multi-device-lct-binding.md` (1126 lines, current `main`)
**Audit date**: 2026-07-24
**Audit series**: C-series, C268 (fifth delta re-audit). Chain: **C19** (first-pass, 2026-05-28, #246) → **C36** (first delta, 2026-06-07, #281) → **C80** / **C81** (second delta + remediation, 2026-06-21, #371/#372) → **C120** (third delta, 2026-06-30, #421) → **C152** (fourth delta, 2026-07-07, #478) → **C268** (this).
**Authorization basis**: `docs/SPRINT.md` Sprint 54 records the C-series as *"not formally defined in advance. Work was proposed and policy-reviewed per session under v2 protocol."* This audit was proposed and policy-reviewed before execution per that precedent (v2 protocol Steps 3–5; APPROVED with six binding conditions, all honored — see §E).
**Instrument**: proportioned single-auditor **refute-by-default** + git-snapshot verification, with in-line adversarial refutation of the flagship (five independent refutation attempts, §B.1). **Instrument change from C152**: C152 used a separate verification subagent; this fire ran the refutation in-line under a session directive restricting subagent use to the mandated policy review. Recorded for method comparability, not as an improvement.

**Window**: since C152 merge `ab44384d` (2026-07-07T16:04Z) → HEAD `8c3711c6`. This is a **two-cycle window** — multi-device was **skipped** in the previous rotation pass (C228 → C230 advanced straight to t3-v3 on an older precedent), making this the **longest delta window in this file's lineage** (17 days, ~64 commits of corpus motion).

**Result**:
- **§A** — target **byte-frozen since C81** (`a6cbde92`, blob `b979ea7d`); SDK `binding.py` (`857f8040`) and `binding-vectors.json` (`dc969641`) **also byte-frozen since C120**. 7/7 C81 fixes HELD by triple byte-identity. **9/9 carries re-adjudicated at live HEAD** — all STILL-OPEN, none closed, **two re-anchored** (line-shift) and **two contextually sharpened**.
- **§B** — **1 confirmed finding** (`C268-N1`, MEDIUM, **routed to author/operator — NOT auditor-applicable**) + 1 newly-derived live-HEAD consumer (`web4-core/src/ratchet.rs`, absent at C152) + 3 refuted candidates + 2 INFO.
- **0 spec mutation, 0 SDK mutation, 0 hub mutation. 1 new file (this document).**

---

## Executive Summary

1. **A frozen file can acquire a genuine finding when the corpus norm moves under it.** This is the mechanism behind this fire's single finding, and it is worth stating plainly because it is the *only* way a MEDIUM can honestly appear on a byte-frozen target. multi-device has not changed since C81. But on **2026-07-16** — nine days *after* the C152 snapshot — PR **#531** (`d89595e8`) canonized **LCT-core §1.2, "Inspectable Evidence, Not Prescribed Trust"** as a **normative, RFC-2119 principle with two MUSTs**. No prior multi-device audit could have found this: C152 predates it. It is not a re-derivation of any guarded item.

2. **§1.2 names this spec's own structure in its enumerated scope.** LCT-core `:26`ff lists what counts as evidence-not-verdict: *"a signed binding proof, a witness quorum, **a constellation's device assurance**, a T3/V3 tensor, a society's authority ratchet."* Three of those five are multi-device's constructs. This file is not adjacent to the new principle — it is squarely inside it.

3. **C268-N1 (the flagship): §2.2.4 / §3.6 render a protocol verdict of exclusion, which §1.2 clause 1 now forbids.** multi-device `:155` states as a hard constraint *"Cannot be sole anchor for recovery quorum"*, and `:795-801` enforces it by **raising `NoHardwareAnchorError`** — an all-software constellation can **never** recover, at any stakes, under any society's law, with **no escalation path**. LCT §1.2 clause 1 says an entity presenting only weak evidence *"MUST NOT be excluded by the protocol"* and is instead *"rightly weighed as riskier"*; clause 2 says a conforming surface *"MUST NOT encode a universal trust threshold."*

4. **The corpus already corrected exactly this shape in the downstream consumer — and left the upstream spec unaligned because it was frozen.** `web4-core/src/ratchet.rs` (#529, `7b048a78`, landed after C152) consumes multi-device's assurance model directly (`FactorClass::DevicePossession`/`HardwareToken` *"map onto the existing constellation `AssuranceLevel`"* `:60`; `SovereignStructureProof.verified_devices` = *"the constellation `AssuranceLevel` device count, recomputed"* `:170`). Its module doc states the corrected form: *"no universal gate here and no exclusion: an entity presenting one-device-reachability-as-proof is **not barred** — it is rightly weighed as **higher risk**"* (`:27-29`), and *"a `false` is 'below this evaluator's bar for these stakes' (higher risk), **not a protocol verdict of exclusion**"* (`:49-50`). Even its hardware requirement is **evaluator-held**, not protocol-held: `require_hardware_backed: bool` (`:87`) is a bar the evaluator sets, with `:144` *"risk, not exclusion. A low-assurance entity is not barred from asking."* The ratchet was corrected; the spec it builds on was not.

5. **The Python SDK is already on the correct side too — the spec is the sole outlier.** `binding.py:589-617` `can_recover()` returns `Tuple[bool, str]` — `(False, "Recovery requires at least one hardware-bound device")` is **inspectable evidence with a stated reason that a caller weighs**. The spec's `recover_identity()` **raises**. Of the three surfaces expressing this same rule (spec §3.6, SDK `can_recover`, Rust `ratchet.rs`), **only the spec renders a verdict.** This is the [[feedback_prose_is_not_ledger]]-adjacent direction *spec-stale, implementations-correct* (C172 direction), not SDK-lag.

6. **Half of the §2.2.4 constraint block is fine, and saying so is part of the finding.** `:154` *"Maximum trust ceiling for software-only: 0.4"* is **not** a §1.2 violation — §1.2 clause 2 explicitly endorses *"assurance levels ... recomputed from structure."* A computed ceiling **is** the evidence. Likewise `:153` *"Software anchors MUST be marked in T3 tensor"* is evidence-production and is exactly what §1.2 wants. The defect is narrow and surgical: it is the **exclusion**, not the **scoring**.

7. **Everything else in the two-cycle window is disjoint, and that is now recorded so C302 need not re-derive it.** All nine W4IP-era and ontology movers were adjudicated for-or-against this file's surface (§B.3). Nine of nine carries were re-read at live HEAD rather than passed through with a C152-era status — the specific failure this fire existed to prevent.

---

## §A — Delta Status of Prior Findings

### A.1 — C81 fixes (7/7 HELD, by triple byte-identity)

Target blob `b979ea7d` = C81 = C120 = C152 state (`git log a6cbde92..HEAD -- <target>` → **0 commits**). SDK `binding.py` blob `857f8040` and `binding-vectors.json` blob `dc969641`: **0 commits since C152** (and none since C120). All three sides of every C120/C152-verified claim are byte-identical ⇒ the 7 C81 remediations (3-arg `cross_witness`, 4-param `record_cross_witness`, `compute_device_trust` formula mirror, bare-string `cross_witnesses`, orphan-block removal, `recovery_revoked` scope note, `ceil(n/2)` quorum wording) **HELD with no re-derivation possible or needed**. Second consecutive triple-frozen wrap.

### A.2 — Carries (9/9 re-adjudicated at live HEAD; 9 STILL-OPEN, 0 closed)

Per the policy condition, **no carry is passed through on a C152-era status.** Each row states the anchor's live-HEAD movement and the resulting adjudication.

| Carry | Anchor | Anchor moved? | Live-HEAD adjudication (2026-07-24) |
|-------|--------|---------------|--------------------------------------|
| **N1** (flat 8-dim `t3_tensor`, §2.3/§4.1) | `t3-v3-tensors.md` 3-root mandate; `ontology/t3v3-ontology.ttl` | **t3-v3 moved** (`d89595e8`); **ttl did NOT** (0 commits) | **STILL-OPEN, RE-ANCHORED.** The 3-root mandate is intact but **shifted `:135` → `:137`** (#531 inserted 2 lines at `:16`). `t3v3-ontology.ttl` byte-frozen ⇒ 3 roots only. **New adjacency**: the inserted t3-v3 `:16` line ("tensors are **evidence, not verdicts** … the standard never prescribes a trust threshold") is the same principle as C268-N1, applied to the tensor multi-device flattens. DESIGN-Q (attach-strategy = t3-v3-side D2, per C121) — **idle, no self-decision.** |
| **N2** (no entity-role binding) | `t3-v3-tensors.md:14` role-context invariant | **moved** (`d89595e8`) | **STILL-OPEN, ANCHOR VERIFIED INTACT.** The #531 hunk is **purely additive at `:16`**; `:14` is byte-identical. Same DESIGN-Q site as N1. |
| **C36-N9** (Society MUSTs / birth-cert owner) | `SOCIETY_SPECIFICATION.md`, `web4-society-authority-law.md` | **both moved** (1 commit each) | **STILL-OPEN by DISJOINTNESS.** Movers are `87377c38` (W4IP Phase 2 — SOCIETY_SPEC §7.3 Correction & Enforcement) and `1354e4c2` (W4IP Phase 3 — Effector role into SAL). `grep -icE "device\|constellation\|enroll\|recovery_quorum"` on both diffs = **0**. Neither touches birth-cert ownership. Operator/cross-track. |
| **C36-N11** (entity-segmented LCT IDs) | `LCT-linked-context-token.md` | **moved** (`d89595e8`) | **STILL-OPEN.** The #531 hunk is the additive §1.2 insert + a §1.2→§1.3 renumber of *Terminology*; it introduces no ID-segmentation scheme. DESIGN-Q (carry-C33 B-H1). |
| **C19-M3** (3 exception classes absent from `errors.md`) | `errors.md` | **NOT moved** (0 commits) | **STILL-OPEN, HELD by byte-identity — and now COUPLED to C268-N1.** `grep -cE "InsufficientRecoveryQuorum\|NoHardwareAnchorError\|DeviceLimitExceeded"` on `errors.md` = **0** at live HEAD. Note the convergence: **`NoHardwareAnchorError` is simultaneously (a) one of C19-M3's three undocumented exception classes and (b) the exact construct C268-N1 identifies as verdict-shaped.** If N1 is resolved by removing/softening the raise, C19-M3's scope shrinks with it — the two should be adjudicated together, not independently. |
| **C19-M4** (LCT-core doesn't acknowledge §7.1 extension) | `LCT-linked-context-token.md` | **moved** (`d89595e8`) | **STILL-OPEN, CONTEXT SHARPENED.** LCT-core's **only** mention of this spec at live HEAD is the *new* §1.2 line `:41` — *"a multi-device, biometric, richly-witnessed constellation"* — cited as an **example inside the trust principle**, not as acknowledgment of the §7.1 protocol extension. So LCT-core's first-ever reference to multi-device arrived via the very commit that creates C268-N1. The M4 gap (extension acknowledgment) is **unchanged**; only the surrounding context moved. Cross-spec (LCT-recip). |
| **C19-M5** (8 sub-dims absent from ontology) | `ontology/t3v3-ontology.ttl` | **NOT moved** (0 commits) | **STILL-OPEN, HELD by byte-identity.** ⚠️ **Step-2 correction**: the pre-scope probe reported "ontology moved (4 commits)" — that is the *directory*. The four commits (`7201a765`, `767eb564`, `cb788768`, `4f76f110`) touch only `hub-law.ttl`, `role-extension.ttl`, `role-extension-schema.md`. The **C19-M5 anchor file is frozen.** Couples N1. |
| **C19-M7** (§7.3 ATP costs free-floating) | `atp-adp-cycle.md` | **NOT moved** | **STILL-OPEN, HELD.** atp-adp byte-frozen since C151 (`256ab51d`, blob `2d060579`) — independently re-confirmed by C266 two fires ago. §7.3 costs remain without a counterpart. |
| **B-10 arm** (adopted C152: `cose:ES256`→`cose:EdDSA` at `:257`/`:270`) | `security-framework.md`, `protocols/` | **NOT moved** (0 commits) | **STILL-OPEN — STATUS-CHECK ONLY** (policy condition 4). Both sites verbatim at live HEAD: `:257` `"binding_proof": "cose:ES256:..."`, `:270` `"sig": "cose:ES256:..."`. The B-10 owner ledger (security-framework/protocols) has **0 commits** since C152 ⇒ **no adjudication has occurred**; C152's sharpening (the prescription overreaches on this hardware-P-256 spec) stands unconsumed. **Not re-litigated here.** |

**Lean-on lens (both directions)**: outbound — multi-device's four citations (`:1111-1114`) are **file-level links with no section numbers**, so #531's LCT-core §1.2→§1.3 renumber **cannot** break them (candidate refuted, §C.3). Inbound — the only new corpus reference *to* multi-device is LCT-core `:41` (above) plus `ratchet.rs`'s consumption (§B.2).

### A.3 — C152's own two findings

| C152 finding | Live-HEAD status |
|---|---|
| **C152-1** (B-10 multi-device arm overreach + §2.4 genesis-signer gap) | **STILL-OPEN, unconsumed** — owner ledger unmoved (0 commits). Status-check only per condition 4. |
| **C152-2** (`hub/docs/PAIRED-CHANNELS.md` §8 item 6 frames specified architecture as open) | **STILL-OPEN.** Re-read at live HEAD: item 6 is **verbatim unchanged** (*"multi-device is later (and probably needs LCT split — separate sub-LCTs per device — which is its own architectural question)"*) despite 25 commits in `hub/`. Already routed to the hub track at C152 — **status-checked, not re-opened, not fixed** (policy condition 3). |

---

## §B — Findings

### B.1 — C268-N1 · §2.2.4 `:155` + §3.6 `:795-801` render a protocol verdict of exclusion, contra the newly-canonized LCT §1.2 clause 1 (MEDIUM · **route: author + operator DESIGN-Q** · NOT auditor-applicable)

**Statement.** multi-device `:155` states as a hard constraint *"Cannot be sole anchor for recovery quorum"*, enforced at `:795-801`:

```python
# 2. Verify at least one hardware-bound anchor
hardware_devices = [d for d in recovery_devices
                    if d.anchor_type != "software"]
if len(hardware_devices) == 0:
    raise NoHardwareAnchorError(
        "Recovery requires at least one hardware-bound device"
    )
```

An all-software constellation is therefore **permanently barred from identity recovery** — at any stakes, under any society's law, with **no escalation or override path anywhere in §3.6**. LCT-core §1.2 (`:26`ff, normative, RFC-2119, canonized `d89595e8` / #531, **2026-07-16**) states two MUSTs that this contradicts:

> 1. *"An entity that can present only weak evidence (e.g. single-device, reachability-as-proof) **MUST NOT be excluded by the protocol**. It is rightly weighed as riskier … Trust is a contextual preponderance of evidence scaled to stakes, not a boolean."*
> 2. *"A conforming surface produces verifiable evidence and **MUST NOT encode a universal trust threshold**: stating who or when to trust is the relying party's, not the standard's."*

**Why this is net-new and not manufactured.** The target has not changed since C81. The *norm* moved under it, 9 days after the C152 snapshot. No prior audit in this lineage (C19/C36/C80/C120/C152) could have raised it. It is not a re-derivation of B-10, the constellation naming collision, or C152-2.

**Corroboration — the corpus corrected this shape everywhere except here.** Both downstream expressions of the same rule are evidence-shaped:

| Surface | Shape | Verdict under §1.2 |
|---|---|---|
| `multi-device §3.6:799` | `raise NoHardwareAnchorError` | **verdict-shaped — the outlier** |
| `binding.py:589-617` `can_recover()` | `-> Tuple[bool, str]`; returns `(False, "Recovery requires at least one hardware-bound device")` | evidence-shaped ✅ |
| `web4-core/src/ratchet.rs` | `require_hardware_backed: bool` (`:87`) = a bar **the evaluator sets**; `:144` *"risk, not exclusion. A low-assurance entity is not barred from asking"*; `:49-50` *"not a protocol verdict of exclusion"* | evidence-shaped ✅ |

`ratchet.rs` is not an analogy — it **consumes this spec's assurance model by name** (`:60`, `:163`, `:168-172`). #529 corrected the ratchet's `satisfied_by` for precisely this defect (the #531 commit message: the ratchet was *"framed as 'the act gate — exercisable only when true,' smuggling a universal threshold + an exclude/admit verdict into a protocol surface"*). **The same smuggled verdict remains one layer upstream, in the spec the ratchet builds on.**

**Refutation attempts (5, all survived).**

| # | Refutation | Outcome |
|---|---|---|
| R1 | *"§3.6 is illustrative pseudocode, not normative — the MUST-vs-reference-impl defect class."* | **Survives.** The constraint is **also prose-normative** at `:155` in §2.2.4's *Constraints* block, independent of the pseudocode. Not a reference-impl artifact. |
| R2 | *"It's the §1.2 clause-2 carve-out — you can't prove evidence your structure doesn't support."* | **Survives.** Clause 2 bars *claiming* unsupported evidence. An all-software constellation claims nothing; it is **denied an act** for lacking hardware. Different construct. |
| R3 | *"It's the RWOA+S+V `V` clause — irreversible acts need a conservative veto."* (strongest) | **Survives, but this is the DESIGN-Q.** Recovery is genuinely irreversible/high-stakes, and V does sanction a veto. But V describes an *explicit veto/escalate path that can fire*; §3.6 has **no escalation route at all** — it is a blanket structural denial. CLAUDE.md holds both norms in the same block and resolves the collision in §1.2's favor: *"Failing an assurance bar is **higher risk, not exclusion**."* That said, **how V and §1.2 compose for irreversible acts is a genuine open question the operator should settle** — which is exactly why this routes rather than gets applied. |
| R4 | *"Already found / a guarded item."* | **Survives.** #531 postdates C152 by 9 days; zero overlap with B-10, constellation-naming, or C152-2. |
| R5 | *"The spec already softens it elsewhere."* | **Survives.** §2.2.4 uses recommendation language for role (*"Recommended Role: Bootstrap, low-trust contexts only"*) and `:289` shows the doc knows how to write implementation latitude (*"Implementations that do not require suspension semantics **MAY** treat…"*). The recovery constraint has **no** such latitude — the contrast is internal to the file. |

**Scope discipline — what is NOT wrong.** `:154` (*"Maximum trust ceiling for software-only: 0.4"*) and `:153` (*"Software anchors MUST be marked in T3 tensor"*) are **§1.2-conformant** and must not be swept in: clause 2 explicitly endorses assurance levels *"recomputed from structure."* A computed ceiling **is** evidence. The defect is the **exclusion**, not the **scoring**.

**Routing.** → **author + operator DESIGN-Q.** Not auditor-applicable: (a) the target is byte-frozen under a standing do-not-self-fix guard; (b) R3 exposes a real unsettled question about how the ratified V clause composes with §1.2 for irreversible acts; (c) resolving it plausibly requires an escalation-path design (who may override, on what witnessed authority) that is a **normative addition**, not an audit fix. **Adjudicate jointly with C19-M3** (`NoHardwareAnchorError` is undocumented in `errors.md`; if the raise goes, M3 shrinks). Candidate shapes for the author, not chosen here: (i) restate as a computed assurance input the relying party weighs; (ii) retain the bar but add an explicit society-law escalation/override; (iii) scope the constraint to a named profile rather than the protocol.

### B.2 — Live-HEAD consumer re-derivation (policy condition 5) — genuine-mirror gate

Re-derived from HEAD, **not** carried from C152's list. `grep -rniE "constellation|device_lct|multi_device|recovery_quorum|anchor_type" web4-core/src/ --include=*.rs` → 23 hits across 5 files, each classified:

| Consumer | Classification | Basis |
|---|---|---|
| `web4-core/src/ratchet.rs` (#529, `7b048a78`) | **GENUINE consumer — NEW since C152** | Consumes constellation `AssuranceLevel` by name (`:60`, `:163`, `:168-172`); recomputes device count from co-signatures. Did not exist at the C152 snapshot. This is the condition-5 case: a consumer present at HEAD and absent at C152. |
| `web4-core/src/sd_jwt_vc.rs`, `oid4vc.rs` | **FALSE mirror** | `multi_device` appears only as a **test-fixture claim value** (`sd_claim_salted("salt1", "assurance_level", json!("multi_device"))` `:465`, `:475`, `:555`). A selective-disclosure test string, not a constellation implementation. |
| `web4-core/src/role_extension.rs` | **FALSE mirror — vocabulary collision** | `role:constellation:mesh-worker`, `constellation_base ∧ role_overlay` = hestia's **law-folding** vocabulary (a fleet role-scope), not a device-LCT set. |
| `web4-core/src/vault/document.rs` | **FALSE mirror** | Single comment, *"constellation-MFA verifier kept private). Not yet impl'd."* — forward-note, no implementation. |

**Genuine-mirror gate verdict (§B′): GENUINE — and *expanded* since C152.** The mirror is no longer just `binding.py` + `binding-vectors.json` (both byte-frozen, both re-verified evidence-shaped). It now includes `ratchet.rs` as a **downstream consumer of the assurance model**. This expansion is what surfaced C268-N1's corroboration, and it is exactly the standing method guard's point: *the SDK mirror is not a fixed set — re-derive at live HEAD.* **Recorded for C302: `ratchet.rs` is now part of this file's mirror surface.**

### B.3 — Corpus-delta adjudication (goal 2: recorded disjointness, so C302 need not re-derive)

Every mover in the two-cycle window, adjudicated for-or-against this file's surface:

| Mover | Concept hits in diff | Adjudication |
|---|---|---|
| `d89595e8` #531 (LCT §1.2 + t3-v3 `:16`) | 5 | **SOURCE of C268-N1.** Also re-anchors N1/N2 and sharpens C19-M4. |
| `7201a765` (role-extension → `web4-standard/ontology/`) | 21 | **DISJOINT — vocabulary collision only** (see §D INFO-1). |
| `1354e4c2` #523 (W4IP Ph3, Effector role → entity-types/society-roles/SAL) | 0 | **DISJOINT.** No device/constellation content; C36-N9 anchor untouched. |
| `87377c38` #522 (W4IP Ph2, SOCIETY_SPEC §7.3 + hub-law-schema) | 0 | **DISJOINT.** |
| `767eb564` #521 (W4IP Ph0/Ph1, Coercive/Extractive category) | 0 | **DISJOINT.** |
| `cb788768` #525 (W4IP N3 code half, response vocabulary) | 1 | **DISJOINT** — incidental word, no constellation surface. |
| `4f76f110` (oracle consult/write sets on Scope) | 1 | **DISJOINT** — incidental. |
| `062fd24b` #526 (C195 remediation, reputation §5) | 0 | **DISJOINT.** |
| `2bc3bafb` #541 (C214 entity-types audit doc) | 2 | **INBOUND-CARRY LINK, not net-new** (see §D INFO-2). |
| `hub/` (25 commits) | — | **Status-checked only** (policy condition 3). C152-2 site verbatim unchanged; no hub mutation. |

---

## §C — Refuted candidates (3)

| # | Candidate | Why refuted |
|---|---|---|
| C.1 | `:154` *"Maximum trust ceiling for software-only: 0.4"* violates §1.2's no-universal-threshold MUST | **Refuted.** §1.2 clause 2 explicitly endorses assurance levels *"recomputed from structure."* A computed ceiling is evidence-production, not threshold-prescription. Keeping this out of N1 is what makes N1 surgical. |
| C.2 | The SDK/spec shape divergence (`can_recover()` returns a tuple; `recover_identity()` raises) is an independent spec↔SDK mismatch finding | **Refuted as a separate finding — folded into N1 as corroboration.** A pre-flight predicate naturally returns a bool and an act naturally raises; the shape difference is partly an artifact of function role. It is evidentially valuable (it shows which side is §1.2-aligned) but does not stand alone. |
| C.3 | #531's LCT-core §1.2→§1.3 *Terminology* renumber leaves stale section cross-references in multi-device | **Refuted.** multi-device's citations (`:1088`, `:1111-1114`) are **file-level markdown links with no section numbers**. The renumber cannot break them. (Whether it breaks *other* files' citations is LCT-core's ledger, not this file's — not pursued, out of scope.) |

---

## §D — INFO (no action)

- **INFO-1 — "constellation" vocabulary collision, second site, escalated locus. NOT re-opened as net-new.** C152 INFO-refuted this charge for `hub/constellation.rs` (hub-internal wire vocabulary vs spec structure; "constellation" is not a protected term). The **only new fact** is that `7201a765` promoted `role-extension.{md,ttl}` — carrying `role:constellation:interactive-dev`, `role:constellation:mesh-worker`, `constellation_base ∧ role_overlay` — **into `web4-standard/ontology/`**, moving the collision from hub-internal to **in-standard**. Per the guarded-item rule this is **recorded as a watch-item, not raised as a finding**: the C152 refutation (no protected term, no redefinition of Device Constellation) still holds. Flagged only so a future delta or a terminology pass can weigh whether in-standard co-residence warrants a disambiguating note.
- **INFO-2 — C176-N1's "Device absent" arm is this file's SDK-side consumer gap.** `2bc3bafb` (C214) narrowed C176-N1 to *"7 absent: **Device**, Service, Oracle, Accumulator, Dictionary, Policy, Infrastructure"* in the Rust `EntityType`. multi-device's per-device LCTs presuppose a Device entity type. **Already booked** on the C172/C174/C176 SDK-track bundle — **newly *linked* to this file's ledger, not re-raised.** Direction unchanged: SDK lags spec, spec CORRECT.

---

## §E — Policy conditions honored

| # | Condition | Disposition |
|---|---|---|
| 1 | Cite SPRINT.md Sprint 54 precedent, not its absence; don't edit SPRINT.md | ✅ Cited in the header; SPRINT.md untouched. (My Step-1 claim that no SPRINT.md exists was **wrong** — the reviewer caught it.) |
| 2 | An empty §B is a PASS; don't manufacture a face | ✅ §B is **not** empty, and §B.1's five-attempt refutation + §C's three refutals (incl. deliberately excluding `:154`) are the evidence that N1 was not manufactured to fill the window. |
| 3 | No hub mutation; status-check only | ✅ 0 hub bytes changed; C152-2 status-checked and left routed to the hub track. |
| 4 | B-10 status-check only | ✅ Sites re-verified verbatim; prescription **not** re-litigated. |
| 5 | Re-derive consumers from live HEAD | ✅ §B.2 — 23 hits classified from scratch; `ratchet.rs` surfaced as a NEW consumer absent at C152. |
| 6 | N1/N2 attach strategy, B-D1, D0 stay idle | ✅ Status recorded, no self-decision. |

**FAIL-criteria check**: 0 bytes changed in the target spec / Python SDK / `web4-core/` / `hub/`; no guarded item presented as net-new; the one MEDIUM is on a *corpus-norm* mechanism with its provenance dated and its refutations shown; §B′ re-derived not carried; **9/9 carries given live-HEAD adjudication**; 1 new file; no second rotation file touched.

---

## §F — Cross-audit signals

- **A frozen file is not a settled file when the corpus canonizes a new normative principle.** The C-series lesson to date has been *frozen ≠ clean* on the **inbound-carry** surface. C268 adds a sharper case: a **newly-canonized RFC-2119 principle retroactively re-scopes every frozen file it names.** #531 named "a constellation's device assurance" in its enumerated scope — that alone put a byte-frozen file back in play. **Method addition: on any delta, check whether a normative *principle* (not just a sibling spec) landed in the window, and re-read the target against it.**
- **When a norm changes, the implementations may be corrected before the spec — invert the usual suspicion.** The standard C-series prior is *SDK lags spec*. Here both implementations (`binding.py`, `ratchet.rs`) are on the correct side of §1.2 and the **spec is the outlier**, because #529 corrected the consumer and #531 canonized the principle while the upstream spec sat frozen. **A frozen spec is exactly the artifact most likely to be left behind by a norm correction** — freeze is what protects it from the sweep.
- **Two ratified norms can collide, and the auditor's job is to route the collision, not resolve it.** R3 (RWOA+S+V's `V` veto for irreversible acts vs §1.2's no-exclusion MUST) is a genuine unsettled composition question. Recording it as the reason for routing — rather than picking a side and applying a fix — is the correct disposition for a byte-frozen target under a do-not-self-fix guard.
- **Refuting half of your own finding is what makes the other half credible.** Excluding `:153`/`:154` from N1 (§C.1) cost nothing and is the difference between "§2.2.4 violates §1.2" (sweeping, wrong) and "the exclusion at `:155`/`:799` violates §1.2, the scoring does not" (surgical, right). [[feedback_refute_your_best_finding]].
- **A directory moving is not an anchor moving.** The Step-2 probe read "ontology: 4 commits" and provisionally marked C19-M5's anchor as moved; the anchor file `t3v3-ontology.ttl` had **0** commits. Corrected in §A.2. [[feedback_enumeration_and_grep_hypotheses]] — baseline the probe at the file, not the directory.

---

## Routing summary

| Item | Route |
|------|-------|
| **C268-N1** (§2.2.4 `:155` + §3.6 `:795-801` protocol-verdict exclusion vs LCT §1.2 clause 1) | **AUTHOR + OPERATOR DESIGN-Q** — adjudicate **jointly with C19-M3**; includes the unsettled `V`-vs-§1.2 composition question. **Do NOT self-apply.** |
| C19-M3 (`NoHardwareAnchorError` et al. absent from `errors.md`) | Coupled to N1 (scope shrinks if N1's raise is removed/softened) |
| C152-1 / B-10 arm | CROSS-TRACK → security/handshake ledger; **unconsumed, owner unmoved** (0 commits since C152) |
| C152-2 (`PAIRED-CHANNELS.md` §8 item 6) | CROSS-TRACK → hub track; **still verbatim-unchanged after 25 hub commits** |
| N1/N2, C36-N9, C36-N11, C19-M4, C19-M5, C19-M7 | STILL-OPEN, re-anchored at live HEAD; operator/cross-track/DESIGN-Q as before |
| INFO-1 (in-standard "constellation" collision), INFO-2 (Device `EntityType`) | Watch-item / existing SDK bundle — **not re-raised** |
| `ratchet.rs` as new mirror-surface member | Recorded for C302 |
| C269 remediation slot | **Expected NO-OP on this file** — zero autonomous-actionable findings; N1 is author/operator-gated. Rotation advances (**t3-v3 = C270**). |

Audit-only: **0 spec mutation, 0 SDK mutation, 0 hub mutation, 1 new file (this document).**

---

*"The file did not move; the ground under it did. A freeze protects a spec from churn — and from correction alike."*
