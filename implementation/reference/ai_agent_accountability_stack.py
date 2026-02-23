#!/usr/bin/env python3
"""
Web4 Reference Implementation: AI Agent Accountability Stack
Spec: proposals/WEB4-PROPOSAL-001-AI-AGENT-ACCOUNTABILITY-STACK.md

Covers all 6 sections of the proposal:
  §1 Hardware-Bound Identity (binding, attestation, migration, revocation)
  §2 Delegation Chain (tokens, scope narrowing, chain verification)
  §3 ATP Budget Enforcement (lock-commit-rollback, alerts, hierarchical budgets)
  §4 Cross-Network Delegation (exchange rates, bridge finality, reputation aggregation)
  §5 Security Mitigations (sybil, forgery, gaming, farming prevention)
  §6 Dynamic Budget Optimization (performance tracking, exhaustion prediction, adaptive allocation)
"""

import copy
import hashlib
import math
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ── §1 Hardware-Bound Identity ───────────────────────────────────────────────

class HardwareType(Enum):
    TPM_2_0 = "TPM_2.0"
    SECURE_ENCLAVE = "SecureEnclave"
    TRUSTZONE = "TrustZone"
    SOFTWARE_EMULATED = "SoftwareEmulated"  # testing only


@dataclass
class HardwareAttestation:
    """§1.2 — Attestation proving identity is bound to physical hardware."""
    tpm_public_key_hash: str       # SHA-256 hash of TPM public key
    tpm_attestation_signature: str # Signed by TPM
    platform_info: Dict[str, str]  # Hardware details
    timestamp: str                 # ISO 8601

    def to_dict(self) -> Dict:
        return {
            "tpm_public_key_hash": self.tpm_public_key_hash,
            "tpm_attestation_signature": self.tpm_attestation_signature,
            "platform_info": self.platform_info,
            "timestamp": self.timestamp,
        }


@dataclass
class HardwareBoundIdentity:
    """§1.1 — AI agent identity bound to hardware security module."""
    lct_uri: str            # lct://namespace:name@network
    hardware_id: str        # SHA-256 hash of TPM public key
    attestation: HardwareAttestation
    signature: str          # Signed with hardware-bound key
    created_at: str         # ISO 8601
    expires_at: Optional[str] = None
    hardware_type: HardwareType = HardwareType.TPM_2_0
    migration_history: List[Dict] = field(default_factory=list)
    revoked: bool = False

    def to_dict(self) -> Dict:
        return {
            "lct_uri": self.lct_uri,
            "hardware_id": self.hardware_id,
            "attestation": self.attestation.to_dict(),
            "signature": self.signature,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "hardware_type": self.hardware_type.value,
            "revoked": self.revoked,
        }


@dataclass
class IdentityRevocation:
    """§1.5 — Revocation record for compromised identities."""
    identity_lct_uri: str
    revoked_at: str
    reason: str          # "compromised", "migrated", "expired"
    revocation_signature: str  # Signed by issuer
    old_hardware_id: str = ""

    VALID_REASONS = {"compromised", "migrated", "expired"}


class HardwareIdentityService:
    """
    §1 — Complete hardware-bound identity management.

    Handles creation, verification, migration, and revocation.
    """

    def __init__(self):
        self.identities: Dict[str, HardwareBoundIdentity] = {}
        self.revocation_list: Dict[str, IdentityRevocation] = {}
        # Map hardware_id → lct_uri for sybil detection
        self.hardware_to_identity: Dict[str, str] = {}

    def _simulate_tpm_keygen(self, lct_uri: str, hw_type: HardwareType) -> Tuple[str, str]:
        """Simulate TPM key generation (in production: real TPM call)."""
        seed = f"{lct_uri}:{hw_type.value}:{time.time_ns()}"
        pub_key_hash = hashlib.sha256(seed.encode()).hexdigest()
        signature = hashlib.sha256(f"sig:{seed}".encode()).hexdigest()
        return pub_key_hash, signature

    def _simulate_attestation_sig(self, pub_key_hash: str) -> str:
        """Simulate TPM attestation signature."""
        return hashlib.sha256(f"attest:{pub_key_hash}".encode()).hexdigest()

    def create_identity(
        self,
        lct_uri: str,
        hardware_type: HardwareType = HardwareType.TPM_2_0,
        platform_info: Optional[Dict[str, str]] = None,
        expires_hours: Optional[int] = None,
    ) -> HardwareBoundIdentity:
        """§1.3 — Binding process: generate keys, create attestation, sign identity."""
        if lct_uri in self.identities:
            raise ValueError(f"Identity already exists: {lct_uri}")

        # Step 1: Generate hardware-bound keypair
        pub_key_hash, signature = self._simulate_tpm_keygen(lct_uri, hardware_type)

        # Step 2: Check for hardware reuse (sybil detection §5.2)
        if pub_key_hash in self.hardware_to_identity:
            raise ValueError(
                f"Hardware already bound to {self.hardware_to_identity[pub_key_hash]}"
            )

        # Step 3: Create attestation
        now = datetime.now(timezone.utc)
        attestation = HardwareAttestation(
            tpm_public_key_hash=pub_key_hash,
            tpm_attestation_signature=self._simulate_attestation_sig(pub_key_hash),
            platform_info=platform_info or {"type": hardware_type.value},
            timestamp=now.isoformat(),
        )

        # Step 4: Create identity
        expires_at = None
        if expires_hours:
            expires_at = (now + timedelta(hours=expires_hours)).isoformat()

        identity = HardwareBoundIdentity(
            lct_uri=lct_uri,
            hardware_id=pub_key_hash,
            attestation=attestation,
            signature=signature,
            created_at=now.isoformat(),
            expires_at=expires_at,
            hardware_type=hardware_type,
        )

        self.identities[lct_uri] = identity
        self.hardware_to_identity[pub_key_hash] = lct_uri
        return identity

    def verify_identity(self, identity: HardwareBoundIdentity) -> Tuple[bool, str]:
        """Verify identity attestation chain."""
        # Check revocation
        if identity.lct_uri in self.revocation_list:
            return False, "Identity has been revoked"
        if identity.revoked:
            return False, "Identity marked as revoked"

        # Check expiration
        if identity.expires_at:
            expires = datetime.fromisoformat(identity.expires_at)
            if datetime.now(timezone.utc) > expires:
                return False, "Identity has expired"

        # Verify hardware binding (attestation matches identity)
        if identity.hardware_id != identity.attestation.tpm_public_key_hash:
            return False, "Hardware ID mismatch with attestation"

        # Verify attestation signature
        expected_attest_sig = self._simulate_attestation_sig(identity.hardware_id)
        if identity.attestation.tpm_attestation_signature != expected_attest_sig:
            return False, "Attestation signature invalid"

        return True, "Valid"

    def migrate_identity(
        self,
        lct_uri: str,
        new_hardware_type: HardwareType = HardwareType.TPM_2_0,
        new_platform_info: Optional[Dict[str, str]] = None,
    ) -> HardwareBoundIdentity:
        """§1.4 — Migration when hardware changes."""
        if lct_uri not in self.identities:
            raise ValueError(f"Identity not found: {lct_uri}")

        old_identity = self.identities[lct_uri]
        old_hw_id = old_identity.hardware_id

        # Remove old hardware mapping
        if old_hw_id in self.hardware_to_identity:
            del self.hardware_to_identity[old_hw_id]

        # Generate new hardware keys
        new_pub_key_hash, new_signature = self._simulate_tpm_keygen(
            lct_uri, new_hardware_type
        )

        now = datetime.now(timezone.utc)

        # Create migration record
        migration_record = {
            "old_hardware_id": old_hw_id,
            "new_hardware_id": new_pub_key_hash,
            "migrated_at": now.isoformat(),
            "migration_signature": hashlib.sha256(
                f"migrate:{old_hw_id}:{new_pub_key_hash}".encode()
            ).hexdigest(),
        }

        # Create new attestation
        attestation = HardwareAttestation(
            tpm_public_key_hash=new_pub_key_hash,
            tpm_attestation_signature=self._simulate_attestation_sig(new_pub_key_hash),
            platform_info=new_platform_info or {"type": new_hardware_type.value},
            timestamp=now.isoformat(),
        )

        # Update identity
        old_identity.hardware_id = new_pub_key_hash
        old_identity.attestation = attestation
        old_identity.signature = new_signature
        old_identity.hardware_type = new_hardware_type
        old_identity.migration_history.append(migration_record)

        self.hardware_to_identity[new_pub_key_hash] = lct_uri

        # Revoke old hardware
        self.revocation_list[f"{lct_uri}:hw:{old_hw_id}"] = IdentityRevocation(
            identity_lct_uri=lct_uri,
            revoked_at=now.isoformat(),
            reason="migrated",
            revocation_signature=migration_record["migration_signature"],
            old_hardware_id=old_hw_id,
        )

        return old_identity

    def revoke_identity(self, lct_uri: str, reason: str = "compromised") -> IdentityRevocation:
        """§1.5 — Revoke compromised identity."""
        if reason not in IdentityRevocation.VALID_REASONS:
            raise ValueError(f"Invalid reason: {reason}")

        if lct_uri not in self.identities:
            raise ValueError(f"Identity not found: {lct_uri}")

        identity = self.identities[lct_uri]
        now = datetime.now(timezone.utc)

        revocation = IdentityRevocation(
            identity_lct_uri=lct_uri,
            revoked_at=now.isoformat(),
            reason=reason,
            revocation_signature=hashlib.sha256(
                f"revoke:{lct_uri}:{reason}".encode()
            ).hexdigest(),
            old_hardware_id=identity.hardware_id,
        )

        identity.revoked = True
        self.revocation_list[lct_uri] = revocation

        # Remove hardware mapping
        if identity.hardware_id in self.hardware_to_identity:
            del self.hardware_to_identity[identity.hardware_id]

        return revocation

    def is_revoked(self, lct_uri: str) -> bool:
        """Check if identity is on revocation list."""
        return lct_uri in self.revocation_list


# ── §2 Delegation Chain ─────────────────────────────────────────────────────

@dataclass
class ResourceLimits:
    """Resource limits within a delegation scope."""
    max_atp_per_operation: float = 100.0
    max_operations_per_hour: int = 100
    max_total_atp: float = 1000.0


@dataclass
class TimeRestrictions:
    """Time-based restrictions on delegation."""
    allowed_hours: Optional[Tuple[int, int]] = None  # (start_hour, end_hour)
    allowed_days: Optional[List[int]] = None  # 0=Mon, 6=Sun
    timezone: str = "UTC"


@dataclass
class DelegationScope:
    """§2.2 — What operations are authorized."""
    allowed_operations: List[str]        # e.g., ["query", "compute", "delegate"]
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    network_restrictions: List[str] = field(default_factory=lambda: ["mainnet"])
    time_restrictions: Optional[TimeRestrictions] = None

    def is_subset_of(self, parent: "DelegationScope") -> bool:
        """
        Verify child scope ⊆ parent scope.
        Delegation can only narrow, never widen.
        """
        # All child operations must be in parent
        if not set(self.allowed_operations).issubset(set(parent.allowed_operations)):
            return False

        # Resource limits must be ≤ parent
        if self.resource_limits.max_atp_per_operation > parent.resource_limits.max_atp_per_operation:
            return False
        if self.resource_limits.max_operations_per_hour > parent.resource_limits.max_operations_per_hour:
            return False
        if self.resource_limits.max_total_atp > parent.resource_limits.max_total_atp:
            return False

        # Network restrictions must be subset
        if not set(self.network_restrictions).issubset(set(parent.network_restrictions)):
            return False

        return True


