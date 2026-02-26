#!/usr/bin/env python3
"""
Spatial Web Integration — Reference Implementation
====================================================
Implements the integration specification from:
  web4-standard/SPATIAL_WEB_INTEGRATION.md (244 lines)

Covers ALL sections:
  §1 Overview — Parallel concepts mapping (Active Inference↔ACP, Spatial Web↔MRH, HSML↔Dict+MCP)
  §2 Critical Gaps — Trust economics, cryptographic identity, trust accountability, trust as force
  §3 Integration Opportunities — RGMs, Active Inference, HSML, HSTP
  §4 Integration Architecture — Foundation/Semantic/Accountability/Application layers
  §5 Implementation Strategy — Phase 1 mapping, Phase 2 integration, Phase 3 convergence
  §6 Key Advantages — Developer, user, organization perspectives
  §7 Risks and Mitigations — Complexity, performance, adoption
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ══════════════════════════════════════════════════════════════
# §1 — Parallel Concepts Mapping
# ══════════════════════════════════════════════════════════════

class SpatialWebConcept(Enum):
    """Spatial Web framework concepts."""
    ACTIVE_INFERENCE = "active_inference"
    SPATIAL_WEB = "spatial_web"
    HSML_HSTP = "hsml_hstp"
    UNIVERSAL_DOMAIN_GRAPH = "universal_domain_graph"
    RGM = "renormalizing_generative_model"


class Web4Concept(Enum):
    """Corresponding Web4 framework concepts."""
    ACP = "agentic_context_protocol"
    MRH = "markov_relevancy_horizon"
    DICTIONARY_MCP = "dictionary_entities_mcp"
    LCT_REGISTRY_MRH = "lct_registry_mrh_graphs"
    TRUST_TENSORS = "trust_tensors"


@dataclass
class ConceptMapping:
    """Maps a Spatial Web concept to its Web4 parallel."""
    spatial_web: SpatialWebConcept
    web4: Web4Concept
    overlap: str
    web4_additions: List[str]


# Canonical mappings from §1
CONCEPT_MAPPINGS: List[ConceptMapping] = [
    ConceptMapping(
        spatial_web=SpatialWebConcept.ACTIVE_INFERENCE,
        web4=Web4Concept.ACP,
        overlap="Autonomous agent decision-making with context-aware reasoning",
        web4_additions=[
            "Cryptographic proof-of-agency",
            "Delegated authority verification",
            "Trust tensor integration",
            "Audit trail requirements",
        ],
    ),
    ConceptMapping(
        spatial_web=SpatialWebConcept.SPATIAL_WEB,
        web4=Web4Concept.MRH,
        overlap="Contextual boundaries and multi-dimensional relationships",
        web4_additions=[
            "Fractal trust decay over distance",
            "Cryptographically verified witness relationships",
            "Context-dependent trust calculations",
            "Unforgeable presence through LCT binding",
        ],
    ),
    ConceptMapping(
        spatial_web=SpatialWebConcept.HSML_HSTP,
        web4=Web4Concept.DICTIONARY_MCP,
        overlap="Semantic interoperability and cross-domain translation",
        web4_additions=[
            "Compression-trust unity principle",
            "Living dictionary entities with their own LCTs",
            "Trust-aware routing through MCP",
            "ATP metering for value exchange",
        ],
    ),
    ConceptMapping(
        spatial_web=SpatialWebConcept.UNIVERSAL_DOMAIN_GRAPH,
        web4=Web4Concept.LCT_REGISTRY_MRH,
        overlap="Distributed knowledge representation",
        web4_additions=[
            "Cryptographic identity binding",
            "Immutable audit trails",
            "Trust-weighted relationships",
            "Society-governed registries",
        ],
    ),
]


# ══════════════════════════════════════════════════════════════
# §2 — Critical Gaps in Spatial Web
# ══════════════════════════════════════════════════════════════

class GapCategory(Enum):
    TRUST_ECONOMICS = "trust_economics"
    CRYPTOGRAPHIC_IDENTITY = "cryptographic_identity"
    TRUST_ACCOUNTABILITY = "trust_accountability"
    TRUST_AS_FORCE = "trust_as_force"


@dataclass
class CriticalGap:
    """A capability gap in Spatial Web that Web4 addresses."""
    category: GapCategory
    missing_capabilities: List[str]
    web4_solution: str


CRITICAL_GAPS: List[CriticalGap] = [
    CriticalGap(
        category=GapCategory.TRUST_ECONOMICS,
        missing_capabilities=[
            "ATP/ADP Value Cycle",
            "Anti-hoarding Mechanisms",
            "Proof-of-value",
            "Economic Incentives",
        ],
        web4_solution="ATP/ADP token cycle with proof-of-value creation and anti-hoarding",
    ),
    CriticalGap(
        category=GapCategory.CRYPTOGRAPHIC_IDENTITY,
        missing_capabilities=[
            "Weak Identity Binding (DIDs not enforced)",
            "No Birth Certificates",
            "Missing Proof-of-presence",
            "Revocation Gaps",
        ],
        web4_solution="LCT binding with birth certificates and witness-verified creation",
    ),
    CriticalGap(
        category=GapCategory.TRUST_ACCOUNTABILITY,
        missing_capabilities=[
            "Society-Authority-Law (SAL)",
            "Law Oracle",
            "Democratic Consensus",
            "Dispute Resolution",
        ],
        web4_solution="SAL framework with law oracle enforcement and dispute resolution",
    ),
    CriticalGap(
        category=GapCategory.TRUST_AS_FORCE,
        missing_capabilities=[
            "Trust Tensors (T3/V3)",
            "Trust Gravity",
            "Trust Degradation",
            "Trust Accumulation",
        ],
        web4_solution="T3/V3 tensor system with trust gravity and fractal degradation",
    ),
]


# ══════════════════════════════════════════════════════════════
# §3 — Integration Opportunities
# ══════════════════════════════════════════════════════════════

class IntegrationOpportunity(Enum):
    """What Spatial Web can enhance in Web4."""
    RGM_COMPRESSION = "rgm_compression"
    ACTIVE_INFERENCE_PLANNING = "active_inference_planning"
    HSML_SEMANTICS = "hsml_semantics"
    HSTP_ROUTING = "hstp_routing"


@dataclass
class EnhancementTarget:
    """A specific Web4 capability enhanced by Spatial Web integration."""
    opportunity: IntegrationOpportunity
    web4_targets: List[str]
    enhancement_description: str


ENHANCEMENT_TARGETS: List[EnhancementTarget] = [
    EnhancementTarget(
        opportunity=IntegrationOpportunity.RGM_COMPRESSION,
        web4_targets=[
            "Dictionary Entity compression algorithms",
            "Predictive trust scoring models",
            "Context-aware value calculations",
            "Adaptive coordination rules",
        ],
        enhancement_description="Renormalizing Generative Models enhance Web4 compression-trust algorithms",
    ),
    EnhancementTarget(
        opportunity=IntegrationOpportunity.ACTIVE_INFERENCE_PLANNING,
        web4_targets=[
            "ACP agent planning algorithms",
            "Decision-making under uncertainty",
            "Multi-agent coordination",
            "Resource optimization",
        ],
        enhancement_description="Active Inference strengthens Web4 agent planning and coordination",
    ),
    EnhancementTarget(
        opportunity=IntegrationOpportunity.HSML_SEMANTICS,
        web4_targets=[
            "Standardized semantic descriptions",
            "Rich metadata representation",
            "Cross-domain ontology mapping",
            "Interoperable data formats",
        ],
        enhancement_description="HSML provides standardized semantic layer for Web4",
    ),
    EnhancementTarget(
        opportunity=IntegrationOpportunity.HSTP_ROUTING,
        web4_targets=[
            "MCP routing capabilities",
            "Complex interaction patterns",
            "Spatial context awareness",
            "Temporal relationship modeling",
        ],
        enhancement_description="HSTP enhances Web4 multi-dimensional protocol routing",
    ),
]


# ══════════════════════════════════════════════════════════════
# §4 — Integration Architecture (4-layer stack)
# ══════════════════════════════════════════════════════════════

class ArchitectureLayer(Enum):
    FOUNDATION = "foundation"          # Web4 Core
    SEMANTIC_ENHANCEMENT = "semantic"  # Hybrid
    TRUST_ACCOUNTABILITY = "accountability"  # Web4 Exclusive
    APPLICATION = "application"        # ACT Platform


@dataclass
class FoundationLayer:
    """Foundation Layer — Web4 Core (§4).
    Identity: LCTs, Ed25519/X25519, birth certificates
    Trust: MRH, T3/V3, trust gravity
    Value: ATP/ADP, proof-of-value, anti-hoarding
    """
    identity_primitives: List[str] = field(default_factory=lambda: [
        "Linked Context Tokens (LCTs)",
        "Ed25519/X25519 cryptography",
        "Birth certificates with witnesses",
    ])
    trust_primitives: List[str] = field(default_factory=lambda: [
        "MRH fractal boundaries",
        "T3/V3 trust tensors",
        "Trust gravity calculations",
    ])
    value_primitives: List[str] = field(default_factory=lambda: [
        "ATP/ADP token cycle",
        "Proof-of-value creation",
        "Anti-hoarding mechanisms",
    ])


@dataclass
class SemanticLayer:
    """Semantic Enhancement Layer — Hybrid (§4).
    Translation: Dictionary Entities + HSML + RGM
    Communication: MCP + HSTP + Active Inference
    Knowledge: MRH graphs + Universal Domain Graph
    """
    translation_components: Dict[str, str] = field(default_factory=lambda: {
        "web4": "Dictionary Entities",
        "spatial_web": "HSML semantic descriptions",
        "enhancement": "RGM predictive models",
    })
    communication_components: Dict[str, str] = field(default_factory=lambda: {
        "web4": "Model Context Protocol (MCP)",
        "spatial_web": "HSTP routing",
        "enhancement": "Active Inference planning",
    })
    knowledge_components: Dict[str, str] = field(default_factory=lambda: {
        "web4": "MRH graphs",
        "spatial_web": "Universal Domain Graph patterns",
        "verification": "All verified through LCT signatures",
    })


@dataclass
class AccountabilityLayer:
    """Trust Accountability Layer — Web4 Exclusive (§4)."""
    society: List[str] = field(default_factory=lambda: [
        "Membership and citizenship",
        "Birth certificate issuance",
        "Collective decision-making",
    ])
    authority: List[str] = field(default_factory=lambda: [
        "Delegated permissions",
        "Proof-of-agency",
        "Revocation mechanisms",
    ])
    law: List[str] = field(default_factory=lambda: [
        "Smart contract rules",
        "Law oracle enforcement",
        "Dispute resolution",
    ])


@dataclass
class ApplicationLayer:
    """Application Layer — ACT Platform (§4)."""
    capabilities: List[str] = field(default_factory=lambda: [
        "Human-friendly interface",
        "Semantic query processing (HSML)",
        "Trust-verified responses (Web4)",
        "Value-metered interactions (ATP)",
    ])


@dataclass
class IntegrationArchitecture:
    """Complete 4-layer integration architecture."""
    foundation: FoundationLayer = field(default_factory=FoundationLayer)
    semantic: SemanticLayer = field(default_factory=SemanticLayer)
    accountability: AccountabilityLayer = field(default_factory=AccountabilityLayer)
    application: ApplicationLayer = field(default_factory=ApplicationLayer)

    def layer_count(self) -> int:
        return 4

    def web4_exclusive_layers(self) -> List[ArchitectureLayer]:
        """Layers that are exclusively Web4 (no Spatial Web equivalent)."""
        return [ArchitectureLayer.FOUNDATION, ArchitectureLayer.TRUST_ACCOUNTABILITY]

    def hybrid_layers(self) -> List[ArchitectureLayer]:
        """Layers that combine Web4 + Spatial Web."""
        return [ArchitectureLayer.SEMANTIC_ENHANCEMENT, ArchitectureLayer.APPLICATION]


# ══════════════════════════════════════════════════════════════
# §5 — Implementation Strategy (3 phases)
# ══════════════════════════════════════════════════════════════

class Phase(Enum):
    PROTOCOL_MAPPING = 1    # Map ontologies, implement endpoints, add RGM
    SEMANTIC_INTEGRATION = 2  # Extend dictionaries, enable Active Inference, support UDG
    FULL_CONVERGENCE = 3    # Bidirectional bridges, trust routing, hybrid agents


@dataclass
class PhaseTask:
    """A task within an implementation phase."""
    description: str
    completed: bool = False


@dataclass
class ImplementationPhase:
    """An implementation strategy phase."""
    phase: Phase
    name: str
    tasks: List[PhaseTask]

    def progress(self) -> float:
        if not self.tasks:
            return 0.0
        return sum(1 for t in self.tasks if t.completed) / len(self.tasks)


IMPLEMENTATION_PHASES: List[ImplementationPhase] = [
    ImplementationPhase(
        phase=Phase.PROTOCOL_MAPPING,
        name="Protocol Mapping",
        tasks=[
            PhaseTask("Map HSML ontologies to Dictionary Entity structures"),
            PhaseTask("Implement HSTP-compatible endpoints in MCP bridges"),
            PhaseTask("Add RGM models to trust calculation algorithms"),
        ],
    ),
    ImplementationPhase(
        phase=Phase.SEMANTIC_INTEGRATION,
        name="Semantic Integration",
        tasks=[
            PhaseTask("Extend Dictionary Entities with HSML descriptors"),
            PhaseTask("Enable Active Inference planning in ACP"),
            PhaseTask("Support Universal Domain Graph queries via MRH"),
        ],
    ),
    ImplementationPhase(
        phase=Phase.FULL_CONVERGENCE,
        name="Full Convergence",
        tasks=[
            PhaseTask("Create bidirectional bridges between protocols"),
            PhaseTask("Implement trust-verified semantic routing"),
            PhaseTask("Deploy hybrid agents using both frameworks"),
        ],
    ),
]


# ══════════════════════════════════════════════════════════════
# §6 — Key Advantages
# ══════════════════════════════════════════════════════════════

class Stakeholder(Enum):
    DEVELOPERS = "developers"
    USERS = "users"
    ORGANIZATIONS = "organizations"


@dataclass
class Advantage:
    """A key advantage for a specific stakeholder."""
    stakeholder: Stakeholder
    benefit: str
    source: str  # "spatial_web", "web4", or "hybrid"


ADVANTAGES: List[Advantage] = [
    # Developers
    Advantage(Stakeholder.DEVELOPERS, "Rich semantic capabilities WITH trust guarantees", "hybrid"),
    Advantage(Stakeholder.DEVELOPERS, "Multi-dimensional interactions WITH value exchange", "hybrid"),
    Advantage(Stakeholder.DEVELOPERS, "Active planning WITH accountability", "hybrid"),
    # Users
    Advantage(Stakeholder.USERS, "Natural language interaction (Spatial Web semantics)", "spatial_web"),
    Advantage(Stakeholder.USERS, "Guaranteed authenticity (Web4 trust)", "web4"),
    Advantage(Stakeholder.USERS, "Fair value exchange (ATP/ADP economy)", "web4"),
    # Organizations
    Advantage(Stakeholder.ORGANIZATIONS, "Semantic interoperability between systems", "spatial_web"),
    Advantage(Stakeholder.ORGANIZATIONS, "Cryptographic proof of all interactions", "web4"),
    Advantage(Stakeholder.ORGANIZATIONS, "Accountability and compliance built-in", "web4"),
]


# ══════════════════════════════════════════════════════════════
# §7 — Risks and Mitigations
# ══════════════════════════════════════════════════════════════

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Risk:
    """An integration risk with mitigation."""
    name: str
    description: str
    level: RiskLevel
    mitigation: str


INTEGRATION_RISKS: List[Risk] = [
    Risk(
        name="Complexity Risk",
        description="Combining two complex systems",
        level=RiskLevel.HIGH,
        mitigation="Modular architecture, optional semantic features",
    ),
    Risk(
        name="Performance Risk",
        description="Additional overhead from dual protocols",
        level=RiskLevel.MEDIUM,
        mitigation="Caching, selective verification, progressive enhancement",
    ),
    Risk(
        name="Adoption Risk",
        description="Requiring understanding of both systems",
        level=RiskLevel.MEDIUM,
        mitigation="ACT as abstraction layer, hiding complexity",
    ),
]


# ══════════════════════════════════════════════════════════════
# Integration Bridge — Practical Implementation
# ══════════════════════════════════════════════════════════════

@dataclass
class HSMLDescriptor:
    """A Spatial Web HSML semantic descriptor mapped to Web4."""
    hsml_type: str          # HSML type identifier
    semantic_label: str     # Human-readable label
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DictionaryHSMLBridge:
    """Bridge between Web4 Dictionary Entities and HSML descriptors.

    Phase 1: Map HSML ontologies to Dictionary Entity structures.
    """
    dictionary_lct: str
    domain: str
    hsml_mappings: Dict[str, HSMLDescriptor] = field(default_factory=dict)

    def add_mapping(self, web4_term: str, hsml: HSMLDescriptor):
        self.hsml_mappings[web4_term] = hsml

    def translate_to_hsml(self, web4_term: str) -> Optional[HSMLDescriptor]:
        return self.hsml_mappings.get(web4_term)

    def translate_from_hsml(self, hsml_type: str) -> Optional[str]:
        for term, desc in self.hsml_mappings.items():
            if desc.hsml_type == hsml_type:
                return term
        return None

    def coverage(self) -> int:
        return len(self.hsml_mappings)


@dataclass
class TrustVerifiedRoute:
    """Trust-verified semantic routing (Phase 3).

    Combines HSTP routing with Web4 trust verification.
    """
    source_lct: str
    destination_lct: str
    semantic_path: List[str]   # HSML path labels
    trust_score: float = 0.0  # T3 composite along route
    atp_cost: float = 0.0     # ATP metering

    def is_trusted(self, threshold: float = 0.5) -> bool:
        return self.trust_score >= threshold

    def cost_per_hop(self) -> float:
        if not self.semantic_path:
            return 0.0
        return self.atp_cost / len(self.semantic_path)


@dataclass
class HybridAgent:
    """A hybrid agent using both Web4 and Spatial Web capabilities (Phase 3)."""
    lct_id: str
    spatial_web_id: str
    capabilities: List[str] = field(default_factory=list)
    trust_score: float = 0.5

    def has_web4_identity(self) -> bool:
        return self.lct_id.startswith("lct:web4:")

    def has_spatial_identity(self) -> bool:
        return len(self.spatial_web_id) > 0

    def is_hybrid(self) -> bool:
        return self.has_web4_identity() and self.has_spatial_identity()


# ══════════════════════════════════════════════════════════════
# Spec Availability Comparison
# ══════════════════════════════════════════════════════════════

class SpecStatus(Enum):
    RATIFIED = "ratified"
    OPEN_DEVELOPMENT = "open_development"


@dataclass
class SpecAvailability:
    """Specification availability comparison (end of spec doc)."""
    name: str
    status: SpecStatus
    open_source: bool
    has_reference_impl: bool
    access: str  # "free", "purchase_required"


SPEC_COMPARISON = [
    SpecAvailability("Spatial Web (IEEE P2874)", SpecStatus.RATIFIED,
                     open_source=False, has_reference_impl=False, access="purchase_required"),
    SpecAvailability("Web4", SpecStatus.OPEN_DEVELOPMENT,
                     open_source=True, has_reference_impl=True, access="free"),
]


# ══════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {label} {detail}")

    # ── T1: Concept Mappings (§1) ──
    print("T1: Concept Mappings (§1)")

    check("T1.1 Four concept mappings", len(CONCEPT_MAPPINGS) == 4)

    ai_mapping = [m for m in CONCEPT_MAPPINGS if m.spatial_web == SpatialWebConcept.ACTIVE_INFERENCE][0]
    check("T1.2 Active Inference → ACP", ai_mapping.web4 == Web4Concept.ACP)
    check("T1.3 ACP has 4 additions", len(ai_mapping.web4_additions) == 4)
    check("T1.4 Proof-of-agency in ACP additions",
          any("proof-of-agency" in a.lower() for a in ai_mapping.web4_additions))

    sw_mapping = [m for m in CONCEPT_MAPPINGS if m.spatial_web == SpatialWebConcept.SPATIAL_WEB][0]
    check("T1.5 Spatial Web → MRH", sw_mapping.web4 == Web4Concept.MRH)
    check("T1.6 Fractal trust in MRH additions",
          any("fractal" in a.lower() for a in sw_mapping.web4_additions))

    hsml_mapping = [m for m in CONCEPT_MAPPINGS if m.spatial_web == SpatialWebConcept.HSML_HSTP][0]
    check("T1.7 HSML → Dictionary+MCP", hsml_mapping.web4 == Web4Concept.DICTIONARY_MCP)
    check("T1.8 Compression-trust in additions",
          any("compression" in a.lower() for a in hsml_mapping.web4_additions))

    udg_mapping = [m for m in CONCEPT_MAPPINGS if m.spatial_web == SpatialWebConcept.UNIVERSAL_DOMAIN_GRAPH][0]
    check("T1.9 UDG → LCT Registry+MRH", udg_mapping.web4 == Web4Concept.LCT_REGISTRY_MRH)

    # Each mapping has overlap description
    for m in CONCEPT_MAPPINGS:
        check(f"T1.10 {m.spatial_web.value} has overlap", len(m.overlap) > 0)

    # ── T2: Critical Gaps (§2) ──
    print("T2: Critical Gaps (§2)")

    check("T2.1 Four gap categories", len(CRITICAL_GAPS) == 4)

    trust_econ = [g for g in CRITICAL_GAPS if g.category == GapCategory.TRUST_ECONOMICS][0]
    check("T2.2 Trust economics has ATP", any("ATP" in c for c in trust_econ.missing_capabilities))

    crypto_id = [g for g in CRITICAL_GAPS if g.category == GapCategory.CRYPTOGRAPHIC_IDENTITY][0]
    check("T2.3 Crypto identity has birth cert", any("Birth" in c for c in crypto_id.missing_capabilities))

    accountability = [g for g in CRITICAL_GAPS if g.category == GapCategory.TRUST_ACCOUNTABILITY][0]
    check("T2.4 Accountability has SAL", any("SAL" in c for c in accountability.missing_capabilities))

    trust_force = [g for g in CRITICAL_GAPS if g.category == GapCategory.TRUST_AS_FORCE][0]
    check("T2.5 Trust force has T3/V3", any("T3/V3" in c for c in trust_force.missing_capabilities))

    # Each gap has Web4 solution
    for g in CRITICAL_GAPS:
        check(f"T2.6 {g.category.value} has solution", len(g.web4_solution) > 0)

    # ── T3: Integration Opportunities (§3) ──
    print("T3: Integration Opportunities (§3)")

    check("T3.1 Four enhancement targets", len(ENHANCEMENT_TARGETS) == 4)

    rgm = [e for e in ENHANCEMENT_TARGETS if e.opportunity == IntegrationOpportunity.RGM_COMPRESSION][0]
    check("T3.2 RGM targets dictionary compression",
          any("dictionary" in t.lower() for t in rgm.web4_targets))

    ai_enh = [e for e in ENHANCEMENT_TARGETS if e.opportunity == IntegrationOpportunity.ACTIVE_INFERENCE_PLANNING][0]
    check("T3.3 Active Inference targets ACP",
          any("acp" in t.lower() for t in ai_enh.web4_targets))

    hsml_enh = [e for e in ENHANCEMENT_TARGETS if e.opportunity == IntegrationOpportunity.HSML_SEMANTICS][0]
    check("T3.4 HSML targets semantic descriptions",
          any("semantic" in t.lower() for t in hsml_enh.web4_targets))

    hstp_enh = [e for e in ENHANCEMENT_TARGETS if e.opportunity == IntegrationOpportunity.HSTP_ROUTING][0]
    check("T3.5 HSTP targets MCP routing",
          any("mcp" in t.lower() for t in hstp_enh.web4_targets))

    # Each target has 4 items
    for e in ENHANCEMENT_TARGETS:
        check(f"T3.6 {e.opportunity.value} has 4 targets", len(e.web4_targets) == 4)

    # ── T4: Integration Architecture (§4) ──
    print("T4: Integration Architecture (§4)")

    arch = IntegrationArchitecture()
    check("T4.1 Four layers", arch.layer_count() == 4)
    check("T4.2 Two exclusive layers", len(arch.web4_exclusive_layers()) == 2)
    check("T4.3 Two hybrid layers", len(arch.hybrid_layers()) == 2)

    # Foundation layer
    check("T4.4 Foundation has LCT", any("LCT" in p for p in arch.foundation.identity_primitives))
    check("T4.5 Foundation has MRH", any("MRH" in p for p in arch.foundation.trust_primitives))
    check("T4.6 Foundation has ATP", any("ATP" in p for p in arch.foundation.value_primitives))

    # Semantic layer
    check("T4.7 Semantic has Dict", "Dictionary" in arch.semantic.translation_components["web4"])
    check("T4.8 Semantic has HSML", "HSML" in arch.semantic.translation_components["spatial_web"])
    check("T4.9 Semantic has MCP", "MCP" in arch.semantic.communication_components["web4"])

    # Accountability layer
    check("T4.10 SAL: Society", len(arch.accountability.society) == 3)
    check("T4.11 SAL: Authority", len(arch.accountability.authority) == 3)
    check("T4.12 SAL: Law", len(arch.accountability.law) == 3)

    # Application layer
    check("T4.13 App has 4 capabilities", len(arch.application.capabilities) == 4)
    check("T4.14 App has HSML", any("HSML" in c for c in arch.application.capabilities))
    check("T4.15 App has ATP", any("ATP" in c for c in arch.application.capabilities))

    # ── T5: Implementation Strategy (§5) ──
    print("T5: Implementation Strategy (§5)")

    check("T5.1 Three phases", len(IMPLEMENTATION_PHASES) == 3)

    phase1 = IMPLEMENTATION_PHASES[0]
    check("T5.2 Phase 1 is Protocol Mapping", phase1.phase == Phase.PROTOCOL_MAPPING)
    check("T5.3 Phase 1 has 3 tasks", len(phase1.tasks) == 3)
    check("T5.4 Phase 1 progress 0%", phase1.progress() == 0.0)

    phase1.tasks[0].completed = True
    check("T5.5 Phase 1 progress 33%", abs(phase1.progress() - 1/3) < 1e-10)
    phase1.tasks[0].completed = False  # reset

    phase2 = IMPLEMENTATION_PHASES[1]
    check("T5.6 Phase 2 is Semantic Integration", phase2.phase == Phase.SEMANTIC_INTEGRATION)
    check("T5.7 Phase 2 has HSML task",
          any("HSML" in t.description for t in phase2.tasks))

    phase3 = IMPLEMENTATION_PHASES[2]
    check("T5.8 Phase 3 is Full Convergence", phase3.phase == Phase.FULL_CONVERGENCE)
    check("T5.9 Phase 3 has hybrid agents",
          any("hybrid" in t.description.lower() for t in phase3.tasks))

    # ── T6: Advantages (§6) ──
    print("T6: Advantages (§6)")

    check("T6.1 Nine advantages", len(ADVANTAGES) == 9)

    dev_adv = [a for a in ADVANTAGES if a.stakeholder == Stakeholder.DEVELOPERS]
    check("T6.2 Three developer advantages", len(dev_adv) == 3)
    check("T6.3 All developer advantages are hybrid",
          all(a.source == "hybrid" for a in dev_adv))

    user_adv = [a for a in ADVANTAGES if a.stakeholder == Stakeholder.USERS]
    check("T6.4 Three user advantages", len(user_adv) == 3)

    org_adv = [a for a in ADVANTAGES if a.stakeholder == Stakeholder.ORGANIZATIONS]
    check("T6.5 Three org advantages", len(org_adv) == 3)

    # ── T7: Risks and Mitigations (§7) ──
    print("T7: Risks and Mitigations (§7)")

    check("T7.1 Three risks", len(INTEGRATION_RISKS) == 3)

    complexity = [r for r in INTEGRATION_RISKS if r.name == "Complexity Risk"][0]
    check("T7.2 Complexity is high", complexity.level == RiskLevel.HIGH)
    check("T7.3 Complexity mitigation", "modular" in complexity.mitigation.lower())

    performance = [r for r in INTEGRATION_RISKS if r.name == "Performance Risk"][0]
    check("T7.4 Performance is medium", performance.level == RiskLevel.MEDIUM)
    check("T7.5 Performance mitigation", "caching" in performance.mitigation.lower())

    adoption = [r for r in INTEGRATION_RISKS if r.name == "Adoption Risk"][0]
    check("T7.6 Adoption is medium", adoption.level == RiskLevel.MEDIUM)
    check("T7.7 Adoption mitigation", "act" in adoption.mitigation.lower())

    # Each risk has all fields
    for r in INTEGRATION_RISKS:
        check(f"T7.8 {r.name} has description", len(r.description) > 0)

    # ── T8: Dictionary-HSML Bridge ──
    print("T8: Dictionary-HSML Bridge")

    bridge = DictionaryHSMLBridge(
        dictionary_lct="lct:web4:dict:technical",
        domain="IoT",
    )

    # Add mappings
    bridge.add_mapping("sensor_reading", HSMLDescriptor(
        hsml_type="hsml:sensor:reading",
        semantic_label="Sensor Data Reading",
        properties={"unit": "celsius", "precision": 0.01},
    ))
    bridge.add_mapping("device_status", HSMLDescriptor(
        hsml_type="hsml:device:status",
        semantic_label="Device Operational Status",
    ))

    check("T8.1 Two mappings", bridge.coverage() == 2)

    # Web4 → HSML
    hsml = bridge.translate_to_hsml("sensor_reading")
    check("T8.2 Web4→HSML found", hsml is not None)
    check("T8.3 HSML type correct", hsml.hsml_type == "hsml:sensor:reading")
    check("T8.4 HSML has properties", hsml.properties["unit"] == "celsius")

    # HSML → Web4
    web4_term = bridge.translate_from_hsml("hsml:device:status")
    check("T8.5 HSML→Web4 found", web4_term == "device_status")

    # Unknown terms
    check("T8.6 Unknown Web4 term", bridge.translate_to_hsml("unknown") is None)
    check("T8.7 Unknown HSML type", bridge.translate_from_hsml("hsml:unknown") is None)

    # ── T9: Trust-Verified Routing ──
    print("T9: Trust-Verified Routing")

    route = TrustVerifiedRoute(
        source_lct="lct:web4:agent:alice",
        destination_lct="lct:web4:agent:bob",
        semantic_path=["sensor", "aggregator", "dashboard"],
        trust_score=0.85,
        atp_cost=30,
    )

    check("T9.1 Route is trusted", route.is_trusted(threshold=0.5))
    check("T9.2 Route not trusted at high threshold", not route.is_trusted(threshold=0.9))
    check("T9.3 Cost per hop", abs(route.cost_per_hop() - 10.0) < 1e-10)

    empty_route = TrustVerifiedRoute("a", "b", [], trust_score=0.0, atp_cost=0)
    check("T9.4 Empty route cost 0", empty_route.cost_per_hop() == 0.0)
    check("T9.5 Zero trust not trusted", not empty_route.is_trusted())

    # ── T10: Hybrid Agent ──
    print("T10: Hybrid Agent")

    agent = HybridAgent(
        lct_id="lct:web4:agent:hybrid1",
        spatial_web_id="sw:agent:hybrid1",
        capabilities=["semantic_query", "trust_verify", "value_meter"],
        trust_score=0.75,
    )

    check("T10.1 Has Web4 identity", agent.has_web4_identity())
    check("T10.2 Has Spatial identity", agent.has_spatial_identity())
    check("T10.3 Is hybrid", agent.is_hybrid())

    web4_only = HybridAgent(lct_id="lct:web4:agent:pure", spatial_web_id="")
    check("T10.4 Web4-only not hybrid", not web4_only.is_hybrid())
    check("T10.5 Web4-only has Web4 identity", web4_only.has_web4_identity())
    check("T10.6 Web4-only no spatial identity", not web4_only.has_spatial_identity())

    # ── T11: Spec Availability ──
    print("T11: Spec Availability")

    check("T11.1 Two specs compared", len(SPEC_COMPARISON) == 2)

    sw_spec = [s for s in SPEC_COMPARISON if "Spatial" in s.name][0]
    check("T11.2 Spatial Web ratified", sw_spec.status == SpecStatus.RATIFIED)
    check("T11.3 Spatial Web not open source", not sw_spec.open_source)
    check("T11.4 Spatial Web purchase required", sw_spec.access == "purchase_required")
    check("T11.5 Spatial Web no ref impl", not sw_spec.has_reference_impl)

    w4_spec = [s for s in SPEC_COMPARISON if "Web4" in s.name][0]
    check("T11.6 Web4 open development", w4_spec.status == SpecStatus.OPEN_DEVELOPMENT)
    check("T11.7 Web4 is open source", w4_spec.open_source)
    check("T11.8 Web4 free access", w4_spec.access == "free")
    check("T11.9 Web4 has ref impl", w4_spec.has_reference_impl)

    # ══════════════════════════════════════════════════════════

    print(f"\n{'='*60}")
    print(f"Spatial Web Integration: {passed}/{passed+failed} checks passed")
    if failed:
        print(f"  {failed} FAILED")
    else:
        print(f"  All checks passed!")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    run_tests()
