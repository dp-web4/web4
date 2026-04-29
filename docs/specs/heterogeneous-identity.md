# Heterogeneous Identity: Multi-Factor Witnessing as a Constellation

**Status**: Design note. Reference implementation in active development across the dp-web4 fleet (`private-context/tools/web4_fleet_bootstrap.py` for bootstrap and signed peer-witness scan; `claude-code/plugins/web4-governance/` v1.1.0 for session→host LCT witnessing). Public interfaces will follow the patterns described here.

**Date**: 2026-04-29

**Audience**: anyone designing identity systems for distributed agents, anyone reading about Web4's LCTs and asking "what stops a hardware vendor from gating access?"

---

## TL;DR

A Web4 entity does not have *an* LCT. It has a **constellation** of LCTs: a set of mutually-witnessing identity factors, each with its own native mechanism (hardware key, host-level token, session token, peer attestation, ledger anchor). The constellation's resilience grows with its size: the bigger and more diverse, the harder it is to gate, compromise, or impersonate.

No single factor is necessary. No single factor is sufficient. Trust is a function of *cross-factor convergence*, not any one credential.

This is the answer to "what stops a hardware vendor from gating LCT access?" — you don't depend on one LCT.

---

## Why this matters

The naive reading of LCT — "non-transferable presence token bound to hardware via Ed25519" — invites a single-point question: *whose hardware? whose attestation root?* If a vendor (Apple, Google, a TPM-chip manufacturer, a cloud KMS) is the sole anchor, that vendor becomes a gatekeeper. They can revoke. They can change terms. They can turn off the whole constellation.

The same critique applies to any single-source identity: a sole government-issued credential, a single account on one platform, one biometric template. Single-source identity is a trap regardless of its technical sophistication.

The Web4 answer isn't to find a "better" single source. It's to abandon the single-source frame entirely. **Identity is a graph of mutually-witnessing factors, not a credential.**

---

## The constellation

Every entity participating in Web4 may carry several identity factors simultaneously. These are not redundant — they're orthogonal, each anchoring a different aspect of presence:

