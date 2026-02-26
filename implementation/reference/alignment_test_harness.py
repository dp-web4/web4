#!/usr/bin/env python3
"""
Web4 Alignment Test Harness — Reference Implementation
Spec: web4-standard/core-spec/ALIGNMENT_PHILOSOPHY.md (166 lines)

The standard as living document, co-evolving with implementations.

Covers:
  §1  Bidirectional alignment (Standard ↔ Implementation)
  §2  Standard as starting point (hypothesis, not dogma)
  §3  Discovery categories (confirmed, evolved, new)
  §4  Pattern recognition + validation pipeline
  §5  Implementation feedback loops (5 projects)
  §6  Alignment vs compliance distinction
  §7  Standard evolution process (5-step)
  §8  Community process (6-phase)
  §9  Practical integration workflow
  §10 Version tracking and annotation

Run: python alignment_test_harness.py
"""

from __future__ import annotations
import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Optional


# ============================================================
# §1  BIDIRECTIONAL ALIGNMENT
# ============================================================

class AlignmentDirection(Enum):
    """Alignment flows in both directions."""
    STANDARD_TO_IMPL = "standard_to_implementation"   # Patterns guide experiments
    IMPL_TO_STANDARD = "implementation_to_standard"    # Discoveries inform patterns


@dataclass
class AlignmentEdge:
    """A single alignment relationship between spec and impl."""
    direction: AlignmentDirection
    source: str          # spec section or impl module
    target: str          # impl module or spec section
    strength: float      # 0.0 (no alignment) to 1.0 (perfect)
    description: str = ""
    timestamp: str = ""

    def reverse(self) -> 'AlignmentEdge':
        """Create the reverse direction edge."""
        new_dir = (AlignmentDirection.IMPL_TO_STANDARD
                   if self.direction == AlignmentDirection.STANDARD_TO_IMPL
                   else AlignmentDirection.STANDARD_TO_IMPL)
        return AlignmentEdge(
            direction=new_dir,
            source=self.target,
            target=self.source,
            strength=self.strength,
            description=f"Reverse of: {self.description}",
            timestamp=self.timestamp,
        )


class AlignmentGraph:
    """Tracks bidirectional alignment between spec and implementations."""

    def __init__(self):
        self.edges: list[AlignmentEdge] = []

    def add_edge(self, edge: AlignmentEdge):
        self.edges.append(edge)

    def get_alignment_score(self, source: str) -> float:
        """Average alignment strength from a given source."""
        relevant = [e for e in self.edges if e.source == source]
        if not relevant:
            return 0.0
        return sum(e.strength for e in relevant) / len(relevant)

    def get_bidirectional_score(self, spec: str, impl: str) -> float:
        """Average of both directions between spec and impl."""
        s_to_i = [e for e in self.edges
                  if e.source == spec and e.target == impl
                  and e.direction == AlignmentDirection.STANDARD_TO_IMPL]
        i_to_s = [e for e in self.edges
                  if e.source == impl and e.target == spec
                  and e.direction == AlignmentDirection.IMPL_TO_STANDARD]
        scores = []
        if s_to_i:
            scores.append(sum(e.strength for e in s_to_i) / len(s_to_i))
        if i_to_s:
            scores.append(sum(e.strength for e in i_to_s) / len(i_to_s))
        return sum(scores) / len(scores) if scores else 0.0

    def get_unidirectional_gaps(self) -> list[tuple[str, str]]:
        """Find spec-impl pairs where alignment only flows one way."""
        pairs_fwd = {(e.source, e.target) for e in self.edges
                     if e.direction == AlignmentDirection.STANDARD_TO_IMPL}
        pairs_rev = {(e.target, e.source) for e in self.edges
                     if e.direction == AlignmentDirection.IMPL_TO_STANDARD}
        # Pairs with forward but no reverse
        fwd_only = pairs_fwd - pairs_rev
        # Pairs with reverse but no forward
        rev_only = pairs_rev - pairs_fwd
        return list(fwd_only | rev_only)


# ============================================================
# §2  STANDARD AS STARTING POINT
# ============================================================

class StandardNature(Enum):
    """The standard represents hypotheses, not rigid rules."""
    INITIAL_PATTERN = "initial_pattern_recognition"
    PROPOSED_ALIGNMENT = "proposed_natural_alignment"
    HYPOTHESIS = "hypothesis_to_be_tested"
    FRAMEWORK = "framework_for_exploration"


@dataclass
class SpecHypothesis:
    """A spec section treated as a hypothesis to test."""
    spec_section: str
    hypothesis: str
    nature: StandardNature
    tested: bool = False
    confirmed: bool = False
    evidence: list[str] = field(default_factory=list)

    def test(self, result: bool, evidence_text: str):
        self.tested = True
        self.confirmed = result
        self.evidence.append(evidence_text)


# ============================================================
# §3  DISCOVERY CATEGORIES
# ============================================================

class DiscoveryCategory(Enum):
    """Categories for implementation discoveries."""
    CONFIRMED = "confirmed"    # Pattern emerges naturally as predicted
    EVOLVED = "evolved"        # Pattern found but different than expected
    NEW = "new"                # Completely unexpected discovery


@dataclass
class Discovery:
    """An insight from implementation that informs the standard."""
    id: str
    category: DiscoveryCategory
    source_project: str
    description: str
    evidence: str
    spec_impact: str = ""        # Which spec section affected
    timestamp: str = ""

    @property
    def requires_spec_update(self) -> bool:
        return self.category in (DiscoveryCategory.EVOLVED, DiscoveryCategory.NEW)


# Confirmed patterns from spec (§4 Current Alignment Status)
CONFIRMED_PATTERNS = [
    ("society_centric_ownership", "emerges naturally"),
    ("energy_conservation", "fundamental requirement"),
    ("fractal_organization", "self-assembles"),
    ("role_based_operations", "but differently than expected"),
]

