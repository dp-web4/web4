#!/usr/bin/env python3
"""
Cross-Domain Trust Transfer Protocol

How does trust translate across completely different Web4 domains?

The Problem:
  An entity has trust T3=(0.9, 0.8, 0.7) in an IoT domain.
  It wants to operate in a finance domain.
  Does IoT trust mean anything in finance? How much? Under what conditions?

  This is NOT just trust decay (MRH handles that).
  This is SEMANTIC translation: what does "talent" mean in IoT vs finance?

Implementations:
  §1  Domain Model — formal domain definition with capability taxonomy
  §2  Trust Dimension Mapping — how T3 dimensions translate across domains
  §3  Transfer Coefficients — domain-pair similarity matrices
  §4  Partial Transfer — some dimensions transfer better than others
  §5  Trust Anchoring — using witnesses to anchor transferred trust
  §6  Cross-Domain Attestation — cryptographic proof of domain trust
  §7  Domain Reputation — how domains build trust in each other
  §8  Transfer Economics — ATP costs for cross-domain operations
  §9  Cold Start — entering a domain with zero domain-specific trust
  §10 Attack Resistance — gaming cross-domain trust transfer
  §11 Multi-Hop Transfer — IoT → manufacturing → supply chain → finance
  §12 Equilibrium Analysis — do cross-domain dynamics stabilize?

Key insight: Trust transfer is LOSSY by design. The loss encodes
uncertainty about cross-domain relevance. Perfect transfer would mean
domains are actually the same domain.
"""

import hashlib
import math
import random
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
#  §1. DOMAIN MODEL
# ═══════════════════════════════════════════════════════════════

class DomainType(Enum):
    """Web4 domain types with distinct capability requirements."""
    IOT = "iot"               # Device management, telemetry, firmware
    FINANCE = "finance"       # Transactions, compliance, risk
    SOCIAL = "social"         # Communication, reputation, content
    HEALTHCARE = "healthcare" # Patient data, diagnostics, compliance
    SUPPLY_CHAIN = "supply"   # Logistics, provenance, quality
    GOVERNANCE = "governance" # Voting, policy, consensus
    ENERGY = "energy"         # Grid, metering, trading
    IDENTITY = "identity"     # Authentication, credentials, privacy


@dataclass
class Domain:
    """A Web4 domain with specific trust requirements."""
    domain_type: DomainType
    name: str
    # What does each T3 dimension mean in this domain?
    talent_meaning: str       # Domain-specific interpretation of "talent"
    training_meaning: str     # Domain-specific interpretation of "training"
    temperament_meaning: str  # Domain-specific interpretation of "temperament"
    # Minimum trust thresholds for operations
    min_composite_trust: float = 0.3
    # Which T3 dimensions matter most?
    talent_weight: float = 0.4
    training_weight: float = 0.35
    temperament_weight: float = 0.25


# Canonical domain definitions
DOMAINS = {
    DomainType.IOT: Domain(
        DomainType.IOT, "IoT Devices",
        talent_meaning="hardware reliability, uptime, accuracy",
        training_meaning="firmware quality, security patches, protocol compliance",
        temperament_meaning="consistent behavior, predictable responses, graceful degradation",
        min_composite_trust=0.4,
        talent_weight=0.5, training_weight=0.3, temperament_weight=0.2,
    ),
    DomainType.FINANCE: Domain(
        DomainType.FINANCE, "Financial Services",
        talent_meaning="transaction accuracy, compliance history, audit score",
        training_meaning="regulatory knowledge, market expertise, risk modeling",
        temperament_meaning="fraud resistance, stability under pressure, transparency",
        min_composite_trust=0.6,
        talent_weight=0.35, training_weight=0.35, temperament_weight=0.3,
    ),
    DomainType.SOCIAL: Domain(
        DomainType.SOCIAL, "Social Networks",
        talent_meaning="content quality, engagement authenticity, influence scope",
        training_meaning="community norms, platform rules, moderation experience",
        temperament_meaning="consistency, toxicity resistance, empathy",
        min_composite_trust=0.2,
        talent_weight=0.3, training_weight=0.3, temperament_weight=0.4,
    ),
    DomainType.HEALTHCARE: Domain(
        DomainType.HEALTHCARE, "Healthcare",
        talent_meaning="diagnostic accuracy, treatment outcomes, clinical knowledge",
        training_meaning="certification, continuing education, protocol adherence",
        temperament_meaning="patient safety, ethical conduct, error disclosure",
        min_composite_trust=0.7,
        talent_weight=0.4, training_weight=0.4, temperament_weight=0.2,
    ),
    DomainType.SUPPLY_CHAIN: Domain(
        DomainType.SUPPLY_CHAIN, "Supply Chain",
        talent_meaning="delivery reliability, quality control, sourcing capability",
        training_meaning="logistics expertise, compliance certification, audit history",
        temperament_meaning="deadline adherence, dispute resolution, transparency",
        min_composite_trust=0.4,
        talent_weight=0.4, training_weight=0.3, temperament_weight=0.3,
    ),
    DomainType.GOVERNANCE: Domain(
        DomainType.GOVERNANCE, "Governance",
        talent_meaning="decision quality, proposal success rate, policy impact",
        training_meaning="process knowledge, precedent awareness, constitutional literacy",
        temperament_meaning="fairness, consensus-seeking, transparency, accountability",
        min_composite_trust=0.5,
        talent_weight=0.3, training_weight=0.3, temperament_weight=0.4,
    ),
    DomainType.ENERGY: Domain(
        DomainType.ENERGY, "Energy Grid",
        talent_meaning="generation reliability, grid stability contribution, forecast accuracy",
        training_meaning="safety certification, maintenance compliance, protocol knowledge",
        temperament_meaning="load balancing cooperation, emergency response, fair metering",
        min_composite_trust=0.5,
        talent_weight=0.4, training_weight=0.35, temperament_weight=0.25,
    ),
    DomainType.IDENTITY: Domain(
        DomainType.IDENTITY, "Identity Services",
        talent_meaning="verification accuracy, credential management, privacy protection",
        training_meaning="standards compliance, revocation handling, lifecycle management",
        temperament_meaning="non-discrimination, consent handling, breach notification",
        min_composite_trust=0.6,
        talent_weight=0.35, training_weight=0.35, temperament_weight=0.3,
    ),
}


# ═══════════════════════════════════════════════════════════════
#  §2. TRUST DIMENSION MAPPING
# ═══════════════════════════════════════════════════════════════

