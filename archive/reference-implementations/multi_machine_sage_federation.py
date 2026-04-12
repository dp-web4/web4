#!/usr/bin/env python3
"""
Web4 Reference Implementation: Multi-Machine SAGE Federation Design
Spec: docs/what/specifications/MULTI_MACHINE_SAGE_FEDERATION_DESIGN.md (643 lines)

Covers:
  §1 Current State (3 platforms: Legion/Thor/Sprout)
  §2 Federation Architecture (server/client, FederationTask, ExecutionProof)
  §3 Federation Protocol (delegation flow, quality-based settlement, permission validation)
  §4 ATP Accounting Integration (lock-commit-rollback)
  §5 Security Considerations (crypto signing, permission enforcement, DoS)
  §6 Deployment Architecture (topology, per-platform config)
  §7 Implementation Plan (4 phases)
  §8 Success Criteria (functional, performance, security)
  §9 Testing Strategy (local + multi-machine)
  §10 Risk Mitigation (4 risks)

Run:  python3 multi_machine_sage_federation.py
"""

import hashlib, json, time, uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum

# ── §1  Platform Capabilities ──────────────────────────────────────────

@dataclass
class PlatformCapabilities:
    """Platform resource profile from spec §1."""
    name: str
    memory_gb: int
    cpu_cores: int
    gpu: str = ""
    network_gbps: float = 1.0
    capabilities: List[str] = field(default_factory=list)
    ed25519_ops_per_sec: int = 0
    tests_passing: int = 0

PLATFORMS = {
    "Legion": PlatformCapabilities(
        name="Legion", memory_gb=128, cpu_cores=24, gpu="RTX 4090",
        network_gbps=10.0, capabilities=["cognition", "cognition.sage"],
        tests_passing=86,
    ),
    "Thor": PlatformCapabilities(
        name="Thor", memory_gb=64, cpu_cores=12, gpu="Jetson AGX Thor",
        network_gbps=10.0, capabilities=["cognition", "cognition.sage"],
        tests_passing=113,
    ),
    "Sprout": PlatformCapabilities(
        name="Sprout", memory_gb=8, cpu_cores=6, gpu="Orin Nano",
        network_gbps=1.0, capabilities=["cognition"],
        ed25519_ops_per_sec=18145, tests_passing=165,
    ),
}


# ── §2  Core Data Structures ──────────────────────────────────────────

@dataclass
class FederationTask:
    """Cognition task for cross-platform delegation (§2.3)."""
    task_id: str
    source_lct: str
    target_lct: str
    task_type: str  # "cognition" or "cognition.sage"
    operation: str  # "perception", "planning", "execution"
    atp_budget: float
    timeout_seconds: int = 60
    parameters: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_signable_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "source_lct": self.source_lct,
            "target_lct": self.target_lct,
            "task_type": self.task_type,
            "operation": self.operation,
            "atp_budget": self.atp_budget,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
        }


@dataclass
class ExecutionProof:
    """Proof of cognition task execution (§2.4)."""
    task_id: str
    executor_lct: str
    atp_consumed: float
    execution_time: float
    quality_score: float
    result: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    signature: bytes = b""

    def to_signable_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "executor_lct": self.executor_lct,
            "atp_consumed": self.atp_consumed,
            "execution_time": self.execution_time,
            "quality_score": self.quality_score,
            "created_at": self.created_at,
        }


# ── §5  Crypto (simplified Ed25519 mock) ──────────────────────────────

class FederationCrypto:
    """Simplified Ed25519 signing/verification for federation."""

    @staticmethod
    def generate_keypair(platform_name: str) -> Tuple[str, str]:
        """Generate mock keypair (privkey, pubkey)."""
        priv = hashlib.sha256(f"priv:{platform_name}".encode()).hexdigest()
        pub = hashlib.sha256(f"pub:{platform_name}".encode()).hexdigest()
        return priv, pub

    @staticmethod
    def sign(data: dict, private_key: str) -> str:
        """Sign data with private key."""
        msg = json.dumps(data, sort_keys=True)
        return hashlib.sha256(f"{msg}:{private_key}".encode()).hexdigest()

    @staticmethod
    def verify(data: dict, signature: str, private_key: str) -> bool:
        """Verify signature (in real impl, would use public key)."""
        expected = FederationCrypto.sign(data, private_key)
        return signature == expected

    @staticmethod
    def sign_task(task: FederationTask, private_key: str) -> str:
        return FederationCrypto.sign(task.to_signable_dict(), private_key)

    @staticmethod
    def sign_proof(proof: ExecutionProof, private_key: str) -> str:
        return FederationCrypto.sign(proof.to_signable_dict(), private_key)


