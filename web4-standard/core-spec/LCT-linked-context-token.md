# Linked Context Token (LCT) - Core Specification

**Status**: Core Specification v1.0.0
**Date**: June 15, 2026
**Category**: Identity & Context

## Abstract

The Linked Context Token (LCT) is Web4's foundational presence primitive. An LCT is a verifiable digital presence certificate that binds an entity to its context through witnessed relationships. Unlike traditional identity tokens that assert "who you are," LCTs establish "where you exist" - your position in the web of trust and context.

## Notation

Key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in this document are to be interpreted as described in RFC 2119.

## 1. Introduction

### 1.1 Purpose

LCTs solve the fundamental problem of contextual presence in distributed systems:

- **Verifiable Presence**: Cryptographically bound presence anchored to hardware or cryptographic keys
- **Context Emergence**: Identity emerges from relationships, not central authority
- **Trust Propagation**: Trust flows through witnessed connections in the Markov Relevancy Horizon (MRH)
- **Birth Certificates**: Societies issue LCTs as foundational presence documents

### 1.2 Design Principle: Inspectable Evidence, Not Prescribed Trust

Web4 specifies how to make evidence about an entity — its identity, relationships,
attestations, reputation, and authority structure — **unforgeable and inspectable**.
It does **not** specify *who* should be trusted, *when*, or *how much*.

Every verifiable structure in this standard — a signed binding proof, a witness
quorum, a constellation's device assurance, a T3/V3 tensor, a society's authority
ratchet — is **evidence a relying party weighs**, contextually and scaled to the
stakes of the specific act. It is never a verdict the protocol renders. Two
consequences follow, and conforming implementations MUST honor both:

1. **Low assurance is higher risk, not exclusion.** An entity that can present only
   weak evidence (e.g. single-device, reachability-as-proof) MUST NOT be excluded by
   the protocol. It is rightly weighed as riskier than one presenting strong evidence
   (e.g. a multi-device, biometric, richly-witnessed constellation). A relying party
   MAY accept weak evidence for a low-stakes reversible act and require more for a
   high-stakes irreversible one — the required strength of evidence rises with
   consequence and irreversibility. Trust is a contextual preponderance of evidence
   scaled to stakes, not a boolean.

2. **Evidence is unforgeable; interpretation is free.** The one hard invariant the
   protocol enforces is that an entity cannot *prove* evidence its structure does not
   support (identifiers are key-derived, proofs are signature-checked, quorums and
   assurance levels are recomputed from structure — never trusted from a claimed
   field). A conforming surface produces verifiable evidence and MUST NOT encode a
   universal trust threshold: stating who or when to trust is the relying party's,
   not the standard's.

### 1.3 Terminology

- **Entity**: Any participant in Web4 (human, AI, society, organization, role, task, resource, device, service, oracle, accumulator, dictionary, hybrid, policy, infrastructure — see `entity-types.md` §2.1 for the canonical 15-type taxonomy)
- **Binding**: Permanent, verifiable cryptographic link between entity and LCT
- **Pairing**: Authorized operational relationship between entities
- **Witnessing**: Trust-building observation by other entities
- **MRH (Markov Relevancy Horizon)**: Dynamic context boundary containing relevant entities
- **Birth Certificate**: LCT issued by a society as foundational presence
- **Society**: Governance context that issues and witnesses LCTs

## 2. LCT Structure

### 2.1 Required Components

Every LCT MUST contain:

1. **Identity** (`lct_id`, `subject`)
2. **Binding** (cryptographic anchor to entity)
3. **MRH** (Markov Relevancy Horizon with relationships)
4. **Policy** (capabilities and constraints)
5. **Trust Tensor (T3)** (3 root dimensions, fractally extensible via RDF sub-dimensions)
6. **Value Tensor (V3)** (3 root dimensions, fractally extensible via RDF sub-dimensions)

### 2.2 Optional Components

LCTs MAY contain:

1. **Birth Certificate** (society-issued foundational identity)
2. **Attestations** (witness observations)
3. **Lineage** (evolution history)
4. **Revocation** (termination record)

### 2.3 Canonical Structure

