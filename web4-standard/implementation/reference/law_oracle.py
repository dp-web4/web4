"""
Web4 Law Oracle Implementation
================================

The Law Oracle is the authoritative source of rules, norms, procedures, and
interpretations for a society. It provides:

1. Versioned law datasets (norms + procedures + interpretations)
2. Role permission queries (what actions are allowed for a role?)
3. Action legality checks (is this specific action legal?)
4. Witness requirements (when is human oversight needed?)
5. Resource limits (ATP caps, compute limits, etc.)
6. Machine-readable rules for R6 action grammar

Architecture:
- Law Oracle LCT: Publishes signed law datasets
- Law Dataset: Versioned collection of norms, procedures, interpretations
- Norm: Rule defining allowed/denied actions with constraints
- Procedure: Process requirements (witness quorum, validation steps)
- Interpretation: Precedents and clarifications with lineage

Integration:
- Authorization Engine: Queries for role permissions and action legality
- LCT Registry: Validates law oracle identity
- Ledger (future): Immutable law version history
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, Any
from enum import Enum
import hashlib
import json
import time


class NormType(Enum):
    """Types of law norms"""
    ALLOW = "allow"          # Explicitly allow action
    DENY = "deny"            # Explicitly deny action
    REQUIRE = "require"      # Action requires condition
    LIMIT = "limit"          # Action has quantitative limit
    PROCEDURE = "procedure"  # Action must follow procedure


class Operator(Enum):
    """Comparison operators for norms"""
    LTE = "<="
    LT = "<"
    GTE = ">="
    GT = ">"
    EQ = "=="
    NE = "!="
    IN = "in"
    NOT_IN = "not_in"


@dataclass
class Norm:
    """
    A single law norm (rule).

    Examples:
    - Norm(id="ATP-LIMIT", type=LIMIT, selector="atp_cost", op="<=", value=1000)
    - Norm(id="WRITE-REQUIRE-WITNESS", type=REQUIRE, selector="action", op="==", value="write", condition="witness_required")
    - Norm(id="COMPUTE-ALLOWED", type=ALLOW, selector="action", op="==", value="compute")
    """
    norm_id: str
    norm_type: NormType
    selector: str                    # What field to evaluate (action, atp_cost, resource, etc.)
    operator: Operator
    value: Any                       # Value to compare against
    condition: Optional[str] = None  # Additional condition or consequence
    reason: Optional[str] = None     # Human-readable explanation


@dataclass
class Procedure:
    """
    A procedure defining process requirements.

    Examples:
    - Procedure(id="HIGH-VALUE-WITNESS", triggers=["atp_cost>500"], requires_witnesses=3)
    - Procedure(id="DELETE-APPROVAL", triggers=["action==delete"], requires_quorum=2)
    """
    procedure_id: str
    triggers: List[str]                    # When this procedure applies
    requires_witnesses: int = 0            # How many witnesses required
    requires_quorum: int = 0               # Quorum of approvers needed
    validation_steps: List[str] = field(default_factory=list)  # Validation requirements
    timeout_seconds: Optional[int] = None  # Time limit for procedure completion


@dataclass
class Interpretation:
    """
    Law interpretation/precedent with lineage.

    Interpretations clarify how norms apply in specific cases
    and build a precedent chain.
    """
    interpretation_id: str
    question: str                   # What was being clarified
    answer: str                     # The interpretation
    applies_to_norms: List[str]     # Which norms this interprets
    replaces: Optional[str] = None  # Previous interpretation replaced
    reason: str = ""                # Why this interpretation was made
    timestamp: float = field(default_factory=time.time)
    hash: str = field(init=False)

    def __post_init__(self):
        """Compute interpretation hash for immutability"""
        content = f"{self.interpretation_id}:{self.question}:{self.answer}:{self.applies_to_norms}:{self.timestamp}"
        self.hash = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class RolePermissions:
    """
    Permissions granted to a role by law.

    This is what authorization engine requests from law oracle.
    """
    role_lct: str
    allowed_actions: Set[str]
    denied_actions: Set[str] = field(default_factory=set)
    resource_limits: Dict[str, int] = field(default_factory=dict)
    trust_threshold: float = 0.5
    requires_witness: bool = False
    max_atp_per_action: int = 1000
    rate_limits: Dict[str, int] = field(default_factory=dict)  # action -> max per hour

    def can_perform(self, action: str) -> bool:
        """Check if this role allows the action"""
        return action in self.allowed_actions and action not in self.denied_actions


@dataclass
class LawDataset:
    """
    Complete law dataset for a society (versioned).

    This is the canonical law that governs all actions in the society.
    """
    version: str
    society_id: str
    law_oracle_lct: str
    norms: List[Norm] = field(default_factory=list)
    procedures: List[Procedure] = field(default_factory=list)
    interpretations: List[Interpretation] = field(default_factory=list)
    role_bindings: Dict[str, RolePermissions] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    previous_version: Optional[str] = None
    hash: str = field(init=False)

    def __post_init__(self):
        """Compute dataset hash for integrity"""
        content = {
            "version": self.version,
            "society_id": self.society_id,
            "law_oracle_lct": self.law_oracle_lct,
            "norms": [{"id": n.norm_id, "type": n.norm_type.value} for n in self.norms],
            "procedures": [{"id": p.procedure_id} for p in self.procedures],
            "interpretations": [i.hash for i in self.interpretations],
            "timestamp": self.timestamp
        }
        content_str = json.dumps(content, sort_keys=True)
        self.hash = hashlib.sha256(content_str.encode()).hexdigest()

    def to_json_ld(self) -> Dict:
        """Export as JSON-LD per SAL specification"""
        return {
            "@context": ["https://web4.io/contexts/law.jsonld"],
            "type": "Web4LawDataset",
            "id": f"web4://law/{self.society_id}/{self.version}",
            "hash": self.hash,
            "society": self.society_id,
            "lawOracle": self.law_oracle_lct,
            "version": self.version,
            "timestamp": self.timestamp,
            "previousVersion": self.previous_version,
            "norms": [
                {
                    "id": n.norm_id,
                    "type": n.norm_type.value,
                    "selector": n.selector,
                    "operator": n.operator.value,
                    "value": n.value,
                    "condition": n.condition,
                    "reason": n.reason
                }
                for n in self.norms
            ],
            "procedures": [
                {
                    "id": p.procedure_id,
                    "triggers": p.triggers,
                    "requiresWitnesses": p.requires_witnesses,
                    "requiresQuorum": p.requires_quorum,
                    "validationSteps": p.validation_steps,
                    "timeout": p.timeout_seconds
                }
                for p in self.procedures
            ],
            "interpretations": [
                {
                    "id": i.interpretation_id,
                    "question": i.question,
                    "answer": i.answer,
                    "appliesToNorms": i.applies_to_norms,
                    "replaces": i.replaces,
                    "reason": i.reason,
                    "hash": i.hash
                }
                for i in self.interpretations
            ]
        }


class LawOracle:
    """
    Law Oracle: Authoritative source of society rules.

    Responsibilities:
    1. Publish and version law datasets
    2. Answer permission queries (role → allowed actions)
    3. Check action legality (specific action → allowed/denied)
    4. Determine witness requirements
    5. Provide resource limits

    Integration with Authorization:
    - Authorization engine queries law oracle for role permissions
    - Each authorization decision is bound to specific law version (hash)
    - Law changes trigger re-authorization of active delegations
    """

    def __init__(self, society_id: str, law_oracle_lct: str):
        self.society_id = society_id
        self.law_oracle_lct = law_oracle_lct
        self.current_dataset: Optional[LawDataset] = None
        self.dataset_history: List[LawDataset] = []

    def publish_law_dataset(self, dataset: LawDataset) -> str:
        """
        Publish a new law dataset version.

        Returns: dataset hash
        """
        # Validate dataset
        if dataset.society_id != self.society_id:
            raise ValueError(f"Dataset society mismatch: {dataset.society_id} != {self.society_id}")

        if dataset.law_oracle_lct != self.law_oracle_lct:
            raise ValueError(f"Law oracle mismatch")

        # Link to previous version
        if self.current_dataset:
            dataset.previous_version = self.current_dataset.version

        # Archive current and update
        if self.current_dataset:
            self.dataset_history.append(self.current_dataset)

        self.current_dataset = dataset

        return dataset.hash

    def get_law_version(self) -> Optional[str]:
        """Get current law version"""
        return self.current_dataset.version if self.current_dataset else None

    def get_law_hash(self) -> Optional[str]:
        """Get current law hash (for binding to authorizations)"""
        return self.current_dataset.hash if self.current_dataset else None

    def get_role_permissions(self, role_lct: str) -> Optional[RolePermissions]:
        """
        Get permissions for a role.

        This is what authorization engine calls to determine:
        - What actions are allowed
        - What resource limits apply
        - What trust threshold is required
        - Whether witnesses are needed
        """
        if not self.current_dataset:
            return None

        # Check for explicit role binding
        if role_lct in self.current_dataset.role_bindings:
            return self.current_dataset.role_bindings[role_lct]

        # Derive from norms
        allowed_actions = set()
        denied_actions = set()
        resource_limits = {}
        trust_threshold = 0.5
        requires_witness = False
        max_atp = 1000

        # Apply norms to derive permissions
        for norm in self.current_dataset.norms:
            if norm.norm_type == NormType.ALLOW:
                if norm.selector == "action":
                    allowed_actions.add(norm.value)

            elif norm.norm_type == NormType.DENY:
                if norm.selector == "action":
                    denied_actions.add(norm.value)

            elif norm.norm_type == NormType.LIMIT:
                if norm.selector == "atp_cost":
                    max_atp = min(max_atp, int(norm.value))
                elif norm.selector.startswith("resource."):
                    resource_name = norm.selector.split(".")[1]
                    resource_limits[resource_name] = int(norm.value)

            elif norm.norm_type == NormType.REQUIRE:
                if "witness" in str(norm.condition):
                    requires_witness = True

        return RolePermissions(
            role_lct=role_lct,
            allowed_actions=allowed_actions,
            denied_actions=denied_actions,
            resource_limits=resource_limits,
            trust_threshold=trust_threshold,
            requires_witness=requires_witness,
            max_atp_per_action=max_atp
        )

    def check_action_legality(
        self,
        action: str,
        context: Dict,
        role_lct: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if specific action is legal under current law.

        Args:
            action: Action being attempted (read, write, compute, etc.)
            context: Additional context (atp_cost, resource, etc.)
            role_lct: Role under which action is performed

        Returns:
            (is_legal, denial_reason)
        """
        if not self.current_dataset:
            return False, "No law dataset published"

        # Check for explicit denials first
        for norm in self.current_dataset.norms:
            if norm.norm_type == NormType.DENY:
                if self._norm_matches(norm, action, context):
                    return False, f"Denied by norm {norm.norm_id}: {norm.reason}"

        # Check limits
        for norm in self.current_dataset.norms:
            if norm.norm_type == NormType.LIMIT:
                if not self._check_limit(norm, context):
                    return False, f"Exceeds limit {norm.norm_id}: {norm.selector} {norm.operator.value} {norm.value}"

        # Check requirements
        for norm in self.current_dataset.norms:
            if norm.norm_type == NormType.REQUIRE:
                if self._norm_matches(norm, action, context):
                    if not self._check_requirement(norm, context):
                        return False, f"Failed requirement {norm.norm_id}: {norm.condition}"

        # Check for explicit allows
        has_allow = False
        for norm in self.current_dataset.norms:
            if norm.norm_type == NormType.ALLOW:
                if self._norm_matches(norm, action, context):
                    has_allow = True
                    break

        if not has_allow:
            return False, "No explicit allow norm for this action"

        return True, None

    def check_witness_requirement(
        self,
        action: str,
        context: Dict,
        role_lct: str
    ) -> Tuple[bool, int]:
        """
        Determine if action requires witnesses and how many.

        Returns:
            (requires_witness, witness_count)
        """
        if not self.current_dataset:
            return False, 0

        # Check procedures first
        for proc in self.current_dataset.procedures:
            if self._procedure_triggers(proc, action, context):
                if proc.requires_witnesses > 0:
                    return True, proc.requires_witnesses

        # Check norms
        for norm in self.current_dataset.norms:
            if norm.norm_type == NormType.REQUIRE:
                if self._norm_matches(norm, action, context):
                    if "witness" in str(norm.condition):
                        # Parse witness count from condition
                        # e.g., "witness_required" or "witness_count_3"
                        if "_" in str(norm.condition):
                            parts = str(norm.condition).split("_")
                            if len(parts) == 3 and parts[1] == "count":
                                return True, int(parts[2])
                        return True, 1

        return False, 0

    def add_interpretation(
        self,
        interpretation_id: str,
        question: str,
        answer: str,
        applies_to_norms: List[str],
        reason: str = "",
        replaces: Optional[str] = None
    ) -> str:
        """
        Add a law interpretation (precedent).

        Returns: interpretation hash
        """
        if not self.current_dataset:
            raise ValueError("No law dataset to add interpretation to")

        interp = Interpretation(
            interpretation_id=interpretation_id,
            question=question,
            answer=answer,
            applies_to_norms=applies_to_norms,
            replaces=replaces,
            reason=reason
        )

        self.current_dataset.interpretations.append(interp)

        # Recompute dataset hash
        self.current_dataset.__post_init__()

        return interp.hash

    def get_interpretation_chain(self, interpretation_id: str) -> List[Interpretation]:
        """
        Get interpretation chain (current and all replaced versions).

        Useful for understanding evolution of law interpretation.
        """
        if not self.current_dataset:
            return []

        chain = []
        current_id = interpretation_id

        # Find in current dataset
        for interp in self.current_dataset.interpretations:
            if interp.interpretation_id == current_id:
                chain.append(interp)
                if interp.replaces:
                    current_id = interp.replaces
                else:
                    break

        # Search historical datasets
        for dataset in reversed(self.dataset_history):
            for interp in dataset.interpretations:
                if interp.interpretation_id == current_id:
                    chain.append(interp)
                    if interp.replaces:
                        current_id = interp.replaces
                    else:
                        return chain

        return chain

    def _norm_matches(self, norm: Norm, action: str, context: Dict) -> bool:
        """Check if norm applies to this action/context"""
        if norm.selector == "action":
            return self._evaluate_operator(action, norm.operator, norm.value)
        elif norm.selector in context:
            return self._evaluate_operator(context[norm.selector], norm.operator, norm.value)
        return False

    def _check_limit(self, norm: Norm, context: Dict) -> bool:
        """Check if context respects limit norm"""
        if norm.selector in context:
            return self._evaluate_operator(context[norm.selector], norm.operator, norm.value)
        return True  # No value to limit

    def _check_requirement(self, norm: Norm, context: Dict) -> bool:
        """Check if context meets requirement"""
        # Requirement checking depends on condition type
        # For now, assume conditions are in context
        if norm.condition:
            return context.get(norm.condition, False)
        return True

    def _procedure_triggers(self, proc: Procedure, action: str, context: Dict) -> bool:
        """Check if procedure is triggered by this action/context"""
        for trigger in proc.triggers:
            # Simple eval (in production, use safe expression parser)
            try:
                # Replace action and context references
                trigger_eval = trigger.replace("action", f"'{action}'")
                for key, value in context.items():
                    if isinstance(value, str):
                        trigger_eval = trigger_eval.replace(key, f"'{value}'")
                    else:
                        trigger_eval = trigger_eval.replace(key, str(value))

                if eval(trigger_eval):
                    return True
            except:
                continue

        return False

    def _evaluate_operator(self, left: Any, op: Operator, right: Any) -> bool:
        """Evaluate comparison operator"""
        try:
            if op == Operator.EQ:
                return left == right
            elif op == Operator.NE:
                return left != right
            elif op == Operator.LT:
                return left < right
            elif op == Operator.LTE:
                return left <= right
            elif op == Operator.GT:
                return left > right
            elif op == Operator.GTE:
                return left >= right
            elif op == Operator.IN:
                return left in right
            elif op == Operator.NOT_IN:
                return left not in right
            else:
                return False
        except:
            return False

    def get_stats(self) -> Dict:
        """Get law oracle statistics"""
        if not self.current_dataset:
            return {"status": "no_dataset"}

        return {
            "society_id": self.society_id,
            "law_oracle_lct": self.law_oracle_lct,
            "current_version": self.current_dataset.version,
            "current_hash": self.current_dataset.hash,
            "version_history": len(self.dataset_history),
            "norms": {
                "total": len(self.current_dataset.norms),
                "allow": sum(1 for n in self.current_dataset.norms if n.norm_type == NormType.ALLOW),
                "deny": sum(1 for n in self.current_dataset.norms if n.norm_type == NormType.DENY),
                "limit": sum(1 for n in self.current_dataset.norms if n.norm_type == NormType.LIMIT),
                "require": sum(1 for n in self.current_dataset.norms if n.norm_type == NormType.REQUIRE)
            },
            "procedures": len(self.current_dataset.procedures),
            "interpretations": len(self.current_dataset.interpretations),
            "role_bindings": len(self.current_dataset.role_bindings)
        }