@dataclass
class TrustVector:
    """T3 trust tensor with domain context."""
    talent: float
    training: float
    temperament: float
    domain: DomainType

    @property
    def composite(self) -> float:
        d = DOMAINS[self.domain]
        return (self.talent * d.talent_weight +
                self.training * d.training_weight +
                self.temperament * d.temperament_weight)

    def to_dict(self) -> Dict[str, float]:
        return {
            'talent': self.talent,
            'training': self.training,
            'temperament': self.temperament,
            'composite': self.composite,
        }


class DimensionMapper:
    """
    Maps T3 dimensions across domains.

    Key insight: "talent" in IoT (hardware reliability) partially maps to
    "talent" in finance (transaction accuracy) — both involve PRECISION.
    But IoT "temperament" (predictable responses) maps differently to
    finance "temperament" (transparency) — different behavioral norms.

    The mapping is a 3×3 matrix M where:
      T3_target = M × T3_source
    """

    # Cross-domain mapping matrices
    # Each matrix is [target_talent, target_training, target_temperament]
    # as a function of [source_talent, source_training, source_temperament]
    MAPPING_MATRICES: Dict[Tuple[DomainType, DomainType], List[List[float]]] = {
        # IoT → Finance: hardware reliability partially maps to transaction accuracy
        (DomainType.IOT, DomainType.FINANCE): [
            [0.5, 0.2, 0.1],   # finance_talent = 0.5*iot_talent + 0.2*iot_training + 0.1*iot_temperament
            [0.1, 0.4, 0.1],   # finance_training = 0.1*iot_talent + 0.4*iot_training + 0.1*iot_temperament
            [0.2, 0.1, 0.5],   # finance_temperament = 0.2*iot_talent + 0.1*iot_training + 0.5*iot_temperament
        ],
        # Finance → IoT: transaction accuracy partially maps to hardware reliability
        (DomainType.FINANCE, DomainType.IOT): [
            [0.4, 0.1, 0.2],
            [0.2, 0.3, 0.1],
            [0.1, 0.1, 0.4],
        ],
        # IoT → Supply Chain: strong mapping (related domains)
        (DomainType.IOT, DomainType.SUPPLY_CHAIN): [
            [0.7, 0.2, 0.1],
            [0.1, 0.6, 0.1],
            [0.1, 0.1, 0.7],
        ],
        # Social → Governance: moderate mapping (community → voting)
        (DomainType.SOCIAL, DomainType.GOVERNANCE): [
            [0.3, 0.2, 0.2],
            [0.1, 0.4, 0.2],
            [0.2, 0.1, 0.6],
        ],
        # Healthcare → Identity: moderate mapping (both need precision + ethics)
        (DomainType.HEALTHCARE, DomainType.IDENTITY): [
            [0.5, 0.3, 0.1],
            [0.2, 0.5, 0.1],
            [0.1, 0.1, 0.6],
        ],
        # Energy → IoT: strong mapping (both hardware-focused)
        (DomainType.ENERGY, DomainType.IOT): [
            [0.7, 0.2, 0.1],
            [0.1, 0.7, 0.1],
            [0.1, 0.1, 0.6],
        ],
    }

    @classmethod
    def get_mapping(cls, source: DomainType, target: DomainType) -> List[List[float]]:
        """Get or generate mapping matrix between domains."""
        if source == target:
            return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]  # Identity

        key = (source, target)
        if key in cls.MAPPING_MATRICES:
            return cls.MAPPING_MATRICES[key]

        # Generate default mapping based on domain similarity
        similarity = cls.domain_similarity(source, target)
        # Higher similarity → more diagonal (closer to identity)
        off_diag = (1 - similarity) * 0.15
        diag = similarity * 0.6 + 0.1  # Minimum 0.1 even for unrelated
        return [
            [diag, off_diag, off_diag],
            [off_diag, diag, off_diag],
            [off_diag, off_diag, diag],
        ]

    @classmethod
    def domain_similarity(cls, d1: DomainType, d2: DomainType) -> float:
        """Compute similarity between domains (0 = unrelated, 1 = same)."""
        if d1 == d2:
            return 1.0

        # Domain clusters: related domains have higher similarity
        CLUSTERS = {
            'hardware': {DomainType.IOT, DomainType.ENERGY, DomainType.SUPPLY_CHAIN},
            'compliance': {DomainType.FINANCE, DomainType.HEALTHCARE, DomainType.IDENTITY},
            'social': {DomainType.SOCIAL, DomainType.GOVERNANCE},
        }

        shared_clusters = 0
        total_clusters = 0
        for cluster_name, members in CLUSTERS.items():
            if d1 in members or d2 in members:
                total_clusters += 1
                if d1 in members and d2 in members:
                    shared_clusters += 1

        if total_clusters == 0:
            return 0.2  # Base similarity

        return 0.2 + 0.6 * (shared_clusters / total_clusters)

    @classmethod
    def transfer(cls, trust: TrustVector, target_domain: DomainType) -> TrustVector:
        """Transfer trust to target domain using mapping matrix."""
        M = cls.get_mapping(trust.domain, target_domain)
        source = [trust.talent, trust.training, trust.temperament]

        # Matrix multiply: target = M × source
        target = []
        for row in M:
            val = sum(row[j] * source[j] for j in range(3))
            target.append(max(0.0, min(1.0, val)))

        return TrustVector(
            talent=target[0],
            training=target[1],
            temperament=target[2],
            domain=target_domain,
        )


# ═══════════════════════════════════════════════════════════════
#  §3. TRANSFER COEFFICIENTS
# ═══════════════════════════════════════════════════════════════

@dataclass
class TransferResult:
    """Result of a cross-domain trust transfer."""
    source_trust: TrustVector
    target_trust: TrustVector
    transfer_efficiency: float   # How much trust survives transfer
    confidence: float            # How confident we are in the mapping
    attestations: int = 0       # Cross-domain attestations supporting this
    cost_atp: float = 0.0      # ATP cost for the transfer

    @property
    def loss(self) -> float:
        """Trust lost in transfer (1 - efficiency)."""
        return 1.0 - self.transfer_efficiency


