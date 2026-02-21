#!/usr/bin/env python3
"""
Web4 ATP/ADP Metering Subprotocol — Reference Implementation

Privacy-preserving, auditable resource metering between Web4 entities.
ATP = credit issuance, ADP = evidence of value delivered.

Protocol flow:
  CreditGrant → UsageReport(s) → Settle (or Dispute → Settle)

Per: forum/nova/web4-core-handshake-and-metering/core-spec/atp-adp-metering.md

Implements:
  - CreditGrant with scope, ceiling, rate limits, time windows
  - UsageReport with sequencing, evidence digests, witness attestation
  - Dispute resolution with partial acceptance
  - Settlement with balance tracking and optional chain anchoring
  - Token-bucket rate limiting
  - Replay protection via (grant_id, seq) uniqueness
  - 6 metering-specific error codes
  - Witness integration (time, audit-minimal, oracle)

@version 1.0.0
@see forum/nova/web4-core-handshake-and-metering/core-spec/atp-adp-metering.md
"""

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
# Metering Error Codes (per spec §6)
# ═══════════════════════════════════════════════════════════════

class MeteringError(Enum):
    """Metering-specific error codes."""
    GRANT_EXPIRED     = ("W4_ERR_GRANT_EXPIRED",    "Grant Expired",         410)
    RATE_LIMIT        = ("W4_ERR_RATE_LIMIT",        "Rate Limit Exceeded",   429)
    SCOPE_DENIED      = ("W4_ERR_SCOPE_DENIED",      "Scope Denied",          403)
    BAD_SEQUENCE      = ("W4_ERR_BAD_SEQUENCE",       "Bad Sequence Number",   400)
    WITNESS_REQUIRED  = ("W4_ERR_WITNESS_REQUIRED",   "Witness Required",      403)
    FORMAT_ERROR      = ("W4_ERR_FORMAT",             "Format Error",          400)

    def __init__(self, code: str, title: str, status: int):
        self.code = code
        self.title = title
        self.status = status


class MeteringException(Exception):
    """Metering protocol error."""
    def __init__(self, err: MeteringError, detail: str = ""):
        self.error = err
        self.detail = detail
        super().__init__(f"[{err.code}] {err.title}: {detail}")


# ═══════════════════════════════════════════════════════════════
# Token Bucket Rate Limiter
# ═══════════════════════════════════════════════════════════════

@dataclass
class TokenBucket:
    """Token-bucket rate limiter per spec §4."""
    max_per_min: float
    window_s: float = 60.0
    burst: float = 2.0
    _tokens: float = 0.0
    _last_refill: float = 0.0

    def __post_init__(self):
        self._tokens = self.max_per_min * self.burst
        self._last_refill = time.time()

    def _refill(self):
        now = time.time()
        elapsed = now - self._last_refill
        refill = (elapsed / self.window_s) * self.max_per_min
        self._tokens = min(self._tokens + refill, self.max_per_min * self.burst)
        self._last_refill = now

    def try_consume(self, amount: float) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        self._refill()
        if self._tokens >= amount:
            self._tokens -= amount
            return True
        return False

    @property
    def available(self) -> float:
        self._refill()
        return self._tokens


# ═══════════════════════════════════════════════════════════════
# Protocol Messages
# ═══════════════════════════════════════════════════════════════

def _nonce() -> str:
    return os.urandom(12).hex()

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class CreditGrant:
    """ATP credit grant from Grantor to Consumer (spec §3.1)."""
    grant_id: str
    scopes: List[str]
    ceiling_total: float
    ceiling_unit: str
    rate_max_per_min: float
    window_size_s: float = 3600.0
    window_burst: float = 2.0
    policy: Dict[str, Any] = field(default_factory=dict)
    not_before: str = ""
    not_after: str = ""
    witness_req: List[str] = field(default_factory=lambda: ["time"])
    nonce: str = ""
    ts: str = ""
    proof_jws: str = ""  # issuer signature placeholder

    def __post_init__(self):
        if not self.nonce:
            self.nonce = _nonce()
        if not self.ts:
            self.ts = _now()
        if not self.not_before:
            self.not_before = self.ts
        if not self.not_after:
            # Default 1 hour
            dt = datetime.now(timezone.utc) + timedelta(hours=1)
            self.not_after = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_dict(self) -> dict:
        return {
            "type": "CreditGrant",
            "ver": "w4/1",
            "grant_id": self.grant_id,
            "scopes": self.scopes,
            "ceil": {"total": self.ceiling_total, "unit": self.ceiling_unit},
            "rate": {"max_per_min": self.rate_max_per_min},
            "window": {"size_s": self.window_size_s, "burst": self.window_burst},
            "policy": self.policy,
            "not_before": self.not_before,
            "not_after": self.not_after,
            "proof": {"jws": self.proof_jws},
            "witness_req": self.witness_req,
            "nonce": self.nonce,
            "ts": self.ts,
        }

    def is_active(self, now: Optional[str] = None) -> bool:
        """Check if grant is within validity window."""
        t = now or _now()
        return self.not_before <= t <= self.not_after


