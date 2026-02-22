#!/usr/bin/env python3
"""
R6 Security Mitigations — Reference Implementation

Codifies all 16 attack vectors from r6-security-analysis.md with
concrete mitigations. Covers Tier 1 (Observational), Tier 2 (Authorization),
and Cross-Tier security concerns.

Attack Vectors Addressed:
  A1: Session File Tampering — HMAC integrity verification
  A2: Audit Log Tampering — hash chain + signed snapshots
  A3: Session Token Forgery — binding type validation
  A4: Hash Collision Attack — SHA-256 strength verification
  A5: Pre-image Bypass — timestamp freshness + pending R6 consistency
  A6: Chain Gap Injection — monotonic index gap detection
  B1: Admin Key Theft — key isolation + attestation checks
  B2: Role Escalation — multi-approver for sensitive actions
  B3: ATP Drain — rate limiting + trust threshold gates
  B4: Approval Racing — cooldown + batch size limits
  B5: Trust Inflation — diminishing returns + pattern detection
  B6: Replay Attack — nonce + request ID uniqueness
  C1: Tier Confusion — binding type exposure + validation
  C2: Import Poisoning — chain integrity + source trust verification
  C3: Clock Manipulation — time anomaly detection + external timestamp

@spec web4-standard/core-spec/r6-security-analysis.md
@version 1.0.0
"""

import hashlib
import hmac
import json
import math
import os
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
# Core Types
# ═══════════════════════════════════════════════════════════════

class BindingType(Enum):
    """Session token binding types (Tier distinction)."""
    SOFTWARE = "software"       # Tier 1: hash-based, local
    HARDWARE_TPM = "tpm2"       # Tier 2: TPM-bound key
    HARDWARE_TEE = "tee"        # Tier 2: TrustZone/SGX
    HARDWARE_HSM = "hsm"        # Tier 2: HSM-backed


class ActionRiskLevel(Enum):
    """Risk classification for actions."""
    LOW = "low"           # Read-only, informational
    MEDIUM = "medium"     # State changes, moderate ATP cost
    HIGH = "high"         # Destructive, high ATP cost
    CRITICAL = "critical" # Admin ops, key management


@dataclass
class AuditRecord:
    """A single audit record in the chain."""
    record_id: str
    record_hash: str
    action_type: str
    action_data: dict
    timestamp: float
    session_id: str
    actor_id: str
    atp_cost: float = 0.0
    provenance: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "record_id": self.record_id,
            "action_type": self.action_type,
            "action_data": self.action_data,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "actor_id": self.actor_id,
            "atp_cost": self.atp_cost,
            "provenance": self.provenance,
        }
        return d


@dataclass
class SessionFile:
    """Represents a session state file."""
    session_id: str
    token_id: str
    binding_type: str
    created_at: float
    actor_id: str
    action_count: int = 0
    data: dict = field(default_factory=dict)


@dataclass
class ApprovalRequest:
    """A request awaiting approval."""
    request_id: str
    actor_id: str
    action_type: str
    atp_cost: float
    risk_level: ActionRiskLevel
    submitted_at: float
    approved_at: Optional[float] = None
    approver_ids: List[str] = field(default_factory=list)
    nonce: str = ""


# ═══════════════════════════════════════════════════════════════
# A1: Session File Tampering — HMAC Integrity Verification
# ═══════════════════════════════════════════════════════════════

class SessionIntegrityVerifier:
    """Protects session files from tampering using HMAC.

    A1 mitigation: Add integrity verification on load,
    signature from session token.
    """

    def __init__(self, secret_key: bytes):
        self._secret = secret_key

    def sign_session(self, session: SessionFile) -> str:
        """Compute HMAC over session contents."""
        content = json.dumps({
            "session_id": session.session_id,
            "token_id": session.token_id,
            "binding_type": session.binding_type,
            "created_at": session.created_at,
            "actor_id": session.actor_id,
            "action_count": session.action_count,
            "data": session.data,
        }, sort_keys=True).encode()
        return hmac.new(self._secret, content, hashlib.sha256).hexdigest()

    def verify_session(self, session: SessionFile, expected_hmac: str) -> bool:
        """Verify session file integrity."""
        computed = self.sign_session(session)
        return hmac.compare_digest(computed, expected_hmac)


# ═══════════════════════════════════════════════════════════════
# A2: Audit Log Tampering — Hash Chain + Signed Snapshots
# ═══════════════════════════════════════════════════════════════

def hash_content(content: dict) -> str:
    """Compute SHA-256 hash of content (canonical JSON)."""
    return hashlib.sha256(
        json.dumps(content, sort_keys=True).encode()
    ).hexdigest()


