"""
Web4 Society Roles — the role taxonomy per society-roles.md.

Every Web4 society MUST fill 7 base-mandatory roles:
Sovereign, LawOracle, PolicyEntity, Treasurer, Administrator, Archivist, Citizen.

A role:
- Has its own LCT (authority binds to role, not filling entity)
- Can be filled by a single entity, a sub-society, or a federation
- Carries its own T3/V3 trust metrics (performance of the role)
- Can be rotated without breaking accountability chains

The role taxonomy has three tiers:
- **Base-mandatory** (7): Must exist in every society
- **Context-mandatory**: Required when certain conditions hold
  (e.g., Witness is mandatory when outward roles exist)
- **Optional**: Societies may define additional roles

Reference: web4-standard/core-spec/society-roles.md
Cross-language parity: web4-core/src/role.rs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from web4.trust import T3, V3

__all__ = [
    # Classes
    "SocietyRole",
    "RoleAssignment",
    # Functions
    "bootstrap_society_roles",
    # Constants
    "BASE_MANDATORY_ROLES",
]


class SocietyRole(str, Enum):
    """Society roles per society-roles.md §2-§4.

    The 7 base-mandatory roles that every Web4 society must fill,
    plus context-mandatory and optional roles.

    Uses str mixin for JSON-friendly serialization (value is the string key).
    """

    # ── Base-mandatory (7) ──────────────────────────────────────

    SOVEREIGN = "sovereign"
    """Final authority for charter amendment, identity recovery,
    and extraordinary inter-society decisions."""

    LAW_ORACLE = "law_oracle"
    """Publishes machine-readable laws, signs interpretations,
    answers compliance queries, maps laws to R6/R7 action grammar.
    NOT a decision-maker — an oracle that the PolicyEntity consults."""

    POLICY_ENTITY = "policy_entity"
    """Takes R6/R7 action requests, evaluates against Law Oracle's laws,
    returns approve/deny/escalate with reasoning. The enforcement arm."""

    TREASURER = "treasurer"
    """Operates Treasury: mints ATP, allocates per law, accounts for
    ATP/ADP movements. Conservation invariant: sum(ATP) + sum(ADP) = const."""

    ADMINISTRATOR = "administrator"
    """Operational execution: citizen lifecycle management, R6/R7 dispatch
    routing, infrastructure liveness, day-to-day society operations."""

    ARCHIVIST = "archivist"
    """Maintains ledger writes, cryptographic chain integrity, retention
    policy enforcement, historical queries. The society's memory."""

    CITIZEN = "citizen"
    """Base membership role. Every entity holds Citizen first; additional
    roles layer on top. Citizen is the genesis role — immutable once granted."""

    # ── Context-mandatory ───────────────────────────────────────

    WITNESS = "witness"
    """Independent attestation of other roles' actions. Mandatory when
    outward-facing roles exist (inter-society interactions)."""

    AUDITOR = "auditor"
    """T3/V3 validation and trust auditing. Mandatory when the society
    issues trust attestations consumed by other societies."""

    @property
    def is_base_mandatory(self) -> bool:
        """Returns True if this is one of the 7 base-mandatory roles."""
        return self in _BASE_MANDATORY_SET

    @property
    def description(self) -> str:
        """Human-readable description of the role's responsibility."""
        return _ROLE_DESCRIPTIONS[self]


# Frozen set for O(1) lookup
_BASE_MANDATORY_SET = frozenset(
    {
        SocietyRole.SOVEREIGN,
        SocietyRole.LAW_ORACLE,
        SocietyRole.POLICY_ENTITY,
        SocietyRole.TREASURER,
        SocietyRole.ADMINISTRATOR,
        SocietyRole.ARCHIVIST,
        SocietyRole.CITIZEN,
    }
)

#: Ordered list of the 7 base-mandatory roles.
BASE_MANDATORY_ROLES: List[SocietyRole] = [
    SocietyRole.SOVEREIGN,
    SocietyRole.LAW_ORACLE,
    SocietyRole.POLICY_ENTITY,
    SocietyRole.TREASURER,
    SocietyRole.ADMINISTRATOR,
    SocietyRole.ARCHIVIST,
    SocietyRole.CITIZEN,
]

_ROLE_DESCRIPTIONS: Dict[SocietyRole, str] = {
    SocietyRole.SOVEREIGN: "Final authority for charter amendment and identity recovery",
    SocietyRole.LAW_ORACLE: "Publishes and interprets machine-readable laws",
    SocietyRole.POLICY_ENTITY: "Evaluates action requests against law, returns signed decisions",
    SocietyRole.TREASURER: "Operates treasury, mints ATP, enforces conservation",
    SocietyRole.ADMINISTRATOR: "Citizen lifecycle, dispatch routing, operations",
    SocietyRole.ARCHIVIST: "Ledger integrity, chain maintenance, historical queries",
    SocietyRole.CITIZEN: "Base membership role — genesis role, immutable once granted",
    SocietyRole.WITNESS: "Independent attestation of other roles' actions",
    SocietyRole.AUDITOR: "T3/V3 validation and trust auditing",
}


