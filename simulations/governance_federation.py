"""
Federation Governance: R6 + Economic Federation Integration

Track BU: Connects R6 workflow with economic federations.

Key principles:
1. Federation-level actions require ATP
2. Presence gates certain governance capabilities
3. Cross-federation proposals need economic backing
4. Trust scores influence voting weight

This creates economic accountability for governance actions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from pathlib import Path

from .r6 import R6Workflow, R6Request, R6Response, R6Status
from .economic_federation import EconomicFederationRegistry, EconomicOperationResult
from .federation_binding import FederationBindingRegistry
from .trust_maintenance import TrustMaintenanceManager


class GovernanceActionType(Enum):
    """Types of federation governance actions."""
    FEDERATION_POLICY_CHANGE = "federation_policy_change"
    CROSS_FED_PROPOSAL = "cross_fed_proposal"
    TRUST_ESTABLISHMENT = "trust_establishment"
    WITNESS_REQUEST = "witness_request"
    MAINTENANCE_WAIVER = "maintenance_waiver"
    EMERGENCY_ACTION = "emergency_action"


@dataclass
class GovernanceProposal:
    """A federation-level governance proposal."""
    proposal_id: str
    federation_id: str
    proposer_lct: str
    action_type: GovernanceActionType
    description: str
    parameters: Dict = field(default_factory=dict)

    # Economics
    atp_cost: float = 0.0
    atp_locked: float = 0.0  # ATP locked until proposal resolves

    # Voting
    approvals: List[str] = field(default_factory=list)  # Federation IDs
    rejections: List[str] = field(default_factory=list)
    approval_threshold: float = 0.6  # 60% weighted approval needed

    # Presence requirements
    min_proposer_presence: float = 0.35
    min_voter_presence: float = 0.3

    # Status
    status: str = "pending"  # pending, approved, rejected, executed, expired
    created_at: str = ""
    expires_at: str = ""

    # Results
    result_data: Dict = field(default_factory=dict)


@dataclass
class GovernanceVote:
    """A vote on a governance proposal."""
    voter_federation_id: str
    voter_presence: float
    voter_trust: float
    vote: str  # "approve" or "reject"
    weight: float  # Calculated from presence + trust
    timestamp: str
    attestation: str = ""


class FederationGovernance:
    """
    Manages federation-level governance with economic integration.

    Track BU: R6 + Economic Federation + Presence

    Features:
    - ATP-gated governance proposals
    - Presence requirements for proposers and voters
    - Weighted voting based on trust and presence
    - Cross-federation coordination
    """

    # Action ATP costs
    ACTION_COSTS = {
        GovernanceActionType.FEDERATION_POLICY_CHANGE: 50.0,
        GovernanceActionType.CROSS_FED_PROPOSAL: 100.0,
        GovernanceActionType.TRUST_ESTABLISHMENT: 30.0,
        GovernanceActionType.WITNESS_REQUEST: 10.0,
        GovernanceActionType.MAINTENANCE_WAIVER: 20.0,
        GovernanceActionType.EMERGENCY_ACTION: 200.0,
    }

    # Presence requirements by action
    ACTION_PRESENCE_REQUIREMENTS = {
        GovernanceActionType.FEDERATION_POLICY_CHANGE: 0.4,
        GovernanceActionType.CROSS_FED_PROPOSAL: 0.35,
        GovernanceActionType.TRUST_ESTABLISHMENT: 0.3,
        GovernanceActionType.WITNESS_REQUEST: 0.4,
        GovernanceActionType.MAINTENANCE_WAIVER: 0.35,
        GovernanceActionType.EMERGENCY_ACTION: 0.5,
    }

    # Default proposal expiry (days)
    DEFAULT_EXPIRY_DAYS = 7

    def __init__(
        self,
        economic_registry: EconomicFederationRegistry,
        binding_registry: FederationBindingRegistry,
        maintenance_manager: Optional[TrustMaintenanceManager] = None,
    ):
        """
        Initialize federation governance.

        Args:
            economic_registry: For ATP operations
            binding_registry: For presence and binding checks
            maintenance_manager: Optional, for trust maintenance operations
        """
        self.economics = economic_registry
        self.binding = binding_registry
        self.maintenance = maintenance_manager

        # Active proposals
        self._proposals: Dict[str, GovernanceProposal] = {}
        self._votes: Dict[str, List[GovernanceVote]] = {}  # proposal_id -> votes

    def create_proposal(
        self,
        federation_id: str,
        proposer_lct: str,
        action_type: GovernanceActionType,
        description: str,
        parameters: Optional[Dict] = None,
        affected_federations: Optional[List[str]] = None,
    ) -> Tuple[Optional[GovernanceProposal], str]:
        """
        Create a governance proposal.

        Returns:
            Tuple of (proposal or None, error message if failed)
        """
        # Check presence requirement
        status = self.binding.get_federation_binding_status(federation_id)
        if not status:
            return None, f"Federation {federation_id} not found in binding registry"

        min_presence = self.ACTION_PRESENCE_REQUIREMENTS.get(action_type, 0.3)
        if status.presence_score < min_presence:
            return None, (
                f"Insufficient presence: {status.presence_score:.2f} < {min_presence:.2f}. "
                f"Build more presence through team activity and witnessing."
            )

        # Calculate ATP cost
        base_cost = self.ACTION_COSTS.get(action_type, 50.0)

        # Cross-federation proposals cost more per affected federation
        num_affected = len(affected_federations) if affected_federations else 1
        total_cost = base_cost * num_affected

        # Check ATP balance
        balance = self.economics.get_balance(federation_id)
        if balance < total_cost:
            return None, f"Insufficient ATP: {balance:.1f} < {total_cost:.1f}"

        # Deduct ATP (locked until proposal resolves)
        # Direct balance modification (economics engine uses entity_balances dict)
        current_balance = self.economics.get_balance(federation_id)
        self.economics.economics.entity_balances[federation_id] = current_balance - total_cost

        # Create proposal
        proposal_id = f"gov:{federation_id}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        now = datetime.now(timezone.utc)

        proposal = GovernanceProposal(
            proposal_id=proposal_id,
            federation_id=federation_id,
            proposer_lct=proposer_lct,
            action_type=action_type,
            description=description,
            parameters=parameters or {},
            atp_cost=total_cost,
            atp_locked=total_cost,
            min_proposer_presence=min_presence,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(days=self.DEFAULT_EXPIRY_DAYS)).isoformat(),
        )

        self._proposals[proposal_id] = proposal
        self._votes[proposal_id] = []

        return proposal, ""

    def vote_on_proposal(
        self,
        proposal_id: str,
        voter_federation_id: str,
        vote: str,  # "approve" or "reject"
        attestation: str = "",
    ) -> Tuple[bool, str]:
        """
        Cast a vote on a governance proposal.

        Returns:
            Tuple of (success, error message if failed)
        """
        if proposal_id not in self._proposals:
            return False, "Proposal not found"

        proposal = self._proposals[proposal_id]

        if proposal.status != "pending":
            return False, f"Proposal is {proposal.status}, cannot vote"

        # Check if already voted
        existing_votes = [v for v in self._votes[proposal_id]
                        if v.voter_federation_id == voter_federation_id]
        if existing_votes:
            return False, "Federation has already voted"

        # Check voter presence
        voter_status = self.binding.get_federation_binding_status(voter_federation_id)
        if not voter_status:
            return False, "Voter federation not found"

        if voter_status.presence_score < proposal.min_voter_presence:
            return False, f"Insufficient voter presence: {voter_status.presence_score:.2f}"

        # Get trust between voter and proposer
        trust_rel = self.economics.registry.get_trust(
            voter_federation_id, proposal.federation_id
        )
        voter_trust = trust_rel.trust_score if trust_rel else 0.3

        # Calculate vote weight (presence + trust combination)
        # Weight = (presence * 0.6) + (trust * 0.4)
        weight = (voter_status.presence_score * 0.6) + (voter_trust * 0.4)

        # Create vote
        gov_vote = GovernanceVote(
            voter_federation_id=voter_federation_id,
            voter_presence=voter_status.presence_score,
            voter_trust=voter_trust,
            vote=vote,
            weight=weight,
            timestamp=datetime.now(timezone.utc).isoformat(),
            attestation=attestation,
        )

        self._votes[proposal_id].append(gov_vote)

        # Track in proposal
        if vote == "approve":
            proposal.approvals.append(voter_federation_id)
        else:
            proposal.rejections.append(voter_federation_id)

        # Check if proposal should be resolved
        self._check_proposal_resolution(proposal_id)

        return True, ""

    def _check_proposal_resolution(self, proposal_id: str) -> None:
        """Check if a proposal should be approved or rejected."""
        proposal = self._proposals[proposal_id]
        votes = self._votes[proposal_id]

        if not votes:
            return

        # Calculate weighted approval
        total_weight = sum(v.weight for v in votes)
        approval_weight = sum(v.weight for v in votes if v.vote == "approve")

        if total_weight == 0:
            return

        approval_ratio = approval_weight / total_weight

        # Check if threshold met
        if approval_ratio >= proposal.approval_threshold:
            self._approve_proposal(proposal_id)
        elif len(votes) >= 3 and approval_ratio < (1 - proposal.approval_threshold):
            # Clear rejection (>40% weighted rejection with 3+ votes)
            self._reject_proposal(proposal_id)

    def _approve_proposal(self, proposal_id: str) -> None:
        """Approve a proposal."""
        proposal = self._proposals[proposal_id]
        proposal.status = "approved"

        # Return half of locked ATP (execution cost still applies)
        return_amount = proposal.atp_locked * 0.5
        current_balance = self.economics.get_balance(proposal.federation_id)
        self.economics.economics.entity_balances[proposal.federation_id] = current_balance + return_amount
        proposal.atp_locked -= return_amount

    def _reject_proposal(self, proposal_id: str) -> None:
        """Reject a proposal."""
        proposal = self._proposals[proposal_id]
        proposal.status = "rejected"

        # Return 75% of locked ATP (25% penalty for rejected proposal)
        return_amount = proposal.atp_locked * 0.75
        current_balance = self.economics.get_balance(proposal.federation_id)
        self.economics.economics.entity_balances[proposal.federation_id] = current_balance + return_amount
        proposal.atp_locked = 0

    def execute_proposal(
        self,
        proposal_id: str,
        executor_lct: str,
    ) -> Tuple[bool, str, Dict]:
        """
        Execute an approved proposal.

        Returns:
            Tuple of (success, error message, result data)
        """
        if proposal_id not in self._proposals:
            return False, "Proposal not found", {}

        proposal = self._proposals[proposal_id]

        if proposal.status != "approved":
            return False, f"Proposal is {proposal.status}, cannot execute", {}

        # Execute based on action type
        result = {}
        success = True
        error = ""

        if proposal.action_type == GovernanceActionType.TRUST_ESTABLISHMENT:
            target_fed = proposal.parameters.get("target_federation")
            if target_fed:
                op_result = self.economics.establish_trust(
                    proposal.federation_id, target_fed
                )
                success = op_result.success
                error = str(op_result.error) if op_result.error else ""
                result = {"trust_result": op_result.success}

        elif proposal.action_type == GovernanceActionType.WITNESS_REQUEST:
            target_fed = proposal.parameters.get("target_federation")
            if target_fed and self.binding:
                witness_rel = self.binding.cross_federation_witness(
                    proposal.federation_id, target_fed
                )
                success = witness_rel is not None
                result = {"witness_established": success}

        elif proposal.action_type == GovernanceActionType.MAINTENANCE_WAIVER:
            # Maintenance waiver extends the due date
            target_rel = proposal.parameters.get("target_relationship")
            if target_rel and self.maintenance:
                # Reset maintenance timer
                source, target = target_rel.split("->")
                self.maintenance._last_maintenance[(source.strip(), target.strip())] = (
                    datetime.now(timezone.utc).isoformat()
                )
                result = {"waiver_granted": True}

        if success:
            proposal.status = "executed"
            proposal.result_data = result
            # Consume remaining locked ATP
            proposal.atp_locked = 0

        return success, error, result

    def get_proposal(self, proposal_id: str) -> Optional[GovernanceProposal]:
        """Get a proposal by ID."""
        return self._proposals.get(proposal_id)

    def get_proposal_votes(self, proposal_id: str) -> List[GovernanceVote]:
        """Get all votes for a proposal."""
        return self._votes.get(proposal_id, [])

    def get_pending_proposals(
        self,
        federation_id: Optional[str] = None,
    ) -> List[GovernanceProposal]:
        """Get pending proposals, optionally filtered by federation."""
        proposals = [p for p in self._proposals.values() if p.status == "pending"]

        if federation_id:
            proposals = [p for p in proposals if p.federation_id == federation_id]

        return proposals

    def get_voting_power(self, federation_id: str) -> Dict:
        """
        Get a federation's voting power breakdown.

        Returns presence, trust average, and total weight.
        """
        status = self.binding.get_federation_binding_status(federation_id)
        if not status:
            return {"error": "Federation not found"}

        # Get average trust with other federations
        trust_sum = 0.0
        trust_count = 0

        for fed_id in self.binding._federation_lcts:
            if fed_id != federation_id:
                trust_rel = self.economics.registry.get_trust(federation_id, fed_id)
                if trust_rel:
                    trust_sum += trust_rel.trust_score
                    trust_count += 1

        avg_trust = trust_sum / trust_count if trust_count > 0 else 0.3

        # Calculate voting weight
        weight = (status.presence_score * 0.6) + (avg_trust * 0.4)

        return {
            "federation_id": federation_id,
            "presence_score": status.presence_score,
            "average_trust": avg_trust,
            "trust_relationships": trust_count,
            "voting_weight": weight,
            "can_vote": status.presence_score >= 0.3,
            "can_propose_policy": status.presence_score >= 0.4,
            "can_propose_cross_fed": status.presence_score >= 0.35,
        }

    def check_governance_readiness(self, federation_id: str) -> Dict:
        """
        Check if a federation is ready for governance participation.

        Returns comprehensive readiness assessment.
        """
        status = self.binding.get_federation_binding_status(federation_id)
        if not status:
            return {"error": "Federation not found", "ready": False}

        balance = self.economics.get_balance(federation_id)
        voting_power = self.get_voting_power(federation_id)

        # Check capabilities
        can_vote = status.presence_score >= 0.3
        can_propose = status.presence_score >= 0.35 and balance >= 50
        can_witness = status.witness_eligible

        # Identify gaps
        gaps = []
        if not can_vote:
            gaps.append(f"Need {0.3 - status.presence_score:.2f} more presence to vote")
        if not can_propose:
            if status.presence_score < 0.35:
                gaps.append(f"Need {0.35 - status.presence_score:.2f} more presence to propose")
            if balance < 50:
                gaps.append(f"Need {50 - balance:.0f} more ATP to propose")
        if not can_witness:
            gaps.append(f"Need {0.4 - status.presence_score:.2f} more presence to witness")

        return {
            "federation_id": federation_id,
            "ready": can_vote and can_propose,
            "presence": status.presence_score,
            "atp_balance": balance,
            "voting_weight": voting_power.get("voting_weight", 0),
            "capabilities": {
                "can_vote": can_vote,
                "can_propose": can_propose,
                "can_witness": can_witness,
            },
            "gaps": gaps,
        }


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Federation Governance - Self Test")
    print("=" * 60)

    import tempfile

    tmp_dir = Path(tempfile.mkdtemp())

    # Create registries
    economic = EconomicFederationRegistry(db_path=tmp_dir / "economic.db")
    binding = FederationBindingRegistry(
        db_path=tmp_dir / "binding.db",
        federation_db_path=tmp_dir / "federation.db",
    )

    # Initialize governance
    governance = FederationGovernance(economic, binding)

    # Register federations
    print("\n1. Register federations:")
    binding.register_federation_with_binding("fed:gov_alpha", "Gov Alpha", initial_trust=0.9)
    binding.register_federation_with_binding("fed:gov_beta", "Gov Beta", initial_trust=0.8)
    economic.register_federation("fed:gov_alpha", "Gov Alpha", initial_atp=500)
    economic.register_federation("fed:gov_beta", "Gov Beta", initial_atp=300)
    print("   Registered fed:gov_alpha and fed:gov_beta")

    # Build presence
    print("\n2. Build presence:")
    for i in range(4):
        binding.bind_team_to_federation("fed:gov_alpha", f"team:alpha:{i}")
    for i in range(3):
        binding.bind_team_to_federation("fed:gov_beta", f"team:beta:{i}")
    binding.build_internal_presence("fed:gov_alpha")
    binding.build_internal_presence("fed:gov_beta")

    alpha_status = binding.get_federation_binding_status("fed:gov_alpha")
    beta_status = binding.get_federation_binding_status("fed:gov_beta")
    print(f"   Alpha presence: {alpha_status.presence_score:.2f}")
    print(f"   Beta presence: {beta_status.presence_score:.2f}")

    # Check readiness
    print("\n3. Check governance readiness:")
    alpha_ready = governance.check_governance_readiness("fed:gov_alpha")
    print(f"   Alpha ready: {alpha_ready['ready']}")
    print(f"   Alpha capabilities: {alpha_ready['capabilities']}")

    # Create proposal
    print("\n4. Create proposal:")
    proposal, error = governance.create_proposal(
        "fed:gov_alpha",
        "lct:proposer:alice",
        GovernanceActionType.CROSS_FED_PROPOSAL,
        "Establish alliance with Beta",
        parameters={"alliance_type": "mutual_trust"},
        affected_federations=["fed:gov_alpha", "fed:gov_beta"],
    )
    if proposal:
        print(f"   Created: {proposal.proposal_id}")
        print(f"   ATP cost: {proposal.atp_cost}")
    else:
        print(f"   Failed: {error}")

    # Vote on proposal
    if proposal:
        print("\n5. Vote on proposal:")
        success, error = governance.vote_on_proposal(
            proposal.proposal_id, "fed:gov_beta", "approve",
            attestation="Beta supports this alliance"
        )
        print(f"   Beta voted: success={success}")

        # Check proposal status
        updated = governance.get_proposal(proposal.proposal_id)
        print(f"   Proposal status: {updated.status}")

        votes = governance.get_proposal_votes(proposal.proposal_id)
        for v in votes:
            print(f"     - {v.voter_federation_id}: {v.vote} (weight: {v.weight:.2f})")

    print("\n" + "=" * 60)
    print("Self-test complete.")
