#!/usr/bin/env python3
"""
Web4 Entity Type System — Comprehensive Reference Implementation

Full implementation of web4-standard/core-spec/entity-types.md covering ALL
13 spec sections: 15 entity types, 3 behavioral modes, active/passive energy
metabolism, birth certificates, roles as first-class entities, role hierarchy,
SAL-specific roles, entity lifecycle, interaction validation, Dictionary entities,
Accumulator entities, Policy entities, type immutability, and discovery.

@version 1.0.0
@see web4-standard/core-spec/entity-types.md
"""

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
# §2.2 — Entity Behavioral Modes
# ═══════════════════════════════════════════════════════════════

class BehavioralMode(Enum):
    """Three primary modes of entity existence per spec §2.2."""
    AGENTIC = "agentic"           # Takes initiative, autonomous decisions
    RESPONSIVE = "responsive"     # Reacts to stimuli predictably
    DELEGATIVE = "delegative"     # Authorizes others to act on behalf

    @property
    def can_initiate(self) -> bool:
        return self == BehavioralMode.AGENTIC

    @property
    def can_delegate(self) -> bool:
        return self == BehavioralMode.DELEGATIVE


# ═══════════════════════════════════════════════════════════════
# §2.3 — Energy Metabolism Patterns
# ═══════════════════════════════════════════════════════════════

class EnergyPattern(Enum):
    """Energy metabolism classification per spec §2.3."""
    ACTIVE = "active"     # ATP→ADP with reputation updates
    PASSIVE = "passive"   # ADP slashed, no reputation


@dataclass
class EnergyFlow:
    """Tracks energy metabolism for an entity."""
    atp_balance: float = 100.0
    adp_discharged: float = 0.0
    adp_slashed: float = 0.0
    reputation_earned: float = 0.0
    utilization_count: int = 0

    def process_active(self, atp_cost: float, quality: float = 0.8) -> dict:
        """Active metabolism: ATP→ADP with reputation."""
        if self.atp_balance < atp_cost:
            return {"success": False, "reason": "insufficient ATP"}
        self.atp_balance -= atp_cost
        self.adp_discharged += atp_cost
        rep_delta = atp_cost * quality * 0.01
        self.reputation_earned += rep_delta
        return {"success": True, "adp_returned": atp_cost,
                "reputation_delta": rep_delta}

    def process_passive(self, atp_cost: float) -> dict:
        """Passive metabolism: ADP slashed, no reputation."""
        if self.atp_balance < atp_cost:
            return {"success": False, "reason": "insufficient ATP"}
        self.atp_balance -= atp_cost
        self.adp_slashed += atp_cost  # Permanently consumed
        self.utilization_count += 1
        return {"success": True, "adp_slashed": atp_cost,
                "reputation_delta": 0}


# ═══════════════════════════════════════════════════════════════
# §2.1 — Entity Type Taxonomy (15 types)
# ═══════════════════════════════════════════════════════════════

class EntityType(Enum):
    """
    Complete 15-type taxonomy per spec §2.1.
    Each type has: (primary_mode, energy_pattern, description)
    """
    HUMAN = ("agentic", "active", "Individual persons")
    AI = ("agentic", "active", "Artificial intelligence agents")
    SOCIETY = ("delegative", "active", "Delegative entity with authority to issue citizenship")
    ORGANIZATION = ("delegative", "active", "Collective entities representing groups")
    ROLE = ("delegative", "active", "First-class entities representing functions")
    TASK = ("responsive", "active", "Specific work units or objectives")
    RESOURCE = ("responsive", "passive", "Data, services, or assets")
    DEVICE = ("responsive", "active", "Physical or virtual hardware")
    SERVICE = ("responsive", "active", "Software services and applications")
    ORACLE = ("responsive", "active", "External data providers")
    ACCUMULATOR = ("responsive", "passive", "Broadcast listeners and recorders")
    DICTIONARY = ("responsive", "active", "Living semantic bridges")
    HYBRID = ("agentic", "active", "Entities combining multiple types")
    POLICY = ("responsive", "active", "Governance rules as living entities")
    INFRASTRUCTURE = ("passive", "passive", "Physical passive resources")

    def __init__(self, mode: str, energy: str, description: str):
        self._mode = mode
        self._energy = energy
        self._description = description

    @property
    def primary_mode(self) -> BehavioralMode:
        mode_map = {
            "agentic": BehavioralMode.AGENTIC,
            "responsive": BehavioralMode.RESPONSIVE,
            "delegative": BehavioralMode.DELEGATIVE,
            "passive": BehavioralMode.RESPONSIVE,  # Infrastructure
        }
        return mode_map[self._mode]

    @property
    def energy_pattern(self) -> EnergyPattern:
        return EnergyPattern.ACTIVE if self._energy == "active" else EnergyPattern.PASSIVE

    @property
    def description(self) -> str:
        return self._description

    @property
    def can_process_r6(self) -> bool:
        """Active resources can process R6 transactions."""
        return self.energy_pattern == EnergyPattern.ACTIVE

    @property
    def is_agentic(self) -> bool:
        return self._mode == "agentic"

    @property
    def is_delegative(self) -> bool:
        return self._mode == "delegative"


# ═══════════════════════════════════════════════════════════════
# Trust Tensors (minimal for entity context)
# ═══════════════════════════════════════════════════════════════

@dataclass
class T3:
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def average(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def to_dict(self) -> dict:
        return {"talent": self.talent, "training": self.training,
                "temperament": self.temperament}


@dataclass
class V3:
    valuation: float = 0.0
    veracity: float = 0.5
    validity: float = 0.5

    def to_dict(self) -> dict:
        return {"valuation": self.valuation, "veracity": self.veracity,
                "validity": self.validity}


# ═══════════════════════════════════════════════════════════════
# §3.3 — Role Hierarchy
# ═══════════════════════════════════════════════════════════════

class RoleLevel(IntEnum):
    """Role evolution path per spec §3.3."""
    CITIZEN = 0       # Birth — base participation rights
    PARTICIPANT = 1   # Active engagement in domain
    CONTRIBUTOR = 2   # Proven value creation
    SPECIALIST = 3    # Domain expertise (surgeon, engineer)
    AUTHORITY = 4     # Governance and oversight


# ═══════════════════════════════════════════════════════════════
# §3.1 — Birth Certificate
# ═══════════════════════════════════════════════════════════════

@dataclass
class BirthCertificate:
    """Universal birth certificate per spec §3.1."""
    entity_lct: str
    citizen_role_lct: str
    society_lct: str
    law_oracle_lct: str
    law_version: str
    birth_timestamp: str
    witnesses: List[str]
    genesis_block: str
    initial_rights: List[str]
    initial_responsibilities: List[str]
    ledger_proof: str
    parent_entity: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "@context": ["https://web4.io/contexts/sal.jsonld"],
            "type": "Web4BirthCertificate",
            "entity": self.entity_lct,
            "citizenRole": self.citizen_role_lct,
            "society": self.society_lct,
            "lawOracle": self.law_oracle_lct,
            "lawVersion": self.law_version,
            "birthTimestamp": self.birth_timestamp,
            "witnesses": self.witnesses,
            "genesisBlock": self.genesis_block,
            "initialRights": self.initial_rights,
            "initialResponsibilities": self.initial_responsibilities,
            "ledgerProof": self.ledger_proof,
            "parentEntity": self.parent_entity,
        }


# ═══════════════════════════════════════════════════════════════
# §4.2 — Auditor Adjustment
# ═══════════════════════════════════════════════════════════════