| Factor | What it asserts | Native mechanism |
|---|---|---|
| **Host LCT** | "This host machine exists, with this Ed25519 keypair" | `~/.web4/{hostname}/lct.json` + signed observations |
| **Hardware-bound key** | "This keypair lives in a TPM/Secure Enclave/TrustZone slot" | TPM2 attestation, FIDO2 attestation, Secure Enclave SEP attestation |
| **Session token** | "This session, on this host, with this binding" | Per-session ephemeral token (e.g. web4-governance plugin's `web4:session:...`) |
| **Software-hash identity** | "This binary running on this user account" | Hash of (machine, user, timestamp) — Hardbound flat token |
| **Peer attestation** | "I observed this host's identity at time T" | Signed peer-witness records |
| **Ledger anchor** | "This identity claim is anchored at block N" | LocalLedger entries; future ACT chain transactions |

Each is its own RDF entity in the trust graph. They are linked by **witness edges** — each factor records observations of the others through *its* native mechanism. The resulting graph is the entity's identity.

A bootstrapped Web4 host today (per the reference implementation) carries at least: a host LCT, an OS-level keypair, a hardware-binding storage record (TPM2 / TrustZone / software fallback), a software-hash identity, a session-token system, and an append-only witness log. That's six factors right out of the gate, before peer attestations have happened.

---

## Witnessing, not vouching

Two distinctions are load-bearing:

**Witness ≠ vouch.** A witness statement says: *"I observed entity X at time T, with these observable properties."* It does not say: *"I endorse X."* No transitive trust is implied. No reputation is staked. The witness is testifying to having seen something — nothing more.

**Signature ≠ vouch.** When a witness signs a record, the signature guarantees the *observation claim* is intact: the witness asserted these specific fields, verifiable against the witness's own published public key. The signature does not guarantee the *underlying observation*. Signing "I saw X" doesn't make X true; it makes the *claim that I saw X* tamper-evident.

Trust accumulates in the convergence between independent observations, not in any one observation's authority. If Alice signs "I saw Bob at fingerprint F" and Charlie independently signs "I saw Bob at fingerprint F," the convergence is meaningful regardless of how trustworthy Alice or Charlie is individually. If they disagree — Alice sees fingerprint F, Charlie sees fingerprint G for the same Bob — that's not a contradiction to be resolved by majority vote; it's a **diagnostic signal** about which mechanism failed.

---

## Salience-aware fingerprinting

For convergence and divergence to be meaningful, fingerprints must hash over what's *salient* to the kind of entity, not over whatever the source happens to expose. Per-kind salience axes:

| Entity kind | Salience axis | What this catches | What this silences |
|---|---|---|---|
| Host LCT | LCT id + cryptographic key bytes | Identity rotation, key compromise | Routine session ticks, file mtime |
| Hardware-bound keypair | sha256(public_key_pem) | Cryptographic rotation | Host fingerprint reuse across keys |
| Storage slot set | sha256(sorted entry names) | Adding/removing slots | Touching a slot |
| Session-token system | sha256(sorted top-level schema keys) | Schema rotation, auth-shape change | Routine session creation |

If a fingerprint changes, that change is recorded as a **divergence event** with both the new and previous fingerprint, in append-only form. Routine state changes (counters, timestamps, log appends) do not contribute to the fingerprint and so do not generate noise. The federated witness log grows in proportion to *meaningful* identity events, not all activity.

---

## Salience-aware publication ("federate by salience")

Records that touch external graph edges (the entity being witnessed differs from the source itself) are mirrored to the federated artifact (in the reference implementation: `private-context/fleet-identity/{machine}/`). Records purely about the source itself stay strictly local. This rule is straightforward to encode and applies to any record-writer in the system.

The federated artifact then grows in proportion to cross-entity activity — which is exactly the activity that matters to relying parties traversing the graph.

---

## Access modes: making the trust tier explicit

Witnessing happens at different tiers, and they are not interchangeable. Every witness record carries an explicit `access_mode` field documenting how the observation was obtained:

| `access_mode` | Trust tier | Mechanism | Tampering surface |
|---|---|---|---|
| `local_cache` | Lowest | Local read of cached state | Local filesystem, requires re-verification to upgrade |
| `federated_artifact` | Medium | Read peer's record from a shared/committed artifact | Whoever maintains the shared artifact |
| `direct_query` | High | Live query to peer's running daemon | Network in flight (mitigated by signature) |
| `chain_attestation` | Highest | Anchored in a consensus ledger (future: ACT chain) | Consensus break (orders of magnitude harder) |

A relying party reading a witness record can decide for itself how much weight to assign based on `access_mode`. A coordination decision that needs only "does this peer exist with a known LCT" is fine on `federated_artifact`. A decision that needs "this peer authoritatively approves this transaction right now" must demand `direct_query` or `chain_attestation`.

This is the honest framing: the same witness record is appropriate in different contexts at different trust weights, and the schema makes that explicit instead of mistaking signature for truth.

---

## Vendor gating, dissolved

Return to the original question: *what stops a hardware vendor from gating access to LCT?*

If LCT were singular, the answer would be "nothing — they hold the root, they hold you." But LCT isn't singular. The LCT is *one factor* in a constellation. Vendor X gates their hardware key? Other factors continue: host LCT, software identity, peer attestations, session tokens, ledger anchors. Identity continuity persists through the surviving factors. The compromised factor is recorded as a divergence event; relying parties degrade trust accordingly; the entity keeps operating.

A determined adversary would have to gate *all* factors simultaneously. The cost of that scales with constellation size. Five factors is hard. Twenty is harder. A factor running on hardware the adversary doesn't control (a separate vendor, a separate physical device, a self-hosted ledger anchor) breaks the gate entirely.

**The bigger and more diverse the constellation, the more resilient and trustworthy the identity.** That is the design objective. Not "find the best single root," but "make the constellation hard to enclose."

---

## ATP, witnessed

A common question, particularly from visitors learning Web4: *where does the first ATP come from?*

The answer follows the same shape: ATP is not granted by an authority. It is **reified from observation of available resources**. To bootstrap an entity, you measure what is already there — compute capacity, network presence, storage, connectivity, peer relationships — and that measurement, signed and witnessed, is the basis of the initial allocation. Existence is witnessed, and ATP follows from witnessed existence.

This is consistent with the rest of Web4: presence is reified, not assigned. Trust accumulates from observation, not declaration. ATP is the same primitive applied to resources.

---

## Reference implementation

The dp-web4 fleet implements Phase 1 + 1.5 + Phase A of the constellation as of 2026-04-29:

- **Phase 1** — each fleet host bootstraps a host LCT + Ed25519 keypair, anchored in a local hash-chained ledger. The public LCT data is committed to a federated artifact (`private-context/fleet-identity/{hostname}/lct.json`). 5 of 6 fleet machines are bootstrapped; the sixth follows the same recipe.
- **Phase 1.5** — each host scans its own filesystem for sibling identity systems (TPM2/TrustZone storage, hardbound flat tokens, hardbound keypair records, session-token system) and records signed observations. Drift detection: salience-aware fingerprints flag real identity changes and silence routine ticks.
- **Phase A** — each host periodically scans peer hosts' committed LCTs and records signed peer-witness observations, each carrying `access_mode: federated_artifact` and `source: fleet-identity/{peer}/lct.json@<commit_sha>`. Verification is by graph traversal: read the witness's `signer_lct_id`, look up that signer's public key from the signer's committed LCT, verify with Ed25519.

The reference tooling lives at `private-context/tools/web4_fleet_bootstrap.py` (private fleet repo) and `claude-code/plugins/web4-governance/` v1.1.0 (publicly forked). A fleet-internal `feedback_heterogeneous_identity_witnessing.md` memory captures the design principles for cross-machine consumption.

Future work:
- **Phase A.2**: direct peer query (higher trust tier, requires a peer-listen protocol)
- **Phase B**: R6/R7 fleet coordination over peer-witness graph (formal request/response with required-tier annotations)
- **Phase C**: anchor witness records to ACT chain (highest trust tier, immutable + consensus)
- **Public reference implementation** in this repo, factored from the fleet tooling, when the design stabilizes

---

## Open questions

- **Constellation size lower bound**: is there a minimum number of independent factors below which identity is insufficiently resilient? The current Phase-1 bootstrap produces six factors per host; smaller deployments may want guidance.
- **Divergence resolution**: when independent witnesses disagree, what's the right relying-party behavior? Current implementation flags divergence as diagnostic but doesn't prescribe action — that's a coordination-layer decision (Phase B).
- **Cross-domain witnessing**: can identity factors from a non-Web4 system (e.g. an OAuth issuer, a national ID, a verifiable credential) be incorporated as constellation members? The `access_mode` field is designed to admit this; the protocol for ingestion is not yet specified.
- **Constellation observability**: can a relying party meaningfully audit "how big and diverse is this entity's constellation" before transacting? This is the "what's my counterparty's identity surface" question, and it deserves a query primitive.

---

## Summary

Web4 identity is a constellation of mutually-witnessing factors, not a credential. Each factor uses its native mechanism. Each carries explicit metadata about the trust tier it represents. The graph is sovereign per source, queryable through publication, and grows in proportion to meaningful events (not all activity). Vendor gating fails because no single factor is necessary or sufficient. Resilience scales with constellation size and diversity.

The principles encoded in the reference implementation:

- **Witness ≠ vouch.** Observation, not endorsement.
- **Signature ≠ vouch.** Tamper-evidence on the claim, not authority over the truth.
- **Fingerprint on salience.** Hash what's meaningful per kind, silence what isn't.
- **Federate by salience.** Publish records that touch external edges; keep purely-internal records local.
- **Access modes are explicit.** Trust weight follows the access mode, not the signature.
- **Resilience scales with constellation size.** Bigger and more diverse = harder to enclose.

The constellation is the identity.
