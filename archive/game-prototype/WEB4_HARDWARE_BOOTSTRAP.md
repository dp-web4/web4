# Web4 Hardware-Bound Society Bootstrap (Draft)

**Status:** Draft, exploratory

This document sketches an interface for bootstrapping a **hardware-bound Web4 society** on a local machine and exposing its root LCT to the wider Web4 world.

It is intentionally minimal and implementation-agnostic (TPM / secure enclave / HSM, etc.).

---

## 1. Goals

- Allow a human to instantiate a **local society** that is:
  - Bound to a **hardware root of trust** (e.g., TPM key).
  - Identified externally by a **root society LCT**.
- Treat this society as a **first-class Web4 entity**:
  - Runs its own per-society blockchain (microchain).
  - Hosts agents (human and AI) with roles (auditor, treasurer, law oracle, etc.).
  - Exposes an auditable history to external auditors and peer societies.
- Provide simple, safe defaults for:
  - Society roles.
  - Block intervals and microblocks.
  - Audit hooks and R6 interaction envelopes.
- Keep the system **open-ended and emergent**:
  - No hard-coded ideology or behavior.
  - Encourage “anti-coherent” attempts so the emerging immune system can react.

---

## 2. High-Level Flow

1. **Hardware Root Setup**
   - Detect or create a hardware-backed keypair (e.g. TPM-resident).
   - Derive a **hardware identity fingerprint** from the public key.

2. **Root LCT Derivation**
   - Use the LCT specification to derive a **society LCT** from the hardware-bound public key.
   - Example shape (not final):
     - `lct:web4:society:{hash(hw_public_key || domain_params)}`.

3. **Society Genesis**
   - Create a `Society` object in the game/engine with:
     - `society_lct` (derived as above).
     - Initial treasury and policy defaults.
     - Empty or minimal membership.
   - Create a **founder agent** (human-controlled) with:
     - `agent_lct` (derived from a user keypair, not necessarily the same as hardware root).
     - Roles such as `role:web4:founder`, `role:web4:auditor`, `role:web4:law_oracle`.

4. **Genesis Block**
   - Write a genesis block to the society microchain containing:
     - Root society LCT.
     - Hardware key fingerprint.
     - Founder agent and roles.
     - Initial policies.
   - Sign the block header with the **hardware-bound key** (future work).

5. **Ongoing Operation**
   - Use the existing game engine:
     - Per-tick MRH/LCT context updates.
     - Per-society microblocks driven by `pending_events`.
     - R6-wrapped audit events.
   - Optionally expose an API for external auditors/peers to:
     - Fetch chain headers and blocks.
     - Verify signatures and structure.

---

## 3. Interface Abstraction (Engine-Level)

We introduce a minimal interface in the game engine to **decouple** hardware details from the simulation logic.

### 3.1 Types

- `HardwareIdentity`
  - Hardware-bound identity descriptor, e.g.:

    ```python
    {
        "public_key": "...",        # serialized public key
        "fingerprint": "...",       # stable identifier derived from key
        "hw_type": "tpm|hsm|enclave",  # implementation hint
    }
    ```

- `BootstrapResult`
  - Combined result of hardware bootstrap and game-world initialization:

    ```python
    {
        "hardware_identity": HardwareIdentity,
        "society_lct": str,
        "world": World,  # a game.engine World instance
    }
    ```

### 3.2 Engine Interface

At the engine level we define (see `engine/hw_bootstrap.py`):

- `get_hardware_identity() -> HardwareIdentity`
  - Abstracts detection/creation of a hardware-resident key.
  - In v0, this can be stubbed with a software key or static fingerprint.

- `derive_society_lct(hw_identity: HardwareIdentity) -> str`
  - Maps `hw_identity["public_key"]` (and optional params) to a canonical LCT using the public LCT spec.

- `bootstrap_hardware_bound_world() -> BootstrapResult`
  - High-level helper that:
    - Obtains `HardwareIdentity`.
    - Derives `society_lct`.
    - Constructs a `World` and a `Society` with that LCT.
    - Creates a founder `Agent` with appropriate roles.
    - Writes a **genesis block** into `Society.blocks`.

This keeps our game logic hardware-agnostic while providing explicit hooks for real TPM bindings later.

---

## 4. Relation to the Existing Game Engine

- The existing `bootstrap_home_society_world()` in `engine/scenarios.py` is a purely **software** bootstrap.
- `bootstrap_hardware_bound_world()` would be a **hardware-aware** variant that:
  - Reuses the same `World`, `Society`, and `Agent` structures.
  - Ensures the root `society_lct` and genesis block are anchored in hardware identity.
- Both flows can coexist:
  - Developers can use pure-software worlds for rapid iteration.
  - Users can use the hardware-bound bootstrap kit for real societies.

---

## 5. Future Work

- Define a concrete mapping from hardware public keys to LCT identifiers that matches the Web4 LCT specification.
- Implement TPM / secure enclave bindings in a separate module or repository, keeping the public `web4` repo generic.
- Add signature and hash fields to society blocks and integrate hardware signing.
- Extend audit and R6 envelopes to include hardware attestation where appropriate.
- Provide a small CLI and/or GUI for non-technical users to run the hardware-bound bootstrap flow.