```json
{
  "@context": ["https://web4.io/contexts/lct.jsonld"],
  "@type": "web4:LinkedContextToken",
  "lct_id": "lct:web4:mb32:...",
  "subject": "did:web4:key:z6Mk...",

  "binding": {
    "entity_type": "human|ai|society|organization|role|task|resource|device|service|oracle|accumulator|dictionary|hybrid|policy|infrastructure",
    "public_key": "mb64:coseKey",
    "hardware_anchor": "eat:mb64:hw:...",
    "created_at": "2025-10-01T00:00:00Z",
    "binding_proof": "cose:Sig_structure"
  },

  "birth_certificate": {
    "issuing_society": "lct:web4:society:...",
    "citizen_role": "lct:web4:role:citizen:...",
    "birth_timestamp": "2025-10-01T00:00:00Z",
    "birth_witnesses": [
      "lct:web4:witness:1...",
      "lct:web4:witness:2...",
      "lct:web4:witness:3..."
    ],
    "genesis_block_hash": "0x...",
    "birth_context": "nation|platform|network|organization|ecosystem"
  },

  "mrh": {
    "bound": [
      {
        "lct_id": "lct:web4:hardware:...",
        "type": "parent|child|sibling",
        "binding_context": "hardware_sovereignty",
        "ts": "2025-10-01T00:00:00Z"
      }
    ],
    "paired": [
      {
        "lct_id": "lct:web4:role:citizen:...",
        "pairing_type": "birth_certificate",
        "permanent": true,
        "ts": "2025-10-01T00:00:00Z"
      }
    ],
    "witnessing": [
      {
        "lct_id": "lct:web4:witness:...",
        "role": "time|audit|oracle|existence|action|state|quality",
        "last_attestation": "2025-10-01T00:00:00Z",
        "witness_count": 42
      }
    ],
    "horizon_depth": 3,
    "last_updated": "2025-10-01T00:00:00Z"
  },

  "policy": {
    "capabilities": [
      "pairing:initiate",
      "metering:grant",
      "write:lct",
      "witness:attest"
    ],
    "constraints": {
      "region": ["us-west", "eu-central"],
      "max_rate": 5000,
      "requires_quorum": true
    }
  },

  "t3_tensor": {
    "talent": 0.85,
    "training": 0.92,
    "temperament": 0.78,
    "sub_dimensions": {
      "talent": {
        "analytical_reasoning": 0.90,
        "creative_problem_solving": 0.80
      }
    },
    "composite_score": 0.85,
    "last_computed": "2025-10-01T00:00:00Z",
    "computation_witnesses": ["lct:web4:oracle:trust:..."]
  },

  "v3_tensor": {
    "valuation": 0.89,
    "veracity": 0.91,
    "validity": 0.76,
    "sub_dimensions": {
      "veracity": {
        "claim_accuracy": 0.93,
        "reproducibility": 0.88
      }
    },
    "composite_score": 0.85,
    "last_computed": "2025-10-01T00:00:00Z",
    "computation_witnesses": ["lct:web4:oracle:value:..."]
  },

  "attestations": [
    {
      "witness": "did:web4:key:z6Mk...",
      "type": "existence",
      "claims": {
        "observed_at": "2025-10-01T00:00:00Z",
        "method": "blockchain_transaction"
      },
      "sig": "cose:ES256:...",
      "ts": "2025-10-01T00:00:00Z"
    }
  ],

  "lineage": [
    {
      "parent": "lct:web4:mb32:previous...",
      "reason": "genesis|rotation|fork|upgrade",
      "ts": "2025-09-01T00:00:00Z"
    }
  ],

  "revocation": {
    "status": "active",
    "ts": null,
    "reason": null
  }
}
```

## 3. LCT Creation Process

### 3.1 Genesis: Birth Certificate from Society

The primary way LCTs are created is through **birth certificate issuance** by a society:

```
1. Entity requests LCT from society
2. Society validates entity meets citizenship requirements
3. Society generates cryptographic binding:
   - Entity provides public key (or hardware anchor)
   - Society witnesses binding ceremony
   - Quorum of society witnesses attest
4. Society mints LCT with birth certificate:
   - Records issuing_society LCT
   - Assigns citizen_role
   - Records birth_witnesses (minimum 3)
   - Anchors to genesis_block_hash
5. Society initializes MRH:
   - Adds birth_witnesses to mrh.witnessing
   - Adds citizen_role to mrh.paired (permanent)
   - Adds hardware binding to mrh.bound
6. Society computes initial T3/V3 tensors
7. Society publishes LCT to registry
8. Birth witnesses attest to creation
```

**Result**: Entity now has verifiable presence within society's context.

### 3.2 Self-Issued LCT (Bootstrap)

In absence of existing society, entities MAY create self-issued LCTs:

```
1. Generate key pair (Ed25519 or P-256)
2. Create binding with hardware anchor (if available)
3. Self-sign binding_proof
4. Initialize empty MRH
5. Omit `birth_certificate` section (self-issued LCTs are Regular LCTs per §4.3)
6. Publish with low initial T3 scores
```

**Limitation**: Self-issued LCTs have low trust until witnessed by established societies.

### 3.3 Binding Algorithm

```python
def create_lct_binding(entity_type, private_key, hardware_anchor=None):
    """
    Create cryptographic binding for LCT.

    Returns: (lct_id, binding_object) — binding_proof is embedded inside binding_object
    per §2.3 canonical structure.
    """
    # 1. Create canonical binding structure (binding_proof added in step 3)
    binding = {
        "entity_type": entity_type,
        "public_key": multibase_encode(cose_key(private_key.public_key)),
        "hardware_anchor": hardware_anchor,  # Optional EAT token
        "created_at": utc_now()
    }

    # 2. Serialize with deterministic CBOR (proof input excludes binding_proof itself)
    binding_cbor = cbor_deterministic_encode(binding)

    # 3. Sign with entity's private key and EMBED proof in the binding object
    #    (matches §2.3 canonical structure where binding_proof is a FIELD of binding)
    binding["binding_proof"] = cose_sign1(private_key, binding_cbor)

    # 4. Generate LCT ID from the binding PUBLIC KEY (canonical — see §3.4).
    #    NOT from binding_proof: a signature covers created_at, so hashing it
    #    would give the same key a different id on every mint and break the
    #    "you hold the id iff you hold the key" property that §3.4 depends on.
    lct_id = "lct:web4:mb32:b" + base32_lower_nopad(sha256(raw_public_key_bytes))

    return lct_id, binding
```