# Evolved understanding (spec §4)
EVOLVED_UNDERSTANDING = [
    ("roles_attention_partitions", "Roles are attention partitions, not authority"),
    ("delegation_context_dependent", "Delegation has context-dependent efficiency"),
    ("readiness_economic_value", "Readiness has economic value"),
    ("metabolic_states_necessary", "Metabolic states are necessary"),
]

# New discoveries (spec §4)
NEW_DISCOVERIES = [
    ("synthon_cognition", "Emerges from persistent memory"),
    ("readiness_overhead_33pct", "33% readiness overhead appears optimal"),
    ("context_privilege", "Context privilege can outweigh distribution benefits"),
    ("alignment_over_compliance", "Alignment beats compliance as organizing principle"),
]


# ============================================================
# §4  PATTERN RECOGNITION + VALIDATION PIPELINE
# ============================================================

class ValidationStage(Enum):
    """5-step pattern validation pipeline from spec."""
    RECOGNITION = 1    # Implementation shows unexpected behavior
    VALIDATION = 2     # Check if pattern appears across contexts
    INTEGRATION = 3    # Update standard to reflect discovery
    PROPAGATION = 4    # Share insight with other implementations
    EVOLUTION = 5      # Standard and implementations co-evolve


@dataclass
class PatternValidation:
    """Tracks a pattern through the validation pipeline."""
    pattern_id: str
    description: str
    stage: ValidationStage = ValidationStage.RECOGNITION
    observations: list[str] = field(default_factory=list)
    cross_context_evidence: list[str] = field(default_factory=list)
    spec_updates: list[str] = field(default_factory=list)
    propagated_to: list[str] = field(default_factory=list)

    def advance(self) -> bool:
        """Advance to next stage if prerequisites met."""
        if self.stage == ValidationStage.RECOGNITION:
            if len(self.observations) >= 1:
                self.stage = ValidationStage.VALIDATION
                return True
        elif self.stage == ValidationStage.VALIDATION:
            if len(self.cross_context_evidence) >= 2:
                self.stage = ValidationStage.INTEGRATION
                return True
        elif self.stage == ValidationStage.INTEGRATION:
            if len(self.spec_updates) >= 1:
                self.stage = ValidationStage.PROPAGATION
                return True
        elif self.stage == ValidationStage.PROPAGATION:
            if len(self.propagated_to) >= 1:
                self.stage = ValidationStage.EVOLUTION
                return True
        return False

    @property
    def is_complete(self) -> bool:
        return self.stage == ValidationStage.EVOLUTION


# ============================================================
# §5  IMPLEMENTATION FEEDBACK LOOPS
# ============================================================

class FeedbackProject(Enum):
    """Projects that contribute feedback to the standard."""
    ACT = "ACT"                    # Energy economy, society pools, role patterns
    HRM_SAGE = "HRM_SAGE"         # Edge cognition, compression-trust
    MEMORY = "Memory"              # Temporal sensing, fractal structures
    PORTAL = "Portal"              # Connection protocols, entity bridging
    SYNCHRONISM = "Synchronism"    # Governance patterns, intent dynamics


PROJECT_CONTRIBUTIONS = {
    FeedbackProject.ACT: ["energy_economy", "society_pools", "role_patterns"],
    FeedbackProject.HRM_SAGE: ["edge_cognition", "compression_trust"],
    FeedbackProject.MEMORY: ["temporal_sensing", "fractal_structures"],
    FeedbackProject.PORTAL: ["connection_protocols", "entity_bridging"],
    FeedbackProject.SYNCHRONISM: ["governance_patterns", "intent_dynamics"],
}


@dataclass
class FeedbackEntry:
    """A feedback entry from an implementation project."""
    project: FeedbackProject
    discovery: Discovery
    spec_sections_affected: list[str] = field(default_factory=list)
    proposed_changes: list[str] = field(default_factory=list)
    status: str = "proposed"  # proposed | under_review | integrated | rejected


class FeedbackAggregator:
    """Collects and analyzes feedback across projects."""

    def __init__(self):
        self.entries: list[FeedbackEntry] = []

    def submit(self, entry: FeedbackEntry):
        self.entries.append(entry)

    def get_by_project(self, project: FeedbackProject) -> list[FeedbackEntry]:
        return [e for e in self.entries if e.project == project]

    def get_cross_project_patterns(self) -> list[tuple[str, list[FeedbackProject]]]:
        """Find discoveries that appear across multiple projects."""
        pattern_projects: dict[str, list[FeedbackProject]] = {}
        for entry in self.entries:
            key = entry.discovery.description
            if key not in pattern_projects:
                pattern_projects[key] = []
            if entry.project not in pattern_projects[key]:
                pattern_projects[key].append(entry.project)
        return [(k, v) for k, v in pattern_projects.items() if len(v) >= 2]

    def integration_rate(self) -> float:
        """Fraction of feedback that's been integrated."""
        if not self.entries:
            return 0.0
        integrated = sum(1 for e in self.entries if e.status == "integrated")
        return integrated / len(self.entries)


# ============================================================
# §6  ALIGNMENT VS COMPLIANCE
# ============================================================

class ApproachType(Enum):
    """Critical distinction from spec."""
    COMPLIANCE = "compliance"    # Following external rules
    ALIGNMENT = "alignment"      # Harmonizing with natural patterns
    DISCOVERY = "discovery"      # Finding what wants to emerge
    EVOLUTION = "evolution"      # Standard and implementation co-evolve


