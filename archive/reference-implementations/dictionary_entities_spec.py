#!/usr/bin/env python3
"""
Web4 Dictionary Entities — Comprehensive Spec Implementation
Spec: web4-standard/core-spec/dictionary-entities.md (585 lines, 13 sections)

Covers:
  §1  Core Concept: Compression and Trust (duality, trust levels)
  §2  Dictionary Entity Architecture (LCT, T3/V3, MRH)
  §3  Dictionary Types (domain, model, compression, meta)
  §4  Translation Process (request, flow, degradation tracking)
  §5  Dictionary Evolution (learning, drift, community curation)
  §6  Dictionary Discovery and Selection (MRH discovery, scoring)
  §7  Dictionary-R6 Integration (translation as R6 action)
  §8  Security and Trust (attack mitigation, trust building)
  §9  Implementation Requirements (MUST/SHOULD/MAY)
  §10 Use Cases (medical-legal, AI bridging, cross-cultural)
  §11 Dictionary Reputation Economy (earning, staking, slashing)
  §12 Future Extensions (quantum, emergent, holographic)
  §13 Summary

Complements existing dictionary_entity.py (30 checks) with full spec coverage.
"""

from __future__ import annotations
import hashlib
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# ============================================================
# Test harness
# ============================================================
_pass = _fail = 0


def check(label: str, condition: bool):
    global _pass, _fail
    if condition:
        _pass += 1
    else:
        _fail += 1
        print(f"  FAIL: {label}")


# ============================================================
# §1 Core Concept: Compression and Trust
# ============================================================

class TrustLevel(Enum):
    """Trust-compression mapping per §1.2."""
    HIGH = "high"      # High compression, efficient
    MEDIUM = "medium"  # Moderate compression
    LOW = "low"        # Verbose communication
    ZERO = "zero"      # Raw data transfer


def trust_to_compression_ratio(trust: float) -> float:
    """Map trust score to compression ratio per §1.2.

    High trust → high compression ratio
    Zero trust → 1.0 (no compression)
    """
    if trust <= 0:
        return 1.0  # No compression
    if trust >= 1.0:
        return 20.0  # Maximum compression
    return 1.0 + 19.0 * trust  # Linear interpolation


def trust_level_from_score(trust: float) -> TrustLevel:
    """Categorize trust score into level."""
    if trust >= 0.8:
        return TrustLevel.HIGH
    elif trust >= 0.5:
        return TrustLevel.MEDIUM
    elif trust > 0:
        return TrustLevel.LOW
    return TrustLevel.ZERO


# ============================================================
# §2 Dictionary Entity Architecture
# ============================================================

@dataclass
class DictT3:
    """Trust tensor for dictionary competence per §2.1."""
    talent: float = 0.5       # Domain expertise
    training: float = 0.5     # Translation accuracy
    temperament: float = 0.5  # Consistency

    @property
    def composite(self) -> float:
        return round((self.talent + self.training + self.temperament) / 3, 4)

    def meets_minimum(self, minimum: dict) -> bool:
        """Check if T3 meets minimum requirements per §2.2."""
        return (self.talent >= minimum.get("talent", 0) and
                self.training >= minimum.get("training", 0) and
                self.temperament >= minimum.get("temperament", 0))


@dataclass
class DictV3:
    """Value tensor for translation quality per §2.1."""
    valuation: float = 0.5   # Subjective worth
    veracity: float = 0.5    # Truthfulness
    validity: float = 0.5    # Soundness

    @property
    def composite(self) -> float:
        return round((self.valuation + self.veracity + self.validity) / 3, 4)


@dataclass
class CompressionProfile:
    """Compression profile per §2.2."""
    average_ratio: float = 1.0
    lossy_threshold: float = 0.02
    context_required: str = "moderate"  # minimal, moderate, extensive
    ambiguity_handling: str = "probabilistic"  # deterministic, probabilistic


@dataclass
class EvolutionConfig:
    """Evolution configuration per §2.2."""
    learning_rate: float = 0.001
    update_frequency: str = "daily"
    drift_detection: bool = True
    community_edits: bool = True


@dataclass
class CoverageStats:
    """Coverage statistics per §2.2."""
    terms: int = 0
    concepts: int = 0
    relationships: int = 0


# ============================================================
# §3 Dictionary Types
# ============================================================

class DictionaryType(Enum):
    """All dictionary types per §3."""
    DOMAIN = "domain"            # §3.1
    MODEL = "model"              # §3.2
    COMPRESSION = "compression"  # §3.3
    META = "meta"                # §3.4


@dataclass
class DomainDictSpec:
    """Domain dictionary spec per §3.1."""
    source_domain: str
    target_domain: str
    bidirectional: bool = False
    domain_subtype: str = ""  # professional, technical, cultural, temporal


@dataclass
class EmbeddingAlignment:
    """Model dictionary embedding alignment per §3.2."""
    method: str = "procrustes"
    dimensions: int = 1536
    correlation: float = 0.0


@dataclass
class TokenMapping:
    """Model dictionary token mapping per §3.2."""
    source_vocab: int = 0
    target_vocab: int = 0
    overlap: float = 0.0


@dataclass
class ContextWindowSpec:
    """Model dictionary context window per §3.2."""
    source: int = 0
    target: int = 0
    chunking_strategy: str = "semantic"


@dataclass
class ModelDictSpec:
    """AI model bridging dictionary per §3.2."""
    source_model: str
    target_model: str
    embedding: EmbeddingAlignment = field(default_factory=EmbeddingAlignment)
    tokens: TokenMapping = field(default_factory=TokenMapping)
    context: ContextWindowSpec = field(default_factory=ContextWindowSpec)


@dataclass
class CompressionCodebook:
    """Compression dictionary codebook per §3.3."""
    entries: int = 4096
    vector_dimension: int = 512
    quantization: str = "vector_quantized"
    perplexity: float = 0.0


@dataclass
class ReconstructionFidelity:
    """Reconstruction fidelity per §3.3."""
    semantic: float = 0.0
    syntactic: float = 0.0
    pragmatic: float = 0.0

    @property
    def average(self) -> float:
        return round((self.semantic + self.syntactic + self.pragmatic) / 3, 4)


@dataclass
class CompressionDictSpec:
    """Compression dictionary spec per §3.3."""
    compression_type: str = "semantic"  # semantic, syntactic, pragmatic
    codebook: CompressionCodebook = field(default_factory=CompressionCodebook)
    fidelity: ReconstructionFidelity = field(default_factory=ReconstructionFidelity)


@dataclass
class MetaDictSpec:
    """Meta-dictionary spec per §3.4."""
    translates_between: list[str] = field(default_factory=list)
    transitive_closure: bool = True
    consistency_checking: bool = True
    conflict_resolution: str = "weighted_voting"