@dataclass
class DelegationToken:
    """§2.1 — Cryptographic delegation token."""
    token_id: str
    issuer: str          # LCT URI (who delegates)
    delegate: str        # LCT URI (who receives delegation)
    scope: DelegationScope
    issued_at: str
    expires_at: str
    signature: str       # Signed by issuer's private key
    parent_token_id: Optional[str] = None  # For sub-delegation
    revoked: bool = False

    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        expires = datetime.fromisoformat(self.expires_at)
        return now > expires

    def to_dict(self) -> Dict:
        return {
            "token_id": self.token_id,
            "issuer": self.issuer,
            "delegate": self.delegate,
            "scope": {
                "allowed_operations": self.scope.allowed_operations,
                "network_restrictions": self.scope.network_restrictions,
            },
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "signature": self.signature,
            "parent_token_id": self.parent_token_id,
        }


class DelegationChainService:
    """
    §2 — Delegation chain management.

    All AI agent actions MUST be traceable to authorizing human
    through cryptographic delegation chain.
    """

    # Entities that are considered "human roots" (terminate chains)
    HUMAN_PREFIXES = ("lct://user:", "lct://human:")

    def __init__(self, identity_service: HardwareIdentityService):
        self.identity_service = identity_service
        self.tokens: Dict[str, DelegationToken] = {}
        self.revoked_tokens: Set[str] = set()
        # Issuer → list of tokens they've issued
        self.tokens_by_issuer: Dict[str, List[str]] = {}

    def _sign_token(self, issuer: str, data: str) -> str:
        """Simulate cryptographic signature."""
        return hashlib.sha256(f"sig:{issuer}:{data}".encode()).hexdigest()

    def _verify_signature(self, issuer: str, data: str, signature: str) -> bool:
        """Verify token signature."""
        expected = self._sign_token(issuer, data)
        return signature == expected

    def create_delegation(
        self,
        issuer: str,
        delegate: str,
        scope: DelegationScope,
        duration_hours: int = 24,
        parent_token_id: Optional[str] = None,
    ) -> DelegationToken:
        """Create a delegation token from issuer to delegate."""
        # Verify issuer identity exists (unless human root)
        if not self._is_human_root(issuer):
            if issuer not in self.identity_service.identities:
                raise ValueError(f"Issuer identity not found: {issuer}")
            if self.identity_service.is_revoked(issuer):
                raise ValueError(f"Issuer identity revoked: {issuer}")

        # If sub-delegation, verify parent token
        if parent_token_id:
            parent_token = self.tokens.get(parent_token_id)
            if not parent_token:
                raise ValueError(f"Parent token not found: {parent_token_id}")
            if parent_token.is_expired():
                raise ValueError("Parent token expired")
            if parent_token.revoked or parent_token_id in self.revoked_tokens:
                raise ValueError("Parent token revoked")
            # Verify issuer is the delegate of parent token
            if parent_token.delegate != issuer:
                raise ValueError("Issuer is not the delegate of parent token")
            # Scope must narrow (child ⊆ parent)
            if not scope.is_subset_of(parent_token.scope):
                raise ValueError("Child scope exceeds parent scope")
            # Check if "delegate" is in parent's allowed operations
            if "delegate" not in parent_token.scope.allowed_operations:
                raise ValueError("Parent scope does not allow sub-delegation")

        now = datetime.now(timezone.utc)
        token_id = f"token_{uuid.uuid4().hex[:12]}"
        expires_at = (now + timedelta(hours=duration_hours)).isoformat()

        signature = self._sign_token(
            issuer, f"{token_id}:{delegate}:{expires_at}"
        )

        token = DelegationToken(
            token_id=token_id,
            issuer=issuer,
            delegate=delegate,
            scope=scope,
            issued_at=now.isoformat(),
            expires_at=expires_at,
            signature=signature,
            parent_token_id=parent_token_id,
        )

        self.tokens[token_id] = token
        self.tokens_by_issuer.setdefault(issuer, []).append(token_id)
        return token

    def _is_human_root(self, lct_uri: str) -> bool:
        """Check if URI represents a human (chain root)."""
        return any(lct_uri.startswith(p) for p in self.HUMAN_PREFIXES)

    def verify_chain(
        self,
        token: DelegationToken,
        max_depth: int = 10,
    ) -> Tuple[bool, str, List[str]]:
        """
        §2.3 — Verify delegation chain.

        Returns (is_valid, reason, chain_path).
        Chain must terminate at an authorized human.
        """
        chain_path = []
        current = token
        depth = 0

        while depth < max_depth:
            # Check token not expired
            if current.is_expired():
                return False, f"Token {current.token_id} expired", chain_path

            # Check not revoked
            if current.revoked or current.token_id in self.revoked_tokens:
                return False, f"Token {current.token_id} revoked", chain_path

            # Verify signature
            expected_data = f"{current.token_id}:{current.delegate}:{current.expires_at}"
            if not self._verify_signature(current.issuer, expected_data, current.signature):
                return False, f"Invalid signature on {current.token_id}", chain_path

            chain_path.append(current.issuer)

            # Check if issuer is human root (chain terminates)
            if self._is_human_root(current.issuer):
                chain_path.append(f"→ {current.delegate}")
                return True, "Valid chain to human root", chain_path

            # Follow parent chain
            if current.parent_token_id:
                parent = self.tokens.get(current.parent_token_id)
                if not parent:
                    return False, f"Parent token {current.parent_token_id} not found", chain_path
                current = parent
            else:
                # No parent and issuer is not human
                return False, "Chain does not terminate at human root", chain_path

            depth += 1

        return False, f"Chain exceeds max depth {max_depth}", chain_path

    def revoke_token(self, token_id: str) -> bool:
        """Revoke a delegation token and all its children."""
        if token_id not in self.tokens:
            return False

        self.revoked_tokens.add(token_id)
        self.tokens[token_id].revoked = True

        # Cascade: revoke all children
        for tid, tok in self.tokens.items():
            if tok.parent_token_id == token_id and tid not in self.revoked_tokens:
                self.revoke_token(tid)

        return True

    def get_chain_depth(self, token: DelegationToken) -> int:
        """Get depth of delegation chain."""
        depth = 0
        current = token
        while current.parent_token_id:
            depth += 1
            parent = self.tokens.get(current.parent_token_id)
            if not parent:
                break
            current = parent
        return depth


# ── §3 ATP Budget Enforcement ────────────────────────────────────────────────

class BudgetAlertLevel(Enum):
    OK = "OK"
    WARNING_80 = "WARNING_80"
    CRITICAL_90 = "CRITICAL_90"
    EXHAUSTED_100 = "EXHAUSTED_100"


@dataclass
class BudgetAlert:
    """§3.3 — Automatic budget alert."""
    level: BudgetAlertLevel
    threshold: float
    triggered_at: str
    message: str


@dataclass
class BudgetTransaction:
    """Atomic ATP transaction (lock-commit-rollback)."""
    tx_id: str
    token_id: str
    amount: float
    status: str  # "locked", "committed", "rolled_back"
    created_at: str
    resolved_at: Optional[str] = None


@dataclass
class BudgetedDelegationToken:
    """§3.1 — Delegation token with ATP budget enforcement."""
    delegation: DelegationToken
    atp_budget: float
    atp_consumed: float = 0.0
    atp_locked: float = 0.0
    budget_alerts: List[BudgetAlert] = field(default_factory=list)
    child_allocations: Dict[str, float] = field(default_factory=dict)

    @property
    def atp_available(self) -> float:
        child_total = sum(self.child_allocations.values())
        return self.atp_budget - self.atp_consumed - self.atp_locked - child_total

    @property
    def utilization(self) -> float:
        if self.atp_budget <= 0:
            return 1.0
        return self.atp_consumed / self.atp_budget

    def get_alert_level(self) -> BudgetAlertLevel:
        if self.atp_budget <= 0:
            return BudgetAlertLevel.EXHAUSTED_100
        ratio = (self.atp_consumed + self.atp_locked) / self.atp_budget
        if ratio >= 1.0:
            return BudgetAlertLevel.EXHAUSTED_100
        elif ratio >= 0.9:
            return BudgetAlertLevel.CRITICAL_90
        elif ratio >= 0.8:
            return BudgetAlertLevel.WARNING_80
        return BudgetAlertLevel.OK


class ATPBudgetService:
    """
    §3 — ATP budget enforcement with lock-commit-rollback.

    All ATP spending MUST use atomic transactions.
    """

    def __init__(self):
        self.budgets: Dict[str, BudgetedDelegationToken] = {}
        self.transactions: Dict[str, BudgetTransaction] = {}
        self.alert_history: List[BudgetAlert] = []

    def create_budgeted_token(
        self,
        delegation: DelegationToken,
        atp_budget: float,
    ) -> BudgetedDelegationToken:
        """Create a budgeted delegation token."""
        if atp_budget <= 0:
            raise ValueError("ATP budget must be positive")

        bt = BudgetedDelegationToken(
            delegation=delegation,
            atp_budget=atp_budget,
        )
        self.budgets[delegation.token_id] = bt
        return bt

    def allocate_child_budget(
        self,
        parent_token_id: str,
        child_token_id: str,
        amount: float,
    ) -> bool:
        """§3.4 — Parent allocates sub-budget to child."""
        parent = self.budgets.get(parent_token_id)
        if not parent:
            raise ValueError(f"Parent budget not found: {parent_token_id}")

        if amount > parent.atp_available:
            raise ValueError(
                f"Insufficient parent budget: {parent.atp_available:.2f} available, {amount:.2f} requested"
            )

        parent.child_allocations[child_token_id] = amount

        # Create child budget entry
        child_deleg = DelegationToken(
            token_id=child_token_id,
            issuer="",
            delegate="",
            scope=DelegationScope(allowed_operations=[]),
            issued_at=datetime.now(timezone.utc).isoformat(),
            expires_at=datetime.now(timezone.utc).isoformat(),
            signature="",
        )
        child_bt = BudgetedDelegationToken(
            delegation=child_deleg,
            atp_budget=amount,
        )
        self.budgets[child_token_id] = child_bt
        return True

    def lock_transaction(
        self,
        token_id: str,
        amount: float,
    ) -> Tuple[Optional[str], Optional[str]]:
        """§3.2 — Lock ATP before operation. Returns (tx_id, error)."""
        bt = self.budgets.get(token_id)
        if not bt:
            return None, f"Budget not found: {token_id}"

        if amount > bt.atp_available:
            return None, f"Insufficient budget: {bt.atp_available:.2f} available, {amount:.2f} requested"

        # Check if budget is exhausted
        if bt.get_alert_level() == BudgetAlertLevel.EXHAUSTED_100:
            return None, "Budget exhausted"

        tx_id = f"tx_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        tx = BudgetTransaction(
            tx_id=tx_id,
            token_id=token_id,
            amount=amount,
            status="locked",
            created_at=now.isoformat(),
        )

        bt.atp_locked += amount
        self.transactions[tx_id] = tx

        # Check and generate alerts
        self._check_alerts(bt)

        return tx_id, None

    def commit_transaction(self, tx_id: str) -> bool:
        """§3.2 — Commit ATP (operation succeeded)."""
        tx = self.transactions.get(tx_id)
        if not tx or tx.status != "locked":
            return False

        bt = self.budgets.get(tx.token_id)
        if not bt:
            return False

        bt.atp_locked -= tx.amount
        bt.atp_consumed += tx.amount
        tx.status = "committed"
        tx.resolved_at = datetime.now(timezone.utc).isoformat()

        self._check_alerts(bt)
        return True

    def rollback_transaction(self, tx_id: str) -> bool:
        """§3.2 — Rollback ATP (operation failed)."""
        tx = self.transactions.get(tx_id)
        if not tx or tx.status != "locked":
            return False

        bt = self.budgets.get(tx.token_id)
        if not bt:
            return False

        bt.atp_locked -= tx.amount
        tx.status = "rolled_back"
        tx.resolved_at = datetime.now(timezone.utc).isoformat()
        return True

    def _check_alerts(self, bt: BudgetedDelegationToken):
        """Generate alerts at thresholds."""
        level = bt.get_alert_level()
        if level == BudgetAlertLevel.OK:
            return

        # Only alert once per level
        existing = {a.level for a in bt.budget_alerts}
        if level in existing:
            return

        now = datetime.now(timezone.utc).isoformat()
        messages = {
            BudgetAlertLevel.WARNING_80: "Budget running low (80% consumed)",
            BudgetAlertLevel.CRITICAL_90: "Budget nearly exhausted (90% consumed)",
            BudgetAlertLevel.EXHAUSTED_100: "Budget fully consumed, token invalid",
        }

        alert = BudgetAlert(
            level=level,
            threshold={"WARNING_80": 0.8, "CRITICAL_90": 0.9, "EXHAUSTED_100": 1.0}[level.value],
            triggered_at=now,
            message=messages.get(level, "Unknown alert"),
        )
        bt.budget_alerts.append(alert)
        self.alert_history.append(alert)


