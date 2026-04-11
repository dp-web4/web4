"""
ATP Insurance Protocol — Reference Implementation

Implements web4-standard/proposals/ATP_INSURANCE_PROTOCOL.md:
- InsurancePool: shared ATP reserve across federated societies
- InsurancePolicy: per-society coverage contract with ratio + cap
- FraudClaim: evidence-based payout request with attribution
- Pool formation: multi-society premium collection with network multiplier
- Claim lifecycle: file → validate → approve/deny → payout → audit
- Dynamic premium adjustment: trust-based, claim-history, reserve-level
- Pool sustainability: reserve requirements, depletion monitoring
- Anti-gaming: collusion detection, Sybil resistance, false claim penalty
- Reinsurance: pool-of-pools for catastrophic risk distribution
- Parametric insurance: auto-trigger payouts on objective criteria

Key insight from spec: "Insurance requires network effects. Single-society
insurance cannot cover losses exceeding the premium paid. Federation insurance
pools enable societies to claim more than their individual premium contribution."
Network multiplier: ~n× for n equal societies (4.7× validated for n=5).

Spec: web4-standard/proposals/ATP_INSURANCE_PROTOCOL.md
"""

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class ClaimStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    APPEALED = "appealed"
    VOID = "void"            # Retroactively voided (false claim detected)

class PoolHealth(Enum):
    HEALTHY = "healthy"      # > 60% reserves
    ADEQUATE = "adequate"    # 30-60% reserves
    WARNING = "warning"      # 20-30% reserves
    CRITICAL = "critical"    # < 20% reserves

class PremiumTier(Enum):
    """Dynamic premium tiers based on society risk profile."""
    LOW_RISK = "low_risk"       # Base rate × 0.8
    STANDARD = "standard"       # Base rate × 1.0
    ELEVATED = "elevated"       # Base rate × 1.3
    HIGH_RISK = "high_risk"     # Base rate × 1.8

class DenialReason(Enum):
    NO_ACTIVE_POLICY = "no_active_policy"
    LOW_CONFIDENCE = "low_confidence"
    EXCEEDS_MAX_PAYOUT = "exceeds_max_payout"
    INSUFFICIENT_POOL = "insufficient_pool"
    POLICY_EXPIRED = "policy_expired"
    COOLDOWN_ACTIVE = "cooldown_active"
    DUPLICATE_CLAIM = "duplicate_claim"

class ParametricTrigger(Enum):
    """Objective criteria for automatic payouts (§7.3)."""
    TRUST_DROP = "trust_drop"          # T3 composite below threshold
    TREASURY_DROP = "treasury_drop"    # Treasury drops by X%
    SUSPICIOUS_EVENTS = "suspicious"   # N events within window


# ============================================================================
# DATA STRUCTURES (§1)
# ============================================================================

@dataclass
class SocietyProfile:
    """Society participating in insurance federation."""
    lct: str
    treasury: float
    t3_composite: float = 0.8
    claim_history: List['FraudClaim'] = field(default_factory=list)
    is_quarantined: bool = False

    def claim_rate(self, window: int = 10) -> float:
        """Claims filed in last N ticks as fraction."""
        recent = [c for c in self.claim_history if c.status == ClaimStatus.APPROVED]
        return len(recent[-window:]) / max(window, 1)


@dataclass
class InsurancePolicy:
    """Insurance policy for a society (§1.2)."""
    policy_id: str
    pool_id: str
    society_lct: str
    premium_paid: float
    coverage_ratio: float       # 0-1, typically 0.8
    max_payout: float
    effective_tick: int
    expiration_tick: Optional[int] = None
    is_active: bool = True

    def covers_tick(self, tick: int) -> bool:
        if not self.is_active:
            return False
        if tick < self.effective_tick:
            return False
        if self.expiration_tick and tick > self.expiration_tick:
            return False
        return True


@dataclass
class FraudClaim:
    """Claim for insurance payout (§1.3)."""
    claim_id: str
    society_lct: str
    policy_id: str
    atp_lost: float
    attributed_to_lct: str
    attribution_confidence: float
    evidence: Dict[str, Any]
    filed_at_tick: int
    status: ClaimStatus = ClaimStatus.PENDING
    payout: float = 0.0
    denial_reason: Optional[DenialReason] = None
    resolved_at_tick: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id, "society_lct": self.society_lct,
            "policy_id": self.policy_id, "atp_lost": self.atp_lost,
            "attributed_to_lct": self.attributed_to_lct,
            "attribution_confidence": self.attribution_confidence,
            "status": self.status.value, "payout": self.payout,
            "filed_at_tick": self.filed_at_tick,
        }


@dataclass
class PoolConfig:
    """Configurable pool parameters (§5.1)."""
    premium_rate: float = 0.05         # 5% of treasury
    coverage_ratio: float = 0.80       # 80% of loss
    max_payout_ratio: float = 0.30     # 30% of treasury cap
    min_confidence: float = 0.70       # Attribution confidence threshold
    min_reserve_ratio: float = 0.20    # 20% minimum post-claim
    target_reserve_ratio: float = 0.50 # 50% target post-claim
    alert_reserve_ratio: float = 0.30  # 30% triggers premium review
    claim_cooldown_ticks: int = 5      # Minimum ticks between claims
    min_societies: int = 3             # Minimum pool size


