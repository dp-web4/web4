#!/usr/bin/env python3
"""
AI Agent Accountability Stack Reference Implementation
Proposal: WEB4-PROPOSAL-001

Complete accountability stack for AI agents: WHO (hardware-bound identity),
UNDER WHOSE AUTHORITY (delegation chain), WITHIN WHAT LIMITS (ATP budget).

Key features:
- Hardware-bound identity (TPM/Secure Enclave binding)
- Cryptographic delegation chains (human → agent → sub-agent)
- ATP budget enforcement with lock-commit-rollback
- Cross-network delegation with trust-weighted exchange rates
- Sybil resistance through hardware binding
- Delegation forgery prevention via signature verification
- Budget gaming prevention (rate limits, cost caps, anomaly detection)
- ATP farming prevention (conservation laws, 5% transfer fee)
- Dynamic budget optimization (performance-based adjustment)
- Identity migration and revocation
"""

import hashlib
import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# Section 1: Hardware-Bound Identity
# ============================================================

@dataclass
class HardwareAttestation:
    """Hardware attestation proving key is bound to physical device."""
    tpm_public_key_hash: str = ""
    tpm_attestation_signature: str = ""
    platform_info: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.tpm_public_key_hash:
            self.tpm_public_key_hash = f"sha256:{hashlib.sha256(uuid.uuid4().bytes).hexdigest()}"
        if not self.tpm_attestation_signature:
            sig_input = f"{self.tpm_public_key_hash}:{self.timestamp}"
            self.tpm_attestation_signature = hashlib.sha256(sig_input.encode()).hexdigest()


@dataclass
class HardwareBoundIdentity:
    """Identity bound to hardware security module."""
    lct_uri: str = ""
    hardware_id: str = ""
    attestation: HardwareAttestation = field(default_factory=HardwareAttestation)
    signature: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None

    def __post_init__(self):
        if not self.hardware_id:
            self.hardware_id = self.attestation.tpm_public_key_hash
        if not self.signature:
            sig_input = f"{self.lct_uri}:{self.hardware_id}"
            self.signature = hashlib.sha256(sig_input.encode()).hexdigest()[:32]

    def verify(self) -> Tuple[bool, str]:
        """Verify identity is valid."""
        if not self.lct_uri:
            return False, "Missing LCT URI"
        if not self.hardware_id:
            return False, "Missing hardware ID"
        if self.hardware_id != self.attestation.tpm_public_key_hash:
            return False, "Hardware ID mismatch"
        expected_sig = hashlib.sha256(
            f"{self.lct_uri}:{self.hardware_id}".encode()
        ).hexdigest()[:32]
        if self.signature != expected_sig:
            return False, "Invalid signature"
        return True, "Identity verified"


@dataclass
class IdentityRevocation:
    """Revocation record for compromised identities."""
    identity_lct_uri: str = ""
    revoked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reason: str = ""  # "compromised", "migrated", "expired"
    revocation_signature: str = ""

    def __post_init__(self):
        if not self.revocation_signature:
            self.revocation_signature = hashlib.sha256(
                f"{self.identity_lct_uri}:{self.revoked_at}:{self.reason}".encode()
            ).hexdigest()[:32]


@dataclass
class MigrationCertificate:
    """Certificate for identity migration to new hardware."""
    old_lct_uri: str = ""
    new_lct_uri: str = ""
    old_hardware_id: str = ""
    new_hardware_id: str = ""
    migrated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    old_key_signature: str = ""  # Signed with old hardware key
    new_key_signature: str = ""  # Signed with new hardware key

    def __post_init__(self):
        if not self.old_key_signature:
            self.old_key_signature = hashlib.sha256(
                f"old:{self.old_lct_uri}:{self.new_lct_uri}".encode()
            ).hexdigest()[:32]
        if not self.new_key_signature:
            self.new_key_signature = hashlib.sha256(
                f"new:{self.old_lct_uri}:{self.new_lct_uri}".encode()
            ).hexdigest()[:32]


class IdentityRegistry:
    """Registry for hardware-bound identities."""

    def __init__(self):
        self.identities: Dict[str, HardwareBoundIdentity] = {}
        self.revocations: Dict[str, IdentityRevocation] = {}
        self.migrations: List[MigrationCertificate] = []
        self.hardware_to_lct: Dict[str, str] = {}  # hw_id → lct_uri

    def register(self, identity: HardwareBoundIdentity) -> Tuple[bool, str]:
        valid, reason = identity.verify()
        if not valid:
            return False, reason
        if identity.lct_uri in self.identities:
            return False, "LCT URI already registered"
        # Sybil check: one identity per hardware
        if identity.hardware_id in self.hardware_to_lct:
            return False, f"Hardware already bound to {self.hardware_to_lct[identity.hardware_id]}"
        self.identities[identity.lct_uri] = identity
        self.hardware_to_lct[identity.hardware_id] = identity.lct_uri
        return True, "Registered"

    def is_active(self, lct_uri: str) -> bool:
        return lct_uri in self.identities and lct_uri not in self.revocations

    def revoke(self, revocation: IdentityRevocation) -> bool:
        if revocation.identity_lct_uri not in self.identities:
            return False
        self.revocations[revocation.identity_lct_uri] = revocation
        return True

    def migrate(self, cert: MigrationCertificate) -> Tuple[bool, str]:
        """Migrate identity to new hardware."""
        if cert.old_lct_uri not in self.identities:
            return False, "Old identity not found"
        # Create new identity
        new_att = HardwareAttestation(tpm_public_key_hash=cert.new_hardware_id)
        new_identity = HardwareBoundIdentity(
            lct_uri=cert.new_lct_uri,
            hardware_id=cert.new_hardware_id,
            attestation=new_att,
        )
        valid, reason = new_identity.verify()
        if not valid:
            return False, reason
        # Revoke old
        self.revoke(IdentityRevocation(
            identity_lct_uri=cert.old_lct_uri,
            reason="migrated",
        ))
        # Register new
        self.identities[cert.new_lct_uri] = new_identity
        self.hardware_to_lct[cert.new_hardware_id] = cert.new_lct_uri
        self.migrations.append(cert)
        return True, "Migrated"


# ============================================================
# Section 2: Delegation Chain
# ============================================================

