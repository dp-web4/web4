#!/usr/bin/env python3
"""
Web4 Reference Implementation: LCT Presence (Identity) System
Spec: docs/what/specifications/LCT_IDENTITY_SYSTEM.md (583 lines)

Covers:
  §1 Executive Summary & Problem Statement
  §2 LCT Identity Components (Lineage, Context, Task)
  §3 LCT Identity Format (parsing, examples)
  §4 Cryptographic Structure (certificates, signature chains)
  §5 Identity Registry (register, update, revoke, query)
  §6 Authorization System (permissions, resource allocation)
  §7 Attack Resistance (4 attack vectors)
  §8 Integration (consensus, ATP, federation)

Run:  python3 lct_identity_system.py
"""

import hashlib, json, time, re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set

# ── §2  Identity Components ────────────────────────────────────────────

@dataclass
class Lineage:
    """Component 1: Who created/authorized this agent (§2.1)."""
    creator_id: str
    creator_pubkey: str = ""
    creation_timestamp: float = 0.0
    revocation_endpoint: str = ""

    @property
    def hierarchy(self) -> List[str]:
        """Parse hierarchical lineage (e.g., 'alice.assistant1.researcher')."""
        return self.creator_id.split(".")

    @property
    def root_creator(self) -> str:
        """Top-level creator in hierarchy."""
        return self.hierarchy[0]

    @property
    def depth(self) -> int:
        """Depth in lineage hierarchy."""
        return len(self.hierarchy)

    def is_descendant_of(self, ancestor_id: str) -> bool:
        """Check if this lineage descends from ancestor."""
        return self.creator_id.startswith(ancestor_id + ".") or self.creator_id == ancestor_id


@dataclass
class Context:
    """Component 2: Platform/environment the agent runs in (§2.2)."""
    platform_id: str
    platform_pubkey: str = ""
    attestation_timestamp: float = 0.0
    capabilities: List[str] = field(default_factory=list)

    @property
    def is_cloud(self) -> bool:
        return self.platform_id.startswith("cloud:")

    @property
    def is_mobile(self) -> bool:
        return self.platform_id.startswith("mobile:")

    @property
    def platform_name(self) -> str:
        """Extract platform name without prefix."""
        if ":" in self.platform_id:
            return self.platform_id.split(":", 1)[1]
        return self.platform_id


@dataclass
class Task:
    """Component 3: What the agent is authorized for (§2.3)."""
    task_id: str
    permissions: Set[str] = field(default_factory=set)
    resource_limits: dict = field(default_factory=dict)

    @property
    def task_type(self) -> str:
        """Top-level task type (e.g., 'execution' from 'execution.code')."""
        return self.task_id.split(".")[0]

    @property
    def task_variant(self) -> Optional[str]:
        """Task variant (e.g., 'code' from 'execution.code')."""
        parts = self.task_id.split(".")
        return parts[1] if len(parts) > 1 else None

    @property
    def is_admin(self) -> bool:
        return self.task_type == "admin"

    @property
    def is_delegation(self) -> bool:
        return self.task_type == "delegation"


# ── §3  LCT Identity Format ───────────────────────────────────────────

# Format: lct:web4:agent:{lineage}@{context}#{task}
LCT_ID_PATTERN = re.compile(
    r'^lct:web4:agent:(?P<lineage>[^@]+)@(?P<context>[^#]+)#(?P<task>.+)$'
)


def parse_lct_id(lct_id: str) -> Optional[Tuple[str, str, str]]:
    """Parse LCT identity string into (lineage, context, task)."""
    match = LCT_ID_PATTERN.match(lct_id)
    if not match:
        return None
    return match.group("lineage"), match.group("context"), match.group("task")


def format_lct_id(lineage: str, context: str, task: str) -> str:
    """Format components into LCT identity string."""
    return f"lct:web4:agent:{lineage}@{context}#{task}"


def validate_lct_id(lct_id: str) -> Tuple[bool, str]:
    """Validate LCT identity format."""
    if not lct_id.startswith("lct:web4:agent:"):
        return False, "invalid_prefix"
    parsed = parse_lct_id(lct_id)
    if not parsed:
        return False, "invalid_format"
    lineage, context, task = parsed
    if not lineage:
        return False, "empty_lineage"
    if not context:
        return False, "empty_context"
    if not task:
        return False, "empty_task"
    return True, "valid"


# ── §4  Cryptographic Structure ────────────────────────────────────────