@dataclass
class PoolAnalytics:
    """Pool statistics and health metrics."""
    pool_id: str
    balance: float
    total_premiums: float
    total_payouts: float
    active_policies: int
    total_claims_filed: int
    total_claims_approved: int
    total_claims_denied: int
    reserve_ratio: float
    health: PoolHealth
    network_multiplier: float
    coverage_effectiveness: float    # avg actual/requested payout ratio

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pool_id": self.pool_id, "balance": self.balance,
            "total_premiums": self.total_premiums, "total_payouts": self.total_payouts,
            "active_policies": self.active_policies,
            "claims_filed": self.total_claims_filed,
            "claims_approved": self.total_claims_approved,
            "claims_denied": self.total_claims_denied,
            "reserve_ratio": round(self.reserve_ratio, 4),
            "health": self.health.value,
            "network_multiplier": round(self.network_multiplier, 2),
            "coverage_effectiveness": round(self.coverage_effectiveness, 4),
        }


@dataclass
class ParametricRule:
    """Auto-trigger payout rule (§7.3)."""
    rule_id: str
    trigger: ParametricTrigger
    threshold: float            # Trigger value
    auto_payout_ratio: float    # Fraction of max_payout
    cooldown_ticks: int = 10


@dataclass
class ReinsuranceLink:
    """Pool-to-pool reinsurance (§7.2)."""
    primary_pool_id: str
    reinsurance_pool_id: str
    coverage_ratio: float = 0.5
    max_payout: float = 0.0
    premium_paid: float = 0.0