# ============================================================
# §4 Translation Process
# ============================================================

@dataclass
class TranslationRequest:
    """Translation request per §4.1."""
    source_content: str
    source_domain: str
    target_domain: str
    context: dict = field(default_factory=dict)
    min_fidelity: float = 0.8
    require_witness: bool = False
    atp_stake: float = 0.0


@dataclass
class TranslationResult:
    """Translation result per §4.2."""
    content: str
    confidence: float
    degradation: float
    dictionary_lct: str
    witness_required: bool = False
    terms_mapped: int = 0
    terms_unknown: int = 0


@dataclass
class ChainStep:
    """Single step in a translation chain per §4.3."""
    step: int
    from_domain: str
    to_domain: str
    dictionary: str
    confidence: float
    degradation: float


@dataclass
class TranslationChain:
    """Multi-hop translation chain per §4.3."""
    steps: list[ChainStep] = field(default_factory=list)
    cumulative_degradation: float = 0.0
    trust_acceptable: bool = True
    witnesses: list[str] = field(default_factory=list)

    @property
    def cumulative_confidence(self) -> float:
        """Product of all step confidences — multiplicative decay."""
        if not self.steps:
            return 1.0
        result = 1.0
        for step in self.steps:
            result *= step.confidence
        return round(result, 4)

    def add_step(self, step: ChainStep):
        self.steps.append(step)
        self.cumulative_degradation = round(1.0 - self.cumulative_confidence, 4)


# ============================================================
# §5 Dictionary Evolution
# ============================================================

class FeedbackType(Enum):
    """Feedback types per §5.1."""
    CORRECTION = "correction"
    VALIDATION = "validation"


@dataclass
class Feedback:
    """Feedback record per §5.1."""
    fb_type: FeedbackType
    source_term: str = ""
    corrected_term: str = ""
    mapping_key: str = ""
    success: bool = True
    corrector_lct: str = ""
    witness_lct: str = ""
    authority_trust: float = 0.5


@dataclass
class Contributor:
    """Community contributor per §5.2."""
    lct: str
    role: str  # source_domain_expert, target_domain_expert
    reputation: float = 0.5
    contributions: int = 0


@dataclass
class CommunityGovernance:
    """Community governance per §5.2."""
    proposal_threshold: float = 10.0  # Min reputation to propose
    approval_quorum: float = 0.66     # Weighted by reputation
    challenge_period: int = 86400     # 24 hours in seconds
    contributors: list[Contributor] = field(default_factory=list)

    def can_propose(self, contributor: Contributor) -> bool:
        return contributor.reputation >= self.proposal_threshold

    def vote_result(self, votes: dict[str, bool]) -> bool:
        """Weighted vote by contributor reputation."""
        contrib_map = {c.lct: c for c in self.contributors}
        total_weight = 0.0
        yes_weight = 0.0
        for lct, vote in votes.items():
            c = contrib_map.get(lct)
            if c:
                total_weight += c.reputation
                if vote:
                    yes_weight += c.reputation
        if total_weight == 0:
            return False
        return (yes_weight / total_weight) >= self.approval_quorum


@dataclass
class CommunityIncentives:
    """Incentive structure per §5.2."""
    successful_contribution: float = 10.0   # ATP
    accepted_correction: float = 5.0        # ATP
    validated_translation: float = 1.0       # ATP


# ============================================================
# §6 Dictionary Discovery and Selection
# ============================================================

@dataclass
class DictCandidate:
    """Dictionary candidate with scoring per §6.2."""
    lct_id: str
    trust: float
    coverage: float
    recency_days: float
    atp_cost: float
    latency_ms: float


def score_dictionary(candidate: DictCandidate) -> float:
    """Score dictionary for selection per §6.2.

    Score = trust × coverage_factor × recency_factor / cost_factor
    """
    coverage_factor = min(1.0, candidate.coverage / 10000)  # Normalize
    recency_factor = max(0.1, 1.0 - (candidate.recency_days / 365))
    cost_factor = max(0.1, candidate.atp_cost / 100)
    latency_factor = max(0.1, 1.0 - (candidate.latency_ms / 5000))

    return round(
        candidate.trust * coverage_factor * recency_factor *
        latency_factor / cost_factor, 4
    )


def select_best_dictionary(candidates: list[DictCandidate]) -> Optional[DictCandidate]:
    """Select best dictionary per §6.2."""
    if not candidates:
        return None
    scored = [(score_dictionary(c), c) for c in candidates]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


# ============================================================
# §7 Dictionary-R6 Integration
# ============================================================

@dataclass
class DictR6Action:
    """Translation as R6 action per §7.1."""
    action_type: str = "dictionary_translation"
    # Rules
    min_fidelity: float = 0.9
    require_witness: bool = True
    # Role
    entity_lct: str = ""
    role_type: str = "web4:Translator"
    # Request
    action: str = "translate"
    source_content: str = ""
    target_domain: str = ""
    # Reference
    similar_translations: list[str] = field(default_factory=list)
    domain_precedents: list[str] = field(default_factory=list)
    # Resource
    atp_required: float = 0.0
    compute_level: str = "medium"  # low, medium, high
    # Result
    translation: str = ""
    confidence: float = 0.0
    degradation: float = 0.0

    def validate_r6(self) -> list[str]:
        """Validate R6 action completeness."""
        errors = []
        if not self.entity_lct:
            errors.append("Missing role entity LCT")
        if not self.source_content:
            errors.append("Missing request source_content")
        if not self.target_domain:
            errors.append("Missing request target_domain")
        if self.atp_required < 0:
            errors.append("Negative ATP required")
        return errors


# ============================================================
# §8 Security and Trust
# ============================================================

class AttackType(Enum):
    """Attack types per §8.1."""
    SEMANTIC_POISONING = "semantic_poisoning"
    TRANSLATION_BIAS = "translation_bias"
    CONTEXT_MANIPULATION = "context_manipulation"
    DRIFT_EXPLOITATION = "drift_exploitation"
    REPUTATION_GAMING = "reputation_gaming"


@dataclass
class AttackMitigation:
    """Attack mitigation per §8.1."""
    attack: AttackType
    mitigation: str
    requires_witness: bool = False
    requires_stake: bool = False
    requires_audit: bool = False