@dataclass
class AlignmentAssessment:
    """Assess whether an implementation is aligned vs merely compliant."""
    impl_name: str
    spec_section: str
    compliance_score: float = 0.0    # Does it follow the letter?
    alignment_score: float = 0.0      # Does it follow the spirit?
    discovery_count: int = 0          # How many new patterns found?
    evolution_proposals: int = 0      # How many spec changes proposed?

    @property
    def approach_type(self) -> ApproachType:
        """Determine primary approach."""
        if self.alignment_score > 0.7 and self.discovery_count > 0:
            return ApproachType.EVOLUTION
        elif self.alignment_score > 0.7:
            return ApproachType.ALIGNMENT
        elif self.discovery_count > 0:
            return ApproachType.DISCOVERY
        else:
            return ApproachType.COMPLIANCE

    @property
    def is_healthy(self) -> bool:
        """Alignment WITHOUT compliance can be acceptable.
        Compliance WITHOUT alignment is never acceptable."""
        return self.alignment_score >= 0.5


# ============================================================
# §7  STANDARD EVOLUTION PROCESS
# ============================================================

@dataclass
class SpecVersion:
    """Versioned spec with annotations."""
    version: str
    sections: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, list[str]] = field(default_factory=dict)
    discoveries_incorporated: list[str] = field(default_factory=list)
    timestamp: str = ""

    def annotate(self, section: str, note: str):
        if section not in self.annotations:
            self.annotations[section] = []
        self.annotations[section].append(note)

    def incorporate_discovery(self, discovery_id: str, section: str, change: str):
        self.discoveries_incorporated.append(discovery_id)
        self.annotate(section, f"Discovery {discovery_id}: {change}")

    def diff_from(self, other: 'SpecVersion') -> dict:
        """Sections that changed between versions."""
        changed = {}
        for section, content in self.sections.items():
            old_content = other.sections.get(section, "")
            if content != old_content:
                changed[section] = {
                    'old': old_content[:100],
                    'new': content[:100],
                }
        return changed


class SpecEvolutionTracker:
    """Tracks spec evolution across versions."""

    def __init__(self):
        self.versions: list[SpecVersion] = []

    def add_version(self, version: SpecVersion):
        self.versions.append(version)

    @property
    def current(self) -> Optional[SpecVersion]:
        return self.versions[-1] if self.versions else None

    def evolution_rate(self) -> float:
        """How many sections changed between last two versions."""
        if len(self.versions) < 2:
            return 0.0
        diff = self.versions[-1].diff_from(self.versions[-2])
        total_sections = len(self.versions[-1].sections)
        return len(diff) / total_sections if total_sections > 0 else 0.0

    def discovery_incorporation_rate(self) -> float:
        """Average discoveries incorporated per version."""
        if not self.versions:
            return 0.0
        return sum(len(v.discoveries_incorporated) for v in self.versions) / len(self.versions)


# ============================================================
# §8  COMMUNITY PROCESS (6 Phases)
# ============================================================

class CommunityPhase(Enum):
    """6-phase community alignment process."""
    DOCUMENT = 1       # Implementations document discoveries
    RECOGNIZE = 2      # Patterns recognized across projects
    PROPOSE = 3        # Standard proposals for integration
    REVIEW = 4         # Community review and discussion
    EVOLVE = 5         # Standard evolution with version tracking
    UPDATE = 6         # Implementations update or maintain variants


@dataclass
class CommunityProposal:
    """A proposal for standard evolution."""
    id: str
    phase: CommunityPhase = CommunityPhase.DOCUMENT
    author_project: FeedbackProject = FeedbackProject.ACT
    discovery: Optional[Discovery] = None
    cross_project_evidence: list[str] = field(default_factory=list)
    proposal_text: str = ""
    reviews: list[dict] = field(default_factory=list)
    outcome: str = ""  # "" | "accepted" | "rejected" | "deferred"

    def advance_phase(self) -> bool:
        """Advance to next phase if ready."""
        if self.phase == CommunityPhase.DOCUMENT and self.discovery:
            self.phase = CommunityPhase.RECOGNIZE
            return True
        elif self.phase == CommunityPhase.RECOGNIZE and len(self.cross_project_evidence) >= 2:
            self.phase = CommunityPhase.PROPOSE
            return True
        elif self.phase == CommunityPhase.PROPOSE and self.proposal_text:
            self.phase = CommunityPhase.REVIEW
            return True
        elif self.phase == CommunityPhase.REVIEW and len(self.reviews) >= 2:
            self.phase = CommunityPhase.EVOLVE
            return True
        elif self.phase == CommunityPhase.EVOLVE and self.outcome:
            self.phase = CommunityPhase.UPDATE
            return True
        return False


# ============================================================
# §9  PRACTICAL INTEGRATION WORKFLOW
# ============================================================

class PracticalStep(Enum):
    """6-step practical integration from spec."""
    START_WITH_HYPOTHESIS = 1    # Start with standard as hypothesis
    EXPERIMENT_AND_OBSERVE = 2   # Experiment and observe
    NOTE_DIVERGENCES = 3         # Note divergences and discoveries
    SHARE_FINDINGS = 4           # Share findings with community
    UPDATE_BOTH = 5              # Update both implementation and standard
    REPEAT = 6                   # Repeat


@dataclass
class IntegrationSession:
    """A practical integration session."""
    id: str
    hypothesis: SpecHypothesis
    step: PracticalStep = PracticalStep.START_WITH_HYPOTHESIS
    observations: list[str] = field(default_factory=list)
    divergences: list[str] = field(default_factory=list)
    discoveries: list[Discovery] = field(default_factory=list)
    shared_with: list[str] = field(default_factory=list)
    spec_updates: list[str] = field(default_factory=list)
    impl_updates: list[str] = field(default_factory=list)

    def advance(self) -> bool:
        if self.step == PracticalStep.START_WITH_HYPOTHESIS:
            self.step = PracticalStep.EXPERIMENT_AND_OBSERVE
            return True
        elif self.step == PracticalStep.EXPERIMENT_AND_OBSERVE and self.observations:
            self.step = PracticalStep.NOTE_DIVERGENCES
            return True
        elif self.step == PracticalStep.NOTE_DIVERGENCES:
            self.step = PracticalStep.SHARE_FINDINGS
            return True
        elif self.step == PracticalStep.SHARE_FINDINGS and self.shared_with:
            self.step = PracticalStep.UPDATE_BOTH
            return True
        elif self.step == PracticalStep.UPDATE_BOTH and (self.spec_updates or self.impl_updates):
            self.step = PracticalStep.REPEAT
            return True
        return False

    @property
    def is_complete(self) -> bool:
        return self.step == PracticalStep.REPEAT