# ── §3  Permission Validation ──────────────────────────────────────────

TASK_PERMISSIONS = {
    "cognition": {
        "delegation": True, "execution": True, "code": True,
        "atp_budget": 1000.0,
    },
    "cognition.sage": {
        "delegation": True, "execution": True, "code": True,
        "atp_budget": 2000.0,
    },
    "perception": {
        "delegation": False, "execution": True, "code": False,
        "atp_budget": 200.0,
    },
}


def check_permission(task_type: str, operation: str) -> bool:
    """Check if task type permits given operation (§3.3)."""
    perms = TASK_PERMISSIONS.get(task_type)
    if not perms:
        return False
    if operation == "federation:delegate":
        return perms.get("delegation", False)
    if operation == "exec:code":
        return perms.get("code", False)
    return perms.get("execution", False)


# ── §4  ATP Accounting ─────────────────────────────────────────────────

class ATPLedger:
    """Lock-Commit-Rollback ATP accounting (§4)."""

    def __init__(self):
        self.balances: Dict[str, float] = {}
        self.available: Dict[str, float] = {}
        self.locks: Dict[str, dict] = {}

    def create_account(self, lct_id: str, balance: float):
        self.balances[lct_id] = balance
        self.available[lct_id] = balance

    def lock_atp(self, lct_id: str, amount: float, reason: str = "") -> Optional[str]:
        """Phase 1: Lock ATP before delegation."""
        if self.available.get(lct_id, 0) < amount:
            return None
        lock_id = str(uuid.uuid4())[:8]
        self.available[lct_id] -= amount
        self.locks[lock_id] = {
            "lct_id": lct_id, "amount": amount, "reason": reason, "status": "locked",
        }
        return lock_id

    def commit(self, lock_id: str, from_lct: str, to_lct: str, amount: float, quality: float = 0.0) -> bool:
        """Phase 2a: Commit ATP transfer on success."""
        lock = self.locks.get(lock_id)
        if not lock or lock["status"] != "locked":
            return False
        self.balances[from_lct] -= amount
        self.balances.setdefault(to_lct, 0.0)
        self.balances[to_lct] += amount
        self.available.setdefault(to_lct, 0.0)
        self.available[to_lct] += amount
        # Refund excess
        excess = lock["amount"] - amount
        if excess > 0:
            self.available[from_lct] += excess
        lock["status"] = "committed"
        return True

    def rollback(self, lock_id: str, reason: str = "") -> bool:
        """Phase 2b: Rollback on failure or low quality."""
        lock = self.locks.get(lock_id)
        if not lock or lock["status"] != "locked":
            return False
        self.available[lock["lct_id"]] += lock["amount"]
        lock["status"] = "rolled_back"
        lock["rollback_reason"] = reason
        return True


# ── §2-§3  Federation Server ──────────────────────────────────────────

class FederationServer:
    """Federation server (Legion) — accepts and executes delegated tasks (§2.1)."""

    def __init__(self, platform_name: str, private_key: str, ledger: ATPLedger):
        self.platform = platform_name
        self.private_key = private_key
        self.ledger = ledger
        self.active_tasks: Dict[str, FederationTask] = {}
        self.completed: Dict[str, ExecutionProof] = {}
        self.max_concurrent = 10

    def validate_task(self, task: FederationTask, task_signature: str, delegator_key: str) -> Tuple[bool, str]:
        """Validate incoming delegation request."""
        # 1. Verify signature
        if not FederationCrypto.verify(task.to_signable_dict(), task_signature, delegator_key):
            return False, "invalid_signature"
        # 2. Check permissions
        if not check_permission(task.task_type, "federation:delegate"):
            return False, "delegation_not_permitted"
        # 3. Check capacity
        if len(self.active_tasks) >= self.max_concurrent:
            return False, "at_capacity"
        # 4. Check ATP budget
        perms = TASK_PERMISSIONS.get(task.task_type, {})
        if task.atp_budget > perms.get("atp_budget", 0):
            return False, "exceeds_budget"
        return True, "valid"

    def execute_task(self, task: FederationTask) -> ExecutionProof:
        """Execute delegated task and create proof."""
        self.active_tasks[task.task_id] = task
        # Simulate execution
        quality = 0.85  # Simulated quality
        atp_consumed = task.atp_budget * 0.8  # Used 80% of budget
        execution_time = 0.045  # 45ms
        proof = ExecutionProof(
            task_id=task.task_id,
            executor_lct=task.target_lct,
            atp_consumed=atp_consumed,
            execution_time=execution_time,
            quality_score=quality,
            result={"status": "completed"},
        )
        proof.signature = FederationCrypto.sign_proof(proof, self.private_key).encode()
        del self.active_tasks[task.task_id]
        self.completed[task.task_id] = proof
        return proof

    def get_status(self, lct_id: str) -> dict:
        """GET /api/v1/cognition/status/{lct_id} (§2.1)."""
        active = [t for t in self.active_tasks.values() if t.source_lct == lct_id]
        total_atp = sum(t.atp_budget for t in active)
        return {
            "active": len(active) > 0,
            "atp_consumed": total_atp,
            "tasks_running": len(active),
        }

    def cancel_task(self, task_id: str) -> dict:
        """POST /api/v1/cognition/cancel/{task_id} (§2.1)."""
        if task_id in self.active_tasks:
            task = self.active_tasks.pop(task_id)
            return {"cancelled": True, "atp_refunded": task.atp_budget}
        return {"cancelled": False, "atp_refunded": 0.0}