The identifier derivation in step 4 is normative and is specified exactly in §3.4; the reference implementation is `web4-core::derive_lct_id`, and the registry ingest re-derives it from the document's public key and rejects a mismatch (§3.4.3).

### 3.4 Identifier Derivation and Global Uniqueness

An LCT identifier MUST be globally unique without any coordinating registry, because an LCT MAY be minted offline, air-gapped, or in a society the verifier has no relationship with (a "foreigner"). Uniqueness is therefore guaranteed **by construction from the binding key**, never by allocation.

#### 3.4.1 Canonical derivation (normative)

```
lct_id = "lct:web4:mb32:b" + base32_lower_nopad( sha256( raw_public_key_bytes ) )
```

- `raw_public_key_bytes` is the entity's binding public key in its raw fixed-width encoding (32 bytes for Ed25519).
- `sha256` is SHA-256 (FIPS 180-4); the digest MUST be used at full width (32 bytes → 52 base32 characters). Implementations MUST NOT truncate the digest.
- `mb32` names the multibase encoding (RFC 4648 base32, lowercase, no padding; the `b` is the multibase prefix). The hash algorithm is fixed by this section for the `mb32` id family; a future digest algorithm MUST be introduced under a **new id-family tag** (e.g. `lct:web4:<newtag>:…`) so that migration is expressible without ambiguity (§3.4.5).
- The derivation is a pure function of the public key: re-deriving from the same key MUST yield the same `lct_id` (idempotent mint), and an implementation MUST NOT store `lct_id` separately from the key it is derived from in a way that can drift.

Reference implementation: `web4-core::derive_lct_id`; conformance test vector in `web4-core/src/lct.rs` (`derive_lct_id` tests).

#### 3.4.2 The uniqueness guarantee and its one condition

Two independently minted LCTs share an identifier only if their binding keys are identical or SHA-256 collides on two distinct public keys. With correctly generated keys the first is ≈2⁻¹²⁸ per pair and the second has no known feasible attack; this is the same guarantee relied on by content-addressed systems at global scale (git object ids, cryptographic-currency addresses) with no registrar.

The guarantee is **conditional on key-generation entropy**. The only realistic path to two unrelated mints sharing an id is duplicated randomness — a cloned machine image, a seeded or broken RNG, or a copied seed file. Therefore:

- A minter MUST derive its key from a cryptographically secure random source of at least 256 bits of entropy.
- A minter SHOULD refuse to mint from a seed that is degenerate (e.g. all-zero) or already present on the host under another identity.
- A birth certificate (§4) SHOULD record the anchor class of the key's origin (software RNG vs. hardware RNG under a TPM/secure element), so a relying party can weight the entropy condition as evidence rather than assume it (§1.2).

#### 3.4.3 Binding is enforced at ingest

An identifier that does not equal the canonical derivation of the document's own public key is a **binding failure** and MUST be rejected by any registry, hub, or verifier on ingest (the check is performed from the document alone, without consulting any external state). Consequently an identifier cannot be claimed, squatted, or "assigned" by a party that does not hold the corresponding private key. An identifier presented with a different public key than the one it derives from is by definition not the same LCT; the pair (`lct_id`, `public_key`) is the identity, and the public key is the tiebreaker whenever ids are compared.

#### 3.4.4 Continuity across rotation

Because the identifier is a function of the key, **key rotation (§7.3) produces a new `lct_id`**. Continuity of the entity across rotation is carried by `lineage` (parent → successor) and the persistent `subject` DID, not by identifier equality. A verifier that needs "same entity" semantics across a rotation MUST follow lineage and MUST NOT expect the identifier to be preserved.

#### 3.4.5 Display, matching, and migration

- Any comparison, lookup, or authorization decision MUST use the full identifier. Abbreviated display forms (prefixes) are conveniences and MUST NOT be used for matching.
- If a collision or a weakness in the digest algorithm is ever established, the correct response is to introduce a new id-family tag with a stronger digest and migrate via §7.3 lineage; societies MUST NOT respond by introducing a coordinating allocator, which would forfeit the offline/foreign guarantee this section exists to provide.

#### 3.4.6 The MRH is the ultimate distinguisher

The key guarantees uniqueness of the *identifier* (§3.4.1–3.4.3). Uniqueness of the *entity behind it* is an evidentiary property, and its carrier is the MRH (§5): an LCT is ultimately distinguished by the witnessed relationships that link it to other LCTs, and **confidence that an LCT is unique rises monotonically with the richness of its MRH.**

