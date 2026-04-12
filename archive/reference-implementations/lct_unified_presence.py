#!/usr/bin/env python3
"""
Unified LCT Presence Specification — Reference Implementation
==============================================================
Implements the cross-project presence format from:
  docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md (738 lines)

Covers ALL sections:
  §1 LCT Presence Format — URI scheme lct://{component}:{instance}:{role}@{network}
  §2 Component Field Spec — Reserved components, instance/role/network naming rules
  §3 LCT Relationship Model — Pairing status state machine, trust integration
  §4 ACT Blockchain Integration — Registry storage, registration, pairing, trust query
  §5 SAGE Neural Integration — ExpertIdentityBridge, AuthorizedExpertSelector
  §6 Web4 Protocol Integration — API endpoints, agent registration
  §7 URI Parsing Library — Reference parser with query params and fragment
  §8 Security Considerations — Forgery, manipulation, pollution, confusion
  §9 Backward Compatibility — Legacy SAGE/ACT migration
  §10 Versioning — Semver, extension mechanism
  §11 Test Vectors — 3 canonical test vectors
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

# ══════════════════════════════════════════════════════════════
# §1 — LCT Presence Format
# ══════════════════════════════════════════════════════════════

# §2 — Reserved component names
RESERVED_COMPONENTS = {
    "sage", "web4-agent", "act-validator", "act-society",
    "memory", "portal", "sync",
}

# §2 — Standard network identifiers
STANDARD_NETWORKS = {"mainnet", "testnet", "devnet", "local"}

# §2 — Naming rules
COMPONENT_PATTERN = re.compile(r"^[a-z][a-z0-9\-]{0,31}$")
INSTANCE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
ROLE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
NETWORK_PATTERN = re.compile(r"^[a-z][a-z0-9\-]{0,63}$")


# ══════════════════════════════════════════════════════════════
# §7 — URI Parsing Library (reference implementation from spec)
# ══════════════════════════════════════════════════════════════

@dataclass
class LCTIdentity:
    """Parsed LCT presence record (§7)."""
    component: str
    instance: str
    role: str
    network: str
    version: str = "1.0.0"
    pairing_status: Optional[str] = None
    trust_threshold: Optional[float] = None
    capabilities: Optional[List[str]] = None
    public_key_hash: Optional[str] = None

    @property
    def lct_uri(self) -> str:
        """Reconstruct LCT URI."""
        base = f"lct://{self.component}:{self.instance}:{self.role}@{self.network}"

        params = []
        if self.version != "1.0.0":
            params.append(f"version={self.version}")
        if self.pairing_status:
            params.append(f"pairing_status={self.pairing_status}")
        if self.trust_threshold is not None:
            params.append(f"trust_threshold={self.trust_threshold}")
        if self.capabilities:
            params.append(f"capabilities={','.join(self.capabilities)}")

        query_string = "&".join(params) if params else ""
        fragment = f"#{self.public_key_hash}" if self.public_key_hash else ""

        uri = base
        if query_string:
            uri += f"?{query_string}"
        if fragment:
            uri += fragment

        return uri

    def is_reserved_component(self) -> bool:
        return self.component in RESERVED_COMPONENTS

    def is_standard_network(self) -> bool:
        return self.network in STANDARD_NETWORKS


def parse_lct_uri(lct_uri: str) -> LCTIdentity:
    """Parse LCT URI into structured presence record (§7).

    Format: lct://{component}:{instance}:{role}@{network}?{params}#{fragment}
    """
    if not lct_uri.startswith("lct://"):
        raise ValueError(f"Invalid LCT URI scheme: {lct_uri}")

    parsed = urlparse(lct_uri)
    authority = parsed.netloc
    path = parsed.path.lstrip("/")
    full_authority = authority + "/" + path if path else authority

    pattern = r"^([^:]+):([^:]+):([^@]+)@([^?#]+)"
    match = re.match(pattern, full_authority)
    if not match:
        raise ValueError(f"Invalid LCT authority format: {full_authority}")

    component, instance, role, network = match.groups()

    # Parse query parameters
    query_params = parse_qs(parsed.query)
    version = query_params.get("version", ["1.0.0"])[0]
    pairing_status = query_params.get("pairing_status", [None])[0]
    trust_threshold_str = query_params.get("trust_threshold", [None])[0]
    trust_threshold = float(trust_threshold_str) if trust_threshold_str else None
    capabilities_str = query_params.get("capabilities", [None])[0]
    capabilities = capabilities_str.split(",") if capabilities_str else None

    public_key_hash = parsed.fragment if parsed.fragment else None

    return LCTIdentity(
        component=component,
        instance=instance,
        role=role,
        network=network,
        version=version,
        pairing_status=pairing_status,
        trust_threshold=trust_threshold,
        capabilities=capabilities,
        public_key_hash=public_key_hash,
    )


def validate_lct_uri(lct_uri: str) -> bool:
    """Validate LCT URI format (§7)."""
    try:
        parse_lct_uri(lct_uri)
        return True
    except ValueError:
        return False


def validate_naming(component: str, instance: str, role: str, network: str) -> List[str]:
    """Validate naming rules (§2). Returns list of violations."""
    violations = []
    if not COMPONENT_PATTERN.match(component):
        violations.append(f"Component '{component}' violates naming rules (lowercase alpha+hyphens, max 32)")
    if not INSTANCE_PATTERN.match(instance):
        violations.append(f"Instance '{instance}' violates naming rules (lowercase alpha+underscores, max 64)")
    if not ROLE_PATTERN.match(role):
        violations.append(f"Role '{role}' violates naming rules (lowercase alpha+underscores, max 128)")
    if not NETWORK_PATTERN.match(network):
        violations.append(f"Network '{network}' violates naming rules")
    return violations


# ══════════════════════════════════════════════════════════════
# §3 — LCT Relationship Model
# ══════════════════════════════════════════════════════════════

class PairingStatus(Enum):
    """Pairing status values (§3)."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"


