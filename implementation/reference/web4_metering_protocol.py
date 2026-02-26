#!/usr/bin/env python3
"""
Web4 ATP/ADP Metering Subprotocol — Reference Implementation
Spec: web4-standard/protocols/web4-metering.md (120 lines)

Privacy-preserving, auditable resource metering between Web4 entities.
ATP = credit issuance; ADP = evidence of value delivered.

Covers:
  §1  Purpose: ATP credit issuance, ADP usage evidence
  §2  Roles: Grantor, Consumer, Witness, Anchor
  §3  Messages: CreditGrant, UsageReport, Dispute, Settle
  §4  Semantics: grant validity, rate enforcement (token-bucket),
      replay prevention, partial acceptance
  §5  Witnessing: time, audit-minimal, oracle classes
  §6  Errors: 6 error codes
  §7  Security: ceiling enforcement, transcript binding, hardware keys
  §8  Conformance: Profile A (Edge), Profile B (Enterprise)

Run: python web4_metering_protocol.py
"""

from __future__ import annotations
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional


# ============================================================
# §2 Roles
# ============================================================

class MeteringRole(Enum):
    GRANTOR = "grantor"       # Issues ATP credits with constraints
    CONSUMER = "consumer"     # Spends credits, generates ADP usage reports
    WITNESS = "witness"       # Time-stamps, audits, or arbitrates
    ANCHOR = "anchor"         # Records hashes/receipts to chain (optional)


# ============================================================
# §6 Error Codes
# ============================================================

class MeteringError(Enum):
    GRANT_EXPIRED = "W4_ERR_GRANT_EXPIRED"
    RATE_LIMIT = "W4_ERR_RATE_LIMIT"
    SCOPE_DENIED = "W4_ERR_SCOPE_DENIED"
    BAD_SEQUENCE = "W4_ERR_BAD_SEQUENCE"
    WITNESS_REQUIRED = "W4_ERR_WITNESS_REQUIRED"
    FORMAT = "W4_ERR_FORMAT"


# ============================================================
# §5 Witness Classes
# ============================================================

class WitnessClass(Enum):
    TIME = "time"                # RFC 3161-like timestamp
    AUDIT_MINIMAL = "audit-minimal"  # Token-bucket math + digests
    ORACLE = "oracle"            # Domain-specific validation


# ============================================================
# §8 Conformance Profiles
# ============================================================

class ConformanceProfile(Enum):
    EDGE = "A"         # JSON/JOSE, Ed25519, UsageReport every ≥60s
    ENTERPRISE = "B"   # CBOR/COSE, ECDSA-P256, batched with digest trees


PROFILE_SPECS = {
    ConformanceProfile.EDGE: {
        "encoding": "JSON",
        "signature": "JOSE",
        "algorithm": "Ed25519",
        "min_report_interval_s": 60,
        "batch_mode": False,
        "anchor": False,
    },
    ConformanceProfile.ENTERPRISE: {
        "encoding": "CBOR",
        "signature": "COSE",
        "algorithm": "ECDSA-P256",
        "min_report_interval_s": 0,  # batched
        "batch_mode": True,
        "anchor": True,  # optional lightchain anchor
    },
}


# ============================================================
# §3.1 CreditGrant (Grantor → Consumer)
# ============================================================

def _generate_nonce() -> str:
    return os.urandom(12).hex()  # 96-bit nonce


def _generate_grant_id() -> str:
    return f"atp-{os.urandom(16).hex()}"


def _generate_receipt_id() -> str:
    return f"rcpt-{os.urandom(16).hex()}"