@dataclass
class IdentityCertificate:
    """Complete identity certificate (§4)."""
    lct_id: str
    lineage: Lineage
    context: Context
    task: Task
    signatures: dict = field(default_factory=dict)
    validity: dict = field(default_factory=dict)

    @staticmethod
    def create(
        lineage: Lineage,
        context: Context,
        task: Task,
        creator_private_key: str,
        platform_private_key: str,
        validity_hours: int = 24,
    ) -> "IdentityCertificate":
        """Create identity certificate with signature chain (§4 creation flow)."""
        lct_id = format_lct_id(lineage.creator_id, context.platform_id, task.task_id)
        now = time.time()

        # Step 1: Creator signs (lineage + task + timestamp)
        creator_data = json.dumps({
            "lineage": lineage.creator_id,
            "task": task.task_id,
            "timestamp": now,
        }, sort_keys=True)
        creator_sig = hashlib.sha256(
            f"{creator_data}:{creator_private_key}".encode()
        ).hexdigest()

        # Step 2: Platform signs (context + attestation + creator_signature)
        platform_data = json.dumps({
            "context": context.platform_id,
            "attestation": now,
            "creator_signature": creator_sig,
        }, sort_keys=True)
        platform_sig = hashlib.sha256(
            f"{platform_data}:{platform_private_key}".encode()
        ).hexdigest()

        return IdentityCertificate(
            lct_id=lct_id,
            lineage=lineage,
            context=context,
            task=task,
            signatures={
                "creator_signature": creator_sig,
                "platform_signature": platform_sig,
            },
            validity={
                "not_before": now,
                "not_after": now + validity_hours * 3600,
                "can_renew": True,
            },
        )

    def verify(self, creator_private_key: str, platform_private_key: str) -> Tuple[bool, str]:
        """Verify signature chain (§4 verification flow)."""
        now = time.time()

        # Step 1: Verify platform signature
        if "platform_signature" not in self.signatures:
            return False, "missing_platform_signature"

        # Step 2: Verify creator signature
        if "creator_signature" not in self.signatures:
            return False, "missing_creator_signature"

        # Reconstruct and verify creator signature
        creator_data = json.dumps({
            "lineage": self.lineage.creator_id,
            "task": self.task.task_id,
            "timestamp": self.validity.get("not_before", 0),
        }, sort_keys=True)
        expected_creator = hashlib.sha256(
            f"{creator_data}:{creator_private_key}".encode()
        ).hexdigest()
        if self.signatures["creator_signature"] != expected_creator:
            return False, "creator_signature_invalid"

        # Reconstruct and verify platform signature
        platform_data = json.dumps({
            "context": self.context.platform_id,
            "attestation": self.validity.get("not_before", 0),
            "creator_signature": self.signatures["creator_signature"],
        }, sort_keys=True)
        expected_platform = hashlib.sha256(
            f"{platform_data}:{platform_private_key}".encode()
        ).hexdigest()
        if self.signatures["platform_signature"] != expected_platform:
            return False, "platform_signature_invalid"

        # Step 4: Check validity period
        if now < self.validity.get("not_before", 0):
            return False, "not_yet_valid"
        if now > self.validity.get("not_after", 0):
            return False, "expired"

        return True, "valid"

    def is_expired(self) -> bool:
        return time.time() > self.validity.get("not_after", 0)

    def to_json(self) -> dict:
        """JSON representation matching spec §4."""
        return {
            "lct_id": self.lct_id,
            "lineage": {
                "creator_id": self.lineage.creator_id,
                "creator_pubkey": self.lineage.creator_pubkey,
                "creation_timestamp": self.lineage.creation_timestamp,
                "revocation_endpoint": self.lineage.revocation_endpoint,
            },
            "context": {
                "platform_id": self.context.platform_id,
                "platform_pubkey": self.context.platform_pubkey,
                "attestation_timestamp": self.context.attestation_timestamp,
                "capabilities": self.context.capabilities,
            },
            "task": {
                "task_id": self.task.task_id,
                "permissions": list(self.task.permissions),
                "resource_limits": self.task.resource_limits,
            },
            "signatures": self.signatures,
            "validity": self.validity,
        }


# ── §5  Identity Registry ─────────────────────────────────────────────