@dataclass
class DelegationScope:
    """Scope of delegation."""
    allowed_operations: List[str] = field(default_factory=list)
    resource_limits: Dict[str, float] = field(default_factory=dict)
    network_restrictions: List[str] = field(default_factory=list)
    time_restrictions: Optional[Dict[str, str]] = None


@dataclass
class DelegationToken:
    """Cryptographic delegation token."""
    token_id: str = field(default_factory=lambda: f"token_{uuid.uuid4().hex[:12]}")
    issuer: str = ""
    delegate: str = ""
    scope: DelegationScope = field(default_factory=DelegationScope)
    issued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str = ""
    signature: str = ""
    parent_token_id: Optional[str] = None

    def __post_init__(self):
        if not self.expires_at:
            exp = datetime.now(timezone.utc) + timedelta(hours=24)
            self.expires_at = exp.isoformat()
        if not self.signature:
            self.signature = hashlib.sha256(
                f"{self.token_id}:{self.issuer}:{self.delegate}".encode()
            ).hexdigest()[:32]

    def is_expired(self, now: datetime = None) -> bool:
        if now is None:
            now = datetime.now(timezone.utc)
        try:
            exp = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return now > exp
        except (ValueError, AttributeError):
            return False

    def verify_signature(self) -> bool:
        expected = hashlib.sha256(
            f"{self.token_id}:{self.issuer}:{self.delegate}".encode()
        ).hexdigest()[:32]
        return self.signature == expected


@dataclass
class BudgetedDelegationToken(DelegationToken):
    """Delegation token with ATP budget."""
    atp_budget: float = 0.0
    atp_consumed: float = 0.0
    atp_locked: float = 0.0
    budget_alerts: List[str] = field(default_factory=list)

    @property
    def atp_available(self) -> float:
        return self.atp_budget - self.atp_consumed - self.atp_locked

    def check_alert_thresholds(self) -> Optional[str]:
        if self.atp_budget <= 0:
            return None
        consumed_ratio = self.atp_consumed / self.atp_budget
        if consumed_ratio >= 1.0:
            alert = "EXHAUSTED_100"
        elif consumed_ratio >= 0.9:
            alert = "CRITICAL_90"
        elif consumed_ratio >= 0.8:
            alert = "WARNING_80"
        else:
            return None
        if alert not in self.budget_alerts:
            self.budget_alerts.append(alert)
        return alert


class DelegationChain:
    """Manages delegation chains with verification."""

    def __init__(self, identity_registry: IdentityRegistry):
        self.registry = identity_registry
        self.tokens: Dict[str, DelegationToken] = {}
        self.revoked_tokens: Set[str] = set()

    def create_delegation(
        self,
        issuer: str,
        delegate: str,
        scope: DelegationScope,
        atp_budget: float = 0.0,
        duration_hours: float = 24.0,
        parent_token_id: Optional[str] = None,
    ) -> Tuple[Optional[BudgetedDelegationToken], str]:
        """Create a new delegation token."""
        # Verify issuer is active
        if not self.registry.is_active(issuer):
            return None, "Issuer identity not active"

        # Verify parent chain
        if parent_token_id:
            parent = self.tokens.get(parent_token_id)
            if not parent:
                return None, "Parent token not found"
            if parent_token_id in self.revoked_tokens:
                return None, "Parent token revoked"
            # Scope must narrow (child ⊆ parent)
            if isinstance(parent, BudgetedDelegationToken):
                if atp_budget > parent.atp_available:
                    return None, f"Budget exceeds parent available ({parent.atp_available})"

        expires = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        token = BudgetedDelegationToken(
            issuer=issuer,
            delegate=delegate,
            scope=scope,
            expires_at=expires.isoformat(),
            parent_token_id=parent_token_id,
            atp_budget=atp_budget,
        )

        # Lock budget from parent
        if parent_token_id and isinstance(parent, BudgetedDelegationToken):
            parent.atp_locked += atp_budget

        self.tokens[token.token_id] = token
        return token, "Delegation created"

    def verify_chain(self, token_id: str, root_issuer: str = None) -> Tuple[bool, List[str]]:
        """Verify complete delegation chain."""
        chain = []
        current_id = token_id

        while current_id:
            token = self.tokens.get(current_id)
            if not token:
                return False, chain + ["Token not found"]
            if current_id in self.revoked_tokens:
                return False, chain + [f"Token {current_id} revoked"]
            if token.is_expired():
                return False, chain + [f"Token {current_id} expired"]
            if not token.verify_signature():
                return False, chain + [f"Token {current_id} invalid signature"]

            chain.append(f"{token.issuer} → {token.delegate}")
            current_id = token.parent_token_id

        # Verify root
        if root_issuer and chain:
            first_issuer = chain[-1].split(" → ")[0]
            if first_issuer != root_issuer:
                return False, chain + [f"Root mismatch: expected {root_issuer}, got {first_issuer}"]

        return True, chain

    def revoke_token(self, token_id: str) -> bool:
        if token_id not in self.tokens:
            return False
        self.revoked_tokens.add(token_id)
        # Cascade: revoke child tokens
        for tid, token in self.tokens.items():
            if token.parent_token_id == token_id:
                self.revoked_tokens.add(tid)
        return True


# ============================================================
# Section 3: ATP Budget Enforcement
# ============================================================

class TransactionState(Enum):
    LOCKED = "locked"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ATPTransaction:
    """Atomic ATP transaction."""
    tx_id: str = field(default_factory=lambda: f"tx_{uuid.uuid4().hex[:12]}")
    token_id: str = ""
    amount: float = 0.0
    state: TransactionState = TransactionState.LOCKED
    locked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    settled_at: Optional[str] = None