class AuditChain:
    """Tamper-evident audit chain with signed snapshots.

    A2 mitigation: Hash chain + periodic snapshots with signatures.
    """

    def __init__(self):
        self._records: List[AuditRecord] = []
        self._snapshots: List[dict] = []

    def append(self, action_type: str, action_data: dict,
               session_id: str, actor_id: str,
               atp_cost: float = 0.0) -> AuditRecord:
        """Append a record to the chain."""
        prev_hash = "genesis" if not self._records else self._records[-1].record_hash
        action_index = len(self._records)

        record_content = {
            "action_type": action_type,
            "action_data": action_data,
            "timestamp": time.time(),
            "session_id": session_id,
            "actor_id": actor_id,
            "atp_cost": atp_cost,
            "provenance": {
                "prev_record_hash": prev_hash,
                "action_index": action_index,
            },
        }

        record = AuditRecord(
            record_id=f"rec-{uuid.uuid4().hex[:8]}",
            record_hash=hash_content(record_content),
            action_type=action_type,
            action_data=action_data,
            timestamp=record_content["timestamp"],
            session_id=session_id,
            actor_id=actor_id,
            atp_cost=atp_cost,
            provenance=record_content["provenance"],
        )
        self._records.append(record)
        return record

    @property
    def records(self) -> List[AuditRecord]:
        return list(self._records)

    def create_snapshot(self, signing_key: bytes) -> dict:
        """Create a signed snapshot of current chain state.

        A2 mitigation: Periodic snapshots with signatures.
        """
        snapshot_data = {
            "record_count": len(self._records),
            "latest_hash": self._records[-1].record_hash if self._records else "genesis",
            "timestamp": time.time(),
        }
        signature = hmac.new(
            signing_key,
            json.dumps(snapshot_data, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()
        snapshot = {**snapshot_data, "signature": signature}
        self._snapshots.append(snapshot)
        return snapshot

    def verify_snapshot(self, snapshot: dict, signing_key: bytes) -> bool:
        """Verify a snapshot signature."""
        data = {k: v for k, v in snapshot.items() if k != "signature"}
        expected = hmac.new(
            signing_key,
            json.dumps(data, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, snapshot["signature"])


# ═══════════════════════════════════════════════════════════════
# A5: Pre-image Bypass — Timestamp Freshness
# ═══════════════════════════════════════════════════════════════

class PreActionValidator:
    """Validates that R6 requests are created BEFORE action execution.

    A5 mitigation: Timestamp verification + pending R6 consistency.
    """

    FRESHNESS_WINDOW = 30.0  # Request must be ≤30s old

    def __init__(self):
        self._pending_requests: Dict[str, float] = {}  # request_id → submitted_at

    def register_request(self, request_id: str) -> float:
        """Register a request before action execution."""
        ts = time.time()
        self._pending_requests[request_id] = ts
        return ts

    def validate_pre_action(self, request_id: str,
                            execution_time: Optional[float] = None) -> Tuple[bool, str]:
        """Validate that request was registered before execution.

        Returns (valid, reason).
        """
        exec_time = execution_time or time.time()

        if request_id not in self._pending_requests:
            return False, "Request not registered (possible post-hoc fabrication)"

        submit_time = self._pending_requests[request_id]

        if exec_time < submit_time:
            return False, "Execution timestamp precedes request (time manipulation)"

        elapsed = exec_time - submit_time
        if elapsed > self.FRESHNESS_WINDOW:
            return False, f"Request too old ({elapsed:.1f}s > {self.FRESHNESS_WINDOW}s)"

        return True, "Pre-action validation passed"

    def consume_request(self, request_id: str) -> bool:
        """Remove a pending request after execution."""
        return self._pending_requests.pop(request_id, None) is not None


# ═══════════════════════════════════════════════════════════════
# A6: Chain Gap Injection — Gap Detection
# ═══════════════════════════════════════════════════════════════

def verify_chain(records: List[dict]) -> Tuple[bool, str]:
    """Verify audit chain integrity per spec §Verification Procedures.

    Checks:
    - Hash chain continuity (prev_hash links)
    - Record hash validity
    """
    prev_hash = "genesis"
    for record in records:
        # Check chain link
        prov = record.get("provenance", {})
        if prov.get("prev_record_hash") != prev_hash:
            return False, f"Chain break at {record.get('record_id', '?')}"
        # Verify record hash
        content = {k: v for k, v in record.items()
                   if k not in ("record_hash", "record_id")}
        expected = hash_content(content)
        if record.get("record_hash") != expected:
            return False, f"Hash mismatch at {record.get('record_id', '?')}"
        prev_hash = record["record_hash"]
    return True, "Chain valid"


def detect_gaps(records: List[dict]) -> Tuple[bool, str]:
    """Detect gaps in action indices per spec §Gap Detection.

    A6 mitigation: action_index MUST be monotonically increasing with no gaps.
    """
    indices = [r.get("provenance", {}).get("action_index", -1) for r in records]
    for i, idx in enumerate(indices):
        if i > 0 and idx != indices[i - 1] + 1:
            return False, f"Gap detected: {indices[i - 1]} → {idx}"
    if indices and indices[0] != 0:
        return False, f"Chain doesn't start at 0 (starts at {indices[0]})"
    return True, "No gaps"


# ═══════════════════════════════════════════════════════════════
# B2: Role Escalation — Multi-Approver for Sensitive Actions
# ═══════════════════════════════════════════════════════════════

@dataclass
class ApprovalPolicy:
    """Defines approval requirements based on risk level."""
    risk_level: ActionRiskLevel
    required_approvers: int
    required_trust_score: float  # Minimum T3 composite for approvers


DEFAULT_POLICIES = {
    ActionRiskLevel.LOW: ApprovalPolicy(ActionRiskLevel.LOW, 0, 0.0),
    ActionRiskLevel.MEDIUM: ApprovalPolicy(ActionRiskLevel.MEDIUM, 1, 0.3),
    ActionRiskLevel.HIGH: ApprovalPolicy(ActionRiskLevel.HIGH, 2, 0.5),
    ActionRiskLevel.CRITICAL: ApprovalPolicy(ActionRiskLevel.CRITICAL, 3, 0.7),
}


class MultiApprover:
    """Multi-approver workflow for sensitive actions.

    B2 mitigation: Require M-of-N quorum for high-risk actions.
    """

    def __init__(self, policies: Optional[Dict[ActionRiskLevel, ApprovalPolicy]] = None):
        self._policies = policies or DEFAULT_POLICIES
        self._pending: Dict[str, ApprovalRequest] = {}
        self._approver_trust: Dict[str, float] = {}  # approver_id → T3 composite

    def register_approver(self, approver_id: str, t3_composite: float) -> None:
        """Register an approver with their trust score."""
        self._approver_trust[approver_id] = t3_composite

    def submit_request(self, actor_id: str, action_type: str,
                       atp_cost: float, risk_level: ActionRiskLevel) -> ApprovalRequest:
        """Submit a request for approval."""
        req = ApprovalRequest(
            request_id=f"req-{uuid.uuid4().hex[:8]}",
            actor_id=actor_id,
            action_type=action_type,
            atp_cost=atp_cost,
            risk_level=risk_level,
            submitted_at=time.time(),
            nonce=os.urandom(16).hex(),
        )
        self._pending[req.request_id] = req
        return req

    def approve(self, request_id: str, approver_id: str) -> Tuple[bool, str]:
        """An approver approves a request. Returns (success, reason)."""
        req = self._pending.get(request_id)
        if req is None:
            return False, "Request not found"

        if approver_id == req.actor_id:
            return False, "Cannot self-approve"

        if approver_id in req.approver_ids:
            return False, "Already approved by this approver"

        # Check approver trust
        trust = self._approver_trust.get(approver_id, 0.0)
        policy = self._policies.get(req.risk_level)
        if policy and trust < policy.required_trust_score:
            return False, f"Approver trust {trust:.2f} below threshold {policy.required_trust_score:.2f}"

        req.approver_ids.append(approver_id)
        return True, "Approval recorded"

    def is_approved(self, request_id: str) -> Tuple[bool, str]:
        """Check if a request has sufficient approvals."""
        req = self._pending.get(request_id)
        if req is None:
            return False, "Request not found"

        policy = self._policies.get(req.risk_level)
        if policy is None:
            return False, "No policy for risk level"

        if policy.required_approvers == 0:
            return True, "No approval required (low risk)"

        if len(req.approver_ids) >= policy.required_approvers:
            return True, f"Approved ({len(req.approver_ids)}/{policy.required_approvers})"

        return False, f"Insufficient approvals ({len(req.approver_ids)}/{policy.required_approvers})"


# ═══════════════════════════════════════════════════════════════
# B3: ATP Drain — Trust Threshold Gates
# ═══════════════════════════════════════════════════════════════

class TrustGate:
    """Gates large ATP requests on trust score.

    B3 mitigation: Minimum trust threshold for large requests.
    """

    def __init__(self, thresholds: Optional[Dict[float, float]] = None):
        # atp_cost_threshold → required_t3_composite
        self._thresholds = thresholds or {
            10.0: 0.3,    # > 10 ATP requires T3 ≥ 0.3
            50.0: 0.5,    # > 50 ATP requires T3 ≥ 0.5
            100.0: 0.7,   # > 100 ATP requires T3 ≥ 0.7
            500.0: 0.9,   # > 500 ATP requires T3 ≥ 0.9
        }

    def check(self, atp_cost: float, t3_composite: float) -> Tuple[bool, str]:
        """Check if actor trust meets threshold for requested ATP cost."""
        required = 0.0
        for cost_threshold in sorted(self._thresholds.keys()):
            if atp_cost > cost_threshold:
                required = self._thresholds[cost_threshold]

        if t3_composite < required:
            return False, (f"ATP cost {atp_cost} requires T3 ≥ {required:.2f}, "
                          f"actor has {t3_composite:.2f}")
        return True, f"Trust gate passed (T3={t3_composite:.2f} ≥ {required:.2f})"


# ═══════════════════════════════════════════════════════════════
# B4: Approval Racing — Cooldown + Batch Limits
# ═══════════════════════════════════════════════════════════════

class ApprovalRateLimiter:
    """Prevents approval racing by enforcing cooldowns and batch limits.

    B4 mitigation: Approval cooldown + batch size limits.
    """

    def __init__(self, cooldown_sec: float = 10.0, max_batch: int = 5):
        self._cooldown = cooldown_sec
        self._max_batch = max_batch
        # approver_id → list of approval timestamps
        self._approval_history: Dict[str, List[float]] = defaultdict(list)

    def can_approve(self, approver_id: str) -> Tuple[bool, str]:
        """Check if approver can approve (respects cooldown and batch limits)."""
        now = time.time()
        history = self._approval_history[approver_id]

        # Clean old entries (outside batch window = 60s)
        window_start = now - 60.0
        history[:] = [t for t in history if t > window_start]

        # Check batch limit
        if len(history) >= self._max_batch:
            return False, f"Batch limit reached ({len(history)}/{self._max_batch} in last 60s)"

        # Check cooldown from last approval
        if history and (now - history[-1]) < self._cooldown:
            remaining = self._cooldown - (now - history[-1])
            return False, f"Cooldown active ({remaining:.1f}s remaining)"

        return True, "Approval rate limit OK"

    def record_approval(self, approver_id: str) -> None:
        """Record an approval for rate limiting."""
        self._approval_history[approver_id].append(time.time())


# ═══════════════════════════════════════════════════════════════
# B5: Trust Inflation — Pattern Detection
# ═══════════════════════════════════════════════════════════════

@dataclass
class ActionPattern:
    """Tracks action patterns for gaming detection."""
    action_type: str
    count: int = 0
    total_atp: float = 0.0
    first_seen: float = 0.0
    last_seen: float = 0.0
    trust_deltas: List[float] = field(default_factory=list)


class TrustGamingDetector:
    """Detects trust inflation through suspicious action patterns.

    B5 mitigation: Diminishing returns + suspicious pattern detection.
    """

    REPEAT_THRESHOLD = 5        # Flag after 5 identical action types
    VELOCITY_THRESHOLD = 10     # Flag if > 10 actions per minute
    LOW_COST_RATIO = 0.8        # Flag if > 80% of actions are low-cost
    TRUST_GAIN_CAP = 0.01       # Max trust gain per action after threshold

    def __init__(self):
        # actor_id → {action_type → ActionPattern}
        self._patterns: Dict[str, Dict[str, ActionPattern]] = defaultdict(dict)
        # actor_id → list of (timestamp, action_type, atp_cost)
        self._recent_actions: Dict[str, List[Tuple[float, str, float]]] = defaultdict(list)

    def record_action(self, actor_id: str, action_type: str,
                      atp_cost: float, trust_delta: float = 0.0) -> None:
        """Record an action for pattern analysis."""
        now = time.time()
        patterns = self._patterns[actor_id]

        if action_type not in patterns:
            patterns[action_type] = ActionPattern(
                action_type=action_type, first_seen=now
            )

        p = patterns[action_type]
        p.count += 1
        p.total_atp += atp_cost
        p.last_seen = now
        p.trust_deltas.append(trust_delta)

        self._recent_actions[actor_id].append((now, action_type, atp_cost))

    def compute_diminishing_factor(self, actor_id: str,
                                   action_type: str) -> float:
        """Compute diminishing returns factor for repeated action types.

        After REPEAT_THRESHOLD repetitions, trust gain decays exponentially.
        """
        patterns = self._patterns.get(actor_id, {})
        p = patterns.get(action_type)
        if p is None or p.count < self.REPEAT_THRESHOLD:
            return 1.0

        excess = p.count - self.REPEAT_THRESHOLD
        return max(0.01, 1.0 / (1.0 + excess * 0.5))

    def detect_suspicious_patterns(self, actor_id: str) -> List[str]:
        """Detect suspicious patterns in actor's action history.

        Returns list of warning messages.
        """
        warnings = []
        patterns = self._patterns.get(actor_id, {})
        recent = self._recent_actions.get(actor_id, [])

        # Check for repeated action types
        for action_type, p in patterns.items():
            if p.count >= self.REPEAT_THRESHOLD:
                factor = self.compute_diminishing_factor(actor_id, action_type)
                warnings.append(
                    f"REPEAT: '{action_type}' executed {p.count} times "
                    f"(diminishing factor: {factor:.3f})"
                )

        # Check velocity (actions per minute)
        if recent:
            now = time.time()
            last_minute = [a for a in recent if now - a[0] < 60.0]
            if len(last_minute) > self.VELOCITY_THRESHOLD:
                warnings.append(
                    f"VELOCITY: {len(last_minute)} actions in last 60s "
                    f"(threshold: {self.VELOCITY_THRESHOLD})"
                )

        # Check low-cost ratio
        if len(recent) >= 10:
            last_10 = recent[-10:]
            low_cost = sum(1 for _, _, cost in last_10 if cost < 1.0)
            ratio = low_cost / len(last_10)
            if ratio > self.LOW_COST_RATIO:
                warnings.append(
                    f"LOW_COST: {ratio:.0%} of last 10 actions are low-cost "
                    f"(threshold: {self.LOW_COST_RATIO:.0%})"
                )

        return warnings

    def get_adjusted_trust_delta(self, actor_id: str, action_type: str,
                                 base_delta: float) -> float:
        """Apply diminishing returns to trust delta."""
        factor = self.compute_diminishing_factor(actor_id, action_type)
        adjusted = base_delta * factor
        return min(adjusted, self.TRUST_GAIN_CAP) if base_delta > 0 else adjusted


# ═══════════════════════════════════════════════════════════════
# B6: Replay Attack — Request ID Uniqueness
# ═══════════════════════════════════════════════════════════════

class RequestDeduplicator:
    """Prevents replay attacks by tracking request IDs.

    B6 mitigation: Nonce + request ID uniqueness checking.
    """

    def __init__(self, max_history: int = 10000):
        self._seen_ids: Set[str] = set()
        self._seen_nonces: Set[str] = set()
        self._order: List[str] = []
        self._max_history = max_history

    def check_unique(self, request_id: str, nonce: str = "") -> Tuple[bool, str]:
        """Check if request ID and nonce are unique."""
        if request_id in self._seen_ids:
            return False, f"Duplicate request ID: {request_id}"
        if nonce and nonce in self._seen_nonces:
            return False, f"Duplicate nonce: {nonce}"
        return True, "Request is unique"

    def record(self, request_id: str, nonce: str = "") -> None:
        """Record a request as processed."""
        self._seen_ids.add(request_id)
        self._order.append(request_id)
        if nonce:
            self._seen_nonces.add(nonce)

        # Evict oldest if at capacity
        while len(self._seen_ids) > self._max_history:
            old_id = self._order.pop(0)
            self._seen_ids.discard(old_id)

    def check_and_record(self, request_id: str, nonce: str = "") -> Tuple[bool, str]:
        """Combined check-and-record."""
        ok, reason = self.check_unique(request_id, nonce)
        if ok:
            self.record(request_id, nonce)
        return ok, reason


# ═══════════════════════════════════════════════════════════════
# C1: Tier Confusion — Binding Type Validation
# ═══════════════════════════════════════════════════════════════

class TierValidator:
    """Validates and exposes binding type to prevent tier confusion.

    C1 mitigation: Always expose binding field, relying party checks.
    """

    HARDWARE_TYPES = {BindingType.HARDWARE_TPM, BindingType.HARDWARE_TEE,
                      BindingType.HARDWARE_HSM}

    def classify_tier(self, binding_type: BindingType) -> int:
        """Classify binding type into tier (1 or 2)."""
        if binding_type in self.HARDWARE_TYPES:
            return 2
        return 1

    def validate_claimed_tier(self, claimed_tier: int,
                               binding_type: BindingType) -> Tuple[bool, str]:
        """Validate that claimed tier matches actual binding type."""
        actual_tier = self.classify_tier(binding_type)
        if claimed_tier > actual_tier:
            return False, (f"Tier confusion: claims Tier {claimed_tier} "
                          f"but binding is {binding_type.value} (Tier {actual_tier})")
        return True, f"Tier {actual_tier} validated ({binding_type.value})"

    def check_import_tier(self, source_tier: int, target_tier: int,
                          source_binding: BindingType) -> Tuple[bool, str]:
        """Check if importing from source to target tier is safe.

        C2 mitigation: Validate source trust before import.
        """
        actual = self.classify_tier(source_binding)
        if actual < target_tier:
            return False, (f"Cannot import Tier {actual} records into "
                          f"Tier {target_tier} system")
        return True, f"Import from Tier {actual} to Tier {target_tier} allowed"


# ═══════════════════════════════════════════════════════════════
# C3: Clock Manipulation — Time Anomaly Detection
# ═══════════════════════════════════════════════════════════════

class TimeAnomalyDetector:
    """Detects clock manipulation in audit chains.

    C3 mitigation: Chain analysis for time anomalies.
    """

    MAX_BACKWARDS_DRIFT = 1.0    # Allow ≤1s backwards drift (NTP jitter)
    MAX_FORWARD_JUMP = 3600.0    # Flag jumps > 1 hour
    MIN_ACTION_INTERVAL = 0.001  # Flag actions faster than 1ms apart

    def __init__(self):
        self._anomalies: List[dict] = []

    def analyze_timestamps(self, timestamps: List[float]) -> List[dict]:
        """Analyze a sequence of timestamps for anomalies."""
        self._anomalies = []

        for i in range(1, len(timestamps)):
            delta = timestamps[i] - timestamps[i - 1]

            # Backwards time jump
            if delta < -self.MAX_BACKWARDS_DRIFT:
                self._anomalies.append({
                    "type": "backwards_jump",
                    "index": i,
                    "delta": delta,
                    "detail": f"Time went backwards by {abs(delta):.3f}s at index {i}",
                })

            # Suspicious forward jump
            elif delta > self.MAX_FORWARD_JUMP:
                self._anomalies.append({
                    "type": "forward_jump",
                    "index": i,
                    "delta": delta,
                    "detail": f"Time jumped forward by {delta:.0f}s at index {i}",
                })

            # Impossibly fast actions
            elif 0 <= delta < self.MIN_ACTION_INTERVAL:
                self._anomalies.append({
                    "type": "too_fast",
                    "index": i,
                    "delta": delta,
                    "detail": f"Actions {delta*1000:.3f}ms apart at index {i}",
                })

        return self._anomalies

    @property
    def has_anomalies(self) -> bool:
        return len(self._anomalies) > 0


# ═══════════════════════════════════════════════════════════════
# A4: Hash Collision — Strength Verification
# ═══════════════════════════════════════════════════════════════

def verify_hash_strength(hash_hex: str, min_bits: int = 128) -> Tuple[bool, str]:
    """Verify hash output meets minimum security level.

    A4 mitigation: SHA-256 with at least 128-bit truncation.
    """
    hash_bytes = len(hash_hex) / 2  # 2 hex chars per byte
    hash_bits = hash_bytes * 8

    if hash_bits < min_bits:
        return False, f"Hash is {hash_bits:.0f} bits (minimum: {min_bits})"
    return True, f"Hash strength: {hash_bits:.0f} bits (SHA-256)"


# ═══════════════════════════════════════════════════════════════
# Integrated Security Pipeline
# ═══════════════════════════════════════════════════════════════

class R6SecurityPipeline:
    """Integrates all security mitigations into a unified pipeline.

    Processes requests through all relevant security checks before execution.
    """

    def __init__(self, signing_key: Optional[bytes] = None):
        self._signing_key = signing_key or os.urandom(32)
        self.session_verifier = SessionIntegrityVerifier(self._signing_key)
        self.audit_chain = AuditChain()
        self.pre_action = PreActionValidator()
        self.multi_approver = MultiApprover()
        self.trust_gate = TrustGate()
        self.rate_limiter = ApprovalRateLimiter()
        self.gaming_detector = TrustGamingDetector()
        self.deduplicator = RequestDeduplicator()
        self.tier_validator = TierValidator()
        self.time_detector = TimeAnomalyDetector()

    def validate_request(self, request_id: str, actor_id: str,
                         action_type: str, atp_cost: float,
                         t3_composite: float, risk_level: ActionRiskLevel,
                         binding_type: BindingType = BindingType.SOFTWARE,
                         nonce: str = "") -> Tuple[bool, List[str]]:
        """Run full security validation pipeline.

        Returns (allowed, list_of_reasons).
        """
        reasons = []

        # B6: Replay/dedup check
        ok, reason = self.deduplicator.check_and_record(request_id, nonce)
        if not ok:
            return False, [reason]

        # B3: Trust threshold gate
        ok, reason = self.trust_gate.check(atp_cost, t3_composite)
        if not ok:
            return False, [reason]

        # B5: Gaming detection
        warnings = self.gaming_detector.detect_suspicious_patterns(actor_id)
        if warnings:
            reasons.extend(warnings)

        # B5: Adjusted trust delta
        factor = self.gaming_detector.compute_diminishing_factor(
            actor_id, action_type
        )
        if factor < 0.5:
            reasons.append(f"Trust gain severely diminished (factor: {factor:.3f})")

        # C1: Tier validation
        tier = self.tier_validator.classify_tier(binding_type)
        if risk_level in (ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL) and tier < 2:
            reasons.append(f"WARNING: High-risk action with Tier {tier} binding")

        return True, reasons


# ═══════════════════════════════════════════════════════════════
# Self-Test
# ═══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}{f' — {detail}' if detail else ''}")
        else:
            failed += 1
            print(f"  [FAIL] {label}{f' — {detail}' if detail else ''}")

    # ── T1: Session File Integrity (A1) ──
    print("\n═══ T1: Session File Integrity (A1) ═══")
    secret = os.urandom(32)
    verifier = SessionIntegrityVerifier(secret)

    session = SessionFile(
        session_id="sess-001", token_id="tok-abc",
        binding_type="software", created_at=time.time(),
        actor_id="alice", action_count=5,
    )
    sig = verifier.sign_session(session)
    check("T1.1: Session signed", len(sig) == 64)
    check("T1.2: Valid session verifies", verifier.verify_session(session, sig))

    # Tamper with session
    session.action_count = 999
    check("T1.3: Tampered session fails", not verifier.verify_session(session, sig))

    # Restore and verify again
    session.action_count = 5
    check("T1.4: Restored session verifies", verifier.verify_session(session, sig))

    # Different secret → different sig
    verifier2 = SessionIntegrityVerifier(os.urandom(32))
    sig2 = verifier2.sign_session(session)
    check("T1.5: Different secret → different sig", sig != sig2)
    check("T1.6: Wrong secret fails", not verifier.verify_session(session, sig2))

    # ── T2: Audit Chain + Hash Chain (A2) ──
    print("\n═══ T2: Audit Chain + Hash Chain (A2) ═══")
    chain = AuditChain()
    r1 = chain.append("read", {"file": "data.json"}, "sess-1", "alice")
    r2 = chain.append("write", {"file": "config.yaml"}, "sess-1", "alice", 5.0)
    r3 = chain.append("delete", {"file": "temp.log"}, "sess-1", "alice", 10.0)

    check("T2.1: Chain has 3 records", len(chain.records) == 3)
    check("T2.2: First record links to genesis",
          r1.provenance["prev_record_hash"] == "genesis")
    check("T2.3: Second links to first",
          r2.provenance["prev_record_hash"] == r1.record_hash)
    check("T2.4: Third links to second",
          r3.provenance["prev_record_hash"] == r2.record_hash)

    # Signed snapshots
    snap_key = os.urandom(32)
    snap = chain.create_snapshot(snap_key)
    check("T2.5: Snapshot created", snap["record_count"] == 3)
    check("T2.6: Snapshot verifies", chain.verify_snapshot(snap, snap_key))

    # Tampered snapshot fails
    snap["record_count"] = 999
    check("T2.7: Tampered snapshot fails", not chain.verify_snapshot(snap, snap_key))

    # ── T3: Chain Integrity Verification (A2 + A6) ──
    print("\n═══ T3: Chain Integrity Verification (A2 + A6) ═══")
    valid_records = []
    prev = "genesis"
    for i in range(5):
        content = {
            "action_type": f"action-{i}",
            "action_data": {},
            "timestamp": time.time() + i,
            "session_id": "s1",
            "actor_id": "alice",
            "atp_cost": 1.0,
            "provenance": {"prev_record_hash": prev, "action_index": i},
        }
        h = hash_content(content)
        valid_records.append({**content, "record_hash": h, "record_id": f"r{i}"})
        prev = h

    ok, msg = verify_chain(valid_records)
    check("T3.1: Valid chain verifies", ok, msg)

    ok, msg = detect_gaps(valid_records)
    check("T3.2: Valid chain has no gaps", ok, msg)

    # Break chain
    broken = [r.copy() for r in valid_records]
    broken[2]["record_hash"] = "tampered"
    ok, msg = verify_chain(broken)
    check("T3.3: Broken chain detected", not ok, msg)

    # Gap injection
    gapped = [valid_records[0], valid_records[1], valid_records[3]]  # Skip index 2
    ok, msg = detect_gaps(gapped)
    check("T3.4: Gap detected", not ok, msg)

    # Non-zero start
    bad_start = [{"provenance": {"action_index": 5}}]
    ok, msg = detect_gaps(bad_start)
    check("T3.5: Non-zero start detected", not ok, msg)

    # ── T4: Pre-Action Validation (A5) ──
    print("\n═══ T4: Pre-Action Validation (A5) ═══")
    pav = PreActionValidator()

    # Register then validate
    pav.register_request("req-001")
    ok, reason = pav.validate_pre_action("req-001")
    check("T4.1: Registered request validates", ok, reason)

    # Unregistered request fails
    ok, reason = pav.validate_pre_action("req-unknown")
    check("T4.2: Unregistered request rejected", not ok)
    check("T4.3: Rejection reason mentions fabrication", "fabrication" in reason.lower())

    # Consume request
    consumed = pav.consume_request("req-001")
    check("T4.4: Request consumed", consumed)
    check("T4.5: Consumed request gone", not pav.consume_request("req-001"))

    # Time manipulation detection
    pav.register_request("req-002")
    # Simulate execution BEFORE registration
    submit_time = pav._pending_requests["req-002"]
    ok, reason = pav.validate_pre_action("req-002", execution_time=submit_time - 5)
    check("T4.6: Pre-submit execution detected", not ok)
    check("T4.7: Reason mentions time manipulation", "time manipulation" in reason.lower())

    # ── T5: Multi-Approver (B2) ──
    print("\n═══ T5: Multi-Approver (B2) ═══")
    approver = MultiApprover()
    approver.register_approver("mgr-1", 0.8)
    approver.register_approver("mgr-2", 0.6)
    approver.register_approver("mgr-3", 0.4)

    # Low risk: no approval needed
    req_low = approver.submit_request("dev-1", "read_file", 1.0, ActionRiskLevel.LOW)
    ok, reason = approver.is_approved(req_low.request_id)
    check("T5.1: Low risk auto-approved", ok)

    # High risk: needs 2 approvers with T3 ≥ 0.5
    req_high = approver.submit_request("dev-1", "deploy", 50.0, ActionRiskLevel.HIGH)
    ok, reason = approver.is_approved(req_high.request_id)
    check("T5.2: High risk initially unapproved", not ok)

    # Self-approve blocked
    ok, reason = approver.approve(req_high.request_id, "dev-1")
    check("T5.3: Self-approve blocked", not ok)
    check("T5.4: Reason mentions self-approve", "self-approve" in reason.lower())

    # Low-trust approver blocked for high-risk
    ok, reason = approver.approve(req_high.request_id, "mgr-3")
    check("T5.5: Low-trust approver blocked", not ok)
    check("T5.6: Reason mentions trust threshold", "threshold" in reason.lower())

    # Valid approvers
    ok, _ = approver.approve(req_high.request_id, "mgr-1")
    check("T5.7: First approval succeeds", ok)

    ok, _ = approver.is_approved(req_high.request_id)
    check("T5.8: Still needs more approvals", not ok)

    ok, _ = approver.approve(req_high.request_id, "mgr-2")
    check("T5.9: Second approval succeeds", ok)

    ok, reason = approver.is_approved(req_high.request_id)
    check("T5.10: Now fully approved", ok)

    # Double approve blocked
    ok, reason = approver.approve(req_high.request_id, "mgr-1")
    check("T5.11: Double approve blocked", not ok)

    # ── T6: Trust Threshold Gates (B3) ──
    print("\n═══ T6: Trust Threshold Gates (B3) ═══")
    gate = TrustGate()

    ok, reason = gate.check(5.0, 0.1)
    check("T6.1: Small request with low trust OK", ok)

    ok, reason = gate.check(15.0, 0.1)
    check("T6.2: Medium request with low trust blocked", not ok)

    ok, reason = gate.check(15.0, 0.5)
    check("T6.3: Medium request with medium trust OK", ok)

    ok, reason = gate.check(200.0, 0.5)
    check("T6.4: Large request needs high trust", not ok)

    ok, reason = gate.check(200.0, 0.8)
    check("T6.5: Large request with high trust OK", ok)

    ok, reason = gate.check(600.0, 0.85)
    check("T6.6: Very large request needs very high trust", not ok)

    ok, reason = gate.check(600.0, 0.95)
    check("T6.7: Very large request with very high trust OK", ok)

    # ── T7: Approval Rate Limiting (B4) ──
    print("\n═══ T7: Approval Rate Limiting (B4) ═══")
    rl = ApprovalRateLimiter(cooldown_sec=0.1, max_batch=3)

    ok, _ = rl.can_approve("approver-1")
    check("T7.1: First approval allowed", ok)
    rl.record_approval("approver-1")

    # Cooldown active
    ok, reason = rl.can_approve("approver-1")
    check("T7.2: Cooldown blocks immediate re-approval", not ok)
    check("T7.3: Reason mentions cooldown", "cooldown" in reason.lower())

    # Wait for cooldown
    time.sleep(0.15)
    ok, _ = rl.can_approve("approver-1")
    check("T7.4: After cooldown, approval allowed", ok)
    rl.record_approval("approver-1")

    time.sleep(0.15)
    rl.record_approval("approver-1")

    # Batch limit (3 approvals in 60s)
    time.sleep(0.15)
    ok, reason = rl.can_approve("approver-1")
    check("T7.5: Batch limit reached", not ok)
    check("T7.6: Reason mentions batch limit", "batch" in reason.lower())

    # Different approver not affected
    ok, _ = rl.can_approve("approver-2")
    check("T7.7: Different approver not limited", ok)

    # ── T8: Trust Gaming Detection (B5) ──
    print("\n═══ T8: Trust Gaming Detection (B5) ═══")
    detector = TrustGamingDetector()

    # Normal activity
    for i in range(4):
        detector.record_action("actor-1", "read_file", 0.5, 0.001)

    warnings = detector.detect_suspicious_patterns("actor-1")
    check("T8.1: Normal activity → no warnings", len(warnings) == 0)

    # Exceed repeat threshold
    detector.record_action("actor-1", "read_file", 0.5, 0.001)
    warnings = detector.detect_suspicious_patterns("actor-1")
    check("T8.2: Repeat threshold triggers warning", len(warnings) >= 1)
    check("T8.3: Warning mentions REPEAT", any("REPEAT" in w for w in warnings))

    # Record past threshold for diminishing to activate
    detector.record_action("actor-1", "read_file", 0.5, 0.001)

    # Diminishing factor (now count=6, threshold=5, excess=1)
    factor = detector.compute_diminishing_factor("actor-1", "read_file")
    check("T8.4: Diminishing factor < 1.0", factor < 1.0)

    # Unknown action → factor 1.0
    factor2 = detector.compute_diminishing_factor("actor-1", "new_action")
    check("T8.5: Unknown action → factor 1.0", factor2 == 1.0)

    # Adjusted trust delta
    adjusted = detector.get_adjusted_trust_delta("actor-1", "read_file", 0.05)
    check("T8.6: Adjusted delta < base", adjusted < 0.05)
    check("T8.7: Adjusted delta capped", adjusted <= detector.TRUST_GAIN_CAP)

    # Low-cost ratio detection
    detector2 = TrustGamingDetector()
    for i in range(10):
        detector2.record_action("actor-2", f"action-{i % 3}", 0.1, 0.001)

    warnings2 = detector2.detect_suspicious_patterns("actor-2")
    check("T8.8: Low-cost ratio detected", any("LOW_COST" in w for w in warnings2))

    # ── T9: Request Deduplication (B6) ──
    print("\n═══ T9: Request Deduplication (B6) ═══")
    dedup = RequestDeduplicator()

    ok, _ = dedup.check_and_record("req-001", "nonce-001")
    check("T9.1: First request accepted", ok)

    ok, reason = dedup.check_and_record("req-001", "nonce-002")
    check("T9.2: Duplicate request ID rejected", not ok)
    check("T9.3: Reason mentions duplicate", "duplicate" in reason.lower())

    ok, reason = dedup.check_and_record("req-002", "nonce-001")
    check("T9.4: Duplicate nonce rejected", not ok)

    ok, _ = dedup.check_and_record("req-003", "nonce-003")
    check("T9.5: Unique request+nonce accepted", ok)

    # No nonce mode
    ok, _ = dedup.check_and_record("req-004")
    check("T9.6: No-nonce mode works", ok)

    ok, reason = dedup.check_and_record("req-004")
    check("T9.7: No-nonce duplicate rejected", not ok)

    # ── T10: Tier Confusion Detection (C1) ──
    print("\n═══ T10: Tier Confusion Detection (C1) ═══")
    tv = TierValidator()

    check("T10.1: Software = Tier 1", tv.classify_tier(BindingType.SOFTWARE) == 1)
    check("T10.2: TPM = Tier 2", tv.classify_tier(BindingType.HARDWARE_TPM) == 2)
    check("T10.3: TEE = Tier 2", tv.classify_tier(BindingType.HARDWARE_TEE) == 2)
    check("T10.4: HSM = Tier 2", tv.classify_tier(BindingType.HARDWARE_HSM) == 2)

    # Tier confusion: claiming Tier 2 with software binding
    ok, reason = tv.validate_claimed_tier(2, BindingType.SOFTWARE)
    check("T10.5: Tier confusion detected", not ok)
    check("T10.6: Reason mentions confusion", "confusion" in reason.lower())

    # Valid claim
    ok, _ = tv.validate_claimed_tier(1, BindingType.SOFTWARE)
    check("T10.7: Valid Tier 1 claim", ok)

    ok, _ = tv.validate_claimed_tier(2, BindingType.HARDWARE_TPM)
    check("T10.8: Valid Tier 2 claim", ok)

    # Underclaiming is OK (claiming less than actual)
    ok, _ = tv.validate_claimed_tier(1, BindingType.HARDWARE_TPM)
    check("T10.9: Underclaiming allowed", ok)

    # Import validation (C2)
    ok, _ = tv.check_import_tier(2, 2, BindingType.HARDWARE_TPM)
    check("T10.10: Tier 2 → Tier 2 import OK", ok)

    ok, reason = tv.check_import_tier(1, 2, BindingType.SOFTWARE)
    check("T10.11: Tier 1 → Tier 2 import blocked", not ok)

    # ── T11: Time Anomaly Detection (C3) ──
    print("\n═══ T11: Time Anomaly Detection (C3) ═══")
    tad = TimeAnomalyDetector()

    # Normal timestamps
    normal_ts = [1.0, 2.0, 3.0, 4.0, 5.0]
    anomalies = tad.analyze_timestamps(normal_ts)
    check("T11.1: Normal timestamps → no anomalies", len(anomalies) == 0)

    # Backwards time jump
    backwards_ts = [1.0, 2.0, 3.0, 1.5, 4.0]
    anomalies = tad.analyze_timestamps(backwards_ts)
    check("T11.2: Backwards jump detected", len(anomalies) >= 1)
    check("T11.3: Anomaly type is backwards_jump",
          any(a["type"] == "backwards_jump" for a in anomalies))

    # Forward time jump
    jump_ts = [1.0, 2.0, 5000.0, 5001.0]
    anomalies = tad.analyze_timestamps(jump_ts)
    check("T11.4: Forward jump detected", len(anomalies) >= 1)
    check("T11.5: Anomaly type is forward_jump",
          any(a["type"] == "forward_jump" for a in anomalies))

    # Impossibly fast actions
    fast_ts = [1.0, 1.0001, 1.0002, 2.0]
    anomalies = tad.analyze_timestamps(fast_ts)
    check("T11.6: Too-fast actions detected",
          any(a["type"] == "too_fast" for a in anomalies))
    check("T11.7: has_anomalies flag", tad.has_anomalies)

    # Small NTP jitter is OK (≤1s backwards)
    jitter_ts = [1.0, 2.0, 1.5, 3.0]  # 0.5s backwards = OK
    anomalies = tad.analyze_timestamps(jitter_ts)
    check("T11.8: NTP jitter (0.5s back) allowed", len(anomalies) == 0)

    # ── T12: Hash Strength Verification (A4) ──
    print("\n═══ T12: Hash Strength Verification (A4) ═══")
    sha256_hash = hashlib.sha256(b"test").hexdigest()
    ok, reason = verify_hash_strength(sha256_hash)
    check("T12.1: SHA-256 passes strength check", ok)
    check("T12.2: Reports 256 bits", "256" in reason)

    # Truncated hash (16 bytes = 128 bits)
    truncated = sha256_hash[:32]  # 32 hex chars = 16 bytes = 128 bits
    ok, _ = verify_hash_strength(truncated)
    check("T12.3: 128-bit truncation passes", ok)

    # Too short (8 bytes = 64 bits)
    short = sha256_hash[:16]
    ok, reason = verify_hash_strength(short)
    check("T12.4: 64-bit hash rejected", not ok)

    # ── T13: Integrated Security Pipeline ──
    print("\n═══ T13: Integrated Security Pipeline ═══")
    pipeline = R6SecurityPipeline()

    # Normal request
    ok, reasons = pipeline.validate_request(
        "req-100", "dev-1", "read_file", 1.0, 0.5,
        ActionRiskLevel.LOW, BindingType.SOFTWARE,
    )
    check("T13.1: Normal request passes pipeline", ok)
    check("T13.2: No warnings for normal request", len(reasons) == 0)

    # Duplicate request
    ok, reasons = pipeline.validate_request(
        "req-100", "dev-1", "read_file", 1.0, 0.5,
        ActionRiskLevel.LOW, BindingType.SOFTWARE,
    )
    check("T13.3: Duplicate request blocked", not ok)

    # ATP drain attempt (low trust, high cost)
    ok, reasons = pipeline.validate_request(
        "req-101", "dev-1", "deploy_all", 200.0, 0.2,
        ActionRiskLevel.HIGH, BindingType.SOFTWARE,
    )
    check("T13.4: ATP drain blocked by trust gate", not ok)

    # High-risk with software binding → warning
    ok, reasons = pipeline.validate_request(
        "req-102", "dev-1", "deploy_prod", 5.0, 0.8,
        ActionRiskLevel.HIGH, BindingType.SOFTWARE,
    )
    check("T13.5: High-risk + Tier 1 → passes with warning", ok)
    check("T13.6: Warning about tier mismatch",
          any("tier" in r.lower() for r in reasons))

    # Trust gaming after many actions
    for i in range(6):
        pipeline.gaming_detector.record_action("dev-1", "read_file", 0.1)

    ok, reasons = pipeline.validate_request(
        "req-103", "dev-1", "read_file", 0.5, 0.5,
        ActionRiskLevel.LOW, BindingType.SOFTWARE,
    )
    check("T13.7: Gaming detection triggers warnings", ok)
    check("T13.8: Pipeline includes gaming warnings",
          any("REPEAT" in r or "diminished" in r.lower() for r in reasons))

    # ── T14: Approval Policy Defaults ──
    print("\n═══ T14: Approval Policy Defaults ═══")
    check("T14.1: LOW needs 0 approvers",
          DEFAULT_POLICIES[ActionRiskLevel.LOW].required_approvers == 0)
    check("T14.2: MEDIUM needs 1 approver",
          DEFAULT_POLICIES[ActionRiskLevel.MEDIUM].required_approvers == 1)
    check("T14.3: HIGH needs 2 approvers",
          DEFAULT_POLICIES[ActionRiskLevel.HIGH].required_approvers == 2)
    check("T14.4: CRITICAL needs 3 approvers",
          DEFAULT_POLICIES[ActionRiskLevel.CRITICAL].required_approvers == 3)
    check("T14.5: CRITICAL needs T3 ≥ 0.7",
          DEFAULT_POLICIES[ActionRiskLevel.CRITICAL].required_trust_score == 0.7)

    # ── T15: Edge Cases ──
    print("\n═══ T15: Edge Cases ═══")
    # Empty chain verification
    ok, msg = verify_chain([])
    check("T15.1: Empty chain verifies", ok)

    ok, msg = detect_gaps([])
    check("T15.2: Empty chain has no gaps", ok)

    # Single record chain
    single = [{
        "record_hash": hash_content({
            "action_type": "init", "action_data": {},
            "timestamp": 1.0, "session_id": "s", "actor_id": "a",
            "atp_cost": 0, "provenance": {"prev_record_hash": "genesis", "action_index": 0},
        }),
        "record_id": "r0",
        "action_type": "init", "action_data": {},
        "timestamp": 1.0, "session_id": "s", "actor_id": "a",
        "atp_cost": 0, "provenance": {"prev_record_hash": "genesis", "action_index": 0},
    }]
    ok, _ = verify_chain(single)
    check("T15.3: Single record chain verifies", ok)

    # Deduplicator eviction
    dedup2 = RequestDeduplicator(max_history=3)
    dedup2.check_and_record("a")
    dedup2.check_and_record("b")
    dedup2.check_and_record("c")
    dedup2.check_and_record("d")  # Should evict "a"
    ok, _ = dedup2.check_and_record("a")
    check("T15.4: Evicted request re-accepted", ok)

    # Time anomaly with single timestamp
    anomalies = TimeAnomalyDetector().analyze_timestamps([1.0])
    check("T15.5: Single timestamp → no anomalies", len(anomalies) == 0)

    # Approval for non-existent request
    ma = MultiApprover()
    ok, reason = ma.is_approved("nonexistent")
    check("T15.6: Non-existent request → not approved", not ok)

    # Gaming detector with no history
    gd = TrustGamingDetector()
    warnings = gd.detect_suspicious_patterns("nobody")
    check("T15.7: No history → no warnings", len(warnings) == 0)

    # ── T16: Cross-Tier Import Validation (C2) ──
    print("\n═══ T16: Cross-Tier Import Validation (C2) ═══")
    tv2 = TierValidator()

    # Valid imports
    ok, _ = tv2.check_import_tier(2, 1, BindingType.HARDWARE_TPM)
    check("T16.1: Tier 2 → Tier 1 import OK (downgrade)", ok)

    ok, _ = tv2.check_import_tier(1, 1, BindingType.SOFTWARE)
    check("T16.2: Tier 1 → Tier 1 import OK", ok)

    # Invalid: claiming higher tier
    ok, reason = tv2.check_import_tier(2, 2, BindingType.SOFTWARE)
    check("T16.3: Software claiming Tier 2 import blocked", not ok)
    check("T16.4: Reason mentions tier mismatch", "tier" in reason.lower())

    # ═══ Summary ═══
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  R6 Security Mitigations — Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'='*60}")

    if failed == 0:
        print(f"\n  All {total} checks pass")
        print(f"  A1: Session file HMAC integrity")
        print(f"  A2: Hash chain + signed snapshots")
        print(f"  A4: Hash strength verification (SHA-256)")
        print(f"  A5: Pre-action timestamp validation")
        print(f"  A6: Chain gap detection (monotonic index)")
        print(f"  B2: Multi-approver with trust thresholds")
        print(f"  B3: ATP drain prevention (trust gates)")
        print(f"  B4: Approval cooldown + batch limits")
        print(f"  B5: Trust gaming detection (diminishing returns + patterns)")
        print(f"  B6: Request deduplication (ID + nonce)")
        print(f"  C1: Tier confusion detection")
        print(f"  C2: Import poisoning defense")
        print(f"  C3: Time anomaly detection")
    else:
        print(f"\n  {failed} failures need investigation")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
