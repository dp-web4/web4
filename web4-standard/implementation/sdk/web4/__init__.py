"""
Web4 SDK — core data types and operations.

Provides offline-capable primitives for:
- Trust tensors (T3/V3) — multi-dimensional trust and value assessment
- Linked Context Tokens (LCT) — identity and presence substrate
- ATP/ADP lifecycle — bio-inspired value metabolism
- Federation (SAL) — Society, Authority, Law governance with citizenship lifecycle,
  quorum policy, ledger types, law merge, and audit adjustments
- R7 Action Framework — Rules+Role+Request+Reference+Resource->Result+Reputation
- MRH graph — Markov Relevancy Horizon context traversal
- ACP — Agentic Context Protocol for autonomous agent workflows
- Dictionary entities — semantic bridges with trust-tracked translation
- Reputation computation — rule-based reputation engine with aggregation and decay
- Entity taxonomy — behavioral modes, energy patterns, and interaction rules
- Capability levels — 6-level LCT capability framework (Stub -> Hardware)
- Error taxonomy — RFC 9457 error types for 6 Web4 protocol categories
- Metabolic states — society operational modes with energy, trust, and witness effects
- Multi-device binding — device constellation management, trust computation, and recovery
- Society — core organizational primitive composing federation, treasury, ledger, and trust
- Security primitives — crypto suite definitions, W4ID identifiers, key policies, VCs
- Core protocol — handshake, transport, discovery, and Web4 URI types
- MCP protocol types — Web4 context headers, resources, sessions, ATP metering
- Attestation — unified hardware trust envelope, verification dispatcher

These modules define the canonical data types and algorithms specified
in the web4-standard. They work offline (no network services required)
and are designed to be imported by applications, services, and other
SDKs that build on web4.

Usage::

    from web4 import T3, LCT, Society, R7Action
    from web4 import W4ID, parse_w4id
    from web4 import ATPAccount, energy_ratio

For module-specific imports (recommended for large applications)::

    from web4.trust import T3, V3
    from web4.federation import Society, LawDataset
    from web4.security import W4ID, CryptoSuite
"""

__version__ = "0.10.1"

# ── Trust (T3/V3) ──────────────────────────────────────────────
from .trust import (
    T3,
    V3,
    TrustProfile,
    ActionOutcome,
    RoleRequirement,
    compute_team_t3,
    operational_health,
    is_healthy,
    T3_JSONLD_CONTEXT,
    V3_JSONLD_CONTEXT,
)

# ── Linked Context Tokens ──────────────────────────────────────
from .lct import (
    LCT,
    EntityType,
    RevocationStatus,
    BirthCertificate,
    Attestation,
    LineageEntry,
    LCT_JSONLD_CONTEXT,
)

# ── ATP/ADP ────────────────────────────────────────────────────
from .atp import (
    ATPAccount,
    TransferResult,
    ATP_JSONLD_CONTEXT,
    energy_ratio,
)

# ── Federation (SAL) ──────────────────────────────────────────
from .federation import (
    Society,
    Society as FederationSociety,
    LawDataset,
    Delegation,
    RoleType,
    CitizenshipStatus,
    CitizenshipRecord,
    valid_citizenship_transition,
    QuorumMode,
    QuorumPolicy,
    LedgerType,
    AuditRequest,
    AuditAdjustment,
    Norm,
    Procedure,
    Interpretation,
    merge_law,
)

# ── R7 Action Framework ───────────────────────────────────────
from .r6 import (
    R7Action,
    ActionChain,
    ActionStatus,
    ReputationDelta,
    Rules,
    Role,
    Request,
    ResourceRequirements,
    Result,
    build_action,
    R7_JSONLD_CONTEXT,
)

# ── MRH Graph ─────────────────────────────────────────────────
from .mrh import (
    MRHGraph,
    MRHNode,
    MRHEdge,
    RelationType,
    mrh_trust_decay,
    mrh_zone,
    propagate_multiplicative,
    propagate_probabilistic,
    propagate_maximal,
)

# ── ACP (Agentic Context Protocol) ────────────────────────────
from .acp import (
    ACP_JSONLD_CONTEXT,
    ACPStateMachine,
    ACPState,
    ACPError,
    AgentPlan,
    PlanStep,
    Intent,
    Decision,
    DecisionType,
    ProofOfAgency,
    ExecutionRecord,
    ApprovalMode,
    ResourceCaps,
    Guards,
    Trigger,
    TriggerKind,
    build_intent,
    validate_plan,
)