@dataclass
class UsageItem:
    """Single scope usage entry."""
    scope: str
    amount: float
    unit: str

    def to_dict(self) -> dict:
        return {"scope": self.scope, "amount": self.amount, "unit": self.unit}


@dataclass
class WitnessAttestation:
    """Witness attestation on a message."""
    witness_type: str  # "time", "audit-minimal", "oracle"
    witness_ref: str   # w4id of witness
    sig: str = ""      # signature placeholder

    def to_dict(self) -> dict:
        return {"type": self.witness_type, "ref": self.witness_ref, "sig": self.sig}


@dataclass
class UsageReport:
    """Consumer usage report (spec §3.2)."""
    grant_id: str
    seq: int
    window_start: str
    window_end: str
    usage: List[UsageItem]
    evidence_digest: str = ""
    evidence_method: str = "sha256-agg"
    evidence_samples: int = 0
    witness: List[WitnessAttestation] = field(default_factory=list)
    nonce: str = ""
    ts: str = ""

    def __post_init__(self):
        if not self.nonce:
            self.nonce = _nonce()
        if not self.ts:
            self.ts = _now()
        if not self.evidence_digest:
            raw = json.dumps([u.to_dict() for u in self.usage], sort_keys=True).encode()
            self.evidence_digest = _digest(raw)

    @property
    def total_amount(self) -> float:
        return sum(u.amount for u in self.usage)

    def to_dict(self) -> dict:
        return {
            "type": "UsageReport",
            "ver": "w4/1",
            "grant_id": self.grant_id,
            "seq": self.seq,
            "window": f"{self.window_start}/{self.window_end}",
            "usage": [u.to_dict() for u in self.usage],
            "evidence": {
                "digest": self.evidence_digest,
                "method": self.evidence_method,
                "samples": self.evidence_samples,
            },
            "witness": [w.to_dict() for w in self.witness],
            "nonce": self.nonce,
            "ts": self.ts,
        }


@dataclass
class Dispute:
    """Dispute on a usage report (spec §3.3)."""
    grant_id: str
    seq: int
    reason: str  # "exceeds-rate-limit", "exceeds-ceiling", "invalid-scope", "bad-evidence"
    details: Dict[str, Any] = field(default_factory=dict)
    proposed: str = "partial-accept"  # "partial-accept", "reject", "renegotiate"
    nonce: str = ""
    ts: str = ""

    def __post_init__(self):
        if not self.nonce:
            self.nonce = _nonce()
        if not self.ts:
            self.ts = _now()

    def to_dict(self) -> dict:
        return {
            "type": "Dispute",
            "ver": "w4/1",
            "grant_id": self.grant_id,
            "seq": self.seq,
            "reason": self.reason,
            "details": self.details,
            "proposed": self.proposed,
            "nonce": self.nonce,
            "ts": self.ts,
        }


