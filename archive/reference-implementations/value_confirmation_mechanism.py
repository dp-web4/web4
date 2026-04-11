"""
Value Confirmation Mechanism (VCM) — Reference Implementation

The missing piece of the ATP/ADP cycle: ADP→ATP recharge gated by
recipient-attested value confirmation. Value is not self-declared by
a producer — it is certified by the actual beneficiaries.

Core principle: You cannot attest your own value. Only recipients can.

VCM sits after Settle (metering protocol end) and before next CreditGrant:
  CreditGrant → UsageReport → Settle → [VCM] → Recharge → CreditGrant

Exchange rate formula:
  certified_v3 = weighted_mean(attestations, weights=t3*expertise)
  exchange_rate = 0.8 + 0.7 * certified_v3   # maps [0,1] → [0.8, 1.5]
  atp_recharged = adp_amount * exchange_rate

Checks: 65
"""
from __future__ import annotations
import hashlib
import hmac
import math
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


# ─── Core Types ───────────────────────────────────────────────────────────────

class AttestationStatus(Enum):
    PENDING = auto()
    SUBMITTED = auto()
    EXPIRED = auto()
    REJECTED = auto()


class VCMPhase(Enum):
    COLLECTION = auto()     # Gathering attestations from recipients
    AGGREGATION = auto()    # Computing weighted consensus
    CERTIFICATION = auto()  # Issuing exchange rate
    RECHARGE = auto()       # Converting ADP → ATP
    COMPLETE = auto()


class FraudType(Enum):
    SELF_ATTESTATION = auto()
    COLLUSION = auto()
    SYBIL_ATTESTATION = auto()
    SCORE_INFLATION = auto()
    RECIPROCAL_INFLATION = auto()


@dataclass
class V3Assessment:
    """Recipient's assessment of value received along V3 dimensions."""
    valuation: float    # Subjective worth — did this benefit me? [0, 1]
    veracity: float     # Objective accuracy — is it truthful? [0, 1]
    validity: float     # Confirmed transfer — did value arrive? [0, 1]

    def composite(self) -> float:
        return (self.valuation + self.veracity + self.validity) / 3.0

    def __post_init__(self):
        for dim in ('valuation', 'veracity', 'validity'):
            v = getattr(self, dim)
            if not (0.0 <= v <= 1.0):
                object.__setattr__(self, dim, max(0.0, min(1.0, v)))


@dataclass
class T3Score:
    """Trust tensor scores for weighting attestations."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0


@dataclass
class Recipient:
    """An entity who received value and can attest to it."""
    entity_id: str
    t3: T3Score
    domain_expertise: float = 0.5   # [0, 1] — domain relevance
    attestation_history: List[float] = field(default_factory=list)

    def weight(self) -> float:
        """Attestation weight = T3 composite × domain expertise."""
        return self.t3.composite() * self.domain_expertise

    def credibility(self) -> float:
        """Long-term credibility based on attestation consistency."""
        if len(self.attestation_history) < 2:
            return 1.0
        # Variance in past attestations — low variance = consistent = credible
        mean = sum(self.attestation_history) / len(self.attestation_history)
        variance = sum((x - mean) ** 2 for x in self.attestation_history) / len(self.attestation_history)
        return max(0.1, 1.0 - min(variance * 5.0, 0.9))


@dataclass
class Attestation:
    """A single recipient's attestation of value received."""
    attestation_id: str
    recipient_id: str
    producer_id: str
    adp_proof_id: str
    v3: V3Assessment
    weight: float
    timestamp: float
    status: AttestationStatus = AttestationStatus.SUBMITTED
    signature: bytes = b""

    def sign(self, key: bytes) -> None:
        msg = f"{self.attestation_id}:{self.recipient_id}:{self.producer_id}:{self.v3.composite():.6f}"
        self.signature = hmac.new(key, msg.encode(), hashlib.sha256).digest()

    def verify(self, key: bytes) -> bool:
        msg = f"{self.attestation_id}:{self.recipient_id}:{self.producer_id}:{self.v3.composite():.6f}"
        expected = hmac.new(key, msg.encode(), hashlib.sha256).digest()
        return hmac.compare_digest(self.signature, expected)


@dataclass
class ADPProof:
    """Discharge proof — what work was done and how much ADP was spent."""
    adp_id: str
    grant_id: str
    producer_id: str
    discharged_amount: float
    remaining: float
    evidence_digest: str
    quality_score: float = 0.0
    timestamp: float = 0.0


@dataclass
class VCMResult:
    """Result of the value confirmation process."""
    adp_proof_id: str
    producer_id: str
    certified_v3: float
    exchange_rate: float
    adp_amount: float
    atp_recharged: float
    attestation_count: int
    quorum_met: bool
    t3_delta: Dict[str, float] = field(default_factory=dict)
    v3_delta: Dict[str, float] = field(default_factory=dict)
    fraud_flags: List[FraudType] = field(default_factory=list)


@dataclass
class FraudAlert:
    """Alert raised when attestation fraud is detected."""
    fraud_type: FraudType
    entity_ids: List[str]
    severity: float     # [0, 1]
    evidence: str


# ─── VCM Engine ───────────────────────────────────────────────────────────────