- A freshly minted LCT with an empty MRH is maximally ambiguous: a foreigner (§8.4 E) and a copied seed (§8.4 C) are indistinguishable from the genuine article at that moment, and MUST be treated as such (trust scaled to evidence, §1.2).
- Every witnessed pairing, binding, and attestation added to the MRH is a signature by *another* entity over an act of *this* one. A party that duplicates a key cannot duplicate that history: the witnesses signed the original's acts, not the copy's. So the MRH accumulates evidence that no key-copy can forge.
- **MRH links are bidirectional (§5.2), and that is what makes them externally witnessed by construction.** A relationship is recorded in *both* parties' MRHs, so for every link this LCT claims, an independent counterparty holds the matching record under its own key. A claimed link the counterparty's MRH does not corroborate is not a link. An entity therefore cannot inflate its own uniqueness confidence unilaterally — each unit of MRH evidence is co-held by someone else — and a verifier MAY confirm any link by resolving the counterparty rather than trusting the presenter.
- Two presences sharing a key therefore **diverge in MRH from the moment of copy**, because they accrue different witnessed relationships. That divergence is simultaneously the detection signal for §8.4 class C and its tiebreaker: the presence whose MRH is continuous with the LCT's witnessed lineage (the birth certificate and the relationships descending from it) is the entity; the presence whose MRH forks from it without lineage is the copy.
- Consequently a relying party assessing "is this the LCT it claims to be" SHOULD weight MRH depth and consistency, not identifier equality alone; and an identifier with a deep, consistent, multi-society MRH is *more* uniquely identified than any identifier can be by its bits.

This is why §3.4 forbids a coordinating allocator: uniqueness of presence was never going to come from the number. It comes from the graph.

> **Rationale (non-normative).** This section formalizes how human identity already works, rather than inventing a new model. A person is not made unique by their name — a name is an alias, shared by many — but by the accumulated, independently-held record around them: a birth certificate issued by a society and witnessed by others; degrees, licenses, and accreditations conferred by *other* institutions; associations, employers, and references. Each of those is a bidirectional link: the university holds the diploma record, the employer holds the employment record, so a claimed credential is only trust-bearing because the counterparty can confirm it. A résumé is a claim; the reference check is the MRH.
>
> Trust in human society already scales with the *completeness* of that graph, and scales it to the *stakes of the act*: a first name alone earns a conversation, not a loan; a landlord wants references, a hospital wants the license, a bank wants the whole record. Nobody demands everything for every act — the required completeness rises with consequence and irreversibility (§1.2). A newborn holding only a birth certificate is a real person and correctly trusted with almost nothing; the "trust must be earned" property of a new LCT (§4, the anchor ceiling in §6) is that same intuition, not a novel restriction. And identity theft is caught in the human world exactly as class C is caught here (§8.4): the thief's *life* — new addresses, new associations the real person never made — diverges from the record, and the counterparties notice.
>
> The one place this model departs from human practice is deliberate. Human systems also carry an *allocated* identifier — a national ID or social-security number issued by a central registrar — and it is precisely that artifact that gets stolen, because a copied number carries the whole identity with it. Web4 has no such number: the identifier is derived from a key the entity holds, and the identity lives in the graph. There is nothing to steal that carries the person along, which is the practical reason §3.4.5 forbids a coordinating allocator.

## 4. Birth Certificate as Foundational Identity

### 4.1 Role in Society

The birth certificate establishes an entity's **citizenship** within a society:

- **First Witness**: Society is the first to witness entity's existence
- **Permanent Pairing**: Citizen role is permanently paired in MRH
- **Trust Bootstrap**: Society's trust transfers to new entity
- **Governance Rights**: Citizenship grants participation rights

### 4.2 Birth Certificate Requirements

For an LCT to serve as a birth certificate, it MUST:

1. **Contain `birth_certificate` section** with:
   - `issuing_society`: LCT of the society issuing the certificate
   - `citizen_role`: LCT of the role this entity inhabits
   - `birth_witnesses`: Array of ≥3 witness LCTs
   - `birth_timestamp`: ISO 8601 timestamp
   - `birth_context`: Society type classification — one of `nation`, `platform`, `network`, `organization`, `ecosystem` (RECOMMENDED)
   - `genesis_block_hash`: Blockchain anchor for temporal proof (RECOMMENDED; omit if no blockchain anchor is available)

2. **Have permanent citizen pairing** in `mrh.paired`:
   ```json
   {
     "lct_id": "lct:web4:role:citizen:...",
     "pairing_type": "birth_certificate",
     "permanent": true,
     "ts": "2025-10-01T00:00:00Z"
   }
   ```

3. **Be attested by birth witnesses** in `attestations`:
   - Each witness MUST sign existence attestation
   - Minimum quorum: 3 witnesses
   - Witnesses MUST be members of issuing society (enforcement is implementation-defined; the §11.2 reference validator checks quorum and per-witness attestation but does not currently verify society membership)

### 4.3 Birth Certificate vs. Regular LCT