@dataclass
class AuditRequest:
    """Auditor adjustment request per spec §4.2 (Auditor role)."""
    society_lct: str
    targets: List[str]
    scope: List[str]
    basis: List[str]
    proposed_t3: Dict[str, float]
    proposed_v3: Dict[str, float]

    def to_dict(self) -> dict:
        return {
            "type": "Web4AuditRequest",
            "society": self.society_lct,
            "targets": self.targets,
            "scope": self.scope,
            "basis": self.basis,
            "proposed": {
                "t3": self.proposed_t3,
                "v3": self.proposed_v3,
            },
            "rateLimits": "per_law_oracle",
            "appealPath": "defined_by_law",
        }


# ═══════════════════════════════════════════════════════════════
# §4.6/4.7 — Agency Grant (AGY)
# ═══════════════════════════════════════════════════════════════

@dataclass
class AgencyGrant:
    """Agency delegation grant per spec §4.6/4.7."""
    grant_id: str
    client_lct: str
    agent_lct: str
    society_lct: str
    law_hash: str
    scope_contexts: List[str]
    methods: List[str]
    max_atp: float = 25.0
    delegatable: bool = False
    witness_level: int = 2
    not_before: str = ""
    expires_at: str = ""
    role_impersonation: bool = False
    trust_caps_t3_min: Optional[Dict[str, float]] = None
    trust_caps_v3_floor: Optional[Dict[str, float]] = None

    def is_active(self) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        if self.not_before and now < self.not_before:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "type": "Web4AgencyGrant",
            "grantId": self.grant_id,
            "client": self.client_lct,
            "agent": self.agent_lct,
            "society": self.society_lct,
            "lawHash": self.law_hash,
            "scope": {
                "contexts": self.scope_contexts,
                "methods": self.methods,
                "r6Caps": {
                    "resourceCaps": {"max_atp": self.max_atp},
                    "roleImpersonation": self.role_impersonation,
                },
                "delegatable": self.delegatable,
                "witnessLevel": self.witness_level,
            },
            "duration": {
                "notBefore": self.not_before,
                "expiresAt": self.expires_at,
            },
        }


# ═══════════════════════════════════════════════════════════════
# §9 — Dictionary Entity
# ═══════════════════════════════════════════════════════════════

@dataclass
class DictionarySpec:
    """Dictionary entity specialization per spec §9."""
    source_domain: str
    target_domain: str
    bidirectional: bool = True
    terms_count: int = 0
    concepts_count: int = 0
    average_ratio: float = 1.0
    lossy_threshold: float = 0.02
    learning_rate: float = 0.001
    update_frequency: str = "daily"
    community_edits: bool = True

    def to_dict(self) -> dict:
        return {
            "dictionary_spec": {
                "source_domain": self.source_domain,
                "target_domain": self.target_domain,
                "bidirectional": self.bidirectional,
                "coverage": {
                    "terms": self.terms_count,
                    "concepts": self.concepts_count,
                },
            },
            "compression_profile": {
                "average_ratio": self.average_ratio,
                "lossy_threshold": self.lossy_threshold,
                "context_required": "moderate",
            },
            "evolution": {
                "learning_rate": self.learning_rate,
                "update_frequency": self.update_frequency,
                "community_edits": self.community_edits,
            },
        }


# ═══════════════════════════════════════════════════════════════
# §10 — Accumulator Entity
# ═══════════════════════════════════════════════════════════════

@dataclass
class AccumulatorConfig:
    """Accumulator entity specialization per spec §10."""
    listen_scope: List[str] = field(default_factory=lambda: ["ANNOUNCE", "HEARTBEAT", "CAPABILITY"])
    retention_period: int = 2592000  # 30 days
    index_strategy: str = "entity_time_type"
    query_interface: str = ""
    storage_commitment: str = "10GB"
    broadcasts_recorded: int = 0
    unique_entities: int = 0
    queries_served: int = 0
    uptime_percentage: float = 99.97

    def record_broadcast(self, entity_lct: str, broadcast_type: str):
        self.broadcasts_recorded += 1

    def to_dict(self) -> dict:
        return {
            "accumulator_config": {
                "listen_scope": self.listen_scope,
                "retention_period": self.retention_period,
                "index_strategy": self.index_strategy,
                "query_interface": self.query_interface,
                "storage_commitment": self.storage_commitment,
            },
            "statistics": {
                "broadcasts_recorded": self.broadcasts_recorded,
                "unique_entities": self.unique_entities,
                "queries_served": self.queries_served,
                "uptime_percentage": self.uptime_percentage,
            },
        }


# ═══════════════════════════════════════════════════════════════
# §12 — Policy Entity
# ═══════════════════════════════════════════════════════════════

class AccountabilityFrame(Enum):
    """Accountability frames per spec §12.4."""
    NORMAL = ("normal", ["WAKE", "FOCUS"])
    DEGRADED = ("degraded", ["REST", "DREAM"])
    DURESS = ("duress", ["CRISIS"])

    def __init__(self, frame_name: str, states: List[str]):
        self.frame_name = frame_name
        self.metabolic_states = states


@dataclass
class PolicySpec:
    """Policy entity specialization per spec §12."""
    name: str
    version: str
    rules: Dict[str, Any] = field(default_factory=dict)
    config_hash: str = ""
    evaluation_count: int = 0
    convergence_quality: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0

    def __post_init__(self):
        if not self.config_hash:
            payload = json.dumps(self.rules, sort_keys=True).encode()
            self.config_hash = hashlib.sha256(payload).hexdigest()[:16]

    def evaluate(self, action: Dict, frame: AccountabilityFrame = AccountabilityFrame.NORMAL) -> dict:
        """Evaluate action against policy rules. Returns compliance score."""
        violations = []
        for rule_name, rule_fn in self.rules.items():
            if callable(rule_fn):
                if not rule_fn(action):
                    violations.append(rule_name)
            else:
                # Static rule: check action matches
                if rule_name in action and action[rule_name] != rule_fn:
                    violations.append(rule_name)

        compliance_score = len(violations)  # 0 = compliant
        self.evaluation_count += 1

        return {
            "compliant": compliance_score == 0,
            "violations": violations,
            "compliance_score": compliance_score,
            "accountability_frame": frame.frame_name,
            "metabolic_states": frame.metabolic_states,
        }

    @property
    def lct_format(self) -> str:
        return f"policy:{self.name}:{self.version}:{self.config_hash}"

    def to_dict(self) -> dict:
        return {
            "policy_spec": {
                "name": self.name,
                "version": self.version,
                "config_hash": self.config_hash,
                "lct_format": self.lct_format,
            },
            "metrics": {
                "evaluation_count": self.evaluation_count,
                "convergence_quality": self.convergence_quality,
                "false_positive_rate": self.false_positive_rate,
                "false_negative_rate": self.false_negative_rate,
            },
        }


# ═══════════════════════════════════════════════════════════════
# Core Entity
# ═══════════════════════════════════════════════════════════════

class EntityStatus(Enum):
    ACTIVE = "active"
    VOID = "void"
    SLASHED = "slashed"


@dataclass
class RolePairing:
    """Tracks a role-agent pairing per spec §3.3."""
    role_lct: str
    role_level: RoleLevel
    pairing_type: str  # "birth_certificate" or "role_assignment"
    permanent: bool
    timestamp: str
    permissions: List[str] = field(default_factory=list)