class ValueConfirmationEngine:
    """
    Core VCM engine: collects attestations, detects fraud,
    aggregates trust-weighted consensus, computes exchange rate.
    """

    # Exchange rate bounds from whitepaper §3.1.5
    MIN_RATE = 0.8
    MAX_RATE = 1.5

    def __init__(self, min_quorum: int = 1, quorum_fraction: float = 0.5,
                 attestation_timeout: float = 86400.0,  # 24h
                 fraud_threshold: float = 0.3):
        self.min_quorum = max(1, min_quorum)
        self.quorum_fraction = quorum_fraction
        self.attestation_timeout = attestation_timeout
        self.fraud_threshold = fraud_threshold
        self.pending: Dict[str, List[Attestation]] = {}  # adp_id → attestations
        self.results: Dict[str, VCMResult] = {}
        self.fraud_alerts: List[FraudAlert] = []
        self._signing_key = secrets.token_bytes(32)

    def request_attestations(self, adp_proof: ADPProof,
                              recipients: List[Recipient]) -> str:
        """Phase 1: Request attestations from recipients for an ADP proof."""
        self.pending[adp_proof.adp_id] = []
        return adp_proof.adp_id

    def submit_attestation(self, adp_id: str, recipient: Recipient,
                            v3: V3Assessment, now: Optional[float] = None) -> Optional[Attestation]:
        """Phase 1 continued: A recipient submits their V3 attestation."""
        if adp_id not in self.pending:
            return None

        att = Attestation(
            attestation_id=f"att_{secrets.token_hex(8)}",
            recipient_id=recipient.entity_id,
            producer_id="",  # filled by certify
            adp_proof_id=adp_id,
            v3=v3,
            weight=recipient.weight(),
            timestamp=now or time.time(),
        )
        att.sign(self._signing_key)
        self.pending[adp_id].append(att)
        recipient.attestation_history.append(v3.composite())
        return att

    def check_quorum(self, adp_id: str, total_recipients: int) -> bool:
        """Check if enough attestations have been collected."""
        if adp_id not in self.pending:
            return False
        count = len(self.pending[adp_id])
        required = max(self.min_quorum, math.ceil(total_recipients * self.quorum_fraction))
        return count >= required

    def detect_fraud(self, adp_id: str, adp_proof: ADPProof,
                      recipients: Dict[str, Recipient]) -> List[FraudAlert]:
        """Phase 2: Detect attestation fraud before aggregation."""
        alerts = []
        attestations = self.pending.get(adp_id, [])

        # 1. Self-attestation: producer cannot attest own value
        for att in attestations:
            if att.recipient_id == adp_proof.producer_id:
                alerts.append(FraudAlert(
                    FraudType.SELF_ATTESTATION,
                    [att.recipient_id],
                    1.0,
                    f"Producer {adp_proof.producer_id} attempted self-attestation"
                ))

        # 2. Sybil attestation: multiple low-trust attestors with similar scores
        if len(attestations) >= 3:
            low_trust = [a for a in attestations
                         if a.recipient_id in recipients
                         and recipients[a.recipient_id].t3.composite() < 0.3]
            if len(low_trust) >= 2:
                scores = [a.v3.composite() for a in low_trust]
                if len(scores) >= 2:
                    mean_s = sum(scores) / len(scores)
                    variance = sum((s - mean_s) ** 2 for s in scores) / len(scores)
                    if variance < 0.01:  # suspiciously uniform
                        alerts.append(FraudAlert(
                            FraudType.SYBIL_ATTESTATION,
                            [a.recipient_id for a in low_trust],
                            0.7,
                            f"Low-trust cluster with variance={variance:.4f}"
                        ))

        # 3. Score inflation: attestation much higher than historical average
        for att in attestations:
            if att.recipient_id in recipients:
                r = recipients[att.recipient_id]
                if len(r.attestation_history) >= 5:
                    hist_mean = sum(r.attestation_history[:-1]) / (len(r.attestation_history) - 1)
                    if att.v3.composite() > hist_mean + 0.4:
                        alerts.append(FraudAlert(
                            FraudType.SCORE_INFLATION,
                            [att.recipient_id],
                            0.5,
                            f"Score {att.v3.composite():.3f} >> historical mean {hist_mean:.3f}"
                        ))

        # 4. Reciprocal inflation: A attests B high, B attests A high in recent history
        # (Would need cross-VCM tracking — simplified here)

        self.fraud_alerts.extend(alerts)
        return alerts

    def aggregate_attestations(self, adp_id: str,
                                exclude_ids: Optional[List[str]] = None) -> Tuple[float, float]:
        """Phase 2: Compute trust-weighted V3 consensus.

        Returns: (certified_v3, total_weight)
        """
        attestations = self.pending.get(adp_id, [])
        exclude = set(exclude_ids or [])

        total_weight = 0.0
        weighted_sum = 0.0

        for att in attestations:
            if att.recipient_id in exclude:
                continue
            if att.status == AttestationStatus.REJECTED:
                continue
            w = att.weight
            weighted_sum += att.v3.composite() * w
            total_weight += w

        if total_weight == 0:
            return 0.0, 0.0

        certified_v3 = weighted_sum / total_weight
        return certified_v3, total_weight

    def compute_exchange_rate(self, certified_v3: float) -> float:
        """Phase 3: Map certified V3 to exchange rate.

        Formula: rate = 0.8 + 0.7 * certified_v3
        Maps [0, 1] → [0.8, 1.5]
        """
        rate = self.MIN_RATE + (self.MAX_RATE - self.MIN_RATE) * certified_v3
        return max(self.MIN_RATE, min(self.MAX_RATE, rate))

    def certify_value(self, adp_proof: ADPProof,
                       recipients: Dict[str, Recipient]) -> VCMResult:
        """Full VCM pipeline: fraud detection → aggregation → rate → recharge."""
        adp_id = adp_proof.adp_id

        # Detect and exclude fraudulent attestations
        fraud_alerts = self.detect_fraud(adp_id, adp_proof, recipients)
        exclude = set()
        fraud_flags = []
        for alert in fraud_alerts:
            if alert.severity >= self.fraud_threshold:
                exclude.update(alert.entity_ids)
                fraud_flags.append(alert.fraud_type)
                # Mark excluded attestations as rejected
                for att in self.pending.get(adp_id, []):
                    if att.recipient_id in alert.entity_ids:
                        att.status = AttestationStatus.REJECTED

        # Aggregate
        certified_v3, total_weight = self.aggregate_attestations(adp_id, list(exclude))

        # Quorum check (after exclusions)
        valid_count = sum(1 for a in self.pending.get(adp_id, [])
                         if a.status != AttestationStatus.REJECTED
                         and a.recipient_id not in exclude)
        total_expected = len(recipients) - len(exclude & set(recipients.keys()))
        quorum_met = valid_count >= max(self.min_quorum,
                                        math.ceil(total_expected * self.quorum_fraction))

        # Exchange rate
        exchange_rate = self.compute_exchange_rate(certified_v3) if quorum_met else self.MIN_RATE

        # ATP recharge amount
        atp_recharged = adp_proof.discharged_amount * exchange_rate

        # T3/V3 deltas for producer
        t3_delta = {"training": 0.01 * (certified_v3 - 0.5)}
        v3_delta = {"valuation": 0.02 * (certified_v3 - 0.5)}

        result = VCMResult(
            adp_proof_id=adp_id,
            producer_id=adp_proof.producer_id,
            certified_v3=certified_v3,
            exchange_rate=exchange_rate,
            adp_amount=adp_proof.discharged_amount,
            atp_recharged=atp_recharged,
            attestation_count=valid_count,
            quorum_met=quorum_met,
            t3_delta=t3_delta,
            v3_delta=v3_delta,
            fraud_flags=fraud_flags,
        )
        self.results[adp_id] = result
        return result