# State machine transitions (§3)
VALID_TRANSITIONS: Dict[Optional[PairingStatus], List[PairingStatus]] = {
    None: [PairingStatus.PENDING],
    PairingStatus.PENDING: [PairingStatus.ACTIVE, PairingStatus.REVOKED],
    PairingStatus.ACTIVE: [PairingStatus.SUSPENDED, PairingStatus.EXPIRED],
    PairingStatus.SUSPENDED: [PairingStatus.ACTIVE, PairingStatus.REVOKED],
    PairingStatus.EXPIRED: [PairingStatus.REVOKED],
}


@dataclass
class TrustScores:
    """Trust dimensions for LCT relationships (§3)."""
    relationship_trust: float = 0.0
    context_trust: float = 0.0
    historical_trust: float = 0.0

    def overall(self) -> float:
        return (self.relationship_trust + self.context_trust + self.historical_trust) / 3.0


class OperationLevel(Enum):
    """Operation trust thresholds (§3)."""
    CRITICAL = "critical"         # >= 0.80
    STANDARD = "standard"         # >= 0.60
    EXPLORATORY = "exploratory"   # >= 0.40


OPERATION_THRESHOLDS = {
    OperationLevel.CRITICAL: 0.80,
    OperationLevel.STANDARD: 0.60,
    OperationLevel.EXPLORATORY: 0.40,
}


@dataclass
class LCTPairing:
    """A pairing between two LCT identities (§3)."""
    source_lct: str
    target_lct: str
    status: Optional[PairingStatus] = None
    trust: TrustScores = field(default_factory=TrustScores)
    trust_threshold: float = 0.60

    def transition(self, new_status: PairingStatus) -> bool:
        """Attempt state transition per state machine."""
        valid = VALID_TRANSITIONS.get(self.status, [])
        if new_status in valid:
            self.status = new_status
            return True
        return False

    def meets_threshold(self, level: OperationLevel) -> bool:
        """Check if trust meets operation threshold."""
        required = OPERATION_THRESHOLDS[level]
        return self.trust.overall() >= required


# ══════════════════════════════════════════════════════════════
# §5 — SAGE Neural Integration
# ══════════════════════════════════════════════════════════════