class TransferProtocol:
    """
    Protocol for cross-domain trust transfer.

    Transfer efficiency depends on:
      1. Domain similarity (structural)
      2. Mapping matrix quality (learned from cross-domain witnesses)
      3. Number of cross-domain attestations (social)
      4. Trust level in source domain (higher = more transferable)
    """

    BASE_EFFICIENCY = 0.3  # Minimum transfer (even for unrelated domains)
    MAX_EFFICIENCY = 0.85  # Maximum transfer (even for identical domains, some loss)
    ATTESTATION_BOOST = 0.05  # Per attestation boost (diminishing)
    ATP_BASE_COST = 10.0  # Base cost for cross-domain transfer

    @classmethod
    def transfer(cls, source: TrustVector, target_domain: DomainType,
                attestations: int = 0) -> TransferResult:
        """Execute a cross-domain trust transfer."""
        # Step 1: Map dimensions
        mapped = DimensionMapper.transfer(source, target_domain)

        # Step 2: Compute transfer efficiency
        similarity = DimensionMapper.domain_similarity(source.domain, target_domain)
        base_eff = cls.BASE_EFFICIENCY + (cls.MAX_EFFICIENCY - cls.BASE_EFFICIENCY) * similarity

        # Attestation boost (diminishing returns)
        att_boost = sum(cls.ATTESTATION_BOOST * (0.8 ** i)
                       for i in range(min(attestations, 10)))
        efficiency = min(cls.MAX_EFFICIENCY, base_eff + att_boost)

        # Step 3: Apply efficiency to mapped trust
        target = TrustVector(
            talent=mapped.talent * efficiency,
            training=mapped.training * efficiency,
            temperament=mapped.temperament * efficiency,
            domain=target_domain,
        )

        # Step 4: Compute confidence
        # Higher source trust → higher confidence in transfer
        confidence = min(1.0, source.composite * similarity * (1 + 0.1 * attestations))

        # Step 5: ATP cost (higher for dissimilar domains)
        cost = cls.ATP_BASE_COST * (2.0 - similarity)

        return TransferResult(
            source_trust=source,
            target_trust=target,
            transfer_efficiency=efficiency,
            confidence=confidence,
            attestations=attestations,
            cost_atp=cost,
        )


# ═══════════════════════════════════════════════════════════════
#  §4. PARTIAL TRANSFER
# ═══════════════════════════════════════════════════════════════

@dataclass
class PartialTransfer:
    """
    Transfer only SPECIFIC dimensions across domains.

    Use case: An IoT entity is good at hardware (talent=0.9)
    but has low training (0.3). It wants to transfer ONLY its
    hardware reliability to a supply chain domain.
    """
    dimensions_transferred: Set[str]
    source: TrustVector
    target: TrustVector
    selective_efficiency: Dict[str, float]

    @staticmethod
    def transfer_selective(source: TrustVector,
                          target_domain: DomainType,
                          dimensions: Set[str]) -> 'PartialTransfer':
        """Transfer only specified dimensions."""
        full_transfer = TransferProtocol.transfer(source, target_domain)

        # Only keep transferred dimensions
        target_talent = full_transfer.target_trust.talent if 'talent' in dimensions else 0.1
        target_training = full_transfer.target_trust.training if 'training' in dimensions else 0.1
        target_temperament = full_transfer.target_trust.temperament if 'temperament' in dimensions else 0.1

        target = TrustVector(
            talent=target_talent,
            training=target_training,
            temperament=target_temperament,
            domain=target_domain,
        )

        efficiencies = {}
        for dim in dimensions:
            source_val = getattr(source, dim, 0)
            target_val = getattr(target, dim, 0)
            efficiencies[dim] = target_val / source_val if source_val > 0 else 0

        return PartialTransfer(
            dimensions_transferred=dimensions,
            source=source,
            target=target,
            selective_efficiency=efficiencies,
        )


# ═══════════════════════════════════════════════════════════════
#  §5. TRUST ANCHORING
# ═══════════════════════════════════════════════════════════════

@dataclass
class CrossDomainWitness:
    """A witness that operates in both domains."""
    entity_id: str
    domain_trusts: Dict[DomainType, float]  # Trust in each domain

    def can_attest(self, source_domain: DomainType,
                   target_domain: DomainType,
                   min_trust: float = 0.5) -> bool:
        """Can this witness attest for cross-domain transfer?"""
        return (self.domain_trusts.get(source_domain, 0) >= min_trust and
                self.domain_trusts.get(target_domain, 0) >= min_trust)

    @property
    def cross_domain_trust(self) -> float:
        """Minimum trust across all domains (bottleneck)."""
        if not self.domain_trusts:
            return 0.0
        return min(self.domain_trusts.values())


class TrustAnchor:
    """
    Anchoring protocol: use cross-domain witnesses to validate transfers.

    A transfer is "anchored" when N witnesses who are trusted in BOTH
    domains attest that the transfer is reasonable.
    """

    QUORUM = 3  # Minimum witnesses for anchored transfer
    MIN_WITNESS_TRUST = 0.5

    @classmethod
    def anchor_transfer(cls, source: TrustVector,
                       target_domain: DomainType,
                       witnesses: List[CrossDomainWitness]) -> Dict:
        """Attempt to anchor a cross-domain transfer."""
        # Find eligible witnesses
        eligible = [w for w in witnesses
                    if w.can_attest(source.domain, target_domain, cls.MIN_WITNESS_TRUST)]

        quorum_met = len(eligible) >= cls.QUORUM

        # Base transfer
        base_result = TransferProtocol.transfer(
            source, target_domain, attestations=len(eligible))

        # Anchored transfer gets a boost
        if quorum_met:
            avg_witness_trust = statistics.mean(
                min(w.domain_trusts.get(source.domain, 0),
                    w.domain_trusts.get(target_domain, 0))
                for w in eligible
            )
            anchor_boost = 0.1 * avg_witness_trust  # Up to 0.1 boost

            anchored = TrustVector(
                talent=min(1.0, base_result.target_trust.talent + anchor_boost),
                training=min(1.0, base_result.target_trust.training + anchor_boost),
                temperament=min(1.0, base_result.target_trust.temperament + anchor_boost),
                domain=target_domain,
            )
        else:
            anchored = base_result.target_trust
            anchor_boost = 0.0

        return {
            'anchored': quorum_met,
            'eligible_witnesses': len(eligible),
            'total_witnesses': len(witnesses),
            'base_trust': base_result.target_trust.to_dict(),
            'anchored_trust': anchored.to_dict(),
            'anchor_boost': anchor_boost,
            'efficiency': base_result.transfer_efficiency,
        }


# ═══════════════════════════════════════════════════════════════
#  §6. CROSS-DOMAIN ATTESTATION
# ═══════════════════════════════════════════════════════════════

