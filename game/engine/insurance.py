"""
ATP Insurance for Web4 Game Societies
Session #69 Track 1: Integration of Session #65 insurance with game fraud scenarios
Session #73: Added quality gates using V3 veracity for auditor selection

This module provides insurance mechanics for society treasuries to protect against
fraud and unexpected ATP losses.

Insurance Model:
- Societies purchase insurance policies for their treasuries
- Premium paid upfront (% of treasury balance)
- Coverage protects against fraud-related ATP losses
- Claims filed automatically when fraud detected
- Payouts compensate victim societies

Integration with failure_attributions:
- High-confidence fraud (confidence >= 0.80) triggers claims
- Payout amount = min(ATP_lost, max_payout * coverage_ratio)
- Insurance pool funded by premiums across all policies

Quality Gates (Session #73):
- Insurance claims require high V3 veracity auditors (≥0.90)
- Uses quality-aware agent selection
- Fail-fast if no qualified auditor available
"""

from typing import Dict, Any, Optional, List
from .models import World, Society
from .lct import LCT
from .agent_selection import (
    select_agent_with_quality,
    InsufficientQualityError,
    InsufficientATPBudgetError
)

class InsurancePool:
    """
    Simple insurance pool for game societies

    In production, this would be managed via database tables.
    For game simulation, we track it in-memory.
    """

    def __init__(self):
        self.total_premiums = 0.0
        self.total_payouts = 0.0
        self.active_policies: Dict[str, Dict[str, Any]] = {}  # {society_lct: policy}

    def get_balance(self) -> float:
        """Get current insurance pool balance"""
        return self.total_premiums - self.total_payouts

    def create_policy(
        self,
        society_lct: str,
        premium_paid: float,
        max_payout: float,
        coverage_ratio: float = 0.8
    ) -> Dict[str, Any]:
        """
        Create insurance policy for a society

        Args:
            society_lct: Society LCT identifier
            premium_paid: Upfront premium (ATP)
            max_payout: Maximum claim payout
            coverage_ratio: % of losses covered (0.0-1.0)

        Returns:
            Policy dict with details
        """
        policy = {
            'policy_id': f"policy:{society_lct}:{len(self.active_policies)}",
            'society_lct': society_lct,
            'premium_paid': premium_paid,
            'max_payout': max_payout,
            'coverage_ratio': coverage_ratio,
            'status': 'active',
            'claims_filed': 0,
            'total_paid_out': 0.0
        }

        self.active_policies[society_lct] = policy
        self.total_premiums += premium_paid

        return policy

    def file_claim(
        self,
        society_lct: str,
        atp_lost: float,
        fraud_evidence: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        File insurance claim for ATP loss

        Args:
            society_lct: Society filing claim
            atp_lost: ATP amount lost to fraud
            fraud_evidence: Evidence from failure_attribution

        Returns:
            Claim result with payout amount, or None if denied
        """
        policy = self.active_policies.get(society_lct)
        if not policy:
            return {
                'status': 'denied',
                'reason': 'no_active_policy',
                'payout': 0.0
            }

        if policy['status'] != 'active':
            return {
                'status': 'denied',
                'reason': f"policy_status_{policy['status']}",
                'payout': 0.0
            }

        # Check fraud confidence (require high confidence for payout)
        confidence = fraud_evidence.get('confidence_score', 0.0)
        if confidence < 0.80:
            return {
                'status': 'denied',
                'reason': f'confidence_too_low_{confidence:.2f}',
                'payout': 0.0
            }

        # Calculate payout
        covered_amount = atp_lost * policy['coverage_ratio']
        payout = min(covered_amount, policy['max_payout'] - policy['total_paid_out'])

        # Check insurance pool has funds
        if payout > self.get_balance():
            payout = self.get_balance()  # Partial payout if insufficient funds

        if payout <= 0:
            return {
                'status': 'denied',
                'reason': 'insufficient_pool_funds',
                'payout': 0.0
            }

        # Approve claim
        self.total_payouts += payout
        policy['claims_filed'] += 1
        policy['total_paid_out'] += payout

        claim = {
            'claim_id': f"claim:{society_lct}:{policy['claims_filed']}",
            'policy_id': policy['policy_id'],
            'atp_lost': atp_lost,
            'payout': payout,
            'coverage_ratio': policy['coverage_ratio'],
            'confidence': confidence,
            'status': 'approved',
            'evidence': fraud_evidence
        }

        return claim

    def get_policy(self, society_lct: str) -> Optional[Dict[str, Any]]:
        """Get active policy for society"""
        return self.active_policies.get(society_lct)

    def get_stats(self) -> Dict[str, Any]:
        """Get insurance pool statistics"""
        return {
            'total_premiums': self.total_premiums,
            'total_payouts': self.total_payouts,
            'balance': self.get_balance(),
            'active_policies': len(self.active_policies),
            'avg_premium': self.total_premiums / len(self.active_policies) if self.active_policies else 0.0,
            'claim_rate': self.total_payouts / self.total_premiums if self.total_premiums > 0 else 0.0
        }


def calculate_premium(
    treasury_balance: float,
    premium_rate: float = 0.05
) -> float:
    """
    Calculate insurance premium for society treasury

    Args:
        treasury_balance: Current ATP balance
        premium_rate: Premium as % of treasury (default 5%)

    Returns:
        Premium amount in ATP
    """
    return treasury_balance * premium_rate


def calculate_max_payout(
    treasury_balance: float,
    payout_ratio: float = 0.3
) -> float:
    """
    Calculate maximum payout for insurance policy

    Args:
        treasury_balance: Current ATP balance
        payout_ratio: Max payout as % of treasury (default 30%)

    Returns:
        Maximum payout amount in ATP
    """
    return treasury_balance * payout_ratio


def insure_society(
    world: World,
    society: Society,
    insurance_pool: InsurancePool,
    premium_rate: float = 0.05,
    coverage_ratio: float = 0.8
) -> Dict[str, Any]:
    """
    Purchase insurance policy for society treasury

    Args:
        world: Game world
        society: Society to insure
        insurance_pool: Insurance pool manager
        premium_rate: Premium as % of treasury
        coverage_ratio: % of losses covered

    Returns:
        Policy details
    """
    treasury_balance = society.treasury.get("ATP", 0.0)

    # Calculate premium and max payout
    premium = calculate_premium(treasury_balance, premium_rate)
    max_payout = calculate_max_payout(treasury_balance)

    # Deduct premium from treasury
    society.treasury["ATP"] = max(0.0, treasury_balance - premium)

    # Create policy
    policy = insurance_pool.create_policy(
        society_lct=society.society_lct,
        premium_paid=premium,
        max_payout=max_payout,
        coverage_ratio=coverage_ratio
    )

    # Create event for audit trail
    event = {
        'type': 'insurance_purchased',
        'society_lct': society.society_lct,
        'premium_paid': premium,
        'max_payout': max_payout,
        'coverage_ratio': coverage_ratio,
        'treasury_before': treasury_balance,
        'treasury_after': society.treasury["ATP"],
        'world_tick': world.tick
    }
    society.pending_events.append(event)

    return policy


def file_fraud_claim(
    world: World,
    society: Society,
    insurance_pool: InsurancePool,
    atp_lost: float,
    attribution_id: int,
    confidence_score: float,
    attributed_to_lct: str
) -> Optional[Dict[str, Any]]:
    """
    File insurance claim for fraud-related ATP loss

    Args:
        world: Game world
        society: Victim society
        insurance_pool: Insurance pool manager
        atp_lost: ATP stolen/lost
        attribution_id: Database attribution ID
        confidence_score: Fraud confidence (0.0-1.0)
        attributed_to_lct: Fraudster LCT

    Returns:
        Claim result with payout, or None if denied
    """
    fraud_evidence = {
        'attribution_id': attribution_id,
        'confidence_score': confidence_score,
        'attributed_to_lct': attributed_to_lct,
        'atp_lost': atp_lost,
        'world_tick': world.tick
    }

    claim = insurance_pool.file_claim(
        society_lct=society.society_lct,
        atp_lost=atp_lost,
        fraud_evidence=fraud_evidence
    )

    if claim and claim['status'] == 'approved':
        # Credit payout to society treasury
        payout = claim['payout']
        society.treasury["ATP"] = society.treasury.get("ATP", 0.0) + payout

        # Create event for audit trail
        event = {
            'type': 'insurance_payout',
            'society_lct': society.society_lct,
            'claim_id': claim['claim_id'],
            'atp_lost': atp_lost,
            'payout': payout,
            'attribution_id': attribution_id,
            'confidence': confidence_score,
            'world_tick': world.tick
        }
        society.pending_events.append(event)

    return claim


def file_fraud_claim_with_quality(
    world: World,
    society: Society,
    insurance_pool: InsurancePool,
    atp_lost: float,
    attribution_id: int,
    confidence_score: float,
    attributed_to_lct: str,
    available_auditors: List[LCT],
    auditor_atp_costs: Dict[str, float],
    atp_budget: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    File insurance claim with quality-aware auditor selection (Session #73)

    This version requires high V3 veracity auditor (≥0.90) to process claim.
    Implements fail-fast quality gates from HRM integration.

    Args:
        world: Game world
        society: Victim society
        insurance_pool: Insurance pool manager
        atp_lost: ATP stolen/lost
        attribution_id: Database attribution ID
        confidence_score: Fraud confidence (0.0-1.0)
        attributed_to_lct: Fraudster LCT
        available_auditors: List of auditor LCT objects
        auditor_atp_costs: ATP cost per auditor
        atp_budget: Optional ATP budget for auditor selection

    Returns:
        Claim result with payout and auditor info, or None if denied

    Raises:
        InsufficientQualityError: No auditor meets V3 veracity ≥0.90
        InsufficientATPBudgetError: Qualified auditors exceed budget

    Example:
        >>> try:
        ...     claim = file_fraud_claim_with_quality(
        ...         world, society, pool, atp_lost=300,
        ...         attribution_id=123, confidence_score=0.85,
        ...         attributed_to_lct="bad_agent",
        ...         available_auditors=auditors,
        ...         auditor_atp_costs={"auditor1": 50, "auditor2": 100}
        ...     )
        ... except InsufficientQualityError as e:
        ...     print(f"Cannot process claim: {e}")
    """
    # Step 1: Select qualified auditor using quality-aware selection
    try:
        auditor_selection = select_agent_with_quality(
            operation_type="insurance_claim",  # Requires V3 veracity ≥0.90
            agents=available_auditors,
            atp_costs=auditor_atp_costs,
            atp_budget=atp_budget
        )
    except (InsufficientQualityError, InsufficientATPBudgetError) as e:
        # Quality gate failed - cannot process claim
        # Return denied claim with quality failure reason
        return {
            'status': 'denied',
            'reason': f'quality_gate_failed: {str(e)}',
            'payout': 0.0,
            'auditor_selected': None,
            'quality_error': str(e)
        }

    # Step 2: Process claim with selected auditor
    fraud_evidence = {
        'attribution_id': attribution_id,
        'confidence_score': confidence_score,
        'attributed_to_lct': attributed_to_lct,
        'atp_lost': atp_lost,
        'world_tick': world.tick,
        'auditor_lct': auditor_selection.agent_lct,
        'auditor_veracity': auditor_selection.v3_veracity,
        'auditor_atp_cost': auditor_selection.atp_cost
    }

    claim = insurance_pool.file_claim(
        society_lct=society.society_lct,
        atp_lost=atp_lost,
        fraud_evidence=fraud_evidence
    )

    # Enhance claim result with quality gate info
    if claim:
        claim['auditor_lct'] = auditor_selection.agent_lct
        claim['auditor_veracity'] = auditor_selection.v3_veracity
        claim['auditor_atp_cost'] = auditor_selection.atp_cost
        claim['selection_reason'] = auditor_selection.reason

    if claim and claim['status'] == 'approved':
        # Credit payout to society treasury
        payout = claim['payout']
        society.treasury["ATP"] = society.treasury.get("ATP", 0.0) + payout

        # Deduct auditor cost from society treasury (or from payout)
        # For now, deduct from payout to keep net gain positive
        net_payout = payout - auditor_selection.atp_cost
        if net_payout < 0:
            # Auditor cost exceeds payout - claim might not be worth filing
            claim['net_payout'] = 0
            claim['auditor_cost_note'] = "Auditor cost exceeded payout"
        else:
            claim['net_payout'] = net_payout

        # Create event for audit trail
        event = {
            'type': 'insurance_payout_with_quality',
            'society_lct': society.society_lct,
            'claim_id': claim['claim_id'],
            'atp_lost': atp_lost,
            'payout': payout,
            'auditor_lct': auditor_selection.agent_lct,
            'auditor_veracity': auditor_selection.v3_veracity,
            'auditor_atp_cost': auditor_selection.atp_cost,
            'net_payout': claim.get('net_payout', payout),
            'attribution_id': attribution_id,
            'confidence': confidence_score,
            'world_tick': world.tick
        }
        society.pending_events.append(event)

    return claim


# Example usage and test
if __name__ == "__main__":
    print("ATP Insurance System Test")
    print("=" * 80)

    # Create insurance pool
    pool = InsurancePool()
    print(f"Initial pool balance: {pool.get_balance()} ATP")

    # Society A purchases insurance
    print(f"\n--- Society A Purchases Insurance ---")
    treasury_a = 2000.0
    premium_a = calculate_premium(treasury_a, 0.05)  # 5% = 100 ATP
    max_payout_a = calculate_max_payout(treasury_a, 0.3)  # 30% = 600 ATP

    policy_a = pool.create_policy(
        society_lct="lct:society:a",
        premium_paid=premium_a,
        max_payout=max_payout_a,
        coverage_ratio=0.8
    )

    print(f"Premium paid: {premium_a} ATP (5% of {treasury_a})")
    print(f"Max payout: {max_payout_a} ATP (30% of {treasury_a})")
    print(f"Coverage: {policy_a['coverage_ratio']*100:.0f}%")
    print(f"Pool balance: {pool.get_balance()} ATP")

    # Society B purchases insurance
    print(f"\n--- Society B Purchases Insurance ---")
    treasury_b = 1500.0
    premium_b = calculate_premium(treasury_b, 0.05)
    max_payout_b = calculate_max_payout(treasury_b)

    policy_b = pool.create_policy(
        society_lct="lct:society:b",
        premium_paid=premium_b,
        max_payout=max_payout_b,
        coverage_ratio=0.8
    )

    print(f"Premium paid: {premium_b} ATP (5% of {treasury_b})")
    print(f"Max payout: {max_payout_b} ATP")
    print(f"Pool balance: {pool.get_balance()} ATP")

    # Society A files claim for fraud
    print(f"\n--- Society A Files Fraud Claim ---")
    claim_a = pool.file_claim(
        society_lct="lct:society:a",
        atp_lost=300.0,  # Lost 300 ATP to fraud
        fraud_evidence={
            'attribution_id': 123,
            'confidence_score': 0.85,
            'attributed_to_lct': 'lct:agent:bob'
        }
    )

    print(f"ATP lost: 300")
    print(f"Coverage: 80% × 300 = 240 ATP covered")
    print(f"Payout: {claim_a['payout']} ATP")
    print(f"Claim status: {claim_a['status']}")
    print(f"Pool balance: {pool.get_balance()} ATP")

    # Statistics
    print(f"\n--- Insurance Pool Statistics ---")
    stats = pool.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
