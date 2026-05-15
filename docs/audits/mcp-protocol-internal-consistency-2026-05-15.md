# mcp-protocol.md Internal-Consistency Audit

**Date**: 2026-05-15
**Auditor**: autonomous web4 session (legion, peer `*24`, Sprint 54 candidate C2)
**Subject**: `web4-standard/core-spec/mcp-protocol.md` (881 lines, 16 sections)
**Scope**: Internal consistency only — contradictions, undefined-term usage,
normative/informative-status conflicts, and broken seams **within this one
document**. This audit does NOT compare the spec to the Python SDK (that is
the separate C1 task) and does NOT patch the spec.

**Trigger**: PR #190 (`docs/audits/sprint-52-conformance-gap-consolidation-2026-05-15.md`,
merged `c09d0d21`) enumerated this as autonomous-pickable candidate C2 (memory
ref D4). The §7.7 WIP block (operator burst-4, 2026-05-14) was layered onto a
§7.4 normative block (operator burst-2) without a reconciliation pass; that
seam is the primary risk surface.

---

## Methodology

Full end-to-end read. Each candidate inconsistency is recorded with: location,
the two (or more) passages in tension, why it is an *internal* inconsistency
(not merely an omission), and a recommended resolution direction. Severity:

| Sev | Meaning |
|-----|---------|
| **HIGH** | A conformant implementation cannot satisfy the document as written, OR two normative passages specify structurally incompatible wire data. |
| **MEDIUM** | Normative guidance is self-contradicting or ambiguous enough that two good-faith implementations would diverge. |
| **LOW** | Maintainability / terminology / cross-document-coupling hazard; not a blocking contradiction today. |

**Headline**: The §7.4 (normative, burst-2) ↔ §7.7 (WIP, burst-4) seam carries
the four highest-severity findings (F2, F3, F4, F12). §7.4 contains a hard
`MUST` for an `exchange_rate` field whose *only* specification (§7.7) is both
(a) explicitly non-dependable and (b) structurally contradictory to §7.4's own
example schema. This is the load-bearing internal defect: an implementer
following stable normative text alone has no consistent way to populate a
required field.

---

## Findings Summary

| # | Location | Sev | One-line |
|---|----------|-----|----------|
| F1 | Overview vs §1.1, §7 intro | MED | Abstract frames MCP as inter-*entity*; §1.1/§7 declare inter-*society* the "load-bearing"/"primary" use — the document's own opening contradicts its stated primary purpose. |
| F2 | §7.4 ↔ §7.7 status | **HIGH** | §7.4 `MUST` carry a negotiated `exchange_rate`; the only spec of how to negotiate it (§7.7) is marked "SHOULD NOT depend on" until v0.1.0-final. The MUST has no stable normative path. |
| F3 | §7.4 example ↔ §7.7.1/§7.7.3 | **HIGH** | §7.4's `exchange_rate: {denominator, rate}` is exactly the single-scalar bilateral model §7.7.1 explicitly declares "is NOT the Web4 model"; §7.7.3 acceptance carries dual referent-grounded valuations instead. |
| F4 | §7.4 `atp_settlement` ↔ §7.7.1 | **HIGH** | §7.4's `atp_settlement` block has `currency`+`amount`+`exchange_rate` but **no referent slot**; the §7.7 referent-grounded model cannot be expressed in the normative envelope schema. |
| F5 | §7.6 ↔ §7.7.7 | MED | Overlapping failure conditions get different codes (`409 web4_cross_society_exchange_invalid` vs `409 web4_rate_standing_expired` / `408 web4_rate_negotiation_timeout`) with no stated precedence/refinement rule. |
| F6 | §7.3 ↔ §7.5 (`caller_society`) | MED | §7.3 treats `propagation_scope` as a single enum; §7.5 says `caller_society` is "typically combined with `both` semantics" — a combination the data model and `web4_propagation_scope_unsupported` error do not support. |
| F7 | §7.3 default ↔ §7.5 federation | MED | §7.3 flat default is `both` for all cross-society R7; §7.5 says `encompassing_society` is "standard for federation". No rule says federated interactions override the §7.3 default. |
| F8 | §4.1 ↔ §7.4 headers | **HIGH** | §7.4 introduces `sender_society`/`responding_society` and `agency_chain` (array) without stating their relationship to §4.1's `society` (single) and `proof_of_agency` (object) — unreconciled wire-field redefinition across two normative sections. |
| F9 | §7.3/§7.6/§7.7.2 "Policy-Entity" | LOW | Internally consistent spelling, but "Policy-Entity" diverges from the project's established `PolicyEntity`/`PolicyGate` terminology (CLAUDE.md SOIA-SAGE). Cross-doc terminology drift. |
| F10 | §7.4 ↔ §7.6 law-conflict | LOW | §7.6 recovery "escalate to encompassing society or refuse" presupposes an encompassing society; under §7.4 Caller-law with no encompassing D, "refuse" is the only option but isn't stated as such. |
| F11 | §7.3 ↔ §7.4 ↔ §7.7.3 signer | MED | Rate is Treasurer-signed (§7.7.3); reputation is Policy-Entity-signed (§7.3); the §7.4 `atp_settlement` envelope has **no stated signer**. Settlement-amount signing authority is unspecified at exactly the role-separation seam §7.7 deliberately creates. |
| F12 | §7.7 header ↔ §7.7.3–7.7.7 | **HIGH** | Section-level "SHOULD NOT depend on the wire format" coexists with RFC2119 SHOULD/MAY in §7.7.3, an error-code table in §7.7.7, and explicit "(informative)" tags on §7.7.5/§7.7.6 — which implies §7.7.3/§7.7.7 are normative. Conformance status of §7.7.3/§7.7.7 is undeterminable from the text. |
| F13 | §7.7.1 / §7.7.5 / §7.7.6 | LOW | Per-transaction/standing/oracle guidance is near-verbatim triplicated; future edits to one copy will silently diverge. |
| F14 | §1.1/§7.4/§7.5/§7.7 → inter-society-protocol.md | LOW | Specific section-number claims about another file (§3.1, §3.2 Option 3, §4, §9), incl. "§7.5 resolves §9's future-work item" — a status-coupling claim; verify in the C1/cross-doc pass. |
| F15 | §7.3 `outcome_class` enum | MED | `violation` is an enumerated R7 outcome but no section specifies how a `violation` outcome propagates (sign of T3/V3 deltas, signature path, ledger handling). The doc under-specifies its own enum. |
| F16 | §9.1 ↔ §9.2 | LOW | Two non-reconciled trust-discount models in adjacent subsections (§9.1 `1.0 - avg*0.2`; §9.2 flat `0.8`). Illustrative only, but a reader gets two cost models for one idea. |

