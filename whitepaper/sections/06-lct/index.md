# LCT: The Presence Substrate

**The question it answers: who is present?**

The **Linked Context Token (LCT)** is Web4's foundational primitive: a non-transferable, cryptographically anchored record permanently bound to exactly one entity for the duration of its participation. It is not an account, not a wallet, and not merely an identifier — it is the **reification of presence itself**. An LCT crystallizes when an entity enters Web4 and accompanies it until its participation ends.

The standard puts the distinction in one sentence: *an LCT is not an identity; it is a presence.* An identity answers "who are you?" A presence answers "who is here, acting, accumulating a record?" — and it is the record, not the claim, that everything else in Web4 computes on.

## What can be present

Web4 deliberately widens what counts as an entity — anything that can leave a footprint can have one:

- **Humans** and **AI agents** (the obvious participants)
- **Organizations** (collective entities with their own presence)
- **Roles** (a job itself, distinct from whoever performs it — a key move covered later)
- **Tasks and resources** (things that exist, execute, complete, or get consumed)
- **Devices** (hardware that senses and acts)

## The anatomy: what an LCT contains

An LCT is a JSON-LD document (`@type: web4:LinkedContextToken`) with **six required components**, and the list is the single most structural fact in this paper:

1. **Identity** — the `lct_id` and the subject's DID.
2. **Binding** — the cryptographic anchor and its `binding_proof`.
3. **MRH** — the entity's Markov Relevancy Horizon: its typed relationship graph.
4. **Policy** — the constraints under which the presence acts.
5. **T3** — the trust tensor (talent / training / temperament).
6. **V3** — the value tensor (valuation / veracity / validity).

Read that list against the equation. The `LCT` term and the `T3/V3 * MRH` term are not separate systems that reference each other — **the token is the container**: every LCT *carries* its own relevancy horizon and its own trust and value tensors as mandatory fields. The MRH section and the tensor section that follow describe the contents of every LCT ever minted, not auxiliary databases beside it.

The identifier is **self-certifying**. The binding (entity, key, optional hardware anchor) is serialized as deterministic CBOR, signed as a COSE_Sign1 `binding_proof`, and the LCT's identifier is derived from the proof itself: `lct:web4:` + multibase32(sha256(binding_proof)). The name cannot be pointed at anything other than the binding that produced it — the identifier *is* a hash of the anchoring act.

## Birth: witnessed, or bootstrapped

The primary issuance path is a **society-issued birth certificate**. An entity requests presence; its society validates citizenship; a binding ceremony runs with a quorum of **at least three birth witnesses**; and the new LCT's MRH is initialized from the ceremony itself — the witnesses become its first `witnessing` edges, the citizen role becomes a permanent `paired` edge, the hardware anchor becomes a `bound` edge. Presence begins *already woven into* the witnessing fabric, with initial T3/V3 computed and the token published to the society's registry.

A bootstrap path exists for entities without a society: the **self-issued LCT** — self-signed binding proof, empty MRH, minimal trust. It is real presence, but presence that has corroborated nothing yet. The distance between the two paths is exactly the distance trust must travel, and the capability ladder below makes that distance legible rather than binary.

## The capability ladder

LCTs are graded into six **capability levels** (0–5), each with explicit required fields: **STUB** (a placeholder), **MINIMAL** (self-issued), **BASIC** (at least one MRH relationship), **STANDARD** (witnessed, with oracle-computed tensors and attestation), **FULL** (birth certificate, ≥3 witnesses, permanent citizen pairing), and **HARDWARE** (a hardware-anchored EAT attestation). Levels 0→4 are additive — an LCT accretes capability as its record grows. Level 4→5 is **re-issuance**: hardware binding cannot be bolted on after the fact, because the anchor must be inside the binding proof the identifier hashes. Unimplemented components are carried as explicit stubs (`{stub: true, reason}`) — partial presence is declared, not hidden.

## One presence, many devices

A modern entity acts through several devices, and Web4's answer inverts the usual instinct that more endpoints mean more attack surface. A **Root LCT** carries a *device constellation*; each device holds its own **Device LCT** bound to one hardware anchor (phone secure enclave, FIDO2 key, TPM, or software fallback), cross-witnessing the others. Trust is **capped by anchor composition**: a single software key tops out at 0.40, a phone enclave or TPM alone at 0.75, and three or more diverse hardware anchors at 0.98. Recovery follows a quorum of the constellation itself. The design principle: **identity is coherence across witnesses** — a presence that many independent anchors keep agreeing on is *stronger*, not weaker, for each device added.

## Core properties

**Permanently bound and non-transferable.** An LCT cannot be sold, given away, or moved between entities. This is not a limitation but the structural guarantee that makes reputation *mean* something: every witnessed interaction traces back to the entity that actually participated. Trust histories cannot be bought, inherited, or laundered.

**Cryptographically anchored.** Each LCT roots in keypair-backed identity, with an optional hardware-binding ladder (from software keys up to TPM- and secure-enclave-anchored attestation). "I am the entity bound to this LCT, here is a fresh signature over your challenge" is a claim cryptography can check — unlike "I am @alice," which is a claim a platform accepts.

**Witness-hardened.** An LCT's strength is not secrecy but *accumulated corroboration*. Every interaction can be witnessed by other entities; every witness link makes the presence harder to forge and its history harder to dispute. Trust in Web4 is built from this witnessing fabric — presence that has been repeatedly, independently observed.

**Linked and contextual.** LCTs form malleable links to other LCTs — trust webs, delegation chains, parent/child lineage. The token is permanent; its *expression* is contextual (the same doctor's presence carries different weight in a medical forum than a book club — a fact made precise by the MRH, two sections ahead, which lives inside the token itself).

## Lifecycle: rotation, revocation, and a record that outlives participation

An LCT is created (genesis), lives (active), and can **rotate**: keys change by issuing a successor LCT under the same subject DID, with explicit lineage to the parent and a 24–48 hour overlap before the parent is marked superseded. It can be **revoked** — for compromise, supersession, expiry, or violation — which disables its capabilities while preserving its MRH read-only: the graph of what it touched remains queryable evidence. Participation ends in one of two states — *void* for a natural ending, *slashed* for a trust violation — and in both cases **the record persists beyond conclusion**. Accountability outlives participation; that is the point of presence rather than identity.

Underneath the entire mechanism runs one discipline the standard states explicitly: **inspectable evidence, not prescribed trust.** The protocol's job is to make the evidence unforgeable — the binding, the witnesses, the history. Whether to trust, and for what, remains the relying party's contextual call.

## Why this is the foundation

Every subsequent term in the equation presupposes this one. Trust tensors describe *an LCT's* capability — and live inside it. Relevancy horizons scope *an LCT's* context — and live inside it. Value cycles reward *an LCT's* contribution. Verifiable presence is the move that converts "trust as declaration" into "trust as computable record" — the rest of the architecture is the machinery that computes it.

*Normative reference: [`core-spec/LCT-linked-context-token.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/LCT-linked-context-token.md) (Core Specification v1.0.0), with [`lct-capability-levels.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/lct-capability-levels.md) for the capability ladder, [`multi-device-lct-binding.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/multi-device-lct-binding.md) for device constellations, [`entity-types.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/entity-types.md) for the entity taxonomy, and [`did-web4-method.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/did-web4-method.md) for the DID-standard bridge.*