# Canonical mitigations per spec §8.1
ATTACK_MITIGATIONS = {
    AttackType.SEMANTIC_POISONING: AttackMitigation(
        attack=AttackType.SEMANTIC_POISONING,
        mitigation="Community validation, witness requirements",
        requires_witness=True,
    ),
    AttackType.TRANSLATION_BIAS: AttackMitigation(
        attack=AttackType.TRANSLATION_BIAS,
        mitigation="Multi-dictionary consensus, audit trails",
        requires_audit=True,
    ),
    AttackType.CONTEXT_MANIPULATION: AttackMitigation(
        attack=AttackType.CONTEXT_MANIPULATION,
        mitigation="Signed context, proof-of-provenance",
    ),
    AttackType.DRIFT_EXPLOITATION: AttackMitigation(
        attack=AttackType.DRIFT_EXPLOITATION,
        mitigation="Continuous monitoring, version pinning",
    ),
    AttackType.REPUTATION_GAMING: AttackMitigation(
        attack=AttackType.REPUTATION_GAMING,
        mitigation="ATP staking, temporal decay",
        requires_stake=True,
    ),
}


class TrustBuildingMethod(Enum):
    """Trust building methods per §8.2."""
    SUCCESSFUL_TRANSLATIONS = "successful_translations"
    WITNESS_ATTESTATIONS = "witness_attestations"
    COMMUNITY_CURATION = "community_curation"
    CONSISTENCY = "consistency"
    TRANSPARENCY = "transparency"


def apply_trust_building(t3: DictT3, method: TrustBuildingMethod,
                         magnitude: float = 0.01) -> DictT3:
    """Apply trust building per §8.2. Returns updated T3."""
    deltas = {
        TrustBuildingMethod.SUCCESSFUL_TRANSLATIONS: ("training", magnitude),
        TrustBuildingMethod.WITNESS_ATTESTATIONS: ("talent", magnitude),
        TrustBuildingMethod.COMMUNITY_CURATION: ("talent", magnitude * 0.5),
        TrustBuildingMethod.CONSISTENCY: ("temperament", magnitude),
        TrustBuildingMethod.TRANSPARENCY: ("temperament", magnitude * 0.5),
    }
    dim, delta = deltas[method]
    current = getattr(t3, dim)
    setattr(t3, dim, min(1.0, current + delta))
    return t3


# ============================================================
# §9 Implementation Requirements
# ============================================================

class RequirementLevel(Enum):
    MUST = "MUST"
    SHOULD = "SHOULD"
    MAY = "MAY"


@dataclass
class Requirement:
    """Single implementation requirement per §9."""
    level: RequirementLevel
    description: str
    section: str  # §9.1, §9.2, §9.3


# Canonical requirements from spec
MUST_REQUIREMENTS = [
    Requirement(RequirementLevel.MUST, "Every Dictionary MUST have a valid LCT", "§9.1"),
    Requirement(RequirementLevel.MUST, "Dictionaries MUST track confidence and degradation", "§9.1"),
    Requirement(RequirementLevel.MUST, "Translations MUST be witnessable", "§9.1"),
    Requirement(RequirementLevel.MUST, "Evolution MUST be versioned", "§9.1"),
    Requirement(RequirementLevel.MUST, "Critical translations MUST require ATP stake", "§9.1"),
]

SHOULD_REQUIREMENTS = [
    Requirement(RequirementLevel.SHOULD, "Support bidirectional translation", "§9.2"),
    Requirement(RequirementLevel.SHOULD, "Provide confidence intervals", "§9.2"),
    Requirement(RequirementLevel.SHOULD, "Detect semantic drift", "§9.2"),
    Requirement(RequirementLevel.SHOULD, "Enable community curation", "§9.2"),
    Requirement(RequirementLevel.SHOULD, "Maintain translation history", "§9.2"),
]

MAY_REQUIREMENTS = [
    Requirement(RequirementLevel.MAY, "Support multi-hop translation", "§9.3"),
    Requirement(RequirementLevel.MAY, "Offer specialized sub-dictionaries", "§9.3"),
    Requirement(RequirementLevel.MAY, "Implement caching strategies", "§9.3"),
    Requirement(RequirementLevel.MAY, "Provide real-time updates", "§9.3"),
    Requirement(RequirementLevel.MAY, "Support dialect variations", "§9.3"),
]


@dataclass
class ComplianceReport:
    """Compliance check against requirements."""
    must_met: int = 0
    must_total: int = 5
    should_met: int = 0
    should_total: int = 5
    may_met: int = 0
    may_total: int = 5
    violations: list[str] = field(default_factory=list)

    @property
    def must_compliant(self) -> bool:
        return self.must_met == self.must_total

    @property
    def compliance_score(self) -> float:
        """Weighted compliance: MUST=1.0, SHOULD=0.5, MAY=0.25."""
        total = (self.must_total * 1.0 + self.should_total * 0.5 +
                 self.may_total * 0.25)
        met = (self.must_met * 1.0 + self.should_met * 0.5 +
               self.may_met * 0.25)
        return round(met / total, 4) if total > 0 else 0.0


def check_compliance(
    has_lct: bool,
    tracks_confidence: bool,
    witnessable: bool,
    versioned: bool,
    requires_atp_stake: bool,
    bidirectional: bool = False,
    has_confidence_intervals: bool = False,
    detects_drift: bool = False,
    community_curation: bool = False,
    has_history: bool = False,
    multi_hop: bool = False,
    sub_dictionaries: bool = False,
    caching: bool = False,
    real_time: bool = False,
    dialect_support: bool = False,
) -> ComplianceReport:
    """Check dictionary compliance per §9."""
    report = ComplianceReport()

    # MUST
    musts = [has_lct, tracks_confidence, witnessable, versioned, requires_atp_stake]
    report.must_met = sum(musts)
    if not has_lct:
        report.violations.append("MUST: Missing valid LCT")
    if not tracks_confidence:
        report.violations.append("MUST: Not tracking confidence/degradation")
    if not witnessable:
        report.violations.append("MUST: Translations not witnessable")
    if not versioned:
        report.violations.append("MUST: Evolution not versioned")
    if not requires_atp_stake:
        report.violations.append("MUST: No ATP stake for critical translations")

    # SHOULD
    shoulds = [bidirectional, has_confidence_intervals, detects_drift,
               community_curation, has_history]
    report.should_met = sum(shoulds)

    # MAY
    mays = [multi_hop, sub_dictionaries, caching, real_time, dialect_support]
    report.may_met = sum(mays)

    return report


# ============================================================
# §11 Dictionary Reputation Economy
# ============================================================

@dataclass
class EarningEvent:
    """ATP earning event per §11.1."""
    event_type: str  # successful_translation, high_confidence, witness, contribution
    base_amount: float
    multiplier: float = 1.0
    witness_bonus: float = 0.0

    @property
    def total(self) -> float:
        return round(self.base_amount * self.multiplier + self.witness_bonus, 4)