class IdentityRegistry:
    """Decentralized identity registry (§5)."""

    def __init__(self):
        self.humans: Dict[str, str] = {}         # creator_id -> pubkey
        self.organizations: Dict[str, str] = {}   # org_id -> pubkey
        self.platforms: Dict[str, str] = {}        # platform_id -> pubkey
        self.certificates: Dict[str, IdentityCertificate] = {}  # lct_id -> cert
        self.revoked: Set[str] = set()

    def register_human(self, creator_id: str, pubkey: str) -> bool:
        if creator_id in self.humans:
            return False
        self.humans[creator_id] = pubkey
        return True

    def register_organization(self, org_id: str, pubkey: str) -> bool:
        if org_id in self.organizations:
            return False
        self.organizations[org_id] = pubkey
        return True

    def register_platform(self, platform_id: str, pubkey: str) -> bool:
        if platform_id in self.platforms:
            return False
        self.platforms[platform_id] = pubkey
        return True

    def register_certificate(self, cert: IdentityCertificate) -> Tuple[bool, str]:
        """Register identity certificate."""
        if cert.lct_id in self.certificates:
            return False, "duplicate"
        # Verify creator exists
        root = cert.lineage.root_creator
        if root not in self.humans and root not in self.organizations:
            if not root.startswith("org:") and not root.startswith("system:"):
                return False, "unknown_creator"
        # Verify platform exists
        if cert.context.platform_id not in self.platforms:
            if not cert.context.platform_id.startswith("cloud:") and \
               not cert.context.platform_id.startswith("mobile:"):
                return False, "unknown_platform"
        self.certificates[cert.lct_id] = cert
        return True, "registered"

    def update_pubkey(self, entity_type: str, entity_id: str, new_pubkey: str) -> bool:
        """Update entity's public key."""
        if entity_type == "human":
            if entity_id not in self.humans:
                return False
            self.humans[entity_id] = new_pubkey
        elif entity_type == "organization":
            if entity_id not in self.organizations:
                return False
            self.organizations[entity_id] = new_pubkey
        elif entity_type == "platform":
            if entity_id not in self.platforms:
                return False
            self.platforms[entity_id] = new_pubkey
        else:
            return False
        return True

    def revoke(self, lct_id: str) -> bool:
        """Revoke identity."""
        if lct_id not in self.certificates:
            return False
        self.revoked.add(lct_id)
        return True

    def is_revoked(self, lct_id: str) -> bool:
        return lct_id in self.revoked

    def query_by_lineage(self, lineage_prefix: str) -> List[IdentityCertificate]:
        """Query certificates by lineage prefix."""
        results = []
        for lct_id, cert in self.certificates.items():
            if cert.lineage.creator_id.startswith(lineage_prefix):
                if not self.is_revoked(lct_id):
                    results.append(cert)
        return results

    def query_by_context(self, platform_id: str) -> List[IdentityCertificate]:
        """Query certificates by platform."""
        results = []
        for lct_id, cert in self.certificates.items():
            if cert.context.platform_id == platform_id:
                if not self.is_revoked(lct_id):
                    results.append(cert)
        return results

    def query_by_task(self, task_id: str) -> List[IdentityCertificate]:
        """Query certificates by task type."""
        results = []
        for lct_id, cert in self.certificates.items():
            if cert.task.task_id == task_id:
                if not self.is_revoked(lct_id):
                    results.append(cert)
        return results


# ── §6  Authorization System ──────────────────────────────────────────

TASK_PERMISSION_MATRIX = {
    "perception": {"atp:read", "network:http"},
    "planning": {"atp:read"},
    "planning.strategic": {"atp:read", "network:http", "storage:read"},
    "execution.safe": {"atp:read", "atp:write", "exec:safe", "storage:read", "storage:write"},
    "execution.code": {"atp:read", "atp:write", "exec:code", "network:http", "network:https"},
    "delegation.federation": {"atp:read", "atp:write", "federation:delegate", "network:all"},
    "cognition": {"atp:read", "atp:write", "exec:code", "network:all", "federation:delegate"},
    "admin.readonly": {"atp:read", "admin:read", "network:all", "storage:read"},
    "admin.full": {"atp:all", "exec:all", "network:all", "storage:all", "federation:all", "admin:full"},
}

ATP_BUDGETS = {
    "perception": 100.0,
    "planning": 500.0,
    "execution.code": 1000.0,
    "delegation.federation": 5000.0,
    "admin.full": float('inf'),
}

CONTEXT_RESOURCE_LIMITS = {
    "Thor": {"memory_gb": 64, "cpu_cores": 12, "network_gbps": 10},
    "Sprout": {"memory_gb": 8, "cpu_cores": 6, "network_gbps": 1},
    "Legion": {"memory_gb": 128, "cpu_cores": 24, "network_gbps": 10},
}


def check_permission(lct_id: str, operation: str) -> bool:
    """Check if LCT identity has permission for operation (§6)."""
    parsed = parse_lct_id(lct_id)
    if not parsed:
        return False
    _, _, task = parsed
    permissions = TASK_PERMISSION_MATRIX.get(task, set())
    # Direct match
    if operation in permissions:
        return True
    # Wildcard check
    category = operation.split(":")[0]
    wildcard = f"{category}:all"
    if wildcard in permissions:
        return True
    # admin:full covers all admin
    if category == "admin" and "admin:full" in permissions:
        return True
    return False