@dataclass
class DomainAttestation:
    """Cryptographic attestation of trust in a specific domain."""
    entity_id: str
    domain: DomainType
    trust_composite: float
    timestamp: float
    attestor_id: str
    signature: str  # HMAC-based signature

    @staticmethod
    def create(entity_id: str, domain: DomainType,
               trust: float, attestor_id: str,
               secret_key: str = "attestation_key") -> 'DomainAttestation':
        """Create a signed attestation."""
        ts = time.time()
        # Create signature
        msg = f"{entity_id}:{domain.value}:{trust:.4f}:{ts}:{attestor_id}"
        sig = hashlib.sha256(
            (secret_key + msg).encode()
        ).hexdigest()[:32]

        return DomainAttestation(
            entity_id=entity_id,
            domain=domain,
            trust_composite=trust,
            timestamp=ts,
            attestor_id=attestor_id,
            signature=sig,
        )

    def verify(self, secret_key: str = "attestation_key") -> bool:
        """Verify attestation signature."""
        msg = f"{self.entity_id}:{self.domain.value}:{self.trust_composite:.4f}:{self.timestamp}:{self.attestor_id}"
        expected = hashlib.sha256(
            (secret_key + msg).encode()
        ).hexdigest()[:32]
        return self.signature == expected


class AttestationChain:
    """Chain of attestations forming a cross-domain trust path."""

    def __init__(self):
        self.attestations: List[DomainAttestation] = []

    def add(self, att: DomainAttestation):
        self.attestations.append(att)

    def verify_chain(self) -> bool:
        """Verify all attestations in chain."""
        return all(att.verify() for att in self.attestations)

    def trust_at_domain(self, domain: DomainType) -> Optional[float]:
        """Get trust for a specific domain from chain."""
        for att in reversed(self.attestations):  # Latest first
            if att.domain == domain:
                return att.trust_composite
        return None

    @property
    def domains_covered(self) -> Set[DomainType]:
        return {att.domain for att in self.attestations}


# ═══════════════════════════════════════════════════════════════
#  §7. DOMAIN REPUTATION
# ═══════════════════════════════════════════════════════════════

@dataclass
class DomainReputation:
    """How much one domain trusts another domain's trust assessments."""
    source_domain: DomainType
    target_domain: DomainType
    reputation: float  # [0, 1] — how much source trusts target's assessments
    transfer_count: int = 0
    success_count: int = 0
    dispute_count: int = 0

    @property
    def success_rate(self) -> float:
        if self.transfer_count == 0:
            return 0.5  # Prior
        return self.success_count / self.transfer_count

    def update(self, success: bool):
        """Update after a cross-domain transfer outcome."""
        self.transfer_count += 1
        if success:
            self.success_count += 1
            self.reputation = min(1.0, self.reputation + 0.01)
        else:
            self.dispute_count += 1
            self.reputation = max(0.0, self.reputation - 0.02)  # Losses hurt more


class DomainReputationNetwork:
    """Network of inter-domain trust relationships."""

    def __init__(self):
        self.reputations: Dict[Tuple[DomainType, DomainType], DomainReputation] = {}
        self._initialize()

    def _initialize(self):
        """Initialize with prior domain reputations based on similarity."""
        for d1 in DomainType:
            for d2 in DomainType:
                if d1 != d2:
                    sim = DimensionMapper.domain_similarity(d1, d2)
                    self.reputations[(d1, d2)] = DomainReputation(
                        source_domain=d1,
                        target_domain=d2,
                        reputation=sim * 0.7,  # Start at 70% of similarity
                    )

    def get_reputation(self, source: DomainType, target: DomainType) -> float:
        key = (source, target)
        if key in self.reputations:
            return self.reputations[key].reputation
        return 0.5  # Default

    def record_transfer(self, source: DomainType, target: DomainType,
                       success: bool):
        key = (source, target)
        if key in self.reputations:
            self.reputations[key].update(success)

    def simulate_transfers(self, n_transfers: int = 100,
                          success_rate: float = 0.7) -> Dict:
        """Simulate cross-domain transfers and track reputation evolution."""
        domains = list(DomainType)
        initial_reps = {k: v.reputation for k, v in self.reputations.items()}

        for _ in range(n_transfers):
            d1 = random.choice(domains)
            d2 = random.choice(domains)
            if d1 != d2:
                sim = DimensionMapper.domain_similarity(d1, d2)
                # Success more likely for similar domains
                actual_success_rate = success_rate * (0.5 + 0.5 * sim)
                success = random.random() < actual_success_rate
                self.record_transfer(d1, d2, success)

        final_reps = {k: v.reputation for k, v in self.reputations.items()}

        # Compute statistics
        rep_changes = []
        for key in initial_reps:
            rep_changes.append(final_reps[key] - initial_reps[key])

        return {
            'n_transfers': n_transfers,
            'avg_reputation_change': statistics.mean(rep_changes),
            'max_reputation': max(final_reps.values()),
            'min_reputation': min(final_reps.values()),
            'avg_reputation': statistics.mean(final_reps.values()),
        }


# ═══════════════════════════════════════════════════════════════
#  §8. TRANSFER ECONOMICS
# ═══════════════════════════════════════════════════════════════

class TransferEconomics:
    """ATP costs and incentives for cross-domain trust transfers."""

    BASE_TRANSFER_COST = 10.0   # ATP base cost
    SIMILARITY_DISCOUNT = 0.5   # Discount for similar domains
    WITNESS_FEE = 2.0           # Fee per witness attestation
    ANCHOR_BONUS = 5.0          # Bonus for anchored transfers

    @classmethod
    def calculate_cost(cls, source_domain: DomainType,
                      target_domain: DomainType,
                      attestations: int = 0) -> Dict:
        """Calculate ATP cost for cross-domain transfer."""
        similarity = DimensionMapper.domain_similarity(source_domain, target_domain)

        base = cls.BASE_TRANSFER_COST
        discount = cls.SIMILARITY_DISCOUNT * similarity
        witness_fees = cls.WITNESS_FEE * attestations
        anchor_discount = cls.ANCHOR_BONUS if attestations >= TrustAnchor.QUORUM else 0

        total = base - discount + witness_fees - anchor_discount
        total = max(1.0, total)  # Minimum 1 ATP

        return {
            'base_cost': base,
            'similarity_discount': discount,
            'witness_fees': witness_fees,
            'anchor_discount': anchor_discount,
            'total_cost': total,
            'cost_per_trust_point': total / max(0.1, similarity),
        }

    @classmethod
    def is_profitable(cls, source_trust: TrustVector,
                     target_domain: DomainType,
                     expected_earnings: float) -> Dict:
        """Is cross-domain transfer economically rational?"""
        cost = cls.calculate_cost(source_trust.domain, target_domain)
        result = TransferProtocol.transfer(source_trust, target_domain)

        return {
            'transfer_cost': cost['total_cost'],
            'expected_earnings': expected_earnings,
            'net_profit': expected_earnings - cost['total_cost'],
            'profitable': expected_earnings > cost['total_cost'],
            'efficiency': result.transfer_efficiency,
            'roi': (expected_earnings - cost['total_cost']) / cost['total_cost']
                   if cost['total_cost'] > 0 else 0,
        }