# ── §4 Cross-Network Delegation ─────────────────────────────────────────────

@dataclass
class Network:
    """Represents a Web4 network."""
    name: str
    base_exchange_rate: float = 1.0
    trust_level: float = 1.0
    min_confirmations: int = 12

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "base_exchange_rate": self.base_exchange_rate,
            "trust_level": self.trust_level,
        }


@dataclass
class CrossNetworkDelegationToken:
    """§4.1 — Delegation that spans networks."""
    budgeted_token: BudgetedDelegationToken
    source_network: Network
    target_network: Network
    exchange_rate: float
    source_atp_budget: float
    target_atp_budget: float
    bridge_contract: str
    bridge_tx_hash: str
    bridge_confirmations: int = 0
    bridge_finalized: bool = False
    bridge_fee_rate: float = 0.01  # 1% forward

    def to_dict(self) -> Dict:
        return {
            "source_network": self.source_network.name,
            "target_network": self.target_network.name,
            "exchange_rate": self.exchange_rate,
            "source_atp_budget": self.source_atp_budget,
            "target_atp_budget": self.target_atp_budget,
            "bridge_fee": self.source_atp_budget * self.bridge_fee_rate,
            "bridge_confirmations": self.bridge_confirmations,
            "bridge_finalized": self.bridge_finalized,
        }


class CrossNetworkService:
    """
    §4 — Cross-network delegation support.

    Handles exchange rates, bridge finality, and reputation aggregation.
    """

    FORWARD_FEE = 0.01   # 1% forward bridge fee
    RETURN_FEE = 0.005   # 0.5% return bridge fee
    MIN_CONFIRMATIONS = 12

    def __init__(self):
        self.networks: Dict[str, Network] = {}
        self.cross_tokens: Dict[str, CrossNetworkDelegationToken] = {}
        self.reputation_data: Dict[str, Dict[str, float]] = {}  # identity → {network: rep}

    def register_network(self, network: Network):
        self.networks[network.name] = network

    def get_exchange_rate(self, source: Network, target: Network) -> float:
        """§4.2 — Trust-weighted exchange rate."""
        base_rate = target.base_exchange_rate / source.base_exchange_rate
        return base_rate * target.trust_level

    def create_cross_network_delegation(
        self,
        budgeted_token: BudgetedDelegationToken,
        source_network: Network,
        target_network: Network,
        source_atp_budget: float,
    ) -> CrossNetworkDelegationToken:
        """Create cross-network delegation with bridge."""
        exchange_rate = self.get_exchange_rate(source_network, target_network)

        # Apply bridge fee
        bridge_fee = source_atp_budget * self.FORWARD_FEE
        net_source = source_atp_budget - bridge_fee

        # Convert to target network ATP
        target_atp = net_source * exchange_rate

        # Generate bridge identifiers
        bridge_contract = f"bridge:{source_network.name}:{target_network.name}"
        bridge_tx_hash = hashlib.sha256(
            f"{bridge_contract}:{source_atp_budget}:{time.time_ns()}".encode()
        ).hexdigest()

        cn_token = CrossNetworkDelegationToken(
            budgeted_token=budgeted_token,
            source_network=source_network,
            target_network=target_network,
            exchange_rate=exchange_rate,
            source_atp_budget=source_atp_budget,
            target_atp_budget=round(target_atp, 2),
            bridge_contract=bridge_contract,
            bridge_tx_hash=bridge_tx_hash,
            bridge_fee_rate=self.FORWARD_FEE,
        )

        self.cross_tokens[bridge_tx_hash] = cn_token
        return cn_token

    def confirm_bridge(self, bridge_tx_hash: str, confirmations: int) -> bool:
        """§4.3 — Advance bridge confirmations toward finality."""
        cn_token = self.cross_tokens.get(bridge_tx_hash)
        if not cn_token:
            return False

        cn_token.bridge_confirmations = confirmations
        if confirmations >= self.MIN_CONFIRMATIONS:
            cn_token.bridge_finalized = True
        return True

    def reverse_bridge(
        self,
        bridge_tx_hash: str,
        return_amount: float,
    ) -> float:
        """Return unused ATP to source network (with return fee)."""
        cn_token = self.cross_tokens.get(bridge_tx_hash)
        if not cn_token or not cn_token.bridge_finalized:
            return 0.0

        # Convert back with return fee
        reverse_rate = 1.0 / cn_token.exchange_rate
        source_amount = return_amount * reverse_rate
        fee = source_amount * self.RETURN_FEE
        return round(source_amount - fee, 2)

    def set_reputation(self, identity: str, network: str, reputation: float):
        """Set reputation for identity on a network."""
        self.reputation_data.setdefault(identity, {})[network] = reputation

    def aggregate_reputation(
        self,
        identity: str,
        networks: Optional[List[str]] = None,
    ) -> float:
        """§4.4 — Network-trust-weighted reputation aggregation."""
        if identity not in self.reputation_data:
            return 0.5  # default neutral

        rep_data = self.reputation_data[identity]
        target_nets = networks or list(rep_data.keys())

        total_weight = 0.0
        weighted_sum = 0.0

        for net_name in target_nets:
            if net_name not in rep_data or net_name not in self.networks:
                continue
            reputation = rep_data[net_name]
            weight = self.networks[net_name].trust_level
            weighted_sum += reputation * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.5


# ── §5 Security Mitigations ─────────────────────────────────────────────────

@dataclass
class SecurityEvent:
    """Security event for audit trail."""
    event_type: str   # "sybil_attempt", "forgery_attempt", "budget_gaming", "atp_farming"
    severity: str     # "low", "medium", "high", "critical"
    identity: str
    details: str
    timestamp: str
    mitigated: bool = False


