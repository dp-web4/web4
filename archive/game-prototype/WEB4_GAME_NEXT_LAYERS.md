# Web4 Game – Next Layers Overview (v0)

This document summarizes the new layers added on top of the core game
engine to move toward emergent behavior and external auditability.

---

## 1. Treasury Layer (engine/treasury.py)

Defines structured treasury events and simple ATP hooks:

- `treasury_spend(world, society, treasury_lct, initiator_lct, amount, reason, mrh=None)`
  - Decreases `society.treasury["ATP"]` (clamped at 0).
  - Appends a `treasury_spend` event with:
    - `society_lct`, `treasury_lct`, `initiator_lct`, `amount`.
    - `atp_before`, `atp_after`.
    - `mrh` profile and R6 envelope (`interaction_type="treasury_spend"`).

- `treasury_deposit(world, society, treasury_lct, source_lct, amount, reason, mrh=None)`
  - Increases `society.treasury["ATP"]`.
  - Emits `treasury_deposit` events with MRH + R6 metadata.

- `treasury_transfer(world, society, from_lct, to_lct, amount, reason, mrh=None)`
  - Records a logical transfer between LCTs within/related to the society.
  - Does not yet adjust per-agent balances (v0), but appends a
    `treasury_transfer` event with MRH + R6.

All treasury events are appended to `society.pending_events` and will be
sealed into microblocks with hashes and stub signatures.

---

## 2. Membership Layer (engine/membership.py)

Defines membership lifecycle events and MRH/LCT context updates:

- `membership_join(world, society, agent_lct, reason, mrh=None)`
  - Ensures `agent_lct` is in `society.members`.
  - Emits `membership_join` with MRH + R6.
  - Adds context edge: `agent_lct --web4:memberOf--> society_lct`.

- `membership_leave(world, society, agent_lct, reason, mrh=None)`
  - Removes `agent_lct` from `society.members` (if present).
  - Emits `membership_leave` with MRH + R6.
  - Adds context edge: `agent_lct --web4:wasMemberOf--> society_lct`.

- `membership_revocation(world, society, agent_lct, reason, mrh=None)`
  - Removes `agent_lct` from `society.members` (if present).
  - Emits `membership_revocation` with MRH + R6.
  - Adds context edge: `agent_lct --web4:membershipRevokedBy--> society_lct`.

These events and edges provide a clear, auditable view of membership
history for each society.

---

## 3. Chain Verification Layer (engine/verify.py)

Provides basic helpers for external or test-time verification of a
society's microchain:

- `verify_chain_structure(society)`
  - Recomputes `header_hash` for each block from:
    - `index`, `society_lct`, `previous_hash`, `timestamp`.
  - Checks that:
    - Stored `header_hash` matches recomputed one.
    - `previous_hash` forms a consistent hash-chain.
  - Returns:
    - `{"valid": bool, "errors": [...], "block_count": N}`.

- `verify_stub_signatures(society)`
  - v0 placeholder that only checks presence of `signature` fields.
  - Returns the same `valid/errors/block_count` structure.

Future work will replace stub signature checks with real public-key
verification against a `HardwareIdentity` or TPM-backed key.

---

## 4. Integration Points

- Treasury events can be used by scenarios and policies to:
  - Track spending patterns.
  - Trigger audits and role revocations when thresholds are exceeded.

- Membership events provide:
  - A clean history of who joined/left/was expelled from each society.
  - Inputs for trust / policy modules (e.g., repeated expulsions lower
    cross-society trust).

- Verification helpers give external auditors, peer societies, or test
harnesses a way to:
  - Validate the structural integrity of the microchain.
  - Prepare for future signature-based attestation.

These layers push the game closer to the "complexity threshold" needed
for meaningful emergent behavior, while keeping things modular and
adjustable as the Web4 spec and experiments evolve.
