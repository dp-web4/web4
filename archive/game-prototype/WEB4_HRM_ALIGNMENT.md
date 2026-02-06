# Web4 `/game` ↔ HRM/SAGE Federation Alignment (v0)

This document sketches a concrete alignment between the **Web4 game engine**
(`web4/game/`) and the **HRM/SAGE federation layer** (`HRM/sage/federation/`).

It is a **research-stage integration note**, not a binding spec. The goal is to
make it easy to:

- Wire Web4 game societies to real SAGE federation identities.
- Use SAGE federation crypto (Ed25519) to sign/verify Web4 microchains.
- Treat Web4 cross-society policies as clients of SAGE federation trust.

## 1. Identity Mapping

### 1.1 Web4 societies and agents

- Web4 `/game` identities (simplified):
  - `Society.society_lct: str` – logical society identifier.
  - `Agent.agent_lct: str` – logical agent identifier.
  - `Society.hardware_fingerprint: str | None` – MVP hardware anchor.
  - `engine.hw_bootstrap.HardwareIdentity`:
    - `public_key: str` (placeholder)
    - `fingerprint: str`
    - `hw_type: str`

### 1.2 SAGE federation identities and keys

From `HRM/sage/federation/federation_types.py` and `federation_crypto.py`:

- `FederationIdentity`:
  - `lct_id: str` – hardware-anchored identity (e.g. `"thor_sage_lct"`).
  - `platform_name: str` – human-readable label.
  - `hardware_spec: HardwareSpec` – RAM/GPU/power.
  - `max_mrh_horizon: MRHProfile` – MRH capability.
  - `public_key: bytes` – Ed25519 public key (Phase 2).
  - `stake: Optional[IdentityStake]` – ATP stake for Sybil defense.
  - `reputation_score: float` – platform trust.

- `FederationKeyPair`:
  - `generate(platform_name: str, lct_id: str) -> FederationKeyPair`.
  - `sign(message: bytes) -> bytes` / `verify(message, signature) -> bool`.
  - Serialization helpers for public/private keys.

### 1.3 Proposed mapping

- A **hardware-bound Web4 root society** SHOULD correspond to a
  **SAGE FederationIdentity**:
  - `Society.society_lct == FederationIdentity.lct_id` (or an injective
    mapping `society_lct -> lct_id`).
  - `Society.hardware_fingerprint` is a stable label for the hardware that
    holds `FederationKeyPair.private_key`.
  - `HardwareIdentity.public_key` SHOULD carry the same bytes as
    `FederationIdentity.public_key`.

- In other words:

  > "This Web4 society's microchain is signed by the same Ed25519 key that
  > identifies this SAGE federation platform."

## 2. Block Signing and Verification

### 2.1 Current Web4 block structure

From `web4/game/engine/sim_loop.py` and `engine/hw_bootstrap.py`:

- Block header:
  - `index: int`
  - `society_lct: str`
  - `previous_hash: str | None`
  - `timestamp: float`
- Hash:
  - `header_hash: str = sha256(json.dumps(header, sort_keys=True))`.
- Body:
  - `events: list[dict]`
  - `signature: str` – **stub** (`"stub-signature"` or `"stub-hw-genesis-signature"`).

### 2.2 SAGE crypto interface

From `federation_crypto.py`:

- `FederationKeyPair.sign(message: bytes) -> bytes`.
- `FederationCrypto.verify_signature(public_key_bytes, message, signature) -> bool`.
- `SignatureRegistry` keeps track of platform public keys and verifies
  signatures on tasks/proofs/attestations.

### 2.3 Suggested signer/verifier interface for `/game`

Define a minimal interface (conceptual):

```python
class BlockSigner(Protocol):
    def sign_block_header(self, header: dict) -> bytes: ...

class BlockVerifier(Protocol):
    def verify_block_signature(self, header: dict, signature: bytes, *,
                               public_key: bytes) -> bool: ...
```

Concrete SAGE-backed implementation (sketch):

```python
from sage.federation.federation_crypto import FederationKeyPair, FederationCrypto

class SageBlockSigner:
    def __init__(self, keypair: FederationKeyPair):
        self.keypair = keypair

    def sign_block_header(self, header: dict) -> bytes:
        header_json = json.dumps(header, sort_keys=True, separators=(",", ":"))
        return self.keypair.sign(header_json.encode("utf-8"))

class SageBlockVerifier:
    def verify_block_signature(self, header: dict, signature: bytes, *,
                               public_key: bytes) -> bool:
        header_json = json.dumps(header, sort_keys=True, separators=(",", ":"))
        header_bytes = header_json.encode("utf-8")
        return FederationCrypto.verify_signature(public_key, header_bytes, signature)
```

### 2.4 Where to plug this into `/game`

- **Genesis block** (`engine/hw_bootstrap.bootstrap_hardware_bound_world`):
  - Replace `"stub-hw-genesis-signature"` with a real Ed25519 signature from
    `SageBlockSigner` using a `FederationKeyPair` tied to this hardware.

- **Microblocks** (`engine/sim_loop._society_step`):
  - Replace `"stub-signature"` with:
    - `signature: bytes` from `SageBlockSigner.sign_block_header(header)`.
  - Optionally store `public_key` bytes on `Society` or in genesis metadata for
    later verification.