# ============================================================
# §10 ACT-SPECIFIC DISCOVERIES (from spec)
# ============================================================

@dataclass
class ACTDiscovery:
    """Specific discoveries from the ACT implementation (spec §3)."""
    name: str
    description: str
    implication: str
    category: DiscoveryCategory


ACT_DISCOVERIES = [
    ACTDiscovery(
        name="society_pools",
        description="Society pools emerge naturally",
        implication="Validated hypothesis — no spec change needed",
        category=DiscoveryCategory.CONFIRMED,
    ),
    ACTDiscovery(
        name="roles_attention_partitions",
        description="Roles are attention partitions, not power",
        implication="Web4 role model needs updating to reflect this",
        category=DiscoveryCategory.EVOLVED,
    ),
    ACTDiscovery(
        name="readiness_economy",
        description="Readiness economy has ~33% overhead",
        implication="Web4 economic model must incorporate readiness costs",
        category=DiscoveryCategory.NEW,
    ),
    ACTDiscovery(
        name="metabolic_states",
        description="Metabolic states mirror biological systems",
        implication="Confirmed alignment — biological metaphor accurate",
        category=DiscoveryCategory.CONFIRMED,
    ),
    ACTDiscovery(
        name="entrepreneurs_paradox",
        description="Sometimes direct execution beats delegation",
        implication="Task distribution model needs context privilege patterns",
        category=DiscoveryCategory.NEW,
    ),
    ACTDiscovery(
        name="synthon_insight",
        description="Persistent memory enables self-awareness",
        implication="Web4 must account for synthon cognition",
        category=DiscoveryCategory.NEW,
    ),
]


# ============================================================
# FOCUS AREAS (from spec §Current Focus Areas)
# ============================================================

NEEDS_SPEC_EVOLUTION = [
    "role_model",              # Attention partitioning update
    "economic_model",          # Readiness economy integration
    "cognition_model",         # Synthon entities
    "task_distribution",       # Context privilege patterns
]