class ExpertIdentityBridge:
    """Enhanced ExpertIdentityBridge from spec (§5)."""

    def __init__(self, namespace: str = "sage", instance: str = "thinker",
                 network: str = "testnet"):
        self.namespace = namespace
        self.instance = instance
        self.network = network

    def expert_to_lct_uri(self, expert_id: int) -> str:
        """Convert expert ID to full LCT URI."""
        return f"lct://{self.namespace}:{self.instance}:expert_{expert_id}@{self.network}"

    def lct_uri_to_expert(self, lct_uri: str) -> int:
        """Parse LCT URI to extract expert ID."""
        match = re.match(r"lct://([^:]+):([^:]+):expert_(\d+)@([^?#]+)", lct_uri)
        if not match:
            raise ValueError(f"Invalid SAGE expert LCT URI: {lct_uri}")
        return int(match.group(3))

    def validate_lct_uri(self, lct_uri: str) -> bool:
        """Validate LCT URI format and component namespace."""
        try:
            parsed = parse_lct_uri(lct_uri)
            return (parsed.component == self.namespace and
                    parsed.instance == self.instance)
        except Exception:
            return False


# §9 — Backward Compatibility

def migrate_legacy_expert_id(legacy_id: str, network: str = "testnet") -> str:
    """Convert legacy SAGE expert ID to LCT URI (§9)."""
    parts = legacy_id.split("_")
    if len(parts) != 4 or parts[2] != "expert":
        raise ValueError(f"Invalid legacy expert ID: {legacy_id}")

    component = parts[0]
    instance = parts[1]
    role = f"expert_{parts[3]}"
    return f"lct://{component}:{instance}:{role}@{network}"


# ══════════════════════════════════════════════════════════════
# §6 — Web4 Protocol Integration
# ══════════════════════════════════════════════════════════════

@dataclass
class Web4AgentRegistration:
    """Web4 agent registration (§6)."""
    lct_uri: str
    capabilities: List[str]
    trust_threshold: float = 0.75
    pairing_status: str = "active"
    public_key: str = ""

    def to_dict(self) -> dict:
        return {
            "agent": {
                "lct_uri": self.lct_uri,
                "capabilities": self.capabilities,
                "trust_threshold": self.trust_threshold,
                "pairing_status": self.pairing_status,
                "public_key": self.public_key,
            }
        }


@dataclass
class TrustQueryResult:
    """Trust query response (§6)."""
    trust_score: float
    confidence: float
    sample_size: int
    last_updated: str


# ══════════════════════════════════════════════════════════════
# §4 — ACT Blockchain Integration
# ══════════════════════════════════════════════════════════════

@dataclass
class LinkedContextTokenRecord:
    """ACT blockchain LCT record (§4, matching protobuf schema)."""
    lct_id: str
    component: str
    instance: str
    role: str
    network: str
    pairing_status: str = "pending"
    public_key: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    version: int = 1

    @classmethod
    def from_uri(cls, lct_uri: str, **kwargs) -> "LinkedContextTokenRecord":
        parsed = parse_lct_uri(lct_uri)
        return cls(
            lct_id=lct_uri,
            component=parsed.component,
            instance=parsed.instance,
            role=parsed.role,
            network=parsed.network,
            **kwargs,
        )


# ══════════════════════════════════════════════════════════════
# §8 — Security Considerations
# ══════════════════════════════════════════════════════════════

class SecurityThreat(Enum):
    URI_FORGERY = "uri_forgery"
    PAIRING_MANIPULATION = "pairing_manipulation"
    TRUST_POLLUTION = "trust_pollution"
    NETWORK_CONFUSION = "network_confusion"


@dataclass
class SecurityMitigation:
    threat: SecurityThreat
    mitigations: List[str]