# ─── Multi-Party Attestation Protocol ─────────────────────────────────────────

class AttestationProtocol:
    """
    Structured protocol for collecting attestations with deadlines,
    reminders, and dispute handling.
    """

    def __init__(self, engine: ValueConfirmationEngine, deadline_hours: float = 24.0):
        self.engine = engine
        self.deadline_hours = deadline_hours
        self.sessions: Dict[str, AttestationSession] = {}

    def open_session(self, adp_proof: ADPProof,
                      recipients: List[Recipient]) -> AttestationSession:
        session = AttestationSession(
            session_id=f"vcm_{secrets.token_hex(8)}",
            adp_proof=adp_proof,
            recipients={r.entity_id: r for r in recipients},
            deadline=time.time() + self.deadline_hours * 3600,
            phase=VCMPhase.COLLECTION,
        )
        self.sessions[session.session_id] = session
        self.engine.request_attestations(adp_proof, recipients)
        return session

    def submit(self, session_id: str, recipient_id: str,
               v3: V3Assessment, now: Optional[float] = None) -> Optional[Attestation]:
        session = self.sessions.get(session_id)
        if not session or session.phase != VCMPhase.COLLECTION:
            return None
        recipient = session.recipients.get(recipient_id)
        if not recipient:
            return None
        return self.engine.submit_attestation(
            session.adp_proof.adp_id, recipient, v3, now)

    def finalize(self, session_id: str) -> Optional[VCMResult]:
        session = self.sessions.get(session_id)
        if not session:
            return None

        session.phase = VCMPhase.AGGREGATION
        result = self.engine.certify_value(session.adp_proof, session.recipients)
        session.phase = VCMPhase.COMPLETE
        session.result = result
        return result


@dataclass
class AttestationSession:
    session_id: str
    adp_proof: ADPProof
    recipients: Dict[str, Recipient]
    deadline: float
    phase: VCMPhase
    result: Optional[VCMResult] = None


# ─── Quality Multiplier Curves ────────────────────────────────────────────────

class QualityMultiplier:
    """
    Maps certified V3 to exchange rate with configurable curves.
    The whitepaper says 0.8–1.5× but doesn't specify the curve shape.
    """

    @staticmethod
    def linear(v3: float) -> float:
        """Linear mapping: rate = 0.8 + 0.7 * v3."""
        return 0.8 + 0.7 * v3

    @staticmethod
    def sigmoid(v3: float, steepness: float = 10.0) -> float:
        """Sigmoid: rewards differentiation in the middle range."""
        x = steepness * (v3 - 0.5)
        s = 1.0 / (1.0 + math.exp(-x))
        return 0.8 + 0.7 * s

    @staticmethod
    def threshold(v3: float, threshold: float = 0.5) -> float:
        """Step function: below threshold = 0.8×, above = 1.5×."""
        return 1.5 if v3 >= threshold else 0.8

    @staticmethod
    def quadratic(v3: float) -> float:
        """Quadratic: generous to high performers, harsh on low."""
        return 0.8 + 0.7 * v3 * v3


# ─── Dispute Resolution ──────────────────────────────────────────────────────

class DisputeReason(Enum):
    UNFAIR_ASSESSMENT = auto()
    MISSING_RECIPIENT = auto()
    COERCED_ATTESTATION = auto()
    WRONG_EXCHANGE_RATE = auto()


@dataclass
class Dispute:
    dispute_id: str
    vcm_result_id: str
    producer_id: str
    reason: DisputeReason
    evidence: str
    resolved: bool = False
    upheld: bool = False
    revised_rate: Optional[float] = None


class DisputeResolver:
    """Handles producer disputes of VCM results."""

    def __init__(self):
        self.disputes: List[Dispute] = []

    def file_dispute(self, result: VCMResult, reason: DisputeReason,
                      evidence: str) -> Dispute:
        dispute = Dispute(
            dispute_id=f"disp_{secrets.token_hex(8)}",
            vcm_result_id=result.adp_proof_id,
            producer_id=result.producer_id,
            reason=reason,
            evidence=evidence,
        )
        self.disputes.append(dispute)
        return dispute

    def resolve(self, dispute: Dispute, upheld: bool,
                revised_rate: Optional[float] = None) -> Dispute:
        dispute.resolved = True
        dispute.upheld = upheld
        if upheld and revised_rate is not None:
            dispute.revised_rate = max(0.8, min(1.5, revised_rate))
        return dispute