- **Verification** (`engine/verify.py`):
  - Extend `verify_stub_signatures` into a real
    `verify_block_signatures(society, registry: SignatureRegistry)` that:
    - Looks up `public_key` via SAGE's `SignatureRegistry` based on
      `society.society_lct` / `platform_name`.
    - Recomputes header JSON and calls `FederationCrypto.verify_signature`.

## 3. Trust and Policy Alignment

### 3.1 SAGE federation trust

From `FEDERATION_TRUST_PROTOCOL.md`, `federation_types.py`, `federation_router.py`:

- Trust is driven by **witnessed execution quality**:
  - `FederationIdentity.reputation_score: float`.
  - Execution history via `ExecutionRecord`.
  - Challenge system + witness attestations adjust reputation.

- Routing decisions use thresholds (e.g. `reputation_score >= 0.6`).

### 3.2 Web4 `/game` trust and policies

From `web4/game/engine/policy.py` and `engine/cross_society_policy.py`:

- Agent-level `T3` composite trust with MRH-aware thresholds for:
  - Suspicious treasury behavior → role/membership revocation.
- Society-level `T3` composite trust for:
  - Cross-society `federation_throttle` / `quarantine_request` decisions.
  - Thresholds derived from MRH quality bands via `quality_level_to_veracity`.

### 3.3 Proposed cross-layer flows

- **Federation → Web4 game**:
  - Use `FederationIdentity.reputation_score` as an **input** when initializing
    or updating society-level trust tensors in `/game`:
    - E.g., map reputation into the society's `T3.composite` or a separate
      `"FED"` trust axis.
  - Use federation challenge / evasion stats as additional MRH context for
    cross-society policies.

- **Web4 game → Federation**:
  - Selected `/game` events (e.g. `federation_throttle`, `quarantine_request`,
    repeated suspicious treasury behavior) can be surfaced as **inputs into the
    SAGE federation trust model**, for example by:
    - Recording them as `ExecutionRecord`-like events with downgraded
      `execution_quality`.
    - Feeding them into a SAGE-side compliance validator.

The key design principle:

> Both layers use **scalar trust under context-dependent thresholds**.
> SAGE's reputation_score and Web4's T3 composite trust should be
> treated as different, but mappable, summary statistics.

## 4. Event Bridge Sketch

To make the relationship concrete:

- Define a simple event schema that Web4 `/game` can emit and SAGE can ingest:

```jsonc
{
  "type": "web4_policy_event",
  "society_lct": "lct:web4:society:...",
  "event_type": "federation_throttle" | "quarantine_request" | "treasury_spend_rejected",
  "trust": 0.73,
  "threshold": 0.9,
  "quality_band": "high",
  "timestamp": 123456.0
}
```

- A small adapter in HRM could:
  - Map these into SAGE `ExecutionRecord` or dedicated compliance events.
  - Adjust `FederationIdentity.reputation_score` or stake status accordingly.

## 5. Hardware Binding and Identity Stakes

### 5.1 Hardware binding in `/game`

From `THREAT_MODEL_GAME.md` and `engine/hw_bootstrap.py`:

- `Society.hardware_fingerprint` tags a root society with a hardware anchor.
- Genesis block records the same `hardware_fingerprint`.
- `verify_hardware_binding` checks consistency of this claim.

### 5.2 Identity stakes in SAGE

From `federation_types.py` and `FEDERATION_TRUST_PROTOCOL.md`:

- `IdentityStake` bonds ATP to `FederationIdentity.lct_id`.
- Stake is slashed for malicious behavior; locked/unlockable states.

### 5.3 Alignment suggestion

- For a hardware-bound Web4 root society that also participates in SAGE
  federation:
  - `Society.society_lct == FederationIdentity.lct_id`.
  - `Society.hardware_fingerprint` should be documented alongside
    `FederationIdentity.hardware_spec` as the **physical instantiation** of
    that identity.
  - Stake metadata (`IdentityStake`) can be mirrored or referenced in `/game`
    if the simulation needs to reason about economic penalties.

This alignment allows:

- `/game` to treat SAGE stakes as **ground truth for identity legitimacy**.
- SAGE to treat `/game` microchains as **signed local histories** anchored in
  the same hardware and keys.

## 6. Next-Step Implementation Hooks

This doc is intentionally light on code changes; it is meant to guide them.
Near-term implementation steps, if/when desired:

1. **Introduce a BlockSigner/Verifier abstraction in `/game`**
   - Refactor `sim_loop._society_step` and `hw_bootstrap` to call a signer
     object instead of hard-coding stub signatures.

2. **Provide a SAGE-backed signer implementation in HRM**
   - Implement `SageBlockSigner` / `SageBlockVerifier` using
     `FederationKeyPair` and `FederationCrypto`.
   - Optionally expose them via a small Python API that `/web4/game` imports
     when running in a unified environment.

3. **Add a minimal event exporter**
   - In `/web4/game`, add a helper that converts selected policy outcomes into
     a JSON event stream consumable by SAGE.

4. **Update threat models**
   - When the integration is live, update both:
     - `/web4/game/THREAT_MODEL_GAME.md`.
     - `HRM/sage/docs/FEDERATION_INTEGRATION_GUIDE.md`.

This keeps the integration grounded while leaving room for evolution as both
systems mature.