@dataclass
class Settle:
    """Settlement confirmation (spec §3.4)."""
    grant_id: str
    up_to_seq: int
    remaining: float
    unit: str
    receipt: str = ""
    anchor_txid: Optional[str] = None
    anchor_digest: Optional[str] = None
    nonce: str = ""
    ts: str = ""

    def __post_init__(self):
        if not self.nonce:
            self.nonce = _nonce()
        if not self.ts:
            self.ts = _now()
        if not self.receipt:
            self.receipt = f"rcpt-{os.urandom(8).hex()}"

    def to_dict(self) -> dict:
        d = {
            "type": "Settle",
            "ver": "w4/1",
            "grant_id": self.grant_id,
            "up_to_seq": self.up_to_seq,
            "balance": {"remaining": self.remaining, "unit": self.unit},
            "receipt": self.receipt,
            "nonce": self.nonce,
            "ts": self.ts,
        }
        if self.anchor_txid:
            d["anchor"] = {"txid": self.anchor_txid, "digest": self.anchor_digest or ""}
        return d


# ═══════════════════════════════════════════════════════════════
# Grant State Machine
# ═══════════════════════════════════════════════════════════════

class GrantState(Enum):
    ACTIVE = "active"
    DISPUTED = "disputed"
    SETTLED = "settled"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"


@dataclass
class GrantTracker:
    """Tracks state and usage for a single credit grant."""
    grant: CreditGrant
    state: GrantState = GrantState.ACTIVE
    consumed: float = 0.0
    last_seq: int = 0
    replay_window: Set[int] = field(default_factory=set)
    reports: List[UsageReport] = field(default_factory=list)
    disputes: List[Dispute] = field(default_factory=list)
    settlements: List[Settle] = field(default_factory=list)
    rate_limiter: Optional[TokenBucket] = None

    def __post_init__(self):
        self.rate_limiter = TokenBucket(
            max_per_min=self.grant.rate_max_per_min,
            window_s=self.grant.window_size_s / 60,  # convert to per-minute basis
            burst=self.grant.window_burst,
        )

    @property
    def remaining(self) -> float:
        return max(0.0, self.grant.ceiling_total - self.consumed)


# ═══════════════════════════════════════════════════════════════
# Metering Engine
# ═══════════════════════════════════════════════════════════════