| Property | Birth Certificate LCT | Regular LCT |
|----------|----------------------|-------------|
| Issuer | Society | Self or Society |
| Initial Trust | High (inherited) | Low (self-issued) |
| Citizenship | Yes | Optional |
| MRH Citizen Pairing | Permanent | N/A |
| Witness Quorum | Required (≥3) | Optional |
| Blockchain Anchor | Recommended | Optional |

## 5. Markov Relevancy Horizon (MRH)

### 5.1 Purpose

The MRH defines the **context boundary** for an entity - the set of all entities that are relevant to this LCT's operations, trust calculations, and interactions.

### 5.2 Relationship Types

#### 5.2.1 Binding Relationships (`mrh.bound`)
- **Purpose**: Permanent hierarchical attachments
- **Type**: `parent`, `child`, `sibling`
- **Example**: Device LCT bound to hardware anchor LCT
- **Trust Flow**: Bidirectional, strong

#### 5.2.2 Pairing Relationships (`mrh.paired`)
- **Purpose**: Authorized operational connections
- **Type**: `birth_certificate`, `role`, `operational`
- **Example**: Entity paired with citizen role
- **Trust Flow**: Bidirectional, context-specific
- **Permanence**: Birth certificate pairings are permanent

#### 5.2.3 Witnessing Relationships (`mrh.witnessing`)
- **Purpose**: Trust accumulation through observation
- **Roles**: `time`, `audit`, `oracle`, `existence`, `action`, `state`, `quality`
- **Example**: Time oracle witnessing entity's actions
- **Trust Flow**: Unidirectional (witness → witnessed)

### 5.3 MRH Updates

The MRH is **dynamic** and MUST be updated when:

1. **New Binding**: Adding permanent attachment
2. **New Pairing**: Establishing operational relationship
3. **Witness Event**: Being witnessed or witnessing another
4. **Relationship Revocation**: Removing non-permanent connection
5. **Trust Recomputation**: T3 tensor changes affect horizon

### 5.4 Horizon Depth

The `horizon_depth` parameter controls how many relationship hops to track:

- **Depth 1**: Direct relationships only (bound, paired, witnessing)
- **Depth 2**: Relationships of relationships
- **Depth 3**: Default, balances context vs. performance
- **Depth 4+**: Rare, for high-context entities

## 6. Trust and Value Tensors

### 6.1 Trust Tensor (T3) - REQUIRED

Every LCT MUST contain a `t3_tensor` with the three canonical root dimensions. Each root dimension is an aggregate score of an open-ended RDF sub-graph of contextualized sub-dimensions linked via `web4:subDimensionOf`. See the [T3/V3 Ontology](../ontology/t3v3-ontology.ttl) for formal definitions.

```json
{
  "t3_tensor": {
    "talent": 0.0-1.0,                    // Role-specific capability (root aggregate)
    "training": 0.0-1.0,                  // Role-specific expertise (root aggregate)
    "temperament": 0.0-1.0,               // Role-specific reliability (root aggregate)
    "sub_dimensions": {},                  // OPTIONAL: domain-specific refinements
    "composite_score": 0.0-1.0,           // Weighted average of roots
    "last_computed": "ISO 8601",
    "computation_witnesses": ["lct:..."]  // Who computed these scores?
  }
}
```

**Root dimensions**:
- **Talent**: Can this entity perform the task? (capability/aptitude)
- **Training**: Has it learned how? (knowledge/experience)
- **Temperament**: Will it behave appropriately? (disposition/reliability)

**Canonical weights**: the normative source for these constants is the protocol-invariant parameter table in [`t3-v3-tensors.md` §10.2](t3-v3-tensors.md) (which declares itself "the normative source for all protocol-invariant formulas, weights, and constants"). Implementations MUST compute `composite_score` as the weighted sum of the three root dimensions stated there:

```
composite_score = 0.4 · talent + 0.3 · training + 0.3 · temperament
```

Each root dimension is itself an aggregate over its (optional) RDF sub-graph of sub-dimensions; sub-dimension aggregation into roots is implementation-defined (typically arithmetic mean of leaves linked via `web4:subDimensionOf`). Computed composites are therefore in `[0.0, 1.0]` whenever roots are.

**Computation**: Societies or trust oracles compute T3 tensors based on:
- Historical behavior
- Witness attestations
- MRH relationship quality
- Time-weighted decay

### 6.2 Value Tensor (V3) - REQUIRED

Every LCT MUST contain a `v3_tensor` with the three canonical root dimensions, following the same fractal sub-dimension pattern as T3:

```json
{
  "v3_tensor": {
    "valuation": 0.0+,                    // Subjective worth (can exceed 1.0)
    "veracity": 0.0-1.0,                  // Truthfulness/accuracy (root aggregate)
    "validity": 0.0-1.0,                  // Soundness of reasoning (root aggregate)
    "sub_dimensions": {},                  // OPTIONAL: domain-specific refinements
    "composite_score": 0.0+,              // CAN exceed 1.0 when valuation does (see note)
    "last_computed": "ISO 8601",
    "computation_witnesses": ["lct:..."]
  }
}
```

