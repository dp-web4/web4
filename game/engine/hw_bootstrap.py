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
import hashlib
import json
import importlib
import os

from .models import World, Society, Agent, make_society_lct, make_agent_lct
from .signing import get_block_signer


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
    # First, try to load a per-machine provider module if configured.
    provider_path = os.getenv("WEB4_HW_IDENTITY_PROVIDER")
    if provider_path:
        try:
            module = importlib.import_module(provider_path)
            provider_func = getattr(module, "get_hardware_identity", None)
            if callable(provider_func):
                identity = provider_func()
                if isinstance(identity, HardwareIdentity):
                    return identity
        except Exception as exc:  # Best-effort only, fall back to stub
            print(f"[web4/game] WEB4_HW_IDENTITY_PROVIDER failed ({exc!r}), falling back to stub identity")

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
        hardware_fingerprint=hw_identity.fingerprint,
    )
    world.add_society(root_society)

    # Founder agent (human-controlled)
    founder_lct = make_agent_lct("founder")
    founder_roles = [
        "role:web4:founder",
        "role:web4:auditor",
        "role:web4:law_oracle",
    ]
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
    )
    world.add_agent(founder)
    root_society.members.append(founder_lct)

    # Minimal genesis block (v0): hash-chained header plus stub signature.
    header = {
        "index": 0,
        "society_lct": society_lct,
        "previous_hash": None,
        "timestamp": 0.0,
    }
    header_json = json.dumps(header, sort_keys=True, separators=(",", ":"))
    header_hash = hashlib.sha256(header_json.encode("utf-8")).hexdigest()

    signer = get_block_signer()
    signature = signer.sign_block_header(header)

    genesis_block = {
        **header,
        "events": [
            {
                "type": "genesis",
                "society_lct": society_lct,
                "hardware_fingerprint": hw_identity.fingerprint,
                "founder_lct": founder_lct,
                "roles": founder_roles,
                "policies": root_society.policies,
            }
        ],
        "header_hash": header_hash,
        # TODO: replace with real hardware-backed signature from hw_identity.
        "signature": signature,
    }
    root_society.blocks.append(genesis_block)
    root_society.last_block_time = 0.0

    return BootstrapResult(
        hardware_identity=hw_identity,
        society_lct=society_lct,
        world=world,
    )