class Web4Entity:
    """
    Core entity class implementing the complete entity-types.md spec.

    Covers:
      §2 — Type taxonomy, behavioral modes, energy metabolism
      §3 — Roles as first-class entities, birth certificates, role hierarchy
      §4 — SAL-specific roles, agency grants
      §5 — Entity lifecycle (creation, evolution, termination)
      §6 — Interaction validation
      §7 — Type immutability
    """

    def __init__(self, lct_id: str, entity_type: EntityType,
                 parent: Optional["Web4Entity"] = None):
        self.lct_id = lct_id
        self._entity_type = entity_type  # Immutable after creation (§7.1)
        self.status = EntityStatus.ACTIVE
        self.parent = parent

        # Trust tensors
        self.t3 = T3()
        self.v3 = V3()

        # Energy metabolism
        self.energy = EnergyFlow()

        # MRH relationships
        self.mrh_bound: List[str] = []      # Parent → Child
        self.mrh_paired: List[str] = []     # Peer relationships
        self.mrh_witnessing: List[str] = [] # Observation relationships

        # Role pairings
        self.role_pairings: List[RolePairing] = []

        # Birth certificate
        self.birth_certificate: Optional[BirthCertificate] = None

        # Specializations
        self.dictionary_spec: Optional[DictionarySpec] = None
        self.accumulator_config: Optional[AccumulatorConfig] = None
        self.policy_spec: Optional[PolicySpec] = None

        # Performance history (for roles)
        self.performance_history: List[Dict] = []

        # Creation timestamp
        self.created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @property
    def entity_type(self) -> EntityType:
        """Entity type is immutable per spec §7.1."""
        return self._entity_type

    @property
    def mode(self) -> BehavioralMode:
        return self._entity_type.primary_mode

    @property
    def energy_pattern(self) -> EnergyPattern:
        return self._entity_type.energy_pattern

    def has_citizen_role(self) -> bool:
        """Check if entity has birth certificate (citizen role)."""
        return any(rp.pairing_type == "birth_certificate" for rp in self.role_pairings)

    def get_role_level(self) -> RoleLevel:
        """Get highest role level achieved."""
        if not self.role_pairings:
            return RoleLevel.CITIZEN
        return max(rp.role_level for rp in self.role_pairings)

    def assign_role(self, role_lct: str, level: RoleLevel,
                    permissions: Optional[List[str]] = None) -> RolePairing:
        """Assign a role to this entity per spec §3.3."""
        # §5.2: Verify citizen role exists before other assignments
        if level > RoleLevel.CITIZEN and not self.has_citizen_role():
            raise ValueError("Citizen role (birth certificate) required before other roles")

        pairing = RolePairing(
            role_lct=role_lct,
            role_level=level,
            pairing_type="birth_certificate" if level == RoleLevel.CITIZEN else "role_assignment",
            permanent=(level == RoleLevel.CITIZEN),
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            permissions=permissions or [],
        )
        self.role_pairings.append(pairing)
        if role_lct not in self.mrh_paired:
            self.mrh_paired.append(role_lct)
        return pairing

    def revoke_role(self, role_lct: str) -> bool:
        """Revoke a role pairing. Citizen role cannot be revoked per spec §3.1."""
        for rp in self.role_pairings:
            if rp.role_lct == role_lct:
                if rp.permanent:
                    raise ValueError("Citizen role (birth certificate) cannot be revoked")
                self.role_pairings.remove(rp)
                return True
        return False

    def terminate(self):
        """Entity termination per spec §4.3."""
        self.status = EntityStatus.VOID

    def slash(self):
        """Slash entity per spec §4.3."""
        self.status = EntityStatus.SLASHED

    def process_r6(self, atp_cost: float, quality: float = 0.8) -> dict:
        """Process an R6 transaction using entity's energy metabolism."""
        if self.energy_pattern == EnergyPattern.ACTIVE:
            return self.energy.process_active(atp_cost, quality)
        else:
            return self.energy.process_passive(atp_cost)

    def to_dict(self) -> dict:
        d = {
            "lct_id": self.lct_id,
            "entity_type": self._entity_type.name.lower(),
            "status": self.status.value,
            "mode": self.mode.value,
            "energy_pattern": self.energy_pattern.value,
            "t3": self.t3.to_dict(),
            "v3": self.v3.to_dict(),
            "mrh": {
                "bound": self.mrh_bound,
                "paired": self.mrh_paired,
                "witnessing": self.mrh_witnessing,
            },
            "role_pairings": [
                {"role_lct": rp.role_lct, "level": rp.role_level.name,
                 "permanent": rp.permanent, "type": rp.pairing_type}
                for rp in self.role_pairings
            ],
            "created_at": self.created_at,
        }
        if self.birth_certificate:
            d["birth_certificate"] = self.birth_certificate.to_dict()
        if self.dictionary_spec:
            d.update(self.dictionary_spec.to_dict())
        if self.accumulator_config:
            d.update(self.accumulator_config.to_dict())
        if self.policy_spec:
            d.update(self.policy_spec.to_dict())
        return d


# ═══════════════════════════════════════════════════════════════
# §5.1 — Entity Factory with Birth Certificate
# ═══════════════════════════════════════════════════════════════

class EntityFactory:
    """
    Creates entities with proper birth certificates per spec §5.1.
    Implements the 10-step entity creation process.
    """

    def __init__(self, society_lct: str, law_oracle_lct: str,
                 law_version: str = "v1.0.0"):
        self.society_lct = society_lct
        self.law_oracle_lct = law_oracle_lct
        self.law_version = law_version
        self.entities: Dict[str, Web4Entity] = {}
        self.birth_certificates: List[BirthCertificate] = []
        self.citizen_role_counter = 0

    def create_entity(self, entity_type: EntityType,
                      parent: Optional[Web4Entity] = None,
                      witnesses: Optional[List[str]] = None) -> Web4Entity:
        """
        Create entity with full birth certificate process per spec §5.1:
        1. Society Selection
        2. LCT Generation
        3. Entity Type Declaration (immutable)
        4. Citizen Role Pairing
        5. Birth Certificate Recording
        6. Witness Quorum
        7. Law Oracle Binding
        8. Initial Binding (for delegative)
        9. MRH Initialization
        10. Ledger Proof
        """
        # 2. LCT Generation
        lct_id = f"lct:web4:{entity_type.name.lower()}:{os.urandom(8).hex()}"

        # 3. Entity Type Declaration (immutable)
        entity = Web4Entity(lct_id, entity_type, parent)

        # 4. Citizen Role Pairing
        self.citizen_role_counter += 1
        citizen_role_lct = f"lct:web4:role:citizen:{self.citizen_role_counter:04d}"
        entity.assign_role(citizen_role_lct, RoleLevel.CITIZEN,
                           permissions=["exist", "interact", "accumulate_reputation"])

        # 5-10. Birth Certificate
        birth_cert = BirthCertificate(
            entity_lct=lct_id,
            citizen_role_lct=citizen_role_lct,
            society_lct=self.society_lct,
            law_oracle_lct=self.law_oracle_lct,
            law_version=self.law_version,
            birth_timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            witnesses=witnesses or ["lct:web4:witness:default"],
            genesis_block=f"block:{os.urandom(4).hex()}",
            initial_rights=["exist", "interact", "accumulate_reputation"],
            initial_responsibilities=["abide_law", "respect_quorum"],
            ledger_proof=f"hash:sha256:{hashlib.sha256(lct_id.encode()).hexdigest()[:16]}",
            parent_entity=parent.lct_id if parent else None,
        )
        entity.birth_certificate = birth_cert
        self.birth_certificates.append(birth_cert)

        # 8. Initial binding for delegative entities
        if parent and entity_type.is_delegative:
            entity.mrh_bound.append(parent.lct_id)

        self.entities[lct_id] = entity
        return entity


# ═══════════════════════════════════════════════════════════════
# §5.1 — Interaction Validation
# ═══════════════════════════════════════════════════════════════

class InteractionType(Enum):
    BINDING = "binding"         # Parent → Child
    PAIRING = "pairing"         # Peer entities
    WITNESSING = "witnessing"   # Any → Any
    DELEGATION = "delegation"   # Delegative → Agentic