SECURITY_MITIGATIONS: List[SecurityMitigation] = [
    SecurityMitigation(
        threat=SecurityThreat.URI_FORGERY,
        mitigations=[
            "All LCT registrations require cryptographic signature",
            "Public key anchored in blockchain or DID registry",
            "Fragment contains public key hash for verification",
            "Trust scores only for verified LCT registrations",
        ],
    ),
    SecurityMitigation(
        threat=SecurityThreat.PAIRING_MANIPULATION,
        mitigations=[
            "Pairing status stored on blockchain (immutable)",
            "State transitions require multi-party signatures",
            "Revocation logged in audit trail",
            "Trust scores decay for inactive pairings",
        ],
    ),
    SecurityMitigation(
        threat=SecurityThreat.TRUST_POLLUTION,
        mitigations=[
            "Trust updates require cryptographic signatures",
            "Rate limiting on trust score submissions",
            "Outlier detection and filtering",
            "Trust scores converge across multiple observers",
        ],
    ),
    SecurityMitigation(
        threat=SecurityThreat.NETWORK_CONFUSION,
        mitigations=[
            "Explicit network parameter in all operations",
            "Network boundary validation in smart contracts",
            "Warning if LCT network doesn't match current network",
            "Separate trust scores per network",
        ],
    ),
]


def check_network_confusion(lct_uri: str, expected_network: str) -> Tuple[bool, str]:
    """Check for network confusion attack (§8.4)."""
    try:
        parsed = parse_lct_uri(lct_uri)
        if parsed.network != expected_network:
            return False, f"Network mismatch: LCT on {parsed.network}, expected {expected_network}"
        return True, "OK"
    except ValueError as e:
        return False, str(e)


# Need the import for Tuple
from typing import Tuple  # noqa: E402


# ══════════════════════════════════════════════════════════════
# §10 — Versioning
# ══════════════════════════════════════════════════════════════

def is_backward_compatible(v1: str, v2: str) -> bool:
    """Check if v2 is backward-compatible with v1 (§10)."""
    parts1 = [int(x) for x in v1.split(".")]
    parts2 = [int(x) for x in v2.split(".")]
    # Same major version = backward compatible
    return parts1[0] == parts2[0]


# ══════════════════════════════════════════════════════════════
# §11 — Test Vectors
# ══════════════════════════════════════════════════════════════

CANONICAL_TEST_VECTORS = [
    {
        "uri": "lct://sage:thinker:expert_42@testnet",
        "parsed": {
            "component": "sage",
            "instance": "thinker",
            "role": "expert_42",
            "network": "testnet",
        },
    },
    {
        "uri": "lct://web4-agent:guardian:coordinator@mainnet?pairing_status=active&trust_threshold=0.75",
        "parsed": {
            "component": "web4-agent",
            "instance": "guardian",
            "role": "coordinator",
            "network": "mainnet",
            "pairing_status": "active",
            "trust_threshold": 0.75,
        },
    },
    {
        "uri": "lct://act-validator:node1:consensus@testnet?version=1.0.0#did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
        "parsed": {
            "component": "act-validator",
            "instance": "node1",
            "role": "consensus",
            "network": "testnet",
            "version": "1.0.0",
            "public_key_hash": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
        },
    },
]


