# Inter-Society Protocol Specification

**Status**: Core Specification v0.1.2 (DRAFT)
**Date**: 2026-06-16
**Category**: Society & Federation
**Extends**: `SOCIETY_SPECIFICATION.md` (single-society semantics), `atp-adp-cycle.md` (ATP form)
**Companion to**: `LCT-linked-context-token.md`, `t3-v3-tensors.md`, `mrh-tensors.md`

## Abstract

The Inter-Society Protocol specifies the primitives required for sovereign Web4 societies to discover, contact, transact with, federate with, and exit from each other. It explicitly addresses three gaps in the existing core spec: society genesis (how a society first comes into being), first-contact negotiation (what happens when two previously-independent societies meet), and secession/dissolution (how a society leaves a federation).

This document establishes that **Web4 is anti-hierarchical by design**. There is no root certificate authority, no DNS root, no canonical top-level society. Trust emerges from the bottom up through peer witnessing and federation. Higher-order societies are *overlays*, not *owners* — they exist by the consent of their constituents and dissolve when that consent is withdrawn.

## 1. Introduction

### 1.1 Purpose

The existing `SOCIETY_SPECIFICATION.md` defines what constitutes a single Web4 society (law oracle, ledger, treasury, society LCT) and describes a hierarchical fractal pattern (parent-child citizenship inheritance). This document complements that specification by addressing:

- **How societies come into being** in the first place (the bootstrap problem)
- **How sovereign societies interact** without subordinating to a higher authority (the federation problem)
- **How societies separate** when continued federation is no longer beneficial (the secession problem)
- **What ATP reification sovereignty means** for inter-society economic exchange

### 1.2 Relationship to Existing Specs

This document **extends** but does not replace:
- `SOCIETY_SPECIFICATION.md` — single-society semantics remain authoritative; this spec adds inter-society protocols on top
- `atp-adp-cycle.md` — the ATP/ADP *form* (charge/discharge accounting) remains as specified; this spec makes explicit that *substance* (what is reified, at what rate, with what policy) is society-sovereign

Where this spec's federation model and the existing fractal-nature section appear to differ: the existing spec describes one valid pattern (hierarchical inheritance, like EU member states accepting some EU law). This spec describes additional valid patterns (peer federation with shared currency but retained sovereignty, like Eurozone within EU). Societies MAY choose either or both patterns; the Web4 protocol does not mandate hierarchical inheritance.

### 1.3 Anti-Hierarchical-by-Design as a Stated Property

This is a normative architectural property:

> **The Web4 protocol provides no mechanism for any society to assert authority over another society without that other society's consent.**

Higher-order societies exist by accumulated consent of constituents. They can mint, can witness, can mediate, but they cannot compel. A constituent society can always exit (per §5). This is structurally analogous to:

- NATO (members commit to collective defense; commitments are mutual, not commanded; withdrawal mechanism defined in Article 13)
- UN (members confer specific authorities; sovereignty retained for unconferred matters; withdrawal practiced historically)
- International standards bodies (IETF, W3C — participating organizations retain all authority not explicitly delegated to working groups; participation is at-will)
- Eurozone (members chose to join EUR; an exit right is generally held to exist but is untested and has no defined mechanism — the weakest of these analogies on the exit axis, listed last for that reason)

What Web4 is NOT structurally analogous to:
- DNS (single hierarchical root; ICANN holds final authority)
- Public Key Infrastructure (root CAs hold ultimate trust anchor)
- Blockchain mainnets with foundation governance

This property is a feature, not a limitation. It is the source of Web4's claim that "trust emerges from the bottom up."

## 2. Society Genesis

Two genesis protocols are specified. Both produce a sovereign society LCT with the requirements defined in `SOCIETY_SPECIFICATION.md` §1.2.

### 2.1 Self-Bootstrapped Genesis (Solo Founder)

A single entity MAY found a society. The process:

```
1. Founder entity SHALL hold a valid LCT (self-issued is sufficient at genesis)
2. Founder SHALL generate or select an Ed25519 keypair for the society itself
3. Founder SHALL publish a society charter (RDF graph) containing:
   - At least one foundational law (e.g., "all decisions by founder until governance amended")
   - Amendment mechanism
   - Citizenship admission criteria
   - ATP reification policy (what resources are accounted, in what units, with what charge/discharge rules)
4. Founder SHALL initialize the society treasury (initial ADP allocation, MAY be zero)
5. Founder SHALL mint the society LCT with:
   - genesis_block_hash anchored to a ledger of the founder's choice (per §7)
   - Society LCT public key from step 2
   - Charter hash from step 3
   - Birth witnesses — ≥3 required per `LCT-linked-context-token.md`; these MAY be entities under the founder's control (see §6 on minimum viable society)
6. The society is now sovereign and MAY:
   - Admit citizens per its charter
   - Issue ATP per its reification policy
   - Witness external LCTs and attestations
   - Initiate first-contact with other societies (per §3)
```

**Note on the witness quorum**: `LCT-linked-context-token.md` requires ≥3 birth witnesses. A self-bootstrapped genesis where all three witnesses are under the founder's control satisfies the structural requirement but provides minimal external trust. The society's T3 trust will be self-issued-low until it accumulates witnessed interactions with other societies.

**Note on the genesis record**: The charter (step 3), citizenship admission criteria (step 3), and birth witnesses (step 5) are governed authoritatively by `web4-society-authority-law.md` (SAL) — see SAL §2 for the genesis Citizen role and SAL §2.2 for the canonical Birth Certificate JSON-LD shape that records this genesis.

### 2.2 Federation-Based Genesis (Higher-Order Society)

Two or more existing sovereign societies MAY agree to form a higher-order society. The process:

```
1. Existing societies A, B, [C, ...] SHALL each delegate a representative entity
   to participate in genesis (the Diplomat role per `society-roles.md`).
   The representative MUST hold a valid LCT issued by or recognized in
   the delegating society.
2. The delegated representatives SHALL collectively:
   - Generate or select an Ed25519 keypair for the new society D
   - Negotiate and publish a charter (RDF graph) including:
     * Foundational laws (typically: scope of D's authority, decision rules)
     * Amendment mechanism (typically: requires constituent ratification)
     * Citizenship policy (typically: D's citizens are the constituent societies themselves,
       not individual entities; constituent societies retain authority over their own citizens)
     * ATP reification policy (D MAY define a shared currency; constituent societies
       MAY retain their own currencies and use D's only for inter-constituent exchange;
       see §4 on Eurozone-style federation)
     * Exit conditions (per §5)
3. D SHALL mint constituent-society LCTs for A, B, [C, ...] as constituent societies
4. A, B, [C, ...] MAY update their own LCTs to record citizenship in D
   (this is voluntary at any time; constituents can decline if charter changes)
5. D's society LCT genesis is anchored:
   - Witnesses are the constituent societies themselves
   - genesis_block_hash anchors to a ledger chosen by D
```

**Note on formation events**: D's minting of constituent-society LCTs (step 3) and the constituents' citizenship updates (step 4) are recorded as `incorporate_child` / `incorporated_by` formation events per `SOCIETY_SPECIFICATION.md` §4.2.1 (symmetric to the secession formation events §5.1 records via SAL §3.4).

**Critical property**: D is an *overlay*, not an *owner*. A, B, C retain all sovereignty not explicitly delegated to D. D cannot override A's internal law; it can only mediate matters A and B chose to delegate to D.

## 3. First-Contact Protocol

Two previously-independent societies MAY discover each other and choose to interact. Three sovereign options exist; the choice is by mutual agreement.

### 3.1 Discovery

Society discovery is out of scope for this protocol — societies MAY use any discovery mechanism (public registries, direct introduction, third-society referral). The protocol begins once two societies have established communication channels and exchanged society LCTs.

Both societies SHOULD independently verify the other's:
- Society LCT signature and binding
- Charter (RDF graph hash) and current laws
- T3/V3 trust attestations from any common witnesses
- ATP reification policy (what they account, at what nominal rates)