# ── §2-§3  Federation Client ──────────────────────────────────────────

class FederationClient:
    """Federation client (Thor/Sprout) — delegates tasks (§2.2)."""

    def __init__(self, platform_name: str, private_key: str, ledger: ATPLedger):
        self.platform = platform_name
        self.private_key = private_key
        self.ledger = ledger
        self.registry: Dict[str, dict] = {}  # Platform capabilities
        self.pending_locks: Dict[str, str] = {}  # task_id -> lock_id

    def register_platform(self, name: str, endpoint: str, capabilities: List[str]):
        """Register a remote platform."""
        self.registry[name] = {
            "endpoint": endpoint, "capabilities": capabilities,
        }

    def delegate_task(
        self,
        task: FederationTask,
        server: FederationServer,
        server_key: str,
    ) -> Tuple[Optional[ExecutionProof], str]:
        """Full delegation flow (§3.1 steps 1-13)."""
        # Step 2: Select target (already done — server is target)
        # Step 3: Lock ATP
        lock_id = self.ledger.lock_atp(
            task.source_lct, task.atp_budget,
            f"Federation delegation to {task.target_lct}"
        )
        if not lock_id:
            return None, "insufficient_atp"
        self.pending_locks[task.task_id] = lock_id

        # Step 3: Sign task
        task_sig = FederationCrypto.sign_task(task, self.private_key)

        # Step 4: Send to server (simulated)
        valid, reason = server.validate_task(task, task_sig, self.private_key)
        if not valid:
            self.ledger.rollback(lock_id, reason)
            return None, reason

        # Steps 5-8: Server executes
        proof = server.execute_task(task)

        # Step 10: Verify proof signature
        proof_sig = proof.signature.decode() if isinstance(proof.signature, bytes) else proof.signature
        if not FederationCrypto.verify(proof.to_signable_dict(), proof_sig, server_key):
            self.ledger.rollback(lock_id, "invalid_proof_signature")
            return None, "invalid_proof_signature"

        # Step 11-12: Quality-based ATP settlement
        quality_threshold = 0.7
        if proof.quality_score >= quality_threshold:
            self.ledger.commit(
                lock_id, task.source_lct, task.target_lct,
                proof.atp_consumed, proof.quality_score,
            )
            return proof, "COMMIT"
        else:
            self.ledger.rollback(lock_id, f"Low quality ({proof.quality_score})")
            return proof, "ROLLBACK"


# ── §5  DoS Protection ────────────────────────────────────────────────

class RateLimiter:
    """Rate limiting for federation requests (§5.3)."""

    def __init__(self, max_per_minute: int = 60, max_concurrent: int = 10):
        self.max_per_minute = max_per_minute
        self.max_concurrent = max_concurrent
        self.requests: List[float] = []
        self.active = 0

    def allow_request(self) -> bool:
        now = time.time()
        # Clean old requests
        self.requests = [t for t in self.requests if now - t < 60]
        if len(self.requests) >= self.max_per_minute:
            return False
        if self.active >= self.max_concurrent:
            return False
        self.requests.append(now)
        self.active += 1
        return True

    def release(self):
        self.active = max(0, self.active - 1)


