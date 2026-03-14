"""
Web4 Dictionary Entities — Semantic Bridges with Trust

Canonical implementation per web4-standard/core-spec/dictionary-entities.md.

Dictionary Entities are first-class Web4 entities that mediate meaning across
domain boundaries. They are living semantic bridges: each has its own LCT,
T3/V3 tensors, and reputation built through successful translations.

Core principle: all meaningful communication is compression plus trust
across shared or sufficiently aligned latent fields.

Key spec requirements (§9.1 MUST):
1. Every Dictionary MUST have a valid LCT
2. Dictionaries MUST track confidence and degradation
3. Translations MUST be witnessable
4. Evolution MUST be versioned
5. Critical translations MUST require ATP stake

Validated against: web4-standard/test-vectors/dictionary/dictionary-operations.json
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from .lct import LCT, EntityType
from .trust import T3, V3, _clamp


# ── Dictionary Types ─────────────────────────────────────────────

class DictionaryType(str, Enum):
    """Dictionary type taxonomy (spec §3)."""
    DOMAIN = "domain"            # Professional/technical domain bridges
    MODEL = "model"              # AI model-to-model bridges
    COMPRESSION = "compression"  # Semantic codebook management
    META = "meta"                # Dictionary-to-dictionary translation


class AmbiguityHandling(str, Enum):
    """How the dictionary resolves ambiguous mappings."""
    DETERMINISTIC = "deterministic"
    PROBABILISTIC = "probabilistic"
    CONTEXT_AWARE = "context_aware"
    REJECT = "reject"


# ── Dictionary Specification ─────────────────────────────────────

@dataclass(frozen=True)
class DomainCoverage:
    """Coverage metrics for a dictionary's domain knowledge."""
    terms: int = 0
    concepts: int = 0
    relationships: int = 0


@dataclass(frozen=True)
class CompressionProfile:
    """
    How this dictionary compresses meaning (spec §2.2).

    High trust → high compression → efficient communication.
    Low trust → low compression → verbose communication.
    """
    average_ratio: float = 1.0
    lossy_threshold: float = 0.02
    context_required: str = "moderate"  # "none", "minimal", "moderate", "full"
    ambiguity_handling: AmbiguityHandling = AmbiguityHandling.PROBABILISTIC


@dataclass(frozen=True)
class DictionarySpec:
    """
    Specification defining a dictionary's scope and capabilities (spec §2.2).

    A DictionarySpec declares what domains the dictionary bridges, its version,
    and its coverage. This is the "identity card" of the dictionary's competence.
    """
    source_domain: str
    target_domain: str
    bidirectional: bool = True
    version: str = "1.0.0"
    coverage: DomainCoverage = field(default_factory=DomainCoverage)
    compression: CompressionProfile = field(default_factory=CompressionProfile)
    dictionary_type: DictionaryType = DictionaryType.DOMAIN

    def covers_domains(self, source: str, target: str) -> bool:
        """Check if this spec covers the requested domain pair."""
        forward = self.source_domain == source and self.target_domain == target
        reverse = self.bidirectional and self.source_domain == target and self.target_domain == source
        return forward or reverse


# ── Translation ──────────────────────────────────────────────────

@dataclass(frozen=True)
class TranslationRequest:
    """
    A request for dictionary translation (spec §4.1).

    The source_content is opaque — this module doesn't process content,
    only tracks trust, confidence, and degradation metadata.
    """
    source_content: str
    source_domain: str
    target_domain: str
    context: Dict = field(default_factory=dict)
    minimum_fidelity: float = 0.9
    require_witness: bool = False
    atp_stake: float = 0.0