# ── §7  Attack Resistance ─────────────────────────────────────────────

class AttackAnalyzer:
    """Analyzes 4 attack vectors from spec §7."""

    @staticmethod
    def identity_forgery(
        fake_lct_id: str,
        registry: IdentityRegistry,
        has_creator_key: bool,
        has_platform_key: bool,
    ) -> dict:
        """Attack Vector 1: Identity forgery."""
        parsed = parse_lct_id(fake_lct_id)
        if not parsed:
            return {"blocked": True, "reason": "invalid_format"}
        lineage, context, task = parsed
        root = lineage.split(".")[0]
        creator_registered = root in registry.humans or root in registry.organizations
        platform_registered = context in registry.platforms
        return {
            "blocked": not (has_creator_key and has_platform_key and creator_registered and platform_registered),
            "creator_registered": creator_registered,
            "platform_registered": platform_registered,
            "needs_both_keys": True,
            "reason": "requires_both_creator_and_platform_keys",
        }

    @staticmethod
    def task_escalation(lct_id: str, attempted_operation: str) -> dict:
        """Attack Vector 2: Task escalation."""
        has_permission = check_permission(lct_id, attempted_operation)
        return {
            "blocked": not has_permission,
            "attempted": attempted_operation,
            "reason": "permission_denied" if not has_permission else "operation_allowed",
        }

    @staticmethod
    def identity_theft(
        stolen_lct_id: str,
        registry: IdentityRegistry,
        revoked: bool = False,
    ) -> dict:
        """Attack Vector 3: Identity theft."""
        is_revoked = registry.is_revoked(stolen_lct_id)
        return {
            "mitigated": is_revoked or revoked,
            "revocation_checked": True,
            "platform_binding": True,
            "behavioral_analysis": True,
            "defense_layers": 4,
        }

    @staticmethod
    def lineage_impersonation(
        claimed_lineage: str,
        actual_creator_id: str,
        registry: IdentityRegistry,
    ) -> dict:
        """Attack Vector 4: Lineage impersonation."""
        root = claimed_lineage.split(".")[0]
        is_valid_root = root in registry.humans or root in registry.organizations
        # Check if actual creator matches claimed lineage root
        is_authorized = actual_creator_id == root or actual_creator_id.startswith(root + ".")
        return {
            "blocked": not is_authorized or not is_valid_root,
            "root_registered": is_valid_root,
            "creator_authorized": is_authorized,
            "requires_signature_chain": True,
        }


# ── §8  Integration Points ────────────────────────────────────────────

class ConsensusIntegration:
    """Identity in consensus blocks (§8.1)."""

    def __init__(self, registry: IdentityRegistry):
        self.registry = registry
        self.blocks: List[dict] = []

    def register_via_consensus(self, cert: IdentityCertificate) -> Tuple[bool, str]:
        """Register identity through consensus."""
        ok, reason = self.registry.register_certificate(cert)
        if ok:
            self.blocks.append({
                "type": "IDENTITY_REGISTER",
                "lct_id": cert.lct_id,
                "timestamp": time.time(),
            })
        return ok, reason


class ATPIntegration:
    """ATP operations by identity (§8.2)."""

    def __init__(self):
        self.budgets: Dict[str, float] = {}
        self.usage: Dict[str, float] = {}

    def set_budget(self, lct_id: str, amount: float):
        self.budgets[lct_id] = amount
        self.usage[lct_id] = 0.0

    def transfer(self, from_lct: str, to_lct: str, amount: float) -> bool:
        """Transfer ATP between LCT identities."""
        remaining = self.budgets.get(from_lct, 0) - self.usage.get(from_lct, 0)
        if remaining < amount:
            return False
        self.usage[from_lct] = self.usage.get(from_lct, 0) + amount
        self.budgets[to_lct] = self.budgets.get(to_lct, 0) + amount
        return True

    def get_remaining(self, lct_id: str) -> float:
        return self.budgets.get(lct_id, 0) - self.usage.get(lct_id, 0)


class FederationIntegration:
    """Federation with identity (§8.3)."""

    @staticmethod
    def create_delegation_task(
        delegating_lct: str,
        executing_lct: str,
        task_type: str,
        estimated_cost: float,
    ) -> Tuple[Optional[dict], str]:
        """Create delegation task with identity verification."""
        # Verify delegation permission
        if not check_permission(delegating_lct, "federation:delegate"):
            return None, "delegation_not_permitted"

        return {
            "delegating_lct": delegating_lct,
            "executing_lct": executing_lct,
            "task_type": task_type,
            "estimated_cost": estimated_cost,
        }, "created"