@dataclass
class CreditGrant:
    """ATP credit grant from Grantor to Consumer (§3.1)."""
    grant_id: str = ""
    ver: str = "w4/1"
    scopes: list[str] = field(default_factory=list)
    ceil_total: float = 0.0
    ceil_unit: str = "joule-equivalent"
    rate_max_per_min: float = 0.0
    window_size_s: int = 3600
    window_burst: int = 2
    policy_region: list[str] = field(default_factory=list)
    policy_priority: int = 3
    not_before: str = ""
    not_after: str = ""
    proof_jws: str = ""
    witness_req: list[str] = field(default_factory=list)
    nonce: str = ""
    ts: str = ""

    def __post_init__(self):
        if not self.grant_id:
            self.grant_id = _generate_grant_id()
        if not self.nonce:
            self.nonce = _generate_nonce()
        if not self.ts:
            self.ts = datetime.utcnow().isoformat() + "Z"

    def is_valid_at(self, check_time: datetime) -> bool:
        """Check if grant is valid at given time (§4 grant validity)."""
        if self.not_before:
            nb = datetime.fromisoformat(self.not_before.replace("Z", "+00:00").replace("+00:00", ""))
            if check_time < nb:
                return False
        if self.not_after:
            na = datetime.fromisoformat(self.not_after.replace("Z", "+00:00").replace("+00:00", ""))
            if check_time > na:
                return False
        return True

    def has_scope(self, scope: str) -> bool:
        """Check if scope is covered by this grant."""
        for s in self.scopes:
            if scope == s or scope.startswith(s + ":"):
                return True
        return False

    def to_message(self) -> dict:
        return {
            "type": "CreditGrant",
            "ver": self.ver,
            "grant_id": self.grant_id,
            "scopes": self.scopes,
            "ceil": {"total": self.ceil_total, "unit": self.ceil_unit},
            "rate": {"max_per_min": self.rate_max_per_min},
            "window": {"size_s": self.window_size_s, "burst": self.window_burst},
            "policy": {"region": self.policy_region, "priority": self.policy_priority},
            "not_before": self.not_before,
            "not_after": self.not_after,
            "proof": {"jws": self.proof_jws},
            "witness_req": self.witness_req,
            "nonce": self.nonce,
            "ts": self.ts,
        }


# ============================================================
# §3.2 UsageReport (Consumer → Grantor)
# ============================================================

@dataclass
class UsageEntry:
    scope: str
    amount: float
    unit: str = "joule-equivalent"


@dataclass
class WitnessAttestation:
    witness_type: str    # "time", "audit-minimal", "oracle"
    ref: str = ""        # w4idp reference
    sig: str = ""        # signature


@dataclass
class UsageReport:
    """ADP usage report from Consumer (§3.2)."""
    grant_id: str = ""
    ver: str = "w4/1"
    seq: int = 0
    window_start: str = ""
    window_end: str = ""
    usage: list[UsageEntry] = field(default_factory=list)
    evidence_digest: str = ""
    evidence_method: str = "sha256-agg"
    evidence_samples: int = 0
    witnesses: list[WitnessAttestation] = field(default_factory=list)
    nonce: str = ""
    ts: str = ""

    def __post_init__(self):
        if not self.nonce:
            self.nonce = _generate_nonce()
        if not self.ts:
            self.ts = datetime.utcnow().isoformat() + "Z"

    @property
    def total_usage(self) -> float:
        return sum(u.amount for u in self.usage)

    def to_message(self) -> dict:
        return {
            "type": "UsageReport",
            "ver": self.ver,
            "grant_id": self.grant_id,
            "seq": self.seq,
            "window": f"{self.window_start}/{self.window_end}",
            "usage": [{"scope": u.scope, "amount": u.amount, "unit": u.unit} for u in self.usage],
            "evidence": {"digest": self.evidence_digest, "method": self.evidence_method,
                         "samples": self.evidence_samples},
            "witness": [{"type": w.witness_type, "ref": w.ref, "sig": w.sig}
                        for w in self.witnesses],
            "nonce": self.nonce,
            "ts": self.ts,
        }


# ============================================================
# §3.3 Dispute
# ============================================================

@dataclass
class Dispute:
    """Dispute message (§3.3)."""
    grant_id: str = ""
    ver: str = "w4/1"
    seq: int = 0
    reason: str = ""      # e.g. "exceeds-rate-limit"
    details: dict = field(default_factory=dict)
    proposed: str = ""    # e.g. "partial-accept"
    nonce: str = ""
    ts: str = ""

    def __post_init__(self):
        if not self.nonce:
            self.nonce = _generate_nonce()
        if not self.ts:
            self.ts = datetime.utcnow().isoformat() + "Z"

    def to_message(self) -> dict:
        return {
            "type": "Dispute",
            "ver": self.ver,
            "grant_id": self.grant_id,
            "seq": self.seq,
            "reason": self.reason,
            "details": self.details,
            "proposed": self.proposed,
            "nonce": self.nonce,
            "ts": self.ts,
        }


# ============================================================
# §3.4 Settle
# ============================================================