@dataclass
class RoleAssignment:
    """A role assignment — binds a role to its own LCT and tracks the filling entity.

    Key principle from society-roles.md §5: authority binds to ``role_lct_id``,
    not ``filling_entity_lct_id``. When the filling entity rotates, accountability
    chains remain intact because the role's LCT (and its signature history)
    doesn't change.

    Cross-language parity with ``web4-core/src/role.rs::RoleAssignment``.
    """

    role: SocietyRole
    """The role being assigned."""

    role_lct_id: str
    """The role's own LCT — authority binds here."""

    filling_entity_lct_id: str
    """The entity currently filling this role."""

    assigned_by: str
    """Who assigned this role (typically Sovereign or Administrator LCT ID)."""

    assigned_at: str = ""
    """ISO timestamp of when this assignment was made."""

    role_trust: T3 = field(default_factory=T3)
    """Trust metrics for this role's performance."""

    role_value: V3 = field(default_factory=V3)
    """Value metrics for this role's contributions."""

    multi_holder: bool = False
    """Whether the role is filled by multiple entities simultaneously
    (e.g., a committee of Witnesses)."""

    additional_holders: List[str] = field(default_factory=list)
    """Additional entities filling this role (for committee/federation patterns)."""

    def rotate(self, new_entity_lct_id: str, rotated_by: str, timestamp: str = "") -> None:
        """Rotate the entity filling this role. The role-LCT stays the same.

        This is the core principle: authority binds to the role, not the person.
        When a Treasurer is replaced, the Treasury's signature chain continues
        uninterrupted under the same role-LCT.

        Args:
            new_entity_lct_id: LCT ID of the entity now filling the role.
            rotated_by: LCT ID of the entity authorizing the rotation
                        (typically Sovereign or Administrator).
            timestamp: ISO timestamp of the rotation.
        """
        self.filling_entity_lct_id = new_entity_lct_id
        self.assigned_by = rotated_by
        if timestamp:
            self.assigned_at = timestamp

    def add_holder(self, entity_lct_id: str) -> bool:
        """Add an additional holder (committee/federation pattern).

        For roles like Witness where multiple entities may need to act
        in the same role simultaneously.

        Returns False if the entity is already a holder or is the primary filler.
        """
        if entity_lct_id == self.filling_entity_lct_id:
            return False
        if entity_lct_id in self.additional_holders:
            return False
        self.additional_holders.append(entity_lct_id)
        self.multi_holder = True
        return True

    def remove_holder(self, entity_lct_id: str) -> bool:
        """Remove an additional holder.

        Returns False if the entity is not an additional holder.
        Cannot remove the primary filling entity — use rotate() for that.
        """
        if entity_lct_id not in self.additional_holders:
            return False
        self.additional_holders.remove(entity_lct_id)
        if not self.additional_holders:
            self.multi_holder = False
        return True

    def is_authorized(self, entity_lct_id: str) -> bool:
        """Check if an entity is authorized to act in this role.

        Returns True if the entity is the primary filler or an additional holder.
        """
        return entity_lct_id == self.filling_entity_lct_id or entity_lct_id in self.additional_holders

    @property
    def all_holders(self) -> List[str]:
        """All entities authorized for this role (primary + additional)."""
        return [self.filling_entity_lct_id] + list(self.additional_holders)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "role": self.role.value,
            "role_lct_id": self.role_lct_id,
            "filling_entity_lct_id": self.filling_entity_lct_id,
            "assigned_by": self.assigned_by,
            "assigned_at": self.assigned_at,
            "role_trust": {
                "talent": self.role_trust.talent,
                "training": self.role_trust.training,
                "temperament": self.role_trust.temperament,
            },
            "role_value": {
                "valuation": self.role_value.valuation,
                "veracity": self.role_value.veracity,
                "validity": self.role_value.validity,
            },
            "multi_holder": self.multi_holder,
            "additional_holders": list(self.additional_holders),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RoleAssignment:
        """Deserialize from dictionary."""
        rt = data.get("role_trust", {})
        rv = data.get("role_value", {})
        return cls(
            role=SocietyRole(data["role"]),
            role_lct_id=data["role_lct_id"],
            filling_entity_lct_id=data["filling_entity_lct_id"],
            assigned_by=data["assigned_by"],
            assigned_at=data.get("assigned_at", ""),
            role_trust=T3(
                talent=rt.get("talent", 0.5),
                training=rt.get("training", 0.5),
                temperament=rt.get("temperament", 0.5),
            ),
            role_value=V3(
                valuation=rv.get("valuation", 0.5),
                veracity=rv.get("veracity", 0.5),
                validity=rv.get("validity", 0.5),
            ),
            multi_holder=data.get("multi_holder", False),
            additional_holders=list(data.get("additional_holders", [])),
        )


# ── Bootstrap (solo-founder genesis) ─────────────────────────


def bootstrap_society_roles(
    founder_lct_id: str,
    timestamp: str = "",
    role_lct_factory: Optional[Any] = None,
) -> List[RoleAssignment]:
    """Create role assignments for solo-founder genesis.

    Per inter-society-protocol.md §2.1: a single entity MAY found a society.
    "Solo founder wears many hats." The founder fills all 7 base-mandatory
    roles. Each role gets its own LCT ID (supplied by ``role_lct_factory``
    or generated as deterministic strings).

    This resolves the cross-language gap where the Python SDK's
    ``create_society()`` required ``len(founders) >= 2`` while the spec
    and Rust SDK support solo-founder genesis.

    Args:
        founder_lct_id: LCT ID of the founding entity.
        timestamp: ISO timestamp of the bootstrap.
        role_lct_factory: Optional callable that returns a new LCT ID string.
            If None, generates deterministic IDs as ``{founder_lct_id}:role:{role_value}``.

    Returns:
        List of 7 RoleAssignment objects, one per base-mandatory role,
        all with the founder as both assigner and filler.
    """
    assignments: List[RoleAssignment] = []

    for role in BASE_MANDATORY_ROLES:
        if role_lct_factory is not None:
            role_lct_id = str(role_lct_factory())
        else:
            role_lct_id = f"{founder_lct_id}:role:{role.value}"

        assignments.append(
            RoleAssignment(
                role=role,
                role_lct_id=role_lct_id,
                filling_entity_lct_id=founder_lct_id,
                assigned_by=founder_lct_id,
                assigned_at=timestamp,
            )
        )

    return assignments