# ── Dictionary Entities ───────────────────────────────────────
from .dictionary import (
    DICTIONARY_JSONLD_CONTEXT,
    DictionaryEntity,
    DictionarySpec,
    DictionaryType,
    DictionaryVersion,
    CompressionProfile,
    DomainCoverage,
    TranslationRequest,
    TranslationResult,
    TranslationChain,
    dictionary_selection_score,
    select_best_dictionary,
)

# ── Reputation ─────────────────────────────────────────────────
from .reputation import (
    ReputationRule,
    DimensionImpact,
    Modifier,
    ReputationEngine,
    ReputationStore,
    analyze_factors,
)

# ── Entity Taxonomy ────────────────────────────────────────────
from .entity import (
    BehavioralMode,
    EnergyPattern,
    InteractionType,
    EntityTypeInfo,
    ENTITY_JSONLD_CONTEXT,
    behavioral_modes,
    energy_pattern,
    is_agentic,
    can_initiate,
    can_delegate,
    can_process_r6,
    valid_interaction,
    all_entity_types,
    entity_registry_to_jsonld,
)

# ── Capability Levels ─────────────────────────────────────────
from .capability import (
    CapabilityLevel,
    TrustTier,
    ENTITY_LEVEL_RANGES,
    LevelRequirement,
    CAPABILITY_JSONLD_CONTEXT,
    assess_level,
    validate_level,
    can_upgrade,
    level_requirements,
    trust_tier,
    entity_level_range,
    is_level_typical,
    common_ground,
    capability_assessment_to_jsonld,
    capability_framework_to_jsonld,
)

# ── Error Taxonomy ─────────────────────────────────────────────
from .errors import (
    ErrorCode,
    ErrorCategory,
    ErrorMeta,
    Web4Error,
    BindingError,
    PairingError,
    WitnessError,
    AuthzError,
    CryptoError,
    ProtoError,
    get_error_meta,
    codes_for_category,
    make_error,
)

# ── Metabolic States ──────────────────────────────────────────
from .metabolic import (
    MetabolicState,
    TrustEffect,
    MetabolicProfile,
    ReliabilityFactors,
    ENERGY_MULTIPLIERS,
    TRUST_EFFECTS,
    WITNESS_REQUIREMENTS,
    DORMANT_STATES,
    ACTIVE_STATES,
    reachable_states,
    transition_trigger,
    all_transitions,
    energy_cost,
    wake_penalty,
    metabolic_reliability,
    required_witnesses,
    all_profiles,
    is_dormant,
    accepts_transactions,
    accepts_new_citizens,
)
# Alias to disambiguate from other Transition types
from .metabolic import Transition as MetabolicTransition
from .metabolic import valid_transition as metabolic_valid_transition

# ── Multi-device Binding ──────────────────────────────────────
from .binding import (
    AnchorType,
    DeviceStatus,
    HardwareAnchor,
    DeviceRecord,
    DeviceConstellation,
    ANCHOR_TRUST_WEIGHT,
    ANCHOR_TYPE_TO_ATTESTATION,
    ATTESTATION_TO_ANCHOR_TYPE,
    CONSTELLATION_TRUST_CEILING,
    WITNESS_DECAY_TABLE,
    witness_freshness,
    default_recovery_quorum,
    attestation_anchor_type,
    binding_anchor_type,
    enroll_device,
    remove_device,
    coherence_bonus,
    cross_witness_density,
    constellation_trust_ceiling,
    compute_device_trust,
    compute_constellation_trust,
    record_cross_witness,
    check_recovery_quorum,
    can_recover,
)

# ── Society ────────────────────────────────────────────────────
from .society import (
    SocietyPhase,
    LedgerEventType,
    LedgerEntry,
    SocietyLedger,
    Treasury,
    SocietyState,
    create_society,
    admit_citizen,
    suspend_citizen,
    reinstate_citizen,
    terminate_citizen,
    transition_metabolic_state,
    deposit_treasury,
    allocate_treasury,
    record_law_change,
    compute_society_t3,
    society_energy_cost,
    society_health,
    incorporate_child,
    society_depth,
    society_ancestry,
)

# ── Security Primitives ───────────────────────────────────────
from .security import (
    CryptoSuiteId,
    CryptoSuite,
    EncodingProfile,
    SUITE_BASE,
    SUITE_FIPS,
    SUITES,
    get_suite,
    negotiate_suite,
    W4ID,
    W4IDError,
    parse_w4id,
    derive_pairwise_w4id,
    KNOWN_METHODS,
    KeyStorageLevel,
    KeyPolicy,
    SignatureEnvelope,
    VerifiableCredential,
)