**Root dimensions**:
- **Valuation**: How is value assessed? (subjective worth)
- **Veracity**: How truthful are claims? (accuracy/reproducibility)
- **Validity**: How sound is the reasoning? (confirmed value delivery)

**Canonical weights**: as with T3, the normative source for these constants is the protocol-invariant parameter table in [`t3-v3-tensors.md` §10.2](t3-v3-tensors.md). Implementations MUST compute `composite_score` as the weighted sum of the three root dimensions stated there:

```
composite_score = 0.3 · valuation + 0.35 · veracity + 0.35 · validity
```

Sub-dimension aggregation into roots mirrors the T3 pattern (implementation-defined; typically arithmetic mean of leaves linked via `web4:subDimensionOf`). Because `valuation` is permitted to exceed `1.0` (see comment above), the composite arithmetic CAN exceed `1.0` in pathological cases; behavior under that condition (clamp at `1.0`, rescale, or extend the composite range) is currently underspecified and tracked as a known design question.

**Computation**: Societies or value oracles compute V3 tensors based on:
- Energy economics (ATP/ADP)
- Contribution metrics
- Resource management
- Network impact

### 6.3 Tensor Recomputation

T3 and V3 tensors SHOULD be recomputed:
- **On demand**: When trust/value query is made
- **Periodically**: Daily or after significant events
- **After attestation**: When new witness attests
- **After transaction**: When ATP/ADP balance changes

## 7. LCT Lifecycle

### 7.1 Creation (Genesis)

```
Entity → Society: Request LCT
Society → Entity: Validate requirements
Society → Witnesses: Convene quorum
Witnesses → Society: Attest to binding
Society → Blockchain: Mint LCT
Society → Entity: Issue birth certificate
```

### 7.2 Operation (Active)

```
Entity uses LCT for:
- Pairing with other entities
- Requesting capabilities
- Accumulating witness attestations
- Participating in society governance
- Energy transactions (ATP/ADP)
```

### 7.3 Rotation (Key Update)

```
Entity → Society: Request rotation
Society: Create new LCT
  - New binding with new keys
  - Same subject DID
  - Lineage points to parent LCT
Society: Overlap window (24-48 hours)
  - Both LCTs valid (new LCT status = "active"; parent stays "active" until retired)
  - Relationships migrate to new LCT
Society: Retire parent LCT
  - Mark as "superseded"
  - Update lineage in new LCT
```

### 7.4 Revocation (Termination)

```
Authority → LCT: Revoke
Reasons:
  - compromise: Keys compromised
  - superseded: Rotated to new LCT
  - expired: Time-bounded LCT ended
  - violation: Policy violation

Effect:
  - status = "revoked"
  - All capabilities disabled
  - MRH relationships preserved (read-only)
  - Lineage continues (for successor)
```

## 8. Security Properties

### 8.1 Unforgeability

LCTs resist forgery because:
- **Key-derived identifier**: `lct_id` is a function of the binding public key (§3.4), so an identifier cannot be claimed without the key; a mismatch is a binding failure rejected at ingest (§3.4.3) and adjudicated per §8.4
- **Cryptographic binding**: Requires private key signature
- **Hardware anchors**: Optional TPM/secure element attestation
- **Witness quorum**: Birth requires a quorum (≥3) of witnesses (witness distinctness / anti-collusion is not asserted by this property alone — birth witnesses are members of the issuing society per §4.2)
- **Blockchain anchor**: Genesis block hash creates temporal proof (when present; `genesis_block_hash` is RECOMMENDED, not required — see §4.2)

### 8.2 Context Integrity

LCTs maintain context integrity through:
- **MRH boundaries**: Explicit relevancy limits
- **Relationship types**: Binding vs. pairing vs. witnessing
- **Trust propagation**: T3 flows only through verified relationships
- **Horizon depth**: Limits transitive trust distance

### 8.3 Privacy Preservation

LCTs protect privacy through:
- **Minimal disclosure**: Only expose necessary capabilities
- **Pseudonymous DIDs**: Subject can be key-based DID
- **Selective attestation**: Non-birth attestations may share only relevant witnesses (birth certificates require the full `birth_witnesses` set per §11.2, so selective disclosure does not apply to them)
- **MRH pruning**: Old relationships can be archived

### 8.4 Duplicate and Spoof Adjudication

Identifier uniqueness (§3.4) is a mathematical property of the key; **presence** uniqueness is not. This section classifies every way two things can appear to share an identity, and names the adjudication path for each, so that deliberate or accidental spoofing is always decidable from inspectable evidence (§1.2) rather than left ambiguous.