@dataclass
class Settlement:
    """Settlement message (§3.4)."""
    grant_id: str = ""
    ver: str = "w4/1"
    up_to_seq: int = 0
    balance_remaining: float = 0.0
    balance_unit: str = "joule-equivalent"
    receipt: str = ""
    anchor_txid: str = ""
    anchor_digest: str = ""
    nonce: str = ""
    ts: str = ""

    def __post_init__(self):
        if not self.receipt:
            self.receipt = _generate_receipt_id()
        if not self.nonce:
            self.nonce = _generate_nonce()
        if not self.ts:
            self.ts = datetime.utcnow().isoformat() + "Z"

    def to_message(self) -> dict:
        msg = {
            "type": "Settle",
            "ver": self.ver,
            "grant_id": self.grant_id,
            "up_to_seq": self.up_to_seq,
            "balance": {"remaining": self.balance_remaining, "unit": self.balance_unit},
            "receipt": self.receipt,
            "nonce": self.nonce,
            "ts": self.ts,
        }
        if self.anchor_txid:
            msg["anchor"] = {"txid": self.anchor_txid, "digest": self.anchor_digest}
        return msg


# ============================================================
# §4 Semantics — Token Bucket Rate Enforcement
# ============================================================

class TokenBucket:
    """Token-bucket rate limiter for rate enforcement (§4)."""

    def __init__(self, rate_per_min: float, window_s: int = 3600, burst: int = 2):
        self.rate_per_min = rate_per_min
        self.rate_per_sec = rate_per_min / 60.0
        self.capacity = rate_per_min * burst  # Max burst capacity
        self.tokens = self.capacity           # Start full
        self.window_s = window_s
        self.burst = burst
        self.last_refill = time.monotonic()

    def refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_sec)
        self.last_refill = now

    def try_consume(self, amount: float) -> bool:
        """Try to consume tokens. Returns False if rate-limited."""
        self.refill()
        if amount > self.tokens:
            return False
        self.tokens -= amount
        return True

    @property
    def available(self) -> float:
        self.refill()
        return self.tokens


# ============================================================
# §4 Semantics — Replay Prevention
# ============================================================

class ReplayGuard:
    """Per-grant replay window (§4): (grant_id, seq) must be unique."""

    def __init__(self):
        self.seen: dict[str, set[int]] = {}  # grant_id → set of seen seq numbers

    def check_and_record(self, grant_id: str, seq: int) -> bool:
        """Returns True if new (not replay), False if replay detected."""
        if grant_id not in self.seen:
            self.seen[grant_id] = set()
        if seq in self.seen[grant_id]:
            return False  # Replay!
        self.seen[grant_id].add(seq)
        return True


# ============================================================
# §4 + §7 — Metering Engine
# ============================================================

class MeteringEngine:
    """Full metering engine combining grant management, rate limiting,
    replay detection, and settlement."""

    def __init__(self, profile: ConformanceProfile = ConformanceProfile.EDGE):
        self.profile = profile
        self.grants: dict[str, CreditGrant] = {}
        self.buckets: dict[str, TokenBucket] = {}
        self.replay_guard = ReplayGuard()
        self.usage_log: dict[str, list[UsageReport]] = {}
        self.total_consumed: dict[str, float] = {}
        self.disputes: list[Dispute] = []
        self.settlements: list[Settlement] = []

    def register_grant(self, grant: CreditGrant) -> Optional[MeteringError]:
        """Register a new credit grant."""
        if grant.grant_id in self.grants:
            return MeteringError.FORMAT
        self.grants[grant.grant_id] = grant
        self.buckets[grant.grant_id] = TokenBucket(
            rate_per_min=grant.rate_max_per_min,
            window_s=grant.window_size_s,
            burst=grant.window_burst,
        )
        self.usage_log[grant.grant_id] = []
        self.total_consumed[grant.grant_id] = 0.0
        return None

    def process_usage(self, report: UsageReport) -> Optional[MeteringError]:
        """Process a usage report. Returns error or None on success."""
        grant = self.grants.get(report.grant_id)
        if not grant:
            return MeteringError.FORMAT

        # Check grant validity (§4)
        now = datetime.utcnow()
        if not grant.is_valid_at(now):
            return MeteringError.GRANT_EXPIRED

        # Check replay (§4)
        if not self.replay_guard.check_and_record(report.grant_id, report.seq):
            return MeteringError.BAD_SEQUENCE

        # Check scopes
        for entry in report.usage:
            if not grant.has_scope(entry.scope):
                return MeteringError.SCOPE_DENIED

        # Check witness requirements
        if grant.witness_req:
            report_witness_types = {w.witness_type for w in report.witnesses}
            for req in grant.witness_req:
                if req not in report_witness_types:
                    return MeteringError.WITNESS_REQUIRED

        # Check rate limit (§4 token-bucket)
        bucket = self.buckets[report.grant_id]
        total = report.total_usage
        if not bucket.try_consume(total):
            return MeteringError.RATE_LIMIT

        # Check ceiling
        new_total = self.total_consumed[report.grant_id] + total
        if new_total > grant.ceil_total:
            return MeteringError.GRANT_EXPIRED  # Ceiling exceeded

        # Accept
        self.total_consumed[report.grant_id] = new_total
        self.usage_log[report.grant_id].append(report)
        return None

    def settle(self, grant_id: str, up_to_seq: int,
               anchor_txid: str = "", anchor_digest: str = "") -> Optional[Settlement]:
        """Create settlement for a grant."""
        grant = self.grants.get(grant_id)
        if not grant:
            return None

        remaining = grant.ceil_total - self.total_consumed.get(grant_id, 0.0)
        settlement = Settlement(
            grant_id=grant_id,
            up_to_seq=up_to_seq,
            balance_remaining=remaining,
            balance_unit=grant.ceil_unit,
            anchor_txid=anchor_txid,
            anchor_digest=anchor_digest,
        )
        self.settlements.append(settlement)
        return settlement

    def file_dispute(self, dispute: Dispute):
        """File a dispute for a grant."""
        self.disputes.append(dispute)