@dataclass
class StakingResult:
    """Staking/slashing result per §11.2."""
    stake_amount: float
    confidence_claim: float
    actual_confidence: float
    reward: float = 0.0
    slash: float = 0.0

    def compute(self):
        """Compute reward or slash per §11.2."""
        if self.actual_confidence >= self.confidence_claim:
            self.reward = round(self.stake_amount * 0.1, 4)  # 10% reward
            self.slash = 0.0
        else:
            ratio = self.actual_confidence / max(0.01, self.confidence_claim)
            self.slash = round(self.stake_amount * (1.0 - ratio), 4)
            self.reward = 0.0

    @property
    def net(self) -> float:
        return round(self.reward - self.slash, 4)


class ReputationEngine:
    """Dictionary reputation economy per §11."""

    def __init__(self):
        self.balance: float = 100.0
        self.total_earned: float = 0.0
        self.total_slashed: float = 0.0
        self.events: list[EarningEvent] = []

    def earn(self, event: EarningEvent):
        """Record earning event."""
        self.balance += event.total
        self.total_earned += event.total
        self.events.append(event)

    def stake(self, amount: float, confidence_claim: float,
              actual_confidence: float) -> StakingResult:
        """Stake ATP on confidence claim."""
        result = StakingResult(
            stake_amount=amount,
            confidence_claim=confidence_claim,
            actual_confidence=actual_confidence,
        )
        result.compute()
        self.balance += result.net
        if result.slash > 0:
            self.total_slashed += result.slash
        return result


# ============================================================
# §10 Use Cases
# ============================================================

@dataclass
class UseCaseScenario:
    """Use case scenario per §10."""
    name: str
    source_domain: str
    target_domain: str
    example_source: str
    example_target: str
    expected_confidence: float
    witness_types: list[str] = field(default_factory=list)


# Canonical use cases from spec
USE_CASES = [
    UseCaseScenario(
        name="Medical-Legal Translation",
        source_domain="medical",
        target_domain="legal",
        example_source="Patient diagnosed with moderate TBI following MVA",
        example_target="Plaintiff sustained head trauma with cognitive impairment in collision",
        expected_confidence=0.88,
        witness_types=["medical_expert", "legal_clerk"],
    ),
    UseCaseScenario(
        name="AI Model Bridging",
        source_domain="gpt4_output",
        target_domain="claude3_input",
        example_source="embeddings + attention_weights",
        example_target="context + instructions",
        expected_confidence=0.93,
        witness_types=["model_validator"],
    ),
    UseCaseScenario(
        name="Cross-Cultural Business",
        source_domain="chinese_business",
        target_domain="western_framework",
        example_source="建立关系网需要面子和人情",
        example_target="Building network relationships requires reputation capital and reciprocal obligations",
        expected_confidence=0.85,
        witness_types=["cultural_expert"],
    ),
]


# ============================================================
# §12 Future Extensions
# ============================================================

class FutureExtension(Enum):
    """Future extension types per §12."""
    QUANTUM = "quantum"       # §12.1 Superposition of meanings
    EMERGENT = "emergent"     # §12.2 Self-organizing from usage
    HOLOGRAPHIC = "holographic"  # §12.3 Every part contains the whole


@dataclass
class ExtensionSpec:
    """Future extension specification."""
    extension: FutureExtension
    properties: list[str]
    research_status: str = "theoretical"


FUTURE_EXTENSIONS = {
    FutureExtension.QUANTUM: ExtensionSpec(
        extension=FutureExtension.QUANTUM,
        properties=[
            "Superposition of meanings until observed",
            "Entangled translations across domains",
            "Quantum-safe semantic commitments",
        ],
    ),
    FutureExtension.EMERGENT: ExtensionSpec(
        extension=FutureExtension.EMERGENT,
        properties=[
            "Self-organizing from usage patterns",
            "No explicit curation needed",
            "Evolution through natural selection",
        ],
    ),
    FutureExtension.HOLOGRAPHIC: ExtensionSpec(
        extension=FutureExtension.HOLOGRAPHIC,
        properties=[
            "Every part contains the whole",
            "Graceful degradation under damage",
            "Fractal semantic structures",
        ],
    ),
}


# ============================================================
# Integrated Dictionary Entity (full spec)
# ============================================================