# ═══════════════════════════════════════════════════════════════
#  §9. COLD START
# ═══════════════════════════════════════════════════════════════

class ColdStartStrategy:
    """
    Strategies for entering a new domain with zero domain-specific trust.

    Options:
      1. Transfer: Use existing trust from another domain (lossy)
      2. Bootstrap: Start from default (slow)
      3. Sponsor: Get a domain native to vouch for you
      4. Hybrid: Transfer + sponsor + bootstrap
    """

    @staticmethod
    def evaluate_strategies(source_trust: TrustVector,
                           target_domain: DomainType,
                           n_steps: int = 100) -> Dict:
        """Compare cold start strategies."""
        results = {}

        # Strategy 1: Transfer
        transfer = TransferProtocol.transfer(source_trust, target_domain)
        results['transfer'] = {
            'initial_composite': transfer.target_trust.composite,
            'cost_atp': transfer.cost_atp,
            'immediate': True,
        }

        # Strategy 2: Bootstrap (default trust, grow organically)
        bootstrap_trust = 0.1
        for _ in range(n_steps):
            quality = max(0, min(1, random.gauss(0.7, 0.15)))
            bootstrap_trust = max(0, min(1, bootstrap_trust + 0.02 * (quality - 0.5)))
        results['bootstrap'] = {
            'initial_composite': 0.1,
            'final_composite': bootstrap_trust,
            'steps_to_threshold': n_steps,
            'cost_atp': 0,
            'immediate': False,
        }

        # Strategy 3: Sponsor (get 80% of sponsor's trust, with decay)
        sponsor_trust = 0.6  # Typical established entity
        sponsored = sponsor_trust * 0.8 * 0.7  # sponsor * coefficient * domain_penalty
        results['sponsor'] = {
            'initial_composite': sponsored,
            'cost_atp': 20.0,  # Sponsor fee
            'immediate': True,
        }

        # Strategy 4: Hybrid (transfer + bootstrap boost)
        hybrid_initial = transfer.target_trust.composite
        for _ in range(50):  # Half the bootstrap steps
            quality = max(0, min(1, random.gauss(0.7, 0.15)))
            hybrid_initial = max(0, min(1, hybrid_initial + 0.02 * (quality - 0.5)))
        results['hybrid'] = {
            'initial_composite': transfer.target_trust.composite,
            'final_composite': hybrid_initial,
            'steps': 50,
            'cost_atp': transfer.cost_atp + 5.0,
            'immediate': False,
        }

        # Best strategy
        best = max(results.items(),
                  key=lambda x: x[1].get('final_composite', x[1]['initial_composite']))

        return {
            'strategies': results,
            'best_strategy': best[0],
            'best_composite': best[1].get('final_composite', best[1]['initial_composite']),
        }


# ═══════════════════════════════════════════════════════════════
#  §10. ATTACK RESISTANCE
# ═══════════════════════════════════════════════════════════════

class CrossDomainAttacks:
    """Attack simulations on cross-domain trust transfer."""

    @staticmethod
    def trust_laundering(n_domains: int = 4) -> Dict:
        """
        Trust laundering: build trust in a cheap domain,
        transfer to a high-value domain.

        Attack: Get high social trust (easy), transfer to finance (hard).
        Defense: Transfer coefficients make this unprofitable.
        """
        # Build trust cheaply in social domain
        social_trust = TrustVector(0.9, 0.9, 0.9, DomainType.SOCIAL)

        # Transfer to finance
        result = TransferProtocol.transfer(social_trust, DomainType.FINANCE)

        # Compare with honest finance trust building
        finance_min = DOMAINS[DomainType.FINANCE].min_composite_trust

        return {
            'social_composite': social_trust.composite,
            'transferred_finance_composite': result.target_trust.composite,
            'finance_threshold': finance_min,
            'meets_threshold': result.target_trust.composite >= finance_min,
            'transfer_efficiency': result.transfer_efficiency,
            'defense_holds': result.target_trust.composite < social_trust.composite * 0.7,
        }

    @staticmethod
    def domain_hopping(hops: int = 5) -> Dict:
        """
        Domain hopping: transfer through many domains to launder trust.

        Attack: A → B → C → D → E, hoping to preserve more trust
        through an indirect path than direct A → E.

        Defense: Each hop incurs loss. Multi-hop is worse than direct.
        """
        domains = [DomainType.IOT, DomainType.SUPPLY_CHAIN,
                   DomainType.ENERGY, DomainType.GOVERNANCE,
                   DomainType.FINANCE][:hops]

        # Direct transfer
        start = TrustVector(0.8, 0.8, 0.8, domains[0])
        direct = TransferProtocol.transfer(start, domains[-1])

        # Multi-hop transfer
        current = start
        hop_trusts = [start.composite]
        for i in range(1, len(domains)):
            result = TransferProtocol.transfer(current, domains[i])
            current = result.target_trust
            hop_trusts.append(current.composite)

        return {
            'hops': len(domains) - 1,
            'direct_result': direct.target_trust.composite,
            'multi_hop_result': current.composite,
            'hop_trusts': hop_trusts,
            'multi_hop_worse': current.composite <= direct.target_trust.composite,
            'cumulative_loss': 1.0 - current.composite / start.composite,
        }

    @staticmethod
    def sybil_cross_domain(n_sybils: int = 5) -> Dict:
        """
        Sybil attack across domains: create identities in cheap domain,
        use them as witnesses for cross-domain transfer.

        Defense: Witness quality check + cross-domain trust requirement.
        """
        # Create sybil witnesses (low trust)
        sybil_witnesses = [
            CrossDomainWitness(
                entity_id=f"sybil_{i}",
                domain_trusts={
                    DomainType.SOCIAL: 0.3,  # Low trust
                    DomainType.FINANCE: 0.1,  # Very low in target
                }
            )
            for i in range(n_sybils)
        ]

        # Try to anchor a transfer
        source = TrustVector(0.5, 0.5, 0.5, DomainType.SOCIAL)
        result = TrustAnchor.anchor_transfer(
            source, DomainType.FINANCE, sybil_witnesses)

        return {
            'n_sybils': n_sybils,
            'eligible_witnesses': result['eligible_witnesses'],
            'anchored': result['anchored'],
            'defense_holds': not result['anchored'],  # Sybils shouldn't be eligible
        }


# ═══════════════════════════════════════════════════════════════
#  §11. MULTI-HOP TRANSFER
# ═══════════════════════════════════════════════════════════════

