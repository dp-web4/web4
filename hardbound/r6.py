# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - R6 Workflow Implementation
# https://github.com/dp-web4/web4

"""
R6 Workflow: Request → Process → Result

Every action in a governed team follows the R6 pattern:
1. Rules - Which policy applies
2. Role - Who is requesting
3. Request - What action is requested
4. Reference - Context (code, issue, etc.)
5. Resource - ATP cost estimate
6. Result - Outcome (approved/rejected)

This creates an auditable trail of intent + outcome.
"""

import hashlib
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any
from enum import Enum

from .policy import Policy, PolicyRule, ApprovalType


class R6Status(Enum):
    """Status of an R6 request."""
    PENDING = "pending"      # Awaiting approval
    APPROVED = "approved"    # Approved, action can proceed
    REJECTED = "rejected"    # Rejected, action denied
    EXECUTED = "executed"    # Action executed successfully
    FAILED = "failed"        # Action execution failed
    CANCELLED = "cancelled"  # Cancelled by requester


@dataclass
class R6Request:
    """
    R6 Request capturing intent.

    The first 5 R's (Rules, Role, Request, Reference, Resource)
    are filled when the request is created.
    """
    # Identity
    r6_id: str
    team_id: str
    requester_lct: str
    created_at: str

    # R1: Rules - which policy applies
    action_type: str
    policy_version: int

    # R2: Role - requester's role in team
    requester_role: str
    requester_trust: float

    # R3: Request - what action is requested
    description: str
    target: str = ""  # File, branch, environment, etc.
    parameters: Dict = field(default_factory=dict)

    # R4: Reference - context
    reference_type: str = ""  # issue, pr, discussion, etc.
    reference_id: str = ""
    reference_data: Dict = field(default_factory=dict)

    # R5: Resource - cost estimate
    atp_cost: int = 1

    # State
    status: R6Status = R6Status.PENDING
    approvals: List[str] = field(default_factory=list)  # LCTs that approved
    rejections: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'R6Request':
        data = dict(data)  # Copy
        data["status"] = R6Status(data.get("status", "pending"))
        return cls(**data)


@dataclass
class R6Response:
    """
    R6 Response completing the workflow.

    The 6th R (Result) is filled when the request is closed.
    """
    r6_id: str
    status: R6Status
    closed_at: str
    closed_by: str  # LCT that closed the request

    # Result details
    result_type: str = ""  # success, error, cancelled
    result_data: Dict = field(default_factory=dict)
    error_message: str = ""

    # ATP accounting
    atp_consumed: int = 0
    atp_returned: int = 0

    # Trust impact
    trust_delta: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