class TimeoutEnforcer:
    """Timeout enforcement for task execution (§5.3)."""

    @staticmethod
    def check_timeout(execution_time: float, timeout_seconds: int) -> bool:
        """Returns True if within timeout."""
        return execution_time <= timeout_seconds

    @staticmethod
    def handle_timeout(lock_id: str, ledger: ATPLedger) -> bool:
        """Rollback ATP on timeout."""
        return ledger.rollback(lock_id, "task_timeout")


# ── §6  Deployment Configuration ───────────────────────────────────────

@dataclass
class PlatformConfig:
    """Per-platform configuration (§6)."""
    platform_name: str
    role: str  # "server" or "client"
    host: str = "0.0.0.0"
    port: int = 8080
    lct_context: str = ""
    keypair_path: str = ""
    cognition_budget: float = 1000.0
    sage_budget: float = 2000.0
    max_concurrent: int = 10
    remote_servers: List[dict] = field(default_factory=list)

DEPLOYMENT_CONFIGS = {
    "Legion": PlatformConfig(
        platform_name="Legion", role="server",
        host="0.0.0.0", port=8080, lct_context="Legion",
        keypair_path="~/.web4/federation/legion_ed25519.key",
        cognition_budget=1000.0, sage_budget=2000.0, max_concurrent=10,
    ),
    "Thor": PlatformConfig(
        platform_name="Thor", role="client",
        lct_context="Thor",
        keypair_path="~/HRM/sage/data/keys/Thor_ed25519.key",
        remote_servers=[
            {"name": "Legion", "endpoint": "http://legion.local:8080", "capabilities": ["cognition", "cognition.sage"]},
            {"name": "Sprout", "endpoint": "http://sprout.local:8081", "capabilities": ["cognition"]},
        ],
    ),
    "Sprout": PlatformConfig(
        platform_name="Sprout", role="client",
        lct_context="Sprout",
        keypair_path="~/.web4/federation/sprout_ed25519.key",
        remote_servers=[
            {"name": "Legion", "endpoint": "http://legion.local:8080", "capabilities": ["cognition", "cognition.sage"]},
            {"name": "Thor", "endpoint": "http://thor.local:8082", "capabilities": ["cognition", "cognition.sage"]},
        ],
    ),
}


# ── §8  Success Criteria ──────────────────────────────────────────────

@dataclass
class SuccessCriteria:
    """Success criteria from spec §8."""
    # Functional
    delegation_works: bool = False
    bidirectional: bool = False
    signatures_verified: bool = False
    atp_accurate: bool = False
    quality_settlement: bool = False
    permissions_enforced: bool = False
    # Performance
    delegation_latency_ms: float = 0.0
    proof_verification_ms: float = 0.0
    settlement_ms: float = 0.0
    max_concurrent: int = 0
    # Security
    signatures_before_exec: bool = False
    permission_checks: bool = False
    atp_lock_prevents_double_spend: bool = False
    resource_limits: bool = False
    quality_thresholds: bool = False

    def functional_pass(self) -> bool:
        return all([
            self.delegation_works, self.signatures_verified,
            self.atp_accurate, self.quality_settlement,
            self.permissions_enforced,
        ])

    def performance_pass(self) -> bool:
        return (
            self.delegation_latency_ms < 100
            and self.proof_verification_ms < 10
            and self.settlement_ms < 50
            and self.max_concurrent >= 10
        )

    def security_pass(self) -> bool:
        return all([
            self.signatures_before_exec, self.permission_checks,
            self.atp_lock_prevents_double_spend, self.resource_limits,
            self.quality_thresholds,
        ])


# ── §10  Risk Mitigation ──────────────────────────────────────────────