# ── Core Protocol ─────────────────────────────────────────────
from .protocol import (
    HandshakePhase,
    ClientHello,
    ServerHello,
    ClientFinished,
    ServerFinished,
    HandshakeMessage,
    PairingMethod,
    Transport,
    TransportCompliance,
    TransportProfile,
    TRANSPORT_PROFILES,
    get_transport_profile,
    required_transports,
    negotiate_transport,
    DiscoveryMethod,
    PrivacyLevel,
    DISCOVERY_METADATA,
    required_discovery_methods,
    discovery_privacy,
    DiscoveryRequest,
    DiscoveryResponse,
    Web4URI,
    web4_uri_to_dict,
    web4_uri_from_dict,
    transport_profile_to_dict,
)

# ── Attestation (Hardware Trust) ──────────────────────────────
from .attestation import (
    AttestationEnvelope,
    AnchorInfo,
    Proof,
    PlatformState,
    VerificationResult,
    TRUST_CEILINGS,
    FRESHNESS_MAX_AGE,
    ATTESTATION_JSONLD_CONTEXT,
    verify_envelope,
)

# ── MCP Protocol Types ────────────────────────────────────────
from .mcp import (
    CommunicationPattern,
    TrustDimension,
    MCPResourceType,
    TrustRequirements,
    MCPToolResource,
    MCPPromptResource,
    TrustContext,
    Web4Context,
    WitnessedInteraction,
    WitnessAttestation,
    MCPCapabilities,
    CapabilityBroadcast,
    MCPAuthority,
    MCPSession,
    SessionHandoff,
    PricingModifiers,
    calculate_mcp_cost,
    MCPErrorContext,
    web4_context_to_json,
    web4_context_from_json,
)
# Aliases for disambiguation with r6 types
from .mcp import ResourceRequirements as MCPResourceRequirements
from .mcp import ProofOfAgency as MCPProofOfAgency


