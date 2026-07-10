# LCT: The Presence Substrate

**The question it answers: who is present?**

The **Linked Context Token (LCT)** is Web4's foundational primitive: a non-transferable, cryptographically anchored record permanently bound to exactly one entity for the duration of its participation. It is not an account, not a wallet, and not merely an identifier — it is the **reification of presence itself**. An LCT crystallizes when an entity enters Web4 and accompanies it until its participation ends.

## What can be present

Web4 deliberately widens what counts as an entity — anything that can leave a footprint can have one:

- **Humans** and **AI agents** (the obvious participants)
- **Organizations** (collective entities with their own presence)
- **Roles** (a job itself, distinct from whoever performs it — a key move covered later)
- **Tasks and resources** (things that exist, execute, complete, or get consumed)
- **Devices** (hardware that senses and acts)

## Core properties

**Permanently bound and non-transferable.** An LCT cannot be sold, given away, or moved between entities. This is not a limitation but the structural guarantee that makes reputation *mean* something: every witnessed interaction traces back to the entity that actually participated. Trust histories cannot be bought, inherited, or laundered.

**Cryptographically anchored.** Each LCT roots in keypair-backed identity, with an optional hardware-binding ladder (from software keys up to TPM- and secure-enclave-anchored attestation). "I am the entity bound to this LCT, here is a fresh signature over your challenge" is a claim cryptography can check — unlike "I am @alice," which is a claim a platform accepts.

**Witness-hardened.** An LCT's strength is not secrecy but *accumulated corroboration*. Every interaction can be witnessed by other entities; every witness link makes the presence harder to forge and its history harder to dispute. Trust in Web4 is built from this witnessing fabric — presence that has been repeatedly, independently observed. The lifecycle is explicit: an LCT is created, accumulates witnessed history, and concludes (*void* for natural ending, *slashed* for trust violation) — with the record persisting beyond conclusion, so accountability outlives participation.

**Linked and contextual.** LCTs form malleable links to other LCTs — trust webs, delegation chains, parent/child lineage. The token is permanent; its *expression* is contextual (the same doctor's presence carries different weight in a medical forum than a book club — a fact made precise by the MRH, two sections ahead).

## Why this is the foundation

Every subsequent term in the equation presupposes this one. Trust tensors describe *an LCT's* capability. Relevancy horizons scope *an LCT's* context. Value cycles reward *an LCT's* contribution. Verifiable presence is the move that converts "trust as declaration" into "trust as computable record" — the rest of the architecture is the machinery that computes it.

*Normative reference: [`core-spec/LCT-linked-context-token.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/LCT-linked-context-token.md) (Core Specification v1.0.0), with [`entity-types.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/entity-types.md) for the entity taxonomy and [`did-web4-method.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/did-web4-method.md) for the DID-standard bridge.*