class R6Workflow:
    """
    Manages R6 request lifecycle.

    Usage:
        workflow = R6Workflow(team, policy)
        request = workflow.create_request(...)
        response = workflow.process_request(request, approver_lct)
        workflow.execute_request(request_id, execution_result)
    """

    def __init__(self, team: 'Team', policy: Optional[Policy] = None):
        """
        Initialize R6 workflow.

        Args:
            team: Team this workflow is for
            policy: Policy to enforce (uses default if None)
        """
        from .team import Team
        self.team = team
        self.policy = policy or Policy()
        self.pending_requests: Dict[str, R6Request] = {}

    def create_request(
        self,
        requester_lct: str,
        action_type: str,
        description: str,
        target: str = "",
        parameters: Optional[Dict] = None,
        reference_type: str = "",
        reference_id: str = "",
        reference_data: Optional[Dict] = None
    ) -> R6Request:
        """
        Create a new R6 request.

        Args:
            requester_lct: LCT of the entity making the request
            action_type: Type of action (must match policy)
            description: Human-readable description
            target: Target of action (file, branch, etc.)
            parameters: Action parameters
            reference_type: Type of reference (issue, pr, etc.)
            reference_id: ID of reference
            reference_data: Additional reference data

        Returns:
            R6Request object

        Raises:
            ValueError: If requester is not a member
            PermissionError: If action not permitted by policy
        """
        # Get member info
        member = self.team.get_member(requester_lct)
        if not member:
            raise ValueError(f"Not a team member: {requester_lct}")

        # Get rule for action
        rule = self.policy.get_rule(action_type)
        if not rule:
            raise ValueError(f"No policy rule for action: {action_type}")

        # Check basic permission (without ATP deduction)
        trust_score = self.team.get_member_trust_score(requester_lct)
        atp_available = self.team.get_member_atp(requester_lct)

        permitted, reason, _ = self.policy.check_permission(
            action_type=action_type,
            role=member["role"],
            trust_score=trust_score,
            atp_available=atp_available
        )

        if not permitted:
            raise PermissionError(reason)

        # Generate request ID
        timestamp = datetime.now(timezone.utc)
        seed = f"{self.team.team_id}:{requester_lct}:{timestamp.isoformat()}"
        r6_hash = hashlib.sha256(seed.encode()).hexdigest()[:12]
        r6_id = f"r6:{r6_hash}"

        request = R6Request(
            r6_id=r6_id,
            team_id=self.team.team_id,
            requester_lct=requester_lct,
            created_at=timestamp.isoformat() + "Z",
            action_type=action_type,
            policy_version=self.policy.version,
            requester_role=member["role"],
            requester_trust=trust_score,
            description=description,
            target=target,
            parameters=parameters or {},
            reference_type=reference_type,
            reference_id=reference_id,
            reference_data=reference_data or {},
            atp_cost=rule.atp_cost,
            status=R6Status.PENDING
        )

        self.pending_requests[r6_id] = request

        # Record in audit trail
        self.team.ledger.record_audit(
            session_id=self.team.team_id,
            action_type="r6_created",
            tool_name="hardbound",
            target=r6_id,
            r6_data=request.to_dict()
        )

        return request

    def approve_request(self, r6_id: str, approver_lct: str) -> R6Request:
        """
        Approve an R6 request.

        For ADMIN approval, approver must be admin.
        For PEER approval, approver must be a team member (not requester).
        For MULTI_SIG, collects approvals until threshold met.
        """
        if r6_id not in self.pending_requests:
            raise ValueError(f"Request not found: {r6_id}")

        request = self.pending_requests[r6_id]

        if request.status != R6Status.PENDING:
            raise ValueError(f"Request not pending: {request.status.value}")

        # Get rule
        rule = self.policy.get_rule(request.action_type)
        if not rule:
            raise ValueError(f"No policy rule for: {request.action_type}")

        # Check approver permission
        if rule.approval == ApprovalType.ADMIN:
            if not self.team.verify_admin(approver_lct):
                raise PermissionError("Only admin can approve this request")
        elif rule.approval == ApprovalType.PEER:
            member = self.team.get_member(approver_lct)
            if not member:
                raise PermissionError("Approver must be a team member")
            if approver_lct == request.requester_lct:
                raise PermissionError("Cannot self-approve")
        elif rule.approval == ApprovalType.MULTI_SIG:
            member = self.team.get_member(approver_lct)
            if not member:
                raise PermissionError("Approver must be a team member")

        # Add approval
        if approver_lct not in request.approvals:
            request.approvals.append(approver_lct)

        # Check if sufficient approvals
        if rule.approval == ApprovalType.NONE:
            request.status = R6Status.APPROVED
        elif rule.approval == ApprovalType.MULTI_SIG:
            if len(request.approvals) >= rule.approval_count:
                request.status = R6Status.APPROVED
        else:
            # Single approval (ADMIN or PEER)
            request.status = R6Status.APPROVED

        # Record approval
        self.team.ledger.record_audit(
            session_id=self.team.team_id,
            action_type="r6_approved",
            tool_name="hardbound",
            target=r6_id,
            r6_data={
                "approver": approver_lct,
                "status": request.status.value,
                "approvals": request.approvals
            }
        )

        return request

    def reject_request(self, r6_id: str, rejector_lct: str,
                       reason: str = "") -> R6Response:
        """
        Reject an R6 request.

        Admin can reject any request.
        Peer reviewers can reject if they have review rights.
        """
        if r6_id not in self.pending_requests:
            raise ValueError(f"Request not found: {r6_id}")

        request = self.pending_requests[r6_id]

        if request.status != R6Status.PENDING:
            raise ValueError(f"Request not pending: {request.status.value}")

        # Check rejector permission
        is_admin = self.team.verify_admin(rejector_lct)
        member = self.team.get_member(rejector_lct)

        if not is_admin and not member:
            raise PermissionError("Must be admin or team member to reject")

        # Create response
        response = R6Response(
            r6_id=r6_id,
            status=R6Status.REJECTED,
            closed_at=datetime.now(timezone.utc).isoformat() + "Z",
            closed_by=rejector_lct,
            result_type="rejected",
            error_message=reason,
            atp_consumed=0,  # No ATP consumed on rejection
            atp_returned=0,
            trust_delta=-0.02  # Small trust penalty for rejected requests
        )

        # Update request
        request.status = R6Status.REJECTED
        request.rejections.append(rejector_lct)

        # Apply trust penalty to requester
        self.team.update_member_trust(
            request.requester_lct, "failure", 0.05
        )

        # Record rejection
        self.team.ledger.record_audit(
            session_id=self.team.team_id,
            action_type="r6_rejected",
            tool_name="hardbound",
            target=r6_id,
            r6_data={
                "rejector": rejector_lct,
                "reason": reason,
                "response": response.to_dict()
            }
        )

        # Remove from pending
        del self.pending_requests[r6_id]

        return response

    def execute_request(self, r6_id: str, success: bool,
                        result_data: Optional[Dict] = None,
                        error_message: str = "") -> R6Response:
        """
        Record execution result for an approved request.

        This completes the R6 lifecycle (the 6th R - Result).
        """
        if r6_id not in self.pending_requests:
            raise ValueError(f"Request not found: {r6_id}")

        request = self.pending_requests[r6_id]

        if request.status != R6Status.APPROVED:
            raise ValueError(f"Request not approved: {request.status.value}")

        # Consume ATP
        self.team.consume_member_atp(request.requester_lct, request.atp_cost)

        # Update trust based on outcome
        if success:
            trust_delta = self.team.update_member_trust(
                request.requester_lct, "success", 0.1
            )
            status = R6Status.EXECUTED
            result_type = "success"
        else:
            trust_delta = self.team.update_member_trust(
                request.requester_lct, "failure", 0.1
            )
            status = R6Status.FAILED
            result_type = "error"

        # Create response
        response = R6Response(
            r6_id=r6_id,
            status=status,
            closed_at=datetime.now(timezone.utc).isoformat() + "Z",
            closed_by=request.requester_lct,
            result_type=result_type,
            result_data=result_data or {},
            error_message=error_message if not success else "",
            atp_consumed=request.atp_cost,
            trust_delta=trust_delta.get("reliability", 0) if isinstance(trust_delta, dict) else 0
        )

        # Update request
        request.status = status

        # Record completion
        self.team.ledger.record_audit(
            session_id=self.team.team_id,
            action_type="r6_completed",
            tool_name="hardbound",
            target=r6_id,
            r6_data={
                "request": request.to_dict(),
                "response": response.to_dict()
            }
        )

        # Remove from pending
        del self.pending_requests[r6_id]

        return response

    def get_pending_requests(self) -> List[R6Request]:
        """Get all pending requests."""
        return list(self.pending_requests.values())

    def get_request(self, r6_id: str) -> Optional[R6Request]:
        """Get a specific request."""
        return self.pending_requests.get(r6_id)