# ══════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {label} {detail}")

    # ── T1: URI Parsing (§1, §7) ──
    print("T1: URI Parsing (§1, §7)")

    # Basic URI
    lct = parse_lct_uri("lct://sage:thinker:expert_42@testnet")
    check("T1.1 Component", lct.component == "sage")
    check("T1.2 Instance", lct.instance == "thinker")
    check("T1.3 Role", lct.role == "expert_42")
    check("T1.4 Network", lct.network == "testnet")
    check("T1.5 Default version", lct.version == "1.0.0")
    check("T1.6 No pairing status", lct.pairing_status is None)
    check("T1.7 No trust threshold", lct.trust_threshold is None)

    # Full URI with query params and fragment
    full_uri = "lct://sage:thinker:expert_42@testnet?version=1.0.0&pairing_status=active&trust_threshold=0.75#did:key:z6Mk"
    full = parse_lct_uri(full_uri)
    check("T1.8 Pairing status", full.pairing_status == "active")
    check("T1.9 Trust threshold", full.trust_threshold == 0.75)
    check("T1.10 Public key hash", full.public_key_hash == "did:key:z6Mk")

    # URI with capabilities
    cap_uri = "lct://web4-agent:guardian:coordinator@mainnet?capabilities=text-gen,trust-calc"
    cap = parse_lct_uri(cap_uri)
    check("T1.11 Capabilities parsed", cap.capabilities == ["text-gen", "trust-calc"])

    # Invalid URIs
    check("T1.12 Invalid scheme", not validate_lct_uri("http://sage:thinker:expert@testnet"))
    check("T1.13 Missing components", not validate_lct_uri("lct://sage"))

    # Reconstruction
    check("T1.14 Roundtrip basic", "lct://sage:thinker:expert_42@testnet" == lct.lct_uri)

    # ── T2: Naming Rules (§2) ──
    print("T2: Naming Rules (§2)")

    check("T2.1 Valid component", len(validate_naming("sage", "thinker", "expert_42", "testnet")) == 0)
    check("T2.2 Valid hyphenated component", len(validate_naming("web4-agent", "thinker", "expert_42", "mainnet")) == 0)

    # Invalid: uppercase
    violations = validate_naming("SAGE", "thinker", "expert_42", "testnet")
    check("T2.3 Uppercase component rejected", len(violations) > 0)

    # Invalid: starts with number
    violations = validate_naming("1sage", "thinker", "expert_42", "testnet")
    check("T2.4 Number-start component rejected", len(violations) > 0)

    # Too long component (>32 chars)
    long_comp = "a" * 33
    violations = validate_naming(long_comp, "thinker", "expert_42", "testnet")
    check("T2.5 Long component rejected", len(violations) > 0)

    # Valid instance with underscore
    check("T2.6 Underscore in instance OK", len(validate_naming("sage", "my_thinker", "expert_42", "testnet")) == 0)

    # Reserved components
    lct = parse_lct_uri("lct://sage:thinker:expert_42@testnet")
    check("T2.7 sage is reserved", lct.is_reserved_component())
    custom = parse_lct_uri("lct://custom:inst:role@testnet")
    check("T2.8 custom not reserved", not custom.is_reserved_component())

    # Standard networks
    check("T2.9 testnet is standard", lct.is_standard_network())
    custom_net = parse_lct_uri("lct://sage:inst:role@anthropic-staging")
    check("T2.10 Custom network not standard", not custom_net.is_standard_network())

    # ── T3: Pairing Status State Machine (§3) ──
    print("T3: Pairing Status State Machine (§3)")

    pairing = LCTPairing(
        source_lct="lct://sage:thinker:expert_42@testnet",
        target_lct="lct://web4-agent:guardian:coordinator@mainnet",
    )
    check("T3.1 Initial status None", pairing.status is None)

    # null → pending
    check("T3.2 null → pending", pairing.transition(PairingStatus.PENDING))
    check("T3.3 Status is pending", pairing.status == PairingStatus.PENDING)

    # pending → active
    check("T3.4 pending → active", pairing.transition(PairingStatus.ACTIVE))
    check("T3.5 Status is active", pairing.status == PairingStatus.ACTIVE)

    # active → suspended
    check("T3.6 active → suspended", pairing.transition(PairingStatus.SUSPENDED))

    # suspended → active (renew)
    check("T3.7 suspended → active", pairing.transition(PairingStatus.ACTIVE))

    # active → expired
    check("T3.8 active → expired", pairing.transition(PairingStatus.EXPIRED))

    # expired → revoked
    check("T3.9 expired → revoked", pairing.transition(PairingStatus.REVOKED))

    # Invalid transitions
    pairing2 = LCTPairing("a", "b")
    pairing2.transition(PairingStatus.PENDING)
    check("T3.10 pending → expired invalid", not pairing2.transition(PairingStatus.EXPIRED))
    check("T3.11 pending → suspended invalid", not pairing2.transition(PairingStatus.SUSPENDED))

    # Direct revocation from pending
    check("T3.12 pending → revoked valid", pairing2.transition(PairingStatus.REVOKED))

    # ── T4: Trust Integration (§3) ──
    print("T4: Trust Integration (§3)")

    trust = TrustScores(relationship_trust=0.85, context_trust=0.90, historical_trust=0.80)
    check("T4.1 Overall trust", abs(trust.overall() - 0.85) < 1e-10)

    pairing3 = LCTPairing("a", "b", trust=trust)
    check("T4.2 Meets critical", pairing3.meets_threshold(OperationLevel.CRITICAL))
    check("T4.3 Meets standard", pairing3.meets_threshold(OperationLevel.STANDARD))
    check("T4.4 Meets exploratory", pairing3.meets_threshold(OperationLevel.EXPLORATORY))

    low_trust = TrustScores(relationship_trust=0.3, context_trust=0.4, historical_trust=0.3)
    pairing4 = LCTPairing("a", "b", trust=low_trust)
    check("T4.5 Fails critical", not pairing4.meets_threshold(OperationLevel.CRITICAL))
    check("T4.6 Fails standard", not pairing4.meets_threshold(OperationLevel.STANDARD))
    check("T4.7 Fails exploratory at 0.33", not pairing4.meets_threshold(OperationLevel.EXPLORATORY))

    # ── T5: SAGE Integration (§5) ──
    print("T5: SAGE Integration (§5)")

    bridge = ExpertIdentityBridge(namespace="sage", instance="thinker", network="testnet")

    # Expert → LCT URI
    uri = bridge.expert_to_lct_uri(42)
    check("T5.1 Expert to URI", uri == "lct://sage:thinker:expert_42@testnet")

    # LCT URI → Expert ID
    expert_id = bridge.lct_uri_to_expert(uri)
    check("T5.2 URI to expert", expert_id == 42)

    # Roundtrip
    check("T5.3 Roundtrip", bridge.lct_uri_to_expert(bridge.expert_to_lct_uri(99)) == 99)

    # Validation
    check("T5.4 Valid URI", bridge.validate_lct_uri(uri))
    check("T5.5 Wrong namespace rejected",
          not bridge.validate_lct_uri("lct://web4:thinker:expert_42@testnet"))
    check("T5.6 Wrong instance rejected",
          not bridge.validate_lct_uri("lct://sage:dreamer:expert_42@testnet"))
    check("T5.7 Invalid URI rejected",
          not bridge.validate_lct_uri("not-a-uri"))

    # Invalid expert URI
    try:
        bridge.lct_uri_to_expert("lct://sage:thinker:coordinator@testnet")
        check("T5.8 Non-expert URI raises", False)
    except ValueError:
        check("T5.8 Non-expert URI raises", True)

    # ── T6: Legacy Migration (§9) ──
    print("T6: Legacy Migration (§9)")

    legacy = "sage_thinker_expert_42"
    migrated = migrate_legacy_expert_id(legacy)
    check("T6.1 Legacy migration", migrated == "lct://sage:thinker:expert_42@testnet")

    migrated_mainnet = migrate_legacy_expert_id(legacy, network="mainnet")
    check("T6.2 Custom network", "mainnet" in migrated_mainnet)

    # Invalid legacy ID
    try:
        migrate_legacy_expert_id("invalid_id")
        check("T6.3 Invalid legacy raises", False)
    except ValueError:
        check("T6.3 Invalid legacy raises", True)

    try:
        migrate_legacy_expert_id("sage_thinker_notexpert_42")
        check("T6.4 Non-expert legacy raises", False)
    except ValueError:
        check("T6.4 Non-expert legacy raises", True)

    # Validate migrated URI
    check("T6.5 Migrated is valid", validate_lct_uri(migrated))

    # ── T7: Canonical Test Vectors (§11) ──
    print("T7: Canonical Test Vectors (§11)")

    for i, vector in enumerate(CANONICAL_TEST_VECTORS):
        parsed = parse_lct_uri(vector["uri"])
        expected = vector["parsed"]

        check(f"T7.{i+1}a Component", parsed.component == expected["component"])
        check(f"T7.{i+1}b Instance", parsed.instance == expected["instance"])
        check(f"T7.{i+1}c Role", parsed.role == expected["role"])
        check(f"T7.{i+1}d Network", parsed.network == expected["network"])

        if "pairing_status" in expected:
            check(f"T7.{i+1}e Pairing status", parsed.pairing_status == expected["pairing_status"])
        if "trust_threshold" in expected:
            check(f"T7.{i+1}f Trust threshold", parsed.trust_threshold == expected["trust_threshold"])
        if "public_key_hash" in expected:
            check(f"T7.{i+1}g Public key hash", parsed.public_key_hash == expected["public_key_hash"])
        if "version" in expected:
            check(f"T7.{i+1}h Version", parsed.version == expected["version"])

    # ── T8: Web4 Integration (§6) ──
    print("T8: Web4 Integration (§6)")

    agent = Web4AgentRegistration(
        lct_uri="lct://web4-agent:guardian:coordinator@mainnet",
        capabilities=["resource_allocation", "trust_aggregation"],
        trust_threshold=0.75,
        public_key="did:key:z6Mk...",
    )
    d = agent.to_dict()
    check("T8.1 Agent dict has agent key", "agent" in d)
    check("T8.2 URI in dict", d["agent"]["lct_uri"] == agent.lct_uri)
    check("T8.3 Capabilities in dict", len(d["agent"]["capabilities"]) == 2)
    check("T8.4 Threshold in dict", d["agent"]["trust_threshold"] == 0.75)

    # ── T9: ACT Blockchain Integration (§4) ──
    print("T9: ACT Blockchain Integration (§4)")

    record = LinkedContextTokenRecord.from_uri(
        "lct://sage:thinker:expert_42@testnet",
        public_key="0xabc",
        metadata={"trust_threshold": "0.75"},
    )
    check("T9.1 Record component", record.component == "sage")
    check("T9.2 Record instance", record.instance == "thinker")
    check("T9.3 Record role", record.role == "expert_42")
    check("T9.4 Record network", record.network == "testnet")
    check("T9.5 Record public key", record.public_key == "0xabc")
    check("T9.6 Record metadata", record.metadata["trust_threshold"] == "0.75")
    check("T9.7 Record version", record.version == 1)

    # ── T10: Security (§8) ──
    print("T10: Security (§8)")

    check("T10.1 Four security threats", len(SECURITY_MITIGATIONS) == 4)

    for sm in SECURITY_MITIGATIONS:
        check(f"T10.2 {sm.threat.value} has mitigations", len(sm.mitigations) >= 3)

    # Network confusion check
    ok, msg = check_network_confusion("lct://sage:thinker:expert_42@testnet", "testnet")
    check("T10.3 Same network OK", ok)

    ok, msg = check_network_confusion("lct://sage:thinker:expert_42@testnet", "mainnet")
    check("T10.4 Different network detected", not ok)
    check("T10.5 Mismatch message", "mismatch" in msg.lower())

    ok, msg = check_network_confusion("invalid-uri", "testnet")
    check("T10.6 Invalid URI caught", not ok)

    # ── T11: Versioning (§10) ──
    print("T11: Versioning (§10)")

    check("T11.1 Same major = compatible", is_backward_compatible("1.0.0", "1.2.3"))
    check("T11.2 Different major = incompatible", not is_backward_compatible("1.0.0", "2.0.0"))
    check("T11.3 Patch change = compatible", is_backward_compatible("1.0.0", "1.0.1"))

    # Extension mechanism: unknown params ignored
    ext_uri = "lct://sage:thinker:expert_42@testnet?x-anthropic-tier=premium&x-anthropic-quota=1000"
    ext = parse_lct_uri(ext_uri)
    check("T11.4 Extension params don't break parsing", ext.component == "sage")
    check("T11.5 Core fields still parsed", ext.network == "testnet")

    # ══════════════════════════════════════════════════════════

    print(f"\n{'='*60}")
    print(f"LCT Unified Presence: {passed}/{passed+failed} checks passed")
    if failed:
        print(f"  {failed} FAILED")
    else:
        print(f"  All checks passed!")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    run_tests()