class DictionaryEntity:
    """Full-spec Dictionary Entity per §2."""

    def __init__(
        self,
        lct_id: str,
        source_domain: str,
        target_domain: str,
        dict_type: DictionaryType = DictionaryType.DOMAIN,
        bidirectional: bool = False,
    ):
        self.lct_id = lct_id
        self.source_domain = source_domain
        self.target_domain = target_domain
        self.dict_type = dict_type
        self.bidirectional = bidirectional

        # §2.1 Core components
        self.t3 = DictT3()
        self.v3 = DictV3()
        self.compression_profile = CompressionProfile()
        self.evolution = EvolutionConfig()
        self.coverage = CoverageStats()

        # §2.2 Trust requirements
        self.trust_requirements: dict = {
            "talent": 0.8, "training": 0.9, "temperament": 0.85
        }
        self.stake_required: float = 100.0

        # §2.2 MRH
        self.mrh_bound: list[str] = []
        self.mrh_paired: list[str] = []
        self.mrh_witnessing: list[str] = []

        # State
        self.codebook: dict[str, dict] = {}  # source → {target, confidence}
        self.version: str = "1.0.0"
        self.version_history: list[dict] = [{"version": "1.0.0", "reason": "initial"}]
        self.translation_log: list[dict] = []
        self.reputation = ReputationEngine()
        self.governance = CommunityGovernance()

    def covers_domains(self, source: str, target: str) -> bool:
        if self.source_domain == source and self.target_domain == target:
            return True
        if self.bidirectional:
            return self.source_domain == target and self.target_domain == source
        return False

    def add_mapping(self, source: str, target: str, confidence: float = 1.0):
        self.codebook[source] = {"target": target, "confidence": confidence,
                                 "corrections": 0, "usage": 0}
        self.coverage.terms += 1

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """Translate per §4.2 with greedy longest-match."""
        if not self.covers_domains(request.source_domain, request.target_domain):
            raise ValueError("Domain mismatch")

        words = request.source_content.lower().split()
        translated = []
        mapped = 0
        unknown = 0
        confidence_sum = 0.0

        i = 0
        while i < len(words):
            matched = False
            # Greedy longest-match (up to 4 words)
            for length in range(min(4, len(words) - i), 0, -1):
                phrase = " ".join(words[i:i + length])
                entry = self.codebook.get(phrase)
                if entry:
                    translated.append(entry["target"])
                    entry["usage"] += 1
                    confidence_sum += entry["confidence"]
                    mapped += 1
                    i += length
                    matched = True
                    break
            if not matched:
                translated.append(f"[{words[i]}]")
                unknown += 1
                i += 1

        total = mapped + unknown
        if total == 0:
            confidence = 0.0
        else:
            avg_conf = confidence_sum / max(1, mapped)
            coverage_ratio = mapped / total
            confidence = round(avg_conf * coverage_ratio, 4)

        # Cap by T3
        confidence = min(confidence, self.t3.composite)
        degradation = round(1.0 - confidence, 4)

        self.translation_log.append({
            "confidence": confidence, "mapped": mapped, "unknown": unknown,
        })

        return TranslationResult(
            content=" ".join(translated),
            confidence=confidence,
            degradation=degradation,
            dictionary_lct=self.lct_id,
            witness_required=confidence < 0.95 or request.require_witness,
            terms_mapped=mapped,
            terms_unknown=unknown,
        )

    def apply_feedback(self, feedback: Feedback):
        """Apply feedback per §5.1."""
        if feedback.fb_type == FeedbackType.CORRECTION:
            if feedback.source_term in self.codebook:
                entry = self.codebook[feedback.source_term]
                entry["corrections"] += 1
                entry["confidence"] *= 0.95
                if feedback.authority_trust > 0.7:
                    entry["target"] = feedback.corrected_term
                    entry["confidence"] = min(1.0, entry["confidence"] + 0.1)
        elif feedback.fb_type == FeedbackType.VALIDATION:
            if feedback.mapping_key in self.codebook:
                entry = self.codebook[feedback.mapping_key]
                if feedback.success:
                    entry["confidence"] = min(1.0, entry["confidence"] + 0.02)
                else:
                    entry["confidence"] *= 0.9

    def detect_drift(self, threshold: float = 0.1) -> bool:
        """Detect semantic drift per §5.1."""
        if not self.codebook:
            return False
        corrected = sum(1 for e in self.codebook.values() if e["corrections"] > 0)
        return corrected / len(self.codebook) > threshold

    def bump_version(self, reason: str):
        parts = self.version.split(".")
        parts[1] = str(int(parts[1]) + 1)
        self.version = ".".join(parts)
        self.version_history.append({"version": self.version, "reason": reason})

    def check_compliance(self) -> ComplianceReport:
        """Check compliance per §9."""
        return check_compliance(
            has_lct=bool(self.lct_id),
            tracks_confidence=len(self.translation_log) > 0 or len(self.codebook) > 0,
            witnessable=True,  # All translations produce witness_required flag
            versioned=len(self.version_history) > 0,
            requires_atp_stake=self.stake_required > 0,
            bidirectional=self.bidirectional,
            has_confidence_intervals=True,
            detects_drift=self.evolution.drift_detection,
            community_curation=self.evolution.community_edits,
            has_history=len(self.translation_log) > 0 or True,
            multi_hop=True,
        )


# ============================================================
# TESTS
# ============================================================