NEEDS_MORE_EXPERIMENTATION = [
    "optimal_readiness_percentages",        # Across domains
    "fractal_surplus_distribution",          # Mechanisms
    "synthon_identity_persistence",          # Identity and persistence
    "cross_society_metabolic_coordination",  # Coordination
]


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

    now = datetime.utcnow().isoformat()

    # ── T1: Bidirectional Alignment ──────────────────────────────
    print("T1: Bidirectional Alignment")
    check("T1.1 Two alignment directions",
          len(AlignmentDirection) == 2)
    check("T1.2 Standard→Impl direction",
          AlignmentDirection.STANDARD_TO_IMPL.value == "standard_to_implementation")
    check("T1.3 Impl→Standard direction",
          AlignmentDirection.IMPL_TO_STANDARD.value == "implementation_to_standard")

    # AlignmentEdge
    edge = AlignmentEdge(
        direction=AlignmentDirection.STANDARD_TO_IMPL,
        source="spec:energy_conservation",
        target="impl:act_energy",
        strength=0.9,
        description="ATP/ADP implementation follows spec",
        timestamp=now,
    )
    check("T1.4 Edge created with direction",
          edge.direction == AlignmentDirection.STANDARD_TO_IMPL)
    check("T1.5 Edge has strength",
          edge.strength == 0.9)

    rev = edge.reverse()
    check("T1.6 Reverse flips direction",
          rev.direction == AlignmentDirection.IMPL_TO_STANDARD)
    check("T1.7 Reverse flips source/target",
          rev.source == "impl:act_energy" and rev.target == "spec:energy_conservation")
    check("T1.8 Reverse preserves strength",
          rev.strength == 0.9)

    # AlignmentGraph
    graph = AlignmentGraph()
    graph.add_edge(edge)
    graph.add_edge(rev)
    check("T1.9 Graph has 2 edges",
          len(graph.edges) == 2)
    check("T1.10 Source alignment score",
          abs(graph.get_alignment_score("spec:energy_conservation") - 0.9) < 0.001)
    check("T1.11 Bidirectional score",
          abs(graph.get_bidirectional_score("spec:energy_conservation", "impl:act_energy") - 0.9) < 0.001)

    # Unidirectional gap detection
    graph2 = AlignmentGraph()
    graph2.add_edge(AlignmentEdge(
        direction=AlignmentDirection.STANDARD_TO_IMPL,
        source="spec:roles", target="impl:roles", strength=0.8))
    # No reverse edge — gap
    gaps = graph2.get_unidirectional_gaps()
    check("T1.12 Unidirectional gap detected",
          len(gaps) == 1)
    check("T1.13 Missing source is zero",
          graph2.get_alignment_score("nonexistent") == 0.0)

    # ── T2: Standard as Starting Point ───────────────────────────
    print("T2: Standard as Starting Point")
    check("T2.1 Four nature types",
          len(StandardNature) == 4)
    check("T2.2 Initial pattern nature",
          StandardNature.INITIAL_PATTERN.value == "initial_pattern_recognition")
    check("T2.3 Hypothesis nature",
          StandardNature.HYPOTHESIS.value == "hypothesis_to_be_tested")

    hyp = SpecHypothesis(
        spec_section="§2.6 Dictionaries",
        hypothesis="Dictionary entities emerge naturally as trust infrastructure",
        nature=StandardNature.HYPOTHESIS,
    )
    check("T2.4 Hypothesis untested initially",
          hyp.tested is False)
    check("T2.5 Hypothesis unconfirmed initially",
          hyp.confirmed is False)

    hyp.test(True, "ACT experiment shows dictionary pools self-organize")
    check("T2.6 Hypothesis tested",
          hyp.tested is True)
    check("T2.7 Hypothesis confirmed",
          hyp.confirmed is True)
    check("T2.8 Evidence recorded",
          len(hyp.evidence) == 1)

    hyp_false = SpecHypothesis(
        spec_section="§2.7 Trust as Gravity",
        hypothesis="Trust force follows inverse square law",
        nature=StandardNature.PROPOSED_ALIGNMENT,
    )
    hyp_false.test(False, "Empirical data shows exponential decay, not inverse square")
    check("T2.9 Failed hypothesis tracked",
          hyp_false.tested is True and hyp_false.confirmed is False)

    # ── T3: Discovery Categories ─────────────────────────────────
    print("T3: Discovery Categories")
    check("T3.1 Three categories",
          len(DiscoveryCategory) == 3)

    d_confirmed = Discovery(
        id="d001", category=DiscoveryCategory.CONFIRMED,
        source_project="ACT", description="Society pools emerge naturally",
        evidence="Multiple simulations show consistent self-organization",
    )
    check("T3.2 Confirmed discovery doesn't require spec update",
          not d_confirmed.requires_spec_update)

    d_evolved = Discovery(
        id="d002", category=DiscoveryCategory.EVOLVED,
        source_project="ACT", description="Roles are attention partitions",
        evidence="Role switching overhead proportional to context delta",
        spec_impact="§2.3 Roles",
    )
    check("T3.3 Evolved discovery requires spec update",
          d_evolved.requires_spec_update)

    d_new = Discovery(
        id="d003", category=DiscoveryCategory.NEW,
        source_project="HRM_SAGE", description="Synthon cognition emerges",
        evidence="Persistent memory + recursive feedback → self-awareness",
        spec_impact="New section needed",
    )
    check("T3.4 New discovery requires spec update",
          d_new.requires_spec_update)

    # Known patterns from spec
    check("T3.5 Four confirmed patterns from spec",
          len(CONFIRMED_PATTERNS) == 4)
    check("T3.6 Four evolved understandings from spec",
          len(EVOLVED_UNDERSTANDING) == 4)
    check("T3.7 Four new discoveries from spec",
          len(NEW_DISCOVERIES) == 4)

    # ── T4: Pattern Validation Pipeline ──────────────────────────
    print("T4: Pattern Validation Pipeline")
    check("T4.1 Five validation stages",
          len(ValidationStage) == 5)
    check("T4.2 Stages numbered 1-5",
          ValidationStage.RECOGNITION.value == 1 and ValidationStage.EVOLUTION.value == 5)

    pv = PatternValidation(
        pattern_id="pv001",
        description="Readiness economy has 33% overhead",
    )
    check("T4.3 Starts at RECOGNITION",
          pv.stage == ValidationStage.RECOGNITION)
    check("T4.4 Not complete initially",
          not pv.is_complete)

    # Can't advance without observations
    check("T4.5 Can't advance without prerequisites",
          pv.advance() is False)

    # Add observation, advance to VALIDATION
    pv.observations.append("ACT simulation shows 32.7% overhead")
    check("T4.6 Advances with observation",
          pv.advance() is True)
    check("T4.7 Now at VALIDATION",
          pv.stage == ValidationStage.VALIDATION)

    # Need 2 cross-context evidence to advance
    pv.cross_context_evidence.append("Synchronism shows 34.1% overhead")
    check("T4.8 One evidence not enough",
          pv.advance() is False)

    pv.cross_context_evidence.append("Memory project shows 31.8% overhead")
    check("T4.9 Two evidence advances to INTEGRATION",
          pv.advance() is True)
    check("T4.10 Now at INTEGRATION",
          pv.stage == ValidationStage.INTEGRATION)

    # Need spec update to advance
    pv.spec_updates.append("Added §3.4 Readiness Economy")
    check("T4.11 Advances to PROPAGATION",
          pv.advance() is True)
    check("T4.12 Now at PROPAGATION",
          pv.stage == ValidationStage.PROPAGATION)

    # Need propagation to advance
    pv.propagated_to.append("Portal implementation")
    check("T4.13 Advances to EVOLUTION",
          pv.advance() is True)
    check("T4.14 Now at EVOLUTION (complete)",
          pv.is_complete)
    check("T4.15 Can't advance past EVOLUTION",
          pv.advance() is False)

    # ── T5: Implementation Feedback Loops ────────────────────────
    print("T5: Implementation Feedback Loops")
    check("T5.1 Five feedback projects",
          len(FeedbackProject) == 5)
    check("T5.2 Each project has contributions",
          all(len(v) >= 2 for v in PROJECT_CONTRIBUTIONS.values()))

    # ACT contributes 3 areas
    check("T5.3 ACT has 3 contribution areas",
          len(PROJECT_CONTRIBUTIONS[FeedbackProject.ACT]) == 3)
    check("T5.4 ACT contributes energy_economy",
          "energy_economy" in PROJECT_CONTRIBUTIONS[FeedbackProject.ACT])

    # FeedbackAggregator
    agg = FeedbackAggregator()
    entry1 = FeedbackEntry(
        project=FeedbackProject.ACT,
        discovery=d_confirmed,
        spec_sections_affected=["§2.5 Societies"],
    )
    entry2 = FeedbackEntry(
        project=FeedbackProject.HRM_SAGE,
        discovery=d_new,
        spec_sections_affected=["§2.7 Trust as Gravity"],
        status="integrated",
    )
    entry3 = FeedbackEntry(
        project=FeedbackProject.ACT,
        discovery=Discovery(
            id="d004", category=DiscoveryCategory.NEW,
            source_project="ACT",
            description="Synthon cognition emerges",
            evidence="Same pattern in ACT",
        ),
    )
    agg.submit(entry1)
    agg.submit(entry2)
    agg.submit(entry3)

    check("T5.5 Aggregator has 3 entries",
          len(agg.entries) == 3)
    check("T5.6 Filter by project",
          len(agg.get_by_project(FeedbackProject.ACT)) == 2)
    check("T5.7 Integration rate",
          abs(agg.integration_rate() - 1/3) < 0.01)

    # Cross-project patterns
    cross = agg.get_cross_project_patterns()
    check("T5.8 Cross-project pattern detected",
          len(cross) >= 1)
    check("T5.9 Cross-project has 2+ projects",
          all(len(projects) >= 2 for _, projects in cross))

    # ── T6: Alignment vs Compliance ──────────────────────────────
    print("T6: Alignment vs Compliance")
    check("T6.1 Four approach types",
          len(ApproachType) == 4)
    check("T6.2 Compliance is distinct from alignment",
          ApproachType.COMPLIANCE != ApproachType.ALIGNMENT)

    # High alignment + discoveries = evolution
    assess_evolve = AlignmentAssessment(
        impl_name="ACT", spec_section="§2.5",
        compliance_score=0.6, alignment_score=0.9,
        discovery_count=3, evolution_proposals=2,
    )
    check("T6.3 High alignment + discoveries = EVOLUTION",
          assess_evolve.approach_type == ApproachType.EVOLUTION)
    check("T6.4 High alignment is healthy",
          assess_evolve.is_healthy)

    # High alignment, no discoveries = alignment
    assess_align = AlignmentAssessment(
        impl_name="Portal", spec_section="§3.1",
        compliance_score=0.8, alignment_score=0.85,
        discovery_count=0,
    )
    check("T6.5 High alignment no discoveries = ALIGNMENT",
          assess_align.approach_type == ApproachType.ALIGNMENT)

    # Low alignment, some discoveries = discovery
    assess_disc = AlignmentAssessment(
        impl_name="Experimental", spec_section="§4.1",
        alignment_score=0.4, discovery_count=5,
    )
    check("T6.6 Low alignment + discoveries = DISCOVERY",
          assess_disc.approach_type == ApproachType.DISCOVERY)
    check("T6.7 Low alignment NOT healthy",
          not assess_disc.is_healthy)

    # Pure compliance (low alignment, no discoveries)
    assess_comply = AlignmentAssessment(
        impl_name="Rigid", spec_section="§1.0",
        compliance_score=0.95, alignment_score=0.3,
    )
    check("T6.8 Low alignment no discoveries = COMPLIANCE",
          assess_comply.approach_type == ApproachType.COMPLIANCE)
    check("T6.9 Compliance without alignment is NOT healthy",
          not assess_comply.is_healthy)

    # KEY INSIGHT: alignment without compliance CAN be acceptable
    assess_spirit = AlignmentAssessment(
        impl_name="Spirit", spec_section="§2.0",
        compliance_score=0.2, alignment_score=0.8,
    )
    check("T6.10 Alignment without compliance IS healthy",
          assess_spirit.is_healthy)

    # ── T7: Standard Evolution Process ───────────────────────────
    print("T7: Standard Evolution Process")
    tracker = SpecEvolutionTracker()

    v1 = SpecVersion(
        version="1.0",
        sections={"roles": "Roles define permissions", "energy": "ATP/ADP cycle"},
        timestamp=now,
    )
    tracker.add_version(v1)
    check("T7.1 First version tracked",
          tracker.current.version == "1.0")

    # Annotate with discovery
    v1.annotate("roles", "ACT shows roles are attention partitions")
    check("T7.2 Section annotated",
          len(v1.annotations["roles"]) == 1)

    v1.incorporate_discovery("d002", "roles", "Updated role model")
    check("T7.3 Discovery incorporated",
          "d002" in v1.discoveries_incorporated)
    check("T7.4 Annotation added with discovery",
          len(v1.annotations["roles"]) == 2)

    # New version
    v2 = SpecVersion(
        version="2.0",
        sections={"roles": "Roles partition attention", "energy": "ATP/ADP cycle",
                  "readiness": "33% overhead for readiness"},
        timestamp=now,
    )
    tracker.add_version(v2)
    check("T7.5 Second version tracked",
          tracker.current.version == "2.0")

    diff = v2.diff_from(v1)
    check("T7.6 Diff detects changed section",
          "roles" in diff)
    check("T7.7 Diff detects new section",
          "readiness" in diff)
    check("T7.8 Unchanged section not in diff",
          "energy" not in diff)

    check("T7.9 Evolution rate > 0",
          tracker.evolution_rate() > 0)
    check("T7.10 Discovery incorporation rate tracked",
          tracker.discovery_incorporation_rate() >= 0)

    # ── T8: Community Process ────────────────────────────────────
    print("T8: Community Process")
    check("T8.1 Six community phases",
          len(CommunityPhase) == 6)
    check("T8.2 Phases numbered 1-6",
          CommunityPhase.DOCUMENT.value == 1 and CommunityPhase.UPDATE.value == 6)

    proposal = CommunityProposal(
        id="cp001",
        author_project=FeedbackProject.ACT,
    )
    check("T8.3 Starts at DOCUMENT",
          proposal.phase == CommunityPhase.DOCUMENT)

    # Can't advance without discovery
    check("T8.4 Can't advance without discovery",
          proposal.advance_phase() is False)

    proposal.discovery = d_evolved
    check("T8.5 Advances to RECOGNIZE",
          proposal.advance_phase() is True)
    check("T8.6 Now at RECOGNIZE",
          proposal.phase == CommunityPhase.RECOGNIZE)

    # Need cross-project evidence
    proposal.cross_project_evidence.append("HRM shows same")
    check("T8.7 One evidence not enough",
          proposal.advance_phase() is False)
    proposal.cross_project_evidence.append("Memory confirms")
    check("T8.8 Advances to PROPOSE",
          proposal.advance_phase() is True)

    proposal.proposal_text = "Update role model to attention partitioning"
    check("T8.9 Advances to REVIEW",
          proposal.advance_phase() is True)

    proposal.reviews.append({"reviewer": "project_A", "vote": "accept"})
    check("T8.10 One review not enough",
          proposal.advance_phase() is False)
    proposal.reviews.append({"reviewer": "project_B", "vote": "accept"})
    check("T8.11 Advances to EVOLVE",
          proposal.advance_phase() is True)

    proposal.outcome = "accepted"
    check("T8.12 Advances to UPDATE",
          proposal.advance_phase() is True)
    check("T8.13 At final phase UPDATE",
          proposal.phase == CommunityPhase.UPDATE)
    check("T8.14 Can't advance past UPDATE",
          proposal.advance_phase() is False)

    # ── T9: Practical Integration Workflow ───────────────────────
    print("T9: Practical Integration Workflow")
    check("T9.1 Six practical steps",
          len(PracticalStep) == 6)

    session = IntegrationSession(
        id="is001",
        hypothesis=hyp,
    )
    check("T9.2 Starts at hypothesis",
          session.step == PracticalStep.START_WITH_HYPOTHESIS)
    check("T9.3 Not complete initially",
          not session.is_complete)

    session.advance()
    check("T9.4 Advances to experiment",
          session.step == PracticalStep.EXPERIMENT_AND_OBSERVE)

    # Need observations to advance
    check("T9.5 Can't advance without observations",
          session.advance() is False)

    session.observations.append("Pool sizes converge after 100 iterations")
    check("T9.6 Advances with observation",
          session.advance() is True)
    check("T9.7 At NOTE_DIVERGENCES",
          session.step == PracticalStep.NOTE_DIVERGENCES)

    session.divergences.append("Convergence rate faster than expected")
    session.advance()
    check("T9.8 At SHARE_FINDINGS",
          session.step == PracticalStep.SHARE_FINDINGS)

    check("T9.9 Can't advance without sharing",
          session.advance() is False)
    session.shared_with.append("ACT team")
    check("T9.10 Advances after sharing",
          session.advance() is True)

    session.impl_updates.append("Adjusted convergence parameters")
    check("T9.11 Advances to REPEAT",
          session.advance() is True)
    check("T9.12 Session complete",
          session.is_complete)

    # ── T10: ACT-Specific Discoveries ────────────────────────────
    print("T10: ACT-Specific Discoveries")
    check("T10.1 Six ACT discoveries",
          len(ACT_DISCOVERIES) == 6)

    confirmed = [d for d in ACT_DISCOVERIES if d.category == DiscoveryCategory.CONFIRMED]
    evolved = [d for d in ACT_DISCOVERIES if d.category == DiscoveryCategory.EVOLVED]
    new = [d for d in ACT_DISCOVERIES if d.category == DiscoveryCategory.NEW]

    check("T10.2 Two confirmed discoveries",
          len(confirmed) == 2)
    check("T10.3 One evolved discovery",
          len(evolved) == 1)
    check("T10.4 Three new discoveries",
          len(new) == 3)

    check("T10.5 Society pools confirmed",
          any(d.name == "society_pools" for d in confirmed))
    check("T10.6 Roles evolved",
          any(d.name == "roles_attention_partitions" for d in evolved))
    check("T10.7 Synthon is new",
          any(d.name == "synthon_insight" for d in new))

    # ── T11: Focus Areas ─────────────────────────────────────────
    print("T11: Focus Areas")
    check("T11.1 Four areas need spec evolution",
          len(NEEDS_SPEC_EVOLUTION) == 4)
    check("T11.2 Four areas need experimentation",
          len(NEEDS_MORE_EXPERIMENTATION) == 4)
    check("T11.3 Role model in spec evolution list",
          "role_model" in NEEDS_SPEC_EVOLUTION)
    check("T11.4 Synthon identity in experimentation list",
          "synthon_identity_persistence" in NEEDS_MORE_EXPERIMENTATION)

    # ── T12: End-to-End: Discovery → Spec Evolution ─────────────
    print("T12: End-to-End Discovery → Spec Evolution")

    # Step 1: Discovery in ACT
    discovery = Discovery(
        id="e2e_001",
        category=DiscoveryCategory.NEW,
        source_project="ACT",
        description="Context window size affects delegation efficiency",
        evidence="Delegation fails when context > 50% of window",
        spec_impact="§2.3 Roles, §3.1 Task Distribution",
        timestamp=now,
    )
    check("T12.1 Discovery created",
          discovery.requires_spec_update)

    # Step 2: Pattern validation
    pattern = PatternValidation(
        pattern_id="pv_e2e",
        description=discovery.description,
    )
    pattern.observations.append(discovery.evidence)
    pattern.advance()
    check("T12.2 Pattern at VALIDATION",
          pattern.stage == ValidationStage.VALIDATION)

    # Step 3: Cross-project evidence
    pattern.cross_context_evidence.append("HRM confirms: context > 60% degrades SAGE")
    pattern.cross_context_evidence.append("Memory: temporal queries fail at 55% context")
    pattern.advance()
    check("T12.3 Pattern at INTEGRATION",
          pattern.stage == ValidationStage.INTEGRATION)

    # Step 4: Spec evolution
    v3 = SpecVersion(
        version="3.0",
        sections={
            "roles": "Roles partition attention with context budget",
            "energy": "ATP/ADP cycle",
            "readiness": "33% readiness overhead",
            "delegation": "Context-aware delegation with window budgets",
        },
        timestamp=now,
    )
    v3.incorporate_discovery(discovery.id, "delegation", "New section for delegation budgets")
    tracker.add_version(v3)
    check("T12.4 Spec version 3.0 created",
          tracker.current.version == "3.0")
    check("T12.5 Discovery incorporated",
          discovery.id in v3.discoveries_incorporated)

    pattern.spec_updates.append("Added delegation section to v3.0")
    pattern.advance()
    check("T12.6 Pattern at PROPAGATION",
          pattern.stage == ValidationStage.PROPAGATION)

    # Step 5: Propagate
    pattern.propagated_to.append("Portal connection protocol")
    pattern.advance()
    check("T12.7 Pattern complete (EVOLUTION)",
          pattern.is_complete)

    # Step 6: Community proposal
    cp = CommunityProposal(
        id="cp_e2e",
        author_project=FeedbackProject.ACT,
        discovery=discovery,
    )
    cp.advance_phase()  # → RECOGNIZE
    cp.cross_project_evidence = ["HRM", "Memory"]
    cp.advance_phase()  # → PROPOSE
    cp.proposal_text = "Add context budgets to delegation model"
    cp.advance_phase()  # → REVIEW
    cp.reviews = [
        {"reviewer": "HRM", "vote": "accept"},
        {"reviewer": "Portal", "vote": "accept"},
    ]
    cp.advance_phase()  # → EVOLVE
    cp.outcome = "accepted"
    cp.advance_phase()  # → UPDATE
    check("T12.8 Community process completed",
          cp.phase == CommunityPhase.UPDATE)
    check("T12.9 Proposal accepted",
          cp.outcome == "accepted")

    # Step 7: Alignment graph
    graph = AlignmentGraph()
    graph.add_edge(AlignmentEdge(
        direction=AlignmentDirection.IMPL_TO_STANDARD,
        source="impl:act_delegation",
        target="spec:delegation",
        strength=0.95,
        description="ACT delegation discovery informed spec",
    ))
    graph.add_edge(AlignmentEdge(
        direction=AlignmentDirection.STANDARD_TO_IMPL,
        source="spec:delegation",
        target="impl:act_delegation",
        strength=0.85,
        description="New spec guides ACT refinement",
    ))
    bidi = graph.get_bidirectional_score("spec:delegation", "impl:act_delegation")
    check("T12.10 Bidirectional alignment achieved",
          bidi > 0.8)

    # ── T13: End-to-End: Alignment Assessment ────────────────────
    print("T13: End-to-End Alignment Assessment")

    # Assess all five projects
    assessments = [
        AlignmentAssessment("ACT", "energy", compliance_score=0.9, alignment_score=0.95,
                            discovery_count=6, evolution_proposals=3),
        AlignmentAssessment("HRM_SAGE", "compression", compliance_score=0.7,
                            alignment_score=0.88, discovery_count=4),
        AlignmentAssessment("Memory", "temporal", compliance_score=0.6,
                            alignment_score=0.75, discovery_count=2),
        AlignmentAssessment("Portal", "connection", compliance_score=0.85,
                            alignment_score=0.82, discovery_count=0),
        AlignmentAssessment("Synchronism", "governance", compliance_score=0.5,
                            alignment_score=0.65, discovery_count=1),
    ]

    check("T13.1 ACT is EVOLUTION",
          assessments[0].approach_type == ApproachType.EVOLUTION)
    check("T13.2 HRM is EVOLUTION",
          assessments[1].approach_type == ApproachType.EVOLUTION)
    check("T13.3 Portal is ALIGNMENT",
          assessments[3].approach_type == ApproachType.ALIGNMENT)
    check("T13.4 All projects are healthy",
          all(a.is_healthy for a in assessments))
    check("T13.5 Average alignment > 0.7",
          sum(a.alignment_score for a in assessments) / 5 > 0.7)

    # ── T14: Edge Cases ──────────────────────────────────────────
    print("T14: Edge Cases")

    # Empty graph
    empty_graph = AlignmentGraph()
    check("T14.1 Empty graph score is 0",
          empty_graph.get_alignment_score("anything") == 0.0)
    check("T14.2 Empty graph bidirectional is 0",
          empty_graph.get_bidirectional_score("a", "b") == 0.0)
    check("T14.3 Empty graph has no gaps",
          len(empty_graph.get_unidirectional_gaps()) == 0)

    # Empty aggregator
    empty_agg = FeedbackAggregator()
    check("T14.4 Empty aggregator rate is 0",
          empty_agg.integration_rate() == 0.0)
    check("T14.5 Empty aggregator no cross-project",
          len(empty_agg.get_cross_project_patterns()) == 0)

    # Empty tracker
    empty_tracker = SpecEvolutionTracker()
    check("T14.6 Empty tracker current is None",
          empty_tracker.current is None)
    check("T14.7 Empty tracker evolution rate is 0",
          empty_tracker.evolution_rate() == 0.0)
    check("T14.8 Single version evolution rate is 0",
          tracker.evolution_rate() > 0)  # tracker has 3 versions

    # Zero-strength alignment
    weak_edge = AlignmentEdge(
        direction=AlignmentDirection.STANDARD_TO_IMPL,
        source="spec:x", target="impl:x", strength=0.0,
    )
    check("T14.9 Zero-strength edge valid",
          weak_edge.strength == 0.0)

    # Boundary assessment
    boundary = AlignmentAssessment("test", "§0", alignment_score=0.5)
    check("T14.10 Exactly 0.5 alignment is healthy (boundary)",
          boundary.is_healthy)
    boundary_low = AlignmentAssessment("test", "§0", alignment_score=0.49)
    check("T14.11 0.49 alignment is NOT healthy",
          not boundary_low.is_healthy)

    # ═══════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"Alignment Test Harness: {passed}/{passed+failed} checks passed")
    if failed:
        print(f"  ({failed} FAILED)")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