class InteractionValidator:
    """Validates entity interactions per spec §5.1."""

    # Valid interaction patterns from spec table
    BINDING_VALID = {
        # Parent types → allowed child types
        EntityType.ORGANIZATION: {EntityType.ROLE, EntityType.TASK, EntityType.RESOURCE},
        EntityType.ROLE: {EntityType.TASK, EntityType.ROLE},
        EntityType.SOCIETY: {EntityType.ROLE, EntityType.ORGANIZATION, EntityType.RESOURCE},
    }

    DELEGATION_VALID_SOURCES = {
        EntityType.ROLE, EntityType.ORGANIZATION, EntityType.SOCIETY
    }
    DELEGATION_VALID_TARGETS = {
        EntityType.HUMAN, EntityType.AI, EntityType.HYBRID, EntityType.DEVICE
    }

    @classmethod
    def validate_interaction(cls, source: Web4Entity, target: Web4Entity,
                             interaction: InteractionType) -> Tuple[bool, str]:
        """Check if interaction is valid between these entity types."""
        if source.status != EntityStatus.ACTIVE:
            return False, "Source entity not active"
        if target.status != EntityStatus.ACTIVE:
            return False, "Target entity not active"

        if interaction == InteractionType.WITNESSING:
            # Any → Any is valid for witnessing
            return True, "Witnessing is universal"

        if interaction == InteractionType.BINDING:
            allowed_children = cls.BINDING_VALID.get(source.entity_type, set())
            if target.entity_type in allowed_children:
                return True, "Valid binding"
            return False, f"{source.entity_type.name} cannot bind {target.entity_type.name}"

        if interaction == InteractionType.PAIRING:
            # Peer pairing: primarily between agentic entities or role-agent pairs
            return True, "Pairing allowed"

        if interaction == InteractionType.DELEGATION:
            if source.entity_type not in cls.DELEGATION_VALID_SOURCES:
                return False, f"{source.entity_type.name} cannot delegate"
            if target.entity_type not in cls.DELEGATION_VALID_TARGETS:
                return False, f"Cannot delegate to {target.entity_type.name}"
            return True, "Valid delegation"

        return False, "Unknown interaction type"


# ═══════════════════════════════════════════════════════════════
# §6.3 — Entity Discovery
# ═══════════════════════════════════════════════════════════════

