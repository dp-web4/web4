#!/usr/bin/env python3
"""
End-to-End Integration Prototype
==================================

Chains the full Web4 stack into a single coherent flow:

  Identity → Permissions → ATP → Federation → Reputation

This prototype proves that the independently-built reference implementations
can wire together despite the divergences found in the coherence analysis.

Each phase uses actual logic from the spec implementations, bridged by
adapter interfaces that resolve the cross-spec gaps identified in
cross_spec_coherence_analysis.py.

The flow:
  1. IDENTITY:    Create LCT identities for Alice (Thor) and Bob (Sprout)
  2. PERMISSIONS: Verify task authorization via LUPS
  3. ATP:         Lock, transfer, settle ATP for task delegation
  4. FEDERATION:  Delegate task from Thor to Sprout with quality gate
  5. REPUTATION:  Update T3 tensors based on task outcome
  6. LIFECYCLE:   Verify the complete audit trail

Session: Legion Autonomous 2026-02-26
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# SECTION 1: IDENTITY LAYER (from lct_identity_system.py)
# ============================================================================

@dataclass
class Lineage:
    """Who created/authorized this agent (§2.1 LCT Identity Spec)."""
    creator_id: str
    creator_pubkey: str = ""
    creation_timestamp: float = 0.0

    @property
    def hierarchy(self) -> List[str]:
        return self.creator_id.split(".")

    @property
    def root_creator(self) -> str:
        return self.hierarchy[0]

    @property
    def depth(self) -> int:
        return len(self.hierarchy)


@dataclass
class Context:
    """Platform/environment where agent runs (§2.2 LCT Identity Spec)."""
    platform_id: str
    platform_pubkey: str = ""
    capabilities: List[str] = field(default_factory=list)

    @property
    def platform_name(self) -> str:
        if ":" in self.platform_id:
            return self.platform_id.split(":")[-1]
        return self.platform_id


@dataclass
class Task:
    """What the agent is authorized for (§2.3 LCT Identity Spec)."""
    task_id: str
    permissions: Set[str] = field(default_factory=set)
    resource_limits: Dict[str, Any] = field(default_factory=dict)

    @property
    def task_type(self) -> str:
        return self.task_id.split(".")[0]

    @property
    def task_variant(self) -> Optional[str]:
        parts = self.task_id.split(".")
        return parts[1] if len(parts) > 1 else None

    @property
    def is_delegation(self) -> bool:
        return self.task_type == "delegation"


@dataclass
class IdentityCertificate:
    """Complete identity with signature chain (§4 LCT Identity Spec)."""
    lct_id: str
    lineage: Lineage
    context: Context
    task: Task
    signatures: Dict[str, str] = field(default_factory=dict)
    validity: Dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0

    @staticmethod
    def create(lineage: Lineage, context: Context, task: Task,
               creator_key: str = "", platform_key: str = "",
               validity_hours: int = 24) -> "IdentityCertificate":
        lct_id = f"lct:web4:agent:{lineage.creator_id}@{context.platform_id}#{task.task_id}"
        now = time.time()

        # Signature chain (§4.2)
        lineage_data = f"{lineage.creator_id}:{task.task_id}:{now}"
        creator_sig = hashlib.sha256(f"{creator_key}:{lineage_data}".encode()).hexdigest()[:16]

        context_data = f"{context.platform_id}:{creator_sig}:{now}"
        platform_sig = hashlib.sha256(f"{platform_key}:{context_data}".encode()).hexdigest()[:16]

        return IdentityCertificate(
            lct_id=lct_id,
            lineage=lineage,
            context=context,
            task=task,
            signatures={"creator": creator_sig, "platform": platform_sig},
            validity={"not_before": now, "not_after": now + validity_hours * 3600},
            created_at=now,
        )

    def verify(self, creator_key: str = "", platform_key: str = "") -> Tuple[bool, str]:
        if not self.signatures:
            return False, "No signatures"

        # Recreate creator signature
        lineage_data = f"{self.lineage.creator_id}:{self.task.task_id}:{self.created_at}"
        expected_creator = hashlib.sha256(f"{creator_key}:{lineage_data}".encode()).hexdigest()[:16]
        if self.signatures.get("creator") != expected_creator:
            return False, "Creator signature mismatch"

        # Recreate platform signature
        context_data = f"{self.context.platform_id}:{self.signatures['creator']}:{self.created_at}"
        expected_platform = hashlib.sha256(f"{platform_key}:{context_data}".encode()).hexdigest()[:16]
        if self.signatures.get("platform") != expected_platform:
            return False, "Platform signature mismatch"

        return True, "Valid"


# ============================================================================
# SECTION 2: PERMISSION LAYER (from lct_unified_permission_standard.py)
# ============================================================================

@dataclass
class TaskPermissionConfig:
    """LUPS permission configuration for a task type."""
    permissions: Set[str]
    can_delegate: bool
    can_execute_code: bool
    code_execution_level: Optional[str] = None


# LUPS v1.0 — 10 unified task types (§3)
UNIFIED_TASK_PERMISSIONS: Dict[str, TaskPermissionConfig] = {
    "perception": TaskPermissionConfig(
        permissions={"atp:read", "network:http"},
        can_delegate=False, can_execute_code=False,
    ),
    "planning": TaskPermissionConfig(
        permissions={"atp:read", "network:http"},
        can_delegate=False, can_execute_code=False,
    ),
    "planning.strategic": TaskPermissionConfig(
        permissions={"atp:read", "atp:write", "network:http", "storage:read"},
        can_delegate=False, can_execute_code=False,
    ),
    "execution.safe": TaskPermissionConfig(
        permissions={"atp:read", "exec:safe", "network:http", "storage:read"},
        can_delegate=False, can_execute_code=True,
        code_execution_level="sandbox",
    ),
    "execution.code": TaskPermissionConfig(
        permissions={"atp:read", "atp:write", "exec:code", "exec:network",
                     "network:http", "network:ws", "storage:read", "storage:write"},
        can_delegate=False, can_execute_code=True,
        code_execution_level="full",
    ),
    "delegation.federation": TaskPermissionConfig(
        permissions={"atp:read", "atp:write", "federation:delegate",
                     "federation:execute", "network:http", "network:p2p"},
        can_delegate=True, can_execute_code=False,
    ),
    "cognition": TaskPermissionConfig(
        permissions={"atp:read", "atp:write", "exec:safe", "network:http",
                     "network:ws", "storage:read", "storage:write"},
        can_delegate=True, can_execute_code=True,
        code_execution_level="sandbox",
    ),
    "cognition.sage": TaskPermissionConfig(
        permissions={"atp:read", "atp:write", "exec:code", "exec:network",
                     "federation:delegate", "network:all", "storage:all"},
        can_delegate=True, can_execute_code=True,
        code_execution_level="full",
    ),
    "admin.readonly": TaskPermissionConfig(
        permissions={"atp:read", "admin:read", "network:http", "storage:read"},
        can_delegate=False, can_execute_code=False,
    ),
    "admin.full": TaskPermissionConfig(
        permissions={"atp:all", "federation:all", "exec:all", "network:all",
                     "storage:all", "admin:full"},
        can_delegate=True, can_execute_code=True,
        code_execution_level="full",
    ),
}


@dataclass
class UnifiedResourceLimits:
    """Resource limits per task type."""
    atp_budget: float = 0.0
    memory_mb: int = 1024
    cpu_cores: int = 1


UNIFIED_RESOURCE_LIMITS: Dict[str, UnifiedResourceLimits] = {
    "perception": UnifiedResourceLimits(200.0, 2048, 2),
    "planning": UnifiedResourceLimits(500.0, 2048, 2),
    "planning.strategic": UnifiedResourceLimits(500.0, 4096, 4),
    "execution.safe": UnifiedResourceLimits(200.0, 2048, 2),
    "execution.code": UnifiedResourceLimits(1000.0, 8192, 8),
    "delegation.federation": UnifiedResourceLimits(1000.0, 4096, 2),
    "cognition": UnifiedResourceLimits(1000.0, 16384, 8),
    "cognition.sage": UnifiedResourceLimits(2000.0, 32768, 16),
    "admin.readonly": UnifiedResourceLimits(100.0, 1024, 1),
    "admin.full": UnifiedResourceLimits(float("inf"), 1048576, 128),
}


class PermissionChecker:
    """LUPS permission checker with wildcard support."""

    def check_permission(self, task_type: str, permission: str) -> bool:
        config = UNIFIED_TASK_PERMISSIONS.get(task_type)
        if not config:
            return False
        if permission in config.permissions:
            return True
        # Wildcard check (category:all covers all in category)
        category = permission.split(":")[0]
        wildcard = f"{category}:all"
        if wildcard in config.permissions:
            return True
        # admin:full covers all admin:*
        if category == "admin" and "admin:full" in config.permissions:
            return True
        return False

    def can_delegate(self, task_type: str) -> bool:
        config = UNIFIED_TASK_PERMISSIONS.get(task_type)
        return config.can_delegate if config else False

    def validate_operation(self, task_type: str, operation: str,
                          atp_cost: float = 0.0) -> Tuple[bool, str]:
        config = UNIFIED_TASK_PERMISSIONS.get(task_type)
        if not config:
            return False, f"Unknown task type: {task_type}"
        if not self.check_permission(task_type, operation):
            return False, f"Permission denied: {task_type} cannot {operation}"
        limits = UNIFIED_RESOURCE_LIMITS.get(task_type)
        if limits and atp_cost > limits.atp_budget:
            return False, f"ATP cost {atp_cost} exceeds budget {limits.atp_budget}"
        return True, "Authorized"


# ============================================================================
# SECTION 3: ATP LAYER (from federation_consensus_atp.py)
# ============================================================================

@dataclass
class ATPAccount:
    """ATP account with two-phase commit (Layer 1 ATP Spec)."""
    lct_id: str
    total: float = 0.0
    available: float = 0.0
    locked: float = 0.0
    history: List[Dict] = field(default_factory=list)

    def lock(self, amount: float, reason: str = "") -> bool:
        if amount > self.available:
            return False
        self.available -= amount
        self.locked += amount
        self.history.append({
            "action": "lock", "amount": amount, "reason": reason,
            "timestamp": time.time(),
        })
        return True

    def commit(self, amount: float, destination: str = "") -> bool:
        if amount > self.locked:
            return False
        self.locked -= amount
        self.total -= amount
        # Refund excess lock
        excess = self.locked
        if excess > 0:
            self.available += excess
            self.locked = 0.0
        self.history.append({
            "action": "commit", "amount": amount, "destination": destination,
            "timestamp": time.time(),
        })
        return True

    def rollback(self, amount: float = 0.0) -> bool:
        rollback_amount = amount if amount > 0 else self.locked
        if rollback_amount > self.locked:
            return False
        self.locked -= rollback_amount
        self.available += rollback_amount
        self.history.append({
            "action": "rollback", "amount": rollback_amount,
            "timestamp": time.time(),
        })
        return True

    def credit(self, amount: float, source: str = "") -> None:
        self.total += amount
        self.available += amount
        self.history.append({
            "action": "credit", "amount": amount, "source": source,
            "timestamp": time.time(),
        })


class ATPLedger:
    """ATP ledger managing accounts and transfers."""

    TRANSFER_FEE = 0.05  # 5% fee per transfer

    def __init__(self):
        self.accounts: Dict[str, ATPAccount] = {}
        self.pending_transfers: Dict[str, Dict] = {}
        self.completed_transfers: List[Dict] = []

    def create_account(self, lct_id: str, initial_balance: float = 0.0) -> ATPAccount:
        account = ATPAccount(lct_id=lct_id, total=initial_balance, available=initial_balance)
        self.accounts[lct_id] = account
        return account

    def get_account(self, lct_id: str) -> Optional[ATPAccount]:
        return self.accounts.get(lct_id)

    def lock_transfer(self, transfer_id: str, source: str, amount: float) -> Tuple[bool, str]:
        account = self.accounts.get(source)
        if not account:
            return False, f"Account not found: {source}"
        fee = amount * self.TRANSFER_FEE
        total_cost = amount + fee
        if not account.lock(total_cost, f"transfer:{transfer_id}"):
            return False, f"Insufficient balance: need {total_cost}, have {account.available}"
        self.pending_transfers[transfer_id] = {
            "source": source, "amount": amount, "fee": fee,
            "total_locked": total_cost, "status": "locked",
        }
        return True, f"Locked {total_cost} ATP (amount={amount}, fee={fee})"

    def commit_transfer(self, transfer_id: str, destination: str) -> Tuple[bool, str]:
        transfer = self.pending_transfers.get(transfer_id)
        if not transfer or transfer["status"] != "locked":
            return False, f"No pending transfer: {transfer_id}"

        source_account = self.accounts.get(transfer["source"])
        dest_account = self.accounts.get(destination)
        if not source_account or not dest_account:
            return False, "Account not found"

        # Commit: deduct from source, credit to destination
        if not source_account.commit(transfer["total_locked"]):
            return False, "Commit failed on source account"
        dest_account.credit(transfer["amount"], transfer["source"])

        transfer["status"] = "committed"
        transfer["destination"] = destination
        self.completed_transfers.append(transfer)
        del self.pending_transfers[transfer_id]

        return True, f"Transferred {transfer['amount']} ATP to {destination}"

    def rollback_transfer(self, transfer_id: str) -> Tuple[bool, str]:
        transfer = self.pending_transfers.get(transfer_id)
        if not transfer or transfer["status"] != "locked":
            return False, f"No pending transfer: {transfer_id}"

        source_account = self.accounts.get(transfer["source"])
        if not source_account:
            return False, "Source account not found"

        source_account.rollback(transfer["total_locked"])
        transfer["status"] = "rolled_back"
        del self.pending_transfers[transfer_id]

        return True, f"Rolled back {transfer['total_locked']} ATP"


# ============================================================================
# SECTION 4: FEDERATION LAYER (from multi_machine_sage_federation.py)
# ============================================================================

class TaskStatus(Enum):
    CREATED = "created"
    DELEGATED = "delegated"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SETTLED = "settled"


@dataclass
class FederationTask:
    """A task delegated across federation platforms."""
    task_id: str
    delegator_lct: str
    executor_lct: str
    task_type: str
    description: str
    atp_budget: float
    quality_threshold: float = 0.7
    status: TaskStatus = TaskStatus.CREATED
    quality_score: float = 0.0
    result_hash: str = ""
    atp_consumed: float = 0.0
    timeline: List[Dict] = field(default_factory=list)

    def record_event(self, event: str, details: str = ""):
        self.timeline.append({
            "event": event, "details": details, "timestamp": time.time(),
        })


class FederationProcessor:
    """Processes federation task delegation with ATP settlement."""

    def __init__(self, ledger: ATPLedger, permission_checker: PermissionChecker):
        self.ledger = ledger
        self.checker = permission_checker
        self.tasks: Dict[str, FederationTask] = {}

    def delegate_task(self, task: FederationTask) -> Tuple[bool, str]:
        """Full delegation flow: validate → lock ATP → delegate."""
        # Step 1: Verify delegator has delegation permission
        delegator_task_type = self._extract_task_type(task.delegator_lct)
        if not self.checker.can_delegate(delegator_task_type):
            return False, f"Task type '{delegator_task_type}' cannot delegate"

        # Step 2: Verify federation permission
        ok, reason = self.checker.validate_operation(
            delegator_task_type, "federation:delegate", task.atp_budget
        )
        if not ok:
            return False, reason

        # Step 3: Lock ATP for the task
        transfer_id = f"fed:{task.task_id}"
        ok, reason = self.ledger.lock_transfer(transfer_id, task.delegator_lct, task.atp_budget)
        if not ok:
            return False, f"ATP lock failed: {reason}"

        # Step 4: Record delegation
        task.status = TaskStatus.DELEGATED
        task.record_event("delegated", f"ATP locked: {task.atp_budget}")
        self.tasks[task.task_id] = task

        return True, f"Task {task.task_id} delegated with {task.atp_budget} ATP locked"

    def execute_task(self, task_id: str, quality_score: float,
                     atp_consumed: float) -> Tuple[bool, str]:
        """Record task execution result."""
        task = self.tasks.get(task_id)
        if not task:
            return False, f"Task not found: {task_id}"
        if task.status != TaskStatus.DELEGATED:
            return False, f"Task not in delegated state: {task.status.value}"

        task.status = TaskStatus.COMPLETED
        task.quality_score = quality_score
        task.atp_consumed = atp_consumed
        task.result_hash = hashlib.sha256(f"{task_id}:{quality_score}".encode()).hexdigest()[:16]
        task.record_event("completed", f"quality={quality_score}, consumed={atp_consumed}")

        return True, f"Task completed: quality={quality_score}"

    def settle_task(self, task_id: str) -> Tuple[bool, str, Dict]:
        """Quality-based settlement: commit if quality >= threshold, else rollback."""
        task = self.tasks.get(task_id)
        if not task:
            return False, f"Task not found: {task_id}", {}
        if task.status != TaskStatus.COMPLETED:
            return False, f"Task not completed: {task.status.value}", {}

        transfer_id = f"fed:{task.task_id}"
        settlement = {
            "task_id": task_id,
            "quality_score": task.quality_score,
            "quality_threshold": task.quality_threshold,
            "atp_budget": task.atp_budget,
            "atp_consumed": task.atp_consumed,
        }

        if task.quality_score >= task.quality_threshold:
            # Quality met: commit (pay executor)
            ok, reason = self.ledger.commit_transfer(transfer_id, task.executor_lct)
            if not ok:
                return False, f"Settlement commit failed: {reason}", settlement
            settlement["outcome"] = "committed"
            settlement["executor_paid"] = task.atp_budget
            task.status = TaskStatus.SETTLED
            task.record_event("settled", f"committed: executor paid {task.atp_budget}")
        else:
            # Quality not met: rollback (refund delegator)
            ok, reason = self.ledger.rollback_transfer(transfer_id)
            if not ok:
                return False, f"Settlement rollback failed: {reason}", settlement
            settlement["outcome"] = "rolled_back"
            settlement["delegator_refunded"] = True
            task.status = TaskStatus.FAILED
            task.record_event("settled", "rolled_back: quality below threshold")

        return True, f"Settlement: {settlement['outcome']}", settlement

    def _extract_task_type(self, lct_id: str) -> str:
        """Extract task type from LCT ID (Format A: ...#task_type)."""
        if "#" in lct_id:
            return lct_id.split("#")[-1]
        return "unknown"


# ============================================================================
# SECTION 5: REPUTATION LAYER (from t3v3_reputation_engine.py)
# ============================================================================

@dataclass
class T3Tensor:
    """Trust tensor with canonical 3 dimensions."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def update_from_task(self, quality_score: float, task_type: str,
                         weight: float = 0.02) -> "T3Tensor":
        """Update tensor based on task outcome (§R7 spec)."""
        delta = weight * (quality_score - 0.5)

        # Dimension-specific updates based on task type
        talent_delta = delta
        training_delta = delta
        temperament_delta = delta

        if task_type in ("execution.code", "cognition", "cognition.sage"):
            talent_delta *= 1.5  # Technical tasks weight talent more
        if task_type in ("planning", "planning.strategic"):
            training_delta *= 1.5  # Planning tasks weight training more
        if task_type == "delegation.federation":
            temperament_delta *= 1.5  # Delegation tasks weight temperament more

        new_talent = max(0.0, min(1.0, self.talent + talent_delta))
        new_training = max(0.0, min(1.0, self.training + training_delta))
        new_temperament = max(0.0, min(1.0, self.temperament + temperament_delta))

        return T3Tensor(
            talent=round(new_talent, 6),
            training=round(new_training, 6),
            temperament=round(new_temperament, 6),
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "talent": self.talent,
            "training": self.training,
            "temperament": self.temperament,
            "composite": round(self.composite, 6),
        }


@dataclass
class ReputationRecord:
    """Reputation record for an entity."""
    lct_id: str
    t3: T3Tensor = field(default_factory=T3Tensor)
    task_history: List[Dict] = field(default_factory=list)
    total_tasks: int = 0
    successful_tasks: int = 0

    @property
    def success_rate(self) -> float:
        return self.successful_tasks / self.total_tasks if self.total_tasks > 0 else 0.0

    def record_task_outcome(self, task_id: str, quality_score: float,
                           task_type: str, was_settled: bool):
        """Update reputation based on task settlement."""
        old_t3 = self.t3.to_dict()
        self.t3 = self.t3.update_from_task(quality_score, task_type)
        new_t3 = self.t3.to_dict()

        self.total_tasks += 1
        if was_settled:
            self.successful_tasks += 1

        self.task_history.append({
            "task_id": task_id,
            "quality_score": quality_score,
            "task_type": task_type,
            "settled": was_settled,
            "t3_before": old_t3,
            "t3_after": new_t3,
            "t3_delta": {
                k: round(new_t3[k] - old_t3[k], 6)
                for k in ["talent", "training", "temperament", "composite"]
            },
            "timestamp": time.time(),
        })


class ReputationEngine:
    """Manages reputation records for all entities."""

    def __init__(self):
        self.records: Dict[str, ReputationRecord] = {}

    def get_or_create(self, lct_id: str) -> ReputationRecord:
        if lct_id not in self.records:
            self.records[lct_id] = ReputationRecord(lct_id=lct_id)
        return self.records[lct_id]

    def process_settlement(self, settlement: Dict, task: FederationTask):
        """Update reputation for both delegator and executor after settlement."""
        delegator = self.get_or_create(task.delegator_lct)
        executor = self.get_or_create(task.executor_lct)

        was_committed = settlement.get("outcome") == "committed"

        # Executor reputation based on quality
        executor.record_task_outcome(
            task.task_id, task.quality_score, task.task_type, was_committed
        )

        # Delegator reputation based on delegation judgment
        # Good delegation = chose right executor (quality >= threshold)
        delegation_quality = min(1.0, task.quality_score / task.quality_threshold) if task.quality_threshold > 0 else 0.5
        delegator.record_task_outcome(
            task.task_id, delegation_quality, "delegation.federation", was_committed
        )


# ============================================================================
# SECTION 6: AUDIT TRAIL (from society_lifecycle.py)
# ============================================================================

@dataclass
class AuditEntry:
    """Immutable audit entry with hash chain."""
    entry_id: str
    entry_type: str
    data: Dict
    timestamp: float
    prev_hash: str = ""
    entry_hash: str = ""

    def compute_hash(self) -> str:
        content = json.dumps({
            "entry_id": self.entry_id,
            "entry_type": self.entry_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class AuditTrail:
    """Append-only hash-chained audit trail."""

    def __init__(self):
        self.entries: List[AuditEntry] = []
        self.entry_count = 0

    def append(self, entry_type: str, data: Dict) -> AuditEntry:
        prev_hash = self.entries[-1].entry_hash if self.entries else "genesis"
        self.entry_count += 1
        entry = AuditEntry(
            entry_id=f"audit:{self.entry_count}",
            entry_type=entry_type,
            data=data,
            timestamp=time.time(),
            prev_hash=prev_hash,
        )
        entry.entry_hash = entry.compute_hash()
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> Tuple[bool, str]:
        """Verify hash chain integrity."""
        for i, entry in enumerate(self.entries):
            # Verify hash
            if entry.entry_hash != entry.compute_hash():
                return False, f"Hash mismatch at entry {entry.entry_id}"
            # Verify chain link
            if i == 0:
                if entry.prev_hash != "genesis":
                    return False, "First entry prev_hash != genesis"
            else:
                if entry.prev_hash != self.entries[i - 1].entry_hash:
                    return False, f"Chain break at entry {entry.entry_id}"
        return True, f"Chain valid: {len(self.entries)} entries"

    def query(self, entry_type: str = None) -> List[AuditEntry]:
        if entry_type:
            return [e for e in self.entries if e.entry_type == entry_type]
        return list(self.entries)


# ============================================================================
# SECTION 7: E2E INTEGRATION ORCHESTRATOR
# ============================================================================

class E2EOrchestrator:
    """
    Orchestrates the full Web4 stack flow:
    Identity → Permissions → ATP → Federation → Reputation → Audit
    """

    def __init__(self):
        self.permission_checker = PermissionChecker()
        self.ledger = ATPLedger()
        self.federation = FederationProcessor(self.ledger, self.permission_checker)
        self.reputation = ReputationEngine()
        self.audit = AuditTrail()
        self.identities: Dict[str, IdentityCertificate] = {}

    def create_identity(self, creator_id: str, platform_id: str, task_id: str,
                       creator_key: str = "", platform_key: str = "",
                       initial_atp: float = 1000.0) -> IdentityCertificate:
        """Phase 1: Create identity + ATP account."""
        lineage = Lineage(creator_id=creator_id, creator_pubkey=creator_key)
        context = Context(platform_id=platform_id, platform_pubkey=platform_key)
        task = Task(task_id=task_id)

        cert = IdentityCertificate.create(lineage, context, task, creator_key, platform_key)
        self.identities[cert.lct_id] = cert

        # Create ATP account
        self.ledger.create_account(cert.lct_id, initial_atp)

        # Audit
        self.audit.append("identity_created", {
            "lct_id": cert.lct_id,
            "creator": creator_id,
            "platform": platform_id,
            "task": task_id,
            "initial_atp": initial_atp,
        })

        return cert

    def delegate_task(self, delegator_lct: str, executor_lct: str,
                     task_type: str, description: str,
                     atp_budget: float, quality_threshold: float = 0.7) -> Tuple[bool, str, Optional[FederationTask]]:
        """Phase 2-4: Validate permissions → Lock ATP → Delegate."""
        task = FederationTask(
            task_id=f"task:{hashlib.sha256(f'{delegator_lct}:{time.time()}'.encode()).hexdigest()[:8]}",
            delegator_lct=delegator_lct,
            executor_lct=executor_lct,
            task_type=task_type,
            description=description,
            atp_budget=atp_budget,
            quality_threshold=quality_threshold,
        )

        ok, reason = self.federation.delegate_task(task)
        if not ok:
            self.audit.append("delegation_failed", {
                "delegator": delegator_lct,
                "executor": executor_lct,
                "reason": reason,
            })
            return False, reason, None

        self.audit.append("task_delegated", {
            "task_id": task.task_id,
            "delegator": delegator_lct,
            "executor": executor_lct,
            "task_type": task_type,
            "atp_budget": atp_budget,
        })

        return True, reason, task

    def complete_task(self, task_id: str, quality_score: float,
                     atp_consumed: float) -> Tuple[bool, str]:
        """Phase 4: Record task completion."""
        ok, reason = self.federation.execute_task(task_id, quality_score, atp_consumed)
        if ok:
            self.audit.append("task_completed", {
                "task_id": task_id,
                "quality_score": quality_score,
                "atp_consumed": atp_consumed,
            })
        return ok, reason

    def settle_task(self, task_id: str) -> Tuple[bool, str, Dict]:
        """Phase 5-6: Settle ATP + Update reputation."""
        ok, reason, settlement = self.federation.settle_task(task_id)
        if not ok:
            return ok, reason, settlement

        # Update reputation
        task = self.federation.tasks.get(task_id)
        if task:
            self.reputation.process_settlement(settlement, task)

        self.audit.append("task_settled", settlement)

        return True, reason, settlement

    def get_full_state(self) -> Dict:
        """Get complete state for verification."""
        chain_valid, chain_msg = self.audit.verify_chain()
        return {
            "identities": len(self.identities),
            "atp_accounts": {
                lct: {"total": a.total, "available": a.available, "locked": a.locked}
                for lct, a in self.ledger.accounts.items()
            },
            "federation_tasks": {
                tid: {"status": t.status.value, "quality": t.quality_score}
                for tid, t in self.federation.tasks.items()
            },
            "reputation": {
                lct: {
                    "t3": r.t3.to_dict(),
                    "total_tasks": r.total_tasks,
                    "success_rate": r.success_rate,
                }
                for lct, r in self.reputation.records.items()
            },
            "audit": {
                "entries": len(self.audit.entries),
                "chain_valid": chain_valid,
                "chain_message": chain_msg,
            },
        }


# ============================================================================
# SECTION 8: TEST SUITE
# ============================================================================

def run_tests():
    """Full E2E integration test suite."""
    checks_passed = 0
    checks_failed = 0
    total_checks = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal checks_passed, checks_failed, total_checks
        total_checks += 1
        if condition:
            checks_passed += 1
        else:
            checks_failed += 1
            print(f"  FAIL: {name}: {detail}")

    # ====================================================================
    # SCENARIO 1: Successful delegation flow
    # Alice@Thor delegates code execution to Bob@Sprout
    # ====================================================================
    print("S1: Successful delegation (Alice@Thor -> Bob@Sprout)")
    orch = E2EOrchestrator()

    # Phase 1: Identity creation
    alice_cert = orch.create_identity(
        creator_id="alice", platform_id="Thor",
        task_id="delegation.federation",
        creator_key="alice_key", platform_key="thor_key",
        initial_atp=1000.0,
    )
    bob_cert = orch.create_identity(
        creator_id="bob", platform_id="Sprout",
        task_id="execution.code",
        creator_key="bob_key", platform_key="sprout_key",
        initial_atp=500.0,
    )

    check("S1.1 Alice LCT format correct",
          alice_cert.lct_id == "lct:web4:agent:alice@Thor#delegation.federation")
    check("S1.2 Bob LCT format correct",
          bob_cert.lct_id == "lct:web4:agent:bob@Sprout#execution.code")
    check("S1.3 Alice identity verifies",
          alice_cert.verify("alice_key", "thor_key")[0])
    check("S1.4 Bob identity verifies",
          bob_cert.verify("bob_key", "sprout_key")[0])
    check("S1.5 Alice ATP account created",
          orch.ledger.get_account(alice_cert.lct_id).available == 1000.0)
    check("S1.6 Bob ATP account created",
          orch.ledger.get_account(bob_cert.lct_id).available == 500.0)

    # Phase 2: Permission check (pre-delegation)
    check("S1.7 Alice can delegate",
          orch.permission_checker.can_delegate("delegation.federation"))
    check("S1.8 Bob cannot delegate",
          not orch.permission_checker.can_delegate("execution.code"))
    check("S1.9 Alice has federation:delegate",
          orch.permission_checker.check_permission("delegation.federation", "federation:delegate"))
    check("S1.10 Bob has exec:code",
          orch.permission_checker.check_permission("execution.code", "exec:code"))

    # Phase 3-4: Delegate task
    ok, reason, task = orch.delegate_task(
        delegator_lct=alice_cert.lct_id,
        executor_lct=bob_cert.lct_id,
        task_type="execution.code",
        description="Run analysis script",
        atp_budget=200.0,
        quality_threshold=0.7,
    )
    check("S1.11 Delegation succeeds", ok, reason)
    check("S1.12 Task created", task is not None)
    check("S1.13 Task status = delegated",
          task.status == TaskStatus.DELEGATED if task else False)

    # Verify ATP locked
    alice_account = orch.ledger.get_account(alice_cert.lct_id)
    # 200 ATP + 5% fee = 210 locked
    check("S1.14 Alice ATP locked (210 = 200 + 5% fee)",
          alice_account.locked == 210.0,
          f"locked={alice_account.locked}")
    check("S1.15 Alice available reduced",
          alice_account.available == 790.0,
          f"available={alice_account.available}")

    # Phase 4: Task completion (good quality)
    ok, reason = orch.complete_task(task.task_id, quality_score=0.85, atp_consumed=150.0)
    check("S1.16 Task completion recorded", ok, reason)

    # Phase 5: Settlement
    ok, reason, settlement = orch.settle_task(task.task_id)
    check("S1.17 Settlement succeeds", ok, reason)
    check("S1.18 Settlement outcome = committed",
          settlement.get("outcome") == "committed")
    check("S1.19 Executor paid",
          settlement.get("executor_paid") == 200.0,
          f"paid={settlement.get('executor_paid')}")

    # Verify ATP final state
    alice_final = orch.ledger.get_account(alice_cert.lct_id)
    bob_final = orch.ledger.get_account(bob_cert.lct_id)
    check("S1.20 Alice total decreased by 210 (200 + fee)",
          alice_final.total == 790.0,
          f"total={alice_final.total}")
    check("S1.21 Bob total increased by 200",
          bob_final.total == 700.0,
          f"total={bob_final.total}")

    # Phase 6: Reputation updated
    bob_rep = orch.reputation.records.get(bob_cert.lct_id)
    check("S1.22 Bob reputation record exists", bob_rep is not None)
    check("S1.23 Bob has 1 task recorded",
          bob_rep.total_tasks == 1 if bob_rep else False)
    check("S1.24 Bob success rate = 100%",
          bob_rep.success_rate == 1.0 if bob_rep else False)
    check("S1.25 Bob T3 talent increased (quality 0.85 > 0.5)",
          bob_rep.t3.talent > 0.5 if bob_rep else False,
          f"talent={bob_rep.t3.talent}" if bob_rep else "no record")

    # Verify audit trail
    chain_valid, chain_msg = orch.audit.verify_chain()
    check("S1.26 Audit chain valid", chain_valid, chain_msg)
    check("S1.27 Audit has entries",
          len(orch.audit.entries) >= 4,
          f"entries={len(orch.audit.entries)}")

    identity_entries = orch.audit.query("identity_created")
    check("S1.28 2 identity creation audited",
          len(identity_entries) == 2)
    delegation_entries = orch.audit.query("task_delegated")
    check("S1.29 1 delegation audited",
          len(delegation_entries) == 1)
    settlement_entries = orch.audit.query("task_settled")
    check("S1.30 1 settlement audited",
          len(settlement_entries) == 1)

    # ====================================================================
    # SCENARIO 2: Failed delegation (quality below threshold)
    # ====================================================================
    print("S2: Failed delegation (quality below threshold)")
    orch2 = E2EOrchestrator()

    alice2 = orch2.create_identity("alice", "Thor", "delegation.federation",
                                    "ak2", "tk2", 500.0)
    charlie = orch2.create_identity("charlie", "Legion", "cognition.sage",
                                     "ck", "lk", 0.0)

    ok, reason, task2 = orch2.delegate_task(
        delegator_lct=alice2.lct_id,
        executor_lct=charlie.lct_id,
        task_type="cognition.sage",
        description="Complex analysis",
        atp_budget=100.0,
        quality_threshold=0.8,
    )
    check("S2.1 Delegation succeeds", ok, reason)

    # Execute with low quality
    ok, _ = orch2.complete_task(task2.task_id, quality_score=0.4, atp_consumed=80.0)
    check("S2.2 Completion recorded", ok)

    # Settle — should rollback
    ok, reason, settlement2 = orch2.settle_task(task2.task_id)
    check("S2.3 Settlement succeeds", ok)
    check("S2.4 Outcome = rolled_back",
          settlement2.get("outcome") == "rolled_back")
    check("S2.5 Delegator refunded",
          settlement2.get("delegator_refunded") is True)

    # Alice should get her ATP back
    alice2_final = orch2.ledger.get_account(alice2.lct_id)
    check("S2.6 Alice ATP restored after rollback",
          alice2_final.available == 500.0,
          f"available={alice2_final.available}")
    check("S2.7 Alice total unchanged",
          alice2_final.total == 500.0,
          f"total={alice2_final.total}")

    # Charlie reputation should reflect failure
    charlie_rep = orch2.reputation.records.get(charlie.lct_id)
    check("S2.8 Charlie T3 talent decreased (quality 0.4 < 0.5)",
          charlie_rep.t3.talent < 0.5 if charlie_rep else False,
          f"talent={charlie_rep.t3.talent}" if charlie_rep else "no record")
    check("S2.9 Charlie success rate = 0%",
          charlie_rep.success_rate == 0.0 if charlie_rep else False)

    chain_valid2, _ = orch2.audit.verify_chain()
    check("S2.10 Audit chain valid", chain_valid2)

    # ====================================================================
    # SCENARIO 3: Permission denied (wrong task type)
    # ====================================================================
    print("S3: Permission denied (wrong task type)")
    orch3 = E2EOrchestrator()

    # Bob has perception task — cannot delegate
    bob3 = orch3.create_identity("bob", "Sprout", "perception", "bk3", "sk3", 1000.0)
    eve = orch3.create_identity("eve", "Legion", "execution.code", "ek", "lk3", 0.0)

    ok, reason, task3 = orch3.delegate_task(
        delegator_lct=bob3.lct_id,
        executor_lct=eve.lct_id,
        task_type="execution.code",
        description="Run exploit",
        atp_budget=100.0,
    )
    check("S3.1 Delegation denied", not ok)
    check("S3.2 Reason mentions cannot delegate",
          "cannot delegate" in reason.lower(),
          f"reason={reason}")
    check("S3.3 No task created", task3 is None)
    check("S3.4 Bob ATP untouched",
          orch3.ledger.get_account(bob3.lct_id).available == 1000.0)

    # Verify denial audited
    failures = orch3.audit.query("delegation_failed")
    check("S3.5 Delegation failure audited", len(failures) == 1)

    # ====================================================================
    # SCENARIO 4: Insufficient ATP
    # ====================================================================
    print("S4: Insufficient ATP")
    orch4 = E2EOrchestrator()

    poor_alice = orch4.create_identity("alice", "Thor", "delegation.federation",
                                        "pak", "ptk", 50.0)
    worker = orch4.create_identity("worker", "Legion", "execution.code",
                                    "wk", "wlk", 0.0)

    ok, reason, _ = orch4.delegate_task(
        delegator_lct=poor_alice.lct_id,
        executor_lct=worker.lct_id,
        task_type="execution.code",
        description="Expensive task",
        atp_budget=100.0,  # Needs 105 with fee, only has 50
    )
    check("S4.1 Delegation denied (insufficient ATP)", not ok)
    check("S4.2 Reason mentions ATP",
          "atp" in reason.lower() or "insufficient" in reason.lower() or "balance" in reason.lower(),
          f"reason={reason}")

    # ====================================================================
    # SCENARIO 5: Identity verification failure
    # ====================================================================
    print("S5: Identity verification")

    cert_good = IdentityCertificate.create(
        Lineage("alice", "alice_pubkey"),
        Context("Thor", "thor_pubkey"),
        Task("perception"),
        "alice_key", "thor_key",
    )

    check("S5.1 Good cert verifies with correct keys",
          cert_good.verify("alice_key", "thor_key")[0])
    check("S5.2 Bad creator key fails",
          not cert_good.verify("wrong_key", "thor_key")[0])
    check("S5.3 Bad platform key fails",
          not cert_good.verify("alice_key", "wrong_key")[0])

    # ====================================================================
    # SCENARIO 6: Multi-task reputation evolution
    # ====================================================================
    print("S6: Reputation evolution over multiple tasks")
    orch6 = E2EOrchestrator()

    delegator = orch6.create_identity("alice", "Thor", "delegation.federation",
                                       "dk6", "dtk6", 5000.0)
    executor = orch6.create_identity("bob", "Sprout", "execution.code",
                                      "ek6", "etk6", 0.0)

    # Run 5 tasks with varying quality
    qualities = [0.9, 0.85, 0.6, 0.95, 0.3]
    expected_successes = sum(1 for q in qualities if q >= 0.7)

    for i, quality in enumerate(qualities):
        ok, _, task = orch6.delegate_task(
            delegator_lct=delegator.lct_id,
            executor_lct=executor.lct_id,
            task_type="execution.code",
            description=f"Task {i+1}",
            atp_budget=50.0,
        )
        if ok:
            orch6.complete_task(task.task_id, quality, atp_consumed=40.0)
            orch6.settle_task(task.task_id)

    exec_rep = orch6.reputation.records.get(executor.lct_id)
    check("S6.1 5 tasks recorded",
          exec_rep.total_tasks == 5 if exec_rep else False,
          f"total={exec_rep.total_tasks}" if exec_rep else "no record")
    check(f"S6.2 {expected_successes} successes",
          exec_rep.successful_tasks == expected_successes if exec_rep else False,
          f"successes={exec_rep.successful_tasks}" if exec_rep else "no record")

    # T3 should reflect mixed performance (3 good, 1 mediocre, 1 bad)
    # Net quality: avg(0.9, 0.85, 0.6, 0.95, 0.3) = 0.72 > 0.5 → net positive
    check("S6.3 T3 composite reflects net positive performance",
          exec_rep.t3.composite > 0.5 if exec_rep else False,
          f"composite={exec_rep.t3.composite:.4f}" if exec_rep else "no record")

    # Talent should increase more than temperament (execution.code tasks)
    talent_change = exec_rep.t3.talent - 0.5 if exec_rep else 0
    temperament_change = exec_rep.t3.temperament - 0.5 if exec_rep else 0
    check("S6.4 Talent changes more than temperament for code tasks",
          abs(talent_change) > abs(temperament_change) if exec_rep else False,
          f"talent_delta={talent_change:.4f}, temperament_delta={temperament_change:.4f}")

    # Task history tracked
    check("S6.5 Task history has 5 entries",
          len(exec_rep.task_history) == 5 if exec_rep else False)

    # Verify all deltas recorded
    all_have_deltas = all(
        "t3_delta" in entry for entry in (exec_rep.task_history if exec_rep else [])
    )
    check("S6.6 All history entries have T3 deltas", all_have_deltas)

    chain_valid6, _ = orch6.audit.verify_chain()
    check("S6.7 Audit chain valid after 5 tasks", chain_valid6)
    check("S6.8 Audit has correct entry count",
          len(orch6.audit.entries) >= 17,  # 2 identity + 5*(delegated+completed+settled)
          f"entries={len(orch6.audit.entries)}")

    # ====================================================================
    # SCENARIO 7: Permission matrix edge cases
    # ====================================================================
    print("S7: Permission matrix validation")

    checker = PermissionChecker()

    # admin.full should have all permissions (wildcard)
    check("S7.1 admin.full has atp:read (via atp:all)",
          checker.check_permission("admin.full", "atp:read"))
    check("S7.2 admin.full has federation:delegate (via federation:all)",
          checker.check_permission("admin.full", "federation:delegate"))
    check("S7.3 admin.full has exec:code (via exec:all)",
          checker.check_permission("admin.full", "exec:code"))
    check("S7.4 admin.full has admin:read (via admin:full)",
          checker.check_permission("admin.full", "admin:read"))
    check("S7.5 admin.full has admin:write (via admin:full)",
          checker.check_permission("admin.full", "admin:write"))

    # perception should have minimal permissions
    check("S7.6 perception has atp:read",
          checker.check_permission("perception", "atp:read"))
    check("S7.7 perception lacks atp:write",
          not checker.check_permission("perception", "atp:write"))
    check("S7.8 perception lacks exec:code",
          not checker.check_permission("perception", "exec:code"))
    check("S7.9 perception lacks federation:delegate",
          not checker.check_permission("perception", "federation:delegate"))

    # Delegation permission checks
    check("S7.10 delegation.federation can delegate",
          checker.can_delegate("delegation.federation"))
    check("S7.11 cognition.sage can delegate",
          checker.can_delegate("cognition.sage"))
    check("S7.12 execution.code cannot delegate",
          not checker.can_delegate("execution.code"))
    check("S7.13 admin.readonly cannot delegate",
          not checker.can_delegate("admin.readonly"))

    # Validate operation with ATP cost
    ok, _ = checker.validate_operation("perception", "atp:read", 50.0)
    check("S7.14 perception: atp:read within budget", ok)
    ok, _ = checker.validate_operation("perception", "atp:read", 500.0)
    check("S7.15 perception: atp:read exceeds budget (200)", not ok)

    # Unknown task type
    ok, _ = checker.validate_operation("nonexistent", "atp:read")
    check("S7.16 Unknown task type rejected", not ok)

    # ====================================================================
    # SCENARIO 8: ATP two-phase commit invariants
    # ====================================================================
    print("S8: ATP ledger invariants")
    ledger = ATPLedger()

    acct = ledger.create_account("test:alice", 1000.0)
    check("S8.1 Initial state: total=available=1000, locked=0",
          acct.total == 1000.0 and acct.available == 1000.0 and acct.locked == 0.0)

    # Lock
    ok, _ = ledger.lock_transfer("tx1", "test:alice", 100.0)  # 105 with fee
    check("S8.2 Lock succeeds", ok)
    check("S8.3 After lock: available=895, locked=105",
          acct.available == 895.0 and acct.locked == 105.0,
          f"available={acct.available}, locked={acct.locked}")
    check("S8.4 Total unchanged after lock",
          acct.total == 1000.0)

    # Conservation: total = available + locked (always)
    check("S8.5 Conservation: total = available + locked",
          abs(acct.total - (acct.available + acct.locked)) < 0.001,
          f"{acct.total} != {acct.available} + {acct.locked}")

    # Rollback
    ok, _ = ledger.rollback_transfer("tx1")
    check("S8.6 Rollback succeeds", ok)
    check("S8.7 After rollback: available=1000, locked=0",
          acct.available == 1000.0 and acct.locked == 0.0,
          f"available={acct.available}, locked={acct.locked}")

    # Lock + Commit
    ledger.create_account("test:bob", 0.0)
    ok, _ = ledger.lock_transfer("tx2", "test:alice", 200.0)  # 210 with fee
    check("S8.8 Second lock succeeds", ok)

    ok, _ = ledger.commit_transfer("tx2", "test:bob")
    check("S8.9 Commit succeeds", ok)

    alice_acct = ledger.get_account("test:alice")
    bob_acct = ledger.get_account("test:bob")
    check("S8.10 Alice total decreased by 210",
          alice_acct.total == 790.0,
          f"total={alice_acct.total}")
    check("S8.11 Bob received 200 (fee not passed through)",
          bob_acct.total == 200.0,
          f"total={bob_acct.total}")

    # Insufficient balance
    ok, reason = ledger.lock_transfer("tx3", "test:alice", 800.0)  # needs 840 with fee
    check("S8.12 Insufficient balance rejected", not ok)

    # History tracking
    check("S8.13 Alice has transfer history",
          len(alice_acct.history) >= 3)  # lock, rollback, lock, commit

    # ====================================================================
    # SCENARIO 9: Reputation T3 update mechanics
    # ====================================================================
    print("S9: T3 tensor update mechanics")

    t3 = T3Tensor(0.5, 0.5, 0.5)

    # High quality execution.code task → talent increases more
    t3_after = t3.update_from_task(0.9, "execution.code")
    check("S9.1 High quality increases all dims",
          t3_after.talent > 0.5 and t3_after.training > 0.5 and t3_after.temperament > 0.5)
    check("S9.2 Talent increases most for code tasks",
          (t3_after.talent - 0.5) > (t3_after.temperament - 0.5))

    # Low quality decreases
    t3_low = t3.update_from_task(0.1, "execution.code")
    check("S9.3 Low quality decreases all dims",
          t3_low.talent < 0.5 and t3_low.training < 0.5 and t3_low.temperament < 0.5)

    # Delegation task → temperament increases more
    t3_deleg = t3.update_from_task(0.9, "delegation.federation")
    check("S9.4 Temperament increases most for delegation",
          (t3_deleg.temperament - 0.5) > (t3_deleg.talent - 0.5))

    # Planning task → training increases more
    t3_plan = t3.update_from_task(0.9, "planning")
    check("S9.5 Training increases most for planning",
          (t3_plan.training - 0.5) > (t3_plan.talent - 0.5))

    # Neutral quality (0.5) → no change
    t3_neutral = t3.update_from_task(0.5, "perception")
    check("S9.6 Quality 0.5 causes no change",
          t3_neutral.talent == 0.5 and t3_neutral.training == 0.5 and t3_neutral.temperament == 0.5)

    # Clamping
    t3_high = T3Tensor(0.99, 0.99, 0.99)
    t3_clamped = t3_high.update_from_task(1.0, "execution.code")
    check("S9.7 Clamped to 1.0 max",
          t3_clamped.talent <= 1.0 and t3_clamped.training <= 1.0 and t3_clamped.temperament <= 1.0)

    t3_low_base = T3Tensor(0.01, 0.01, 0.01)
    t3_clamped_low = t3_low_base.update_from_task(0.0, "execution.code")
    check("S9.8 Clamped to 0.0 min",
          t3_clamped_low.talent >= 0.0 and t3_clamped_low.training >= 0.0 and t3_clamped_low.temperament >= 0.0)

    # ====================================================================
    # SCENARIO 10: Audit trail integrity
    # ====================================================================
    print("S10: Audit trail integrity")
    audit = AuditTrail()

    entries = []
    for i in range(10):
        entry = audit.append(f"event_{i}", {"seq": i, "data": f"payload_{i}"})
        entries.append(entry)

    check("S10.1 10 entries created", len(audit.entries) == 10)

    valid, msg = audit.verify_chain()
    check("S10.2 Chain valid", valid, msg)

    # First entry links to genesis
    check("S10.3 First entry prev_hash = genesis",
          audit.entries[0].prev_hash == "genesis")

    # All subsequent entries link to previous
    check("S10.4 Chain continuity",
          all(
              audit.entries[i].prev_hash == audit.entries[i-1].entry_hash
              for i in range(1, len(audit.entries))
          ))

    # Tamper detection
    original_hash = audit.entries[5].entry_hash
    audit.entries[5].data = {"seq": 5, "data": "TAMPERED"}
    valid_after_tamper, _ = audit.verify_chain()
    check("S10.5 Tamper detected", not valid_after_tamper)

    # Restore
    audit.entries[5].data = {"seq": 5, "data": "payload_5"}
    audit.entries[5].entry_hash = original_hash
    valid_restored, _ = audit.verify_chain()
    check("S10.6 Chain restored after fix", valid_restored)

    # Query by type
    event_3 = audit.query("event_3")
    check("S10.7 Query by type works", len(event_3) == 1)

    # ====================================================================
    # SCENARIO 11: Full state verification
    # ====================================================================
    print("S11: Full state dump")
    state = orch.get_full_state()
    check("S11.1 State has identities", state["identities"] == 2)
    check("S11.2 State has accounts", len(state["atp_accounts"]) == 2)
    check("S11.3 State has reputation", len(state["reputation"]) == 2)
    check("S11.4 Audit chain valid in state",
          state["audit"]["chain_valid"] is True)

    # ====================================================================
    # SCENARIO 12: Cross-format LCT ID handling
    # ====================================================================
    print("S12: LCT ID format handling")

    # Format A (identity system)
    format_a = "lct:web4:agent:alice@Thor#perception"
    check("S12.1 Format A has @ and #",
          "@" in format_a and "#" in format_a)

    # Extract task type from Format A
    task_from_a = format_a.split("#")[-1]
    check("S12.2 Task extraction from Format A",
          task_from_a == "perception")

    # Format C (ad-hoc)
    format_c = "lct:web4:ai:claude"
    parts = format_c.split(":")
    check("S12.3 Format C parts: 4 colon-separated",
          len(parts) == 4)

    # Both formats should be usable as ATP account keys
    ledger = ATPLedger()
    ledger.create_account(format_a, 100.0)
    ledger.create_account(format_c, 200.0)
    check("S12.4 Format A as account key",
          ledger.get_account(format_a).available == 100.0)
    check("S12.5 Format C as account key",
          ledger.get_account(format_c).available == 200.0)

    # ====================================================================
    # Print Summary
    # ====================================================================
    print(f"\n{'='*60}")
    print(f"E2E Integration Prototype: {checks_passed}/{total_checks} checks passed")
    print(f"{'='*60}")

    if checks_failed == 0:
        print("\nAll scenarios validated successfully!")
        print("\nIntegration chain proven:")
        print("  Identity (LCT) → Permissions (LUPS) → ATP (2-phase)")
        print("  → Federation (quality-gated) → Reputation (T3)")
        print("  → Audit (hash-chain)")
        print("\nKey integration mechanics:")
        print("  - LCT ID format carries task type for permission lookup")
        print("  - Permission check gates delegation before ATP lock")
        print("  - ATP 2-phase commit ensures atomic settlement")
        print("  - Quality threshold determines commit vs rollback")
        print("  - T3 tensor update reflects task-specific performance")
        print("  - Audit trail captures every state transition")
    else:
        print(f"\n{checks_failed} checks failed — see details above")

    return checks_passed, total_checks


if __name__ == "__main__":
    passed, total = run_tests()
    exit(0 if passed == total else 1)