class MeteringEngine:
    """
    ATP/ADP metering engine implementing the full protocol lifecycle.

    Roles:
      - Grantor creates CreditGrant
      - Consumer submits UsageReport
      - Engine enforces rate limits, scope, ceilings, replay protection
      - Either side can Dispute
      - Grantor issues Settle
    """

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.grants: Dict[str, GrantTracker] = {}
        self.event_log: List[Dict[str, Any]] = []

    def _log(self, event: str, grant_id: str, **details):
        self.event_log.append({
            "ts": _now(),
            "entity": self.entity_id,
            "event": event,
            "grant_id": grant_id,
            **details,
        })

    # ── Grant Management ──

    def issue_grant(self, scopes: List[str], ceiling: float,
                    unit: str = "joule-equivalent",
                    rate_max_per_min: float = 5000,
                    witness_req: Optional[List[str]] = None,
                    policy: Optional[Dict] = None,
                    not_after: Optional[str] = None) -> CreditGrant:
        """Grantor creates a new credit grant."""
        grant_id = f"atp-{os.urandom(8).hex()}"
        grant = CreditGrant(
            grant_id=grant_id,
            scopes=scopes,
            ceiling_total=ceiling,
            ceiling_unit=unit,
            rate_max_per_min=rate_max_per_min,
            witness_req=witness_req or ["time"],
            policy=policy or {},
        )
        if not_after:
            grant.not_after = not_after
        self.grants[grant_id] = GrantTracker(grant=grant)
        self._log("grant_issued", grant_id, ceiling=ceiling, scopes=scopes)
        return grant

    def receive_grant(self, grant: CreditGrant):
        """Consumer receives and registers a grant."""
        self.grants[grant.grant_id] = GrantTracker(grant=grant)
        self._log("grant_received", grant.grant_id)

    # ── Usage Reporting ──

    def submit_usage(self, grant_id: str, usage: List[UsageItem],
                     witness: Optional[List[WitnessAttestation]] = None) -> UsageReport:
        """Consumer submits a usage report."""
        if grant_id not in self.grants:
            raise MeteringException(MeteringError.FORMAT_ERROR, f"Unknown grant: {grant_id}")

        tracker = self.grants[grant_id]
        grant = tracker.grant

        # Check grant is active
        if tracker.state == GrantState.EXPIRED:
            raise MeteringException(MeteringError.GRANT_EXPIRED, f"Grant {grant_id} expired")
        if tracker.state == GrantState.EXHAUSTED:
            raise MeteringException(MeteringError.GRANT_EXPIRED, f"Grant {grant_id} exhausted")
        if not grant.is_active():
            tracker.state = GrantState.EXPIRED
            raise MeteringException(MeteringError.GRANT_EXPIRED,
                                    f"Grant {grant_id} outside validity window")

        # Check scopes
        for item in usage:
            if item.scope not in grant.scopes:
                raise MeteringException(MeteringError.SCOPE_DENIED,
                                        f"Scope '{item.scope}' not in grant scopes {grant.scopes}")

        # Check ceiling
        total = sum(u.amount for u in usage)
        if tracker.consumed + total > grant.ceiling_total:
            raise MeteringException(MeteringError.RATE_LIMIT,
                                    f"Would exceed ceiling: consumed={tracker.consumed}, "
                                    f"requested={total}, ceiling={grant.ceiling_total}")

        # Rate limiting (token bucket)
        if not tracker.rate_limiter.try_consume(total):
            raise MeteringException(MeteringError.RATE_LIMIT,
                                    f"Rate limit exceeded: available={tracker.rate_limiter.available:.1f}, "
                                    f"requested={total}")

        # Check witness requirements
        if grant.witness_req and not witness:
            raise MeteringException(MeteringError.WITNESS_REQUIRED,
                                    f"Grant requires witnesses: {grant.witness_req}")

        # Sequence management
        next_seq = tracker.last_seq + 1

        # Create report
        now = _now()
        report = UsageReport(
            grant_id=grant_id,
            seq=next_seq,
            window_start=now,
            window_end=now,
            usage=usage,
            witness=witness or [],
        )

        # Update tracker
        tracker.consumed += total
        tracker.last_seq = next_seq
        tracker.replay_window.add(next_seq)
        tracker.reports.append(report)

        if tracker.consumed >= grant.ceiling_total:
            tracker.state = GrantState.EXHAUSTED

        self._log("usage_submitted", grant_id, seq=next_seq, amount=total,
                  remaining=tracker.remaining)
        return report

    # ── Usage Validation (Grantor side) ──

    def validate_usage(self, report: UsageReport) -> Tuple[bool, Optional[Dispute]]:
        """Grantor validates a usage report. Returns (accepted, dispute_or_none)."""
        grant_id = report.grant_id
        if grant_id not in self.grants:
            return False, Dispute(grant_id=grant_id, seq=report.seq,
                                  reason="unknown-grant")

        tracker = self.grants[grant_id]
        grant = tracker.grant

        # Replay check
        if report.seq in tracker.replay_window:
            return False, Dispute(grant_id=grant_id, seq=report.seq,
                                  reason="replay-detected")

        # Sequence check
        if report.seq != tracker.last_seq + 1:
            return False, Dispute(grant_id=grant_id, seq=report.seq,
                                  reason="bad-sequence",
                                  details={"expected": tracker.last_seq + 1, "got": report.seq})

        # Scope check
        for item in report.usage:
            if item.scope not in grant.scopes:
                return False, Dispute(grant_id=grant_id, seq=report.seq,
                                      reason="invalid-scope",
                                      details={"scope": item.scope})

        # Ceiling check
        total = report.total_amount
        if tracker.consumed + total > grant.ceiling_total:
            return False, Dispute(
                grant_id=grant_id, seq=report.seq,
                reason="exceeds-ceiling",
                details={"consumed": tracker.consumed, "requested": total,
                         "ceiling": grant.ceiling_total},
                proposed="partial-accept",
            )

        # Accept
        tracker.consumed += total
        tracker.last_seq = report.seq
        tracker.replay_window.add(report.seq)
        tracker.reports.append(report)

        if tracker.consumed >= grant.ceiling_total:
            tracker.state = GrantState.EXHAUSTED

        self._log("usage_accepted", grant_id, seq=report.seq, amount=total)
        return True, None

    # ── Dispute ──

    def file_dispute(self, grant_id: str, seq: int, reason: str,
                     details: Optional[Dict] = None) -> Dispute:
        """File a dispute on a usage report."""
        if grant_id not in self.grants:
            raise MeteringException(MeteringError.FORMAT_ERROR, f"Unknown grant: {grant_id}")

        tracker = self.grants[grant_id]
        dispute = Dispute(
            grant_id=grant_id, seq=seq, reason=reason,
            details=details or {},
        )
        tracker.disputes.append(dispute)
        tracker.state = GrantState.DISPUTED
        self._log("dispute_filed", grant_id, seq=seq, reason=reason)
        return dispute

    # ── Settlement ──

    def settle(self, grant_id: str, up_to_seq: Optional[int] = None,
               anchor_txid: Optional[str] = None) -> Settle:
        """Grantor settles a grant (or partial settlement up to a sequence)."""
        if grant_id not in self.grants:
            raise MeteringException(MeteringError.FORMAT_ERROR, f"Unknown grant: {grant_id}")

        tracker = self.grants[grant_id]
        seq = up_to_seq or tracker.last_seq

        settlement = Settle(
            grant_id=grant_id,
            up_to_seq=seq,
            remaining=tracker.remaining,
            unit=tracker.grant.ceiling_unit,
            anchor_txid=anchor_txid,
        )
        tracker.settlements.append(settlement)
        tracker.state = GrantState.SETTLED
        self._log("settled", grant_id, up_to_seq=seq, remaining=tracker.remaining)
        return settlement

    # ── Queries ──

    def get_balance(self, grant_id: str) -> Tuple[float, float]:
        """Returns (consumed, remaining) for a grant."""
        if grant_id not in self.grants:
            raise MeteringException(MeteringError.FORMAT_ERROR, f"Unknown grant: {grant_id}")
        tracker = self.grants[grant_id]
        return tracker.consumed, tracker.remaining

    def get_state(self, grant_id: str) -> GrantState:
        if grant_id not in self.grants:
            raise MeteringException(MeteringError.FORMAT_ERROR, f"Unknown grant: {grant_id}")
        return self.grants[grant_id].state

    def active_grants(self) -> List[str]:
        return [gid for gid, t in self.grants.items() if t.state == GrantState.ACTIVE]

    def statistics(self) -> dict:
        """Aggregate metering statistics."""
        total_issued = sum(t.grant.ceiling_total for t in self.grants.values())
        total_consumed = sum(t.consumed for t in self.grants.values())
        states = {}
        for t in self.grants.values():
            states[t.state.value] = states.get(t.state.value, 0) + 1
        return {
            "grants": len(self.grants),
            "total_issued": total_issued,
            "total_consumed": total_consumed,
            "utilization": total_consumed / total_issued if total_issued > 0 else 0,
            "states": states,
            "events": len(self.event_log),
        }


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

    # ── T1: Credit Grant ──
    print("\n═══ T1: Credit Grant ═══")
    grantor = MeteringEngine("grantor-001")
    grant = grantor.issue_grant(
        scopes=["compute:infer", "net:egress"],
        ceiling=100000,
        unit="joule-equivalent",
        rate_max_per_min=5000,
    )
    check("T1: Grant created", grant.grant_id.startswith("atp-"))
    check("T1: Scopes set", grant.scopes == ["compute:infer", "net:egress"])
    check("T1: Ceiling set", grant.ceiling_total == 100000)
    check("T1: Has nonce", len(grant.nonce) == 24)
    check("T1: Has timestamp", len(grant.ts) > 0)
    check("T1: Is active", grant.is_active())

    d = grant.to_dict()
    check("T1: Serializes to dict", d["type"] == "CreditGrant")
    check("T1: Version is w4/1", d["ver"] == "w4/1")
    check("T1: Ceiling in dict", d["ceil"]["total"] == 100000)
    check("T1: Rate in dict", d["rate"]["max_per_min"] == 5000)

    # ── T2: Usage Report ──
    print("\n═══ T2: Usage Report ═══")
    consumer = MeteringEngine("consumer-001")
    consumer.receive_grant(grant)

    witness = WitnessAttestation(witness_type="time", witness_ref="w4id:witness:clock-1")
    report = consumer.submit_usage(grant.grant_id, [
        UsageItem(scope="compute:infer", amount=420, unit="joule-equivalent"),
        UsageItem(scope="net:egress", amount=12, unit="MB"),
    ], witness=[witness])

    check("T2: Report created", report.seq == 1)
    check("T2: Grant ID matches", report.grant_id == grant.grant_id)
    check("T2: Total amount", report.total_amount == 432)
    check("T2: Has evidence digest", len(report.evidence_digest) == 64)
    check("T2: Has witness", len(report.witness) == 1)

    d = report.to_dict()
    check("T2: Serializes", d["type"] == "UsageReport")
    check("T2: Seq in dict", d["seq"] == 1)
    check("T2: Usage in dict", len(d["usage"]) == 2)

    # Check balance
    consumed, remaining = consumer.get_balance(grant.grant_id)
    check("T2: Consumed = 432", consumed == 432)
    check("T2: Remaining = 99568", remaining == 99568)

    # ── T3: Multiple Usage Reports ──
    print("\n═══ T3: Multiple Usage Reports ═══")
    for i in range(5):
        r = consumer.submit_usage(grant.grant_id, [
            UsageItem(scope="compute:infer", amount=100, unit="joule-equivalent"),
        ], witness=[witness])
        check(f"T3: Report {i+2} seq = {r.seq}", r.seq == i + 2)

    consumed, remaining = consumer.get_balance(grant.grant_id)
    check("T3: Total consumed = 932", consumed == 932, f"consumed={consumed}")
    check("T3: Remaining = 99068", remaining == 99068)

    # ── T4: Scope Enforcement ──
    print("\n═══ T4: Scope Enforcement ═══")
    try:
        consumer.submit_usage(grant.grant_id, [
            UsageItem(scope="storage:write", amount=100, unit="GB"),
        ], witness=[witness])
        check("T4: Invalid scope rejected", False)
    except MeteringException as e:
        check("T4: Invalid scope rejected", e.error == MeteringError.SCOPE_DENIED,
              f"scope='storage:write'")

    # ── T5: Ceiling Enforcement ──
    print("\n═══ T5: Ceiling Enforcement ═══")
    small_grant = grantor.issue_grant(
        scopes=["compute:infer"],
        ceiling=500,
    )
    consumer.receive_grant(small_grant)
    consumer.submit_usage(small_grant.grant_id, [
        UsageItem(scope="compute:infer", amount=400, unit="joule-equivalent"),
    ], witness=[witness])

    try:
        consumer.submit_usage(small_grant.grant_id, [
            UsageItem(scope="compute:infer", amount=200, unit="joule-equivalent"),
        ], witness=[witness])
        check("T5: Ceiling exceeded rejected", False)
    except MeteringException as e:
        check("T5: Ceiling exceeded rejected", e.error == MeteringError.RATE_LIMIT,
              f"consumed=400, requested=200, ceiling=500")

    # Check exhausted state
    consumer.submit_usage(small_grant.grant_id, [
        UsageItem(scope="compute:infer", amount=100, unit="joule-equivalent"),
    ], witness=[witness])
    check("T5: Grant exhausted", consumer.get_state(small_grant.grant_id) == GrantState.EXHAUSTED)

    try:
        consumer.submit_usage(small_grant.grant_id, [
            UsageItem(scope="compute:infer", amount=1, unit="joule-equivalent"),
        ], witness=[witness])
        check("T5: Exhausted grant rejected", False)
    except MeteringException as e:
        check("T5: Exhausted grant rejected", e.error == MeteringError.GRANT_EXPIRED)

    # ── T6: Witness Requirement ──
    print("\n═══ T6: Witness Requirement ═══")
    witnessed_grant = grantor.issue_grant(
        scopes=["compute:infer"],
        ceiling=10000,
        witness_req=["time", "audit-minimal"],
    )
    consumer.receive_grant(witnessed_grant)

    try:
        consumer.submit_usage(witnessed_grant.grant_id, [
            UsageItem(scope="compute:infer", amount=100, unit="joule-equivalent"),
        ])  # No witness!
        check("T6: Missing witness rejected", False)
    except MeteringException as e:
        check("T6: Missing witness rejected", e.error == MeteringError.WITNESS_REQUIRED)

    # With witness — passes
    r = consumer.submit_usage(witnessed_grant.grant_id, [
        UsageItem(scope="compute:infer", amount=100, unit="joule-equivalent"),
    ], witness=[witness])
    check("T6: With witness accepted", r.seq == 1)

    # ── T7: Grantor Validation ──
    print("\n═══ T7: Grantor Validation ═══")
    # Simulate grantor receiving consumer's report
    grantor.receive_grant(grant)  # grantor also tracks the grant
    # Reset grantor's tracker for clean validation
    grantor.grants[grant.grant_id].last_seq = 0
    grantor.grants[grant.grant_id].replay_window.clear()

    # Build a fresh report for grantor validation
    test_report = UsageReport(
        grant_id=grant.grant_id, seq=1,
        window_start=_now(), window_end=_now(),
        usage=[UsageItem(scope="compute:infer", amount=500, unit="joule-equivalent")],
    )
    accepted, dispute = grantor.validate_usage(test_report)
    check("T7: Valid report accepted", accepted)
    check("T7: No dispute", dispute is None)

    # Replay — same seq again
    accepted2, dispute2 = grantor.validate_usage(test_report)
    check("T7: Replay rejected", not accepted2)
    check("T7: Replay dispute reason", dispute2.reason == "replay-detected")

    # Bad sequence
    skip_report = UsageReport(
        grant_id=grant.grant_id, seq=5,
        window_start=_now(), window_end=_now(),
        usage=[UsageItem(scope="compute:infer", amount=100, unit="joule-equivalent")],
    )
    accepted3, dispute3 = grantor.validate_usage(skip_report)
    check("T7: Bad sequence rejected", not accepted3)
    check("T7: Bad sequence dispute", dispute3.reason == "bad-sequence")

    # Invalid scope
    bad_scope_report = UsageReport(
        grant_id=grant.grant_id, seq=2,
        window_start=_now(), window_end=_now(),
        usage=[UsageItem(scope="storage:write", amount=100, unit="GB")],
    )
    accepted4, dispute4 = grantor.validate_usage(bad_scope_report)
    check("T7: Invalid scope rejected", not accepted4)
    check("T7: Invalid scope dispute reason", dispute4.reason == "invalid-scope")

    # ── T8: Dispute ──
    print("\n═══ T8: Dispute ═══")
    disp = grantor.file_dispute(grant.grant_id, seq=42,
                                reason="exceeds-rate-limit",
                                details={"limit": 5000, "observed": 7200})
    check("T8: Dispute created", disp.reason == "exceeds-rate-limit")
    check("T8: Dispute has details", disp.details["observed"] == 7200)
    check("T8: Proposed partial-accept", disp.proposed == "partial-accept")
    check("T8: Grant state = disputed",
          grantor.get_state(grant.grant_id) == GrantState.DISPUTED)

    d = disp.to_dict()
    check("T8: Dispute serializes", d["type"] == "Dispute")
    check("T8: Dispute has nonce", len(d["nonce"]) == 24)

    # ── T9: Settlement ──
    print("\n═══ T9: Settlement ═══")
    settlement = grantor.settle(grant.grant_id, up_to_seq=1,
                                anchor_txid="lc:abc123")
    check("T9: Settlement created", settlement.grant_id == grant.grant_id)
    check("T9: Up to seq 1", settlement.up_to_seq == 1)
    check("T9: Has receipt", settlement.receipt.startswith("rcpt-"))
    check("T9: Has anchor", settlement.anchor_txid == "lc:abc123")
    check("T9: Grant state = settled",
          grantor.get_state(grant.grant_id) == GrantState.SETTLED)

    d = settlement.to_dict()
    check("T9: Settlement serializes", d["type"] == "Settle")
    check("T9: Balance in dict", "remaining" in d["balance"])
    check("T9: Anchor in dict", d["anchor"]["txid"] == "lc:abc123")

    # ── T10: Full Flow (Grant → Usage → Settle) ──
    print("\n═══ T10: Full Flow ═══")
    g = MeteringEngine("g-full")
    c = MeteringEngine("c-full")

    grant_f = g.issue_grant(
        scopes=["compute:infer"],
        ceiling=1000,
        rate_max_per_min=500,
    )
    c.receive_grant(grant_f)
    g.receive_grant(grant_f)
    # Reset grantor tracker
    g.grants[grant_f.grant_id].last_seq = 0
    g.grants[grant_f.grant_id].replay_window.clear()

    # Consumer uses resources
    total_used = 0
    for i in range(5):
        r = c.submit_usage(grant_f.grant_id, [
            UsageItem(scope="compute:infer", amount=100, unit="joule-equivalent"),
        ], witness=[witness])
        # Grantor validates
        report_copy = UsageReport(
            grant_id=grant_f.grant_id, seq=r.seq,
            window_start=r.window_start, window_end=r.window_end,
            usage=[UsageItem(scope="compute:infer", amount=100, unit="joule-equivalent")],
        )
        accepted, _ = g.validate_usage(report_copy)
        check(f"T10: Report {i+1} accepted", accepted)
        total_used += 100

    # Settle
    s = g.settle(grant_f.grant_id)
    check("T10: Final settlement", s.remaining == 500, f"remaining={s.remaining}")
    check("T10: Consumed = 500", total_used == 500)

    # ── T11: Error Codes ──
    print("\n═══ T11: Error Codes ═══")
    check("T11: 6 error codes defined", len(MeteringError) == 6)

    for err in MeteringError:
        check(f"T11: {err.code} has status", err.status in (400, 403, 410, 429))

    # Test each error path
    try:
        consumer.submit_usage("nonexistent", [
            UsageItem(scope="x", amount=1, unit="y")
        ])
    except MeteringException as e:
        check("T11: Unknown grant → FORMAT_ERROR", e.error == MeteringError.FORMAT_ERROR)

    # ── T12: Statistics ──
    print("\n═══ T12: Statistics ═══")
    stats = consumer.statistics()
    check("T12: Stats has grants", stats["grants"] > 0, f"grants={stats['grants']}")
    check("T12: Stats has consumed", stats["total_consumed"] > 0)
    check("T12: Stats has utilization", 0 <= stats["utilization"] <= 1)
    check("T12: Stats has events", stats["events"] > 0)
    check("T12: Stats has states", len(stats["states"]) > 0)

    # ── T13: Token Bucket ──
    print("\n═══ T13: Token Bucket ═══")
    bucket = TokenBucket(max_per_min=100, window_s=60, burst=2)
    check("T13: Initial tokens = burst × rate", bucket.available == 200)
    check("T13: Consume 150", bucket.try_consume(150))
    check("T13: Remaining ≈ 50", abs(bucket.available - 50) < 5)
    check("T13: Consume 100 fails", not bucket.try_consume(100))
    check("T13: Consume 30 succeeds", bucket.try_consume(30))

    # ── T14: Serialization Roundtrip ──
    print("\n═══ T14: Serialization ═══")
    # Grant
    gd = grant.to_dict()
    check("T14: Grant has all fields",
          all(k in gd for k in ["type", "ver", "grant_id", "scopes", "ceil", "rate", "window"]))

    # Report
    rd = report.to_dict()
    check("T14: Report has evidence", "evidence" in rd)
    check("T14: Report evidence has digest", len(rd["evidence"]["digest"]) == 64)

    # Full JSON roundtrip
    grant_json = json.dumps(gd)
    check("T14: Grant JSON valid", json.loads(grant_json)["type"] == "CreditGrant")
    report_json = json.dumps(rd)
    check("T14: Report JSON valid", json.loads(report_json)["type"] == "UsageReport")

    # ── T15: Policy ──
    print("\n═══ T15: Policy ═══")
    policy_grant = grantor.issue_grant(
        scopes=["compute:infer"],
        ceiling=50000,
        policy={"region": ["us-west"], "priority": 3},
    )
    check("T15: Policy stored", policy_grant.policy["region"] == ["us-west"])
    check("T15: Policy priority", policy_grant.policy["priority"] == 3)
    d = policy_grant.to_dict()
    check("T15: Policy in dict", d["policy"]["region"] == ["us-west"])

    # ═══ Summary ═══
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  ATP/ADP Metering Protocol — Track O Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'='*60}")

    if failed == 0:
        print(f"\n  All {total} checks pass — metering protocol operational")
        print(f"  CreditGrant → UsageReport → Settle (with Dispute)")
        print(f"  Token-bucket rate limiting, scope enforcement, replay protection")
        print(f"  6 metering-specific error codes")
    else:
        print(f"\n  {failed} failures need investigation")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