# ─── ATP Recharge Integration ─────────────────────────────────────────────────

@dataclass
class ATPAccount:
    """Simplified ATP account for VCM integration."""
    entity_id: str
    balance: float = 0.0
    total_recharged: float = 0.0
    total_discharged: float = 0.0
    adp_pool: float = 0.0


class VCMRechargeGate:
    """
    Gates ATP recharge through VCM certification.
    Replaces unconditional recharge with attestation-gated recharge.
    """

    def __init__(self, engine: ValueConfirmationEngine):
        self.engine = engine
        self.accounts: Dict[str, ATPAccount] = {}
        self.recharge_log: List[Dict] = []

    def register(self, entity_id: str, initial_atp: float = 0.0) -> ATPAccount:
        acct = ATPAccount(entity_id=entity_id, balance=initial_atp)
        self.accounts[entity_id] = acct
        return acct

    def discharge(self, entity_id: str, amount: float) -> Optional[ADPProof]:
        """Spend ATP → create ADP proof for later VCM recharge."""
        acct = self.accounts.get(entity_id)
        if not acct or acct.balance < amount:
            return None
        acct.balance -= amount
        acct.adp_pool += amount
        acct.total_discharged += amount

        proof = ADPProof(
            adp_id=f"adp_{secrets.token_hex(8)}",
            grant_id=f"grant_{secrets.token_hex(4)}",
            producer_id=entity_id,
            discharged_amount=amount,
            remaining=acct.adp_pool,
            evidence_digest=hashlib.sha256(
                f"{entity_id}:{amount}:{time.time()}".encode()
            ).hexdigest(),
            timestamp=time.time(),
        )
        return proof

    def recharge_via_vcm(self, result: VCMResult) -> float:
        """Apply VCM result to recharge ATP."""
        acct = self.accounts.get(result.producer_id)
        if not acct:
            return 0.0
        if not result.quorum_met:
            return 0.0

        # Deduct from ADP pool
        actual_adp = min(result.adp_amount, acct.adp_pool)
        atp_amount = actual_adp * result.exchange_rate
        acct.adp_pool -= actual_adp
        acct.balance += atp_amount
        acct.total_recharged += atp_amount

        self.recharge_log.append({
            "entity_id": result.producer_id,
            "adp_spent": actual_adp,
            "atp_recharged": atp_amount,
            "exchange_rate": result.exchange_rate,
            "certified_v3": result.certified_v3,
            "attestation_count": result.attestation_count,
        })
        return atp_amount


# ─── Batch VCM Processing ────────────────────────────────────────────────────

class BatchVCM:
    """Process multiple VCM certifications efficiently."""

    def __init__(self, engine: ValueConfirmationEngine):
        self.engine = engine

    def process_batch(self, proofs: List[ADPProof],
                       recipient_map: Dict[str, List[Recipient]],
                       attestation_map: Dict[str, List[Tuple[str, V3Assessment]]]) -> List[VCMResult]:
        """Process a batch of ADP proofs through VCM.

        attestation_map: adp_id → [(recipient_id, V3Assessment), ...]
        """
        results = []
        for proof in proofs:
            recipients = recipient_map.get(proof.adp_id, [])
            self.engine.request_attestations(proof, recipients)

            # Submit attestations
            for r_id, v3 in attestation_map.get(proof.adp_id, []):
                r = next((r for r in recipients if r.entity_id == r_id), None)
                if r:
                    self.engine.submit_attestation(proof.adp_id, r, v3)

            # Certify
            r_map = {r.entity_id: r for r in recipients}
            result = self.engine.certify_value(proof, r_map)
            results.append(result)
        return results


# ─── Attestation Audit Trail ──────────────────────────────────────────────────

@dataclass
class AuditEntry:
    entry_id: str
    adp_id: str
    phase: VCMPhase
    data_hash: str
    prev_hash: str
    timestamp: float


class VCMAuditTrail:
    """Hash-chained audit trail for VCM decisions."""

    def __init__(self):
        self.entries: List[AuditEntry] = []

    def _hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def record(self, adp_id: str, phase: VCMPhase, data: str) -> AuditEntry:
        prev = self.entries[-1].data_hash if self.entries else "genesis"
        entry = AuditEntry(
            entry_id=f"audit_{len(self.entries)}",
            adp_id=adp_id,
            phase=phase,
            data_hash=self._hash(f"{data}:{prev}"),
            prev_hash=prev,
            timestamp=time.time(),
        )
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        """Verify hash chain integrity."""
        for i in range(1, len(self.entries)):
            if self.entries[i].prev_hash != self.entries[i - 1].data_hash:
                return False
        return True


# ─── Checks ──────────────────────────────────────────────────────────────────

