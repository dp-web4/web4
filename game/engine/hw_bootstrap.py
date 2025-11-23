from __future__ import annotations

"""Hardware-bound society bootstrap interfaces (v0, stub).

This module defines minimal, implementation-agnostic interfaces for
bootstrapping a hardware-bound Web4 society and initializing a game
`World` with a root `Society` derived from a hardware identity.

Concrete TPM / HSM / enclave integrations should implement the
get_hardware_identity() and signing logic elsewhere and plug into this
interface.
"""

from dataclasses import dataclass
from typing import Dict, Any

from .models import World, Society, Agent, make_society_lct, make_agent_lct


@dataclass
class HardwareIdentity:
    """Descriptor for a hardware-bound identity (v0 stub)."""

    public_key: str
    fingerprint: str
    hw_type: str  # e.g. "tpm", "hsm", "enclave", or "stub"


@dataclass
class BootstrapResult:
    """Result of bootstrapping a hardware-bound society world."""

    hardware_identity: HardwareIdentity
    society_lct: str
    world: World


def get_hardware_identity() -> HardwareIdentity:
    """Obtain a hardware-bound identity.

    v0 stub: returns a deterministic, software-only identity. Future
    work can replace this with real TPM / HSM / enclave bindings.
    """

    # TODO: replace with real hardware key discovery / creation.
    return HardwareIdentity(
        public_key="stub-public-key",
        fingerprint="stub-fingerprint",
        hw_type="stub",
    )


def derive_society_lct(hw_identity: HardwareIdentity) -> str:
    """Derive a society LCT from the hardware identity.

    In v0 this is a simple placeholder using the fingerprint. Future
    work should align this with the formal LCT specification for
    key-derived identifiers.
    """

    local_id = f"hw-{hw_identity.fingerprint}"
    return make_society_lct(local_id)


def bootstrap_hardware_bound_world() -> BootstrapResult:
    """Create a hardware-bound world with a root society and founder agent.

    This is the hardware-aware analogue of bootstrap_home_society_world().
    It keeps behavior minimal while ensuring that the root society LCT
    is derived from a hardware identity.
    """

    hw_identity = get_hardware_identity()
    society_lct = derive_society_lct(hw_identity)

    world = World()

    # Root society
    root_society = Society(
        society_lct=society_lct,
        name="Hardware-Bound Society",
        treasury={"ATP": 1000.0},
        members=[],
        policies={
            "admission": "open",  # placeholder
            "governance": "simple-majority",
        },
    )
    world.add_society(root_society)

    # Founder agent (human-controlled)
    founder_lct = make_agent_lct("founder")
    founder = Agent(
        agent_lct=founder_lct,
        name="Founder",
        trust_axes={
            "T3": {
                "talent": 0.5,
                "training": 0.5,
                "temperament": 0.5,
                "composite": 0.5,
            }
        },
        capabilities={"witness_general": 0.6},
        resources={"ATP": 200.0},
        memberships=[society_lct],
        roles=[
            "role:web4:founder",
            "role:web4:auditor",
            "role:web4:law_oracle",
        ],
    )
    world.add_agent(founder)
    root_society.members.append(founder_lct)

    # Minimal genesis block (unsigned, v0 stub)
    genesis_block = {
        "index": 0,
        "society_lct": society_lct,
        "timestamp": 0.0,
        "events": [
            {
                "type": "genesis",
                "society_lct": society_lct,
                "hardware_fingerprint": hw_identity.fingerprint,
                "founder_lct": founder_lct,
                "roles": founder.roles,
                "policies": root_society.policies,
            }
        ],
        # TODO: add previous_hash, block_hash, and hardware-backed signatures.
    }
    root_society.blocks.append(genesis_block)
    root_society.last_block_time = 0.0

    return BootstrapResult(
        hardware_identity=hw_identity,
        society_lct=society_lct,
        world=world,
    )