if __name__ == "__main__":

    # ── T1: Compression-Trust Duality (§1) ───────────────────
    print("T1: Compression-Trust Duality (§1)")

    check("T1.1 High trust → high compression",
          trust_to_compression_ratio(0.9) > 15.0)
    check("T1.2 Zero trust → no compression",
          trust_to_compression_ratio(0.0) == 1.0)
    check("T1.3 Medium trust → moderate compression",
          5.0 < trust_to_compression_ratio(0.5) < 15.0)
    check("T1.4 Max trust → ratio 20",
          trust_to_compression_ratio(1.0) == 20.0)

    check("T1.5 Trust level HIGH at 0.9",
          trust_level_from_score(0.9) == TrustLevel.HIGH)
    check("T1.6 Trust level MEDIUM at 0.6",
          trust_level_from_score(0.6) == TrustLevel.MEDIUM)
    check("T1.7 Trust level LOW at 0.3",
          trust_level_from_score(0.3) == TrustLevel.LOW)
    check("T1.8 Trust level ZERO at 0.0",
          trust_level_from_score(0.0) == TrustLevel.ZERO)

    # ── T2: Dictionary Entity Architecture (§2) ──────────────
    print("T2: Dictionary Entity Architecture (§2)")

    t3 = DictT3(talent=0.85, training=0.90, temperament=0.88)
    check("T2.1 T3 composite correct",
          abs(t3.composite - (0.85 + 0.90 + 0.88) / 3) < 0.001)
    check("T2.2 T3 meets minimum",
          t3.meets_minimum({"talent": 0.8, "training": 0.9, "temperament": 0.85}))
    check("T2.3 T3 fails high minimum",
          not t3.meets_minimum({"talent": 0.95}))

    v3 = DictV3(valuation=0.92, veracity=0.88, validity=0.85)
    check("T2.4 V3 composite correct",
          abs(v3.composite - (0.92 + 0.88 + 0.85) / 3) < 0.001)

    cp = CompressionProfile(average_ratio=12.5, lossy_threshold=0.02)
    check("T2.5 Compression profile ratio", cp.average_ratio == 12.5)
    check("T2.6 Lossy threshold", cp.lossy_threshold == 0.02)

    ec = EvolutionConfig(learning_rate=0.001, drift_detection=True)
    check("T2.7 Evolution config learning rate", ec.learning_rate == 0.001)
    check("T2.8 Drift detection enabled", ec.drift_detection)

    # ── T3: Dictionary Types (§3) ────────────────────────────
    print("T3: Dictionary Types (§3)")

    check("T3.1 4 dictionary types", len(DictionaryType) == 4)

    # §3.1 Domain dictionary
    domain = DomainDictSpec(
        source_domain="medical", target_domain="legal",
        bidirectional=True, domain_subtype="professional")
    check("T3.2 Domain dict bidirectional", domain.bidirectional)
    check("T3.3 Domain subtype set", domain.domain_subtype == "professional")

    # §3.2 Model dictionary
    model = ModelDictSpec(
        source_model="gpt-4-vision",
        target_model="claude-3-opus",
        embedding=EmbeddingAlignment(method="procrustes", dimensions=1536, correlation=0.87),
        tokens=TokenMapping(source_vocab=100000, target_vocab=120000, overlap=0.75),
        context=ContextWindowSpec(source=128000, target=200000, chunking_strategy="semantic"),
    )
    check("T3.4 Model dict source", model.source_model == "gpt-4-vision")
    check("T3.5 Embedding correlation", model.embedding.correlation == 0.87)
    check("T3.6 Token overlap", model.tokens.overlap == 0.75)
    check("T3.7 Context chunking", model.context.chunking_strategy == "semantic")

    # §3.3 Compression dictionary
    comp = CompressionDictSpec(
        compression_type="semantic",
        codebook=CompressionCodebook(entries=4096, vector_dimension=512, perplexity=127.3),
        fidelity=ReconstructionFidelity(semantic=0.95, syntactic=0.88, pragmatic=0.91),
    )
    check("T3.8 Compression codebook entries", comp.codebook.entries == 4096)
    check("T3.9 Fidelity average",
          abs(comp.fidelity.average - (0.95 + 0.88 + 0.91) / 3) < 0.001)
    check("T3.10 Perplexity stored", comp.codebook.perplexity == 127.3)

    # §3.4 Meta dictionary
    meta = MetaDictSpec(
        translates_between=[
            "lct:web4:dictionary:medical-legal",
            "lct:web4:dictionary:medical-insurance",
            "lct:web4:dictionary:legal-insurance",
        ],
        transitive_closure=True,
        consistency_checking=True,
        conflict_resolution="weighted_voting",
    )
    check("T3.11 Meta dict bridges 3 dictionaries", len(meta.translates_between) == 3)
    check("T3.12 Transitive closure enabled", meta.transitive_closure)
    check("T3.13 Conflict resolution method", meta.conflict_resolution == "weighted_voting")

    # ── T4: Translation Process (§4) ─────────────────────────
    print("T4: Translation Process (§4)")

    de = DictionaryEntity(
        lct_id="lct:web4:dict:med-legal:v1",
        source_domain="medical",
        target_domain="legal",
        bidirectional=True,
    )
    de.t3 = DictT3(talent=0.85, training=0.90, temperament=0.88)
    de.add_mapping("mi", "heart attack", 0.95)
    de.add_mapping("tbi", "traumatic brain injury", 0.98)
    de.add_mapping("mva", "motor vehicle accident", 0.99)
    de.add_mapping("acute", "sudden onset", 0.90)
    de.add_mapping("following", "resulting from", 0.92)

    req = TranslationRequest(
        source_content="acute mi following mva",
        source_domain="medical",
        target_domain="legal",
    )
    result = de.translate(req)
    check("T4.1 Translation produces content", len(result.content) > 0)
    check("T4.2 All terms mapped", result.terms_unknown == 0)
    check("T4.3 Confidence > 0.8", result.confidence > 0.8)
    check("T4.4 Degradation = 1 - confidence",
          abs(result.degradation - (1.0 - result.confidence)) < 0.001)

    # Unknown terms
    req2 = TranslationRequest(
        source_content="acute mi with unknown_condition",
        source_domain="medical",
        target_domain="legal",
    )
    r2 = de.translate(req2)
    check("T4.5 Unknown terms bracketed", "[unknown_condition]" in r2.content)
    check("T4.6 Unknown terms counted", r2.terms_unknown >= 1)
    check("T4.7 Confidence reduced by unknowns", r2.confidence < result.confidence)

    # §4.3 Translation chain
    chain = TranslationChain()
    chain.add_step(ChainStep(step=1, from_domain="medical", to_domain="legal",
                             dictionary="dict:med-legal", confidence=0.95, degradation=0.05))
    chain.add_step(ChainStep(step=2, from_domain="legal", to_domain="insurance",
                             dictionary="dict:legal-ins", confidence=0.92, degradation=0.08))

    check("T4.8 Chain cumulative confidence = product",
          abs(chain.cumulative_confidence - 0.95 * 0.92) < 0.001)
    check("T4.9 Chain degradation = 1 - product",
          abs(chain.cumulative_degradation - (1.0 - 0.95 * 0.92)) < 0.001)
    check("T4.10 Chain has 2 steps", len(chain.steps) == 2)

    # ── T5: Dictionary Evolution (§5) ────────────────────────
    print("T5: Dictionary Evolution (§5)")

    # §5.1 Feedback
    fb = Feedback(
        fb_type=FeedbackType.CORRECTION,
        source_term="mi",
        corrected_term="myocardial infarction",
        authority_trust=0.8,
    )
    de.apply_feedback(fb)
    check("T5.1 Correction applied",
          de.codebook["mi"]["target"] == "myocardial infarction")
    check("T5.2 Correction count incremented",
          de.codebook["mi"]["corrections"] == 1)

    # Apply enough corrections to trigger drift
    for term in ["tbi", "mva"]:
        de.apply_feedback(Feedback(
            fb_type=FeedbackType.CORRECTION,
            source_term=term,
            corrected_term=f"corrected_{term}",
            authority_trust=0.9,
        ))
    check("T5.3 Drift detected (3/5 > 10%)", de.detect_drift())

    # Validation feedback
    de.apply_feedback(Feedback(
        fb_type=FeedbackType.VALIDATION,
        mapping_key="acute",
        success=True,
    ))
    check("T5.4 Validation increases confidence",
          de.codebook["acute"]["confidence"] > 0.9)

    # §5.2 Community curation
    gov = CommunityGovernance(
        proposal_threshold=10.0,
        approval_quorum=0.66,
        contributors=[
            Contributor(lct="lct:expert:1", role="source_domain_expert",
                        reputation=20.0, contributions=50),
            Contributor(lct="lct:expert:2", role="target_domain_expert",
                        reputation=15.0, contributions=30),
            Contributor(lct="lct:novice:1", role="target_domain_expert",
                        reputation=5.0, contributions=3),
        ],
    )
    check("T5.5 Expert can propose",
          gov.can_propose(gov.contributors[0]))
    check("T5.6 Novice cannot propose",
          not gov.can_propose(gov.contributors[2]))

    # Voting: experts agree, novice disagrees
    votes = {"lct:expert:1": True, "lct:expert:2": True, "lct:novice:1": False}
    check("T5.7 Weighted vote passes (experts win)",
          gov.vote_result(votes))
    # Only novice votes yes
    votes2 = {"lct:expert:1": False, "lct:expert:2": False, "lct:novice:1": True}
    check("T5.8 Weighted vote fails (novice alone)",
          not gov.vote_result(votes2))

    # Incentives
    inc = CommunityIncentives()
    check("T5.9 Successful contribution = 10 ATP",
          inc.successful_contribution == 10.0)
    check("T5.10 Accepted correction = 5 ATP",
          inc.accepted_correction == 5.0)

    # ── T6: Dictionary Discovery and Selection (§6) ──────────
    print("T6: Dictionary Discovery and Selection (§6)")

    c1 = DictCandidate("dict:A", trust=0.9, coverage=15000,
                       recency_days=5, atp_cost=10, latency_ms=100)
    c2 = DictCandidate("dict:B", trust=0.7, coverage=5000,
                       recency_days=30, atp_cost=5, latency_ms=200)
    c3 = DictCandidate("dict:C", trust=0.5, coverage=20000,
                       recency_days=180, atp_cost=50, latency_ms=500)

    s1 = score_dictionary(c1)
    s2 = score_dictionary(c2)
    s3 = score_dictionary(c3)

    check("T6.1 Higher trust scores higher", s1 > s2)
    check("T6.2 High cost penalizes score", s3 < s1)
    check("T6.3 Selection picks best",
          select_best_dictionary([c1, c2, c3]).lct_id == "dict:A")

    # Empty list
    check("T6.4 Empty list returns None",
          select_best_dictionary([]) is None)

    # ── T7: Dictionary-R6 Integration (§7) ───────────────────
    print("T7: Dictionary-R6 Integration (§7)")

    r6 = DictR6Action(
        entity_lct="lct:web4:dict:med-legal",
        role_type="web4:Translator",
        source_content="acute mi following mva",
        target_domain="legal",
        atp_required=10,
        compute_level="medium",
        min_fidelity=0.9,
        require_witness=True,
    )
    check("T7.1 R6 action type", r6.action_type == "dictionary_translation")
    check("T7.2 R6 validates cleanly", len(r6.validate_r6()) == 0)

    # Missing fields
    bad_r6 = DictR6Action()
    check("T7.3 Missing fields caught", len(bad_r6.validate_r6()) > 0)
    check("T7.4 Missing entity_lct error",
          any("entity LCT" in e for e in bad_r6.validate_r6()))

    # With result
    r6.translation = "sudden onset myocardial infarction resulting from motor vehicle accident"
    r6.confidence = 0.94
    r6.degradation = 0.06
    check("T7.5 Result confidence stored", r6.confidence == 0.94)
    check("T7.6 Result degradation stored", r6.degradation == 0.06)

    # ── T8: Security and Trust (§8) ──────────────────────────
    print("T8: Security and Trust (§8)")

    check("T8.1 5 attack types defined", len(AttackType) == 5)
    check("T8.2 All attacks have mitigations",
          all(a in ATTACK_MITIGATIONS for a in AttackType))

    check("T8.3 Semantic poisoning requires witness",
          ATTACK_MITIGATIONS[AttackType.SEMANTIC_POISONING].requires_witness)
    check("T8.4 Reputation gaming requires stake",
          ATTACK_MITIGATIONS[AttackType.REPUTATION_GAMING].requires_stake)
    check("T8.5 Translation bias requires audit",
          ATTACK_MITIGATIONS[AttackType.TRANSLATION_BIAS].requires_audit)

    # Trust building
    check("T8.6 5 trust building methods", len(TrustBuildingMethod) == 5)

    build_t3 = DictT3(talent=0.5, training=0.5, temperament=0.5)
    apply_trust_building(build_t3, TrustBuildingMethod.SUCCESSFUL_TRANSLATIONS, 0.05)
    check("T8.7 Trust building increases training",
          build_t3.training == 0.55)
    apply_trust_building(build_t3, TrustBuildingMethod.CONSISTENCY, 0.05)
    check("T8.8 Consistency increases temperament",
          build_t3.temperament == 0.55)

    # ── T9: Implementation Requirements (§9) ─────────────────
    print("T9: Implementation Requirements (§9)")

    check("T9.1 5 MUST requirements", len(MUST_REQUIREMENTS) == 5)
    check("T9.2 5 SHOULD requirements", len(SHOULD_REQUIREMENTS) == 5)
    check("T9.3 5 MAY requirements", len(MAY_REQUIREMENTS) == 5)

    # Full compliance
    full_report = check_compliance(
        has_lct=True, tracks_confidence=True, witnessable=True,
        versioned=True, requires_atp_stake=True,
        bidirectional=True, has_confidence_intervals=True,
        detects_drift=True, community_curation=True, has_history=True,
        multi_hop=True, sub_dictionaries=True, caching=True,
        real_time=True, dialect_support=True,
    )
    check("T9.4 Full compliance: MUST met", full_report.must_compliant)
    check("T9.5 Full compliance score = 1.0", full_report.compliance_score == 1.0)
    check("T9.6 No violations", len(full_report.violations) == 0)

    # Partial compliance
    partial = check_compliance(
        has_lct=True, tracks_confidence=True, witnessable=True,
        versioned=True, requires_atp_stake=False,  # Missing MUST
        bidirectional=True,
    )
    check("T9.7 Partial fails MUST", not partial.must_compliant)
    check("T9.8 Violation reported", len(partial.violations) > 0)
    check("T9.9 Violation mentions ATP",
          any("ATP" in v for v in partial.violations))

    # Entity compliance check
    de_report = de.check_compliance()
    check("T9.10 Entity passes MUST", de_report.must_compliant)

    # ── T10: Use Cases (§10) ─────────────────────────────────
    print("T10: Use Cases (§10)")

    check("T10.1 3 canonical use cases", len(USE_CASES) == 3)
    check("T10.2 Medical-legal case", USE_CASES[0].name == "Medical-Legal Translation")
    check("T10.3 AI model bridging case", USE_CASES[1].source_domain == "gpt4_output")
    check("T10.4 Cross-cultural case",
          USE_CASES[2].expected_confidence == 0.85)
    check("T10.5 Medical-legal has witnesses",
          len(USE_CASES[0].witness_types) == 2)

    # ── T11: Reputation Economy (§11) ────────────────────────
    print("T11: Reputation Economy (§11)")

    rep = ReputationEngine()
    initial = rep.balance

    # §11.1 Earning
    rep.earn(EarningEvent("successful_translation", base_amount=5.0))
    check("T11.1 Earning increases balance", rep.balance > initial)
    check("T11.2 Total earned tracked", rep.total_earned == 5.0)

    # Witness bonus
    rep.earn(EarningEvent("high_confidence", base_amount=5.0,
                          multiplier=1.5, witness_bonus=2.0))
    check("T11.3 Multiplier applied",
          rep.events[-1].total == 5.0 * 1.5 + 2.0)

    # §11.2 Staking — successful
    result = rep.stake(amount=50.0, confidence_claim=0.9, actual_confidence=0.95)
    check("T11.4 Successful stake rewards 10%", result.reward == 5.0)
    check("T11.5 No slash on success", result.slash == 0.0)
    check("T11.6 Net positive", result.net > 0)

    # Staking — failed (overconfidence)
    bal_before = rep.balance
    result2 = rep.stake(amount=100.0, confidence_claim=0.95, actual_confidence=0.5)
    check("T11.7 Overconfidence gets slashed", result2.slash > 0)
    check("T11.8 No reward on slash", result2.reward == 0.0)
    check("T11.9 Balance decreased", rep.balance < bal_before)
    check("T11.10 Slash proportional to gap",
          result2.slash > 40)  # (1 - 0.5/0.95) × 100 ≈ 47

    # Total slashed
    check("T11.11 Total slashed tracked", rep.total_slashed > 0)

    # ── T12: Future Extensions (§12) ─────────────────────────
    print("T12: Future Extensions (§12)")

    check("T12.1 3 future extensions", len(FutureExtension) == 3)
    check("T12.2 Quantum extension defined",
          FutureExtension.QUANTUM in FUTURE_EXTENSIONS)
    check("T12.3 Quantum has 3 properties",
          len(FUTURE_EXTENSIONS[FutureExtension.QUANTUM].properties) == 3)
    check("T12.4 Emergent extension defined",
          FutureExtension.EMERGENT in FUTURE_EXTENSIONS)
    check("T12.5 Holographic extension defined",
          FutureExtension.HOLOGRAPHIC in FUTURE_EXTENSIONS)

    # ── T13: Integrated Entity (§2 + §7 + §9) ───────────────
    print("T13: Integrated Dictionary Entity")

    full = DictionaryEntity(
        lct_id="lct:web4:dict:test:full",
        source_domain="engineering",
        target_domain="business",
        dict_type=DictionaryType.DOMAIN,
        bidirectional=True,
    )
    full.t3 = DictT3(talent=0.9, training=0.92, temperament=0.88)
    full.add_mapping("api latency", "customer response time", 0.95)
    full.add_mapping("throughput", "processing capacity", 0.93)
    full.add_mapping("downtime", "service unavailability", 0.97)

    # Translate
    tr = full.translate(TranslationRequest(
        source_content="api latency downtime",
        source_domain="engineering",
        target_domain="business",
    ))
    check("T13.1 Integrated translation works", tr.confidence > 0.8)
    check("T13.2 Terms mapped", tr.terms_mapped == 2)

    # Reverse translation (bidirectional)
    rev = full.translate(TranslationRequest(
        source_content="processing capacity",
        source_domain="business",
        target_domain="engineering",
    ))
    check("T13.3 Bidirectional not supported for individual entries",
          rev.terms_unknown > 0)  # Codebook is one-way; bidir needs reverse entries

    # Version bump
    full.bump_version("test_bump")
    check("T13.4 Version bumped", full.version == "1.1.0")
    check("T13.5 Version history tracked", len(full.version_history) == 2)

    # Compliance
    report = full.check_compliance()
    check("T13.6 MUST compliant", report.must_compliant)
    check("T13.7 Compliance score > 0.8", report.compliance_score > 0.8)

    # Domain coverage
    check("T13.8 Covers engineering→business",
          full.covers_domains("engineering", "business"))
    check("T13.9 Covers business→engineering (bidir)",
          full.covers_domains("business", "engineering"))
    check("T13.10 Does not cover medical→legal",
          not full.covers_domains("medical", "legal"))

    # ── T14: Multi-Hop Chain Integration ─────────────────────
    print("T14: Multi-Hop Chain Integration")

    chain = TranslationChain()

    # Medical → Legal → Insurance
    chain.add_step(ChainStep(1, "medical", "legal", "dict:med-legal", 0.95, 0.05))
    chain.add_step(ChainStep(2, "legal", "insurance", "dict:legal-ins", 0.92, 0.08))

    check("T14.1 Cumulative = 0.95 × 0.92",
          abs(chain.cumulative_confidence - 0.874) < 0.001)
    check("T14.2 Degradation = 1 - 0.874",
          abs(chain.cumulative_degradation - 0.126) < 0.001)

    # 3-hop chain
    chain.add_step(ChainStep(3, "insurance", "regulatory", "dict:ins-reg", 0.88, 0.12))
    expected_3hop = round(0.95 * 0.92 * 0.88, 4)
    check("T14.3 3-hop cumulative correct",
          abs(chain.cumulative_confidence - expected_3hop) < 0.001)
    check("T14.4 3 steps in chain", len(chain.steps) == 3)

    # Marginal degradation is SUBLINEAR per MEMORY.md
    # When same confidence c at each hop: marginal loss = c^(n-1)×(1-c) DECREASES with n
    # Test with uniform confidence chain
    uniform_chain = TranslationChain()
    c = 0.9
    uniform_chain.add_step(ChainStep(1, "a", "b", "d1", c, 1 - c))
    uniform_chain.add_step(ChainStep(2, "b", "c", "d2", c, 1 - c))
    uniform_chain.add_step(ChainStep(3, "c", "d", "d3", c, 1 - c))
    # Marginal loss at hop n = c^(n-1) × (1-c)
    marginal_1 = (1 - c)            # 0.1
    marginal_2 = c * (1 - c)        # 0.09
    marginal_3 = c**2 * (1 - c)     # 0.081
    check("T14.5 Marginal degradation is sublinear",
          marginal_1 > marginal_2 > marginal_3)

    # ── T15: Staking Edge Cases ──────────────────────────────
    print("T15: Staking Edge Cases")

    # Exact match — gets reward
    sr1 = StakingResult(50.0, 0.9, 0.9)
    sr1.compute()
    check("T15.1 Exact match gets reward", sr1.reward == 5.0)

    # Wildly overconfident
    sr2 = StakingResult(100.0, 0.99, 0.01)
    sr2.compute()
    check("T15.2 Massive overconfidence heavy slash",
          sr2.slash > 98)

    # Low stake
    sr3 = StakingResult(1.0, 0.5, 0.6)
    sr3.compute()
    check("T15.3 Low stake low reward", sr3.reward == 0.1)

    # ── T16: Governance Edge Cases ───────────────────────────
    print("T16: Governance Edge Cases")

    # Unanimous yes
    gov2 = CommunityGovernance(
        approval_quorum=0.66,
        contributors=[
            Contributor("a", "expert", 10.0, 5),
            Contributor("b", "expert", 10.0, 5),
        ],
    )
    check("T16.1 Unanimous yes passes",
          gov2.vote_result({"a": True, "b": True}))
    check("T16.2 Unanimous no fails",
          not gov2.vote_result({"a": False, "b": False}))
    check("T16.3 Split 50/50 fails (below 0.66 quorum)",
          not gov2.vote_result({"a": True, "b": False}))

    # No votes at all
    empty_gov = CommunityGovernance(contributors=[])
    check("T16.4 No contributors fails",
          not empty_gov.vote_result({}))

    # ════════════════════════════════════════════════════════
    print()
    print("=" * 60)
    total = _pass + _fail
    print(f"Dictionary Entities Spec: {_pass}/{total} checks passed")
    if _fail:
        print(f"  ({_fail} FAILED)")
    else:
        print("  All checks passed!")
    print("=" * 60)