class RiskMitigator:
    """Risk mitigation strategies from spec §10."""

    @staticmethod
    def mitigate_network_failure(lock_id: str, ledger: ATPLedger) -> dict:
        """Risk 1: Network failures — rollback ATP."""
        rolled_back = ledger.rollback(lock_id, "network_failure")
        return {"mitigated": rolled_back, "action": "atp_rollback"}

    @staticmethod
    def mitigate_signature_failure(task: FederationTask, sig: str, key: str) -> dict:
        """Risk 2: Signature verification failures."""
        valid = FederationCrypto.verify(task.to_signable_dict(), sig, key)
        return {
            "signature_valid": valid,
            "action": "reject_task" if not valid else "proceed",
        }

    @staticmethod
    def mitigate_atp_error(ledger: ATPLedger, lct_id: str, expected: float) -> dict:
        """Risk 3: ATP accounting errors — reconciliation."""
        actual = ledger.balances.get(lct_id, 0.0)
        discrepancy = abs(actual - expected)
        return {
            "actual": actual,
            "expected": expected,
            "discrepancy": discrepancy,
            "reconciled": discrepancy < 0.01,
        }

    @staticmethod
    def mitigate_resource_exhaustion(active_tasks: int, max_tasks: int) -> dict:
        """Risk 4: Resource exhaustion — reject new tasks."""
        return {
            "at_capacity": active_tasks >= max_tasks,
            "action": "reject_new" if active_tasks >= max_tasks else "accept",
            "utilization": active_tasks / max_tasks if max_tasks > 0 else 1.0,
        }


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

    # ── §1  Platform Status ────────────────────────────────────────
    print("\n§1 Platform Capabilities")

    check("T1.1 3 platforms defined", len(PLATFORMS) == 3)
    check("T1.2 Legion 128GB", PLATFORMS["Legion"].memory_gb == 128)
    check("T1.3 Thor 64GB", PLATFORMS["Thor"].memory_gb == 64)
    check("T1.4 Sprout 8GB", PLATFORMS["Sprout"].memory_gb == 8)
    check("T1.5 Legion has cognition.sage", "cognition.sage" in PLATFORMS["Legion"].capabilities)
    check("T1.6 Sprout lacks sage", "cognition.sage" not in PLATFORMS["Sprout"].capabilities)
    check("T1.7 Sprout Ed25519 18145 ops", PLATFORMS["Sprout"].ed25519_ops_per_sec == 18145)
    check("T1.8 All platforms have tests", all(p.tests_passing > 0 for p in PLATFORMS.values()))

    # ── §2  Core Data Structures ───────────────────────────────────
    print("\n§2 FederationTask & ExecutionProof")

    task = FederationTask(
        task_id="task-001",
        source_lct="lct:web4:agent:dp@Legion#cognition",
        target_lct="lct:web4:agent:dp@Thor#cognition.sage",
        task_type="cognition",
        operation="perception",
        atp_budget=300.0,
        timeout_seconds=60,
        parameters={"perception_size": 512},
    )

    check("T2.1 Task has ID", task.task_id == "task-001")
    check("T2.2 Task has source", "Legion" in task.source_lct)
    check("T2.3 Task has target", "Thor" in task.target_lct)
    check("T2.4 Task signable dict", "task_id" in task.to_signable_dict())
    check("T2.5 Task signable no params", "parameters" not in task.to_signable_dict())

    proof = ExecutionProof(
        task_id="task-001",
        executor_lct="lct:web4:agent:dp@Thor#cognition.sage",
        atp_consumed=240.0,
        execution_time=0.045,
        quality_score=0.85,
        result={"status": "completed"},
    )

    check("T2.6 Proof has task ID", proof.task_id == "task-001")
    check("T2.7 Proof has quality", proof.quality_score == 0.85)
    check("T2.8 Proof signable dict", "executor_lct" in proof.to_signable_dict())
    check("T2.9 Proof signable no result", "result" not in proof.to_signable_dict())

    # ── §5  Crypto Signing ─────────────────────────────────────────
    print("\n§5a Cryptographic Signing")

    legion_priv, legion_pub = FederationCrypto.generate_keypair("Legion")
    thor_priv, thor_pub = FederationCrypto.generate_keypair("Thor")

    check("T3.1 Keys are hex strings", len(legion_priv) == 64)
    check("T3.2 Different keys per platform", legion_priv != thor_priv)

    task_sig = FederationCrypto.sign_task(task, legion_priv)
    check("T3.3 Task signature generated", len(task_sig) == 64)
    check("T3.4 Task signature verifies", FederationCrypto.verify(task.to_signable_dict(), task_sig, legion_priv))
    check("T3.5 Wrong key fails verify", not FederationCrypto.verify(task.to_signable_dict(), task_sig, thor_priv))

    proof_sig = FederationCrypto.sign_proof(proof, thor_priv)
    check("T3.6 Proof signature generated", len(proof_sig) == 64)
    check("T3.7 Proof signature verifies", FederationCrypto.verify(proof.to_signable_dict(), proof_sig, thor_priv))

    # ── §3  Permission Validation ──────────────────────────────────
    print("\n§3 Permission Validation")

    check("T4.1 cognition can delegate", check_permission("cognition", "federation:delegate"))
    check("T4.2 cognition.sage can delegate", check_permission("cognition.sage", "federation:delegate"))
    check("T4.3 perception cannot delegate", not check_permission("perception", "federation:delegate"))
    check("T4.4 cognition can execute", check_permission("cognition", "exec:code"))
    check("T4.5 perception cannot code", not check_permission("perception", "exec:code"))

    # ── §4  ATP Lock-Commit-Rollback ───────────────────────────────
    print("\n§4 ATP Accounting Integration")

    ledger = ATPLedger()
    ledger.create_account("alice@Legion", 1000.0)
    ledger.create_account("bob@Thor", 500.0)

    # Phase 1: Lock
    lock_id = ledger.lock_atp("alice@Legion", 300.0, "Federation delegation to bob@Thor")
    check("T5.1 Lock successful", lock_id is not None)
    check("T5.2 Available reduced", ledger.available["alice@Legion"] == 700.0)
    check("T5.3 Balance unchanged", ledger.balances["alice@Legion"] == 1000.0)

    # Phase 2a: Commit
    committed = ledger.commit(lock_id, "alice@Legion", "bob@Thor", 240.0, 0.85)
    check("T5.4 Commit successful", committed)
    check("T5.5 Alice balance reduced", ledger.balances["alice@Legion"] == 760.0)
    check("T5.6 Bob balance increased", ledger.balances["bob@Thor"] == 740.0)
    check("T5.7 Alice gets excess back", ledger.available["alice@Legion"] == 760.0)

    # Phase 2b: Rollback
    ledger2 = ATPLedger()
    ledger2.create_account("charlie@Sprout", 500.0)
    lock2 = ledger2.lock_atp("charlie@Sprout", 200.0, "test")
    check("T5.8 Lock for rollback", lock2 is not None)
    rolled = ledger2.rollback(lock2, "Low quality (0.55)")
    check("T5.9 Rollback successful", rolled)
    check("T5.10 Charlie available restored", ledger2.available["charlie@Sprout"] == 500.0)
    check("T5.11 Charlie balance unchanged", ledger2.balances["charlie@Sprout"] == 500.0)

    # Insufficient ATP
    lock3 = ledger2.lock_atp("charlie@Sprout", 999.0)
    check("T5.12 Lock fails insufficient", lock3 is None)

    # ── §2-§3  Server-Client Flow ──────────────────────────────────
    print("\n§3b Full Delegation Flow")

    flow_ledger = ATPLedger()
    flow_ledger.create_account("dp@Legion", 1000.0)
    flow_ledger.create_account("dp@Thor", 200.0)

    server = FederationServer("Legion", legion_priv, flow_ledger)
    client = FederationClient("Thor", thor_priv, flow_ledger)
    client.register_platform("Legion", "http://legion.local:8080", ["cognition", "cognition.sage"])

    flow_task = FederationTask(
        task_id="flow-001",
        source_lct="dp@Legion",
        target_lct="dp@Thor",
        task_type="cognition",
        operation="perception",
        atp_budget=300.0,
    )

    proof_result, settlement = client.delegate_task(flow_task, server, legion_priv)
    check("T6.1 Delegation succeeded", proof_result is not None)
    check("T6.2 Settlement COMMIT", settlement == "COMMIT")
    check("T6.3 Quality ≥ 0.7", proof_result.quality_score >= 0.7)
    check("T6.4 Task completed", flow_task.task_id in server.completed)
    check("T6.5 ATP consumed", proof_result.atp_consumed == 240.0)

    # Server status
    status = server.get_status("dp@Legion")
    check("T6.6 No active tasks", status["tasks_running"] == 0)

    # Cancel (task already completed, so cancel should fail)
    cancel = server.cancel_task("flow-001")
    check("T6.7 Cancel completed task fails", not cancel["cancelled"])

    # ── §5  Server Validation ──────────────────────────────────────
    print("\n§5b Server Validation")

    # Invalid signature
    bad_task = FederationTask(
        task_id="bad-001", source_lct="a", target_lct="b",
        task_type="cognition", operation="perception", atp_budget=100.0,
    )
    valid, reason = server.validate_task(bad_task, "wrong_signature", thor_priv)
    check("T7.1 Invalid sig rejected", not valid)
    check("T7.2 Reason invalid_signature", reason == "invalid_signature")

    # Permission denied
    bad_perm_task = FederationTask(
        task_id="bad-002", source_lct="a", target_lct="b",
        task_type="perception", operation="perception", atp_budget=100.0,
    )
    sig = FederationCrypto.sign_task(bad_perm_task, thor_priv)
    valid2, reason2 = server.validate_task(bad_perm_task, sig, thor_priv)
    check("T7.3 Perception cannot delegate", not valid2)
    check("T7.4 Reason delegation_not_permitted", reason2 == "delegation_not_permitted")

    # At capacity
    server.max_concurrent = 0  # Simulate full
    cap_task = FederationTask(
        task_id="cap-001", source_lct="a", target_lct="b",
        task_type="cognition", operation="perception", atp_budget=100.0,
    )
    sig3 = FederationCrypto.sign_task(cap_task, thor_priv)
    valid3, reason3 = server.validate_task(cap_task, sig3, thor_priv)
    check("T7.5 At capacity rejected", not valid3)
    check("T7.6 Reason at_capacity", reason3 == "at_capacity")
    server.max_concurrent = 10  # Restore

    # ── §5  DoS Protection ─────────────────────────────────────────
    print("\n§5c DoS Protection")

    rl = RateLimiter(max_per_minute=5, max_concurrent=2)
    check("T8.1 First request allowed", rl.allow_request())
    check("T8.2 Second request allowed", rl.allow_request())
    check("T8.3 Third blocked (concurrent)", not rl.allow_request())
    rl.release()
    check("T8.4 After release, allowed", rl.allow_request())
    rl.release()
    rl.release()
    check("T8.5 4th request", rl.allow_request())
    check("T8.6 5th request", rl.allow_request())
    check("T8.7 6th blocked (rate limit)", not rl.allow_request())

    # Timeout enforcement
    check("T8.8 Within timeout", TimeoutEnforcer.check_timeout(45.0, 60))
    check("T8.9 Exceeds timeout", not TimeoutEnforcer.check_timeout(100.0, 60))

    timeout_ledger = ATPLedger()
    timeout_ledger.create_account("test", 500.0)
    timeout_lock = timeout_ledger.lock_atp("test", 200.0)
    check("T8.10 Timeout rollback", TimeoutEnforcer.handle_timeout(timeout_lock, timeout_ledger))
    check("T8.11 ATP restored after timeout", timeout_ledger.available["test"] == 500.0)

    # ── §6  Deployment Configuration ───────────────────────────────
    print("\n§6 Deployment Architecture")

    check("T9.1 3 deployment configs", len(DEPLOYMENT_CONFIGS) == 3)
    check("T9.2 Legion is server", DEPLOYMENT_CONFIGS["Legion"].role == "server")
    check("T9.3 Thor is client", DEPLOYMENT_CONFIGS["Thor"].role == "client")
    check("T9.4 Sprout is client", DEPLOYMENT_CONFIGS["Sprout"].role == "client")
    check("T9.5 Legion port 8080", DEPLOYMENT_CONFIGS["Legion"].port == 8080)
    check("T9.6 Thor has 2 servers", len(DEPLOYMENT_CONFIGS["Thor"].remote_servers) == 2)
    check("T9.7 Sprout has 2 servers", len(DEPLOYMENT_CONFIGS["Sprout"].remote_servers) == 2)
    check("T9.8 Legion sage budget 2000", DEPLOYMENT_CONFIGS["Legion"].sage_budget == 2000.0)

    # ── §8  Success Criteria ───────────────────────────────────────
    print("\n§8 Success Criteria")

    criteria = SuccessCriteria(
        delegation_works=True, bidirectional=True, signatures_verified=True,
        atp_accurate=True, quality_settlement=True, permissions_enforced=True,
        delegation_latency_ms=45.0, proof_verification_ms=1.0,
        settlement_ms=5.0, max_concurrent=10,
        signatures_before_exec=True, permission_checks=True,
        atp_lock_prevents_double_spend=True, resource_limits=True,
        quality_thresholds=True,
    )
    check("T10.1 Functional pass", criteria.functional_pass())
    check("T10.2 Performance pass", criteria.performance_pass())
    check("T10.3 Security pass", criteria.security_pass())

    # Failing criteria
    bad_criteria = SuccessCriteria(delegation_latency_ms=200.0, max_concurrent=5)
    check("T10.4 Bad perf fails", not bad_criteria.performance_pass())
    check("T10.5 Bad functional fails", not bad_criteria.functional_pass())

    # ── §10  Risk Mitigation ───────────────────────────────────────
    print("\n§10 Risk Mitigation")

    risk_ledger = ATPLedger()
    risk_ledger.create_account("risk_test", 500.0)
    risk_lock = risk_ledger.lock_atp("risk_test", 200.0)

    # Risk 1: Network failure
    r1 = RiskMitigator.mitigate_network_failure(risk_lock, risk_ledger)
    check("T11.1 Network failure mitigated", r1["mitigated"])
    check("T11.2 ATP rolled back", risk_ledger.available["risk_test"] == 500.0)

    # Risk 2: Signature failure
    test_task = FederationTask(
        task_id="risk-001", source_lct="a", target_lct="b",
        task_type="cognition", operation="perception", atp_budget=100.0,
    )
    good_sig = FederationCrypto.sign_task(test_task, legion_priv)
    r2_good = RiskMitigator.mitigate_signature_failure(test_task, good_sig, legion_priv)
    check("T11.3 Good signature proceeds", r2_good["action"] == "proceed")
    r2_bad = RiskMitigator.mitigate_signature_failure(test_task, "bad_sig", legion_priv)
    check("T11.4 Bad signature rejected", r2_bad["action"] == "reject_task")

    # Risk 3: ATP accounting
    r3 = RiskMitigator.mitigate_atp_error(risk_ledger, "risk_test", 500.0)
    check("T11.5 ATP reconciled", r3["reconciled"])
    check("T11.6 No discrepancy", r3["discrepancy"] < 0.01)

    # Risk 4: Resource exhaustion
    r4_ok = RiskMitigator.mitigate_resource_exhaustion(5, 10)
    check("T11.7 Not at capacity", not r4_ok["at_capacity"])
    check("T11.8 Accept action", r4_ok["action"] == "accept")
    r4_full = RiskMitigator.mitigate_resource_exhaustion(10, 10)
    check("T11.9 At capacity", r4_full["at_capacity"])
    check("T11.10 Reject action", r4_full["action"] == "reject_new")
    check("T11.11 100% utilization", r4_full["utilization"] == 1.0)

    # ── Cross-cutting: E2E multi-delegation ────────────────────────
    print("\n§9 E2E Multi-Delegation Test")

    e2e_ledger = ATPLedger()
    e2e_ledger.create_account("alice@Legion", 2000.0)
    e2e_ledger.create_account("bob@Thor", 100.0)
    e2e_ledger.create_account("carol@Sprout", 50.0)

    e2e_server = FederationServer("Legion", legion_priv, e2e_ledger)
    e2e_client_thor = FederationClient("Thor", thor_priv, e2e_ledger)

    # 3 concurrent delegations
    tasks = []
    for i in range(3):
        t = FederationTask(
            task_id=f"e2e-{i:03d}",
            source_lct="alice@Legion",
            target_lct="bob@Thor",
            task_type="cognition",
            operation="perception",
            atp_budget=200.0,
        )
        tasks.append(t)

    results = []
    for t in tasks:
        proof_r, settle = e2e_client_thor.delegate_task(t, e2e_server, legion_priv)
        results.append((proof_r, settle))

    check("T12.1 All 3 delegations succeeded", all(r[0] is not None for r in results))
    check("T12.2 All 3 COMMIT", all(r[1] == "COMMIT" for r in results))
    # Each task: budget=200, consumed=200*0.8=160
    check("T12.3 Alice paid 3×160=480 ATP",
           abs(e2e_ledger.balances["alice@Legion"] - (2000.0 - 480.0)) < 0.01)
    check("T12.4 Bob earned 3×160=480 ATP",
           abs(e2e_ledger.balances["bob@Thor"] - (100.0 + 480.0)) < 0.01)

    # 4th delegation should still work (Alice has 1280 remaining)
    t4 = FederationTask(
        task_id="e2e-003",
        source_lct="alice@Legion",
        target_lct="bob@Thor",
        task_type="cognition",
        operation="perception",
        atp_budget=200.0,
    )
    p4, s4 = e2e_client_thor.delegate_task(t4, e2e_server, legion_priv)
    check("T12.5 4th delegation works", p4 is not None)

    # ── Summary ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Multi-Machine SAGE Federation: {passed}/{total} checks passed")
    if failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {failed} checks FAILED")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    run_tests()