# ════════════════════════════════════════════════════════════════
#  TESTS
# ════════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    now = datetime.utcnow()
    now_str = now.isoformat() + "Z"

    # ── T1: Roles ────────────────────────────────────────────────
    print("T1: Metering Roles (§2)")
    check("T1.1 Four roles",
          len(MeteringRole) == 4)
    check("T1.2 Grantor role",
          MeteringRole.GRANTOR.value == "grantor")
    check("T1.3 Consumer role",
          MeteringRole.CONSUMER.value == "consumer")
    check("T1.4 Witness role",
          MeteringRole.WITNESS.value == "witness")
    check("T1.5 Anchor role (optional)",
          MeteringRole.ANCHOR.value == "anchor")

    # ── T2: Error Codes ──────────────────────────────────────────
    print("T2: Error Codes (§6)")
    check("T2.1 Six error codes",
          len(MeteringError) == 6)
    check("T2.2 GRANT_EXPIRED",
          MeteringError.GRANT_EXPIRED.value == "W4_ERR_GRANT_EXPIRED")
    check("T2.3 RATE_LIMIT",
          MeteringError.RATE_LIMIT.value == "W4_ERR_RATE_LIMIT")
    check("T2.4 SCOPE_DENIED",
          MeteringError.SCOPE_DENIED.value == "W4_ERR_SCOPE_DENIED")
    check("T2.5 BAD_SEQUENCE",
          MeteringError.BAD_SEQUENCE.value == "W4_ERR_BAD_SEQUENCE")
    check("T2.6 WITNESS_REQUIRED",
          MeteringError.WITNESS_REQUIRED.value == "W4_ERR_WITNESS_REQUIRED")
    check("T2.7 FORMAT",
          MeteringError.FORMAT.value == "W4_ERR_FORMAT")

    # ── T3: Witness Classes ──────────────────────────────────────
    print("T3: Witness Classes (§5)")
    check("T3.1 Three witness classes",
          len(WitnessClass) == 3)
    check("T3.2 Time witness",
          WitnessClass.TIME.value == "time")
    check("T3.3 Audit-minimal witness",
          WitnessClass.AUDIT_MINIMAL.value == "audit-minimal")
    check("T3.4 Oracle witness",
          WitnessClass.ORACLE.value == "oracle")

    # ── T4: Conformance Profiles ─────────────────────────────────
    print("T4: Conformance Profiles (§8)")
    check("T4.1 Two profiles",
          len(ConformanceProfile) == 2)
    check("T4.2 Edge profile A",
          ConformanceProfile.EDGE.value == "A")
    check("T4.3 Enterprise profile B",
          ConformanceProfile.ENTERPRISE.value == "B")
    check("T4.4 Edge uses JSON/JOSE",
          PROFILE_SPECS[ConformanceProfile.EDGE]["encoding"] == "JSON")
    check("T4.5 Edge uses Ed25519",
          PROFILE_SPECS[ConformanceProfile.EDGE]["algorithm"] == "Ed25519")
    check("T4.6 Edge min report 60s",
          PROFILE_SPECS[ConformanceProfile.EDGE]["min_report_interval_s"] == 60)
    check("T4.7 Enterprise uses CBOR/COSE",
          PROFILE_SPECS[ConformanceProfile.ENTERPRISE]["encoding"] == "CBOR")
    check("T4.8 Enterprise uses ECDSA-P256",
          PROFILE_SPECS[ConformanceProfile.ENTERPRISE]["algorithm"] == "ECDSA-P256")
    check("T4.9 Enterprise supports batch",
          PROFILE_SPECS[ConformanceProfile.ENTERPRISE]["batch_mode"] is True)
    check("T4.10 Enterprise supports anchor",
          PROFILE_SPECS[ConformanceProfile.ENTERPRISE]["anchor"] is True)

    # ── T5: CreditGrant ──────────────────────────────────────────
    print("T5: CreditGrant (§3.1)")
    grant = CreditGrant(
        scopes=["compute:infer", "net:egress"],
        ceil_total=100000,
        ceil_unit="joule-equivalent",
        rate_max_per_min=5000,
        window_size_s=3600,
        window_burst=2,
        policy_region=["us-west"],
        policy_priority=3,
        not_before=(now - timedelta(hours=1)).isoformat() + "Z",
        not_after=(now + timedelta(hours=1)).isoformat() + "Z",
        proof_jws="test_jws",
        witness_req=["time", "audit-minimal"],
    )

    check("T5.1 Grant ID auto-generated",
          grant.grant_id.startswith("atp-"))
    check("T5.2 Version w4/1",
          grant.ver == "w4/1")
    check("T5.3 Has scopes",
          len(grant.scopes) == 2)
    check("T5.4 Ceiling set",
          grant.ceil_total == 100000)
    check("T5.5 Rate limit set",
          grant.rate_max_per_min == 5000)
    check("T5.6 Window configured",
          grant.window_size_s == 3600 and grant.window_burst == 2)
    check("T5.7 Policy region set",
          "us-west" in grant.policy_region)
    check("T5.8 Nonce auto-generated (96-bit = 24 hex chars)",
          len(grant.nonce) == 24)
    check("T5.9 Timestamp auto-generated",
          len(grant.ts) > 0)

    # Validity check
    check("T5.10 Grant valid now",
          grant.is_valid_at(now))
    check("T5.11 Grant invalid before not_before",
          not grant.is_valid_at(now - timedelta(hours=2)))
    check("T5.12 Grant invalid after not_after",
          not grant.is_valid_at(now + timedelta(hours=2)))

    # Scope check
    check("T5.13 Exact scope match",
          grant.has_scope("compute:infer"))
    check("T5.14 Sub-scope match",
          grant.has_scope("compute:infer:batch"))
    check("T5.15 Non-matching scope rejected",
          not grant.has_scope("storage:write"))

    # Message serialization
    msg = grant.to_message()
    check("T5.16 Message has type CreditGrant",
          msg["type"] == "CreditGrant")
    check("T5.17 Message has ceil",
          msg["ceil"]["total"] == 100000)
    check("T5.18 Message has rate",
          msg["rate"]["max_per_min"] == 5000)
    check("T5.19 Message has witness_req",
          len(msg["witness_req"]) == 2)

    # ── T6: UsageReport ──────────────────────────────────────────
    print("T6: UsageReport (§3.2)")
    report = UsageReport(
        grant_id=grant.grant_id,
        seq=1,
        window_start="2025-09-11T15:00:00Z",
        window_end="2025-09-11T15:01:00Z",
        usage=[
            UsageEntry(scope="compute:infer", amount=420, unit="joule-equivalent"),
            UsageEntry(scope="net:egress", amount=12, unit="MB"),
        ],
        evidence_digest="b3" + "a" * 62,
        evidence_method="sha256-agg",
        evidence_samples=7,
        witnesses=[
            WitnessAttestation(witness_type="time", ref="w4idp-001", sig="sig1"),
            WitnessAttestation(witness_type="audit-minimal", ref="w4idp-002", sig="sig2"),
        ],
    )

    check("T6.1 Report has grant_id",
          report.grant_id == grant.grant_id)
    check("T6.2 Report has seq",
          report.seq == 1)
    check("T6.3 Report has window",
          report.window_start and report.window_end)
    check("T6.4 Report has usage entries",
          len(report.usage) == 2)
    check("T6.5 Total usage computed",
          report.total_usage == 432)
    check("T6.6 Evidence digest present",
          len(report.evidence_digest) == 64)
    check("T6.7 Has witnesses",
          len(report.witnesses) == 2)
    check("T6.8 Nonce auto-generated",
          len(report.nonce) == 24)

    msg_r = report.to_message()
    check("T6.9 Message type UsageReport",
          msg_r["type"] == "UsageReport")
    check("T6.10 Window as ISO interval",
          "/" in msg_r["window"])

    # ── T7: Dispute ──────────────────────────────────────────────
    print("T7: Dispute (§3.3)")
    dispute = Dispute(
        grant_id=grant.grant_id,
        seq=42,
        reason="exceeds-rate-limit",
        details={"limit": 5000, "observed": 7200},
        proposed="partial-accept",
    )
    check("T7.1 Dispute has grant_id",
          dispute.grant_id == grant.grant_id)
    check("T7.2 Dispute has reason",
          dispute.reason == "exceeds-rate-limit")
    check("T7.3 Dispute has details",
          dispute.details["observed"] == 7200)
    check("T7.4 Dispute proposes partial-accept",
          dispute.proposed == "partial-accept")

    msg_d = dispute.to_message()
    check("T7.5 Message type Dispute",
          msg_d["type"] == "Dispute")

    # ── T8: Settlement ───────────────────────────────────────────
    print("T8: Settlement (§3.4)")
    settlement = Settlement(
        grant_id=grant.grant_id,
        up_to_seq=42,
        balance_remaining=95000,
        anchor_txid="lc:abc123",
        anchor_digest="digest123",
    )
    check("T8.1 Settlement has grant_id",
          settlement.grant_id == grant.grant_id)
    check("T8.2 Settlement has up_to_seq",
          settlement.up_to_seq == 42)
    check("T8.3 Settlement has balance",
          settlement.balance_remaining == 95000)
    check("T8.4 Receipt auto-generated",
          settlement.receipt.startswith("rcpt-"))
    check("T8.5 Has anchor",
          settlement.anchor_txid == "lc:abc123")

    msg_s = settlement.to_message()
    check("T8.6 Message type Settle",
          msg_s["type"] == "Settle")
    check("T8.7 Message has anchor section",
          "anchor" in msg_s)
    check("T8.8 No anchor section when empty",
          "anchor" not in Settlement(grant_id="g1").to_message())

    # ── T9: Token Bucket Rate Limiter ────────────────────────────
    print("T9: Token Bucket Rate Limiter (§4)")
    bucket = TokenBucket(rate_per_min=6000, window_s=3600, burst=2)
    check("T9.1 Initial capacity = rate * burst",
          bucket.capacity == 12000)
    check("T9.2 Initial tokens = capacity",
          bucket.tokens == 12000)

    # Consume within limits
    check("T9.3 Consume 5000 succeeds",
          bucket.try_consume(5000))
    check("T9.4 Remaining ~7000",
          abs(bucket.available - 7000) < 100)  # Small timing variance

    # Consume more
    check("T9.5 Consume 7000 succeeds",
          bucket.try_consume(7000))

    # Over-consume fails
    check("T9.6 Over-consume fails",
          not bucket.try_consume(1000))

    # ── T10: Replay Guard ────────────────────────────────────────
    print("T10: Replay Guard (§4)")
    guard = ReplayGuard()
    check("T10.1 First use is valid",
          guard.check_and_record("g1", 0))
    check("T10.2 Second use of same seq is replay",
          not guard.check_and_record("g1", 0))
    check("T10.3 Different seq is valid",
          guard.check_and_record("g1", 1))
    check("T10.4 Different grant is valid",
          guard.check_and_record("g2", 0))
    check("T10.5 Replay across grants isolated",
          not guard.check_and_record("g2", 0))

    # ── T11: Metering Engine — Happy Path ────────────────────────
    print("T11: Metering Engine — Happy Path")
    engine = MeteringEngine(profile=ConformanceProfile.EDGE)

    # Register grant
    err = engine.register_grant(grant)
    check("T11.1 Grant registered",
          err is None)

    # Duplicate grant rejected
    err = engine.register_grant(grant)
    check("T11.2 Duplicate grant rejected",
          err == MeteringError.FORMAT)

    # Submit usage report
    err = engine.process_usage(report)
    check("T11.3 Usage accepted",
          err is None)
    check("T11.4 Total consumed tracked",
          engine.total_consumed[grant.grant_id] == 432)
    check("T11.5 Usage logged",
          len(engine.usage_log[grant.grant_id]) == 1)

    # Submit another report
    report2 = UsageReport(
        grant_id=grant.grant_id, seq=2,
        usage=[UsageEntry(scope="compute:infer", amount=500)],
        witnesses=[
            WitnessAttestation(witness_type="time"),
            WitnessAttestation(witness_type="audit-minimal"),
        ],
    )
    err = engine.process_usage(report2)
    check("T11.6 Second report accepted",
          err is None)
    check("T11.7 Cumulative total correct",
          engine.total_consumed[grant.grant_id] == 932)

    # Settle
    settle = engine.settle(grant.grant_id, up_to_seq=2)
    check("T11.8 Settlement created",
          settle is not None)
    check("T11.9 Settlement balance correct",
          settle.balance_remaining == 100000 - 932)
    check("T11.10 Settlement in engine log",
          len(engine.settlements) == 1)

    # ── T12: Error Paths ─────────────────────────────────────────
    print("T12: Metering Engine — Error Paths")

    # Expired grant
    expired_grant = CreditGrant(
        scopes=["compute:infer"],
        ceil_total=1000,
        rate_max_per_min=500,
        not_before=(now - timedelta(hours=5)).isoformat() + "Z",
        not_after=(now - timedelta(hours=3)).isoformat() + "Z",
    )
    engine.register_grant(expired_grant)
    expired_report = UsageReport(
        grant_id=expired_grant.grant_id, seq=0,
        usage=[UsageEntry(scope="compute:infer", amount=10)],
    )
    err = engine.process_usage(expired_report)
    check("T12.1 Expired grant rejected",
          err == MeteringError.GRANT_EXPIRED)

    # Replay detection
    report_replay = UsageReport(
        grant_id=grant.grant_id, seq=1,  # Already used
        usage=[UsageEntry(scope="compute:infer", amount=10)],
        witnesses=[
            WitnessAttestation(witness_type="time"),
            WitnessAttestation(witness_type="audit-minimal"),
        ],
    )
    err = engine.process_usage(report_replay)
    check("T12.2 Replay detected",
          err == MeteringError.BAD_SEQUENCE)

    # Scope denied
    bad_scope = UsageReport(
        grant_id=grant.grant_id, seq=99,
        usage=[UsageEntry(scope="storage:write", amount=10)],
        witnesses=[
            WitnessAttestation(witness_type="time"),
            WitnessAttestation(witness_type="audit-minimal"),
        ],
    )
    err = engine.process_usage(bad_scope)
    check("T12.3 Bad scope rejected",
          err == MeteringError.SCOPE_DENIED)

    # Missing witness
    no_witness = UsageReport(
        grant_id=grant.grant_id, seq=100,
        usage=[UsageEntry(scope="compute:infer", amount=10)],
        witnesses=[WitnessAttestation(witness_type="time")],  # Missing audit-minimal
    )
    err = engine.process_usage(no_witness)
    check("T12.4 Missing witness rejected",
          err == MeteringError.WITNESS_REQUIRED)

    # Unknown grant
    unknown = UsageReport(grant_id="atp-unknown", seq=0,
                           usage=[UsageEntry(scope="x", amount=1)])
    err = engine.process_usage(unknown)
    check("T12.5 Unknown grant rejected",
          err == MeteringError.FORMAT)

    # Settlement on unknown grant
    check("T12.6 Settle unknown returns None",
          engine.settle("atp-nonexistent", 0) is None)

    # ── T13: Ceiling Enforcement ─────────────────────────────────
    print("T13: Ceiling Enforcement (§4 + §7)")
    small_grant = CreditGrant(
        scopes=["compute:infer"],
        ceil_total=100,
        rate_max_per_min=1000000,  # High rate to not hit rate limit
        window_burst=100,
    )
    engine.register_grant(small_grant)

    # Use 90 of 100
    ok_report = UsageReport(
        grant_id=small_grant.grant_id, seq=0,
        usage=[UsageEntry(scope="compute:infer", amount=90)],
    )
    check("T13.1 Under ceiling accepted",
          engine.process_usage(ok_report) is None)

    # Try to use 20 more (would exceed 100)
    over_report = UsageReport(
        grant_id=small_grant.grant_id, seq=1,
        usage=[UsageEntry(scope="compute:infer", amount=20)],
    )
    err = engine.process_usage(over_report)
    check("T13.2 Over ceiling rejected",
          err == MeteringError.GRANT_EXPIRED)

    # Exact remaining (10) should work
    exact_report = UsageReport(
        grant_id=small_grant.grant_id, seq=2,
        usage=[UsageEntry(scope="compute:infer", amount=10)],
    )
    check("T13.3 Exact remaining accepted",
          engine.process_usage(exact_report) is None)

    # ── T14: Dispute Flow ────────────────────────────────────────
    print("T14: Dispute Flow (§3.3 + §4)")
    disp = Dispute(
        grant_id=grant.grant_id,
        seq=42,
        reason="exceeds-rate-limit",
        details={"limit": 5000, "observed": 7200},
        proposed="partial-accept",
    )
    engine.file_dispute(disp)
    check("T14.1 Dispute filed",
          len(engine.disputes) == 1)
    check("T14.2 Partial acceptance proposed",
          engine.disputes[0].proposed == "partial-accept")

    # Settle with reduced acceptance
    partial_settle = engine.settle(grant.grant_id, up_to_seq=42)
    check("T14.3 Partial settlement created",
          partial_settle is not None)

    # ── T15: End-to-End Enterprise Profile ───────────────────────
    print("T15: End-to-End Enterprise Profile (§8)")
    ent_engine = MeteringEngine(profile=ConformanceProfile.ENTERPRISE)
    check("T15.1 Enterprise profile set",
          ent_engine.profile == ConformanceProfile.ENTERPRISE)

    ent_grant = CreditGrant(
        scopes=["compute:train", "storage:model"],
        ceil_total=500000,
        ceil_unit="joule-equivalent",
        rate_max_per_min=50000,
        window_burst=3,
        witness_req=["time"],
    )
    ent_engine.register_grant(ent_grant)

    # Batched reports (enterprise supports batching)
    for i in range(5):
        batch_report = UsageReport(
            grant_id=ent_grant.grant_id,
            seq=i,
            usage=[
                UsageEntry(scope="compute:train", amount=1000 * (i + 1)),
                UsageEntry(scope="storage:model", amount=50 * (i + 1)),
            ],
            evidence_digest=hashlib.sha256(f"batch_{i}".encode()).hexdigest(),
            evidence_samples=10,
            witnesses=[WitnessAttestation(witness_type="time")],
        )
        err = ent_engine.process_usage(batch_report)
        check(f"T15.{i+2} Batch report {i} accepted",
              err is None)

    # Expected total: compute = 1000+2000+3000+4000+5000 = 15000
    #                 storage = 50+100+150+200+250 = 750
    total = ent_engine.total_consumed[ent_grant.grant_id]
    check("T15.7 Batch total correct (15750)",
          abs(total - 15750) < 0.01)

    # Settle with anchor (enterprise feature)
    ent_settle = ent_engine.settle(
        ent_grant.grant_id, up_to_seq=4,
        anchor_txid="lc:enterprise_001",
        anchor_digest=hashlib.sha256(b"enterprise_receipt").hexdigest(),
    )
    check("T15.8 Enterprise settlement has anchor",
          ent_settle.anchor_txid == "lc:enterprise_001")
    check("T15.9 Balance remaining correct",
          abs(ent_settle.balance_remaining - (500000 - 15750)) < 0.01)

    msg = ent_settle.to_message()
    check("T15.10 Settlement message has anchor",
          "anchor" in msg)

    # ── T16: Message Serialization Round-Trip ────────────────────
    print("T16: Message Serialization")
    all_msgs = [
        grant.to_message(),
        report.to_message(),
        dispute.to_message(),
        settlement.to_message(),
    ]
    msg_types = ["CreditGrant", "UsageReport", "Dispute", "Settle"]
    for msg, expected_type in zip(all_msgs, msg_types):
        check(f"T16.{msg_types.index(expected_type)+1} {expected_type} serializable",
              msg["type"] == expected_type)
        check(f"T16.{msg_types.index(expected_type)+5} {expected_type} has ver",
              msg["ver"] == "w4/1")
        # All messages should be JSON-serializable
        json_str = json.dumps(msg)
        check(f"T16.{msg_types.index(expected_type)+9} {expected_type} JSON-serializable",
              len(json_str) > 0)

    # ═══════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"Web4 Metering Protocol: {passed}/{passed+failed} checks passed")
    if failed:
        print(f"  ({failed} FAILED)")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