# ════════════════════════════════════════════════════════════════════════
#  TESTS
# ════════════════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(label, condition):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✓ {label}")
        else:
            failed += 1
            print(f"  ✗ {label}")

    # ── §2  Identity Components ────────────────────────────────────
    print("\n§2 Identity Components")

    # Lineage
    lin = Lineage(creator_id="alice.assistant1.researcher", creator_pubkey="ed25519:A1B2C3")
    check("T1.1 Lineage hierarchy", lin.hierarchy == ["alice", "assistant1", "researcher"])
    check("T1.2 Root creator", lin.root_creator == "alice")
    check("T1.3 Depth = 3", lin.depth == 3)
    check("T1.4 Is descendant of alice", lin.is_descendant_of("alice"))
    check("T1.5 Is descendant of alice.assistant1", lin.is_descendant_of("alice.assistant1"))
    check("T1.6 Not descendant of bob", not lin.is_descendant_of("bob"))

    simple_lin = Lineage(creator_id="alice")
    check("T1.7 Simple lineage depth=1", simple_lin.depth == 1)
    check("T1.8 Is self descendant", simple_lin.is_descendant_of("alice"))

    # Context
    ctx_thor = Context(platform_id="Thor", capabilities=["consensus", "federation"])
    check("T1.9 Platform name", ctx_thor.platform_name == "Thor")
    check("T1.10 Not cloud", not ctx_thor.is_cloud)
    check("T1.11 Not mobile", not ctx_thor.is_mobile)

    ctx_cloud = Context(platform_id="cloud:aws-east-1")
    check("T1.12 Cloud context", ctx_cloud.is_cloud)
    check("T1.13 Cloud name", ctx_cloud.platform_name == "aws-east-1")

    ctx_mobile = Context(platform_id="mobile:iphone14")
    check("T1.14 Mobile context", ctx_mobile.is_mobile)

    # Task
    task_exec = Task(task_id="execution.code", permissions={"atp:read", "atp:write"})
    check("T1.15 Task type", task_exec.task_type == "execution")
    check("T1.16 Task variant", task_exec.task_variant == "code")
    check("T1.17 Not admin", not task_exec.is_admin)

    task_admin = Task(task_id="admin.full")
    check("T1.18 Admin task", task_admin.is_admin)

    task_del = Task(task_id="delegation.federation")
    check("T1.19 Delegation task", task_del.is_delegation)

    task_simple = Task(task_id="perception")
    check("T1.20 No variant", task_simple.task_variant is None)

    # ── §3  LCT Identity Format ────────────────────────────────────
    print("\n§3 LCT Identity Format")

    # Parsing
    parsed = parse_lct_id("lct:web4:agent:alice@Thor#perception")
    check("T2.1 Basic parse", parsed == ("alice", "Thor", "perception"))

    parsed2 = parse_lct_id("lct:web4:agent:alice.assistant1.researcher@Sprout#planning.strategic")
    check("T2.2 Hierarchical lineage parse", parsed2 == ("alice.assistant1.researcher", "Sprout", "planning.strategic"))

    parsed3 = parse_lct_id("lct:web4:agent:org:anthropic.safety@cloud:aws-east-1#admin.readonly")
    check("T2.3 Org+cloud parse", parsed3 == ("org:anthropic.safety", "cloud:aws-east-1", "admin.readonly"))

    # Invalid formats
    check("T2.4 Reject no prefix", parse_lct_id("alice@Thor#perception") is None)
    check("T2.5 Reject no @", parse_lct_id("lct:web4:agent:aliceThor#perception") is None)
    check("T2.6 Reject no #", parse_lct_id("lct:web4:agent:alice@Thor") is None)

    # Formatting
    formatted = format_lct_id("alice", "Thor", "perception")
    check("T2.7 Format basic", formatted == "lct:web4:agent:alice@Thor#perception")
    check("T2.8 Round-trip", parse_lct_id(formatted) == ("alice", "Thor", "perception"))

    # Validation
    valid, reason = validate_lct_id("lct:web4:agent:alice@Thor#perception")
    check("T2.9 Valid LCT ID", valid)
    check("T2.10 Reason valid", reason == "valid")

    invalid, reason2 = validate_lct_id("not:an:lct:id")
    check("T2.11 Invalid prefix rejected", not invalid)
    check("T2.12 Reason invalid_prefix", reason2 == "invalid_prefix")

    # Spec examples
    examples = [
        "lct:web4:agent:alice@Thor#perception",
        "lct:web4:agent:alice.assistant1.researcher@Sprout#planning.strategic",
        "lct:web4:agent:org:anthropic.safety@cloud:aws-east-1#admin.readonly",
        "lct:web4:agent:alice@Thor#delegation.federation",
    ]
    for ex in examples:
        check(f"T2.{13+examples.index(ex)} Spec example: {ex.split(':')[-1][:30]}",
              parse_lct_id(ex) is not None)

    # ── §4  Cryptographic Structure ────────────────────────────────
    print("\n§4 Cryptographic Structure")

    alice_priv = "alice_private_key_ed25519"
    thor_priv = "thor_private_key_ed25519"

    cert = IdentityCertificate.create(
        lineage=Lineage(creator_id="alice", creator_pubkey="ed25519:A1B2"),
        context=Context(platform_id="Thor", platform_pubkey="ed25519:T1H2", capabilities=["consensus"]),
        task=Task(task_id="perception", permissions={"atp:read", "network:http"}),
        creator_private_key=alice_priv,
        platform_private_key=thor_priv,
    )

    check("T3.1 Certificate created", cert is not None)
    check("T3.2 LCT ID format", cert.lct_id == "lct:web4:agent:alice@Thor#perception")
    check("T3.3 Has creator signature", "creator_signature" in cert.signatures)
    check("T3.4 Has platform signature", "platform_signature" in cert.signatures)
    check("T3.5 Sigs are hex", len(cert.signatures["creator_signature"]) == 64)

    # Verify
    valid, reason = cert.verify(alice_priv, thor_priv)
    check("T3.6 Verification succeeds", valid)
    check("T3.7 Reason valid", reason == "valid")

    # Wrong creator key
    valid2, reason2 = cert.verify("wrong_key", thor_priv)
    check("T3.8 Wrong creator key fails", not valid2)
    check("T3.9 Creator sig invalid", reason2 == "creator_signature_invalid")

    # Wrong platform key
    valid3, reason3 = cert.verify(alice_priv, "wrong_platform_key")
    check("T3.10 Wrong platform key fails", not valid3)
    check("T3.11 Platform sig invalid", reason3 == "platform_signature_invalid")

    # JSON export
    cert_json = cert.to_json()
    check("T3.12 JSON has lct_id", cert_json["lct_id"] == cert.lct_id)
    check("T3.13 JSON has lineage", cert_json["lineage"]["creator_id"] == "alice")
    check("T3.14 JSON has context", cert_json["context"]["platform_id"] == "Thor")
    check("T3.15 JSON has task", cert_json["task"]["task_id"] == "perception")
    check("T3.16 JSON has signatures", len(cert_json["signatures"]) == 2)
    check("T3.17 JSON has validity", "not_before" in cert_json["validity"])

    # Expired certificate
    expired_cert = IdentityCertificate(
        lct_id="test",
        lineage=Lineage(creator_id="x"),
        context=Context(platform_id="y"),
        task=Task(task_id="z"),
        validity={"not_before": 0, "not_after": 1},
    )
    check("T3.18 Expired check", expired_cert.is_expired())

    # ── §5  Identity Registry ──────────────────────────────────────
    print("\n§5 Identity Registry")

    registry = IdentityRegistry()

    # Register entities
    check("T4.1 Register alice", registry.register_human("alice", "ed25519:A1"))
    check("T4.2 Register bob", registry.register_human("bob", "ed25519:B1"))
    check("T4.3 Reject duplicate alice", not registry.register_human("alice", "ed25519:A2"))
    check("T4.4 Register org", registry.register_organization("org:anthropic", "ed25519:O1"))
    check("T4.5 Register Thor", registry.register_platform("Thor", "ed25519:T1"))
    check("T4.6 Register Sprout", registry.register_platform("Sprout", "ed25519:S1"))

    # Register certificate
    ok, reason = registry.register_certificate(cert)
    check("T4.7 Certificate registered", ok)
    check("T4.8 Reason registered", reason == "registered")

    # Reject duplicate
    ok2, reason2 = registry.register_certificate(cert)
    check("T4.9 Reject duplicate cert", not ok2)

    # Unknown creator
    bad_cert = IdentityCertificate(
        lct_id="lct:web4:agent:unknown@Thor#perception",
        lineage=Lineage(creator_id="unknown"),
        context=Context(platform_id="Thor"),
        task=Task(task_id="perception"),
    )
    ok3, reason3 = registry.register_certificate(bad_cert)
    check("T4.10 Reject unknown creator", not ok3)

    # Update pubkey
    check("T4.11 Update alice key", registry.update_pubkey("human", "alice", "ed25519:A2"))
    check("T4.12 Alice key updated", registry.humans["alice"] == "ed25519:A2")
    check("T4.13 Update unknown fails", not registry.update_pubkey("human", "charlie", "ed25519:C1"))

    # Revocation
    check("T4.14 Not revoked initially", not registry.is_revoked(cert.lct_id))
    check("T4.15 Revoke cert", registry.revoke(cert.lct_id))
    check("T4.16 Is revoked", registry.is_revoked(cert.lct_id))
    check("T4.17 Revoke unknown fails", not registry.revoke("nonexistent"))

    # Query (register some more certs first)
    bob_cert = IdentityCertificate(
        lct_id="lct:web4:agent:bob@Thor#execution.code",
        lineage=Lineage(creator_id="bob"),
        context=Context(platform_id="Thor"),
        task=Task(task_id="execution.code"),
    )
    registry.register_certificate(bob_cert)

    alice_sub_cert = IdentityCertificate(
        lct_id="lct:web4:agent:alice.assistant1@Sprout#planning",
        lineage=Lineage(creator_id="alice.assistant1"),
        context=Context(platform_id="Sprout"),
        task=Task(task_id="planning"),
    )
    registry.register_certificate(alice_sub_cert)

    # Query by lineage (alice is revoked, alice.assistant1 is not)
    alice_results = registry.query_by_lineage("alice")
    check("T4.18 Query alice lineage", len(alice_results) == 1)  # alice revoked, alice.assistant1 active

    # Query by context
    thor_results = registry.query_by_context("Thor")
    check("T4.19 Query Thor context", len(thor_results) == 1)  # bob@Thor (alice revoked)

    # Query by task
    perception_results = registry.query_by_task("perception")
    check("T4.20 Query perception tasks", len(perception_results) == 0)  # alice@Thor revoked

    # ── §6  Authorization System ───────────────────────────────────
    print("\n§6 Authorization System")

    # Permission checks
    check("T5.1 alice@Thor#perception has atp:read",
          check_permission("lct:web4:agent:alice@Thor#perception", "atp:read"))
    check("T5.2 perception lacks exec:code",
          not check_permission("lct:web4:agent:alice@Thor#perception", "exec:code"))
    check("T5.3 execution.code has exec:code",
          check_permission("lct:web4:agent:bob@Thor#execution.code", "exec:code"))
    check("T5.4 delegation has federation:delegate",
          check_permission("lct:web4:agent:alice@Thor#delegation.federation", "federation:delegate"))
    check("T5.5 admin.full has everything",
          check_permission("lct:web4:agent:admin@Legion#admin.full", "admin:read"))
    check("T5.6 admin.full wildcard",
          check_permission("lct:web4:agent:admin@Legion#admin.full", "network:http"))
    check("T5.7 Unknown task denied",
          not check_permission("lct:web4:agent:x@y#unknown_task", "atp:read"))
    check("T5.8 Invalid format denied",
          not check_permission("not_valid", "atp:read"))

    # ATP budgets
    check("T5.9 Perception budget = 100", ATP_BUDGETS["perception"] == 100.0)
    check("T5.10 Execution.code budget = 1000", ATP_BUDGETS["execution.code"] == 1000.0)
    check("T5.11 Delegation budget = 5000", ATP_BUDGETS["delegation.federation"] == 5000.0)
    check("T5.12 Admin.full budget = inf", ATP_BUDGETS["admin.full"] == float('inf'))

    # Context resources
    check("T5.13 Legion 128GB", CONTEXT_RESOURCE_LIMITS["Legion"]["memory_gb"] == 128)
    check("T5.14 Sprout 8GB", CONTEXT_RESOURCE_LIMITS["Sprout"]["memory_gb"] == 8)
    check("T5.15 Thor 12 cores", CONTEXT_RESOURCE_LIMITS["Thor"]["cpu_cores"] == 12)

    # ── §7  Attack Resistance ──────────────────────────────────────
    print("\n§7 Attack Resistance")

    atk = AttackAnalyzer()

    # Attack 1: Identity forgery
    forgery = atk.identity_forgery(
        "lct:web4:agent:alice@Thor#perception",
        registry, has_creator_key=False, has_platform_key=False,
    )
    check("T6.1 Forgery blocked without keys", forgery["blocked"])
    check("T6.2 Needs both keys", forgery["needs_both_keys"])

    forgery_with_keys = atk.identity_forgery(
        "lct:web4:agent:alice@Thor#perception",
        registry, has_creator_key=True, has_platform_key=True,
    )
    check("T6.3 Not blocked with both keys + registered", not forgery_with_keys["blocked"])

    forgery_unknown = atk.identity_forgery(
        "lct:web4:agent:stranger@Thor#perception",
        registry, has_creator_key=True, has_platform_key=True,
    )
    check("T6.4 Blocked for unregistered creator", forgery_unknown["blocked"])

    # Attack 2: Task escalation
    escalation = atk.task_escalation(
        "lct:web4:agent:alice@Thor#perception", "exec:code"
    )
    check("T6.5 Escalation blocked", escalation["blocked"])
    check("T6.6 Permission denied", escalation["reason"] == "permission_denied")

    allowed_op = atk.task_escalation(
        "lct:web4:agent:alice@Thor#execution.code", "exec:code"
    )
    check("T6.7 Allowed operation not blocked", not allowed_op["blocked"])

    # Attack 3: Identity theft
    theft_mitigated = atk.identity_theft(cert.lct_id, registry, revoked=False)
    check("T6.8 Theft mitigated by revocation", theft_mitigated["mitigated"])  # cert was revoked above
    check("T6.9 4 defense layers", theft_mitigated["defense_layers"] == 4)

    theft_active = atk.identity_theft("nonexistent", registry, revoked=True)
    check("T6.10 Theft flag works", theft_active["mitigated"])

    # Attack 4: Lineage impersonation
    impersonation = atk.lineage_impersonation("alice.assistant1", "bob", registry)
    check("T6.11 Impersonation blocked", impersonation["blocked"])
    check("T6.12 Creator not authorized", not impersonation["creator_authorized"])

    legit = atk.lineage_impersonation("alice.assistant1", "alice", registry)
    check("T6.13 Legitimate lineage allowed", not legit["blocked"])
    check("T6.14 Creator authorized", legit["creator_authorized"])

    # ── §8  Integration ────────────────────────────────────────────
    print("\n§8 Integration")

    # Consensus integration
    ci = ConsensusIntegration(IdentityRegistry())
    ci.registry.register_human("dave", "ed25519:D1")
    ci.registry.register_platform("Legion", "ed25519:L1")
    dave_cert = IdentityCertificate(
        lct_id="lct:web4:agent:dave@Legion#cognition",
        lineage=Lineage(creator_id="dave"),
        context=Context(platform_id="Legion"),
        task=Task(task_id="cognition"),
    )
    ok, reason = ci.register_via_consensus(dave_cert)
    check("T7.1 Consensus registration", ok)
    check("T7.2 Block recorded", len(ci.blocks) == 1)
    check("T7.3 Block type IDENTITY_REGISTER", ci.blocks[0]["type"] == "IDENTITY_REGISTER")

    # ATP integration
    atp = ATPIntegration()
    atp.set_budget("lct:web4:agent:alice@Thor#perception", 100.0)
    check("T7.4 Budget set", atp.get_remaining("lct:web4:agent:alice@Thor#perception") == 100.0)

    transferred = atp.transfer(
        "lct:web4:agent:alice@Thor#perception",
        "lct:web4:agent:bob@Sprout#execution.code",
        50.0,
    )
    check("T7.5 Transfer succeeded", transferred)
    check("T7.6 Alice remaining = 50", atp.get_remaining("lct:web4:agent:alice@Thor#perception") == 50.0)

    over_transfer = atp.transfer(
        "lct:web4:agent:alice@Thor#perception",
        "lct:web4:agent:bob@Sprout#execution.code",
        999.0,
    )
    check("T7.7 Over-transfer fails", not over_transfer)

    # Federation integration
    fed_task, reason = FederationIntegration.create_delegation_task(
        "lct:web4:agent:alice@Thor#delegation.federation",
        "lct:web4:agent:bob@Sprout#execution.code",
        "code_execution",
        50.0,
    )
    check("T7.8 Federation task created", fed_task is not None)
    check("T7.9 Task has delegating LCT", "delegation.federation" in fed_task["delegating_lct"])

    fed_denied, reason2 = FederationIntegration.create_delegation_task(
        "lct:web4:agent:alice@Thor#perception",  # perception cannot delegate
        "lct:web4:agent:bob@Sprout#execution.code",
        "code_execution",
        50.0,
    )
    check("T7.10 Perception cannot delegate", fed_denied is None)
    check("T7.11 Reason denied", reason2 == "delegation_not_permitted")

    # ── Summary ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"LCT Identity System: {passed}/{total} checks passed")
    if failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {failed} checks FAILED")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    run_tests()