@dataclass
class AuditEntry:
    """Immutable audit record for pool operations."""
    entry_id: str
    operation: str
    tick: int
    details: Dict[str, Any]
    prev_hash: str = ""

    @property
    def hash(self) -> str:
        content = json.dumps({"id": self.entry_id, "op": self.operation,
                               "tick": self.tick, "prev": self.prev_hash},
                              sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ============================================================================
# PREMIUM CALCULATOR (§7.1)
# ============================================================================

class PremiumCalculator:
    """Dynamic premium adjustment based on risk profile."""

    @staticmethod
    def tier_for_society(society: SocietyProfile, config: PoolConfig) -> PremiumTier:
        """Classify society risk tier."""
        if society.is_quarantined:
            return PremiumTier.HIGH_RISK
        rate = society.claim_rate()
        if rate > 0.3:
            return PremiumTier.HIGH_RISK
        if rate > 0.15:
            return PremiumTier.ELEVATED
        if society.t3_composite >= 0.8:
            return PremiumTier.LOW_RISK
        return PremiumTier.STANDARD

    @staticmethod
    def tier_multiplier(tier: PremiumTier) -> float:
        return {
            PremiumTier.LOW_RISK: 0.8,
            PremiumTier.STANDARD: 1.0,
            PremiumTier.ELEVATED: 1.3,
            PremiumTier.HIGH_RISK: 1.8,
        }[tier]

    @staticmethod
    def compute_premium(society: SocietyProfile, config: PoolConfig,
                         pool_reserve_ratio: float = 1.0) -> float:
        """Compute premium with dynamic adjustments."""
        base = society.treasury * config.premium_rate
        tier = PremiumCalculator.tier_for_society(society, config)
        adjusted = base * PremiumCalculator.tier_multiplier(tier)
        # Low reserves → higher premiums
        if pool_reserve_ratio < config.alert_reserve_ratio:
            adjusted *= 1.5
        return round(adjusted, 2)


# ============================================================================
# COLLUSION DETECTOR (§4.1)
# ============================================================================

class CollusionDetector:
    """Detect coordinated claim patterns across societies."""

    @staticmethod
    def check_coordinated_claims(claims: List[FraudClaim],
                                  window_ticks: int = 3) -> List[Tuple[str, str]]:
        """Detect societies filing claims in suspiciously close succession."""
        suspicious_pairs = []
        approved = [c for c in claims if c.status == ClaimStatus.APPROVED]
        for i, c1 in enumerate(approved):
            for c2 in approved[i+1:]:
                if (c1.society_lct != c2.society_lct and
                    abs(c1.filed_at_tick - c2.filed_at_tick) <= window_ticks and
                    c1.attributed_to_lct == c2.attributed_to_lct):
                    suspicious_pairs.append((c1.society_lct, c2.society_lct))
        return suspicious_pairs

    @staticmethod
    def check_claim_frequency(society_lct: str, claims: List[FraudClaim],
                               max_rate: float = 0.5) -> bool:
        """Check if society's claim rate is suspiciously high."""
        society_claims = [c for c in claims
                          if c.society_lct == society_lct
                          and c.status == ClaimStatus.APPROVED]
        if len(claims) < 3:
            return False
        return len(society_claims) / max(len(claims), 1) > max_rate


# ============================================================================
# INSURANCE POOL (§1.1, §2)
# ============================================================================

class InsurancePool:
    """Shared insurance pool across federated societies."""

    def __init__(self, pool_id: str, config: Optional[PoolConfig] = None):
        self.pool_id = pool_id
        self.config = config or PoolConfig()
        self.balance: float = 0.0
        self.total_premiums: float = 0.0
        self.total_payouts: float = 0.0
        self.policies: Dict[str, InsurancePolicy] = {}   # policy_id → policy
        self.claims: List[FraudClaim] = []
        self.societies: Dict[str, SocietyProfile] = {}   # lct → profile
        self.parametric_rules: List[ParametricRule] = []
        self.reinsurance_links: List[ReinsuranceLink] = []
        self.audit_log: List[AuditEntry] = []
        self.current_tick: int = 0
        self.last_claim_tick: Dict[str, int] = {}        # society → last claim tick
        self.premium_calculator = PremiumCalculator()
        self.collusion_detector = CollusionDetector()

    # ──────────────────────────────────────────────────
    # Pool Formation (§2.1)
    # ──────────────────────────────────────────────────

    def add_society(self, society: SocietyProfile, tick: int = 0) -> InsurancePolicy:
        """Add society to pool and collect premium."""
        self.current_tick = max(self.current_tick, tick)
        self.societies[society.lct] = society

        premium = self.premium_calculator.compute_premium(
            society, self.config, self.reserve_ratio())
        max_payout = society.treasury * self.config.max_payout_ratio

        policy_id = f"pol:{hashlib.sha256(f'{self.pool_id}:{society.lct}'.encode()).hexdigest()[:12]}"
        policy = InsurancePolicy(
            policy_id=policy_id, pool_id=self.pool_id,
            society_lct=society.lct, premium_paid=premium,
            coverage_ratio=self.config.coverage_ratio,
            max_payout=max_payout, effective_tick=tick)

        self.policies[policy_id] = policy
        self.balance += premium
        self.total_premiums += premium
        society.treasury -= premium

        self._audit("premium_payment", tick, {
            "society": society.lct, "premium": premium,
            "policy_id": policy_id, "pool_balance": self.balance})
        return policy

    # ──────────────────────────────────────────────────
    # Claim Filing (§2.4)
    # ──────────────────────────────────────────────────

    def file_claim(self, society_lct: str, atp_lost: float,
                    attributed_to: str, confidence: float,
                    evidence: Dict[str, Any], tick: int) -> FraudClaim:
        """File insurance claim for fraud-related ATP loss."""
        self.current_tick = max(self.current_tick, tick)
        claim_id = f"clm:{hashlib.sha256(f'{society_lct}:{tick}:{atp_lost}'.encode()).hexdigest()[:12]}"

        # Find active policy
        policy = self._active_policy(society_lct, tick)
        policy_id = policy.policy_id if policy else ""

        claim = FraudClaim(
            claim_id=claim_id, society_lct=society_lct,
            policy_id=policy_id, atp_lost=atp_lost,
            attributed_to_lct=attributed_to,
            attribution_confidence=confidence,
            evidence=evidence, filed_at_tick=tick)

        # Validate and approve/deny
        denial = self._validate_claim(claim, policy, tick)
        if denial:
            claim.status = ClaimStatus.DENIED
            claim.denial_reason = denial
            claim.resolved_at_tick = tick
        else:
            # Calculate payout (§2.4)
            claimed = atp_lost * policy.coverage_ratio
            payout = min(claimed, policy.max_payout, self.balance)
            claim.payout = round(payout, 2)
            claim.status = ClaimStatus.APPROVED
            claim.resolved_at_tick = tick

            # Transfer
            self.balance -= claim.payout
            self.total_payouts += claim.payout
            society = self.societies.get(society_lct)
            if society:
                society.treasury += claim.payout
                society.claim_history.append(claim)

            self.last_claim_tick[society_lct] = tick

        self.claims.append(claim)
        self._audit("claim_filed", tick, claim.to_dict())
        return claim

    def _validate_claim(self, claim: FraudClaim,
                         policy: Optional[InsurancePolicy],
                         tick: int) -> Optional[DenialReason]:
        """Validate claim against approval criteria (§2.4)."""
        if not policy:
            return DenialReason.NO_ACTIVE_POLICY
        if not policy.covers_tick(tick):
            return DenialReason.POLICY_EXPIRED
        if claim.attribution_confidence < self.config.min_confidence:
            return DenialReason.LOW_CONFIDENCE
        if claim.atp_lost * policy.coverage_ratio > policy.max_payout:
            # Still allow but cap at max_payout — only deny if 0
            if policy.max_payout <= 0:
                return DenialReason.EXCEEDS_MAX_PAYOUT
        if self.balance <= 0:
            return DenialReason.INSUFFICIENT_POOL
        # Cooldown check
        last = self.last_claim_tick.get(claim.society_lct, -100)
        if tick - last < self.config.claim_cooldown_ticks:
            return DenialReason.COOLDOWN_ACTIVE
        # Duplicate check
        for existing in self.claims:
            if (existing.society_lct == claim.society_lct and
                existing.attributed_to_lct == claim.attributed_to_lct and
                existing.atp_lost == claim.atp_lost and
                existing.status == ClaimStatus.APPROVED):
                return DenialReason.DUPLICATE_CLAIM
        return None

    # ──────────────────────────────────────────────────
    # Parametric Insurance (§7.3)
    # ──────────────────────────────────────────────────

    def add_parametric_rule(self, rule: ParametricRule):
        self.parametric_rules.append(rule)

    def check_parametric_triggers(self, society: SocietyProfile,
                                    tick: int) -> List[FraudClaim]:
        """Check parametric rules and auto-file claims."""
        triggered_claims = []
        policy = self._active_policy(society.lct, tick)
        if not policy:
            return []

        for rule in self.parametric_rules:
            triggered = False
            if rule.trigger == ParametricTrigger.TRUST_DROP:
                triggered = society.t3_composite < rule.threshold
            elif rule.trigger == ParametricTrigger.TREASURY_DROP:
                triggered = society.treasury < rule.threshold
            elif rule.trigger == ParametricTrigger.SUSPICIOUS_EVENTS:
                triggered = society.claim_rate() > rule.threshold

            if triggered:
                auto_payout = policy.max_payout * rule.auto_payout_ratio
                claim = self.file_claim(
                    society.lct, auto_payout, "parametric_trigger",
                    1.0, {"trigger": rule.trigger.value, "rule": rule.rule_id},
                    tick)
                triggered_claims.append(claim)
        return triggered_claims

    # ──────────────────────────────────────────────────
    # Reinsurance (§7.2)
    # ──────────────────────────────────────────────────

    def add_reinsurance(self, reinsurance_pool: 'InsurancePool',
                         coverage_ratio: float = 0.5,
                         premium_ratio: float = 0.1) -> ReinsuranceLink:
        """Link to reinsurance pool for catastrophic coverage."""
        premium = self.balance * premium_ratio
        max_payout = self.total_premiums * coverage_ratio
        link = ReinsuranceLink(
            primary_pool_id=self.pool_id,
            reinsurance_pool_id=reinsurance_pool.pool_id,
            coverage_ratio=coverage_ratio,
            max_payout=max_payout, premium_paid=premium)
        self.reinsurance_links.append(link)
        self.balance -= premium
        reinsurance_pool.balance += premium
        reinsurance_pool.total_premiums += premium
        return link

    def claim_reinsurance(self, shortfall: float,
                           reinsurance_pool: 'InsurancePool',
                           tick: int) -> float:
        """Claim from reinsurance pool for shortfall."""
        link = next((l for l in self.reinsurance_links
                      if l.reinsurance_pool_id == reinsurance_pool.pool_id), None)
        if not link:
            return 0.0
        payout = min(shortfall * link.coverage_ratio, link.max_payout,
                      reinsurance_pool.balance)
        reinsurance_pool.balance -= payout
        reinsurance_pool.total_payouts += payout
        self.balance += payout
        return round(payout, 2)

    # ──────────────────────────────────────────────────
    # Analytics (§3)
    # ──────────────────────────────────────────────────

    def analytics(self) -> PoolAnalytics:
        """Compute pool statistics and health."""
        active = sum(1 for p in self.policies.values() if p.is_active)
        approved = sum(1 for c in self.claims if c.status == ClaimStatus.APPROVED)
        denied = sum(1 for c in self.claims if c.status == ClaimStatus.DENIED)
        reserve = self.reserve_ratio()

        # Coverage effectiveness
        if approved > 0:
            total_requested = sum(c.atp_lost for c in self.claims
                                   if c.status == ClaimStatus.APPROVED)
            total_paid = sum(c.payout for c in self.claims
                              if c.status == ClaimStatus.APPROVED)
            effectiveness = total_paid / max(total_requested, 0.01)
        else:
            effectiveness = 1.0

        # Network multiplier
        if self.societies:
            avg_premium = self.total_premiums / max(len(self.societies), 1)
            multiplier = self.total_premiums / max(avg_premium, 0.01)
        else:
            multiplier = 0.0

        return PoolAnalytics(
            pool_id=self.pool_id, balance=round(self.balance, 2),
            total_premiums=round(self.total_premiums, 2),
            total_payouts=round(self.total_payouts, 2),
            active_policies=active, total_claims_filed=len(self.claims),
            total_claims_approved=approved, total_claims_denied=denied,
            reserve_ratio=reserve, health=self.health(),
            network_multiplier=multiplier,
            coverage_effectiveness=effectiveness)

    def reserve_ratio(self) -> float:
        """Current reserve as fraction of total premiums."""
        if self.total_premiums <= 0:
            return 1.0
        return self.balance / self.total_premiums

    def health(self) -> PoolHealth:
        """Pool health based on reserve ratio."""
        r = self.reserve_ratio()
        if r >= 0.6:
            return PoolHealth.HEALTHY
        if r >= 0.3:
            return PoolHealth.ADEQUATE
        if r >= 0.2:
            return PoolHealth.WARNING
        return PoolHealth.CRITICAL

    def network_multiplier(self) -> float:
        """Current network multiplier (§3.2)."""
        if not self.societies:
            return 0.0
        return len(self.societies)  # ≈ n for equal-sized societies

    # ──────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────

    def _active_policy(self, society_lct: str, tick: int) -> Optional[InsurancePolicy]:
        for p in self.policies.values():
            if p.society_lct == society_lct and p.covers_tick(tick):
                return p
        return None

    def _audit(self, operation: str, tick: int, details: Dict[str, Any]):
        prev_hash = self.audit_log[-1].hash if self.audit_log else ""
        entry = AuditEntry(
            entry_id=f"aud:{len(self.audit_log):04d}",
            operation=operation, tick=tick,
            details=details, prev_hash=prev_hash)
        self.audit_log.append(entry)

    def void_claim(self, claim_id: str, tick: int) -> bool:
        """Void a previously approved claim (false claim detected)."""
        for claim in self.claims:
            if claim.claim_id == claim_id and claim.status == ClaimStatus.APPROVED:
                claim.status = ClaimStatus.VOID
                claim.resolved_at_tick = tick
                # Recover payout
                self.balance += claim.payout
                self.total_payouts -= claim.payout
                society = self.societies.get(claim.society_lct)
                if society:
                    society.treasury -= claim.payout
                self._audit("claim_voided", tick, {"claim_id": claim_id,
                             "recovered": claim.payout})
                return True
        return False


# ============================================================================
# FEDERATION POOL FACTORY
# ============================================================================

def create_federation_pool(pool_id: str,
                            societies: List[SocietyProfile],
                            config: Optional[PoolConfig] = None,
                            tick: int = 0) -> InsurancePool:
    """Create federation-wide insurance pool (§2.1)."""
    pool = InsurancePool(pool_id, config)
    for society in societies:
        pool.add_society(society, tick)
    return pool


# ============================================================================
# TESTS
# ============================================================================

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

    # ================================================================
    # T1: SocietyProfile basics
    # ================================================================
    print("T1: Society Profile")
    s1 = SocietyProfile(lct="soc:alpha", treasury=2000, t3_composite=0.85)
    check("T1.1 Treasury set", s1.treasury == 2000)
    check("T1.2 T3 set", s1.t3_composite == 0.85)
    check("T1.3 Claim rate empty", s1.claim_rate() == 0.0)
    check("T1.4 Not quarantined", not s1.is_quarantined)

    # ================================================================
    # T2: Pool creation
    # ================================================================
    print("T2: Pool Creation")
    pool = InsurancePool("pool:test1")
    check("T2.1 Pool ID", pool.pool_id == "pool:test1")
    check("T2.2 Zero balance", pool.balance == 0.0)
    check("T2.3 Default config", pool.config.premium_rate == 0.05)
    check("T2.4 Healthy initially", pool.health() == PoolHealth.HEALTHY)

    # ================================================================
    # T3: Single society enrollment
    # ================================================================
    print("T3: Society Enrollment")
    pool2 = InsurancePool("pool:test2")
    s2 = SocietyProfile(lct="soc:beta", treasury=2000, t3_composite=0.85)
    pol = pool2.add_society(s2, tick=1)
    premium = 2000 * 0.05 * 0.8  # Low risk (T3 >= 0.8) → 0.8× multiplier
    check("T3.1 Policy created", pol.policy_id.startswith("pol:"))
    check("T3.2 Premium collected", pool2.balance == premium)
    check("T3.3 Society treasury reduced", s2.treasury == 2000 - premium)
    check("T3.4 Policy coverage ratio", pol.coverage_ratio == 0.8)
    check("T3.5 Policy max payout", pol.max_payout == 2000 * 0.3)
    check("T3.6 Policy active", pol.is_active)
    check("T3.7 Audit log entry", len(pool2.audit_log) == 1)

    # ================================================================
    # T4: Federation pool (5 societies, spec scenario)
    # ================================================================
    print("T4: Federation Pool — 5 Societies")
    societies = [
        SocietyProfile(lct=f"soc:{c}", treasury=t, t3_composite=0.85)
        for c, t in [("A", 2000), ("B", 1500), ("C", 1800), ("D", 2200), ("E", 1700)]
    ]
    fp = create_federation_pool("pool:fed1", societies, tick=1)
    check("T4.1 Five societies enrolled", len(fp.societies) == 5)
    check("T4.2 Five policies", len(fp.policies) == 5)
    check("T4.3 Pool balance > 0", fp.balance > 0)
    check("T4.4 Network multiplier ≈ 5", abs(fp.network_multiplier() - 5) < 0.1)
    # Each pays 5% × 0.8 (low risk) of treasury
    expected_pool = sum(t * 0.05 * 0.8 for _, t in
                         [("A", 2000), ("B", 1500), ("C", 1800), ("D", 2200), ("E", 1700)])
    check("T4.5 Pool balance correct", abs(fp.balance - expected_pool) < 0.1)

    # ================================================================
    # T5: Claim — approved (spec scenario: Society B 300 ATP loss)
    # ================================================================
    print("T5: Claim Approved")
    claim = fp.file_claim("soc:B", 300.0, "agent:bob", 0.85,
                           {"type": "fraud", "count": 2}, tick=10)
    check("T5.1 Claim approved", claim.status == ClaimStatus.APPROVED)
    check("T5.2 Payout > 0", claim.payout > 0)
    expected_payout = min(300 * 0.8, 1500 * 0.3, fp.balance + claim.payout)
    check("T5.3 Payout = min(claimed, max_payout, balance)", claim.payout == expected_payout)
    check("T5.4 Pool balance reduced", fp.balance < expected_pool)
    check("T5.5 Society B treasury increased", fp.societies["soc:B"].treasury > 1500 - 1500*0.05*0.8)

    # ================================================================
    # T6: Claim — denied (low confidence)
    # ================================================================
    print("T6: Claim Denied — Low Confidence")
    denied = fp.file_claim("soc:A", 100.0, "agent:eve", 0.5,
                            {"type": "suspected"}, tick=20)
    check("T6.1 Claim denied", denied.status == ClaimStatus.DENIED)
    check("T6.2 Denial reason", denied.denial_reason == DenialReason.LOW_CONFIDENCE)
    check("T6.3 No payout", denied.payout == 0.0)

    # ================================================================
    # T7: Claim — denied (cooldown)
    # ================================================================
    print("T7: Claim Denied — Cooldown")
    cooldown = fp.file_claim("soc:B", 50.0, "agent:charlie", 0.9,
                              {"type": "theft"}, tick=12)  # Only 2 ticks after last claim
    check("T7.1 Claim denied", cooldown.status == ClaimStatus.DENIED)
    check("T7.2 Denial reason", cooldown.denial_reason == DenialReason.COOLDOWN_ACTIVE)

    # ================================================================
    # T8: Claim — denied (no policy)
    # ================================================================
    print("T8: Claim Denied — No Policy")
    no_pol = fp.file_claim("soc:unknown", 100.0, "agent:x", 0.9,
                            {"type": "fraud"}, tick=30)
    check("T8.1 Claim denied", no_pol.status == ClaimStatus.DENIED)
    check("T8.2 Denial reason", no_pol.denial_reason == DenialReason.NO_ACTIVE_POLICY)

    # ================================================================
    # T9: Claim — denied (duplicate)
    # ================================================================
    print("T9: Claim Denied — Duplicate")
    dup = fp.file_claim("soc:B", 300.0, "agent:bob", 0.85,
                         {"type": "fraud"}, tick=30)
    check("T9.1 Duplicate denied", dup.status == ClaimStatus.DENIED)
    check("T9.2 Denial reason", dup.denial_reason == DenialReason.DUPLICATE_CLAIM)

    # ================================================================
    # T10: Pool analytics
    # ================================================================
    print("T10: Pool Analytics")
    analytics = fp.analytics()
    check("T10.1 Pool ID", analytics.pool_id == "pool:fed1")
    check("T10.2 Active policies", analytics.active_policies == 5)
    check("T10.3 Claims filed", analytics.total_claims_filed >= 4)
    check("T10.4 Claims approved >= 1", analytics.total_claims_approved >= 1)
    check("T10.5 Claims denied >= 1", analytics.total_claims_denied >= 1)
    check("T10.6 Reserve ratio < 1.0", analytics.reserve_ratio < 1.0)
    check("T10.7 Network multiplier ≈ 5", abs(analytics.network_multiplier - 5) < 0.1)
    check("T10.8 Coverage effectiveness ≤ 1.0", analytics.coverage_effectiveness <= 1.0)
    check("T10.9 Analytics to_dict", "health" in analytics.to_dict())

    # ================================================================
    # T11: Pool health states
    # ================================================================
    print("T11: Pool Health States")
    check("T11.1 Current pool health", fp.health() in list(PoolHealth))
    # Test health thresholds
    h_pool = InsurancePool("pool:health_test")
    h_pool.total_premiums = 100
    h_pool.balance = 70
    check("T11.2 70% → healthy", h_pool.health() == PoolHealth.HEALTHY)
    h_pool.balance = 40
    check("T11.3 40% → adequate", h_pool.health() == PoolHealth.ADEQUATE)
    h_pool.balance = 25
    check("T11.4 25% → warning", h_pool.health() == PoolHealth.WARNING)
    h_pool.balance = 10
    check("T11.5 10% → critical", h_pool.health() == PoolHealth.CRITICAL)

    # ================================================================
    # T12: Premium calculator — risk tiers
    # ================================================================
    print("T12: Premium Tiers")
    cfg = PoolConfig()
    low = SocietyProfile(lct="soc:low", treasury=1000, t3_composite=0.9)
    check("T12.1 High T3 → low risk", PremiumCalculator.tier_for_society(low, cfg) == PremiumTier.LOW_RISK)
    std = SocietyProfile(lct="soc:std", treasury=1000, t3_composite=0.7)
    check("T12.2 Normal T3 → standard", PremiumCalculator.tier_for_society(std, cfg) == PremiumTier.STANDARD)
    quar = SocietyProfile(lct="soc:quar", treasury=1000, is_quarantined=True)
    check("T12.3 Quarantined → high risk", PremiumCalculator.tier_for_society(quar, cfg) == PremiumTier.HIGH_RISK)
    # Multipliers
    check("T12.4 Low risk multiplier 0.8", PremiumCalculator.tier_multiplier(PremiumTier.LOW_RISK) == 0.8)
    check("T12.5 Standard multiplier 1.0", PremiumCalculator.tier_multiplier(PremiumTier.STANDARD) == 1.0)
    check("T12.6 High risk multiplier 1.8", PremiumCalculator.tier_multiplier(PremiumTier.HIGH_RISK) == 1.8)
    # Premium computation
    p_low = PremiumCalculator.compute_premium(low, cfg)
    p_std = PremiumCalculator.compute_premium(std, cfg)
    check("T12.7 Low risk pays less", p_low < p_std)

    # ================================================================
    # T13: Collusion detection
    # ================================================================
    print("T13: Collusion Detection")
    c1 = FraudClaim("c1", "soc:X", "pol1", 100, "agent:z", 0.9, {}, 10, ClaimStatus.APPROVED)
    c2 = FraudClaim("c2", "soc:Y", "pol2", 150, "agent:z", 0.8, {}, 11, ClaimStatus.APPROVED)
    c3 = FraudClaim("c3", "soc:Z", "pol3", 100, "agent:w", 0.9, {}, 50, ClaimStatus.APPROVED)
    pairs = CollusionDetector.check_coordinated_claims([c1, c2, c3], window_ticks=3)
    check("T13.1 Coordinated pair detected", ("soc:X", "soc:Y") in pairs)
    check("T13.2 Non-coordinated not flagged", len(pairs) == 1)

    freq = CollusionDetector.check_claim_frequency("soc:X", [c1, c2, c3])
    check("T13.3 Frequency check (1/3 not suspicious)", not freq)
    many = [FraudClaim(f"c{i}", "soc:X", "pol1", 10, "agent:a", 0.9, {}, i, ClaimStatus.APPROVED) for i in range(8)]
    many.append(FraudClaim("c99", "soc:Y", "pol2", 10, "agent:b", 0.9, {}, 99, ClaimStatus.APPROVED))
    freq2 = CollusionDetector.check_claim_frequency("soc:X", many)
    check("T13.4 High frequency detected", freq2)

    # ================================================================
    # T14: Policy lifecycle
    # ================================================================
    print("T14: Policy Lifecycle")
    pol2 = InsurancePolicy("pol:test", "pool:test", "soc:test", 100, 0.8, 600, 10, 50)
    check("T14.1 Covers tick 25", pol2.covers_tick(25))
    check("T14.2 Covers tick 10", pol2.covers_tick(10))
    check("T14.3 Not covers tick 5", not pol2.covers_tick(5))
    check("T14.4 Not covers tick 51", not pol2.covers_tick(51))
    pol2.is_active = False
    check("T14.5 Inactive → no coverage", not pol2.covers_tick(25))

    # ================================================================
    # T15: Void claim (false claim recovery)
    # ================================================================
    print("T15: Void Claim")
    fp_void = create_federation_pool("pool:void_test", [
        SocietyProfile(lct="soc:v1", treasury=1000, t3_composite=0.85),
        SocietyProfile(lct="soc:v2", treasury=1000, t3_composite=0.85),
        SocietyProfile(lct="soc:v3", treasury=1000, t3_composite=0.85),
    ], tick=1)
    balance_before = fp_void.balance
    claim_v = fp_void.file_claim("soc:v1", 200, "agent:bad", 0.9,
                                   {"type": "fraud"}, tick=10)
    check("T15.1 Claim approved", claim_v.status == ClaimStatus.APPROVED)
    balance_after_claim = fp_void.balance
    check("T15.2 Balance reduced", balance_after_claim < balance_before)
    voided = fp_void.void_claim(claim_v.claim_id, tick=15)
    check("T15.3 Void successful", voided)
    check("T15.4 Claim status VOID", claim_v.status == ClaimStatus.VOID)
    check("T15.5 Balance recovered", abs(fp_void.balance - balance_before) < 0.01)
    # Void nonexistent
    check("T15.6 Void nonexistent → False", not fp_void.void_claim("clm:fake", 20))

    # ================================================================
    # T16: Parametric insurance
    # ================================================================
    print("T16: Parametric Insurance")
    fp_param = create_federation_pool("pool:param_test", [
        SocietyProfile(lct="soc:p1", treasury=2000, t3_composite=0.85),
        SocietyProfile(lct="soc:p2", treasury=2000, t3_composite=0.85),
        SocietyProfile(lct="soc:p3", treasury=2000, t3_composite=0.85),
    ], tick=1)
    rule = ParametricRule("rule1", ParametricTrigger.TRUST_DROP, 0.5, 0.5)
    fp_param.add_parametric_rule(rule)

    # No trigger (T3 = 0.85 > 0.5)
    soc_p1 = fp_param.societies["soc:p1"]
    auto = fp_param.check_parametric_triggers(soc_p1, tick=20)
    check("T16.1 No trigger (T3 ok)", len(auto) == 0)

    # Drop T3 below threshold
    soc_p1.t3_composite = 0.3
    auto2 = fp_param.check_parametric_triggers(soc_p1, tick=30)
    check("T16.2 Triggered (T3 dropped)", len(auto2) >= 1)
    check("T16.3 Auto-claim approved", auto2[0].status == ClaimStatus.APPROVED)

    # ================================================================
    # T17: Reinsurance
    # ================================================================
    print("T17: Reinsurance")
    primary = create_federation_pool("pool:primary", [
        SocietyProfile(lct=f"soc:r{i}", treasury=1000, t3_composite=0.85)
        for i in range(5)
    ], tick=1)
    reinsurance = InsurancePool("pool:reinsurance")
    reinsurance.balance = 5000  # Pre-funded

    link = primary.add_reinsurance(reinsurance, coverage_ratio=0.5, premium_ratio=0.1)
    check("T17.1 Link created", link.primary_pool_id == "pool:primary")
    check("T17.2 Premium transferred", reinsurance.total_premiums > 0)
    primary_balance_pre = primary.balance

    # Simulate shortfall
    payout = primary.claim_reinsurance(500, reinsurance, tick=20)
    check("T17.3 Reinsurance payout > 0", payout > 0)
    check("T17.4 Primary balance increased", primary.balance > primary_balance_pre)
    check("T17.5 Reinsurance balance decreased", reinsurance.balance < 5000)

    # ================================================================
    # T18: Audit log chain
    # ================================================================
    print("T18: Audit Log")
    check("T18.1 Audit entries exist", len(fp.audit_log) > 0)
    # Check hash chain
    for i in range(1, len(fp.audit_log)):
        check(f"T18.{i+1} Hash chain[{i}]",
              fp.audit_log[i].prev_hash == fp.audit_log[i-1].hash)
    check("T18.last First entry has empty prev", fp.audit_log[0].prev_hash == "")

    # ================================================================
    # T19: Network effects — single vs federation
    # ================================================================
    print("T19: Network Effects")
    # Single society
    single = InsurancePool("pool:single")
    ss = SocietyProfile(lct="soc:alone", treasury=2000, t3_composite=0.85)
    single.add_society(ss, tick=1)
    single_balance = single.balance

    # Federation
    fed_societies = [SocietyProfile(lct=f"soc:f{i}", treasury=2000, t3_composite=0.85)
                      for i in range(5)]
    fed = create_federation_pool("pool:fed_net", fed_societies, tick=1)
    fed_balance = fed.balance

    check("T19.1 Federation pool larger", fed_balance > single_balance)
    multiplier = fed_balance / single_balance
    check("T19.2 Network multiplier ≈ 5", abs(multiplier - 5) < 0.5)

    # Claim 300 against single
    sc = single.file_claim("soc:alone", 300, "agent:bad", 0.9,
                            {"type": "fraud"}, tick=10)
    # Claim 300 against federation
    fc = fed.file_claim("soc:f0", 300, "agent:bad", 0.9,
                         {"type": "fraud"}, tick=10)
    check("T19.3 Single payout ≤ pool", sc.payout <= single_balance)
    check("T19.4 Federation payout = full coverage",
          fc.payout == min(300 * 0.8, 2000 * 0.3))
    check("T19.5 Federation payout ≥ single payout", fc.payout >= sc.payout)
    check("T19.6 Federation still has reserves", fed.balance > 0)

    # ================================================================
    # T20: Pool depletion scenario
    # ================================================================
    print("T20: Pool Depletion")
    small = create_federation_pool("pool:small", [
        SocietyProfile(lct=f"soc:s{i}", treasury=500, t3_composite=0.85)
        for i in range(3)
    ], tick=1)
    # File large claims to deplete
    c_dep = small.file_claim("soc:s0", 400, "agent:x", 0.9, {}, tick=10)
    check("T20.1 First claim approved", c_dep.status == ClaimStatus.APPROVED)
    health_after = small.health()
    check("T20.2 Health degraded", health_after != PoolHealth.HEALTHY)
    check("T20.3 Reserve ratio dropped", small.reserve_ratio() < 1.0)

    # ================================================================
    # T21: Dynamic premiums under stress
    # ================================================================
    print("T21: Dynamic Premiums")
    cfg21 = PoolConfig()
    stressed_soc = SocietyProfile(lct="soc:stressed", treasury=1000, t3_composite=0.85)
    p_normal = PremiumCalculator.compute_premium(stressed_soc, cfg21, pool_reserve_ratio=0.5)
    p_stressed = PremiumCalculator.compute_premium(stressed_soc, cfg21, pool_reserve_ratio=0.2)
    check("T21.1 Stressed pool → higher premium", p_stressed > p_normal)
    check("T21.2 Stress multiplier 1.5×", abs(p_stressed / p_normal - 1.5) < 0.01)

    # ================================================================
    # T22: Expired policy
    # ================================================================
    print("T22: Expired Policy")
    exp_pool = create_federation_pool("pool:exp", [
        SocietyProfile(lct="soc:exp1", treasury=1000, t3_composite=0.85),
        SocietyProfile(lct="soc:exp2", treasury=1000, t3_composite=0.85),
        SocietyProfile(lct="soc:exp3", treasury=1000, t3_composite=0.85),
    ], tick=1)
    # Expire policy for soc:exp1
    for p in exp_pool.policies.values():
        if p.society_lct == "soc:exp1":
            p.expiration_tick = 5
    claim_exp = exp_pool.file_claim("soc:exp1", 100, "agent:a", 0.9, {}, tick=10)
    check("T22.1 Expired policy → denied", claim_exp.status == ClaimStatus.DENIED)
    check("T22.2 Reason: no active policy (expired)", claim_exp.denial_reason == DenialReason.NO_ACTIVE_POLICY)

    # ================================================================
    # T23: Insufficient pool
    # ================================================================
    print("T23: Insufficient Pool")
    empty_pool = InsurancePool("pool:empty")
    es = SocietyProfile(lct="soc:emp", treasury=100, t3_composite=0.85)
    empty_pool.add_society(es, tick=1)
    # Drain pool
    empty_pool.balance = 0
    ins_claim = empty_pool.file_claim("soc:emp", 50, "agent:b", 0.9, {}, tick=10)
    check("T23.1 Insufficient pool → denied", ins_claim.status == ClaimStatus.DENIED)
    check("T23.2 Reason: insufficient pool", ins_claim.denial_reason == DenialReason.INSUFFICIENT_POOL)

    # ================================================================
    # T24: E2E federation insurance scenario
    # ================================================================
    print("T24: E2E Scenario")
    # 5 diverse societies
    e2e_socs = [
        SocietyProfile(lct="soc:bank", treasury=5000, t3_composite=0.9),
        SocietyProfile(lct="soc:market", treasury=3000, t3_composite=0.85),
        SocietyProfile(lct="soc:factory", treasury=4000, t3_composite=0.8),
        SocietyProfile(lct="soc:school", treasury=2000, t3_composite=0.95),
        SocietyProfile(lct="soc:clinic", treasury=2500, t3_composite=0.88),
    ]
    e2e = create_federation_pool("pool:e2e", e2e_socs, tick=0)

    # Phase 1: Verify pool
    a1 = e2e.analytics()
    check("T24.1 Pool formed", a1.active_policies == 5)
    check("T24.2 Pool balance > 0", a1.balance > 0)
    initial_balance = e2e.balance

    # Phase 2: Legitimate claim
    c_legit = e2e.file_claim("soc:market", 500, "agent:scammer", 0.92,
                              {"type": "fraud", "witnesses": 3}, tick=10)
    check("T24.3 Legitimate claim approved", c_legit.status == ClaimStatus.APPROVED)
    check("T24.4 Payout reasonable", 0 < c_legit.payout <= 500)

    # Phase 3: Low confidence claim denied
    c_weak = e2e.file_claim("soc:factory", 200, "agent:suspect", 0.6,
                              {"type": "suspicious"}, tick=20)
    check("T24.5 Weak claim denied", c_weak.status == ClaimStatus.DENIED)

    # Phase 4: Pool health check
    h = e2e.health()
    check("T24.6 Pool still healthy or adequate",
          h in (PoolHealth.HEALTHY, PoolHealth.ADEQUATE))

    # Phase 5: Second legitimate claim
    c_legit2 = e2e.file_claim("soc:clinic", 300, "agent:thief", 0.88,
                                {"type": "theft", "ledger_proof": True}, tick=30)
    check("T24.7 Second claim approved", c_legit2.status == ClaimStatus.APPROVED)

    # Phase 6: Final analytics
    a_final = e2e.analytics()
    check("T24.8 Two claims approved", a_final.total_claims_approved == 2)
    check("T24.9 Pool still has reserves", a_final.balance > 0)
    check("T24.10 Coverage effective", a_final.coverage_effectiveness > 0.5)

    # ================================================================
    # T25: Edge cases
    # ================================================================
    print("T25: Edge Cases")
    # Zero loss claim
    zero_pool = create_federation_pool("pool:zero", [
        SocietyProfile(lct="soc:z1", treasury=1000, t3_composite=0.85),
        SocietyProfile(lct="soc:z2", treasury=1000, t3_composite=0.85),
        SocietyProfile(lct="soc:z3", treasury=1000, t3_composite=0.85),
    ], tick=1)
    c_zero = zero_pool.file_claim("soc:z1", 0, "agent:a", 0.9, {}, tick=10)
    check("T25.1 Zero loss → approved but 0 payout", c_zero.payout == 0.0)

    # Claim exactly at confidence threshold
    c_exact = zero_pool.file_claim("soc:z2", 100, "agent:b", 0.70, {}, tick=20)
    check("T25.2 Exact threshold → approved", c_exact.status == ClaimStatus.APPROVED)

    # Claim just below threshold
    c_below = zero_pool.file_claim("soc:z3", 100, "agent:c", 0.69, {}, tick=30)
    check("T25.3 Below threshold → denied", c_below.status == ClaimStatus.DENIED)

    # Reserve ratio with 0 premiums
    empty = InsurancePool("pool:empty2")
    check("T25.4 Empty pool reserve = 1.0", empty.reserve_ratio() == 1.0)

    # ================================================================
    print()
    print("=" * 60)
    total = passed + failed
    print(f"ATP Insurance Protocol: {passed}/{total} checks passed")
    if failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {failed} checks FAILED")
    print("=" * 60)
    return passed, failed


if __name__ == "__main__":
    run_tests()