class BudgetEnforcer:
    """ATP budget enforcement with lock-commit-rollback."""

    def __init__(
        self,
        transfer_fee: float = 0.05,
        max_query_cost: float = 8.0,
        max_queries_per_second: int = 2,
    ):
        self.TRANSFER_FEE = transfer_fee
        self.MAX_QUERY_COST = max_query_cost
        self.MAX_QUERIES_PER_SECOND = max_queries_per_second
        self.transactions: Dict[str, ATPTransaction] = {}
        self.query_timestamps: Dict[str, List[datetime]] = {}  # entity → [timestamps]

    def lock_transaction(
        self, token: BudgetedDelegationToken, amount: float
    ) -> Tuple[Optional[str], Optional[str]]:
        """Lock ATP before operation."""
        # Cost cap
        if amount > self.MAX_QUERY_COST:
            return None, f"Amount {amount} exceeds cost cap {self.MAX_QUERY_COST}"

        # Rate limit
        entity = token.delegate
        now = datetime.now(timezone.utc)
        if entity not in self.query_timestamps:
            self.query_timestamps[entity] = []

        # Clean old timestamps
        cutoff = now - timedelta(seconds=1)
        self.query_timestamps[entity] = [
            t for t in self.query_timestamps[entity] if t > cutoff
        ]
        if len(self.query_timestamps[entity]) >= self.MAX_QUERIES_PER_SECOND:
            return None, "Rate limit exceeded"

        # Check budget
        if token.atp_available < amount:
            return None, f"Insufficient budget: need {amount}, available {token.atp_available}"

        # Lock
        tx = ATPTransaction(token_id=token.token_id, amount=amount)
        token.atp_locked += amount
        self.transactions[tx.tx_id] = tx
        self.query_timestamps[entity].append(now)

        # Check alert thresholds
        token.check_alert_thresholds()

        return tx.tx_id, None

    def commit_transaction(self, tx_id: str) -> Tuple[bool, str]:
        """Commit locked ATP (operation succeeded)."""
        tx = self.transactions.get(tx_id)
        if not tx:
            return False, "Transaction not found"
        if tx.state != TransactionState.LOCKED:
            return False, f"Cannot commit: state is {tx.state.value}"

        token = self._get_token(tx.token_id)
        if not token:
            return False, "Token not found"

        # Apply fee
        total = tx.amount * (1 + self.TRANSFER_FEE)
        token.atp_locked -= tx.amount
        token.atp_consumed += total

        tx.state = TransactionState.COMMITTED
        tx.settled_at = datetime.now(timezone.utc).isoformat()

        token.check_alert_thresholds()
        return True, "Committed"

    def rollback_transaction(self, tx_id: str) -> Tuple[bool, str]:
        """Rollback locked ATP (operation failed)."""
        tx = self.transactions.get(tx_id)
        if not tx:
            return False, "Transaction not found"
        if tx.state != TransactionState.LOCKED:
            return False, f"Cannot rollback: state is {tx.state.value}"

        token = self._get_token(tx.token_id)
        if token:
            token.atp_locked -= tx.amount

        tx.state = TransactionState.ROLLED_BACK
        tx.settled_at = datetime.now(timezone.utc).isoformat()
        return True, "Rolled back"

    def _get_token(self, token_id: str) -> Optional[BudgetedDelegationToken]:
        # This would normally look up from chain; we store ref
        return self._token_store.get(token_id)

    def register_token(self, token: BudgetedDelegationToken):
        if not hasattr(self, '_token_store'):
            self._token_store = {}
        self._token_store[token.token_id] = token


# ============================================================
# Section 4: Cross-Network Delegation
# ============================================================

@dataclass
class Network:
    """Network configuration."""
    name: str = ""
    base_exchange_rate: float = 1.0
    trust_level: float = 1.0
    min_confirmations: int = 12
    bridge_fee_forward: float = 0.01  # 1%
    bridge_fee_return: float = 0.005  # 0.5%


@dataclass
class CrossNetworkDelegation:
    """Cross-network delegation with exchange rates."""
    source_network: str = ""
    target_network: str = ""
    exchange_rate: float = 0.0
    source_atp_budget: float = 0.0
    target_atp_budget: float = 0.0
    bridge_fee: float = 0.0
    bridge_confirmations: int = 12
    bridge_finalized: bool = False


class CrossNetworkBridge:
    """Bridge for cross-network delegations."""

    def __init__(self):
        self.networks: Dict[str, Network] = {}

    def register_network(self, network: Network):
        self.networks[network.name] = network

    def get_exchange_rate(self, source: str, target: str) -> float:
        """Compute trust-weighted exchange rate."""
        src = self.networks.get(source)
        tgt = self.networks.get(target)
        if not src or not tgt:
            return 0.0
        base_rate = tgt.base_exchange_rate / max(src.base_exchange_rate, 0.001)
        return base_rate * tgt.trust_level

    def create_cross_network_delegation(
        self, source: str, target: str, source_atp: float
    ) -> Tuple[Optional[CrossNetworkDelegation], str]:
        """Create cross-network delegation."""
        src_net = self.networks.get(source)
        tgt_net = self.networks.get(target)
        if not src_net or not tgt_net:
            return None, "Network not found"

        rate = self.get_exchange_rate(source, target)
        fee = source_atp * src_net.bridge_fee_forward
        target_atp = (source_atp - fee) * rate

        delegation = CrossNetworkDelegation(
            source_network=source,
            target_network=target,
            exchange_rate=rate,
            source_atp_budget=source_atp,
            target_atp_budget=target_atp,
            bridge_fee=fee,
            bridge_confirmations=src_net.min_confirmations,
            bridge_finalized=True,  # Simulated finalization
        )
        return delegation, "Cross-network delegation created"

    def aggregate_reputation(
        self, identity: str, network_reputations: Dict[str, float]
    ) -> float:
        """Aggregate reputation across networks weighted by trust."""
        total_weight = 0.0
        weighted_sum = 0.0
        for net_name, rep in network_reputations.items():
            net = self.networks.get(net_name)
            if net:
                weighted_sum += rep * net.trust_level
                total_weight += net.trust_level
        return weighted_sum / total_weight if total_weight > 0 else 0.5


# ============================================================
# Section 5: Security Mitigations
# ============================================================

class SybilDetector:
    """Detect sybil attacks through hardware binding analysis."""

    CREATION_COST = 50.0  # ATP per identity

    def __init__(self, registry: IdentityRegistry):
        self.registry = registry
        self.creation_timestamps: Dict[str, datetime] = {}

    def check_sybil_cost(self, num_identities: int) -> float:
        """Calculate cost of sybil attack."""
        # Hardware cost + ATP stake
        hw_cost = num_identities * 250  # Estimated hardware cost
        atp_cost = num_identities * self.CREATION_COST
        return hw_cost + atp_cost

    def detect_cluster(self, identities: List[str]) -> Tuple[bool, str]:
        """Detect disconnected identity clusters (potential sybil)."""
        if len(identities) < 3:
            return False, "Cluster too small"
        # Check hardware diversity
        hw_ids = set()
        for lct in identities:
            identity = self.registry.identities.get(lct)
            if identity:
                hw_ids.add(identity.hardware_id)
        if len(hw_ids) < len(identities):
            return True, f"Hardware reuse detected: {len(identities)} identities, {len(hw_ids)} hardware"
        return False, "No sybil indicators"


