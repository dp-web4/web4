# Web4 Game Engine Threat Model (Research Prototype)

This document describes a **research-stage** threat model for the `/web4/game` simulation engine.
It is not a production security specification. The goal is to make current assumptions,
protections, and gaps explicit so that future work can improve on them.

## Scope

- **In scope**
  - The in-memory Web4 game engine under `web4/game/`.
  - Per-society microchains and their hash-chain structure.
  - MRH-aware trust and policy mechanics (local and cross-society).
  - The hardware-binding MVP for root societies.
- **Out of scope (for now)**
  - Real networked deployment, key distribution, and OS-level hardening.
  - Full TPM/HSM/enclave integrations and attested remote verification.
  - Economic/game-theoretic guarantees about ATP pricing or incentives.

## Assets

- **Society microchains**
  - Block sequences for each society (`Society.blocks`) with header hashes and events.
- **Treasuries**
  - Per-society ATP balances (`Society.treasury["ATP"]`).
- **Membership and roles**
  - Membership lists and role assignments that gate treasury actions.
- **Trust state**
  - Agent- and society-level T3 composite trust scores.
- **Hardware binding metadata (MVP)**
  - `Society.hardware_fingerprint` and the genesis event that records it.

## Adversaries (Modelled at v0)

- **Greedy insider treasurer**
  - An agent with initial treasurer role who attempts repeated suspicious spends.
- **Low-trust neighbor society**
  - A federated society whose behavior drives its trust score down.
- **Honest-but-curious observer**
  - Reads chains and context edges, but does not tamper with process memory.

Adversaries who control the entire runtime (e.g., can edit Python objects at will) are
**out of scope** for this prototype; the engine runs in a cooperative environment.

## Current Defenses and Invariants

### 1. Treasury access control

- **Mechanism**
  - `treasury_spend` enforces that the initiator:
    - Is a current member of the society; and
    - Holds an active treasurer role represented as a `web4:hasRole` context edge.
  - If checks fail, a `treasury_spend_rejected` event is emitted and no ATP is deducted.
- **Intended invariants**
  - Only current members with the treasurer role can reduce `Society.treasury["ATP"]`.
  - Unauthorized spend attempts are logged with MRH and R6 context.

### 2. MRH-aware local policy (suspicious treasury behavior)

- **Mechanism**
  - Recent `treasury_spend` events with suspicious reasons are aggregated per-agent.
  - Agent trust is reduced by a fixed delta per suspicious event.
  - A helper maps suspicious-count to MRH-like quality bands
    (e.g., `medium`, `high`, `critical`) and converts this to a trust threshold.
  - Treasurer role and membership are revoked only if:
    - Suspicious count is above a fixed count threshold; **and**
    - The agent's T3 composite is below the MRH-derived threshold.
- **Intended invariants**
  - Low-stakes anomalies do not immediately revoke roles.
  - Repeated suspicious behavior in a high-quality context will eventually
    remove treasury authority and membership.

### 3. MRH-aware cross-society policy

- **Mechanism**
  - Federation relationships are inferred from `web4:federatesWith` context edges.
  - For each pair of federated societies A (source) and B (neighbor), B's
    composite trust is compared to thresholds derived from MRH-like quality bands
    (e.g., `high` for throttle, `critical` for quarantine).
  - If trust falls below these thresholds, A emits `federation_throttle` and/or
    `quarantine_request` events, with constraints logging the chosen threshold
    and quality band.
- **Intended invariants**
  - Very low-trust neighbors are surfaced via explicit throttle/quarantine events.
  - The policy decisions are traceable: logs include trust, threshold, and quality.

### 4. Microchain structure

- **Mechanism**
  - Each society maintains an in-memory microchain:
    - Headers include `index`, `society_lct`, `previous_hash`, `timestamp`.
    - `header_hash` is a deterministic SHA-256 over the header JSON.
    - Blocks carry `events` and a `signature` field (stub until hardware-backed).
  - `verify_chain_structure` recomputes header hashes and checks previous-hash chaining.
- **Intended invariants**
  - Within a single process, code that appends blocks via the provided helpers
    maintains a consistent hash-chain.
  - External verifiers can detect accidental structural corruption of blocks.

### 5. Hardware binding MVP

- **Mechanism**
  - `hardware_fingerprint` is stored on the root society.
  - The hardware-bound bootstrap path derives the root `society_lct` from a
    `HardwareIdentity` and records the same `hardware_fingerprint` in the genesis event.
  - `verify_hardware_binding` checks:
    - `hardware_fingerprint` is present on the society.
    - The first block exists and has a `genesis` event.
    - The genesis event's `hardware_fingerprint` matches the society's.
- **Intended invariants**
  - The genesis block for a hardware-bound society claims a specific
    `hardware_fingerprint` and that claim is consistent across metadata and events.
  - External verifiers can distinguish hardware-bound societies (even with stub
    signers) from purely synthetic ones that omit this metadata.

## Known Limitations and Non-Goals (v0)

- **In-memory only**
  - Chains live in process memory; there is no persistence layer, no replay
    protection, and no secure storage.
- **Stub signatures**
  - Block `signature` fields are placeholders; no real key material or signature
    verification is wired up yet.
- **Weak adversary model**
  - Attackers who can modify the running Python process (e.g., change object
    fields, bypass helpers) are out of scope for this prototype.
- **Coarse MRH / trust heuristics**
  - MRH quality bands and trust deltas are simple heuristics tuned for demos,
    not empirically validated or derived from first principles.
- **No network federation**
  - Federation edges and cross-society policies operate entirely within a single
  - process; there is no signed gossip or cross-machine consistency protocol.

## How to Evaluate Fairly

- Treat this engine as a **research prototype and teaching tool** for:
  - Expressing Web4-style societies, trust tensors, and MRH-aware policies.
  - Exploring how microchains and minimal hardware binding might work.
- Do **not** treat this as:
  - A production security system.
  - A drop-in replacement for real-world key management, consensus, or
    federation infrastructure.

Use this document as a snapshot of current intent and assumptions when designing
experiments, demos, or future hardening passes.