# ── Public API ─────────────────────────────────────────────────
__all__ = [
    # version
    "__version__",
    # trust
    "T3", "V3", "TrustProfile", "ActionOutcome", "RoleRequirement",
    "compute_team_t3", "operational_health", "is_healthy",
    "T3_JSONLD_CONTEXT", "V3_JSONLD_CONTEXT",
    # lct
    "LCT", "EntityType", "RevocationStatus", "BirthCertificate",
    "Attestation", "LineageEntry", "LCT_JSONLD_CONTEXT",
    # atp
    "ATPAccount", "TransferResult", "ATP_JSONLD_CONTEXT", "energy_ratio",
    # federation
    "Society", "FederationSociety", "LawDataset", "Delegation", "RoleType",
    "CitizenshipStatus", "CitizenshipRecord", "valid_citizenship_transition",
    "QuorumMode", "QuorumPolicy", "LedgerType",
    "AuditRequest", "AuditAdjustment",
    "Norm", "Procedure", "Interpretation", "merge_law",
    # r6/r7
    "R7Action", "ActionChain", "ActionStatus", "ReputationDelta",
    "Rules", "Role", "Request", "ResourceRequirements", "Result",
    "build_action", "R7_JSONLD_CONTEXT",
    # mrh
    "MRHGraph", "MRHNode", "MRHEdge", "RelationType",
    "mrh_trust_decay", "mrh_zone",
    "propagate_multiplicative", "propagate_probabilistic", "propagate_maximal",
    # acp
    "ACP_JSONLD_CONTEXT", "ACPStateMachine", "ACPState", "ACPError",
    "AgentPlan", "PlanStep", "Intent", "Decision", "DecisionType",
    "ProofOfAgency", "ExecutionRecord",
    "ApprovalMode", "ResourceCaps", "Guards", "Trigger", "TriggerKind",
    "build_intent", "validate_plan",
    # dictionary
    "DICTIONARY_JSONLD_CONTEXT",
    "DictionaryEntity", "DictionarySpec", "DictionaryType", "DictionaryVersion",
    "CompressionProfile", "DomainCoverage",
    "TranslationRequest", "TranslationResult", "TranslationChain",
    "dictionary_selection_score", "select_best_dictionary",
    # reputation
    "ReputationRule", "DimensionImpact", "Modifier",
    "ReputationEngine", "ReputationStore", "analyze_factors",
    # entity
    "BehavioralMode", "EnergyPattern", "InteractionType",
    "EntityTypeInfo", "ENTITY_JSONLD_CONTEXT",
    "behavioral_modes", "energy_pattern",
    "is_agentic", "can_initiate", "can_delegate", "can_process_r6",
    "valid_interaction", "all_entity_types", "entity_registry_to_jsonld",
    # capability
    "CapabilityLevel", "TrustTier", "ENTITY_LEVEL_RANGES", "LevelRequirement",
    "CAPABILITY_JSONLD_CONTEXT",
    "assess_level", "validate_level", "can_upgrade",
    "level_requirements", "trust_tier",
    "entity_level_range", "is_level_typical", "common_ground",
    "capability_assessment_to_jsonld", "capability_framework_to_jsonld",
    # errors
    "ErrorCode", "ErrorCategory", "ErrorMeta",
    "Web4Error", "BindingError", "PairingError", "WitnessError",
    "AuthzError", "CryptoError", "ProtoError",
    "get_error_meta", "codes_for_category", "make_error",
    # metabolic
    "MetabolicState", "MetabolicTransition", "metabolic_valid_transition",
    "TrustEffect", "MetabolicProfile", "ReliabilityFactors",
    "ENERGY_MULTIPLIERS", "TRUST_EFFECTS", "WITNESS_REQUIREMENTS",
    "DORMANT_STATES", "ACTIVE_STATES",
    "reachable_states", "transition_trigger", "all_transitions",
    "energy_cost", "wake_penalty", "metabolic_reliability",
    "required_witnesses", "all_profiles",
    "is_dormant", "accepts_transactions", "accepts_new_citizens",
    # binding
    "AnchorType", "DeviceStatus",
    "HardwareAnchor", "DeviceRecord", "DeviceConstellation",
    "ANCHOR_TRUST_WEIGHT", "ANCHOR_TYPE_TO_ATTESTATION", "ATTESTATION_TO_ANCHOR_TYPE",
    "CONSTELLATION_TRUST_CEILING", "WITNESS_DECAY_TABLE",
    "witness_freshness", "default_recovery_quorum",
    "attestation_anchor_type", "binding_anchor_type",
    "enroll_device", "remove_device",
    "coherence_bonus", "cross_witness_density",
    "constellation_trust_ceiling", "compute_device_trust", "compute_constellation_trust",
    "record_cross_witness", "check_recovery_quorum", "can_recover",
    # society
    "SocietyPhase", "LedgerEventType",
    "LedgerEntry", "SocietyLedger", "Treasury", "SocietyState",
    "create_society",
    "admit_citizen", "suspend_citizen", "reinstate_citizen", "terminate_citizen",
    "transition_metabolic_state",
    "deposit_treasury", "allocate_treasury", "record_law_change",
    "compute_society_t3", "society_energy_cost", "society_health",
    "incorporate_child", "society_depth", "society_ancestry",
    # security
    "CryptoSuiteId", "CryptoSuite", "EncodingProfile",
    "SUITE_BASE", "SUITE_FIPS", "SUITES",
    "get_suite", "negotiate_suite",
    "W4ID", "W4IDError", "parse_w4id", "derive_pairwise_w4id", "KNOWN_METHODS",
    "KeyStorageLevel", "KeyPolicy",
    "SignatureEnvelope", "VerifiableCredential",
    # protocol
    "HandshakePhase",
    "ClientHello", "ServerHello", "ClientFinished", "ServerFinished",
    "HandshakeMessage", "PairingMethod",
    "Transport", "TransportCompliance", "TransportProfile", "TRANSPORT_PROFILES",
    "get_transport_profile", "required_transports", "negotiate_transport",
    "DiscoveryMethod", "PrivacyLevel", "DISCOVERY_METADATA",
    "required_discovery_methods", "discovery_privacy",
    "DiscoveryRequest", "DiscoveryResponse",
    "Web4URI", "web4_uri_to_dict", "web4_uri_from_dict",
    "transport_profile_to_dict",
    # attestation
    "AttestationEnvelope", "AnchorInfo", "Proof", "PlatformState",
    "VerificationResult", "TRUST_CEILINGS", "FRESHNESS_MAX_AGE",
    "ATTESTATION_JSONLD_CONTEXT", "verify_envelope",
    # mcp
    "CommunicationPattern", "TrustDimension", "MCPResourceType",
    "TrustRequirements", "MCPResourceRequirements",
    "MCPToolResource", "MCPPromptResource",
    "MCPProofOfAgency",
    "TrustContext", "Web4Context",
    "WitnessedInteraction", "WitnessAttestation",
    "MCPCapabilities", "CapabilityBroadcast",
    "MCPAuthority", "MCPSession", "SessionHandoff",
    "PricingModifiers", "calculate_mcp_cost",
    "MCPErrorContext",
    "web4_context_to_json", "web4_context_from_json",
]