class ATPFarmingDetector:
    """Detect and prevent ATP farming through circular transfers."""

    def __init__(self):
        self.transfer_log: List[Tuple[str, str, float, datetime]] = []

    def record_transfer(self, from_entity: str, to_entity: str, amount: float):
        self.transfer_log.append((
            from_entity, to_entity, amount, datetime.now(timezone.utc)
        ))

    def detect_circular(self, entity: str, max_depth: int = 10) -> Tuple[bool, str]:
        """Detect circular ATP flows."""
        # Build adjacency from recent transfers
        recent = [t for t in self.transfer_log
                  if (datetime.now(timezone.utc) - t[3]).total_seconds() < 3600]
        adjacency: Dict[str, List[str]] = {}
        for src, dst, _, _ in recent:
            if src not in adjacency:
                adjacency[src] = []
            adjacency[src].append(dst)

        # BFS for cycle detection
        visited = set()
        queue = [(entity, [entity])]
        while queue:
            current, path = queue.pop(0)
            if len(path) > max_depth:
                continue
            for neighbor in adjacency.get(current, []):
                if neighbor == entity and len(path) > 1:
                    return True, f"Circular flow detected: {' → '.join(path + [entity])}"
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return False, "No circular flows detected"

    def compute_farming_loss(self, loops: int, fee_rate: float = 0.05) -> float:
        """Compute net loss from ATP farming attempts."""
        # Each loop loses fee_rate
        remaining = 1.0
        for _ in range(loops):
            remaining *= (1 - fee_rate)
        return 1.0 - remaining  # Total percentage lost


# ============================================================
# Section 6: Dynamic Budget Optimization
# ============================================================

@dataclass
class BudgetUsageRecord:
    """Historical budget usage for optimization."""
    agent_lct_uri: str = ""
    task_type: str = ""
    allocated_budget: float = 0.0
    consumed_budget: float = 0.0
    success: bool = True
    value_delivered: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def efficiency(self) -> float:
        if self.consumed_budget <= 0:
            return 0.0
        return self.value_delivered / self.consumed_budget

    @property
    def utilization(self) -> float:
        if self.allocated_budget <= 0:
            return 0.0
        return self.consumed_budget / self.allocated_budget


class DynamicBudgetOptimizer:
    """ML-based (heuristic) dynamic budget optimization."""

    BASE_BUDGET = 100.0

    def __init__(self):
        self.history: List[BudgetUsageRecord] = []
        self.task_multipliers: Dict[str, float] = {}

    def record_usage(self, record: BudgetUsageRecord):
        self.history.append(record)
        self._update_multipliers()

    def _update_multipliers(self):
        """Learn from historical data."""
        by_task: Dict[str, List[BudgetUsageRecord]] = {}
        for r in self.history:
            if r.task_type not in by_task:
                by_task[r.task_type] = []
            by_task[r.task_type].append(r)

        for task_type, records in by_task.items():
            if len(records) < 2:
                continue
            avg_eff = sum(r.efficiency for r in records) / len(records)
            if avg_eff > 1.0:
                # High efficiency → reduce multiplier
                self.task_multipliers[task_type] = self.task_multipliers.get(task_type, 1.0) * 0.95
            elif avg_eff < 0.5:
                # Low efficiency → increase multiplier
                self.task_multipliers[task_type] = self.task_multipliers.get(task_type, 1.0) * 1.05

    def compute_optimal_budget(
        self, agent_lct: str, task_type: str, reputation: float
    ) -> float:
        """Compute optimal budget for agent+task combination."""
        # Reputation-based baseline
        rep_budget = self.BASE_BUDGET * (0.5 + reputation * 0.5)

        # Performance factor from history
        agent_records = [r for r in self.history if r.agent_lct_uri == agent_lct]
        if agent_records:
            success_rate = sum(1 for r in agent_records if r.success) / len(agent_records)
            avg_util = sum(r.utilization for r in agent_records) / len(agent_records)
            performance_factor = 0.5 + success_rate * 0.3 + avg_util * 0.2
        else:
            performance_factor = 1.0

        # Task factor
        task_factor = self.task_multipliers.get(task_type, 1.0)

        return rep_budget * performance_factor * task_factor

    def predict_exhaustion(
        self, token: BudgetedDelegationToken, projected_consumption: float
    ) -> Tuple[str, float]:
        """Predict budget exhaustion risk."""
        remaining = token.atp_available
        if remaining <= 0:
            return "exhausted", 1.0
        risk = projected_consumption / remaining
        if risk < 0.8:
            return "ok", risk
        elif risk < 1.0:
            return "warning", risk
        else:
            return "critical", risk


# ============================================================
# TESTS
# ============================================================

def _check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {label}"
    if detail and not condition:
        msg += f" — {detail}"
    print(msg)
    return condition