### 3.2 Three Sovereign Options

Following discovery, the two societies (A and B) negotiate which of three patterns governs their interaction:

#### Option 1: Retain + Exchange (most common, analogous to international trade)

```
A and B both retain their own ATP reification policies.
A and B negotiate an exchange rate (ATP_A : ATP_B) for value transfers.
The exchange rate MAY be:
  - Fixed (renegotiated periodically)
  - Market-derived (continuous price discovery via repeated exchanges)
  - Pegged (one anchors to the other's policy)
Exchange transactions SHALL be witnessed by both societies and anchored in both ledgers.
Neither society's sovereignty is impaired.
```

> **Note on rate substance**: the *substance* of any rate negotiated under this Option is referent-grounded per `mcp-protocol.md` §7.7.1 (Normative) — rates are grounded in a common referent both societies can independently value, not an abstract floating bilateral rate. The Fixed / Market-derived / Pegged enumeration above governs rate *stability over time*, not the basis of valuation.

#### Option 2: Adoption (one society uses the other's ATP, analogous to dollarization)

```
Society A SHALL declare A's ATP reification policy obsolete for new issuance.
A SHALL adopt B's ATP as A's currency.
A's existing ATP balance SHALL be redeemed or grandfathered per A's amendment process.
B's role expands (more entities recognize B's currency); A's role narrows
  (A no longer issues currency).
This is sovereign — A chose this and can reverse it by adopting another society's
  ATP or re-introducing its own.
```

#### Option 3: Federation with Shared Currency (Eurozone pattern)

```
A and B agree to form (or join) a higher-order society D per §2.2.
D's charter includes a shared ATP reification policy (D's currency).
A and B MAY:
  Retain their own currencies in parallel (uncommon but valid)
  Relinquish their own currencies in favor of D's (Eurozone-equivalent)
Inter-constituent value transfers within D use D's currency.
External transfers (D-constituent to non-D society) follow Options 1 or 2.
```

### 3.3 Negotiation Failure

If A and B cannot agree on any of the three options, they MAY:
- Defer (no protocol-level relationship established; either can re-initiate later)
- Establish a minimal observational relationship (mutual witnessing without economic exchange)
- Use a third society as mediator (if one exists with sufficient T3 trust from both)

No protocol-level mechanism forces a relationship.

## 4. ATP Reification Sovereignty

This section makes explicit a property of `atp-adp-cycle.md` that has been under-emphasized: **ATP is the form, not the substance**.

### 4.1 What ATP Is (and What It Is Not)

**ATP is a unit of account, not a medium of exchange with intrinsic value.** It is the standardized token form of a society's internal resource accounting — analogous to how a company might track "engineering hours" or "server capacity" using internal units of account that have no meaning outside the company unless explicitly converted.

The biological metaphor (ATP in cells) is apt precisely because ATP-in-cells is also not currency — it is a chemical carrier of energy potential, a unit-of-account for energy commitments. The analogy holds when ATP/ADP is read as resource accounting, and breaks when over-read as monetary economics.

This framing has important implications that resolve several common misreadings of the spec:

- **"Anti-hoarding" mechanisms are not solving macroeconomics.** They prevent a society from over-committing resources it doesn't have, or from letting resource allocations sit indefinitely unused. Demurrage in the Web4 context is "expiration of resource allocations," not a Gesellian economic experiment.
- **"Charging" (ADP → ATP) is recognizing resource contribution, not creating value.** A society moves ADP to ATP when it accounts for actual resource availability or pledged commitment. It is not minting wealth.
- **No mechanism-design proof is needed** for the ATP/ADP cycle as such, because it is accounting infrastructure rather than market design. Societies that wish to embed market mechanisms in their ATP policies (price discovery, auctions, etc.) MAY do so, but the protocol does not mandate or specify market dynamics.

### 4.2 Form vs. Substance

The Web4 protocol specifies ATP/ADP **form**:
- Tokens have charged (ATP) and discharged (ADP) states
- Discharge represents work performed or resource consumed
- Recharging requires resource input or commitment renewal
- Accounting is per-society, per-policy