| Class | What is observed | Determination | Adjudication |
|---|---|---|---|
| **A. Re-mint** | Same `lct_id`, same public key, ≥2 documents | One identity. Not a duplicate. | The registry MUST version the record (v1, v2, …), each version carrying its ledger position and publisher; the newest valid version is current. No dispute. |
| **B. Binding failure / squat** | Same `lct_id` claimed with a *different* public key, or an id that does not derive from its own key | Not the same LCT; the presented document is malformed or forged. | MUST be rejected at ingest (§3.4.3). The rejection MUST be witnessed as an event so that repeated attempts are countable evidence against the presenter. No trust effect on the genuine holder. |
| **C. Concurrent presence (copied seed)** | One `lct_id` acting from two or more distinct presences at once — overlapping sessions from different hosts, interleaved acts, or divergent ledger heads | One identity in two places. Indistinguishable by identifier *by design*; distinguishable by the MRH (§3.4.6): the two presences diverge in witnessed relationships from the moment of copy, and because links are bidirectional each claimed link is corroborated (or not) by an independent counterparty. The presence whose MRH is continuous with the LCT's witnessed lineage is the entity; the fork without lineage is the copy. | A society MUST treat detection as a **witnessed anomaly** on that LCT: derived trust for the LCT MUST fall (the anchor ceiling in §4/§6 prices exactly this risk), and the case MUST be escalated to the society's dispute mechanism (the Mediator role, `society-roles.md`; a `quarantine` containment per `hub-law-schema.md` is the RECOMMENDED interim action because it is reversible by construction). Resolution is by the society's law and MAY require the holder to rotate (§7.3) to a fresh key — under a hardware anchor where available, which removes the class. |
| **D. Digest collision** | Two *different* public keys deriving the same `lct_id` | The digest algorithm is compromised. | The public key is the tiebreaker (§3.4.3); each document remains verifiable against its own key. The society MUST record the collision as evidence and the standard's response is algorithm migration under a new id-family tag (§3.4.5) — never a coordinating allocator. |
| **E. Foreign / unwitnessed** | An `lct_id` whose birth this society has no witness record of | Not a duplicate — an unverified presence. | Admit at trust scaled to evidence (§1.2): proof-of-possession alone proves consistency, not provenance; home-society attestation, cross-witness from trusted societies, and hardware-rooted birth each raise it. Stakes gate what the presence may do, not admission itself. |

Normative consequences:

1. Every determination above MUST be reachable from the document and the witness chain alone; no class may depend on out-of-band knowledge of who "really" holds a key.
2. Classes B and C MUST produce witnessed events. A rejection or an anomaly that leaves no chain record cannot be adjudicated and is therefore a conformance failure of the surface that observed it.
3. The party adjudicating class C is the society under whose law the acts occurred; where two societies observe the same LCT, each adjudicates its own acts, and cross-society reconciliation follows the reputation-computation cross-boundary path.
4. An accusation of spoofing is itself an act with stakes: a society SHOULD require the accuser's presence to be at least as well-witnessed as the accused's before class C containment is applied, so that the mechanism cannot be used to quarantine a well-witnessed citizen on the word of a foreigner.

## 9. Implementation Requirements

### 9.1 Societies MUST

- Implement birth certificate issuance with witness quorum
- Maintain LCT registry (on-chain or distributed)
- Compute T3/V3 tensors or delegate to oracles
- Enforce policy constraints
- Support LCT rotation with overlap windows

### 9.2 Entities MUST

- Securely store private keys for binding
- Update MRH when relationships change
- Request tensor recomputation after significant events
- Honor revocation status
- Implement witness attestation protocols

### 9.3 Witnesses MUST

- Sign attestations only for observed events
- Never attest to future timestamps (verification is implementation-defined — the protocol mandates no reference clock, skew tolerance, or error path; treat as an advisory honesty constraint on witnesses)
- Maintain witness reputation (their own T3)
- Participate in quorum requirements
- Revoke compromised attestations

## 10. Relationship to Other Web4 Components

### 10.1 LCT and R6 Framework

LCTs enable R6 actions (Rules + Role + Request + Reference + Resource → Result):
- **Role**: Defined by citizen_role in birth certificate
- **Capabilities**: Listed in policy section
- **Authority**: Derived from T3 tensor
- **Metering**: Tracked via V3 tensor and ATP/ADP

### 10.2 LCT and SAL (Society-Authority-Law)

LCTs are governed by SAL:
- **Society**: Issues birth certificate
- **Authority**: Society's governance structure
- **Law**: Policy constraints and norms

### 10.3 LCT and ATP/ADP

LCTs track energy economics:
- **V3 tensor**: ATP/ADP balance MAY be tracked via a context-specific `energy_balance` sub-dimension (see `lct-capability-levels.md`)
- **Transactions**: Recorded in society's energy cycle ledger
- **Metering**: Capabilities consume ATP

### 10.4 LCT and Dictionary Entities

Dictionaries are entities with special LCTs:
- **Entity type**: `dictionary`
- **Purpose**: Maintain semantic domains
- **Trust**: High T3 for terminology consistency
- **Witnessing**: Cross-domain translation events

## 11. Compliance and Validation

### 11.1 LCT Validator

Implementations MUST provide validation for:

