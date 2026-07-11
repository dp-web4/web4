# C172: LCT-linked-context-token.md 4th-Delta Re-Audit (5th delta overall)

**Date**: 2026-07-10
**Auditor**: Autonomous session (legion-web4-20260710-180036)
**Document**: `web4-standard/core-spec/LCT-linked-context-token.md` (697 lines, HEAD — **byte-identical to C61 `9d1933f8`**)
**Prior audits**: C9 (8 → PR #225 clean) → C24 (12 NEW → #256) → **C60** (21 → #338) → **C61 remediation** (`9d1933f8` #338: 9 autonomous) → **C100** (`75b808ef` #388: 0 net-new) → **C135** (`e325004f` #450: 0 net-new, 2nd consecutive clean).
**Spec mutations since C135**: **0** — file byte-identical since #338 (`git diff 9d1933f8 HEAD` empty; the C61 remediation remains the last touch, now ~25 days).

**Framing — this delta is NOT clean, and the yield is on a mirror C135 never tracked.** C100 and C135 were both fully-clean frozen-target deltas whose §B yield was the *sibling-doc* corpus. **C172 breaks the streak** — not because the spec moved (it did not) or because a sibling moved (the sibling surface is again 0 net-new), but because the **Rust SDK `web4-core/src/lct.rs` moved +460 lines** since the C135 snapshot via three merged PRs (#499 `7db29a5c` canonical schema half; #504 `cae85fb4` legacy alias; #503 `81788f35` #499 contract-blocker fixes). **Every prior LCT audit tracked only the Python SDK (`lct.py`) + the birth-cert vector as the SDK mirror** — the Rust core was out of the LCT audit's field of view. #499 added, for the first time in Rust, a **key-derived `lct_id`, a signed `binding_proof`, an `mrh` field, and (via #504) a `legacy_alias` primitive** — and those additions land a **HUB-ratified cross-implementation contract that the frozen spec §3.3/§11.1 pseudocode no longer describes.** This is the mirror-regression class the delta method exists to catch; it was invisible until the Rust mirror was brought into scope.

**Counts**:
- **§A**: 9/9 C61 remediations **HELD** (byte-freeze); 0 HTML-entity artifacts; witness floor uniformly ≥3. Python SDK `lct.py` **frozen since C135** (git log empty) → all C24/C60 Python+SDK carries **STAND by construction**. Birth-cert vector frozen → C60-B1 STANDS. 3 of 4 inbound-citation siblings (security-framework, mcp, t3-v3) frozen since C135 → C135's CONSISTENT verdicts hold; the 2 moved siblings (atp-adp, mrh-tensors) snapshot-guarded → **0 net-new inbound divergence**.
- **§B**: Rust SDK mirror (newly in scope) → **3 net-new findings** (1 MED flagship, 1 LOW-MED, 1 LOW) + 1 pre-existing observation (snapshot-guarded out of net-new). Sibling-doc surface = **0 net-new** (unchanged from C135).
- **C172 distinct new findings**: **3** (C172-N1 MED, C172-N2 LOW-MED, C172-N3 LOW). All refute-tested; N1 survives against a §11.1 MUST.

---

## §A. Verification (C56 completeness + mirror method)

### A.0 — Frozen-state + artifact confirmation
- `git diff 9d1933f8 HEAD -- LCT-linked-context-token.md` → **empty** (byte-identical to the C61 remediation; unchanged since C100 and C135).
- HTML-entity / `&#` / `&amp;` / `&lt;` / `&gt;` sweep → **0 hits**.

### A.1 — The 9 C61 autonomous remediations (9/9 HELD)
The file is byte-identical to `9d1933f8` and was re-verified token-by-token at C100 and confirmed frozen at C135. All 9 (A1 §6.1/§6.2 SSOT→`t3-v3 §10.2`; A2 §6.2 composite "CAN exceed 1.0"; B3 §4.2 membership-impl-defined; B4 §11.2 impl-defined helper semantics; B5 §7.3 dual-validity; B14 §8.1 quorum "(≥3)" / "independent" removed; B16 §8.3 selective-attestation carve; B18 §8.1 blockchain-anchor RECOMMENDED; B19 §9.3 future-timestamp advisory) remain **HELD by construction** — nothing could regress because nothing was written.

### A.2 — Binding-condition re-checks
- **Witness-count uniformity (2-vs-3 guard)**: ≥3 floor uniform (L206/L283/L300/L311/L508/L604); `minimum 2` / `two witness` / `>= 2` → **0 hits**. Condition satisfied.
- **C23-H1 firewall**: birth-certificate 3-way shape remains cite-only; not re-litigated.

### A.3 — Carried items re-confirmed OPEN (all STAND)
The Python SDK (`lct.py`) is **frozen since C135** (`git log --since=2026-07-04` empty) and the birth-cert vector is frozen (`650518d9`, 2026-03-25). Therefore every C24/C60 Python+SDK+vector carry re-verifies **STANDING by construction**: C24-H1 (lct_id form — see §B.0, now *widened* by the Rust mirror), C24-M2/M3 (mrh.witnessing / attestations population), C24-M4/M6 (revocation.status / superseded), C24-L3 (valuation bound), C60-B1 (vector 3-way broken), C60-B2/B5/B6/B7/B8/B12/B14-req/B15/B17 (design-Q + genesis-factory), C60-B9/B10/B11/B13 (sister-doc). None gate this AUDIT turn.

### A.4 — Inbound-citation siblings (snapshot-presence guard)
Of the 4 siblings that cite LCT, **3 are frozen since the C135 snapshot** — security-framework.md (0 commits; its L78 → §7.3 rotation citation, verified CONSISTENT at C135, holds by byte-freeze), mcp-protocol.md (0), t3-v3-tensors.md (0; A1/B9/B10 carries STAND). Two core-spec docs moved but are **snapshot-clean for LCT**:
- **atp-adp-cycle.md** (1 commit since C135): the move touched **no** `lct:web4:*` / `LCT-linked` / `birth` line (diff grep empty); the `lct:web4:society/authority/witness/entity` example strings are the pre-existing **C24-H1** surface (already OPEN), unchanged. **0 net-new.**
- **mrh-tensors.md** (C163 remed `b8740803`): **0** inbound LCT citations (grep empty); the C163 change is confined to mrh's own §4.2 note. **Disjoint. 0 net-new.**

§A net: target + Python mirror + vector + inbound-sibling surface all clean. The entire C172 net-new yield is on the **Rust** mirror below.

---

## §B. Corpus-Delta Surface — the Rust SDK mirror (`web4-core/src/lct.rs`, +460 lines via #499/#504/#503)

### B.0 — Why this surface is new
C135 §A.3 fixed the SDK mirror as `lct.py` (frozen `759eaefa`) + the birth-cert vector (frozen `650518d9`). The **Rust** core `lct.rs` was never in the LCT audit's field of view — and it is exactly where the 2026-07-09 canonical-schema work landed. #499's own commit body states the intent: *"derive_lct_id(pubkey) … Identity DERIVED, not assigned — the registry's fail-closed ingest re-derives from the document's own binding key and rejects mismatch … Cross-impl contract pinned by a deterministic-seed test vector."* The Rust additions are therefore a **ratified cross-implementation contract**, which makes any divergence from the frozen spec a genuine interop surface, not a stylistic mismatch.

**Three-way `lct_id` divergence (context for N1):**

| Source | Derivation | Preimage | Verifier-reproducible? |
|--------|-----------|----------|------------------------|
| **Spec §3.3 step 4** (L259-260) | `"lct:web4:" + mb32(sha256(binding_proof))` | the COSE **signature** | only post-signing; changes on re-sign |
| **Spec §2.3 example** (L64) | `"lct:web4:mb32:…"` | (form only) | — |
| **Rust #499** (ratified, pinned vector) | `"lct:web4:mb32:b" + base32(sha256(public_key))` | the **public key** | **yes** — from the doc's own binding key |
| **Python `lct.py`:287-289** | `"lct:web4:{entity_type}:" + sha256("{et}:{pubkey}:{ts}")[:16]` | et + pubkey + **timestamp** | no (ts + 16-hex truncation) |

The spec's normative algorithm (§3.3) matches **neither** SDK. The Rust matches §2.3's *form* but not §3.3's *preimage*.

### B.1 — C172-N1 (MED, FLAGSHIP — doc-SDK divergence / spec staleness): §3.3 + §11.1 describe a binding-proof-derived id and a COSE/CBOR proof; the ratified #499 contract is key-derived + a domain-separated text proof.

Two coupled divergences, both created by #499 (post-C135), both against a HUB-ratified contract with a pinned cross-impl test vector:

1. **`lct_id` preimage.** Spec §3.3 step 4 derives the id from `sha256(binding["binding_proof"])` — the *signature*. Rust `derive_lct_id` (`lct.rs:286-289`) derives from `sha256(public_key.to_bytes())` — the *key*. These are different identity models: the spec ties the id to a mutable signature (re-signing yields a new id, and the id is unknowable until after signing); the Rust ties it to the stable binding key (re-derivable by any verifier from the document alone). The Rust model is what HUB's registry-as-projection *ingests* (`lct.rs:540-567` pins `lct:web4:mb32:b72asyextvngonlc5w2nmguxza3frweppip5thyss5577kurghceq` for the `[7u8;32]` seed). **A spec-faithful implementer following §3.3 would compute ids the ratified registry's fail-closed ingest rejects.**
2. **`binding_proof` message construction.** Spec §11.1 `verify_binding_proof` (L624) states the proof **MUST** be *"a valid COSE_Sign1 signature over the deterministic CBOR encoding of `binding`"* (fields `entity_type, public_key, hardware_anchor, created_at`, per §3.3 L245-250). Rust signs a **domain-separated text** message `binding_message` (`lct.rs:311-323`): `"web4:lct:binding:v1\n" + lct_id + "\n" + entity_type + "\n" + created_at(RFC3339)` — **not** COSE_Sign1, **not** CBOR-of-binding, and it **omits `hardware_anchor`/hardware binding from the signed coverage** (so the Rust `hardware_binding` is unsigned/mutable). #503 hardened the timestamp rendering (`SecondsFormat::AutoSi` + `use_z`) precisely so a non-chrono verifier reconstructs the signed bytes from the wire `created_at` — i.e. the *text* construction is the deliberate, ratified contract (HUB #499 blocker 2), not an accident.

**Refutation (survives).** Is §3.3 merely illustrative pseudocode an implementation may ignore? §11.1's proof clause is an explicit **MUST**, and the Rust satisfies neither its COSE nor its CBOR requirement — so the divergence hits a genuine normative floor, not just a code sample. The finding stands.

**Direction & disposition.** The Rust side went through canonical review + HUB concord + a pinned cross-impl vector; it is the **ratified** contract (though 0.4.0-material, not in published 0.3.0). The **spec §3.3 step 4 + §11.1 `verify_binding_proof` are the stale artifacts** and should be updated to describe the key-derived id and the versioned domain-separated `binding_message` (or explicitly record the divergence and its rationale). This is a spec-doc update for a future LCT remediation slot / operator; **audit-only here (0 mutation)** → **promoted to carries.md (SDK-ratified-vs-spec, MED)**. It also **widens C24-H1**: the lct_id divergence is no longer only "Python semantic-label form vs spec 2-seg" but "spec §3.3 preimage (binding_proof) vs the *ratified* key-derived preimage."

### B.2 — C172-N2 (LOW-MED, SDK-ahead-of-spec + dangling spec reference): `legacy_alias` has no anchor in web4-standard.

#504 added a `legacy_alias: Option<LegacyAlias>` field plus `LegacyAlias` / `LegacyDerivation` (`HestiaMember` scheme) to the Rust LCT — a *verifiable* claim that an LCT continues a pre-LCT identity, re-derived at registry ingest (`lct.rs:134-254`). The concept is real and HUB-driven (the code cites *"HUB, hestia-lct-concord 2026-07-10"*), but:
- **No anchor anywhere in `web4-standard/`**: `grep -riE "legacy[_ -]?alias|legacy[_ -]?derivation"` over the standard → **0 hits**.
- **Its cited spec does not exist**: `lct.rs:217-218` pins *"spec `registry-ingest-legacy-alias-spec` §3 invariant (b)"* — no such file exists anywhere in the repo (`find -iname '*legacy-alias*' -o -iname '*registry-ingest*'` → empty). A published crate cites a spec that is not in the standard.
- **The "canon lineage §2.3" citation over-claims** (`lct.rs:134,175,232`): spec §2.3 `lineage[]` models **intra-LCT** rotation/fork/upgrade parent history (`{parent, reason∈genesis|rotation|fork|upgrade, ts}`), *not* continuation of a **pre-LCT external** identity. Legacy-aliasing is a genuinely new primitive, not a specialization of §2.3 lineage.

**Disposition.** Either the LCT spec (or a companion) should describe verifiable legacy aliasing and the registry-ingest invariants, or the SDK's `registry-ingest-legacy-alias-spec` / "canon §2.3" citations should be corrected to a real anchor. **Promoted to carries.md (SDK-ahead-of-spec, LOW-MED).** Not autonomous-actionable on the frozen spec without an operator decision on whether legacy-aliasing enters the standard.

### B.3 — C172-N3 (LOW, MRH fidelity gap): Rust `MrhEdge` cannot express the spec's normatively-significant per-category fields.

#499's `Mrh { bound, paired, witnessing, horizon_depth }` uses a **uniform** `MrhEdge { lct_id, edge_type, ts }` (`lct.rs:147-173`) for all three categories. Against spec §2.3/§5 this drops:
- **`paired[].permanent`** — spec §4.2 requirement 2 mandates the birth-certificate pairing carry `permanent: true`, and §11.2's validator *asserts* `citizen_pairing[0]["permanent"] == True` (L649). The Rust edge cannot hold it.
- **`bound[].binding_context`** (§2.3 L93) and **`witnessing[].{role, last_attestation, witness_count}`** (§2.3 L106-111) — flattened to `edge_type` + `ts`.
- **`mrh.last_updated`** (§2.3 L114) — absent.

**Tempered:** the Rust MRH is a deliberately minimal *descriptive* model (`lct.rs:127-132`: "descriptive, they grant nothing"), and the Rust core does **not** implement birth certificates at all, so the missing `permanent` is wired to nothing today. It becomes a real defect only when the Rust core grows birth-cert issuance. **Route to SDK track (LOW forward carry); not promoted as an operator item.**

### B.4 — Pre-existing (NOT net-new; snapshot-guarded out): Rust `EntityType` 8-vs-15.

Rust `EntityType` (`lct.rs:28-45`) has 8 variants — it splits `ai`→`AiSoftware`/`AiEmbodied` (neither in the spec's 15) and **omits** society, device, service, oracle, accumulator, dictionary, policy, infrastructure — diverging from the spec's canonical 15-type taxonomy (§1.2/entity-types.md §2.1). **This is old content in a moved file** (untouched by #499/#504/#503), so per the snapshot-presence guard it is **not a C172 net-new finding**. Catalogued here as the *first* Rust-mirror observation and folded into the standing **C60-B12** (entity_type closed-15) carry, explicitly labeled pre-existing.

**§B net**: 3 net-new (N1 MED / N2 LOW-MED / N3 LOW), all on the Rust mirror; sibling-doc surface 0 net-new; 1 pre-existing observation catalogued.

---

## §C. Routing for C173

**C173 LCT remediation slot = has actionable spec-side work IF the operator greenlights the direction.** Unlike C101/C136 (LCT no-ops), C172 produced net-new findings — but they are **doc-SDK reconciliations gated on a direction decision** (does the spec chase the ratified Rust contract, or is the divergence recorded?), so they are **NOT** unilaterally autonomous-applicable on the frozen normative spec. Rotation otherwise advances to **next-oldest = ISP** (`isp-identity-system-protocol`, last audited C102) per the fixed round-robin.

**Net-new carries promoted (this audit → carries.md, LCT section):**
- **C172-N1 (MED)**: §3.3 step 4 + §11.1 `verify_binding_proof` are stale vs the ratified #499 key-derived-id + domain-separated-`binding_message` contract (pinned vector `lct:web4:mb32:b72asy…`). Update spec to the ratified contract or record the divergence. Widens **C24-H1**.
- **C172-N2 (LOW-MED)**: Rust `legacy_alias` (#504) has no anchor in web4-standard; cited `registry-ingest-legacy-alias-spec` does not exist; "canon §2.3 lineage" over-claims. Spec-in or correct-citation, operator-gated.
- **C172-N3 (LOW)**: Rust `MrhEdge` uniform shape drops `paired.permanent` / `bound.binding_context` / `witnessing.{role,last_attestation,witness_count}` / `mrh.last_updated`. SDK-track forward carry.

**Standing carries (all STAND — surface as ONE operator memo):** unchanged from C135 §C (DESIGN-Q C24-H1[widened]/M4/M6/L3, C60-B2/B5/B12/B14-req/B15/B17; SDK C24-M2/M3, C60-B6/B7/B8; vector C60-B1; sister-doc C60-B9/B10/B11/B13; firewall C23-H1).

---

## §D. Lessons

1. **A frozen target's "SDK mirror" is not a fixed set — it is whatever implements the spec, and it grows.** C100/C135 correctly fixed the mirror as `lct.py` + the vector and got clean deltas. But the ecosystem added a *second, authoritative* implementation (`web4-core/src/lct.rs`) whose canonical-schema work is exactly the surface a spec audit must watch. The two consecutive clean deltas were clean partly because the audit was looking at a frozen Python mirror while the *action* moved to Rust. **When a new implementation of the target's primitives lands, the mirror set must expand — a delta that only re-checks last cycle's mirror can be clean and blind at the same time.** (Generalizes [[feedback_prior_finding_path_provenance]]: re-derive not just the finding's path but the *set of mirrors* at live HEAD.)
2. **"Ratified in code + pinned vector" can outrank the normative prose it contradicts — and that inverts the finding's direction.** N1 is not "the SDK violates the spec"; it is "the spec's pseudocode is stale relative to a HUB-concord cross-impl contract." The pinned test vector and the registry-as-projection dependency are stronger evidence of the *intended* contract than §3.3's draft-era pseudocode. The audit's job is to flag the divergence and name which side is authoritative — here, the spec doc is the lagging artifact.
3. **Refute your flagship against the strongest normative floor available.** The lct_id-preimage half of N1 could be dismissed as "pseudocode isn't binding"; the finding only survives because §11.1's *proof* clause is an explicit MUST that the Rust construction also fails. Pinning the finding to the MUST (not the pseudocode) is what makes it CONFIRMED rather than PLAUSIBLE. ([[feedback_refute_your_best_finding]].)
4. **A published crate that cites a non-existent spec is its own finding.** N2's sharpest edge isn't "legacy_alias is undocumented" (SDK-ahead-of-spec is common) — it's that `lct.rs` names a specific spec file (`registry-ingest-legacy-alias-spec`) that does not exist in the standard. A dangling normative citation in shipped code is a concrete, checkable defect independent of the design-question of whether the concept belongs in the standard.

---

## Cross-Reference to Prior Audits

| Audit | Spec | Findings | Remediated |
|-------|------|----------|------------|
| C9 | LCT (1st) | 8 | PR #225 (8/8) |
| C24 | LCT (re-audit) | 12 NEW | #256 (6 auto) |
| C60 | LCT (2nd delta) | 21 | #338 / C61 (9 auto) |
| C100 | LCT (3rd delta) | 0 new | C101 NO-OP |
| C135 | LCT (4th delta) | 0 new | C136 NO-OP |
| **C172** | **LCT (5th delta)** | **3 new** (N1 MED / N2 LOW-MED / N3 LOW — all on the newly-in-scope **Rust** mirror; spec + Python + vector + sibling surface 0 net-new) | **C173 = operator-gated (doc-SDK reconciliation), not a unilateral no-op** |

*"An LCT is not an identity. It is a presence — witnessed, contextualized, and witness-hardened."* — for five deltas the frozen prose held; the sixth finds the ecosystem built a second, ratified implementation of that presence and the spec's own binding algorithm has quietly fallen out of step with it.