The Web4 protocol does NOT specify ATP/ADP **substance**:
- What resource is being reified (compute time? attention? energy? hardware capacity? combination?)
- At what nominal rate (1 ATP = 1 GPU-hour? 1 minute of senior-engineer attention? a basket?)
- With what charge policy (mining? earning? gifting? allocation?)
- With what discharge policy (per-action? per-tool-call? per-task-completed?)
- With what optional decay or expiration policy (none? linear? exponential?)

Each society chooses its own substance based on what it accounts and what behaviors it incentivizes.

### 4.3 Commitment vs. Record

Two semantically distinct uses of ATP MAY coexist within a single society's accounting. The spec distinguishes them:

- **ATP-as-Commitment**: A society credits ATP to an entity as a forward-looking pledge — "this entity is authorized to consume up to N units of the reified resource." The ATP balance represents *future capacity*, not past contribution.
- **ATP-as-Record**: A society credits ATP to an entity as a backward-looking acknowledgment — "this entity contributed N units of the reified resource that the society can now allocate." The ATP balance represents *recognized past contribution*.

Most real ATP policies combine both: commitments are pledged forward, records track what's been delivered, and the difference between pledged and delivered is itself audit-relevant signal.

Societies SHOULD make explicit in their charter which uses are in force and how they are distinguished in the ledger. Implementations MAY use separate ATP type-tags (e.g., `atp:commit`, `atp:record`) within the same accounting framework. The protocol does not mandate the distinction but acknowledges that conflating commitment and record is a common source of accounting confusion.

### 4.4 Implication for Cross-Society Exchange

Because substance varies, two societies' ATP units are NOT directly comparable until they negotiate an exchange rate (per §3.2 Option 1) or pool into a shared currency (per §3.2 Option 3).

This is structurally similar to national currencies: a US dollar and a Japanese yen are not directly comparable; the foreign exchange market discovers their relationship. There is no "true value" of either currency independent of what it can be exchanged for.

### 4.5 "First ATP" Resolution

A common question (raised in 2026-05-13 review feedback): "How does a brand-new society calculate its initial resource inventory? What prevents a society from over-reporting compute capacity to issue excessive ATP?"

**Resolution**: There is no protocol-level constraint on a society's initial issuance. A society MAY mint any quantity of its own ADP and charge it to ATP under its own policy (minting creates tokens in the discharged ADP state; charging is the ADP→ATP transition — see `atp-adp-cycle.md` §2.1–§2.2). The constraint emerges at the first inter-society exchange: another society negotiating an exchange rate will discount over-reported issuance, just as foreign exchange markets discount over-printed national currencies.

**This is intentional**. A protocol-level constraint on initial issuance would require a universal measurement protocol, which would in turn require a universal authority — directly contradicting the anti-hierarchical-by-design property (§1.3).

### 4.6 Resource Measurement and Attestation

A society's ATP issuance is bound by its policy to measurements of the underlying reified resource. While the *substance* of the resource is society-sovereign, the *protocol of measurement* benefits from cross-platform consistency at the attestation layer so that exchange counterparties can evaluate measurement credibility independent of the society's self-report.

This spec establishes the following as RECOMMENDED practice:

1. **Resource measurement SHOULD be witnessed.** A society's own attestation of its compute capacity, attention budget, or other reified resource SHOULD be co-signed by independent witnesses (other entities within the society at minimum; ideally entities outside the society with no stake in the over-reporting). Self-attestation without witnessing is permitted but limits the credibility of the society's ATP at exchange time.
2. **Measurement frequency SHOULD match resource volatility.** Hardware capacity might be measured at genesis and on hardware change. Attention budget might be measured per-period (daily, hourly). The society's charter SHOULD specify measurement cadence.
3. **Dispute resolution mechanism SHOULD be defined.** When society B's witnesses disagree with society A's self-report (e.g., A claims 10,000 compute units, B's witnesses measure 8,000), the spec does NOT specify how the dispute resolves — this is per-pair-relationship policy negotiated at first contact (per §3). But the existence of a dispute resolution mechanism SHOULD be documented in the society's charter.
4. **Hardware attestation (TPM 2.0, FIDO2, Apple Secure Enclave, etc.) SHOULD be used where available** to anchor resource measurement to verifiable hardware presence. The `AttestationEnvelope` primitive (see `schemas/attestation-envelope-jsonld.schema.json` and the SDK's `web4/attestation.py`) provides one cross-platform interface; implementations are free to use others, but SHOULD document the chosen mechanism in their charter so cross-platform exchange counterparties can evaluate trust.

Note that none of these are protocol-level enforcement. They are RECOMMENDED practices that affect the credibility of a society's ATP at exchange time. A society that over-reports without witnessing will find its ATP discounted heavily by exchange counterparties — the market for the society's ATP is the audit mechanism, not the protocol.

### 4.7 ATP/ADP Policy Examples (informative, not normative)

To illustrate the breadth of valid substance choices:

| Society type | What's reified | Charge mechanism | Discharge mechanism | Decay |
|---|---|---|---|---|
| Compute coop | GPU-hours | Members contribute compute → ATP minted | Tool calls discharge ATP | None |
| Editorial collective | Senior-editor attention-hours | Allocated monthly per role | Manuscript reviews discharge | Linear decay (use-it-or-lose-it) |
| AI agent fleet | Token-budget for foundation model calls | Operator funds USD → ATP minted at market rate | Model calls discharge | None |
| Open-source contributor pool | Reviewer-time + merge authority | Earned by accepted PRs | Spent reviewing others' work | Quarterly decay |
| Mutual-aid society | Promised future labor | Pledged by members | Discharged when redeemed | Per society policy |

None of these are "the" Web4 ATP model; all are valid policies a society can choose. The Web4 standard provides the form for all of them.

## 5. Secession and Dissolution

A constituent society of a federation MAY exit the federation. A standalone society MAY dissolve. This section specifies the protocols.

### 5.1 Secession Protocol (constituent leaves a federation)

Society A is a constituent of federation D. A wishes to exit D.

```
1. A SHALL announce intent-to-secede to D, with reason recorded in A's ledger
   (the Immutable Record per `web4-society-authority-law.md` §3.4, where citizenship
   changes such as the membership update in step 4 are durably recorded)
2. A SHALL provide notice period per D's charter (default: 90 days if unspecified)
3. During the notice period:
   - A retains full federation rights (voting, currency use, etc.)
   - D MAY attempt mediation if the charter specifies it
   - Other constituents MAY attempt direct outreach
4. At end of notice period, A:
   - Settles outstanding ATP balances in D's currency (per D's settlement policy)
   - Withdraws delegation of any sovereignty A had ceded to D
   - Updates A's society LCT to remove citizenship in D
5. D updates its own LCT and ledger to reflect A's departure
6. Inter-society relationships between A and D's remaining constituents:
   - Revert to first-contact protocol (§3) — no longer mediated by D
   - May be renegotiated as Option 1 (Retain + Exchange) bilateral relationships
```

### 5.2 Federation Dissolution (D itself ceases)

D's charter SHOULD specify dissolution procedure. If unspecified, default:

```
1. Dissolution requires the same threshold as charter amendment (e.g., supermajority of constituents)
2. Upon ratified dissolution:
   - D's treasury SHALL be distributed to constituents per charter formula (default: pro-rata by contribution)
   - D's currency SHALL be redeemable per the distribution
   - D's ledger SHALL be archived but NOT destroyed (historical record preserved)
   - D's society LCT SHALL be marked dissolved (cryptographic key destroyed if charter allows; archived otherwise)
3. Constituents' LCTs update to remove D citizenship
4. Inter-society relationships among former constituents revert to bilateral
```

### 5.3 Asymmetric Dissolution

A constituent leaving (§5.1) and the federation dissolving (§5.2) are different events. A constituent may leave a thriving federation; a failing federation may dissolve while remaining constituents continue federating bilaterally. The protocol supports both.

## 6. Minimum Viable Society

The existing `SOCIETY_SPECIFICATION.md` §1.2 specifies the minimum structural requirements (law oracle, ledger, treasury, society LCT). This section adds the minimum *semantic* requirements.

### 6.1 The Structural-vs-Semantic Distinction

A single human with three keypairs can syntactically satisfy the ≥3 witness quorum for genesis. Whether this constitutes a *meaningful* society is a separate question.

**Structural requirements** (from SOCIETY_SPECIFICATION.md): Can the data structures be filled in? Can the protocol mechanics be executed?

**Semantic requirements** (this spec): Does the society have enough internal differentiation to meaningfully witness itself? Does its ATP reification reify something other than the founder's self-attestation?

### 6.2 Minimum Viable Semantic Society

A society is semantically viable when ALL of the following are true:

1. **Internal differentiation**: At least one role-pair exists where role A's authority is meaningfully different from role B's authority. (A founder + three identical worker keypairs does NOT differentiate; a founder + a witness role + an executor role does.)
2. **Witnessing capacity**: At least one role can attest to actions of another role with independent judgment (not just rubber-stamp). Witnessing by an identical-twin keypair does not satisfy this.
3. **Reified resource grounded externally**: ATP reifies something with an external referent (compute, attention, hardware, time) — not just internal self-attestation. A society whose ATP "represents the founder's promise" is a single-party IOU, not a society.

### 6.3 Implications

- A single human running an autonomous AI fleet across multiple roles can constitute a society (the AI roles can witness with independent judgment; the fleet uses real compute that is the ATP referent).
- A single human alone, with no other entities to witness, probably cannot constitute a society in the semantic sense — though they can satisfy the structural requirements as a "society-of-one" for bootstrap purposes (per §2.1).
- A pure AI-agent collective can constitute a society if the agents have differentiated roles and independent judgment in witnessing.

These are GUIDANCE, not protocol enforcement. The Web4 protocol does not adjudicate whether a society is "real enough." Other societies will form their own judgments via the first-contact protocol (§3): a society perceived as not-meaningful will discover this when its first-contact attempts get declined or its exchange rates discount heavily.

## 7. Ledger Anchoring (Cross-Reference)

Society genesis (§2) and inter-society exchanges (§3) reference `genesis_block_hash` and ledger anchoring. The Web4 protocol is ledger-agnostic — any ledger that satisfies the requirements in `SOCIETY_SPECIFICATION.md` §4 (Ledger Types and Requirements) is acceptable. Implementations MAY use:

- A society's own append-only signed log
- A shared federation ledger
- An external blockchain (any chain the society chooses)
- A traditional database with cryptographic chain integrity
- A combination

The choice is per-society policy. The Web4 protocol does not mandate any specific ledger technology.

## 8. Relationship to Other Specs

| Spec | Relationship |
|---|---|
| `LCT-linked-context-token.md` | This spec uses society LCTs as defined there |
| `SOCIETY_SPECIFICATION.md` | This spec extends with genesis, first-contact, secession |
| `web4-society-authority-law.md` (SAL) | Defines the genesis Citizen role and canonical Birth Certificate shape (SAL §2), the fractal Society Topology (SAL §3.1) and `web4:memberOf` edges (SAL §3.3, chained per §3.5), and the Immutable Record ledger service (SAL §3.4). This spec's §2 genesis and §5 secession lifecycle operate on those SAL-defined structures. |
| `atp-adp-cycle.md` | This spec makes explicit the form/substance distinction |
| `mrh-tensors.md` | Inter-society relationships are MRH edges; this spec defines the protocols that create those edges |
| `t3-v3-tensors.md` | Society-society trust tensors may be computed; this spec leaves the computation policy society-sovereign |
| `r6-framework.md` | R6 (Rules+Role+Request+Reference+Resource→Result) is the action grammar for routine, low-consequence inter-society transactions (e.g., read-only resource access) |
| `r7-framework.md` | R7 (R6 + Reputation back-propagation to T3/V3) is the action grammar for consequential inter-society actions where the outcome should feed inter-society trust evolution. Most inter-society actions are R7 because crossing sovereignty boundaries typically justifies the bookkeeping cost. R6 and R7 are both canonical; the choice is per-action or per-role based on consequence tier. |
| `mcp-protocol.md` | MCP is the inter-society action protocol per the canonical Web4 equation. This spec defines genesis/first-contact/secession; `mcp-protocol.md` §7.3–§7.6 specifies R6/R7 actions between societies via MCP. §7.7 (architecture Normative per §7.7.1/§7.7.4; wire format WIP) specifies referent-grounded exchange rate negotiation. |
| `society-roles.md` | Defines roles (including the Diplomat) that inter-society interactions require; conversely this spec's §6.2 semantic-viability criteria constrain how those roles must compose. The dependency runs both ways. |

## 9. Future Work

The following remain open and are explicitly NOT addressed by this draft:

- ~~**Cross-society R6/R7 action protocol**~~ — **RESOLVED — `mcp-protocol.md` §1.1, §7.3–§7.6 (2026-05-14 amendment)**: cross-society R6/R7 actions are realized via MCP per the canonical Web4 equation (`Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP`). See `mcp-protocol.md` §1.1 (MCP as inter-society interface), §7.3 (MCP Actions as R7 Transactions), §7.4 (Cross-Society LCT Envelope), §7.5 (Cross-Society Witnessing and R7 Reputation Propagation), and §7.6 (cross-society R7 failure modes). The "cross-society action protocol" was never a missing spec — it was already specified by MCP's position in the equation; the 2026-05-14 mcp-protocol.md amendment made the binding explicit.
- ~~**Society-society trust tensors**~~ — **RESOLVED — `mcp-protocol.md` §7.5 (2026-05-14 amendment)**: society-society trust tensors emerge as the accumulated R7-Reputation projection at the encompassing society's scope, per `mcp-protocol.md` §7.5. Each society maintains its own bilateral view; the encompassing-society projection (when one exists) provides the canonical reference. Specified there rather than as a separate trust-tensor doc.
- ~~**Exchange-rate discovery mechanisms**~~ — **RESOLVED — `mcp-protocol.md` §7.7 (architecture Normative per §7.7.1/§7.7.4; wire format WIP v0.1.0-draft, 2026-05-14)**: see `mcp-protocol.md` §7.7 for the referent-grounded negotiation protocol. Key architectural insight: rates are not abstract floating bilateral exchange rates; they are grounded in a common referent both societies can independently value (kilowatt-hours, GPU-time, attention-hours, etc.). Per-transaction scoping is ideal (each R6/R7 carries its own rate against its specific referent); standing-agreement and oracle-reference are practical fallbacks. The protocol specifies message format (form); negotiation strategy (substance) is society-sovereign. The §7.7 *architecture* (§7.7.1 referent-grounded premise, §7.7.4 form/substance boundary) is Normative; its *wire format* remains WIP pending fleet review.
- **Federation-of-federations** — when D itself federates with E into higher-order F. Protocol-wise this is recursive application of §2.2 and §3.2 Option 3, but operational guidance for multi-level federations is needed.
- **Cross-federation citizenship conflicts** — when entity X is citizen of A (which is constituent of D) and B (which is constituent of E), and D and E are in opposition. Likely society-policy not protocol, but worth documenting patterns.
- **Trust transitivity vs. trust attenuation across federation levels** — whether T3 in society A propagates to D's level and at what discount. The existing SOCIETY_SPECIFICATION.md §3.2.2 mentions "indirect relationship"; this spec leaves the trust math society-sovereign.

## 10. Acknowledgments

This specification was substantially shaped by 2026-05-13 cross-model dialogue with Kimi 2.6 (Moonshot AI), whose review of the Web4 repository identified the bootstrap-circularity critique that motivated this document. Particular acknowledgment for Kimi's "First ATP problem" framing, which surfaced the form/substance distinction now made explicit in §4. The fractal society model articulated by dp in response to Kimi's critique is the conceptual foundation of this spec; this document is the operationalization of that articulation as protocol primitives.