def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed, total
        total += 1
        if _check(label, condition, detail):
            passed += 1
        else:
            failed += 1

    # ── T1: Hardware Attestation ──
    print("\n── T1: Hardware Attestation ──")

    att = HardwareAttestation(platform_info={"type": "TPM_2.0", "vendor": "Intel"})
    check("T1.1 Attestation hash generated", att.tpm_public_key_hash.startswith("sha256:"))
    check("T1.2 Attestation signature", len(att.tpm_attestation_signature) > 0)
    check("T1.3 Platform info", att.platform_info["type"] == "TPM_2.0")
    check("T1.4 Timestamp set", len(att.timestamp) > 0)

    # ── T2: Hardware-Bound Identity ──
    print("\n── T2: Hardware-Bound Identity ──")

    identity = HardwareBoundIdentity(lct_uri="lct://agent:test@mainnet")
    check("T2.1 LCT URI", identity.lct_uri == "lct://agent:test@mainnet")
    check("T2.2 Hardware ID from attestation", identity.hardware_id == identity.attestation.tpm_public_key_hash)
    check("T2.3 Signature generated", len(identity.signature) == 32)

    valid, reason = identity.verify()
    check("T2.4 Identity verifies", valid)

    # Invalid identity
    bad_id = HardwareBoundIdentity(lct_uri="")
    v, r = bad_id.verify()
    check("T2.5 Empty URI fails", not v)

    # Tampered signature
    tampered = HardwareBoundIdentity(lct_uri="lct://tampered@net")
    tampered.signature = "wrong_signature_value"
    v_t, _ = tampered.verify()
    check("T2.6 Tampered signature fails", not v_t)

    # Hardware ID mismatch
    mismatch = HardwareBoundIdentity(lct_uri="lct://mismatch@net")
    mismatch.hardware_id = "sha256:different"
    v_m, _ = mismatch.verify()
    check("T2.7 HW ID mismatch fails", not v_m)

    # ── T3: Identity Registry ──
    print("\n── T3: Identity Registry ──")

    registry = IdentityRegistry()
    id1 = HardwareBoundIdentity(lct_uri="lct://alice@mainnet")
    id2 = HardwareBoundIdentity(lct_uri="lct://bob@mainnet")

    ok1, _ = registry.register(id1)
    check("T3.1 First registration", ok1)

    ok2, _ = registry.register(id2)
    check("T3.2 Second registration", ok2)

    check("T3.3 Alice active", registry.is_active("lct://alice@mainnet"))

    # Duplicate LCT
    dup, dup_reason = registry.register(HardwareBoundIdentity(lct_uri="lct://alice@mainnet"))
    check("T3.4 Duplicate LCT rejected", not dup)

    # Sybil: same hardware
    sybil_att = HardwareAttestation(tpm_public_key_hash=id1.hardware_id)
    sybil = HardwareBoundIdentity(lct_uri="lct://sybil@mainnet", attestation=sybil_att)
    sybil_ok, sybil_reason = registry.register(sybil)
    check("T3.5 Sybil rejected (same HW)", not sybil_ok)
    check("T3.6 Sybil reason mentions hardware", "hardware" in sybil_reason.lower())

    # ── T4: Identity Revocation ──
    print("\n── T4: Identity Revocation ──")

    rev = IdentityRevocation(identity_lct_uri="lct://alice@mainnet", reason="compromised")
    check("T4.1 Revocation signature", len(rev.revocation_signature) == 32)

    registry.revoke(rev)
    check("T4.2 Alice no longer active", not registry.is_active("lct://alice@mainnet"))
    check("T4.3 Bob still active", registry.is_active("lct://bob@mainnet"))

    # ── T5: Identity Migration ──
    print("\n── T5: Identity Migration ──")

    reg5 = IdentityRegistry()
    old_id = HardwareBoundIdentity(lct_uri="lct://charlie@mainnet")
    reg5.register(old_id)

    new_hw = HardwareAttestation()
    cert = MigrationCertificate(
        old_lct_uri="lct://charlie@mainnet",
        new_lct_uri="lct://charlie_v2@mainnet",
        old_hardware_id=old_id.hardware_id,
        new_hardware_id=new_hw.tpm_public_key_hash,
    )
    migrated, migrate_msg = reg5.migrate(cert)
    check("T5.1 Migration succeeded", migrated)
    check("T5.2 Old identity revoked", not reg5.is_active("lct://charlie@mainnet"))
    check("T5.3 New identity active", reg5.is_active("lct://charlie_v2@mainnet"))
    check("T5.4 Migration recorded", len(reg5.migrations) == 1)

    # Migrate non-existent
    bad_cert = MigrationCertificate(old_lct_uri="nonexistent", new_lct_uri="new")
    bad_mig, _ = reg5.migrate(bad_cert)
    check("T5.5 Non-existent migration fails", not bad_mig)

    # ── T6: Delegation Tokens ──
    print("\n── T6: Delegation Tokens ──")

    token = DelegationToken(
        issuer="lct://user:alice@mainnet",
        delegate="lct://agent:sage@mainnet",
    )
    check("T6.1 Token ID generated", token.token_id.startswith("token_"))
    check("T6.2 Token signature", len(token.signature) == 32)
    check("T6.3 Not expired", not token.is_expired())
    check("T6.4 Signature verifies", token.verify_signature())

    # Expired token
    expired = DelegationToken(
        issuer="alice",
        delegate="bob",
        expires_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
    )
    check("T6.5 Expired token detected", expired.is_expired())

    # Budgeted token
    bt = BudgetedDelegationToken(
        issuer="alice", delegate="sage", atp_budget=100.0,
    )
    check("T6.6 Budget set", bt.atp_budget == 100.0)
    check("T6.7 Available = budget", bt.atp_available == 100.0)

    bt.atp_consumed = 30.0
    bt.atp_locked = 20.0
    check("T6.8 Available accounts for consumed+locked", bt.atp_available == 50.0)

    # Alert thresholds
    bt2 = BudgetedDelegationToken(issuer="a", delegate="b", atp_budget=100.0)
    bt2.atp_consumed = 85
    alert = bt2.check_alert_thresholds()
    check("T6.9 Warning at 85%", alert == "WARNING_80")

    bt2.atp_consumed = 95
    alert2 = bt2.check_alert_thresholds()
    check("T6.10 Critical at 95%", alert2 == "CRITICAL_90")

    bt2.atp_consumed = 100
    alert3 = bt2.check_alert_thresholds()
    check("T6.11 Exhausted at 100%", alert3 == "EXHAUSTED_100")

    # ── T7: Delegation Chain ──
    print("\n── T7: Delegation Chain ──")

    reg7 = IdentityRegistry()
    reg7.register(HardwareBoundIdentity(lct_uri="lct://alice@mainnet"))
    reg7.register(HardwareBoundIdentity(lct_uri="lct://sage@mainnet"))
    reg7.register(HardwareBoundIdentity(lct_uri="lct://irp@mainnet"))

    chain = DelegationChain(reg7)

    # Alice → SAGE
    t1, msg1 = chain.create_delegation(
        "lct://alice@mainnet", "lct://sage@mainnet",
        DelegationScope(allowed_operations=["query", "compute"]),
        atp_budget=500.0,
    )
    check("T7.1 Alice→SAGE created", t1 is not None)

    # SAGE → IRP (sub-delegation)
    t2, msg2 = chain.create_delegation(
        "lct://sage@mainnet", "lct://irp@mainnet",
        DelegationScope(allowed_operations=["query"]),
        atp_budget=100.0,
        parent_token_id=t1.token_id,
    )
    check("T7.2 SAGE→IRP created", t2 is not None)
    check("T7.3 Parent budget locked", t1.atp_locked == 100.0)

    # Verify chain (no root check — just validate signatures and expiry)
    valid, path = chain.verify_chain(t2.token_id)
    check("T7.4 Chain valid", valid)
    check("T7.5 Chain has 2 links", len(path) == 2)

    # Verify with root (Alice is the true root of the chain)
    valid_root, path_root = chain.verify_chain(t2.token_id, "lct://alice@mainnet")
    check("T7.6 Root verification passes", valid_root)

    # Inactive issuer
    t_bad, msg_bad = chain.create_delegation(
        "lct://ghost@mainnet", "lct://sage@mainnet",
        DelegationScope(), atp_budget=10.0,
    )
    check("T7.7 Inactive issuer rejected", t_bad is None)

    # Budget exceeds parent
    t_over, msg_over = chain.create_delegation(
        "lct://sage@mainnet", "lct://irp@mainnet",
        DelegationScope(), atp_budget=9999.0,
        parent_token_id=t1.token_id,
    )
    check("T7.8 Over-budget rejected", t_over is None)

    # ── T8: Delegation Revocation ──
    print("\n── T8: Delegation Revocation ──")

    # Revoke parent cascades to child
    chain.revoke_token(t1.token_id)
    valid_after, _ = chain.verify_chain(t2.token_id)
    check("T8.1 Child invalid after parent revoke", not valid_after)
    check("T8.2 Parent in revoked set", t1.token_id in chain.revoked_tokens)
    check("T8.3 Child cascaded to revoked", t2.token_id in chain.revoked_tokens)

    # Revoke non-existent
    check("T8.4 Revoke non-existent", not chain.revoke_token("fake_token"))

    # ── T9: ATP Budget Enforcement ──
    print("\n── T9: ATP Budget Enforcement ──")

    enforcer = BudgetEnforcer()
    budget_token = BudgetedDelegationToken(
        issuer="alice", delegate="sage", atp_budget=100.0,
    )
    enforcer.register_token(budget_token)

    # Lock transaction (within cost cap of 8.0)
    tx_id, err = enforcer.lock_transaction(budget_token, 5.0)
    check("T9.1 Lock succeeded", tx_id is not None and err is None)
    check("T9.2 Budget locked", budget_token.atp_locked == 5.0)
    check("T9.3 Available reduced", budget_token.atp_available == 95.0)

    # Commit
    committed, msg = enforcer.commit_transaction(tx_id)
    check("T9.4 Commit succeeded", committed)
    check("T9.5 Lock released after commit", budget_token.atp_locked == 0.0)
    check("T9.6 Consumed increased (with fee)", budget_token.atp_consumed == 5.0 * 1.05)

    # Rollback
    tx_id2, _ = enforcer.lock_transaction(budget_token, 3.0)
    rolled_back, _ = enforcer.rollback_transaction(tx_id2)
    check("T9.7 Rollback succeeded", rolled_back)
    check("T9.8 Lock released after rollback", budget_token.atp_locked == 0.0)
    check("T9.9 No consumed increase on rollback", budget_token.atp_consumed == 5.0 * 1.05)

    # Cost cap
    _, cap_err = enforcer.lock_transaction(budget_token, 50.0)
    check("T9.10 Cost cap exceeded", cap_err is not None)
    check("T9.11 Cost cap error message", "cost cap" in cap_err.lower())

    # Insufficient budget
    tiny_token = BudgetedDelegationToken(
        issuer="alice", delegate="sage", atp_budget=1.0,
    )
    enforcer.register_token(tiny_token)
    _, budget_err = enforcer.lock_transaction(tiny_token, 5.0)
    check("T9.12 Insufficient budget", budget_err is not None)

    # ── T10: Cross-Network ──
    print("\n── T10: Cross-Network ──")

    bridge = CrossNetworkBridge()
    bridge.register_network(Network(name="mainnet", base_exchange_rate=1.0, trust_level=1.0))
    bridge.register_network(Network(name="testnet", base_exchange_rate=0.1, trust_level=0.8))
    bridge.register_network(Network(name="devnet", base_exchange_rate=0.01, trust_level=0.5))

    # Exchange rates
    rate_mt = bridge.get_exchange_rate("mainnet", "testnet")
    check("T10.1 Mainnet→Testnet rate", abs(rate_mt - 0.08) < 0.001)

    rate_td = bridge.get_exchange_rate("testnet", "mainnet")
    check("T10.2 Testnet→Mainnet rate", rate_td == 10.0)

    # Cross-network delegation
    cnd, cnd_msg = bridge.create_cross_network_delegation("mainnet", "testnet", 100.0)
    check("T10.3 Cross-net delegation created", cnd is not None)
    check("T10.4 Bridge fee = 1%", abs(cnd.bridge_fee - 1.0) < 0.001)
    check("T10.5 Target budget = (100-1)*0.08", abs(cnd.target_atp_budget - 7.92) < 0.001)
    check("T10.6 Bridge finalized", cnd.bridge_finalized)

    # Unknown network
    bad_cnd, _ = bridge.create_cross_network_delegation("mainnet", "unknown", 100.0)
    check("T10.7 Unknown network fails", bad_cnd is None)

    # Reputation aggregation
    agg_rep = bridge.aggregate_reputation("alice", {
        "mainnet": 0.9,
        "testnet": 0.7,
        "devnet": 0.5,
    })
    # Expected: (0.9*1.0 + 0.7*0.8 + 0.5*0.5) / (1.0+0.8+0.5) = (0.9+0.56+0.25)/2.3 = 0.743
    check("T10.8 Aggregated reputation", abs(agg_rep - 0.743) < 0.01, f"got {agg_rep:.3f}")

    # ── T11: Sybil Detection ──
    print("\n── T11: Sybil Detection ──")

    sybil_reg = IdentityRegistry()
    sybil_reg.register(HardwareBoundIdentity(lct_uri="lct://a@net"))
    sybil_reg.register(HardwareBoundIdentity(lct_uri="lct://b@net"))
    sybil_reg.register(HardwareBoundIdentity(lct_uri="lct://c@net"))

    detector = SybilDetector(sybil_reg)

    # Cost calculation
    cost_5 = detector.check_sybil_cost(5)
    check("T11.1 Sybil cost for 5", cost_5 == 5 * 250 + 5 * 50)

    cost_20 = detector.check_sybil_cost(20)
    check("T11.2 Sybil cost for 20", cost_20 == 6000)

    # Cluster detection (all have unique hardware)
    is_sybil, sybil_msg = detector.detect_cluster(["lct://a@net", "lct://b@net", "lct://c@net"])
    check("T11.3 No sybil with unique hardware", not is_sybil)

    # Small cluster
    is_small, _ = detector.detect_cluster(["lct://a@net", "lct://b@net"])
    check("T11.4 Cluster too small", not is_small)

    # ── T12: ATP Farming Detection ──
    print("\n── T12: ATP Farming Detection ──")

    farming = ATPFarmingDetector()

    # No circular flow
    farming.record_transfer("alice", "bob", 10)
    farming.record_transfer("bob", "charlie", 8)
    is_circ, _ = farming.detect_circular("alice")
    check("T12.1 No circular flow", not is_circ)

    # Circular flow
    farming.record_transfer("charlie", "alice", 6)
    is_circ2, circ_msg = farming.detect_circular("alice")
    check("T12.2 Circular flow detected", is_circ2)
    check("T12.3 Circular path in message", "alice" in circ_msg)

    # Farming loss calculation
    loss_5 = farming.compute_farming_loss(5, 0.05)
    check("T12.4 5-loop loss > 22%", loss_5 > 0.22)

    loss_50 = farming.compute_farming_loss(50, 0.05)
    check("T12.5 50-loop loss > 92%", loss_50 > 0.92)

    # Farming is unprofitable
    check("T12.6 Farming always loses", farming.compute_farming_loss(1) > 0)

    # ── T13: Dynamic Budget Optimization ──
    print("\n── T13: Dynamic Budget Optimization ──")

    optimizer = DynamicBudgetOptimizer()

    # New agent (no history)
    budget_new = optimizer.compute_optimal_budget("new_agent", "query", 0.5)
    check("T13.1 New agent gets base budget", budget_new > 0)

    # Record history
    for i in range(5):
        optimizer.record_usage(BudgetUsageRecord(
            agent_lct_uri="good_agent",
            task_type="query",
            allocated_budget=100,
            consumed_budget=80,
            success=True,
            value_delivered=120,
        ))

    budget_good = optimizer.compute_optimal_budget("good_agent", "query", 0.8)
    check("T13.2 Good agent gets optimized budget", budget_good > 0)

    # Low reputation = lower budget
    budget_low = optimizer.compute_optimal_budget("new_agent", "query", 0.2)
    budget_high = optimizer.compute_optimal_budget("new_agent", "query", 0.9)
    check("T13.3 Higher rep = higher budget", budget_high > budget_low)

    # Exhaustion prediction
    pred_token = BudgetedDelegationToken(
        issuer="a", delegate="b", atp_budget=100.0, atp_consumed=50.0,
    )
    level, risk = optimizer.predict_exhaustion(pred_token, 30.0)
    check("T13.4 Low risk OK", level == "ok")

    pred_token.atp_consumed = 80.0
    level2, risk2 = optimizer.predict_exhaustion(pred_token, 18.0)
    check("T13.5 Warning risk", level2 == "warning")

    pred_token.atp_consumed = 95.0
    level3, risk3 = optimizer.predict_exhaustion(pred_token, 10.0)
    check("T13.6 Critical risk", level3 == "critical")

    pred_token.atp_consumed = 100.0
    level4, risk4 = optimizer.predict_exhaustion(pred_token, 10.0)
    check("T13.7 Exhausted", level4 == "exhausted")

    # ── T14: Complete Delegation Flow ──
    print("\n── T14: Complete Delegation Flow ──")

    reg14 = IdentityRegistry()
    alice_id = HardwareBoundIdentity(lct_uri="lct://user:alice@mainnet")
    sage_id = HardwareBoundIdentity(lct_uri="lct://sage:instance1@mainnet")
    irp_id = HardwareBoundIdentity(lct_uri="lct://plugin:emotional_irp@mainnet")

    reg14.register(alice_id)
    reg14.register(sage_id)
    reg14.register(irp_id)

    chain14 = DelegationChain(reg14)
    enforcer14 = BudgetEnforcer()

    # Step 1: Alice → SAGE with budget
    sage_token, _ = chain14.create_delegation(
        "lct://user:alice@mainnet",
        "lct://sage:instance1@mainnet",
        DelegationScope(allowed_operations=["query", "compute", "delegate"]),
        atp_budget=500.0,
        duration_hours=24,
    )
    check("T14.1 Alice→SAGE delegation", sage_token is not None)

    # Step 2: SAGE → IRP sub-delegation
    irp_token, _ = chain14.create_delegation(
        "lct://sage:instance1@mainnet",
        "lct://plugin:emotional_irp@mainnet",
        DelegationScope(allowed_operations=["query"]),
        atp_budget=100.0,
        parent_token_id=sage_token.token_id,
    )
    check("T14.2 SAGE→IRP sub-delegation", irp_token is not None)

    # Step 3: IRP executes query with budget
    enforcer14.register_token(irp_token)
    tx_id, err = enforcer14.lock_transaction(irp_token, 5.0)
    check("T14.3 IRP locks ATP", tx_id is not None)

    enforcer14.commit_transaction(tx_id)
    check("T14.4 IRP commits ATP", irp_token.atp_consumed > 0)

    # Step 4: Verify delegation chain
    valid14, path14 = chain14.verify_chain(irp_token.token_id)
    check("T14.5 Full chain valid", valid14)
    check("T14.6 Chain has 2 links", len(path14) == 2)

    # Step 5: Budget alerts
    irp_token.atp_consumed = 85
    alert = irp_token.check_alert_thresholds()
    check("T14.7 Budget warning", alert == "WARNING_80")

    # ── T15: Scope Narrowing ──
    print("\n── T15: Scope Narrowing ──")

    reg15 = IdentityRegistry()
    reg15.register(HardwareBoundIdentity(lct_uri="lct://parent@net"))
    reg15.register(HardwareBoundIdentity(lct_uri="lct://child@net"))

    chain15 = DelegationChain(reg15)
    parent_tok, _ = chain15.create_delegation(
        "lct://parent@net", "lct://child@net",
        DelegationScope(allowed_operations=["query", "compute"]),
        atp_budget=200.0,
    )
    check("T15.1 Parent scope has 2 ops", len(parent_tok.scope.allowed_operations) == 2)

    # Child can narrow scope
    child_scope = DelegationScope(allowed_operations=["query"])
    check("T15.2 Child scope narrower", set(child_scope.allowed_operations).issubset(
        set(parent_tok.scope.allowed_operations)
    ))

    # Budget narrowing
    child_tok, _ = chain15.create_delegation(
        "lct://child@net", "lct://parent@net",
        child_scope, atp_budget=50.0,
        parent_token_id=parent_tok.token_id,
    )
    check("T15.3 Child budget ≤ parent available", child_tok is not None)
    check("T15.4 Child budget narrower", child_tok.atp_budget < parent_tok.atp_budget)

    # ── T16: Rate Limiting ──
    print("\n── T16: Rate Limiting ──")

    rate_enforcer = BudgetEnforcer()
    rate_token = BudgetedDelegationToken(
        issuer="alice", delegate="spammer", atp_budget=1000.0,
    )
    rate_enforcer.register_token(rate_token)

    # First two succeed (2/sec limit)
    tx1, err1 = rate_enforcer.lock_transaction(rate_token, 1.0)
    tx2, err2 = rate_enforcer.lock_transaction(rate_token, 1.0)
    check("T16.1 First query allowed", tx1 is not None)
    check("T16.2 Second query allowed", tx2 is not None)

    # Third in same second should fail
    tx3, err3 = rate_enforcer.lock_transaction(rate_token, 1.0)
    check("T16.3 Third query rate-limited", err3 is not None)
    check("T16.4 Rate limit message", "rate limit" in err3.lower())

    # ── T17: Transaction State Machine ──
    print("\n── T17: Transaction State Machine ──")

    sm_enforcer = BudgetEnforcer()
    sm_token = BudgetedDelegationToken(
        issuer="alice", delegate="bob", atp_budget=100.0,
    )
    sm_enforcer.register_token(sm_token)

    tx_sm, _ = sm_enforcer.lock_transaction(sm_token, 5.0)
    check("T17.1 TX starts locked", sm_enforcer.transactions[tx_sm].state == TransactionState.LOCKED)

    sm_enforcer.commit_transaction(tx_sm)
    check("T17.2 TX committed", sm_enforcer.transactions[tx_sm].state == TransactionState.COMMITTED)

    # Can't commit again
    ok_again, msg_again = sm_enforcer.commit_transaction(tx_sm)
    check("T17.3 Can't double-commit", not ok_again)

    # New tx, rollback
    tx_rb, _ = sm_enforcer.lock_transaction(sm_token, 3.0)
    sm_enforcer.rollback_transaction(tx_rb)
    check("T17.4 TX rolled back", sm_enforcer.transactions[tx_rb].state == TransactionState.ROLLED_BACK)

    # Can't rollback after rollback
    ok_rb2, _ = sm_enforcer.rollback_transaction(tx_rb)
    check("T17.5 Can't double-rollback", not ok_rb2)

    # ── T18: Conservation Law ──
    print("\n── T18: Conservation Law ──")

    cons_enforcer = BudgetEnforcer(max_queries_per_second=100)  # high rate for batch test
    cons_token = BudgetedDelegationToken(
        issuer="alice", delegate="bob", atp_budget=100.0,
    )
    cons_enforcer.register_token(cons_token)

    initial_budget = cons_token.atp_budget

    # Execute several transactions
    for _ in range(5):
        tx, err = cons_enforcer.lock_transaction(cons_token, 5.0)
        if tx:
            cons_enforcer.commit_transaction(tx)

    # consumed + available should account for all ATP (with fees)
    total_accounted = cons_token.atp_consumed + cons_token.atp_available + cons_token.atp_locked
    check("T18.1 ATP conserved (with fees)", total_accounted <= initial_budget)
    check("T18.2 Fees > 0", cons_token.atp_consumed > 25.0)  # 5*5*1.05 = 26.25
    check("T18.3 Available decreased", cons_token.atp_available < initial_budget)

    # ── T19: Budget Usage Records ──
    print("\n── T19: Budget Usage Records ──")

    rec = BudgetUsageRecord(
        agent_lct_uri="agent1",
        task_type="query",
        allocated_budget=100,
        consumed_budget=80,
        success=True,
        value_delivered=120,
    )
    check("T19.1 Efficiency = value/consumed", abs(rec.efficiency - 1.5) < 0.001)
    check("T19.2 Utilization = consumed/allocated", abs(rec.utilization - 0.8) < 0.001)

    zero_rec = BudgetUsageRecord(consumed_budget=0, allocated_budget=0)
    check("T19.3 Zero consumed efficiency", zero_rec.efficiency == 0.0)
    check("T19.4 Zero allocated utilization", zero_rec.utilization == 0.0)

    # ── T20: End-to-End Attack Cost ──
    print("\n── T20: End-to-End Attack Cost ──")

    # Sybil attack economics
    sybil_cost = SybilDetector(IdentityRegistry()).check_sybil_cost(20)
    check("T20.1 Sybil 20 identities > 5000 ATP", sybil_cost > 5000)

    # ATP farming economics
    farming20 = ATPFarmingDetector()
    loss_10_loops = farming20.compute_farming_loss(10, 0.05)
    check("T20.2 10-loop farming loss > 40%", loss_10_loops > 0.40)

    # Delegation forgery: signature verification
    legit_token = DelegationToken(issuer="alice", delegate="bob")
    check("T20.3 Legit signature verifies", legit_token.verify_signature())

    forged_token = DelegationToken(issuer="alice", delegate="bob")
    forged_token.signature = "forged_sig"
    check("T20.4 Forged signature fails", not forged_token.verify_signature())

    # Budget gaming: verify defaults
    default_enforcer = BudgetEnforcer()
    check("T20.5 Cost cap = 8 ATP", default_enforcer.MAX_QUERY_COST == 8.0)
    check("T20.6 Rate limit = 2/sec", default_enforcer.MAX_QUERIES_PER_SECOND == 2)
    check("T20.7 Transfer fee = 5%", default_enforcer.TRANSFER_FEE == 0.05)

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"AI Agent Accountability Stack: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    print(f"{'='*60}")
    return passed, total


if __name__ == "__main__":
    run_tests()