def run_checks():
    checks = []
    t0 = time.time()

    # ── S1: V3 Assessment ─────────────────────────────────────────────────
    v3 = V3Assessment(0.8, 0.9, 0.7)
    checks.append(("s1_v3_composite", abs(v3.composite() - 0.8) < 0.01))
    checks.append(("s1_v3_clamped", V3Assessment(1.5, -0.1, 0.5).valuation == 1.0))
    checks.append(("s1_v3_clamped_low", V3Assessment(1.5, -0.1, 0.5).veracity == 0.0))

    t3 = T3Score(0.8, 0.7, 0.9)
    checks.append(("s1_t3_composite", abs(t3.composite() - 0.8) < 0.01))

    r = Recipient("r1", t3, domain_expertise=0.6)
    checks.append(("s1_weight", abs(r.weight() - 0.8 * 0.6) < 0.01))
    checks.append(("s1_credibility_new", r.credibility() == 1.0))

    # ── S2: Attestation Signing ───────────────────────────────────────────
    key = secrets.token_bytes(32)
    att = Attestation("a1", "r1", "p1", "adp1", v3, 0.5, time.time())
    att.sign(key)
    checks.append(("s2_signed", len(att.signature) == 32))
    checks.append(("s2_verify_ok", att.verify(key)))
    checks.append(("s2_verify_bad", not att.verify(b"wrong" * 8)))

    # ── S3: Exchange Rate ─────────────────────────────────────────────────
    engine = ValueConfirmationEngine()
    checks.append(("s3_rate_zero", abs(engine.compute_exchange_rate(0.0) - 0.8) < 0.01))
    checks.append(("s3_rate_one", abs(engine.compute_exchange_rate(1.0) - 1.5) < 0.01))
    checks.append(("s3_rate_half", abs(engine.compute_exchange_rate(0.5) - 1.15) < 0.01))
    checks.append(("s3_rate_clamped_low", engine.compute_exchange_rate(-1.0) == 0.8))
    checks.append(("s3_rate_clamped_high", engine.compute_exchange_rate(2.0) == 1.5))

    # ── S4: Quality Multiplier Curves ─────────────────────────────────────
    checks.append(("s4_linear", abs(QualityMultiplier.linear(0.5) - 1.15) < 0.01))
    sig_mid = QualityMultiplier.sigmoid(0.5)
    checks.append(("s4_sigmoid_mid", abs(sig_mid - 1.15) < 0.01))
    sig_high = QualityMultiplier.sigmoid(0.9)
    checks.append(("s4_sigmoid_high", sig_high > QualityMultiplier.linear(0.9) - 0.05))
    checks.append(("s4_threshold_low", QualityMultiplier.threshold(0.3) == 0.8))
    checks.append(("s4_threshold_high", QualityMultiplier.threshold(0.7) == 1.5))
    checks.append(("s4_quadratic", QualityMultiplier.quadratic(1.0) == 1.5))
    checks.append(("s4_quadratic_low", QualityMultiplier.quadratic(0.0) == 0.8))

    # ── S5: Basic VCM Flow ────────────────────────────────────────────────
    engine2 = ValueConfirmationEngine(min_quorum=1)
    adp = ADPProof("adp_test", "grant_1", "producer_A", 100.0, 0.0,
                    "evidence_hash", timestamp=time.time())
    recipients = [
        Recipient("r1", T3Score(0.8, 0.8, 0.8), 0.7),
        Recipient("r2", T3Score(0.6, 0.6, 0.6), 0.5),
        Recipient("r3", T3Score(0.9, 0.9, 0.9), 0.9),
    ]
    engine2.request_attestations(adp, recipients)

    engine2.submit_attestation("adp_test", recipients[0], V3Assessment(0.9, 0.8, 0.85))
    engine2.submit_attestation("adp_test", recipients[1], V3Assessment(0.7, 0.6, 0.65))
    engine2.submit_attestation("adp_test", recipients[2], V3Assessment(0.95, 0.9, 0.92))

    checks.append(("s5_quorum_met", engine2.check_quorum("adp_test", 3)))

    r_map = {r.entity_id: r for r in recipients}
    result = engine2.certify_value(adp, r_map)
    checks.append(("s5_certified", result.quorum_met))
    checks.append(("s5_v3_reasonable", 0.7 < result.certified_v3 < 1.0))
    checks.append(("s5_rate_above_1", result.exchange_rate > 1.0))
    checks.append(("s5_atp_recharged", result.atp_recharged > 100.0))  # rate > 1.0
    checks.append(("s5_attestation_count", result.attestation_count == 3))
    checks.append(("s5_no_fraud", len(result.fraud_flags) == 0))

    # ── S6: Fraud Detection ───────────────────────────────────────────────
    engine3 = ValueConfirmationEngine(min_quorum=1)
    adp2 = ADPProof("adp_fraud", "grant_2", "producer_B", 50.0, 0.0,
                     "evidence_2", timestamp=time.time())
    # Producer tries to attest own value
    self_attester = Recipient("producer_B", T3Score(0.5, 0.5, 0.5), 0.5)
    honest_r = Recipient("honest_r", T3Score(0.8, 0.8, 0.8), 0.7)
    engine3.request_attestations(adp2, [self_attester, honest_r])
    engine3.submit_attestation("adp_fraud", self_attester, V3Assessment(1.0, 1.0, 1.0))
    engine3.submit_attestation("adp_fraud", honest_r, V3Assessment(0.6, 0.5, 0.55))

    r_map2 = {"producer_B": self_attester, "honest_r": honest_r}
    result2 = engine3.certify_value(adp2, r_map2)
    checks.append(("s6_self_attest_detected", FraudType.SELF_ATTESTATION in result2.fraud_flags))
    # Self-attester excluded, only honest_r counts
    checks.append(("s6_self_excluded", result2.attestation_count == 1))

    # Sybil attestation: multiple low-trust with uniform scores
    engine4 = ValueConfirmationEngine(min_quorum=1)
    adp3 = ADPProof("adp_sybil", "grant_3", "producer_C", 30.0, 0.0,
                     "evidence_3", timestamp=time.time())
    sybils = [Recipient(f"sybil_{i}", T3Score(0.2, 0.2, 0.2), 0.3) for i in range(4)]
    honest = Recipient("honest", T3Score(0.8, 0.8, 0.8), 0.7)
    all_r = sybils + [honest]
    engine4.request_attestations(adp3, all_r)
    for s in sybils:
        engine4.submit_attestation("adp_sybil", s, V3Assessment(0.95, 0.95, 0.95))
    engine4.submit_attestation("adp_sybil", honest, V3Assessment(0.5, 0.4, 0.45))
    r_map3 = {r.entity_id: r for r in all_r}
    result3 = engine4.certify_value(adp3, r_map3)
    checks.append(("s6_sybil_detected", FraudType.SYBIL_ATTESTATION in result3.fraud_flags))

    # ── S7: Quorum Mechanics ──────────────────────────────────────────────
    engine5 = ValueConfirmationEngine(min_quorum=2, quorum_fraction=0.5)
    adp4 = ADPProof("adp_quorum", "grant_4", "prod_D", 80.0, 0.0, "ev_4")
    r_q = Recipient("rq1", T3Score(0.7, 0.7, 0.7), 0.6)
    engine5.request_attestations(adp4, [r_q])
    engine5.submit_attestation("adp_quorum", r_q, V3Assessment(0.8, 0.7, 0.75))
    checks.append(("s7_quorum_1_of_4", not engine5.check_quorum("adp_quorum", 4)))
    r_q2 = Recipient("rq2", T3Score(0.6, 0.6, 0.6), 0.5)
    engine5.submit_attestation("adp_quorum", r_q2, V3Assessment(0.7, 0.6, 0.65))
    checks.append(("s7_quorum_2_of_4", engine5.check_quorum("adp_quorum", 4)))

    # Missing quorum → min rate applied
    engine5b = ValueConfirmationEngine(min_quorum=5)
    adp4b = ADPProof("adp_noquorum", "grant_4b", "prod_E", 50.0, 0.0, "ev_4b")
    r_sparse = Recipient("rs1", T3Score(0.7, 0.7, 0.7), 0.6)
    engine5b.request_attestations(adp4b, [r_sparse])
    engine5b.submit_attestation("adp_noquorum", r_sparse, V3Assessment(0.9, 0.9, 0.9))
    res_nq = engine5b.certify_value(adp4b, {"rs1": r_sparse})
    checks.append(("s7_no_quorum_min_rate", abs(res_nq.exchange_rate - 0.8) < 0.01))
    checks.append(("s7_no_quorum_flag", not res_nq.quorum_met))

    # ── S8: Attestation Protocol ──────────────────────────────────────────
    engine6 = ValueConfirmationEngine(min_quorum=1)
    protocol = AttestationProtocol(engine6, deadline_hours=24.0)
    adp5 = ADPProof("adp_proto", "grant_5", "prod_F", 200.0, 0.0, "ev_5")
    r_set = [
        Recipient("rp1", T3Score(0.8, 0.8, 0.8), 0.7),
        Recipient("rp2", T3Score(0.7, 0.7, 0.7), 0.6),
    ]
    session = protocol.open_session(adp5, r_set)
    checks.append(("s8_session_open", session.phase == VCMPhase.COLLECTION))
    checks.append(("s8_session_has_id", len(session.session_id) > 0))

    protocol.submit(session.session_id, "rp1", V3Assessment(0.85, 0.8, 0.82))
    protocol.submit(session.session_id, "rp2", V3Assessment(0.75, 0.7, 0.72))
    res_proto = protocol.finalize(session.session_id)
    checks.append(("s8_finalized", res_proto is not None))
    checks.append(("s8_complete", session.phase == VCMPhase.COMPLETE))
    checks.append(("s8_result_stored", session.result is not None))
    checks.append(("s8_rate_reasonable", 1.0 < res_proto.exchange_rate < 1.5))

    # Invalid session
    checks.append(("s8_invalid_session", protocol.submit("nonexistent", "rp1",
                                                          V3Assessment(0.5, 0.5, 0.5)) is None))

    # ── S9: Recharge Gate ─────────────────────────────────────────────────
    engine7 = ValueConfirmationEngine(min_quorum=1)
    gate = VCMRechargeGate(engine7)
    acct = gate.register("entity_X", initial_atp=500.0)
    checks.append(("s9_initial_balance", acct.balance == 500.0))

    proof = gate.discharge("entity_X", 100.0)
    checks.append(("s9_discharged", proof is not None))
    checks.append(("s9_balance_after", acct.balance == 400.0))
    checks.append(("s9_adp_pool", acct.adp_pool == 100.0))

    engine7.request_attestations(proof, [])
    r_gate = Recipient("rg1", T3Score(0.9, 0.9, 0.9), 0.8)
    engine7.submit_attestation(proof.adp_id, r_gate, V3Assessment(0.9, 0.85, 0.88))
    vcm_res = engine7.certify_value(proof, {"rg1": r_gate})

    atp_back = gate.recharge_via_vcm(vcm_res)
    checks.append(("s9_recharged_positive", atp_back > 0))
    checks.append(("s9_recharged_above_spent", atp_back > 100.0))  # rate > 1.0
    checks.append(("s9_adp_pool_reduced", acct.adp_pool == 0.0))
    checks.append(("s9_balance_recovered", acct.balance > 400.0))
    checks.append(("s9_log_entry", len(gate.recharge_log) == 1))

    # No quorum → no recharge
    engine7b = ValueConfirmationEngine(min_quorum=10)
    gate_b = VCMRechargeGate(engine7b)
    gate_b.register("entity_Y", 200.0)
    proof_b = gate_b.discharge("entity_Y", 50.0)
    engine7b.request_attestations(proof_b, [])
    r_b = Recipient("rb1", T3Score(0.5, 0.5, 0.5), 0.5)
    engine7b.submit_attestation(proof_b.adp_id, r_b, V3Assessment(0.8, 0.8, 0.8))
    vcm_b = engine7b.certify_value(proof_b, {"rb1": r_b})
    atp_b = gate_b.recharge_via_vcm(vcm_b)
    checks.append(("s9_no_quorum_no_recharge", atp_b == 0.0))

    # Insufficient balance
    checks.append(("s9_insufficient", gate.discharge("entity_X", 99999.0) is None))

    # ── S10: Dispute Resolution ───────────────────────────────────────────
    resolver = DisputeResolver()
    dispute = resolver.file_dispute(result, DisputeReason.UNFAIR_ASSESSMENT,
                                     "V3 assessment too low")
    checks.append(("s10_dispute_filed", not dispute.resolved))
    resolver.resolve(dispute, upheld=True, revised_rate=1.3)
    checks.append(("s10_dispute_resolved", dispute.resolved))
    checks.append(("s10_dispute_upheld", dispute.upheld))
    checks.append(("s10_revised_rate", dispute.revised_rate == 1.3))

    # Dispute rate clamping
    d2 = resolver.file_dispute(result, DisputeReason.WRONG_EXCHANGE_RATE, "")
    resolver.resolve(d2, upheld=True, revised_rate=5.0)
    checks.append(("s10_rate_clamped", d2.revised_rate == 1.5))

    # ── S11: Audit Trail ──────────────────────────────────────────────────
    audit = VCMAuditTrail()
    audit.record("adp_1", VCMPhase.COLLECTION, "started")
    audit.record("adp_1", VCMPhase.AGGREGATION, "3 attestations")
    audit.record("adp_1", VCMPhase.CERTIFICATION, "rate=1.35")
    audit.record("adp_1", VCMPhase.RECHARGE, "115 ATP recharged")
    checks.append(("s11_chain_length", len(audit.entries) == 4))
    checks.append(("s11_chain_valid", audit.verify_chain()))

    # Tamper detection
    audit.entries[1].data_hash = "tampered"
    checks.append(("s11_tamper_detected", not audit.verify_chain()))

    # ── S12: Batch VCM ────────────────────────────────────────────────────
    engine8 = ValueConfirmationEngine(min_quorum=1)
    batch = BatchVCM(engine8)
    proofs = [
        ADPProof(f"batch_{i}", f"g_{i}", f"prod_{i}", 50.0 + i * 10, 0.0,
                  f"ev_{i}", timestamp=time.time())
        for i in range(5)
    ]
    r_batch = [Recipient(f"br_{i}", T3Score(0.7, 0.7, 0.7), 0.6) for i in range(3)]
    r_map_batch = {p.adp_id: r_batch for p in proofs}
    att_map = {
        p.adp_id: [(r.entity_id, V3Assessment(0.7 + i * 0.03, 0.65 + i * 0.03, 0.68 + i * 0.03))
                    for r in r_batch]
        for i, p in enumerate(proofs)
    }
    batch_results = batch.process_batch(proofs, r_map_batch, att_map)
    checks.append(("s12_batch_count", len(batch_results) == 5))
    checks.append(("s12_all_quorum", all(r.quorum_met for r in batch_results)))
    # Later batches should have higher rates (higher V3)
    rates = [r.exchange_rate for r in batch_results]
    checks.append(("s12_rates_increasing", rates[-1] > rates[0]))

    # ── S13: Credibility Decay ────────────────────────────────────────────
    inconsistent = Recipient("inc", T3Score(0.5, 0.5, 0.5), 0.5)
    # Wildly varying attestation history
    inconsistent.attestation_history = [0.1, 0.9, 0.2, 0.8, 0.15, 0.85]
    checks.append(("s13_low_credibility", inconsistent.credibility() < 0.5))

    consistent = Recipient("con", T3Score(0.5, 0.5, 0.5), 0.5)
    consistent.attestation_history = [0.7, 0.72, 0.68, 0.71, 0.69]
    checks.append(("s13_high_credibility", consistent.credibility() > 0.9))

    # ── S14: T3/V3 Deltas ─────────────────────────────────────────────────
    # High V3 → positive deltas
    checks.append(("s14_high_v3_positive_t3", result.t3_delta["training"] > 0))
    checks.append(("s14_high_v3_positive_v3", result.v3_delta["valuation"] > 0))

    # Low V3 → negative deltas
    engine9 = ValueConfirmationEngine(min_quorum=1)
    adp_low = ADPProof("adp_low", "g_low", "prod_low", 50.0, 0.0, "ev_low")
    r_low = Recipient("rl1", T3Score(0.5, 0.5, 0.5), 0.5)
    engine9.request_attestations(adp_low, [r_low])
    engine9.submit_attestation("adp_low", r_low, V3Assessment(0.2, 0.1, 0.15))
    res_low = engine9.certify_value(adp_low, {"rl1": r_low})
    checks.append(("s14_low_v3_negative_t3", res_low.t3_delta["training"] < 0))
    checks.append(("s14_low_v3_below_base", res_low.exchange_rate < 1.0))

    # ── S15: Score Inflation Detection ────────────────────────────────────
    engine10 = ValueConfirmationEngine(min_quorum=1)
    adp_infl = ADPProof("adp_infl", "g_infl", "prod_infl", 40.0, 0.0, "ev_infl")
    # Recipient with history of moderate attestations suddenly gives 1.0
    inflator = Recipient("inflator", T3Score(0.6, 0.6, 0.6), 0.5)
    inflator.attestation_history = [0.5, 0.45, 0.5, 0.48, 0.52]  # ~0.5 average
    engine10.request_attestations(adp_infl, [inflator])
    engine10.submit_attestation("adp_infl", inflator, V3Assessment(0.95, 0.95, 0.95))
    res_infl = engine10.certify_value(adp_infl, {"inflator": inflator})
    checks.append(("s15_inflation_detected", FraudType.SCORE_INFLATION in res_infl.fraud_flags))

    # ── S16: Weight Distribution ──────────────────────────────────────────
    engine11 = ValueConfirmationEngine(min_quorum=1)
    adp_w = ADPProof("adp_weight", "g_w", "prod_w", 100.0, 0.0, "ev_w")
    # High-trust expert vs low-trust novice
    expert = Recipient("expert", T3Score(0.95, 0.95, 0.95), 0.9)
    novice = Recipient("novice", T3Score(0.3, 0.3, 0.3), 0.2)
    engine11.request_attestations(adp_w, [expert, novice])
    engine11.submit_attestation("adp_weight", expert, V3Assessment(0.9, 0.85, 0.88))
    engine11.submit_attestation("adp_weight", novice, V3Assessment(0.3, 0.2, 0.25))
    res_w = engine11.certify_value(adp_w, {"expert": expert, "novice": novice})
    # Expert's high assessment should dominate
    checks.append(("s16_expert_dominates", res_w.certified_v3 > 0.7))
    checks.append(("s16_not_naive_avg", abs(res_w.certified_v3 - 0.525) > 0.1))

    # ── S17: Full Lifecycle ───────────────────────────────────────────────
    engine12 = ValueConfirmationEngine(min_quorum=2)
    gate2 = VCMRechargeGate(engine12)
    protocol2 = AttestationProtocol(engine12, deadline_hours=48.0)
    audit2 = VCMAuditTrail()

    # 1. Register entity with ATP
    acct2 = gate2.register("lifecycle_entity", 1000.0)
    checks.append(("s17_registered", acct2.balance == 1000.0))

    # 2. Discharge ATP (do work)
    proof2 = gate2.discharge("lifecycle_entity", 200.0)
    checks.append(("s17_discharged", proof2 is not None and acct2.balance == 800.0))
    audit2.record(proof2.adp_id, VCMPhase.COLLECTION, "opened")

    # 3. Open attestation session
    r_life = [
        Recipient("life_r1", T3Score(0.85, 0.85, 0.85), 0.8),
        Recipient("life_r2", T3Score(0.75, 0.75, 0.75), 0.7),
        Recipient("life_r3", T3Score(0.65, 0.65, 0.65), 0.6),
    ]
    sess = protocol2.open_session(proof2, r_life)
    checks.append(("s17_session_phase", sess.phase == VCMPhase.COLLECTION))

    # 4. Collect attestations
    protocol2.submit(sess.session_id, "life_r1", V3Assessment(0.88, 0.82, 0.85))
    protocol2.submit(sess.session_id, "life_r2", V3Assessment(0.78, 0.72, 0.75))
    protocol2.submit(sess.session_id, "life_r3", V3Assessment(0.68, 0.62, 0.65))
    audit2.record(proof2.adp_id, VCMPhase.AGGREGATION, "3 attestations collected")

    # 5. Finalize
    final_res = protocol2.finalize(sess.session_id)
    checks.append(("s17_finalized", final_res is not None and final_res.quorum_met))
    audit2.record(proof2.adp_id, VCMPhase.CERTIFICATION,
                  f"rate={final_res.exchange_rate:.3f}")

    # 6. Recharge
    atp_back2 = gate2.recharge_via_vcm(final_res)
    checks.append(("s17_recharged", atp_back2 > 0))
    checks.append(("s17_balance_updated", acct2.balance > 800.0))
    audit2.record(proof2.adp_id, VCMPhase.RECHARGE,
                  f"recharged={atp_back2:.2f}")

    # 7. Audit trail intact
    checks.append(("s17_audit_valid", audit2.verify_chain()))
    checks.append(("s17_audit_4_entries", len(audit2.entries) == 4))

    # ── S18: Conservation ─────────────────────────────────────────────────
    # If exchange rate > 1, more ATP comes back than was spent — this is BY DESIGN
    # (exceptional work creates value). Total system ATP increases.
    # If exchange rate < 1, ATP is destroyed — poor work loses energy.
    checks.append(("s18_exceptional_creates",
                    final_res.exchange_rate > 1.0 and atp_back2 > 200.0))
    # Poor work test
    checks.append(("s18_poor_destroys",
                    res_low.exchange_rate < 1.0 and
                    res_low.adp_amount * res_low.exchange_rate < res_low.adp_amount))

    # ── S19: Performance ──────────────────────────────────────────────────
    perf_engine = ValueConfirmationEngine(min_quorum=1)
    perf_recipients = [Recipient(f"perf_r_{i}", T3Score(0.7, 0.7, 0.7), 0.6)
                        for i in range(10)]

    pt0 = time.time()
    for i in range(200):
        adp_p = ADPProof(f"perf_{i}", f"pg_{i}", "perf_prod", 50.0, 0.0, f"pev_{i}")
        perf_engine.request_attestations(adp_p, perf_recipients)
        for r in perf_recipients[:3]:
            perf_engine.submit_attestation(adp_p.adp_id, r,
                                           V3Assessment(0.7, 0.65, 0.68))
        perf_engine.certify_value(adp_p, {r.entity_id: r for r in perf_recipients})
    pt1 = time.time()
    checks.append(("s19_200_vcm_under_2s", pt1 - pt0 < 2.0))
    checks.append(("s19_results_stored", len(perf_engine.results) == 200))

    elapsed = time.time() - t0

    # ── Print Results ─────────────────────────────────────────────────────
    passed = sum(1 for _, v in checks if v)
    total = len(checks)
    title = f"Value Confirmation Mechanism — {passed}/{total} checks passed"
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    for name, val in checks:
        print(f"  [{'PASS' if val else 'FAIL'}] {name}")

    failed = [n for n, v in checks if not v]
    if failed:
        print(f"\n  FAILURES:")
        for f in failed:
            print(f"    ✗ {f}")

    print(f"\n  Time: {elapsed:.2f}s\n")
    return passed == total


if __name__ == "__main__":
    run_checks()