5 HIGH · 5 MEDIUM · 6 LOW.

---

## Detailed Findings

### F1 — Abstract contradicts the document's own stated primary purpose (MED)

- **Overview, line 5**: "MCP serves as the inter-**entity** communication layer
  for Web4 … the nervous system through which Web4 entities interact."
- **§1.1, line 30**: "**MCP is the protocol by which sovereign Web4 societies
  engage each other**" — called a "load-bearing consequence."
- **§7 intro, line 291**: "Cross-society interactions are the *primary*
  expected use for the Web4 MCP extensions; intra-society … is a special case."

The Overview (pre-burst-2) never mentions the inter-society framing that §1.1
calls load-bearing and §7 calls primary. A reader who stops at the abstract
forms the wrong model of the spec's main purpose. **Resolution**: add one
sentence to the Overview pointing forward to §1.1's inter-society framing;
keep entity-level framing as the general case, society-level as the primary
expected case (consistent with §7 intro's own "special case" wording).

### F2 — A normative MUST depends on an explicitly non-dependable section (HIGH)

- **§7.4, line 437 (normative)**: "`atp_settlement.exchange_rate` **MUST** be
  present for cross-society calls with non-zero ATP cost when the two societies
  use different currencies; reference must be a current … negotiated rate from
  the inter-society protocol."
- **§7.7, line 478 (status)**: "WIP v0.1.0-draft … Implementations **SHOULD
  NOT depend on the wire format** until v0.1.0-final."

§7.7 is the only section that specifies how the negotiated rate is produced.
A conformant implementation is therefore required to carry a field whose only
production mechanism the spec tells it not to depend on. **Resolution**: either
(a) soften §7.4's MUST to a conditional MUST scoped to "once §7.7 reaches
v0.1.0-final," with an interim informative fallback, or (b) extract a minimal
*stable* rate-reference contract out of §7.7 into §7.4 and leave only the
negotiation *strategy* in the WIP block. Option (b) aligns with §7.7's own
form-vs-substance split (§7.7.4).

### F3 — §7.4 exchange_rate schema is the model §7.7.1 explicitly rejects (HIGH)

- **§7.4, line 421**: `"exchange_rate": { "denominator": "lct:web4:society:B:atp", "rate": 1.4 }`
  — a single scalar rate against a denominator currency.
- **§7.7.1, line 484**: "two societies maintain a floating bilateral rate
  `ATP_A : ATP_B` … **This is NOT the Web4 model.**"
- **§7.7.3, lines 587–596**: the acceptance payload carries
  `agreed_rate_caller_atp` **and** `agreed_rate_responder_atp` over a named
  `referent` — "the load-bearing property of referent-grounding."

The normative §7.4 example *is* the abstract-bilateral model the WIP section
declares is not Web4's model. The two representations of the same field are
structurally incompatible. **Resolution**: replace §7.4's `exchange_rate`
example with a referent-grounded shape (referent + dual valuations) consistent
with §7.7.3, or explicitly mark the §7.4 scalar form as a pre-§7.7 placeholder
slated for replacement. Cross-ref F4.

### F4 — §7.4 atp_settlement cannot carry the referent model (HIGH)

- **§7.4, lines 418–422**: `atp_settlement` = `{ currency, amount,
  exchange_rate }`. No slot for a referent or for the responder society's
  independent valuation.
- **§7.7.1, line 486**: "the negotiation seeks a **common referent** … then
  each settles in its own ATP at its own declared valuation of the referent."

The §7.7 settlement model (referent + two independent valuations) has no
expressible form in the normative §7.4 envelope. An implementer following §7.4
alone emits envelopes that cannot represent a §7.7 negotiation outcome.
**Resolution**: extend the §7.4 `atp_settlement` schema with an optional
`referent` + `responder_valuation` (or reference to the §7.7.3 acceptance
record) before §7.7 finalizes, so the normative envelope and the negotiation
output are shape-compatible. Cross-ref F3.

### F5 — Overlapping failure conditions, divergent codes, no precedence (MED)

- **§7.6, line 470**: "Exchange rate stale or absent → `409
  web4_cross_society_exchange_invalid`."
- **§7.7.7, lines 639–641**: `408 web4_rate_negotiation_timeout`, `409
  web4_rate_standing_expired`, `409 web4_rate_valuation_mismatch`.

A stale/expired rate is covered by both tables with different codes. The spec
states no relationship (refinement? supersession? both fire?). **Resolution**:
state that §7.7.7 codes refine §7.6's single code for the rate-negotiation
sub-domain, with §7.6 as the fallback when §7.7 is not in force.

### F6 — `caller_society` "combined with both" is unrepresentable (MED)

- **§7.3, line 386**: `propagation_scope: "caller_society |
  responding_society | both | encompassing_society"` (single enum value).
- **§7.5, line 455**: `caller_society` — "Unusual; **typically combined with
  `both` semantics**."
- **§7.6, line 474**: `web4_propagation_scope_unsupported` — implies one
  requested scope.

There is no described mechanism for combining `caller_society` with `both`;
the enum is single-valued and the error model assumes a single scope.
**Resolution**: either make `propagation_scope` a set/array (and update §7.6),
or delete the "combined with both" prose and describe `caller_society` as the
standalone scope it is.

### F7 — Federation default conflicts with the §7.3 flat default (MED)

- **§7.3, line 397**: default SHOULD be `both` for cross-society R7.
- **§7.5, line 457**: `encompassing_society` is "Standard for cross-society R7
  within a federation."
- **§7.4, line 415**: `interaction_type: first_contact | established | federated`.

For a `federated` interaction, §7.5 says `encompassing_society` is standard but
§7.3's default is `both` regardless of `interaction_type`. **Resolution**: make
the §7.3 default `interaction_type`-aware (`federated` → `encompassing_society`,
else `both`), or downgrade §7.5's "standard" to "recommended, overriding the
§7.3 default when `interaction_type=federated`."

### F8 — §7.4 redefines §4.1 header fields without reconciliation (HIGH)

- **§4.1, lines 129–141**: `society` (single), `sender_role:
  "web4:DataAnalyst"`, `proof_of_agency` (object: `{grant_id, scope}`).
- **§7.4, lines 409–426**: `sender_society` + `responding_society`,
  `sender_role: "web4:role:..."`, `agency_chain` (array, "per existing §4.1
  proof_of_agency").

§7.4 introduces `sender_society` without stating whether it renames, extends,
or supersedes §4.1's `society`. `agency_chain` (array) is parenthetically
equated to `proof_of_agency` (object) despite the shape change. This is a
wire-interop hazard across two normative sections. **Resolution**: add a
sentence to §7.4 stating that cross-society envelopes extend §4.1 — `society`
becomes `sender_society` (deprecate/alias), and `agency_chain` is the ordered
list form of `proof_of_agency` (define the element type explicitly).

### F9 — "Policy-Entity" diverges from project terminology (LOW)

`Policy-Entity` (§7.3 line 394, §7.6 line 473, §7.7.2 line 512) is internally
consistent but differs from the established `PolicyEntity` / `PolicyGate`
(CLAUDE.md SOIA-SAGE). Not an internal contradiction; flagged so the
terminology-protection pass can normalize spelling cross-document.

### F10 — Law-conflict recovery under-specifies the no-encompassing case (LOW)

§7.6 line 471 recovery "Escalate to encompassing society or refuse"
presupposes an encompassing society. Under §7.4 Caller-law with no encompassing
D, "refuse" is the only path but §7.6 lists it as a co-equal alternative.
**Resolution**: split the recovery by whether an encompassing society exists.

### F11 — Settlement-amount signing authority unspecified at the role seam (MED)

§7.7.2 (line 506) makes the **Treasurer** the rate authority; §7.7.3 acceptance
is `accepting_treasurer`-signed. §7.3 (line 394) makes the **Policy-Entity**
the `reputation` signer. The §7.4 `atp_settlement` block (the field that
carries the agreed amount into the action envelope) has **no stated signer**.
§7.7 deliberately separates rate authority into the Treasurer, so "which
signature authorizes the settlement amount in the §7.4 envelope" is a real,
unanswered seam. **Resolution**: state in §7.4 that `atp_settlement` MUST carry
(or reference) the Treasurer-signed §7.7.3 acceptance, distinct from the
Policy-Entity reputation signature.

### F12 — Normative status of §7.7.3/§7.7.7 is undeterminable (HIGH)

§7.7 header (line 478): "SHOULD NOT depend on the wire format." Yet §7.7.3
(line 531) uses RFC2119 "SHOULD"/"MAY", §7.7.7 is a full error-code table, and
§7.7.5/§7.7.6 are explicitly tagged "(informative)" — which by contrast
implies §7.7.3/§7.7.7 are normative. A reader cannot determine whether
§7.7.3/§7.7.7 keywords are normative-now, normative-on-finalization, or
informative. **Resolution**: add a per-subsection status line, or a §7.7
preamble table classifying each subsection (settled-architecture vs
draft-wire vs informative), so RFC2119 keywords have an unambiguous force.

### F13 — Triplicated per-transaction/standing/oracle guidance (LOW)

§7.7.1 (498–502), §7.7.5 (610–624), §7.7.6 (626–630) restate the same
guidance. Not yet contradictory; a divergence hazard on future edits.
**Resolution**: keep the normative statement in one place (§7.7.1), make
§7.7.5/§7.7.6 reference it rather than restate it.

### F14 — Cross-document status-coupling claims (LOW)

§7.5 line 463: "This **resolves** the `inter-society-protocol.md` §9
future-work item." Plus §3.1/§3.2-Option-3/§4 section-number claims. Out of
scope to verify in an internal audit; flagged for the C1/cross-doc pass —
if inter-society-protocol.md §9 still lists the item as future work, the two
documents are inconsistent.

### F15 — `violation` outcome class has no specified propagation path (MED)

§7.3 line 378 enumerates `outcome_class: success | partial | failure |
violation`. No section specifies how `violation` propagates: sign of the
`trust_dimension_updates` deltas, whether the Policy-Entity still signs, ledger
treatment vs a transport `failure`. §7.6 covers protocol/transport failures,
not a completed-but-violating outcome. **Resolution**: add a sentence to §7.3
specifying `violation` handling (negative-bounded deltas, still
Policy-Entity-signed, persisted by the Archivist like any R7 outcome).

### F16 — Two trust-discount models in adjacent subsections (LOW)

§9.1 line 691 `trust_modifier = 1.0 - (t3.average() * 0.2)` (range 0.8–1.0)
vs §9.2 line 712 flat `high_trust_discount: 0.8`. Both illustrative, but a
reader gets two cost models for one concept. **Resolution**: note that §9.1 is
the canonical formula and §9.2 modifiers are illustrative society-config
examples, or reconcile the numbers.

---

## Recommended Sequencing (for a future operator/lead patch pass)

This audit recommends; it does not patch. Suggested order:

1. **F2 + F3 + F4 + F11 together** — the §7.4↔§7.7 settlement seam. These four
   are one coherent defect cluster (a normative envelope that cannot represent,
   and a MUST that cannot stably reference, the negotiation model that
   supersedes it). Fixing them piecemeal will re-introduce inconsistency.
2. **F12** — resolve §7.7 subsection status before anyone implements against
   §7.7.3/§7.7.7; cheap, unblocks conformance reasoning.
3. **F8** — §4.1↔§7.4 header reconciliation; wire-interop, independent of the
   settlement cluster.
4. **F1, F5, F6, F7, F15** — localized normative clarifications.
5. **F9, F10, F13, F14, F16** — terminology / maintainability / cross-doc;
   batch with the next general spec-hygiene pass.

## Out of Scope (handed off, not closed here)

- SDK-vs-spec conformance of any §7 behavior → candidate **C1**.
- §7.7 promotion to v0.1.0-normative → candidate **C3** (F2/F12 are inputs to
  it but the promotion decision is operator-blocked).
- Cross-document verification of the F14 inter-society-protocol.md §3/§4/§9
  claims → cross-doc pass.

---

*Internal-consistency audit only. No spec text was modified. No SDK or test
code touched. One new file.*
