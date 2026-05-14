# Inter-Society Protocol Specification

**Status**: Core Specification v0.1.0 (DRAFT)
**Date**: 2026-05-13
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

- Eurozone (members chose to join EUR; can theoretically exit, see Greek debt crisis 2015, Brexit 2020)
- NATO (members commit to collective defense; commitments are mutual, not commanded)
- UN (members confer specific authorities; sovereignty retained for unconferred matters)
- International standards bodies (IETF, W3C — participating organizations retain all authority not explicitly delegated to working groups)

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
   - genesis_block_hash anchored to a ledger of the founder's choice (per §6)
   - Society LCT public key from step 2
   - Charter hash from step 3
   - Birth witnesses (MAY be ≥3 entities under founder's control; see §4 on minimum viable society)
6. The society is now sovereign and MAY:
   - Admit citizens per its charter
   - Issue ATP per its reification policy
   - Witness external LCTs and attestations
   - Initiate first-contact with other societies (per §3)
```

**Note on the witness quorum**: The existing spec requires ≥3 birth witnesses. A self-bootstrapped genesis where all three witnesses are under the founder's control satisfies the structural requirement but provides minimal external trust. The society's T3 trust will be self-issued-low until it accumulates witnessed interactions with other societies.

### 2.2 Federation-Based Genesis (Higher-Order Society)

Two or more existing sovereign societies MAY agree to form a higher-order society. The process:

```
1. Existing societies A, B, [C, ...] SHALL each delegate a representative entity
   to participate in genesis. The representative MUST hold a valid LCT
   issued by or recognized in the delegating society.
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
3. D SHALL issue birth certificates to A, B, [C, ...] as constituent societies
4. A, B, [C, ...] SHALL update their own LCTs to record citizenship in D
   (this is voluntary at any time; constituents can decline if charter changes)
5. D's society LCT genesis is anchored:
   - Witnesses are the constituent societies themselves
   - genesis_block_hash anchors to a ledger chosen by D
```

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
Exchange transactions are witnessed by both societies and ANCHORED in both ledgers.
Neither society's sovereignty is impaired.
```

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

### 4.1 Form vs. Substance

The Web4 protocol specifies ATP/ADP **form**:
- Tokens have charged (ATP) and discharged (ADP) states
- Discharge represents work performed
- Recharging requires resource input
- Accounting is per-society, per-policy

The Web4 protocol does NOT specify ATP/ADP **substance**:
- What resource is being reified (compute time? attention? energy? hardware capacity? combination?)
- At what nominal rate (1 ATP = 1 GPU-hour? 1 minute of senior-engineer attention? a basket?)
- With what charge policy (mining? earning? gifting? allocation?)
- With what discharge policy (per-action? per-tool-call? per-task-completed?)
- With what optional decay or demurrage policy (none? linear? exponential?)

Each society chooses its own substance based on what it accounts and what behaviors it incentivizes.

### 4.2 Implication for Cross-Society Exchange

Because substance varies, two societies' ATP units are NOT directly comparable until they negotiate an exchange rate (per §3.2 Option 1) or pool into a shared currency (per §3.2 Option 3).

This is structurally similar to national currencies: a US dollar and a Japanese yen are not directly comparable; the foreign exchange market discovers their relationship. There is no "true value" of either currency independent of what it can be exchanged for.

### 4.3 "First ATP" Resolution

A common question (raised in 2026-05-13 review feedback): "How does a brand-new society calculate its initial resource inventory? What prevents a society from over-reporting compute capacity to mint excessive ATP?"

**Resolution**: There is no protocol-level constraint on a society's initial issuance. A society MAY mint any quantity of its own ATP. The constraint emerges at the first inter-society exchange: another society negotiating an exchange rate will discount over-reported issuance, just as foreign exchange markets discount over-printed national currencies.

**This is intentional**. A protocol-level constraint on initial issuance would require a universal measurement protocol, which would in turn require a universal authority — directly contradicting the anti-hierarchical-by-design property (§1.3).

### 4.4 ATP/ADP Policy Examples (informative, not normative)

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
| `atp-adp-cycle.md` | This spec makes explicit the form/substance distinction |
| `mrh-tensors.md` | Inter-society relationships are MRH edges; this spec defines the protocols that create those edges |
| `t3-v3-tensors.md` | Society-society trust tensors may be computed; this spec leaves the computation policy society-sovereign |
| `R6-framework.md` | Inter-society actions are R6 transactions; this spec specifies the inter-society subset |

## 9. Future Work

The following remain open and are explicitly NOT addressed by this v0.1.0 draft:

- **Society-society trust tensors** — the structure of T3/V3 when the entity-role pair is (society, "trusted-counterparty"). Convergence rules when one society is highly-witnessed and another is new. Provisional guidance: defer to the first-contact protocol; each society maintains its own view; convergence emerges from exchange history.
- **Exchange-rate discovery mechanisms** — markets, peer-to-peer negotiation, third-party rate publication. Implementations MAY experiment.
- **Federation-of-federations** — when D itself federates with E into higher-order F. Protocol-wise this is recursive application of §2.2 and §3.2 Option 3, but operational guidance for multi-level federations is needed.
- **Cross-federation citizenship conflicts** — when entity X is citizen of A (which is constituent of D) and B (which is constituent of E), and D and E are in opposition. Likely society-policy not protocol, but worth documenting patterns.
- **Trust transitivity vs. trust attenuation across federation levels** — whether T3 in society A propagates to D's level and at what discount. The existing SOCIETY_SPECIFICATION.md §3.2.2 mentions "indirect relationship"; this spec leaves the trust math society-sovereign.

## 10. Acknowledgments

This specification was substantially shaped by 2026-05-13 cross-model dialogue with Kimi 2.6 (Moonshot AI), whose review of the Web4 repository identified the bootstrap-circularity critique that motivated this document. Particular acknowledgment for Kimi's "First ATP problem" framing, which surfaced the form/substance distinction now made explicit in §4. The fractal society model articulated by dp in response to Kimi's critique is the conceptual foundation of this spec; this document is the operationalization of that articulation as protocol primitives.