class SecurityMitigationService:
    """
    §5 — Attack mitigation framework.

    Covers: budget gaming, sybil attacks, delegation forgery, ATP farming.
    """

    # §5.1 Rate limits
    MAX_QUERIES_PER_SECOND = 2
    MAX_ATP_PER_QUERY = 8.0
    IDENTITY_CREATION_COST = 50.0   # §5.2
    MAX_REPUTATION_PER_HOUR = 0.1   # §5.2
    TRANSFER_FEE_RATE = 0.05        # §5.4 - 5% per transfer
    CIRCULAR_FLOW_THRESHOLD = 10    # §5.4

    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.query_counts: Dict[str, List[float]] = {}  # identity → [timestamps]
        self.transfer_graph: Dict[str, Dict[str, float]] = {}  # from → {to: total}
        self.reputation_changes: Dict[str, List[Tuple[float, float]]] = {}  # identity → [(time, delta)]
        self.total_atp_supply: float = 0.0

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # §5.1 Budget Gaming Prevention

    def check_rate_limit(self, identity: str) -> Tuple[bool, Optional[str]]:
        """Check if identity exceeds query rate limit."""
        now = time.time()
        if identity not in self.query_counts:
            self.query_counts[identity] = []

        # Remove entries older than 1 second
        self.query_counts[identity] = [
            t for t in self.query_counts[identity] if now - t < 1.0
        ]

        if len(self.query_counts[identity]) >= self.MAX_QUERIES_PER_SECOND:
            self.events.append(SecurityEvent(
                event_type="budget_gaming",
                severity="medium",
                identity=identity,
                details=f"Rate limit exceeded: {len(self.query_counts[identity])} queries/sec",
                timestamp=self._now_iso(),
                mitigated=True,
            ))
            return False, "Rate limit exceeded"

        self.query_counts[identity].append(now)
        return True, None

    def check_cost_cap(self, amount: float) -> Tuple[bool, Optional[str]]:
        """Check if query cost exceeds per-query cap."""
        if amount > self.MAX_ATP_PER_QUERY:
            return False, f"Cost cap exceeded: {amount} > {self.MAX_ATP_PER_QUERY}"
        return True, None

    def detect_anomaly(
        self,
        identity: str,
        operation: str,
        amount: float,
        history: Optional[List[float]] = None,
    ) -> Tuple[bool, float]:
        """Detect anomalous spending patterns. Returns (is_anomaly, anomaly_score)."""
        if not history or len(history) < 3:
            return False, 0.0

        mean = sum(history) / len(history)
        if mean == 0:
            return amount > 0, 1.0

        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std_dev = math.sqrt(variance) if variance > 0 else 0.01

        # Z-score
        z_score = abs(amount - mean) / std_dev if std_dev > 0 else 0.0

        is_anomaly = z_score > 3.0  # 3-sigma rule
        if is_anomaly:
            self.events.append(SecurityEvent(
                event_type="budget_gaming",
                severity="high",
                identity=identity,
                details=f"Anomalous {operation}: amount={amount:.2f}, z={z_score:.2f}",
                timestamp=self._now_iso(),
                mitigated=True,
            ))

        return is_anomaly, z_score

    # §5.2 Sybil Attack Prevention

    def check_identity_creation_cost(self, atp_balance: float) -> Tuple[bool, Optional[str]]:
        """Check if creator has enough ATP to cover identity creation stake."""
        if atp_balance < self.IDENTITY_CREATION_COST:
            return False, f"Insufficient ATP: {atp_balance} < {self.IDENTITY_CREATION_COST} required"
        return True, None

    def check_reputation_velocity(
        self,
        identity: str,
        proposed_delta: float,
    ) -> Tuple[bool, Optional[str]]:
        """Check reputation gain rate doesn't exceed velocity limit."""
        now = time.time()
        if identity not in self.reputation_changes:
            self.reputation_changes[identity] = []

        # Sum reputation gains in the last hour
        one_hour_ago = now - 3600
        recent = [
            delta for t, delta in self.reputation_changes[identity]
            if t > one_hour_ago and delta > 0
        ]
        total_recent = sum(recent) + max(proposed_delta, 0)

        if total_recent > self.MAX_REPUTATION_PER_HOUR:
            self.events.append(SecurityEvent(
                event_type="sybil_attempt",
                severity="high",
                identity=identity,
                details=f"Reputation velocity exceeded: {total_recent:.3f}/hr > {self.MAX_REPUTATION_PER_HOUR}",
                timestamp=self._now_iso(),
                mitigated=True,
            ))
            return False, "Reputation velocity limit exceeded"

        self.reputation_changes[identity].append((now, proposed_delta))
        return True, None

    def analyze_social_graph(
        self,
        connections: Dict[str, Set[str]],
    ) -> List[Set[str]]:
        """Detect disconnected clusters (potential sybil groups)."""
        visited: Set[str] = set()
        clusters: List[Set[str]] = []

        def bfs(start: str) -> Set[str]:
            cluster = set()
            queue = [start]
            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue
                visited.add(node)
                cluster.add(node)
                for neighbor in connections.get(node, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)
            return cluster

        for node in connections:
            if node not in visited:
                cluster = bfs(node)
                clusters.append(cluster)

        # Flag small disconnected clusters
        suspicious = [c for c in clusters if len(c) <= 3 and len(clusters) > 1]
        for cluster in suspicious:
            self.events.append(SecurityEvent(
                event_type="sybil_attempt",
                severity="medium",
                identity=str(cluster),
                details=f"Suspicious disconnected cluster: {len(cluster)} nodes",
                timestamp=self._now_iso(),
            ))

        return clusters

    # §5.3 Delegation Forgery Prevention

    def verify_delegation_signature(
        self,
        token: DelegationToken,
        expected_issuer_key: str,
    ) -> Tuple[bool, Optional[str]]:
        """Verify delegation token cryptographic signature."""
        expected_data = f"{token.token_id}:{token.delegate}:{token.expires_at}"
        expected_sig = hashlib.sha256(
            f"sig:{token.issuer}:{expected_data}".encode()
        ).hexdigest()

        if token.signature != expected_sig:
            self.events.append(SecurityEvent(
                event_type="forgery_attempt",
                severity="critical",
                identity=token.delegate,
                details=f"Forged delegation from {token.issuer}: signature mismatch",
                timestamp=self._now_iso(),
                mitigated=True,
            ))
            return False, "Signature verification failed"

        return True, None

    # §5.4 ATP Farming Prevention

    def register_atp_supply(self, total: float):
        """Register total ATP supply for conservation checks."""
        self.total_atp_supply = total

    def check_conservation(
        self,
        balances: Dict[str, float],
    ) -> Tuple[bool, float]:
        """Verify ATP conservation law: total ATP is constant."""
        current_total = sum(balances.values())
        if self.total_atp_supply == 0:
            self.total_atp_supply = current_total
            return True, 0.0

        drift = abs(current_total - self.total_atp_supply)
        if drift > 0.01:  # tolerance
            self.events.append(SecurityEvent(
                event_type="atp_farming",
                severity="critical",
                identity="system",
                details=f"ATP conservation violation: expected={self.total_atp_supply:.2f}, actual={current_total:.2f}, drift={drift:.2f}",
                timestamp=self._now_iso(),
            ))
            return False, drift

        return True, drift

    def apply_transfer_fee(self, amount: float) -> Tuple[float, float]:
        """Apply 5% transfer fee. Returns (net_amount, fee)."""
        fee = amount * self.TRANSFER_FEE_RATE
        return amount - fee, fee

    def record_transfer(self, sender: str, receiver: str, amount: float):
        """Record transfer for circular flow detection."""
        self.transfer_graph.setdefault(sender, {})
        self.transfer_graph[sender][receiver] = (
            self.transfer_graph[sender].get(receiver, 0) + amount
        )

    def detect_circular_flows(self, start: str, max_depth: int = 15) -> List[List[str]]:
        """§5.4 — Detect circular ATP flows (farming attempts)."""
        cycles: List[List[str]] = []

        def dfs(current: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            for neighbor, amount in self.transfer_graph.get(current, {}).items():
                if neighbor == start and len(path) > 1:
                    cycle = path + [neighbor]
                    cycles.append(cycle)
                    if len(cycle) >= self.CIRCULAR_FLOW_THRESHOLD:
                        self.events.append(SecurityEvent(
                            event_type="atp_farming",
                            severity="high",
                            identity=start,
                            details=f"Circular flow detected: {len(cycle)} hops",
                            timestamp=self._now_iso(),
                            mitigated=True,
                        ))
                elif neighbor not in path:
                    dfs(neighbor, path + [neighbor], depth + 1)

        dfs(start, [start], 0)
        return cycles

    def calculate_farming_loss(self, loops: int, initial_amount: float) -> float:
        """Show that farming loses ATP due to 5% transfer fee per loop."""
        amount = initial_amount
        for _ in range(loops):
            amount, _ = self.apply_transfer_fee(amount)
        return amount - initial_amount  # Always negative


# ── §6 Dynamic Budget Optimization ──────────────────────────────────────────

@dataclass
class BudgetUsageRecord:
    """§6.1 — Historical performance tracking."""
    agent_lct_uri: str
    task_type: str
    allocated_budget: float
    consumed_budget: float
    success: bool
    value_delivered: float
    efficiency: float  # value / consumed
    timestamp: str


class DynamicBudgetOptimizer:
    """
    §6 — ML-based dynamic budget optimization.

    Learns from historical data to optimize budget allocation.
    Key insight: efficient agents get LOWER budgets (counter-intuitive
    but economically sound).
    """

    BASE_BUDGET = 100.0
    DEFAULT_TASK_MULTIPLIER = 1.0

    def __init__(self):
        self.history: List[BudgetUsageRecord] = []
        self.task_multipliers: Dict[str, float] = {}
        self.agent_stats: Dict[str, Dict[str, Any]] = {}

    def record_usage(self, record: BudgetUsageRecord):
        """Record budget usage for learning."""
        self.history.append(record)

        # Update agent stats
        agent = record.agent_lct_uri
        if agent not in self.agent_stats:
            self.agent_stats[agent] = {
                "total_tasks": 0,
                "successes": 0,
                "total_efficiency": 0.0,
                "total_utilization": 0.0,
            }

        stats = self.agent_stats[agent]
        stats["total_tasks"] += 1
        if record.success:
            stats["successes"] += 1
        stats["total_efficiency"] += record.efficiency
        utilization = record.consumed_budget / record.allocated_budget if record.allocated_budget > 0 else 0
        stats["total_utilization"] += utilization

    def get_agent_performance(self, agent: str) -> Dict[str, float]:
        """Get agent performance metrics."""
        stats = self.agent_stats.get(agent)
        if not stats or stats["total_tasks"] == 0:
            return {
                "success_rate": 0.5,
                "avg_efficiency": 1.0,
                "avg_utilization": 0.5,
            }

        n = stats["total_tasks"]
        return {
            "success_rate": stats["successes"] / n,
            "avg_efficiency": stats["total_efficiency"] / n,
            "avg_utilization": stats["total_utilization"] / n,
        }

    def calculate_optimal_budget(
        self,
        agent: str,
        task_type: str,
        reputation: float,
    ) -> float:
        """
        §6.2 — Predict optimal budget.

        optimal_budget = reputation_budget × performance_factor × task_factor
        """
        # Static baseline from reputation
        reputation_budget = self.BASE_BUDGET * (0.5 + reputation * 0.5)

        # Performance factor (learned)
        # Key insight from spec: efficient agents need LESS budget.
        # High efficiency (value/consumed) means agent accomplishes more per ATP,
        # so they need a lower allocation to deliver equivalent value.
        perf = self.get_agent_performance(agent)
        eff = max(perf["avg_efficiency"], 0.1)
        need_ratio = perf["avg_utilization"] * min(1.0 / eff, 2.0) / 2.0
        performance_factor = (
            0.3 * perf["success_rate"]
            + 0.7 * need_ratio
        )
        # Clamp to [0.5, 1.5]
        performance_factor = max(0.5, min(1.5, 0.5 + performance_factor))

        # Task factor (learned from data)
        task_factor = self.task_multipliers.get(task_type, self.DEFAULT_TASK_MULTIPLIER)

        return round(reputation_budget * performance_factor * task_factor, 2)

    def predict_exhaustion(
        self,
        current_consumed: float,
        total_budget: float,
        rate_per_hour: float,
        remaining_hours: float,
    ) -> Dict[str, Any]:
        """§6.3 — Predict budget exhaustion before it happens."""
        if total_budget <= 0:
            return {"risk": 1.0, "level": "critical", "hours_remaining": 0}

        remaining_budget = total_budget - current_consumed
        projected_consumption = rate_per_hour * remaining_hours
        exhaustion_risk = projected_consumption / remaining_budget if remaining_budget > 0 else float("inf")

        if exhaustion_risk < 0.8:
            level = "ok"
        elif exhaustion_risk < 1.0:
            level = "warning"
        else:
            level = "critical"

        hours_until_exhaustion = (
            remaining_budget / rate_per_hour if rate_per_hour > 0 else float("inf")
        )

        return {
            "risk": round(min(exhaustion_risk, 10.0), 3),
            "level": level,
            "hours_remaining": round(hours_until_exhaustion, 2),
            "projected_consumption": round(projected_consumption, 2),
            "remaining_budget": round(remaining_budget, 2),
        }

    def adjust_allocation(
        self,
        optimal_budget: float,
        exhaustion_level: str,
    ) -> float:
        """§6.4 — Adaptive allocation based on exhaustion risk."""
        if exhaustion_level == "critical":
            return round(optimal_budget * 1.2, 2)
        elif exhaustion_level == "warning":
            return round(optimal_budget * 1.1, 2)
        return round(optimal_budget, 2)

    def update_model(self, task_type: str, records: List[BudgetUsageRecord]):
        """§6.5 — Learn from new data to update task multipliers."""
        if not records:
            return

        efficiencies = [r.efficiency for r in records if r.consumed_budget > 0]
        if not efficiencies:
            return

        avg_efficiency = sum(efficiencies) / len(efficiencies)

        current = self.task_multipliers.get(task_type, self.DEFAULT_TASK_MULTIPLIER)

        # High efficiency → reduce task multiplier (needs less budget)
        if avg_efficiency > 1.0:
            self.task_multipliers[task_type] = round(current * 0.95, 4)
        # Low efficiency → increase task multiplier (needs more budget)
        elif avg_efficiency < 0.5:
            self.task_multipliers[task_type] = round(current * 1.05, 4)
        else:
            self.task_multipliers[task_type] = current


# ── Test Vectors from Spec ───────────────────────────────────────────────────

def run_test_vector_1():
    """Spec Test Vector 1: Hardware-Bound Identity Creation."""
    svc = HardwareIdentityService()
    identity = svc.create_identity(
        lct_uri="lct://agent:test@mainnet",
        hardware_type=HardwareType.TPM_2_0,
    )

    assert identity.lct_uri == "lct://agent:test@mainnet"
    assert identity.hardware_id == identity.attestation.tpm_public_key_hash
    assert len(identity.hardware_id) == 64  # SHA-256 hex
    assert len(identity.signature) == 64

    valid, reason = svc.verify_identity(identity)
    assert valid, reason

    return identity


def run_test_vector_2():
    """Spec Test Vector 2: Delegation Chain Creation."""
    hw_svc = HardwareIdentityService()
    chain_svc = DelegationChainService(hw_svc)

    # Create agent identity
    hw_svc.create_identity("lct://agent:bob@mainnet")

    scope = DelegationScope(
        allowed_operations=["query", "compute"],
        resource_limits=ResourceLimits(max_total_atp=100.0),
    )

    token = chain_svc.create_delegation(
        issuer="lct://user:alice@mainnet",  # human root
        delegate="lct://agent:bob@mainnet",
        scope=scope,
        duration_hours=24,
    )

    assert token.issuer == "lct://user:alice@mainnet"
    assert token.delegate == "lct://agent:bob@mainnet"
    assert not token.is_expired()

    valid, reason, chain = chain_svc.verify_chain(token)
    assert valid, reason

    return token


def run_test_vector_3():
    """Spec Test Vector 3: Cross-Network Delegation."""
    cn_svc = CrossNetworkService()

    mainnet = Network(name="mainnet", base_exchange_rate=1.0, trust_level=1.0)
    testnet = Network(name="testnet", base_exchange_rate=0.1, trust_level=0.8)
    cn_svc.register_network(mainnet)
    cn_svc.register_network(testnet)

    # Exchange rate = (0.1 / 1.0) × 0.8 = 0.08
    rate = cn_svc.get_exchange_rate(mainnet, testnet)
    assert abs(rate - 0.08) < 0.001

    # Create a dummy budgeted token
    deleg = DelegationToken(
        token_id="test_cn", issuer="lct://user:alice@mainnet",
        delegate="lct://agent:bob@testnet",
        scope=DelegationScope(allowed_operations=["query"]),
        issued_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        signature="test",
    )
    bt = BudgetedDelegationToken(delegation=deleg, atp_budget=100.0)

    cn_token = cn_svc.create_cross_network_delegation(
        budgeted_token=bt,
        source_network=mainnet,
        target_network=testnet,
        source_atp_budget=100.0,
    )

    # Bridge fee = 1% of 100 = 1.0
    # Target = (100 - 1) × 0.08 = 7.92
    assert abs(cn_token.exchange_rate - 0.08) < 0.001
    assert abs(cn_token.target_atp_budget - 7.92) < 0.01
    assert cn_token.source_atp_budget == 100.0
    assert not cn_token.bridge_finalized

    # Finalize bridge
    cn_svc.confirm_bridge(cn_token.bridge_tx_hash, 12)
    assert cn_token.bridge_finalized

    return cn_token


# ═══════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE TESTS
# ═══════════════════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(desc: str, condition: bool):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {desc}")

    # ── T1: Hardware-Bound Identity – Creation ───────────────────────────
    print("T1: Hardware-Bound Identity – Creation")
    svc = HardwareIdentityService()

    id1 = svc.create_identity("lct://agent:alpha@mainnet")
    check("T1.1 Identity created with correct URI", id1.lct_uri == "lct://agent:alpha@mainnet")
    check("T1.2 Hardware ID is SHA-256 hex (64 chars)", len(id1.hardware_id) == 64)
    check("T1.3 Signature is SHA-256 hex", len(id1.signature) == 64)
    check("T1.4 Attestation hash matches hardware_id", id1.hardware_id == id1.attestation.tpm_public_key_hash)
    check("T1.5 Not revoked at creation", not id1.revoked)
    check("T1.6 Hardware type is TPM_2_0", id1.hardware_type == HardwareType.TPM_2_0)
    check("T1.7 Created_at is ISO 8601", "T" in id1.created_at)
    check("T1.8 Hardware mapped to identity", svc.hardware_to_identity[id1.hardware_id] == id1.lct_uri)

    # T1.9 Duplicate creation fails
    try:
        svc.create_identity("lct://agent:alpha@mainnet")
        check("T1.9 Duplicate creation raises", False)
    except ValueError:
        check("T1.9 Duplicate creation raises", True)

    # T1.10 Different hardware types
    id_se = svc.create_identity("lct://agent:beta@mainnet", HardwareType.SECURE_ENCLAVE)
    check("T1.10 SecureEnclave type accepted", id_se.hardware_type == HardwareType.SECURE_ENCLAVE)

    # ── T2: Hardware-Bound Identity – Verification ───────────────────────
    print("T2: Hardware-Bound Identity – Verification")
    valid, reason = svc.verify_identity(id1)
    check("T2.1 Valid identity passes verification", valid)
    check("T2.2 Reason is 'Valid'", reason == "Valid")

    # Tamper with attestation
    tampered = copy.deepcopy(id1)
    tampered.attestation.tpm_public_key_hash = "bad_hash"
    valid, reason = svc.verify_identity(tampered)
    check("T2.3 Tampered attestation hash fails", not valid)
    check("T2.4 Reason mentions mismatch", "mismatch" in reason.lower())

    tampered2 = copy.deepcopy(id1)
    tampered2.attestation.tpm_attestation_signature = "bad_sig"
    valid, reason = svc.verify_identity(tampered2)
    check("T2.5 Tampered attestation sig fails", not valid)

    # Expired identity
    id_exp = svc.create_identity("lct://agent:expiring@mainnet", expires_hours=0)
    id_exp.expires_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    valid, reason = svc.verify_identity(id_exp)
    check("T2.6 Expired identity fails", not valid)
    check("T2.7 Reason mentions expired", "expired" in reason.lower())

    # ── T3: Hardware-Bound Identity – Migration ──────────────────────────
    print("T3: Hardware-Bound Identity – Migration")
    old_hw_id = id1.hardware_id
    migrated = svc.migrate_identity("lct://agent:alpha@mainnet", HardwareType.TRUSTZONE)
    check("T3.1 Hardware ID changed after migration", migrated.hardware_id != old_hw_id)
    check("T3.2 Hardware type updated", migrated.hardware_type == HardwareType.TRUSTZONE)
    check("T3.3 Migration history has 1 entry", len(migrated.migration_history) == 1)
    check("T3.4 Migration records old hardware ID", migrated.migration_history[0]["old_hardware_id"] == old_hw_id)
    check("T3.5 Old hardware key revoked", svc.is_revoked(f"lct://agent:alpha@mainnet:hw:{old_hw_id}"))
    check("T3.6 New identity still valid", svc.verify_identity(migrated)[0])

    # ── T4: Hardware-Bound Identity – Revocation ─────────────────────────
    print("T4: Hardware-Bound Identity – Revocation")
    id_rev = svc.create_identity("lct://agent:revocable@mainnet")
    rev = svc.revoke_identity("lct://agent:revocable@mainnet", "compromised")
    check("T4.1 Revocation reason is compromised", rev.reason == "compromised")
    check("T4.2 Identity marked revoked", svc.identities["lct://agent:revocable@mainnet"].revoked)
    check("T4.3 Identity on revocation list", svc.is_revoked("lct://agent:revocable@mainnet"))

    valid, reason = svc.verify_identity(id_rev)
    check("T4.4 Revoked identity fails verification", not valid)
    check("T4.5 Reason mentions revoked", "revoked" in reason.lower())

    # Invalid reason
    try:
        svc.revoke_identity("lct://agent:beta@mainnet", "invalid_reason")
        check("T4.6 Invalid reason raises", False)
    except ValueError:
        check("T4.6 Invalid reason raises", True)

    # ── T5: Delegation Chain – Basic Creation ────────────────────────────
    print("T5: Delegation Chain – Basic Creation")
    hw_svc = HardwareIdentityService()
    chain_svc = DelegationChainService(hw_svc)
    hw_svc.create_identity("lct://agent:sage1@mainnet")

    scope = DelegationScope(
        allowed_operations=["query", "compute", "delegate"],
        resource_limits=ResourceLimits(max_total_atp=500.0),
        network_restrictions=["mainnet"],
    )

    t1 = chain_svc.create_delegation(
        issuer="lct://user:alice@mainnet",
        delegate="lct://agent:sage1@mainnet",
        scope=scope,
        duration_hours=24,
    )
    check("T5.1 Token created with correct issuer", t1.issuer == "lct://user:alice@mainnet")
    check("T5.2 Token has delegate", t1.delegate == "lct://agent:sage1@mainnet")
    check("T5.3 Token not expired", not t1.is_expired())
    check("T5.4 Token has signature", len(t1.signature) == 64)
    check("T5.5 No parent token (root delegation)", t1.parent_token_id is None)
    check("T5.6 Token stored in service", t1.token_id in chain_svc.tokens)

    # ── T6: Delegation Chain – Verification ──────────────────────────────
    print("T6: Delegation Chain – Verification")
    valid, reason, path = chain_svc.verify_chain(t1)
    check("T6.1 Direct human delegation is valid", valid)
    check("T6.2 Chain path includes human root", "lct://user:alice@mainnet" in path)
    check("T6.3 Reason mentions valid", "valid" in reason.lower())

    # ── T7: Delegation Chain – Hierarchical Sub-delegation ───────────────
    print("T7: Delegation Chain – Hierarchical Sub-delegation")
    hw_svc.create_identity("lct://plugin:irp1@mainnet")

    sub_scope = DelegationScope(
        allowed_operations=["query", "compute"],  # narrower
        resource_limits=ResourceLimits(max_total_atp=100.0),
        network_restrictions=["mainnet"],
    )

    t2 = chain_svc.create_delegation(
        issuer="lct://agent:sage1@mainnet",
        delegate="lct://plugin:irp1@mainnet",
        scope=sub_scope,
        duration_hours=12,
        parent_token_id=t1.token_id,
    )
    check("T7.1 Sub-delegation created", t2.token_id in chain_svc.tokens)
    check("T7.2 Parent token set", t2.parent_token_id == t1.token_id)
    check("T7.3 Scope is narrower", set(t2.scope.allowed_operations).issubset(set(t1.scope.allowed_operations)))

    valid, reason, path = chain_svc.verify_chain(t2)
    check("T7.4 Sub-delegation chain is valid", valid)
    check("T7.5 Chain depth is 1", chain_svc.get_chain_depth(t2) == 1)

    # Attempt to widen scope (should fail)
    wide_scope = DelegationScope(
        allowed_operations=["query", "compute", "delete"],  # 'delete' not in parent
        resource_limits=ResourceLimits(max_total_atp=100.0),
    )
    try:
        chain_svc.create_delegation(
            issuer="lct://agent:sage1@mainnet",
            delegate="lct://plugin:irp1@mainnet",
            scope=wide_scope,
            parent_token_id=t1.token_id,
        )
        check("T7.6 Widened scope rejected", False)
    except ValueError:
        check("T7.6 Widened scope rejected", True)

    # ── T8: Delegation Chain – No Sub-delegation Permission ──────────────
    print("T8: Delegation Chain – No Sub-delegation Permission")
    hw_svc.create_identity("lct://function:query1@mainnet")

    # t2 doesn't have 'delegate' in its scope
    no_deleg_scope = DelegationScope(
        allowed_operations=["query"],
        resource_limits=ResourceLimits(max_total_atp=50.0),
        network_restrictions=["mainnet"],
    )
    try:
        chain_svc.create_delegation(
            issuer="lct://plugin:irp1@mainnet",
            delegate="lct://function:query1@mainnet",
            scope=no_deleg_scope,
            parent_token_id=t2.token_id,
        )
        check("T8.1 Sub-delegation without permission rejected", False)
    except ValueError as e:
        check("T8.1 Sub-delegation without permission rejected", "delegation" in str(e).lower() or "delegate" in str(e).lower())

    # ── T9: Delegation Chain – Revocation Cascade ────────────────────────
    print("T9: Delegation Chain – Revocation Cascade")
    hw_svc.create_identity("lct://agent:s2@mainnet")
    hw_svc.create_identity("lct://plugin:p2@mainnet")
    hw_svc.create_identity("lct://function:f2@mainnet")

    scope_full = DelegationScope(
        allowed_operations=["query", "compute", "delegate"],
        resource_limits=ResourceLimits(max_total_atp=500.0),
        network_restrictions=["mainnet"],
    )
    scope_mid = DelegationScope(
        allowed_operations=["query", "delegate"],
        resource_limits=ResourceLimits(max_total_atp=200.0),
        network_restrictions=["mainnet"],
    )
    scope_leaf = DelegationScope(
        allowed_operations=["query"],
        resource_limits=ResourceLimits(max_total_atp=50.0),
        network_restrictions=["mainnet"],
    )

    tk_root = chain_svc.create_delegation("lct://user:bob@mainnet", "lct://agent:s2@mainnet", scope_full, 24)
    tk_mid = chain_svc.create_delegation("lct://agent:s2@mainnet", "lct://plugin:p2@mainnet", scope_mid, 12, tk_root.token_id)
    tk_leaf = chain_svc.create_delegation("lct://plugin:p2@mainnet", "lct://function:f2@mainnet", scope_leaf, 6, tk_mid.token_id)

    # Revoke middle → cascade to leaf
    chain_svc.revoke_token(tk_mid.token_id)
    check("T9.1 Middle token revoked", tk_mid.token_id in chain_svc.revoked_tokens)
    check("T9.2 Leaf token cascade-revoked", tk_leaf.token_id in chain_svc.revoked_tokens)
    check("T9.3 Root token not affected", tk_root.token_id not in chain_svc.revoked_tokens)

    valid, reason, _ = chain_svc.verify_chain(tk_leaf)
    check("T9.4 Revoked chain fails verification", not valid)

    # ── T10: ATP Budget – Lock-Commit-Rollback ───────────────────────────
    print("T10: ATP Budget – Lock-Commit-Rollback")
    budget_svc = ATPBudgetService()

    deleg = DelegationToken(
        token_id="bt_001", issuer="lct://user:alice@mainnet",
        delegate="lct://agent:sage@mainnet",
        scope=DelegationScope(allowed_operations=["query"]),
        issued_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        signature="test",
    )
    bt = budget_svc.create_budgeted_token(deleg, atp_budget=100.0)

    check("T10.1 Initial budget is 100 ATP", bt.atp_budget == 100.0)
    check("T10.2 Nothing consumed yet", bt.atp_consumed == 0.0)
    check("T10.3 Nothing locked yet", bt.atp_locked == 0.0)
    check("T10.4 Available is 100", bt.atp_available == 100.0)

    # Lock
    tx_id, err = budget_svc.lock_transaction("bt_001", 30.0)
    check("T10.5 Lock succeeds", tx_id is not None and err is None)
    check("T10.6 30 ATP locked", bt.atp_locked == 30.0)
    check("T10.7 70 ATP available", bt.atp_available == 70.0)

    # Commit
    ok = budget_svc.commit_transaction(tx_id)
    check("T10.8 Commit succeeds", ok)
    check("T10.9 30 ATP consumed", bt.atp_consumed == 30.0)
    check("T10.10 Lock released", bt.atp_locked == 0.0)
    check("T10.11 70 ATP available after commit", bt.atp_available == 70.0)

    # Lock + Rollback
    tx_id2, _ = budget_svc.lock_transaction("bt_001", 20.0)
    check("T10.12 Second lock succeeds", tx_id2 is not None)
    ok = budget_svc.rollback_transaction(tx_id2)
    check("T10.13 Rollback succeeds", ok)
    check("T10.14 ATP unlocked after rollback", bt.atp_locked == 0.0)
    check("T10.15 Consumed unchanged after rollback", bt.atp_consumed == 30.0)

    # ── T11: ATP Budget – Insufficient Funds ─────────────────────────────
    print("T11: ATP Budget – Insufficient Funds")
    tx_id3, err3 = budget_svc.lock_transaction("bt_001", 80.0)
    check("T11.1 Over-budget lock fails", tx_id3 is None)
    check("T11.2 Error mentions insufficient", "insufficient" in err3.lower())

    tx_id4, err4 = budget_svc.lock_transaction("nonexistent", 10.0)
    check("T11.3 Nonexistent budget fails", tx_id4 is None)
    check("T11.4 Error mentions not found", "not found" in err4.lower())

    # ── T12: ATP Budget – Alerts ─────────────────────────────────────────
    print("T12: ATP Budget – Alerts")
    deleg2 = DelegationToken(
        token_id="bt_alert", issuer="x", delegate="y",
        scope=DelegationScope(allowed_operations=[]),
        issued_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        signature="test",
    )
    bt2 = budget_svc.create_budgeted_token(deleg2, atp_budget=100.0)

    # Consume 79% → no alert
    tx, _ = budget_svc.lock_transaction("bt_alert", 79.0)
    budget_svc.commit_transaction(tx)
    check("T12.1 No alert at 79%", bt2.get_alert_level() == BudgetAlertLevel.OK)

    # Consume 1 more → 80% → WARNING
    tx, _ = budget_svc.lock_transaction("bt_alert", 1.0)
    budget_svc.commit_transaction(tx)
    check("T12.2 WARNING_80 at 80%", bt2.get_alert_level() == BudgetAlertLevel.WARNING_80)

    # Consume 10 more → 90% → CRITICAL
    tx, _ = budget_svc.lock_transaction("bt_alert", 10.0)
    budget_svc.commit_transaction(tx)
    check("T12.3 CRITICAL_90 at 90%", bt2.get_alert_level() == BudgetAlertLevel.CRITICAL_90)

    # Consume remaining → 100% → EXHAUSTED
    tx, _ = budget_svc.lock_transaction("bt_alert", 10.0)
    budget_svc.commit_transaction(tx)
    check("T12.4 EXHAUSTED_100 at 100%", bt2.get_alert_level() == BudgetAlertLevel.EXHAUSTED_100)

    # Further lock should fail
    tx_ex, err_ex = budget_svc.lock_transaction("bt_alert", 1.0)
    check("T12.5 Lock fails on exhausted budget", tx_ex is None)

    # ── T13: ATP Budget – Hierarchical Budgets ───────────────────────────
    print("T13: ATP Budget – Hierarchical Budgets")
    parent_deleg = DelegationToken(
        token_id="bt_parent", issuer="root", delegate="sage",
        scope=DelegationScope(allowed_operations=[]),
        issued_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        signature="test",
    )
    parent_bt = budget_svc.create_budgeted_token(parent_deleg, atp_budget=200.0)

    budget_svc.allocate_child_budget("bt_parent", "bt_child1", 80.0)
    check("T13.1 Parent available reduced by child allocation", parent_bt.atp_available == 120.0)
    check("T13.2 Child budget created", "bt_child1" in budget_svc.budgets)
    check("T13.3 Child has 80 ATP budget", budget_svc.budgets["bt_child1"].atp_budget == 80.0)

    tx_c, _ = budget_svc.lock_transaction("bt_child1", 30.0)
    budget_svc.commit_transaction(tx_c)
    check("T13.4 Child consumed 30", budget_svc.budgets["bt_child1"].atp_consumed == 30.0)
    check("T13.5 Parent available unchanged by child spend", parent_bt.atp_available == 120.0)

    try:
        budget_svc.allocate_child_budget("bt_parent", "bt_child2", 200.0)
        check("T13.6 Over-allocation fails", False)
    except ValueError:
        check("T13.6 Over-allocation fails", True)

    # ── T14: Cross-Network – Exchange Rates ──────────────────────────────
    print("T14: Cross-Network – Exchange Rates")
    cn_svc = CrossNetworkService()

    mainnet = Network(name="mainnet", base_exchange_rate=1.0, trust_level=1.0)
    testnet = Network(name="testnet", base_exchange_rate=0.1, trust_level=0.8)
    sidechain = Network(name="sidechain", base_exchange_rate=0.5, trust_level=0.6)

    cn_svc.register_network(mainnet)
    cn_svc.register_network(testnet)
    cn_svc.register_network(sidechain)

    rate_mt = cn_svc.get_exchange_rate(mainnet, testnet)
    check("T14.1 Mainnet→Testnet rate = 0.08", abs(rate_mt - 0.08) < 0.001)

    rate_ms = cn_svc.get_exchange_rate(mainnet, sidechain)
    check("T14.2 Mainnet→Sidechain rate = 0.30", abs(rate_ms - 0.30) < 0.001)

    rate_tm = cn_svc.get_exchange_rate(testnet, mainnet)
    check("T14.3 Testnet→Mainnet rate = 10.0", abs(rate_tm - 10.0) < 0.01)

    rate_self = cn_svc.get_exchange_rate(mainnet, mainnet)
    check("T14.4 Self-exchange rate = 1.0", abs(rate_self - 1.0) < 0.001)

    # ── T15: Cross-Network – Bridge Transfer ─────────────────────────────
    print("T15: Cross-Network – Bridge Transfer")
    deleg_cn = DelegationToken(
        token_id="cn_001", issuer="lct://user:alice@mainnet",
        delegate="lct://agent:bob@testnet",
        scope=DelegationScope(allowed_operations=["query"]),
        issued_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        signature="test",
    )
    bt_cn = BudgetedDelegationToken(delegation=deleg_cn, atp_budget=100.0)

    cn_token = cn_svc.create_cross_network_delegation(bt_cn, mainnet, testnet, 100.0)
    check("T15.1 Target ATP = 7.92", abs(cn_token.target_atp_budget - 7.92) < 0.01)
    check("T15.2 Exchange rate = 0.08", abs(cn_token.exchange_rate - 0.08) < 0.001)
    check("T15.3 Not finalized before confirmations", not cn_token.bridge_finalized)

    cn_svc.confirm_bridge(cn_token.bridge_tx_hash, 6)
    check("T15.4 6 confirmations not enough", not cn_token.bridge_finalized)

    cn_svc.confirm_bridge(cn_token.bridge_tx_hash, 12)
    check("T15.5 12 confirmations finalizes", cn_token.bridge_finalized)

    # ── T16: Cross-Network – Reverse Bridge ──────────────────────────────
    print("T16: Cross-Network – Reverse Bridge")
    returned = cn_svc.reverse_bridge(cn_token.bridge_tx_hash, 5.0)
    check("T16.1 Reverse bridge returns positive amount", returned > 0)
    check("T16.2 Return includes fee deduction", returned < 5.0 / cn_token.exchange_rate)

    cn_token2 = cn_svc.create_cross_network_delegation(bt_cn, mainnet, sidechain, 50.0)
    returned_unfinalized = cn_svc.reverse_bridge(cn_token2.bridge_tx_hash, 10.0)
    check("T16.3 Unfinalized bridge returns 0", returned_unfinalized == 0.0)

    # ── T17: Cross-Network – Reputation Aggregation ──────────────────────
    print("T17: Cross-Network – Reputation Aggregation")
    cn_svc.set_reputation("agent:alpha", "mainnet", 0.9)
    cn_svc.set_reputation("agent:alpha", "testnet", 0.7)
    cn_svc.set_reputation("agent:alpha", "sidechain", 0.5)

    agg = cn_svc.aggregate_reputation("agent:alpha")
    check("T17.1 Aggregated reputation ≈ 0.733", abs(agg - 0.7333) < 0.01)

    agg_single = cn_svc.aggregate_reputation("agent:alpha", ["mainnet"])
    check("T17.2 Single-network reputation = 0.9", abs(agg_single - 0.9) < 0.001)

    agg_unknown = cn_svc.aggregate_reputation("unknown:agent")
    check("T17.3 Unknown agent gets default 0.5", agg_unknown == 0.5)

    # ── T18: Security – Rate Limiting ────────────────────────────────────
    print("T18: Security – Rate Limiting")
    sec_svc = SecurityMitigationService()

    ok1, _ = sec_svc.check_rate_limit("agent:test")
    ok2, _ = sec_svc.check_rate_limit("agent:test")
    check("T18.1 First 2 queries within rate limit", ok1 and ok2)

    ok3, err3 = sec_svc.check_rate_limit("agent:test")
    check("T18.2 Third query hits rate limit", not ok3)
    check("T18.3 Rate limit error message", "rate limit" in err3.lower())

    ok_other, _ = sec_svc.check_rate_limit("agent:other")
    check("T18.4 Different identity not rate-limited", ok_other)

    # ── T19: Security – Cost Cap ─────────────────────────────────────────
    print("T19: Security – Cost Cap")
    ok_low, _ = sec_svc.check_cost_cap(5.0)
    check("T19.1 5 ATP under cap", ok_low)

    ok_high, err_high = sec_svc.check_cost_cap(10.0)
    check("T19.2 10 ATP over cap (max 8)", not ok_high)
    check("T19.3 Error mentions cap", "cap" in err_high.lower())

    ok_exact, _ = sec_svc.check_cost_cap(8.0)
    check("T19.4 Exactly 8 ATP is OK", ok_exact)

    # ── T20: Security – Anomaly Detection ────────────────────────────────
    print("T20: Security – Anomaly Detection")
    history = [10.0, 12.0, 11.0, 10.5, 11.5, 10.0, 12.0]

    is_anom, z = sec_svc.detect_anomaly("agent:x", "query", 11.0, history)
    check("T20.1 Normal value not anomalous", not is_anom)

    is_anom2, z2 = sec_svc.detect_anomaly("agent:x", "query", 50.0, history)
    check("T20.2 Extreme value is anomalous", is_anom2)
    check("T20.3 Z-score > 3 for anomaly", z2 > 3.0)

    is_anom3, z3 = sec_svc.detect_anomaly("agent:x", "query", 10.0, None)
    check("T20.4 No history → not anomalous", not is_anom3)

    # ── T21: Security – Sybil Prevention ─────────────────────────────────
    print("T21: Security – Sybil Prevention")
    ok_rich, _ = sec_svc.check_identity_creation_cost(100.0)
    check("T21.1 100 ATP enough for identity creation", ok_rich)

    ok_poor, err_poor = sec_svc.check_identity_creation_cost(10.0)
    check("T21.2 10 ATP not enough", not ok_poor)
    check("T21.3 Error mentions insufficient", "insufficient" in err_poor.lower())

    ok_vel, _ = sec_svc.check_reputation_velocity("new:agent", 0.05)
    check("T21.4 0.05 rep/hr within limit", ok_vel)

    ok_vel2, err_vel2 = sec_svc.check_reputation_velocity("new:agent", 0.06)
    check("T21.5 0.11 total rep/hr exceeds limit", not ok_vel2)

    # ── T22: Security – Social Graph Analysis ────────────────────────────
    print("T22: Security – Social Graph Analysis")
    connections = {
        "a": {"b", "c"},
        "b": {"a", "c", "d"},
        "c": {"a", "b"},
        "d": {"b"},
        "x": {"y"},
        "y": {"x"},
    }

    clusters = sec_svc.analyze_social_graph(connections)
    check("T22.1 Two clusters detected", len(clusters) == 2)

    main_cluster = max(clusters, key=len)
    small_cluster = min(clusters, key=len)
    check("T22.2 Main cluster has 4 nodes", len(main_cluster) == 4)
    check("T22.3 Small cluster has 2 nodes (suspicious)", len(small_cluster) == 2)

    sybil_events = [e for e in sec_svc.events if e.event_type == "sybil_attempt"]
    check("T22.4 Sybil event generated for small cluster", len(sybil_events) > 0)

    # ── T23: Security – Delegation Forgery ───────────────────────────────
    print("T23: Security – Delegation Forgery")
    hw_svc2 = HardwareIdentityService()
    chain_svc2 = DelegationChainService(hw_svc2)
    hw_svc2.create_identity("lct://agent:legit@mainnet")

    legit_token = chain_svc2.create_delegation(
        "lct://user:alice@mainnet", "lct://agent:legit@mainnet",
        DelegationScope(allowed_operations=["query"]),
    )

    ok_legit, _ = sec_svc.verify_delegation_signature(legit_token, "alice_key")
    check("T23.1 Legitimate signature verifies", ok_legit)

    forged = copy.deepcopy(legit_token)
    forged.signature = "forged_signature_data"
    ok_forged, err_forged = sec_svc.verify_delegation_signature(forged, "alice_key")
    check("T23.2 Forged signature rejected", not ok_forged)
    check("T23.3 Error mentions signature", "signature" in err_forged.lower())

    forgery_events = [e for e in sec_svc.events if e.event_type == "forgery_attempt"]
    check("T23.4 Forgery event recorded", len(forgery_events) > 0)

    # ── T24: Security – ATP Farming Prevention ───────────────────────────
    print("T24: Security – ATP Farming Prevention")
    sec_svc2 = SecurityMitigationService()

    balances = {"alice": 100.0, "bob": 200.0, "charlie": 300.0}
    sec_svc2.register_atp_supply(600.0)
    ok_cons, drift = sec_svc2.check_conservation(balances)
    check("T24.1 Conservation holds with correct total", ok_cons)

    balances_bad = {"alice": 100.0, "bob": 200.0, "charlie": 310.0}
    ok_bad, drift_bad = sec_svc2.check_conservation(balances_bad)
    check("T24.2 Conservation violation detected", not ok_bad)
    check("T24.3 Drift = 10.0", abs(drift_bad - 10.0) < 0.01)

    net, fee = sec_svc2.apply_transfer_fee(100.0)
    check("T24.4 Transfer fee = 5%", fee == 5.0)
    check("T24.5 Net amount = 95", net == 95.0)

    loss = sec_svc2.calculate_farming_loss(50, 100.0)
    check("T24.6 Farming always loses ATP", loss < 0)
    check("T24.7 50-loop loss > -90 ATP", loss < -90.0)

    sec_svc2.record_transfer("a", "b", 100)
    sec_svc2.record_transfer("b", "c", 95)
    sec_svc2.record_transfer("c", "a", 90)
    cycles = sec_svc2.detect_circular_flows("a")
    check("T24.8 Circular flow detected", len(cycles) > 0)
    check("T24.9 Cycle contains a→b→c→a", any(len(c) >= 3 for c in cycles))

    # ── T25: Dynamic Optimization – Performance Tracking ─────────────────
    print("T25: Dynamic Optimization – Performance Tracking")
    opt = DynamicBudgetOptimizer()

    for i in range(5):
        opt.record_usage(BudgetUsageRecord(
            agent_lct_uri="agent:efficient",
            task_type="query",
            allocated_budget=100.0,
            consumed_budget=60.0,
            success=True,
            value_delivered=90.0,
            efficiency=90.0 / 60.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))

    perf = opt.get_agent_performance("agent:efficient")
    check("T25.1 Success rate = 1.0", perf["success_rate"] == 1.0)
    check("T25.2 Avg efficiency = 1.5", abs(perf["avg_efficiency"] - 1.5) < 0.01)
    check("T25.3 Avg utilization = 0.6", abs(perf["avg_utilization"] - 0.6) < 0.01)

    perf_new = opt.get_agent_performance("agent:unknown")
    check("T25.4 Unknown agent gets defaults", perf_new["success_rate"] == 0.5)

    # ── T26: Dynamic Optimization – Budget Calculation ───────────────────
    print("T26: Dynamic Optimization – Budget Calculation")
    budget_high_rep = opt.calculate_optimal_budget("agent:efficient", "query", 0.9)
    budget_low_rep = opt.calculate_optimal_budget("agent:new", "query", 0.3)

    check("T26.1 High-rep agent gets higher budget", budget_high_rep > budget_low_rep)
    check("T26.2 Low-rep base ≈ 65 (adjusted by perf)", budget_low_rep > 30)
    check("T26.3 High-rep budget reasonable range", 50 < budget_high_rep < 200)

    # ── T27: Dynamic Optimization – Exhaustion Prediction ────────────────
    print("T27: Dynamic Optimization – Exhaustion Prediction")
    pred_ok = opt.predict_exhaustion(
        current_consumed=30.0, total_budget=100.0,
        rate_per_hour=5.0, remaining_hours=10.0,
    )
    check("T27.1 Low exhaustion risk = ok", pred_ok["level"] == "ok")
    check("T27.2 Risk < 0.8", pred_ok["risk"] < 0.8)

    pred_warn = opt.predict_exhaustion(
        current_consumed=60.0, total_budget=100.0,
        rate_per_hour=10.0, remaining_hours=3.5,
    )
    check("T27.3 Medium exhaustion risk = warning", pred_warn["level"] == "warning")

    pred_crit = opt.predict_exhaustion(
        current_consumed=80.0, total_budget=100.0,
        rate_per_hour=10.0, remaining_hours=5.0,
    )
    check("T27.4 High exhaustion risk = critical", pred_crit["level"] == "critical")

    # ── T28: Dynamic Optimization – Adaptive Allocation ──────────────────
    print("T28: Dynamic Optimization – Adaptive Allocation")
    base = 100.0
    adj_ok = opt.adjust_allocation(base, "ok")
    adj_warn = opt.adjust_allocation(base, "warning")
    adj_crit = opt.adjust_allocation(base, "critical")

    check("T28.1 OK level: no adjustment", adj_ok == 100.0)
    check("T28.2 Warning: +10%", adj_warn == 110.0)
    check("T28.3 Critical: +20%", adj_crit == 120.0)

    # ── T29: Dynamic Optimization – Model Update ─────────────────────────
    print("T29: Dynamic Optimization – Model Update")
    high_eff_records = [
        BudgetUsageRecord("agent:x", "analysis", 100.0, 50.0, True, 100.0, 2.0,
                          datetime.now(timezone.utc).isoformat())
        for _ in range(3)
    ]
    opt.update_model("analysis", high_eff_records)
    check("T29.1 High efficiency reduces task multiplier", opt.task_multipliers.get("analysis", 1.0) < 1.0)

    low_eff_records = [
        BudgetUsageRecord("agent:y", "rendering", 100.0, 100.0, True, 30.0, 0.3,
                          datetime.now(timezone.utc).isoformat())
        for _ in range(3)
    ]
    opt.update_model("rendering", low_eff_records)
    check("T29.2 Low efficiency increases task multiplier", opt.task_multipliers.get("rendering", 1.0) > 1.0)

    old_val = opt.task_multipliers.get("stable", 1.0)
    med_records = [
        BudgetUsageRecord("agent:z", "stable", 100.0, 80.0, True, 60.0, 0.75,
                          datetime.now(timezone.utc).isoformat())
        for _ in range(3)
    ]
    opt.update_model("stable", med_records)
    check("T29.3 Medium efficiency no change", opt.task_multipliers.get("stable", 1.0) == old_val)

    # ── T30: Spec Test Vectors ───────────────────────────────────────────
    print("T30: Spec Test Vectors")
    tv1 = run_test_vector_1()
    check("T30.1 Test Vector 1 (identity) passes", tv1 is not None)

    tv2 = run_test_vector_2()
    check("T30.2 Test Vector 2 (delegation) passes", tv2 is not None)

    tv3 = run_test_vector_3()
    check("T30.3 Test Vector 3 (cross-network) passes", tv3 is not None)

    # ── T31: Integration – Full Delegation Flow (Appendix A) ─────────────
    print("T31: Integration – Full Delegation Flow")
    hw = HardwareIdentityService()
    chains = DelegationChainService(hw)
    budgets = ATPBudgetService()

    human_id = hw.create_identity("lct://user:alice@mainnet")
    check("T31.1 Human identity created", human_id.lct_uri == "lct://user:alice@mainnet")

    hw.create_identity("lct://sage:instance1@mainnet")
    hw.create_identity("lct://plugin:emotional_irp@mainnet")

    sage_scope = DelegationScope(
        allowed_operations=["query", "compute", "delegate"],
        resource_limits=ResourceLimits(max_total_atp=500.0),
    )
    sage_token = chains.create_delegation(
        issuer="lct://user:alice@mainnet",
        delegate="lct://sage:instance1@mainnet",
        scope=sage_scope,
        duration_hours=24,
    )
    sage_bt = budgets.create_budgeted_token(sage_token, 500.0)
    check("T31.2 SAGE delegation created with 500 ATP", sage_bt.atp_budget == 500.0)

    irp_scope = DelegationScope(
        allowed_operations=["query", "compute"],
        resource_limits=ResourceLimits(max_total_atp=100.0),
    )
    irp_token = chains.create_delegation(
        issuer="lct://sage:instance1@mainnet",
        delegate="lct://plugin:emotional_irp@mainnet",
        scope=irp_scope,
        duration_hours=12,
        parent_token_id=sage_token.token_id,
    )
    budgets.allocate_child_budget(sage_token.token_id, irp_token.token_id, 100.0)
    check("T31.3 IRP delegation with 100 ATP sub-budget", budgets.budgets[irp_token.token_id].atp_budget == 100.0)

    tx_id, err = budgets.lock_transaction(irp_token.token_id, 30.0)
    check("T31.4 IRP locks 30 ATP", tx_id is not None)
    budgets.commit_transaction(tx_id)
    check("T31.5 IRP commits 30 ATP", budgets.budgets[irp_token.token_id].atp_consumed == 30.0)

    valid, reason, path = chains.verify_chain(irp_token)
    check("T31.6 Full chain valid: Alice → SAGE → IRP", valid)
    check("T31.7 Chain terminates at human root", "lct://user:alice@mainnet" in path)

    # ── T32: Edge Cases ──────────────────────────────────────────────────
    print("T32: Edge Cases")

    try:
        budgets.create_budgeted_token(
            DelegationToken("zero", "a", "b", DelegationScope([]),
                            datetime.now(timezone.utc).isoformat(),
                            datetime.now(timezone.utc).isoformat(), "s"),
            atp_budget=0.0
        )
        check("T32.1 Zero budget creation rejected", False)
    except ValueError:
        check("T32.1 Zero budget creation rejected", True)

    try:
        budgets.create_budgeted_token(
            DelegationToken("neg", "a", "b", DelegationScope([]),
                            datetime.now(timezone.utc).isoformat(),
                            datetime.now(timezone.utc).isoformat(), "s"),
            atp_budget=-50.0
        )
        check("T32.2 Negative budget creation rejected", False)
    except ValueError:
        check("T32.2 Negative budget creation rejected", True)

    parent_s = DelegationScope(
        allowed_operations=["query", "compute"],
        resource_limits=ResourceLimits(max_total_atp=100.0),
    )
    child_s = DelegationScope(
        allowed_operations=["query"],
        resource_limits=ResourceLimits(max_total_atp=50.0),
    )
    check("T32.3 Narrower scope is subset", child_s.is_subset_of(parent_s))

    wider = DelegationScope(
        allowed_operations=["query", "delete"],
        resource_limits=ResourceLimits(max_total_atp=50.0),
    )
    check("T32.4 Wider operations not subset", not wider.is_subset_of(parent_s))

    higher_limits = DelegationScope(
        allowed_operations=["query"],
        resource_limits=ResourceLimits(max_total_atp=200.0),
    )
    check("T32.5 Higher resource limits not subset", not higher_limits.is_subset_of(parent_s))

    expired_deleg = DelegationToken(
        token_id="expired_t", issuer="lct://user:x@mainnet", delegate="y",
        scope=DelegationScope(allowed_operations=[]),
        issued_at=(datetime.now(timezone.utc) - timedelta(hours=48)).isoformat(),
        expires_at=(datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
        signature="test",
    )
    check("T32.6 Expired token detected", expired_deleg.is_expired())

    deleg_dc = DelegationToken(
        token_id="dc_001", issuer="r", delegate="d",
        scope=DelegationScope(allowed_operations=[]),
        issued_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        signature="test",
    )
    bt_dc = budgets.create_budgeted_token(deleg_dc, 50.0)
    tx_dc, _ = budgets.lock_transaction("dc_001", 10.0)
    budgets.commit_transaction(tx_dc)
    ok_dc = budgets.commit_transaction(tx_dc)
    check("T32.7 Double commit returns False", not ok_dc)

    tx_dr, _ = budgets.lock_transaction("dc_001", 10.0)
    budgets.rollback_transaction(tx_dr)
    ok_dr = budgets.rollback_transaction(tx_dr)
    check("T32.8 Double rollback returns False", not ok_dr)

    # ── T33: Serialization ───────────────────────────────────────────────
    print("T33: Serialization")
    token_dict = sage_token.to_dict()
    check("T33.1 Token dict has token_id", "token_id" in token_dict)
    check("T33.2 Token dict has issuer", token_dict["issuer"] == "lct://user:alice@mainnet")
    check("T33.3 Token dict has scope.allowed_operations", "allowed_operations" in token_dict["scope"])

    id_dict = human_id.to_dict()
    check("T33.4 Identity dict has lct_uri", id_dict["lct_uri"] == "lct://user:alice@mainnet")
    check("T33.5 Identity dict has hardware_type", id_dict["hardware_type"] == "TPM_2.0")

    cn_dict = cn_token.to_dict()
    check("T33.6 Cross-network dict has exchange_rate", abs(cn_dict["exchange_rate"] - 0.08) < 0.001)
    check("T33.7 Cross-network dict has bridge_fee", cn_dict["bridge_fee"] == 1.0)

    # ── T34: Security Event Audit Trail ──────────────────────────────────
    print("T34: Security Event Audit Trail")
    all_events = sec_svc.events
    check("T34.1 Events recorded", len(all_events) > 0)

    event_types = {e.event_type for e in all_events}
    check("T34.2 Multiple event types", len(event_types) >= 2)

    has_critical = any(e.severity == "critical" for e in all_events)
    check("T34.3 Critical severity events exist", has_critical)

    all_timestamped = all(e.timestamp for e in all_events)
    check("T34.4 All events timestamped", all_timestamped)

    # ── T35: Budget Utilization Property ─────────────────────────────────
    print("T35: Budget Utilization Property")
    deleg_util = DelegationToken(
        token_id="util_001", issuer="r", delegate="d",
        scope=DelegationScope(allowed_operations=[]),
        issued_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        signature="test",
    )
    bt_util = budgets.create_budgeted_token(deleg_util, 200.0)

    check("T35.1 Initial utilization = 0", bt_util.utilization == 0.0)

    tx_u, _ = budgets.lock_transaction("util_001", 100.0)
    budgets.commit_transaction(tx_u)
    check("T35.2 50% utilization", abs(bt_util.utilization - 0.5) < 0.01)

    tx_u2, _ = budgets.lock_transaction("util_001", 100.0)
    budgets.commit_transaction(tx_u2)
    check("T35.3 100% utilization", abs(bt_util.utilization - 1.0) < 0.01)

    # ── T36: Efficient Agents Get Lower Budgets ──────────────────────────
    print("T36: Efficient Agents Get Lower Budgets (Key Insight)")
    opt2 = DynamicBudgetOptimizer()

    for _ in range(10):
        opt2.record_usage(BudgetUsageRecord(
            "agent:efficient_high_rep", "task", 100, 50, True, 100, 2.0,
            datetime.now(timezone.utc).isoformat()
        ))

    for _ in range(10):
        opt2.record_usage(BudgetUsageRecord(
            "agent:inefficient_high_rep", "task", 100, 100, True, 40, 0.4,
            datetime.now(timezone.utc).isoformat()
        ))

    budget_efficient = opt2.calculate_optimal_budget("agent:efficient_high_rep", "task", 0.9)
    budget_inefficient = opt2.calculate_optimal_budget("agent:inefficient_high_rep", "task", 0.9)

    check("T36.1 Efficient agent needs less budget", budget_efficient <= budget_inefficient)

    perf_eff = opt2.get_agent_performance("agent:efficient_high_rep")
    perf_ineff = opt2.get_agent_performance("agent:inefficient_high_rep")
    check("T36.2 Efficient agent has higher efficiency", perf_eff["avg_efficiency"] > perf_ineff["avg_efficiency"])
    check("T36.3 Both have same success rate", perf_eff["success_rate"] == perf_ineff["success_rate"])

    # ── T37: Cross-Network – Multiple Networks ───────────────────────────
    print("T37: Cross-Network – Multiple Networks")
    cn_multi = CrossNetworkService()
    nets = [
        Network("mainnet", 1.0, 1.0),
        Network("testnet", 0.1, 0.8),
        Network("sidechain", 0.5, 0.6),
        Network("l2_rollup", 0.8, 0.9),
    ]
    for n in nets:
        cn_multi.register_network(n)

    cn_multi.set_reputation("agent:multi", "mainnet", 0.95)
    cn_multi.set_reputation("agent:multi", "testnet", 0.6)
    cn_multi.set_reputation("agent:multi", "sidechain", 0.4)
    cn_multi.set_reputation("agent:multi", "l2_rollup", 0.85)

    agg_all = cn_multi.aggregate_reputation("agent:multi")
    check("T37.1 4-network aggregation is weighted average",
          0.5 < agg_all < 1.0)

    agg_high = cn_multi.aggregate_reputation("agent:multi", ["mainnet", "l2_rollup"])
    agg_low = cn_multi.aggregate_reputation("agent:multi", ["testnet", "sidechain"])
    check("T37.2 High-trust network aggregation > low-trust", agg_high > agg_low)

    # ── T38: Combined Attack Scenario ────────────────────────────────────
    print("T38: Combined Attack Scenario")
    sec_combined = SecurityMitigationService()

    ok_sybil, _ = sec_combined.check_identity_creation_cost(10.0)
    check("T38.1 Sybil: insufficient ATP for identity", not ok_sybil)

    loss = sec_combined.calculate_farming_loss(100, 1000.0)
    check("T38.2 Farming: 100-loop always net negative", loss < 0)
    final_amount = 1000.0 + loss
    check("T38.3 Farming: nearly all ATP lost after 100 loops",
          final_amount < 1000.0 * 0.01)

    sec_combined.register_atp_supply(10000.0)
    fake_balances = {"attacker": 11000.0}
    ok_cons, _ = sec_combined.check_conservation(fake_balances)
    check("T38.4 Conservation: ATP creation detected", not ok_cons)

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"AI Agent Accountability Stack: {passed}/{total} checks passed")
    if failed:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, total


if __name__ == "__main__":
    run_tests()