def create_default_law_dataset(society_id: str, law_oracle_lct: str, version: str = "1.0.0") -> LawDataset:
    """
    Create a reasonable default law dataset for a society.

    Includes common norms for basic society operations.
    """
    norms = [
        # Allow basic actions
        Norm(
            norm_id="ALLOW-READ",
            norm_type=NormType.ALLOW,
            selector="action",
            operator=Operator.EQ,
            value="read",
            reason="Reading data is generally allowed"
        ),
        Norm(
            norm_id="ALLOW-WRITE",
            norm_type=NormType.ALLOW,
            selector="action",
            operator=Operator.EQ,
            value="write",
            reason="Writing data is allowed with constraints"
        ),
        Norm(
            norm_id="ALLOW-COMPUTE",
            norm_type=NormType.ALLOW,
            selector="action",
            operator=Operator.EQ,
            value="compute",
            reason="Computation is allowed with budget limits"
        ),

        # ATP limits
        Norm(
            norm_id="LIMIT-ATP-PER-ACTION",
            norm_type=NormType.LIMIT,
            selector="atp_cost",
            operator=Operator.LTE,
            value=1000,
            reason="Prevent excessive ATP consumption per action"
        ),

        # Resource limits
        Norm(
            norm_id="LIMIT-STORAGE",
            norm_type=NormType.LIMIT,
            selector="resource.storage",
            operator=Operator.LTE,
            value=10000,
            reason="Storage quota per allocation"
        ),

        # Deny dangerous actions without oversight
        Norm(
            norm_id="DENY-DELETE-UNWITNESSED",
            norm_type=NormType.REQUIRE,
            selector="action",
            operator=Operator.EQ,
            value="delete",
            condition="witness_required",
            reason="Deletions require human oversight"
        ),

        # High-value actions require witnesses
        Norm(
            norm_id="REQUIRE-WITNESS-HIGH-ATP",
            norm_type=NormType.REQUIRE,
            selector="atp_cost",
            operator=Operator.GT,
            value=500,
            condition="witness_count_2",
            reason="High-cost actions need witness validation"
        )
    ]

    procedures = [
        Procedure(
            procedure_id="PROC-HIGH-VALUE",
            triggers=["atp_cost>500"],
            requires_witnesses=2,
            validation_steps=["verify_atp_budget", "check_trust_score"],
            timeout_seconds=3600
        ),
        Procedure(
            procedure_id="PROC-DELETE",
            triggers=["action=='delete'"],
            requires_witnesses=3,
            requires_quorum=2,
            validation_steps=["verify_deletion_target", "confirm_intent"],
            timeout_seconds=7200
        )
    ]

    dataset = LawDataset(
        version=version,
        society_id=society_id,
        law_oracle_lct=law_oracle_lct,
        norms=norms,
        procedures=procedures
    )

    return dataset


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("  Web4 Law Oracle - Implementation Test")
    print("=" * 70)

    # Create law oracle
    society_id = "society:research_institute"
    law_oracle_lct = "lct:web4:oracle:law:society:research_institute:1"

    oracle = LawOracle(society_id, law_oracle_lct)

    print(f"\n✅ Law Oracle created for {society_id}")
    print(f"   Oracle LCT: {law_oracle_lct}")

    # Create and publish default law dataset
    dataset = create_default_law_dataset(society_id, law_oracle_lct, "1.0.0")
    law_hash = oracle.publish_law_dataset(dataset)

    print(f"\n✅ Law dataset v1.0.0 published")
    print(f"   Hash: {law_hash[:16]}...")
    print(f"   Norms: {len(dataset.norms)}")
    print(f"   Procedures: {len(dataset.procedures)}")

    # Query role permissions
    role_lct = "role:researcher"
    permissions = oracle.get_role_permissions(role_lct)

    print(f"\n📋 Permissions for {role_lct}:")
    print(f"   Allowed actions: {permissions.allowed_actions}")
    print(f"   Max ATP: {permissions.max_atp_per_action}")
    print(f"   Trust threshold: {permissions.trust_threshold}")

    # Check action legality
    print(f"\n🔍 Action Legality Checks:")

    # Legal action
    legal, reason = oracle.check_action_legality(
        "read",
        {"atp_cost": 50},
        role_lct
    )
    print(f"   read (50 ATP): {'✅ LEGAL' if legal else f'❌ ILLEGAL - {reason}'}")

    # Legal but high-cost
    legal, reason = oracle.check_action_legality(
        "compute",
        {"atp_cost": 700},
        role_lct
    )
    print(f"   compute (700 ATP): {'✅ LEGAL' if legal else f'❌ ILLEGAL - {reason}'}")

    # Exceeds limit
    legal, reason = oracle.check_action_legality(
        "compute",
        {"atp_cost": 1500},
        role_lct
    )
    print(f"   compute (1500 ATP): {'✅ LEGAL' if legal else f'❌ ILLEGAL - {reason}'}")

    # Check witness requirements
    print(f"\n👁️ Witness Requirements:")

    requires, count = oracle.check_witness_requirement("read", {"atp_cost": 50}, role_lct)
    print(f"   read (50 ATP): {'✅ Requires' if requires else '❌ No'} witness ({count} needed)")

    requires, count = oracle.check_witness_requirement("compute", {"atp_cost": 700}, role_lct)
    print(f"   compute (700 ATP): {'✅ Requires' if requires else '❌ No'} witness ({count} needed)")

    requires, count = oracle.check_witness_requirement("delete", {"atp_cost": 50}, role_lct)
    print(f"   delete (50 ATP): {'✅ Requires' if requires else '❌ No'} witness ({count} needed)")

    # Add interpretation
    print(f"\n📖 Adding Interpretation:")

    interp_hash = oracle.add_interpretation(
        interpretation_id="INTERP-001",
        question="Does 'read' action apply to cached data?",
        answer="Yes, reading includes cached data access",
        applies_to_norms=["ALLOW-READ"],
        reason="Clarification requested by authorization engine"
    )

    print(f"   ✅ Interpretation INTERP-001 added")
    print(f"   Hash: {interp_hash[:16]}...")

    # Export to JSON-LD
    print(f"\n📄 JSON-LD Export:")
    json_ld = dataset.to_json_ld()
    print(f"   Type: {json_ld['type']}")
    print(f"   ID: {json_ld['id']}")
    print(f"   Hash: {json_ld['hash'][:16]}...")

    # Statistics
    print(f"\n📊 Law Oracle Statistics:")
    stats = oracle.get_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for k, v in value.items():
                print(f"     {k}: {v}")
        else:
            print(f"   {key}: {value}")

    print(f"\n✅ Law Oracle implementation complete and tested!")
    print(f"✅ Ready for authorization engine integration")