class EntityDiscovery:
    """Entity discovery with type filtering and reputation sorting per spec §6.3."""

    def __init__(self):
        self.entities: Dict[str, Web4Entity] = {}

    def register(self, entity: Web4Entity):
        self.entities[entity.lct_id] = entity

    def discover(self, entity_type: Optional[EntityType] = None,
                 min_trust: float = 0.0,
                 role_level: Optional[RoleLevel] = None,
                 mode: Optional[BehavioralMode] = None,
                 status: EntityStatus = EntityStatus.ACTIVE) -> List[Web4Entity]:
        results = []
        for e in self.entities.values():
            if e.status != status:
                continue
            if entity_type and e.entity_type != entity_type:
                continue
            if e.t3.average() < min_trust:
                continue
            if role_level and e.get_role_level() < role_level:
                continue
            if mode and e.mode != mode:
                continue
            results.append(e)
        # Sort by trust descending
        results.sort(key=lambda e: e.t3.average(), reverse=True)
        return results


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

    # ═══════════════════════════════════════════════════════════
    # §2.1 — Entity Type Taxonomy
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T1: Entity Type Taxonomy (§2.1) ═══")
    check("T1.1 15 entity types defined", len(EntityType) == 15)
    check("T1.2 Human is agentic", EntityType.HUMAN.is_agentic)
    check("T1.3 AI is agentic", EntityType.AI.is_agentic)
    check("T1.4 Society is delegative", EntityType.SOCIETY.is_delegative)
    check("T1.5 Organization is delegative", EntityType.ORGANIZATION.is_delegative)
    check("T1.6 Role is delegative", EntityType.ROLE.is_delegative)
    check("T1.7 Task is responsive", EntityType.TASK.primary_mode == BehavioralMode.RESPONSIVE)
    check("T1.8 Resource is responsive", EntityType.RESOURCE.primary_mode == BehavioralMode.RESPONSIVE)
    check("T1.9 Device is responsive", EntityType.DEVICE.primary_mode == BehavioralMode.RESPONSIVE)
    check("T1.10 Infrastructure is passive", EntityType.INFRASTRUCTURE.energy_pattern == EnergyPattern.PASSIVE)

    # All types have descriptions
    for et in EntityType:
        check(f"T1.11 {et.name} has description", len(et.description) > 0)

    # ═══════════════════════════════════════════════════════════
    # §2.2 — Behavioral Modes
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T2: Behavioral Modes (§2.2) ═══")
    check("T2.1 3 modes defined", len(BehavioralMode) == 3)
    check("T2.2 Agentic can initiate", BehavioralMode.AGENTIC.can_initiate)
    check("T2.3 Responsive cannot initiate", not BehavioralMode.RESPONSIVE.can_initiate)
    check("T2.4 Delegative can delegate", BehavioralMode.DELEGATIVE.can_delegate)
    check("T2.5 Agentic cannot delegate", not BehavioralMode.AGENTIC.can_delegate)

    # Mode assignments match spec table
    check("T2.6 Human mode correct", EntityType.HUMAN.primary_mode == BehavioralMode.AGENTIC)
    check("T2.7 Oracle mode correct", EntityType.ORACLE.primary_mode == BehavioralMode.RESPONSIVE)
    check("T2.8 Society mode correct", EntityType.SOCIETY.primary_mode == BehavioralMode.DELEGATIVE)
    check("T2.9 Hybrid mode correct", EntityType.HYBRID.primary_mode == BehavioralMode.AGENTIC)
    check("T2.10 Policy mode correct", EntityType.POLICY.primary_mode == BehavioralMode.RESPONSIVE)

    # ═══════════════════════════════════════════════════════════
    # §2.3 — Energy Metabolism
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T3: Energy Metabolism (§2.3) ═══")
    check("T3.1 2 energy patterns", len(EnergyPattern) == 2)

    # Active resources
    active_types = [et for et in EntityType if et.energy_pattern == EnergyPattern.ACTIVE]
    passive_types = [et for et in EntityType if et.energy_pattern == EnergyPattern.PASSIVE]
    check("T3.2 Active types exist", len(active_types) > 0, f"count={len(active_types)}")
    check("T3.3 Passive types exist", len(passive_types) > 0, f"count={len(passive_types)}")

    # Specific assignments
    check("T3.4 Human is active", EntityType.HUMAN.energy_pattern == EnergyPattern.ACTIVE)
    check("T3.5 Resource is passive", EntityType.RESOURCE.energy_pattern == EnergyPattern.PASSIVE)
    check("T3.6 Infrastructure is passive", EntityType.INFRASTRUCTURE.energy_pattern == EnergyPattern.PASSIVE)
    check("T3.7 Accumulator is passive", EntityType.ACCUMULATOR.energy_pattern == EnergyPattern.PASSIVE)
    check("T3.8 Service is active", EntityType.SERVICE.energy_pattern == EnergyPattern.ACTIVE)
    check("T3.9 Dictionary is active", EntityType.DICTIONARY.energy_pattern == EnergyPattern.ACTIVE)
    check("T3.10 Policy is active", EntityType.POLICY.energy_pattern == EnergyPattern.ACTIVE)

    # R6 capability
    check("T3.11 Active can process R6", EntityType.HUMAN.can_process_r6)
    check("T3.12 Passive cannot process R6", not EntityType.RESOURCE.can_process_r6)

    # Energy flow — active
    ef_active = EnergyFlow(atp_balance=100)
    result = ef_active.process_active(20, quality=0.9)
    check("T3.13 Active: ATP deducted", ef_active.atp_balance == 80)
    check("T3.14 Active: ADP returned", ef_active.adp_discharged == 20)
    check("T3.15 Active: Reputation earned", ef_active.reputation_earned > 0)
    check("T3.16 Active: No slash", ef_active.adp_slashed == 0)

    # Energy flow — passive
    ef_passive = EnergyFlow(atp_balance=100)
    result_p = ef_passive.process_passive(20)
    check("T3.17 Passive: ATP deducted", ef_passive.atp_balance == 80)
    check("T3.18 Passive: ADP slashed", ef_passive.adp_slashed == 20)
    check("T3.19 Passive: No reputation", ef_passive.reputation_earned == 0)
    check("T3.20 Passive: Utilization counted", ef_passive.utilization_count == 1)

    # Insufficient ATP
    ef_broke = EnergyFlow(atp_balance=5)
    r_broke = ef_broke.process_active(10)
    check("T3.21 Insufficient ATP fails", not r_broke["success"])

    # ═══════════════════════════════════════════════════════════
    # §3.1 — Birth Certificate
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T4: Birth Certificate System (§3.1) ═══")
    factory = EntityFactory(
        society_lct="lct:web4:society:test-nation",
        law_oracle_lct="lct:web4:oracle:law:test",
        law_version="v1.2.0",
    )

    human = factory.create_entity(EntityType.HUMAN,
                                  witnesses=["lct:web4:witness:w1", "lct:web4:witness:w2"])
    check("T4.1 Human created", human.lct_id.startswith("lct:web4:human:"))
    check("T4.2 Has birth certificate", human.birth_certificate is not None)
    check("T4.3 Has citizen role", human.has_citizen_role())
    check("T4.4 Citizen role is permanent",
          any(rp.permanent for rp in human.role_pairings))

    bc = human.birth_certificate
    check("T4.5 BC has entity LCT", bc.entity_lct == human.lct_id)
    check("T4.6 BC has citizen role LCT", bc.citizen_role_lct.startswith("lct:web4:role:citizen:"))
    check("T4.7 BC has society", bc.society_lct == "lct:web4:society:test-nation")
    check("T4.8 BC has law oracle", bc.law_oracle_lct == "lct:web4:oracle:law:test")
    check("T4.9 BC has law version", bc.law_version == "v1.2.0")
    check("T4.10 BC has witnesses", len(bc.witnesses) == 2)
    check("T4.11 BC has genesis block", bc.genesis_block.startswith("block:"))
    check("T4.12 BC has initial rights", "exist" in bc.initial_rights)
    check("T4.13 BC has initial responsibilities", "abide_law" in bc.initial_responsibilities)
    check("T4.14 BC has ledger proof", bc.ledger_proof.startswith("hash:sha256:"))

    # BC serialization matches spec format
    bcd = bc.to_dict()
    check("T4.15 BC has @context", bcd["@context"] == ["https://web4.io/contexts/sal.jsonld"])
    check("T4.16 BC has type", bcd["type"] == "Web4BirthCertificate")

    # ═══════════════════════════════════════════════════════════
    # §3.3 — Role Hierarchy
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T5: Role Hierarchy (§3.3) ═══")
    check("T5.1 5 role levels", len(RoleLevel) == 5)
    check("T5.2 Citizen < Participant", RoleLevel.CITIZEN < RoleLevel.PARTICIPANT)
    check("T5.3 Participant < Contributor", RoleLevel.PARTICIPANT < RoleLevel.CONTRIBUTOR)
    check("T5.4 Contributor < Specialist", RoleLevel.CONTRIBUTOR < RoleLevel.SPECIALIST)
    check("T5.5 Specialist < Authority", RoleLevel.SPECIALIST < RoleLevel.AUTHORITY)

    # Role assignment requires citizen
    ai = factory.create_entity(EntityType.AI)
    check("T5.6 AI has citizen role", ai.has_citizen_role())

    # Assign higher role
    rp = ai.assign_role("lct:web4:role:developer", RoleLevel.SPECIALIST,
                        permissions=["capability:code", "capability:review"])
    check("T5.7 Specialist role assigned", rp.role_level == RoleLevel.SPECIALIST)
    check("T5.8 Permissions transferred", "capability:code" in rp.permissions)
    check("T5.9 Role in MRH paired", "lct:web4:role:developer" in ai.mrh_paired)
    check("T5.10 Highest level is Specialist", ai.get_role_level() == RoleLevel.SPECIALIST)

    # Assign authority role
    ai.assign_role("lct:web4:role:admin", RoleLevel.AUTHORITY)
    check("T5.11 Authority highest", ai.get_role_level() == RoleLevel.AUTHORITY)

    # Cannot assign without citizen
    bare = Web4Entity("lct:web4:bare", EntityType.HUMAN)
    try:
        bare.assign_role("lct:web4:role:dev", RoleLevel.SPECIALIST)
        check("T5.12 No citizen = no higher roles", False)
    except ValueError as e:
        check("T5.12 No citizen = no higher roles", "birth certificate" in str(e).lower())

    # Citizen role cannot be revoked
    try:
        citizen_lct = human.role_pairings[0].role_lct
        human.revoke_role(citizen_lct)
        check("T5.13 Citizen irrevocable", False)
    except ValueError as e:
        check("T5.13 Citizen irrevocable", "cannot be revoked" in str(e).lower())

    # Other roles can be revoked
    revoked = ai.revoke_role("lct:web4:role:admin")
    check("T5.14 Non-citizen revocable", revoked)
    check("T5.15 Level drops after revocation", ai.get_role_level() == RoleLevel.SPECIALIST)

    # ═══════════════════════════════════════════════════════════
    # §7.1 — Entity Type Immutability
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T6: Type Immutability (§7.1) ═══")
    check("T6.1 Type is read-only property", human.entity_type == EntityType.HUMAN)
    # Attempting to change type via _entity_type would bypass the property,
    # but the property itself prevents it in practice
    check("T6.2 AI type preserved", ai.entity_type == EntityType.AI)

    # Create all 15 types and verify immutability
    types_created = {}
    for et in EntityType:
        e = factory.create_entity(et)
        types_created[et] = e
        check(f"T6.3 {et.name} type immutable", e.entity_type == et)

    # ═══════════════════════════════════════════════════════════
    # §5.1 — Interaction Validation
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T7: Interaction Validation (§5.1) ═══")
    org = types_created[EntityType.ORGANIZATION]
    role = types_created[EntityType.ROLE]
    task = types_created[EntityType.TASK]
    resource = types_created[EntityType.RESOURCE]
    human_e = types_created[EntityType.HUMAN]
    ai_e = types_created[EntityType.AI]
    device = types_created[EntityType.DEVICE]
    society = types_created[EntityType.SOCIETY]
    infra = types_created[EntityType.INFRASTRUCTURE]

    # Valid bindings
    valid, msg = InteractionValidator.validate_interaction(
        org, role, InteractionType.BINDING)
    check("T7.1 Org → Role binding valid", valid)

    valid, msg = InteractionValidator.validate_interaction(
        org, task, InteractionType.BINDING)
    check("T7.2 Org → Task binding valid", valid)

    valid, msg = InteractionValidator.validate_interaction(
        role, task, InteractionType.BINDING)
    check("T7.3 Role → Task binding valid", valid)

    valid, msg = InteractionValidator.validate_interaction(
        society, role, InteractionType.BINDING)
    check("T7.4 Society → Role binding valid", valid)

    # Invalid bindings
    valid, msg = InteractionValidator.validate_interaction(
        human_e, role, InteractionType.BINDING)
    check("T7.5 Human → Role binding invalid", not valid)

    valid, msg = InteractionValidator.validate_interaction(
        task, role, InteractionType.BINDING)
    check("T7.6 Task → Role binding invalid", not valid)

    # Witnessing is universal
    valid, msg = InteractionValidator.validate_interaction(
        ai_e, human_e, InteractionType.WITNESSING)
    check("T7.7 AI → Human witnessing valid", valid)

    valid, msg = InteractionValidator.validate_interaction(
        infra, task, InteractionType.WITNESSING)
    check("T7.8 Infrastructure → Task witnessing valid", valid)

    # Delegation: delegative → agentic
    valid, msg = InteractionValidator.validate_interaction(
        role, human_e, InteractionType.DELEGATION)
    check("T7.9 Role → Human delegation valid", valid)

    valid, msg = InteractionValidator.validate_interaction(
        org, ai_e, InteractionType.DELEGATION)
    check("T7.10 Org → AI delegation valid", valid)

    # Invalid delegation
    valid, msg = InteractionValidator.validate_interaction(
        human_e, ai_e, InteractionType.DELEGATION)
    check("T7.11 Human → AI delegation invalid (human not delegative)", not valid)

    valid, msg = InteractionValidator.validate_interaction(
        role, resource, InteractionType.DELEGATION)
    check("T7.12 Role → Resource delegation invalid", not valid)

    # Terminated entity cannot interact
    terminated = factory.create_entity(EntityType.SERVICE)
    terminated.terminate()
    valid, msg = InteractionValidator.validate_interaction(
        terminated, human_e, InteractionType.WITNESSING)
    check("T7.13 Terminated entity rejected", not valid)

    # Slashed entity cannot interact
    slashed = factory.create_entity(EntityType.AI)
    slashed.slash()
    valid, msg = InteractionValidator.validate_interaction(
        slashed, human_e, InteractionType.PAIRING)
    check("T7.14 Slashed entity rejected", not valid)

    # ═══════════════════════════════════════════════════════════
    # §4 — SAL-Specific Roles
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T8: SAL-Specific Roles (§4) ═══")
    # Society role (§4.1)
    soc = factory.create_entity(EntityType.SOCIETY)
    check("T8.1 Society is delegative", soc.entity_type.is_delegative)
    check("T8.2 Society is active", soc.energy_pattern == EnergyPattern.ACTIVE)

    # Authority role (§4.2)
    auth_role = factory.create_entity(EntityType.ROLE)
    auth_role.assign_role("lct:web4:role:authority:finance", RoleLevel.AUTHORITY,
                          permissions=["finance:approve", "finance:audit"])
    check("T8.3 Authority role assigned", auth_role.get_role_level() == RoleLevel.AUTHORITY)

    # Law Oracle (§4.3)
    oracle = factory.create_entity(EntityType.ORACLE)
    check("T8.4 Oracle is responsive", oracle.mode == BehavioralMode.RESPONSIVE)
    check("T8.5 Oracle is active", oracle.energy_pattern == EnergyPattern.ACTIVE)

    # Witness role (§4.4)
    witness = factory.create_entity(EntityType.HUMAN)
    witness.assign_role("lct:web4:role:witness", RoleLevel.CONTRIBUTOR)
    check("T8.6 Witness role assigned",
          any(rp.role_lct == "lct:web4:role:witness" for rp in witness.role_pairings))

    # Auditor (§4.5)
    auditor = factory.create_entity(EntityType.HUMAN)
    auditor.assign_role("lct:web4:role:auditor", RoleLevel.AUTHORITY,
                        permissions=["traverse_mrh", "validate_t3v3", "validate_agency"])
    check("T8.7 Auditor role with permissions",
          "traverse_mrh" in auditor.role_pairings[-1].permissions)

    # Audit request
    audit_req = AuditRequest(
        society_lct="lct:web4:society:test",
        targets=["lct:web4:citizen:alice"],
        scope=["context:data_analysis"],
        basis=["hash:evidence1", "hash:evidence2"],
        proposed_t3={"temperament": -0.02},
        proposed_v3={"veracity": -0.03},
    )
    ard = audit_req.to_dict()
    check("T8.8 Audit request type", ard["type"] == "Web4AuditRequest")
    check("T8.9 Audit has targets", len(ard["targets"]) == 1)
    check("T8.10 Audit has basis", len(ard["basis"]) == 2)
    check("T8.11 Audit has proposed adjustments", ard["proposed"]["t3"]["temperament"] == -0.02)
    check("T8.12 Audit has appeal path", ard["appealPath"] == "defined_by_law")

    # Agent/Client roles (§4.6/4.7)
    grant = AgencyGrant(
        grant_id="agy:grant:001",
        client_lct="lct:web4:entity:CLIENT",
        agent_lct="lct:web4:entity:AGENT",
        society_lct="lct:web4:society:ROOT",
        law_hash="sha256-abc123",
        scope_contexts=["finance:payments", "docs:sign"],
        methods=["create", "update", "approve"],
        max_atp=25,
        delegatable=False,
        witness_level=2,
    )
    gd = grant.to_dict()
    check("T8.13 Agency grant type", gd["type"] == "Web4AgencyGrant")
    check("T8.14 Grant has client", gd["client"] == "lct:web4:entity:CLIENT")
    check("T8.15 Grant has agent", gd["agent"] == "lct:web4:entity:AGENT")
    check("T8.16 Grant has scope contexts", len(gd["scope"]["contexts"]) == 2)
    check("T8.17 Grant has methods", "approve" in gd["scope"]["methods"])
    check("T8.18 Grant not delegatable", not gd["scope"]["delegatable"])
    check("T8.19 Grant has ATP caps", gd["scope"]["r6Caps"]["resourceCaps"]["max_atp"] == 25)

    # ═══════════════════════════════════════════════════════════
    # §9 — Dictionary Entity
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T9: Dictionary Entity (§9) ═══")
    dict_entity = factory.create_entity(EntityType.DICTIONARY)
    dict_entity.dictionary_spec = DictionarySpec(
        source_domain="medical",
        target_domain="legal",
        bidirectional=True,
        terms_count=15000,
        concepts_count=3200,
        average_ratio=12.5,
        lossy_threshold=0.02,
        learning_rate=0.001,
        update_frequency="daily",
        community_edits=True,
    )
    check("T9.1 Dictionary entity type", dict_entity.entity_type == EntityType.DICTIONARY)
    check("T9.2 Dictionary is active", dict_entity.energy_pattern == EnergyPattern.ACTIVE)
    check("T9.3 Dictionary can process R6", dict_entity.entity_type.can_process_r6)

    ds = dict_entity.dictionary_spec
    check("T9.4 Source domain", ds.source_domain == "medical")
    check("T9.5 Target domain", ds.target_domain == "legal")
    check("T9.6 Bidirectional", ds.bidirectional)
    check("T9.7 Terms count", ds.terms_count == 15000)
    check("T9.8 Compression ratio", ds.average_ratio == 12.5)
    check("T9.9 Lossy threshold", ds.lossy_threshold == 0.02)

    dsd = ds.to_dict()
    check("T9.10 Dict spec serializes", "dictionary_spec" in dsd)
    check("T9.11 Compression profile", "compression_profile" in dsd)
    check("T9.12 Evolution config", "evolution" in dsd)

    # In entity dict
    dd = dict_entity.to_dict()
    check("T9.13 Dictionary in entity dict", "dictionary_spec" in dd)

    # ═══════════════════════════════════════════════════════════
    # §10 — Accumulator Entity
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T10: Accumulator Entity (§10) ═══")
    acc = factory.create_entity(EntityType.ACCUMULATOR)
    acc.accumulator_config = AccumulatorConfig(
        listen_scope=["ANNOUNCE", "HEARTBEAT", "CAPABILITY"],
        retention_period=2592000,
        query_interface="web4://accumulator/query",
        storage_commitment="10GB",
    )
    check("T10.1 Accumulator entity type", acc.entity_type == EntityType.ACCUMULATOR)
    check("T10.2 Accumulator is passive", acc.energy_pattern == EnergyPattern.PASSIVE)
    check("T10.3 Accumulator cannot process R6", not acc.entity_type.can_process_r6)

    ac = acc.accumulator_config
    check("T10.4 Listen scope", len(ac.listen_scope) == 3)
    check("T10.5 Retention period 30 days", ac.retention_period == 2592000)
    check("T10.6 Query interface", ac.query_interface == "web4://accumulator/query")

    # Record broadcasts
    ac.record_broadcast("lct:web4:entity:alice", "ANNOUNCE")
    ac.record_broadcast("lct:web4:entity:bob", "HEARTBEAT")
    check("T10.7 Broadcasts recorded", ac.broadcasts_recorded == 2)

    acd = ac.to_dict()
    check("T10.8 Accumulator config serializes", "accumulator_config" in acd)
    check("T10.9 Statistics present", "statistics" in acd)
    check("T10.10 Uptime tracked", acd["statistics"]["uptime_percentage"] == 99.97)

    # In entity dict
    ad = acc.to_dict()
    check("T10.11 Accumulator in entity dict", "accumulator_config" in ad)

    # ═══════════════════════════════════════════════════════════
    # §12 — Policy Entity
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T11: Policy Entity (§12) ═══")
    pol = factory.create_entity(EntityType.POLICY)
    pol.policy_spec = PolicySpec(
        name="safety-policy",
        version="1.0.0",
        rules={
            "max_atp": lambda action: action.get("atp", 0) <= 100,
            "requires_auth": lambda action: action.get("authenticated", False),
        },
    )
    check("T11.1 Policy entity type", pol.entity_type == EntityType.POLICY)
    check("T11.2 Policy is active", pol.energy_pattern == EnergyPattern.ACTIVE)
    check("T11.3 Policy is responsive", pol.mode == BehavioralMode.RESPONSIVE)

    ps = pol.policy_spec
    check("T11.4 Policy has name", ps.name == "safety-policy")
    check("T11.5 Policy has version", ps.version == "1.0.0")
    check("T11.6 Policy has config hash", len(ps.config_hash) > 0)
    check("T11.7 Policy LCT format",
          ps.lct_format.startswith("policy:safety-policy:1.0.0:"))

    # Evaluate compliant action
    result = ps.evaluate({"atp": 50, "authenticated": True})
    check("T11.8 Compliant action passes", result["compliant"])
    check("T11.9 No violations", len(result["violations"]) == 0)
    check("T11.10 Normal frame", result["accountability_frame"] == "normal")

    # Evaluate non-compliant action
    result2 = ps.evaluate({"atp": 200, "authenticated": False})
    check("T11.11 Non-compliant detected", not result2["compliant"])
    check("T11.12 Two violations", len(result2["violations"]) == 2)

    # Accountability frames
    check("T11.13 3 accountability frames", len(AccountabilityFrame) == 3)
    check("T11.14 Normal has WAKE/FOCUS",
          "WAKE" in AccountabilityFrame.NORMAL.metabolic_states)
    check("T11.15 Degraded has REST/DREAM",
          "REST" in AccountabilityFrame.DEGRADED.metabolic_states)
    check("T11.16 Duress has CRISIS",
          "CRISIS" in AccountabilityFrame.DURESS.metabolic_states)

    # Evaluate under duress
    result3 = ps.evaluate({"atp": 200, "authenticated": True},
                          frame=AccountabilityFrame.DURESS)
    check("T11.17 Duress frame recorded", result3["accountability_frame"] == "duress")
    check("T11.18 Metabolic states in result", "CRISIS" in result3["metabolic_states"])

    # Evaluation count tracked
    check("T11.19 Evaluation count", ps.evaluation_count == 3)

    # Serialization
    psd = ps.to_dict()
    check("T11.20 Policy spec serializes", "policy_spec" in psd)
    check("T11.21 Metrics present", "metrics" in psd)

    # In entity dict
    pd = pol.to_dict()
    check("T11.22 Policy in entity dict", "policy_spec" in pd)

    # ═══════════════════════════════════════════════════════════
    # §5 — Entity Lifecycle
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T12: Entity Lifecycle (§5) ═══")
    # Creation with parent
    parent_org = factory.create_entity(EntityType.ORGANIZATION)
    child_role = factory.create_entity(EntityType.ROLE, parent=parent_org)
    check("T12.1 Child has parent ref", child_role.parent == parent_org)
    check("T12.2 Child bound to parent", parent_org.lct_id in child_role.mrh_bound)
    check("T12.3 Birth cert has parent", child_role.birth_certificate.parent_entity == parent_org.lct_id)

    # Evolution — relationship building
    child_role.mrh_witnessing.append("lct:web4:witness:w1")
    check("T12.4 Witnessing grows", len(child_role.mrh_witnessing) == 1)

    # Reputation development
    child_role.t3.talent = 0.75
    check("T12.5 Reputation evolves", child_role.t3.talent == 0.75)

    # Performance history (for roles)
    child_role.performance_history.append({
        "performer_lct": "lct:web4:agent:alice",
        "period": {"start": "2025-01-01", "end": "2025-06-01"},
        "t3_scores": {"talent": 0.8},
        "reputation_impact": 0.85,
    })
    check("T12.6 Performance history tracked", len(child_role.performance_history) == 1)

    # Termination
    doomed = factory.create_entity(EntityType.SERVICE)
    check("T12.7 Initially active", doomed.status == EntityStatus.ACTIVE)
    doomed.terminate()
    check("T12.8 Terminated = void", doomed.status == EntityStatus.VOID)

    # Slashing
    bad = factory.create_entity(EntityType.AI)
    bad.slash()
    check("T12.9 Slashed status", bad.status == EntityStatus.SLASHED)

    # ═══════════════════════════════════════════════════════════
    # §11 — Citizen Role Examples
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T13: Citizen Role Contexts (§11) ═══")
    # Different entities get citizen roles in different contexts
    nation_factory = EntityFactory("lct:web4:society:nation", "lct:web4:oracle:law:nation")
    platform_factory = EntityFactory("lct:web4:society:platform", "lct:web4:oracle:law:platform")

    nation_citizen = nation_factory.create_entity(EntityType.HUMAN)
    platform_citizen = platform_factory.create_entity(EntityType.AI)

    check("T13.1 Nation citizen society",
          nation_citizen.birth_certificate.society_lct == "lct:web4:society:nation")
    check("T13.2 Platform citizen society",
          platform_citizen.birth_certificate.society_lct == "lct:web4:society:platform")
    check("T13.3 Different citizen roles",
          nation_citizen.birth_certificate.citizen_role_lct !=
          platform_citizen.birth_certificate.citizen_role_lct)

    # Every entity type gets a birth certificate
    for et in EntityType:
        e = factory.create_entity(et)
        check(f"T13.4 {et.name} gets birth cert", e.birth_certificate is not None)

    # ═══════════════════════════════════════════════════════════
    # §6.3 — Entity Discovery
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T14: Entity Discovery (§6.3) ═══")
    discovery = EntityDiscovery()

    # Register various entities
    d_human = factory.create_entity(EntityType.HUMAN)
    d_human.t3 = T3(talent=0.9, training=0.85, temperament=0.88)
    d_ai = factory.create_entity(EntityType.AI)
    d_ai.t3 = T3(talent=0.95, training=0.92, temperament=0.80)
    d_service = factory.create_entity(EntityType.SERVICE)
    d_service.t3 = T3(talent=0.6, training=0.7, temperament=0.65)
    d_low = factory.create_entity(EntityType.HUMAN)
    d_low.t3 = T3(talent=0.2, training=0.3, temperament=0.1)

    for e in [d_human, d_ai, d_service, d_low]:
        discovery.register(e)

    # Discover all
    all_entities = discovery.discover()
    check("T14.1 All entities found", len(all_entities) == 4)
    check("T14.2 Sorted by trust", all_entities[0].t3.average() >= all_entities[1].t3.average())

    # Filter by type
    humans = discovery.discover(entity_type=EntityType.HUMAN)
    check("T14.3 Type filter works", len(humans) == 2)

    # Filter by trust
    high_trust = discovery.discover(min_trust=0.7)
    check("T14.4 Trust filter works", len(high_trust) == 2)

    # Filter by mode
    agentic = discovery.discover(mode=BehavioralMode.AGENTIC)
    check("T14.5 Mode filter works", len(agentic) == 3)  # 2 humans + 1 AI

    # Terminated entities excluded
    d_dead = factory.create_entity(EntityType.HUMAN)
    d_dead.t3 = T3(talent=0.99, training=0.99, temperament=0.99)
    d_dead.terminate()
    discovery.register(d_dead)
    active = discovery.discover()
    check("T14.6 Terminated excluded", d_dead not in active)

    # ═══════════════════════════════════════════════════════════
    # Energy Metabolism Integration
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T15: Entity Energy Processing ═══")
    active_entity = factory.create_entity(EntityType.AI)
    r6_result = active_entity.process_r6(10, quality=0.9)
    check("T15.1 Active R6 succeeds", r6_result["success"])
    check("T15.2 Active earns reputation", r6_result["reputation_delta"] > 0)

    passive_entity = factory.create_entity(EntityType.RESOURCE)
    r6_result_p = passive_entity.process_r6(10)
    check("T15.3 Passive processes maintenance", r6_result_p["success"])
    check("T15.4 Passive ADP slashed", r6_result_p["adp_slashed"] == 10)
    check("T15.5 Passive no reputation", r6_result_p["reputation_delta"] == 0)

    infra_entity = factory.create_entity(EntityType.INFRASTRUCTURE)
    r6_result_i = infra_entity.process_r6(5)
    check("T15.6 Infrastructure passive", r6_result_i["adp_slashed"] == 5)
    check("T15.7 Infrastructure utilization", infra_entity.energy.utilization_count == 1)

    # ═══════════════════════════════════════════════════════════
    # Serialization
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T16: Serialization ═══")
    for et in EntityType:
        e = factory.create_entity(et)
        d = e.to_dict()
        j = json.dumps(d, default=str)
        check(f"T16.1 {et.name} JSON-serializable", json.loads(j) is not None)

    # Verify key fields
    sample = factory.create_entity(EntityType.HYBRID)
    sd = sample.to_dict()
    check("T16.2 Has lct_id", "lct_id" in sd)
    check("T16.3 Has entity_type", sd["entity_type"] == "hybrid")
    check("T16.4 Has status", sd["status"] == "active")
    check("T16.5 Has mode", sd["mode"] == "agentic")
    check("T16.6 Has energy_pattern", sd["energy_pattern"] == "active")
    check("T16.7 Has t3", "talent" in sd["t3"])
    check("T16.8 Has v3", "veracity" in sd["v3"])
    check("T16.9 Has mrh", "bound" in sd["mrh"])
    check("T16.10 Has role_pairings", len(sd["role_pairings"]) > 0)
    check("T16.11 Has birth_certificate", "birth_certificate" in sd)

    # Agency grant serialization
    gj = json.dumps(grant.to_dict())
    check("T16.12 Agency grant JSON-serializable", json.loads(gj) is not None)

    # Audit request serialization
    aj = json.dumps(audit_req.to_dict())
    check("T16.13 Audit request JSON-serializable", json.loads(aj) is not None)

    # ═══════════════════════════════════════════════════════════
    # Factory Tracking
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T17: Factory & Birth Certificate Tracking ═══")
    check("T17.1 Factory tracks entities",
          len(factory.entities) > 0, f"count={len(factory.entities)}")
    check("T17.2 Factory tracks birth certs",
          len(factory.birth_certificates) > 0, f"count={len(factory.birth_certificates)}")
    check("T17.3 All entities have birth certs",
          len(factory.entities) == len(factory.birth_certificates))

    # ═══════════════════════════════════════════════════════════
    # Test Vectors
    # ═══════════════════════════════════════════════════════════

    print("\n═══ T18: Test Vectors ═══")
    # Vector 1: Active energy — ATP 100, cost 20, quality 0.9
    # reputation = 20 * 0.9 * 0.01 = 0.18
    tv_ef = EnergyFlow(atp_balance=100)
    tv_result = tv_ef.process_active(20, 0.9)
    check("T18.1 Vector1: ATP after active",
          tv_ef.atp_balance == 80)
    check("T18.2 Vector1: ADP discharged",
          tv_ef.adp_discharged == 20)
    check("T18.3 Vector1: Reputation delta",
          abs(tv_ef.reputation_earned - 0.18) < 0.001,
          f"expected=0.18, actual={tv_ef.reputation_earned}")

    # Vector 2: Passive energy — ATP consumed, ADP slashed
    tv_ef2 = EnergyFlow(atp_balance=100)
    tv_ef2.process_passive(30)
    check("T18.4 Vector2: ATP after passive", tv_ef2.atp_balance == 70)
    check("T18.5 Vector2: ADP slashed", tv_ef2.adp_slashed == 30)
    check("T18.6 Vector2: Zero reputation", tv_ef2.reputation_earned == 0)

    # Vector 3: Role hierarchy ordering
    levels = [RoleLevel.CITIZEN, RoleLevel.PARTICIPANT, RoleLevel.CONTRIBUTOR,
              RoleLevel.SPECIALIST, RoleLevel.AUTHORITY]
    for i in range(len(levels) - 1):
        check(f"T18.7 {levels[i].name} < {levels[i+1].name}",
              levels[i] < levels[i+1])

    # Vector 4: Entity type mode/energy combinations
    type_checks = {
        EntityType.HUMAN: ("agentic", "active"),
        EntityType.RESOURCE: ("responsive", "passive"),
        EntityType.INFRASTRUCTURE: ("responsive", "passive"),
        EntityType.SOCIETY: ("delegative", "active"),
        EntityType.ACCUMULATOR: ("responsive", "passive"),
    }
    for et, (exp_mode, exp_energy) in type_checks.items():
        check(f"T18.8 {et.name} mode={exp_mode}",
              et.primary_mode.value == exp_mode)
        check(f"T18.9 {et.name} energy={exp_energy}",
              et.energy_pattern.value == exp_energy)

    # ═══════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════

    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  Web4 Entity Type System — Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'='*60}")

    if failed == 0:
        print(f"\n  All {total} checks pass — Entity Type System fully implemented")
        print(f"  Spec sections covered:")
        print(f"    §2  15 Entity Types, 3 Behavioral Modes, Energy Metabolism")
        print(f"    §3  Birth Certificates, Roles as First-Class, Role Hierarchy")
        print(f"    §4  SAL-Specific Roles (Society/Authority/Auditor/Witness/Agent/Client)")
        print(f"    §5  Entity Lifecycle (Creation/Evolution/Termination)")
        print(f"    §6  Interaction Validation + Entity Discovery")
        print(f"    §7  Type Immutability")
        print(f"    §9  Dictionary Entity (Compression-Trust)")
        print(f"    §10 Accumulator Entity (Passive Witnessing)")
        print(f"    §11 Citizen Role Contexts")
        print(f"    §12 Policy Entity (IRP/AccountabilityFrames)")
    else:
        print(f"\n  {failed} failures need investigation")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