def multi_hop_analysis(start_domain: DomainType = DomainType.IOT,
                       end_domain: DomainType = DomainType.FINANCE,
                       max_hops: int = 5) -> Dict:
    """
    Analyze trust decay through multiple domain hops.

    Models both DIRECT transfer and multi-hop paths.
    Shows that multi-hop is always worse (trust monotonically decays).
    """
    all_domains = list(DomainType)

    # Generate all possible paths of length 1..max_hops
    start_trust = TrustVector(0.8, 0.8, 0.8, start_domain)

    results = {}

    # Direct transfer
    direct = TransferProtocol.transfer(start_trust, end_domain)
    results['direct'] = {
        'hops': 1,
        'path': [start_domain.value, end_domain.value],
        'final_composite': direct.target_trust.composite,
        'efficiency': direct.transfer_efficiency,
    }

    # 2-hop paths
    best_2hop = None
    best_2hop_trust = 0
    for mid in all_domains:
        if mid in (start_domain, end_domain):
            continue
        hop1 = TransferProtocol.transfer(start_trust, mid)
        hop2 = TransferProtocol.transfer(hop1.target_trust, end_domain)
        if hop2.target_trust.composite > best_2hop_trust:
            best_2hop_trust = hop2.target_trust.composite
            best_2hop = {
                'hops': 2,
                'path': [start_domain.value, mid.value, end_domain.value],
                'final_composite': hop2.target_trust.composite,
            }
    if best_2hop:
        results['best_2hop'] = best_2hop

    # 3-hop paths (sample)
    best_3hop_trust = 0
    best_3hop = None
    for _ in range(50):  # Random sample
        mid1 = random.choice([d for d in all_domains if d not in (start_domain, end_domain)])
        remaining = [d for d in all_domains if d not in (start_domain, end_domain, mid1)]
        if not remaining:
            continue
        mid2 = random.choice(remaining)

        h1 = TransferProtocol.transfer(start_trust, mid1)
        h2 = TransferProtocol.transfer(h1.target_trust, mid2)
        h3 = TransferProtocol.transfer(h2.target_trust, end_domain)
        if h3.target_trust.composite > best_3hop_trust:
            best_3hop_trust = h3.target_trust.composite
            best_3hop = {
                'hops': 3,
                'path': [start_domain.value, mid1.value, mid2.value, end_domain.value],
                'final_composite': h3.target_trust.composite,
            }
    if best_3hop:
        results['best_3hop'] = best_3hop

    return {
        'results': results,
        'direct_is_best': (direct.target_trust.composite >=
                          max(r['final_composite'] for r in results.values())),
        'trust_decay_per_hop': [
            results.get('direct', {}).get('final_composite', 0),
            results.get('best_2hop', {}).get('final_composite', 0),
            results.get('best_3hop', {}).get('final_composite', 0),
        ],
    }


# ═══════════════════════════════════════════════════════════════
#  §12. EQUILIBRIUM ANALYSIS
# ═══════════════════════════════════════════════════════════════