@dataclass
class TranslationResult:
    """
    Result of a dictionary translation (spec §4.2).

    confidence: [0,1] — how confident the dictionary is in the translation.
    degradation: 1 - confidence — semantic loss in this step.
    witness_required: True if confidence < 0.95 or request requires it.
    """
    content: str
    confidence: float
    degradation: float
    dictionary_lct_id: str
    witness_required: bool = False
    witness_lct_ids: List[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        self.confidence = _clamp(self.confidence)
        self.degradation = _clamp(self.degradation)
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


# ── Translation Chain ────────────────────────────────────────────

@dataclass(frozen=True)
class ChainStep:
    """One step in a multi-hop translation chain (spec §4.3)."""
    step: int
    source_domain: str
    target_domain: str
    dictionary_lct_id: str
    confidence: float
    degradation: float


@dataclass
class TranslationChain:
    """
    Multi-hop translation with cumulative degradation tracking (spec §4.3).

    Trust degrades MULTIPLICATIVELY through chains:
      cumulative_confidence = product(step.confidence for each step)
      cumulative_degradation = 1 - cumulative_confidence

    Example: 0.95 × 0.92 = 0.874 → 12.6% cumulative degradation.
    """
    steps: List[ChainStep] = field(default_factory=list)
    witness_lct_ids: List[str] = field(default_factory=list)

    @property
    def cumulative_confidence(self) -> float:
        """Multiplicative product of all step confidences."""
        if not self.steps:
            return 1.0
        result = 1.0
        for step in self.steps:
            result *= step.confidence
        return result

    @property
    def cumulative_degradation(self) -> float:
        """Total semantic loss: 1 - cumulative_confidence."""
        return 1.0 - self.cumulative_confidence

    @property
    def length(self) -> int:
        return len(self.steps)

    def add_step(
        self,
        source_domain: str,
        target_domain: str,
        dictionary_lct_id: str,
        confidence: float,
    ) -> ChainStep:
        """Append a translation step to the chain."""
        step = ChainStep(
            step=len(self.steps) + 1,
            source_domain=source_domain,
            target_domain=target_domain,
            dictionary_lct_id=dictionary_lct_id,
            confidence=_clamp(confidence),
            degradation=_clamp(1.0 - confidence),
        )
        self.steps.append(step)
        return step

    def is_acceptable(self, minimum_confidence: float = 0.8) -> bool:
        """Check if cumulative confidence meets threshold."""
        return self.cumulative_confidence >= minimum_confidence


# ── Dictionary Evolution ─────────────────────────────────────────

@dataclass
class EvolutionConfig:
    """Configuration for dictionary evolution (spec §5)."""
    learning_rate: float = 0.001
    update_frequency: str = "daily"
    drift_detection: bool = True
    community_edits: bool = True


@dataclass
class DictionaryVersion:
    """A versioned snapshot of dictionary state."""
    version: str
    parent_version: Optional[str] = None
    timestamp: str = ""
    changelog: str = ""
    corrections_applied: int = 0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class FeedbackRecord:
    """Feedback on a translation — correction or validation (spec §5.1)."""
    feedback_type: str  # "correction" or "validation"
    mapping_id: str
    success: bool = True
    corrector_lct_id: str = ""
    original_content: str = ""
    corrected_content: str = ""
    context: Dict = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


# ── Dictionary Entity ────────────────────────────────────────────

@dataclass
class DictionaryEntity:
    """
    A living semantic bridge with its own LCT and trust profile (spec §2.1).

    Every Dictionary has: LCT, MRH, T3, V3, witness history, spec, evolution.
    Dictionaries build trust through successful translations and witness attestations.

    Usage:
        dict_entity = DictionaryEntity.create(
            source_domain="medical",
            target_domain="legal",
            public_key="mb64dictkey",
        )
        result = dict_entity.record_translation(request, "translated content", 0.95)
        dict_entity.apply_feedback(feedback)
    """

    lct: LCT
    spec: DictionarySpec
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    versions: List[DictionaryVersion] = field(default_factory=list)
    translation_count: int = 0
    successful_translations: int = 0
    feedback_history: List[FeedbackRecord] = field(default_factory=list)

    @staticmethod
    def create(
        source_domain: str,
        target_domain: str,
        public_key: str,
        bidirectional: bool = True,
        version: str = "1.0.0",
        coverage: Optional[DomainCoverage] = None,
        compression: Optional[CompressionProfile] = None,
        dictionary_type: DictionaryType = DictionaryType.DOMAIN,
        society: str = "lct:web4:society:genesis",
        witnesses: Optional[List[str]] = None,
        t3: Optional[T3] = None,
        v3: Optional[V3] = None,
        evolution: Optional[EvolutionConfig] = None,
    ) -> DictionaryEntity:
        """Create a new DictionaryEntity with LCT and spec."""
        lct = LCT.create(
            entity_type=EntityType.DICTIONARY,
            public_key=public_key,
            society=society,
            witnesses=witnesses,
            t3=t3,
            v3=v3,
            capabilities=["translate", "evolve", "witness_translations"],
        )

        # Bind to source and target domains
        lct.mrh.bound.append(f"lct:web4:domain:{source_domain}")
        lct.mrh.bound.append(f"lct:web4:domain:{target_domain}")

        spec = DictionarySpec(
            source_domain=source_domain,
            target_domain=target_domain,
            bidirectional=bidirectional,
            version=version,
            coverage=coverage or DomainCoverage(),
            compression=compression or CompressionProfile(),
            dictionary_type=dictionary_type,
        )

        initial_version = DictionaryVersion(
            version=version,
            changelog="Initial version",
        )

        return DictionaryEntity(
            lct=lct,
            spec=spec,
            evolution=evolution or EvolutionConfig(),
            versions=[initial_version],
        )

    @property
    def lct_id(self) -> str:
        return self.lct.lct_id

    @property
    def t3(self) -> T3:
        return self.lct.t3

    @property
    def v3(self) -> V3:
        return self.lct.v3

    @property
    def current_version(self) -> str:
        return self.versions[-1].version if self.versions else "0.0.0"

    @property
    def success_rate(self) -> float:
        """Translation success rate [0,1]."""
        if self.translation_count == 0:
            return 0.0
        return self.successful_translations / self.translation_count

    def can_translate(self, source_domain: str, target_domain: str) -> bool:
        """Check if this dictionary covers the requested domain pair."""
        return self.spec.covers_domains(source_domain, target_domain)

    def meets_trust_requirement(self, minimum_t3_composite: float) -> bool:
        """Check if dictionary's trust meets the minimum threshold."""
        return self.lct.t3.composite >= minimum_t3_composite

    def record_translation(
        self,
        request: TranslationRequest,
        content: str,
        confidence: float,
        witness_lct_ids: Optional[List[str]] = None,
    ) -> TranslationResult:
        """
        Record a translation and update statistics.

        This does NOT process content — the confidence and content are provided
        by the application layer. This module tracks metadata and trust.
        """
        self.translation_count += 1
        if confidence >= request.minimum_fidelity:
            self.successful_translations += 1

        witness_required = confidence < 0.95 or request.require_witness

        result = TranslationResult(
            content=content,
            confidence=confidence,
            degradation=1.0 - confidence,
            dictionary_lct_id=self.lct_id,
            witness_required=witness_required,
            witness_lct_ids=witness_lct_ids or [],
        )

        # Add witnesses to MRH
        for w_id in (witness_lct_ids or []):
            self.lct.add_witness(w_id)

        return result

    def apply_feedback(self, feedback: FeedbackRecord):
        """
        Apply feedback to update the dictionary's trust (spec §5.1).

        Corrections lower temperament slightly (inconsistency signal).
        Validations raise training (demonstrated accuracy).
        """
        self.feedback_history.append(feedback)

        if feedback.feedback_type == "correction":
            # Correction = evidence of inaccuracy → lower quality update
            self.lct.t3 = self.lct.t3.update(quality=0.3, success=False)
        elif feedback.feedback_type == "validation" and feedback.success:
            # Successful validation → positive quality update
            self.lct.t3 = self.lct.t3.update(quality=0.7, success=True)

    def create_new_version(self, new_version: str, changelog: str = "") -> DictionaryVersion:
        """Create a new versioned snapshot (spec §5.1)."""
        parent = self.current_version
        corrections = sum(
            1 for f in self.feedback_history if f.feedback_type == "correction"
        )

        version = DictionaryVersion(
            version=new_version,
            parent_version=parent,
            changelog=changelog,
            corrections_applied=corrections,
        )
        self.versions.append(version)
        return version


# ── Dictionary Selection ─────────────────────────────────────────

# Selection weights (spec §6.2)
SELECTION_WEIGHT_TRUST = 0.4
SELECTION_WEIGHT_COVERAGE = 0.3
SELECTION_WEIGHT_RECENCY = 0.2
SELECTION_WEIGHT_COST = 0.1


def dictionary_selection_score(
    trust_composite: float,
    coverage_ratio: float,
    recency_score: float,
    cost_score: float = 1.0,
) -> float:
    """
    Score a dictionary candidate for selection (spec §6.2).

    Higher is better. All inputs should be in [0,1].
    cost_score: 1.0 = free, 0.0 = most expensive.
    """
    return (
        SELECTION_WEIGHT_TRUST * _clamp(trust_composite)
        + SELECTION_WEIGHT_COVERAGE * _clamp(coverage_ratio)
        + SELECTION_WEIGHT_RECENCY * _clamp(recency_score)
        + SELECTION_WEIGHT_COST * _clamp(cost_score)
    )


def select_best_dictionary(
    candidates: List[DictionaryEntity],
    source_domain: str,
    target_domain: str,
    coverage_scores: Optional[Dict[str, float]] = None,
    recency_scores: Optional[Dict[str, float]] = None,
    cost_scores: Optional[Dict[str, float]] = None,
) -> Optional[DictionaryEntity]:
    """
    Select the best dictionary from candidates (spec §6.2).

    Filters candidates by domain coverage, then ranks by composite score.
    coverage_scores, recency_scores, cost_scores are keyed by lct_id.
    If not provided, defaults to 1.0 (assume perfect).
    """
    coverage_scores = coverage_scores or {}
    recency_scores = recency_scores or {}
    cost_scores = cost_scores or {}

    eligible = [d for d in candidates if d.can_translate(source_domain, target_domain)]
    if not eligible:
        return None

    best = None
    best_score = -1.0

    for d in eligible:
        score = dictionary_selection_score(
            trust_composite=d.t3.composite,
            coverage_ratio=coverage_scores.get(d.lct_id, 1.0),
            recency_score=recency_scores.get(d.lct_id, 1.0),
            cost_score=cost_scores.get(d.lct_id, 1.0),
        )
        if score > best_score:
            best_score = score
            best = d

    return best