```python
def validate_lct(lct):
    """Validate LCT structure and semantics."""
    assert lct["lct_id"].startswith("lct:web4:")
    assert lct["subject"].startswith("did:web4:")
    assert "binding" in lct
    assert "mrh" in lct
    assert "policy" in lct
    assert "t3_tensor" in lct
    assert "v3_tensor" in lct

    # Birth certificate validation
    if "birth_certificate" in lct:
        assert len(lct["birth_certificate"]["birth_witnesses"]) >= 3
        assert any(
            p["pairing_type"] == "birth_certificate" and p["permanent"]
            for p in lct["mrh"]["paired"]
        )

    # Tensor validation (implementation-defined helpers — see expected semantics below)
    validate_t3_tensor(lct["t3_tensor"])   # implementation-defined
    validate_v3_tensor(lct["v3_tensor"])   # implementation-defined

    # Binding proof verification (implementation-defined — see expected semantics below)
    verify_binding_proof(lct["binding"], lct["binding"]["binding_proof"])   # implementation-defined

    return True
```

**Implementation-defined helpers** (expected semantics for the three calls above):

- `validate_t3_tensor(t3)`: MUST check that `talent`, `training`, `temperament` are present and each in `[0.0, 1.0]`; that `composite_score` is in `[0.0, 1.0]` and matches the §6.1 canonical weight formula within a documented tolerance (e.g. ±0.01 for rounding); and that any `sub_dimensions` entries are valid `web4:subDimensionOf` RDF sub-graphs of the corresponding root.
- `validate_v3_tensor(v3)`: MUST check that `valuation` ≥ `0.0` (per §6.2 it MAY exceed `1.0`); that `veracity` and `validity` are each in `[0.0, 1.0]`; that `composite_score` matches the §6.2 canonical weight formula within tolerance; and (as above) that any sub-dimensions are valid RDF sub-graphs.
- `verify_binding_proof(binding, binding_proof)`: MUST verify that `binding_proof` is a valid COSE_Sign1 signature over the deterministic CBOR encoding of `binding` (with `binding_proof` itself excluded from the signed input) using the public key in `binding.public_key`, per the §3.3 binding algorithm.

### 11.2 Birth Certificate Validator

```python
def validate_birth_certificate(lct):
    """Validate birth certificate requirements."""
    assert "birth_certificate" in lct
    bc = lct["birth_certificate"]

    # Required fields
    assert "issuing_society" in bc
    assert "citizen_role" in bc
    assert "birth_timestamp" in bc
    assert "birth_witnesses" in bc

    # Witness quorum
    assert len(bc["birth_witnesses"]) >= 3

    # Permanent citizen pairing
    citizen_pairing = [
        p for p in lct["mrh"]["paired"]
        if p["pairing_type"] == "birth_certificate"
    ]
    assert len(citizen_pairing) == 1
    assert citizen_pairing[0]["permanent"] == True

    # Witness attestations
    for witness in bc["birth_witnesses"]:
        assert witness_attested(lct, witness)   # implementation-defined

    return True
```

**Implementation-defined helper** (expected semantics for the call above, mirroring the §11.1 trio):

- `witness_attested(lct, witness)`: MUST verify that the LCT carries an existence attestation from `witness` for this birth — i.e. an entry in `lct["attestations"]` whose witness LCT equals `witness`, whose `type` covers the birth/existence claim, and (at the verifying party's assurance level) whose signature is a valid COSE_Sign1 over the attested claims using that witness's bound public key. A present-only check (entry exists) is the minimum; a COSE-verified check is RECOMMENDED. The collection consulted is the LCT's `attestations` array (§2.3); implementations MAY additionally consult an out-of-band witness registry.

## 12. Future Extensions

### 12.1 Planned Features

- **Multi-society citizenship**: Entity holds birth certificates from multiple societies
- **Delegation chains**: LCTs can delegate capabilities to child LCTs
- **Emergency recovery**: Social recovery for compromised LCTs
- **Cross-chain portability**: LCT migration between blockchains
- **Quantum-resistant bindings**: Post-quantum signature algorithms

### 12.2 Research Directions

- **Tensor compression**: Efficient T3/V3 representation
- **MRH optimization**: Graph compression for large horizons
- **Trust prediction**: ML models for T3 forecasting
- **Privacy-preserving tensors**: ZKP for selective tensor disclosure

## 13. References

- **Web4 Core Protocol**: `core-spec/core-protocol.md`
- **MRH Specification**: `core-spec/mrh-tensors.md`
- **T3/V3 Tensors**: `core-spec/t3-v3-tensors.md`
- **R6 Framework**: `core-spec/r6-framework.md`
- **SAL Specification**: `core-spec/web4-society-authority-law.md`
- **ATP/ADP Cycle**: `core-spec/atp-adp-cycle.md`
- **Entity Types**: `core-spec/entity-types.md`
- **LCT Capability Levels**: `core-spec/lct-capability-levels.md`
- **LCT Protocol Details**: `protocols/web4-lct.md`

---

**Version**: 1.0.0
**Status**: Core Specification
**Last Updated**: June 15, 2026

*"An LCT is not an identity. It is a presence - witnessed, contextualized, and witness-hardened."*