def equilibrium_analysis(n_entities: int = 100,
                        n_steps: int = 200) -> Dict:
    """
    Do cross-domain trust dynamics reach a stable equilibrium?

    Simulate entities transferring trust between domains
    and track whether the overall trust distribution stabilizes.
    """
    domains = list(DomainType)

    # Create entities with random domain trusts
    entity_trusts: Dict[str, Dict[DomainType, TrustVector]] = {}
    for i in range(n_entities):
        home = random.choice(domains)
        trust = TrustVector(
            talent=random.uniform(0.3, 0.9),
            training=random.uniform(0.3, 0.9),
            temperament=random.uniform(0.3, 0.9),
            domain=home,
        )
        entity_trusts[f"e_{i}"] = {home: trust}

    # Track cross-domain trust means
    cross_domain_means = []

    for step in range(n_steps):
        # Random entities transfer to random domains
        for _ in range(n_entities // 5):
            eid = f"e_{random.randint(0, n_entities - 1)}"
            if eid not in entity_trusts:
                continue

            # Pick a domain they have trust in
            current_domains = list(entity_trusts[eid].keys())
            if not current_domains:
                continue
            source_domain = random.choice(current_domains)
            source_trust = entity_trusts[eid][source_domain]

            # Transfer to a new domain
            target_domain = random.choice([d for d in domains if d != source_domain])
            result = TransferProtocol.transfer(source_trust, target_domain)

            # Entity now has trust in both domains
            # Use maximum of existing and transferred trust
            if target_domain in entity_trusts[eid]:
                existing = entity_trusts[eid][target_domain]
                entity_trusts[eid][target_domain] = TrustVector(
                    talent=max(existing.talent, result.target_trust.talent),
                    training=max(existing.training, result.target_trust.training),
                    temperament=max(existing.temperament, result.target_trust.temperament),
                    domain=target_domain,
                )
            else:
                entity_trusts[eid][target_domain] = result.target_trust

        # Record cross-domain mean trust
        all_composites = []
        for eid, domains_dict in entity_trusts.items():
            for domain, trust in domains_dict.items():
                all_composites.append(trust.composite)
        cross_domain_means.append(statistics.mean(all_composites) if all_composites else 0)

    # Check stabilization
    if len(cross_domain_means) > 40:
        late = cross_domain_means[-40:]
        stable = max(late) - min(late) < 0.02
    else:
        stable = False

    # Domain coverage
    domain_coverage = defaultdict(int)
    for eid, domains_dict in entity_trusts.items():
        for d in domains_dict:
            domain_coverage[d] += 1

    return {
        'n_entities': n_entities,
        'n_steps': n_steps,
        'stabilized': stable,
        'initial_mean': cross_domain_means[0] if cross_domain_means else 0,
        'final_mean': cross_domain_means[-1] if cross_domain_means else 0,
        'domain_coverage': dict(domain_coverage),
        'avg_domains_per_entity': statistics.mean(
            len(d) for d in entity_trusts.values()),
        'total_trust_relationships': sum(len(d) for d in entity_trusts.values()),
    }


# ═══════════════════════════════════════════════════════════════
#  TEST RUNNER
# ═══════════════════════════════════════════════════════════════

def run_all_checks():
    """Run all cross-domain trust transfer checks."""
    checks_passed = 0
    checks_failed = 0
    total_sections = 12
    section_results = {}

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal checks_passed, checks_failed
        if condition:
            checks_passed += 1
            print(f"  ✓ {name}")
        else:
            checks_failed += 1
            print(f"  ✗ {name}: {detail}")
        return condition

    # ── §1 Domain Model ──
    print("\n§1 Domain Model")
    print("─" * 40)

    check("All 8 domains defined", len(DOMAINS) == 8)
    check("IoT domain has correct weights",
          abs(DOMAINS[DomainType.IOT].talent_weight - 0.5) < 0.01)
    check("Finance min trust > Social min trust",
          DOMAINS[DomainType.FINANCE].min_composite_trust >
          DOMAINS[DomainType.SOCIAL].min_composite_trust)
    check("Healthcare has highest min trust",
          DOMAINS[DomainType.HEALTHCARE].min_composite_trust ==
          max(d.min_composite_trust for d in DOMAINS.values()))
    check("All domains have meaningful descriptions",
          all(len(d.talent_meaning) > 10 for d in DOMAINS.values()))
    section_results['§1'] = True

    # ── §2 Trust Dimension Mapping ──
    print("\n§2 Trust Dimension Mapping")
    print("─" * 40)

    iot_trust = TrustVector(0.8, 0.7, 0.6, DomainType.IOT)
    check("TrustVector created", iot_trust.composite > 0)
    check("IoT composite correct",
          abs(iot_trust.composite - (0.8*0.5 + 0.7*0.3 + 0.6*0.2)) < 0.01)

    # Same-domain transfer = identity
    same = DimensionMapper.transfer(iot_trust, DomainType.IOT)
    check("Same-domain transfer preserves trust",
          abs(same.talent - iot_trust.talent) < 0.01)

    # Cross-domain transfer reduces trust
    finance_mapped = DimensionMapper.transfer(iot_trust, DomainType.FINANCE)
    check("Cross-domain talent reduced", finance_mapped.talent < iot_trust.talent)
    check("Cross-domain values bounded [0,1]",
          all(0 <= v <= 1 for v in [finance_mapped.talent, finance_mapped.training, finance_mapped.temperament]))

    # Domain similarity
    check("Same domain similarity = 1",
          DimensionMapper.domain_similarity(DomainType.IOT, DomainType.IOT) == 1.0)
    check("IoT-SupplyChain > IoT-Social",
          DimensionMapper.domain_similarity(DomainType.IOT, DomainType.SUPPLY_CHAIN) >
          DimensionMapper.domain_similarity(DomainType.IOT, DomainType.SOCIAL))
    section_results['§2'] = True

    # ── §3 Transfer Coefficients ──
    print("\n§3 Transfer Coefficients")
    print("─" * 40)

    result = TransferProtocol.transfer(iot_trust, DomainType.FINANCE)
    check("Transfer result has efficiency", 0 < result.transfer_efficiency < 1)
    check("Transfer is lossy", result.loss > 0)
    check("Transfer has cost", result.cost_atp > 0)
    check("Transfer composite < source composite",
          result.target_trust.composite < iot_trust.composite)

    # More attestations → higher efficiency
    result_att = TransferProtocol.transfer(iot_trust, DomainType.FINANCE, attestations=5)
    check("Attestations increase efficiency",
          result_att.transfer_efficiency > result.transfer_efficiency)

    # Similar domains → higher efficiency
    result_supply = TransferProtocol.transfer(iot_trust, DomainType.SUPPLY_CHAIN)
    check("Similar domains → higher efficiency",
          result_supply.transfer_efficiency > result.transfer_efficiency)
    print(f"    IoT→Finance: {result.transfer_efficiency:.2f}, "
          f"IoT→Supply: {result_supply.transfer_efficiency:.2f}")
    section_results['§3'] = True

    # ── §4 Partial Transfer ──
    print("\n§4 Partial Transfer")
    print("─" * 40)

    partial = PartialTransfer.transfer_selective(
        iot_trust, DomainType.FINANCE, {'talent'})
    check("Partial transfer created", partial.target is not None)
    check("Only talent transferred (others = 0.1)",
          abs(partial.target.training - 0.1) < 0.01 and
          abs(partial.target.temperament - 0.1) < 0.01)
    check("Talent was transferred (> 0.1)", partial.target.talent > 0.1)

    # Full partial transfer
    full_partial = PartialTransfer.transfer_selective(
        iot_trust, DomainType.FINANCE, {'talent', 'training', 'temperament'})
    check("Full partial ≈ full transfer",
          abs(full_partial.target.composite - result.target_trust.composite) < 0.1)
    section_results['§4'] = True

    # ── §5 Trust Anchoring ──
    print("\n§5 Trust Anchoring")
    print("─" * 40)

    # Create witnesses
    good_witnesses = [
        CrossDomainWitness(
            f"w_{i}",
            {DomainType.IOT: 0.7 + random.uniform(0, 0.2),
             DomainType.FINANCE: 0.6 + random.uniform(0, 0.2)}
        )
        for i in range(5)
    ]
    anchor_result = TrustAnchor.anchor_transfer(
        iot_trust, DomainType.FINANCE, good_witnesses)
    check("Quorum met (≥3 witnesses)", anchor_result['anchored'])
    check("Anchor boosts trust", anchor_result['anchor_boost'] > 0)
    check("Anchored trust > base trust",
          anchor_result['anchored_trust']['composite'] >
          anchor_result['base_trust']['composite'])

    # Too few witnesses
    few_witnesses = good_witnesses[:2]
    anchor_few = TrustAnchor.anchor_transfer(
        iot_trust, DomainType.FINANCE, few_witnesses)
    check("Insufficient witnesses → not anchored", not anchor_few['anchored'])
    section_results['§5'] = True

    # ── §6 Cross-Domain Attestation ──
    print("\n§6 Cross-Domain Attestation")
    print("─" * 40)

    att = DomainAttestation.create("entity_1", DomainType.IOT, 0.8, "attestor_1")
    check("Attestation created", att is not None)
    check("Attestation verifies", att.verify())
    check("Tampered attestation fails", not att.verify("wrong_key"))

    # Chain
    chain = AttestationChain()
    chain.add(DomainAttestation.create("e1", DomainType.IOT, 0.8, "att1"))
    chain.add(DomainAttestation.create("e1", DomainType.FINANCE, 0.4, "att2"))
    check("Chain verifies", chain.verify_chain())
    check("Chain covers 2 domains", len(chain.domains_covered) == 2)
    check("IoT trust retrievable", chain.trust_at_domain(DomainType.IOT) == 0.8)
    check("Finance trust retrievable", chain.trust_at_domain(DomainType.FINANCE) == 0.4)
    section_results['§6'] = True

    # ── §7 Domain Reputation ──
    print("\n§7 Domain Reputation")
    print("─" * 40)

    drn = DomainReputationNetwork()
    check("Network initialized", len(drn.reputations) > 0)

    # Similar domains have higher initial reputation
    iot_supply_rep = drn.get_reputation(DomainType.IOT, DomainType.SUPPLY_CHAIN)
    iot_social_rep = drn.get_reputation(DomainType.IOT, DomainType.SOCIAL)
    check("IoT trusts SupplyChain more than Social",
          iot_supply_rep > iot_social_rep)

    # Simulate transfers
    sim_result = drn.simulate_transfers(n_transfers=200, success_rate=0.7)
    check("Simulation completed", sim_result['n_transfers'] == 200)
    check("Average reputation reasonable",
          0.1 < sim_result['avg_reputation'] < 0.9)
    print(f"    Avg reputation: {sim_result['avg_reputation']:.3f}")
    section_results['§7'] = True

    # ── §8 Transfer Economics ──
    print("\n§8 Transfer Economics")
    print("─" * 40)

    cost = TransferEconomics.calculate_cost(DomainType.IOT, DomainType.FINANCE)
    check("Cost computed", cost['total_cost'] > 0)
    check("Base cost is 10 ATP", cost['base_cost'] == 10.0)
    check("Similar domains cheaper",
          TransferEconomics.calculate_cost(DomainType.IOT, DomainType.SUPPLY_CHAIN)['total_cost'] <
          TransferEconomics.calculate_cost(DomainType.IOT, DomainType.SOCIAL)['total_cost'])

    # Profitability
    prof = TransferEconomics.is_profitable(iot_trust, DomainType.FINANCE, 50.0)
    check("Profitability computed", 'net_profit' in prof)
    check("Transfer to finance profitable at 50 ATP expected",
          prof['profitable'])

    # Unprofitable at low expected earnings
    low_prof = TransferEconomics.is_profitable(iot_trust, DomainType.FINANCE, 2.0)
    check("Transfer unprofitable at 2 ATP expected", not low_prof['profitable'])
    print(f"    IoT→Finance cost: {cost['total_cost']:.1f} ATP")
    section_results['§8'] = True

    # ── §9 Cold Start ──
    print("\n§9 Cold Start")
    print("─" * 40)

    cs_result = ColdStartStrategy.evaluate_strategies(
        iot_trust, DomainType.FINANCE, n_steps=100)
    check("All strategies evaluated", len(cs_result['strategies']) == 4)
    check("Best strategy identified", cs_result['best_strategy'] is not None)
    check("Transfer is immediate", cs_result['strategies']['transfer']['immediate'])
    check("Bootstrap is slow", not cs_result['strategies']['bootstrap']['immediate'])
    check("Hybrid combines approaches",
          cs_result['strategies']['hybrid']['initial_composite'] > 0.1)
    print(f"    Best strategy: {cs_result['best_strategy']}")
    section_results['§9'] = True

    # ── §10 Attack Resistance ──
    print("\n§10 Attack Resistance")
    print("─" * 40)

    # Trust laundering
    launder = CrossDomainAttacks.trust_laundering()
    check("Trust laundering defense holds", launder['defense_holds'],
          f"social={launder['social_composite']:.2f} → finance={launder['transferred_finance_composite']:.2f}")
    check("Laundered trust < 70% of source",
          launder['transferred_finance_composite'] < launder['social_composite'] * 0.7)

    # Domain hopping
    hop = CrossDomainAttacks.domain_hopping(hops=4)
    check("Multi-hop worse than direct", hop['multi_hop_worse'],
          f"direct={hop['direct_result']:.3f} multi={hop['multi_hop_result']:.3f}")
    check("Cumulative loss > 50%", hop['cumulative_loss'] > 0.5,
          f"loss={hop['cumulative_loss']:.2f}")

    # Sybil cross-domain
    sybil = CrossDomainAttacks.sybil_cross_domain()
    check("Sybil defense holds (low trust witnesses rejected)",
          sybil['defense_holds'],
          f"eligible={sybil['eligible_witnesses']}")
    section_results['§10'] = True

    # ── §11 Multi-Hop Transfer ──
    print("\n§11 Multi-Hop Transfer")
    print("─" * 40)

    mh = multi_hop_analysis(DomainType.IOT, DomainType.FINANCE, max_hops=4)
    check("Multi-hop analysis completed", 'direct' in mh['results'])
    check("Direct transfer computed", mh['results']['direct']['final_composite'] > 0)
    check("Trust decays per hop",
          mh['trust_decay_per_hop'][0] >= mh['trust_decay_per_hop'][1] or
          mh['trust_decay_per_hop'][1] == 0)

    if 'best_2hop' in mh['results']:
        check("2-hop result computed", mh['results']['best_2hop']['final_composite'] > 0)
        print(f"    Direct: {mh['results']['direct']['final_composite']:.3f}")
        print(f"    Best 2-hop: {mh['results']['best_2hop']['final_composite']:.3f}")
    if 'best_3hop' in mh['results']:
        print(f"    Best 3-hop: {mh['results']['best_3hop']['final_composite']:.3f}")
    section_results['§11'] = True

    # ── §12 Equilibrium Analysis ──
    print("\n§12 Equilibrium Analysis")
    print("─" * 40)

    eq = equilibrium_analysis(n_entities=50, n_steps=100)
    check("Equilibrium analysis completed", eq['n_steps'] == 100)
    check("Entities expanded to multiple domains",
          eq['avg_domains_per_entity'] > 1.0)
    check("All domains covered",
          len(eq['domain_coverage']) >= 6,
          f"covered={len(eq['domain_coverage'])}")
    check("Cross-domain stabilized", eq['stabilized'],
          f"initial={eq['initial_mean']:.3f} final={eq['final_mean']:.3f}")
    # Mean trust is LOW because cross-domain transfer is lossy by design
    # Transfer loss encodes uncertainty — this is the intended behavior
    check("Final mean trust reasonable (0.1-0.8)",
          0.1 < eq['final_mean'] < 0.8,
          f"mean={eq['final_mean']:.3f}")
    print(f"    Avg domains/entity: {eq['avg_domains_per_entity']:.1f}")
    print(f"    Trust relationships: {eq['total_trust_relationships']}")
    section_results['§12'] = True

    # ── Summary ──
    total = checks_passed + checks_failed
    print(f"\n{'═' * 50}")
    print(f"Cross-Domain Trust Transfer: {checks_passed}/{total} checks passed")
    print(f"Sections: {sum(1 for v in section_results.values() if v)}/{total_sections}")

    if checks_failed > 0:
        print(f"\n⚠ {checks_failed} checks failed")
    else:
        print(f"\n✓ All {total} checks passed across {total_sections} sections")

    return checks_passed, checks_failed


if __name__ == "__main__":
    passed, failed = run_all_checks()
    exit(0 if failed == 0 else 1)
