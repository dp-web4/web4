#!/usr/bin/env python3
"""
FIPT + Reputation Integration
==============================

Connects Financial Instruction Provenance Tokens to the Web4 reputation system.

Key Concepts:
- Creating FIPTs requires minimum reputation (prevents spam)
- FIPT verification considers issuer reputation
- False/fraudulent FIPTs damage reputation
- High-value FIPTs require higher reputation thresholds

Created: Session #25 (2025-11-14)
"""

import sys
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timezone

# Add reputation module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "reputation"))

from reputation_tracker import ReputationTracker, BehaviorType
from fipt import FIPT, PaymentContext, PaymentEndpoint


class ReputationGatedFIPT:
    """
    FIPT creation and verification with reputation gating.

    Prevents FIPT spam and fraud by requiring minimum reputation levels.
    """

    # Reputation thresholds for FIPT operations
    MIN_T3_CREATE_FIPT = 0.3  # Developing tier minimum
    MIN_T3_HIGH_VALUE = 0.5   # Trusted tier for high-value payments
    HIGH_VALUE_THRESHOLD = 50000  # USD

    def __init__(self, reputation_tracker: Optional[ReputationTracker] = None):
        """
        Initialize reputation-gated FIPT system.

        Args:
            reputation_tracker: Optional reputation tracker (creates new if None)
        """
        self.reputation_tracker = reputation_tracker or ReputationTracker()

    def can_create_fipt(
        self,
        issuer_lct: str,
        organization: str = "default",
        payment_amount: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Check if entity has sufficient reputation to create FIPT.

        Args:
            issuer_lct: LCT of entity requesting FIPT creation
            organization: Organization context
            payment_amount: Optional payment amount for threshold checks

        Returns:
            (allowed, reason) tuple
        """
        # Get reputation
        t3 = self.reputation_tracker.calculate_t3(issuer_lct, organization)

        # Check minimum threshold
        if t3 < self.MIN_T3_CREATE_FIPT:
            return False, f"Insufficient reputation (T3={t3:.2f} < {self.MIN_T3_CREATE_FIPT})"

        # Check high-value threshold if amount specified
        if payment_amount and payment_amount >= self.HIGH_VALUE_THRESHOLD:
            if t3 < self.MIN_T3_HIGH_VALUE:
                return False, f"High-value payment requires T3 >= {self.MIN_T3_HIGH_VALUE} (current: {t3:.2f})"

        return True, "Authorization granted"

    def create_fipt_with_reputation_check(
        self,
        issuer_lct: str,
        subject_entity: str,
        counterparty_entity: str,
        payment_context: PaymentContext,
        payment_endpoint: PaymentEndpoint,
        organization: str = "default",
        validity_days: int = 90
    ) -> Tuple[Optional[FIPT], str]:
        """
        Create FIPT with reputation check.

        Args:
            issuer_lct: LCT of FIPT issuer
            subject_entity: Entity payment is from
            counterparty_entity: Entity payment is to
            payment_context: Payment context
            payment_endpoint: Payment endpoint
            organization: Organization context
            validity_days: FIPT validity in days

        Returns:
            (fipt, message) tuple - FIPT is None if check fails
        """
        # Get payment amount if specified
        payment_amount = None
        if payment_context.amount_range:
            payment_amount = payment_context.amount_range.max

        # Check reputation
        allowed, reason = self.can_create_fipt(issuer_lct, organization, payment_amount)

        if not allowed:
            return None, f"FIPT creation denied: {reason}"

        # Create FIPT
        fipt = FIPT.create(
            issuer_lct=issuer_lct,
            subject_entity=subject_entity,
            counterparty_entity=counterparty_entity,
            payment_context=payment_context,
            payment_endpoint=payment_endpoint,
            validity_days=validity_days
        )

        # Record successful FIPT creation as positive behavior
        self.reputation_tracker.record_event(
            agent_lct=issuer_lct,
            behavior_type=BehaviorType.SUCCESSFUL_ACTION,
            organization=organization,
            description=f"Created FIPT {fipt.fipt_id}",
            metadata={"fipt_id": fipt.fipt_id, "amount_max": payment_amount}
        )

        return fipt, f"FIPT created successfully (T3={self.reputation_tracker.calculate_t3(issuer_lct, organization):.2f})"

    def verify_fipt_with_reputation(
        self,
        fipt: FIPT,
        organization: str = "default",
        min_issuer_t3: float = 0.3
    ) -> Tuple[bool, str]:
        """
        Verify FIPT including issuer reputation check.

        Args:
            fipt: FIPT to verify
            organization: Organization context
            min_issuer_t3: Minimum issuer reputation required

        Returns:
            (verified, message) tuple
        """
        # First, standard FIPT verification
        if not fipt.verify():
            return False, "FIPT verification failed (revoked or expired)"

        # Check issuer reputation
        issuer_t3 = self.reputation_tracker.calculate_t3(fipt.issuer_lct, organization)

        if issuer_t3 < min_issuer_t3:
            return False, f"Issuer reputation too low (T3={issuer_t3:.2f} < {min_issuer_t3})"

        return True, f"FIPT verified (issuer T3={issuer_t3:.2f})"

    def report_fraudulent_fipt(
        self,
        issuer_lct: str,
        fipt_id: str,
        reporter_lct: str,
        organization: str = "default",
        description: str = "Fraudulent FIPT reported"
    ):
        """
        Report a fraudulent FIPT, damaging issuer reputation.

        Args:
            issuer_lct: LCT of fraudulent FIPT issuer
            fipt_id: ID of fraudulent FIPT
            reporter_lct: LCT of entity reporting fraud
            organization: Organization context
            description: Description of fraud
        """
        # Severe penalty for fraudulent financial instructions
        self.reputation_tracker.record_event(
            agent_lct=issuer_lct,
            behavior_type=BehaviorType.FALSE_WITNESS,  # Analogous to false attestation
            organization=organization,
            description=description,
            attested_by=reporter_lct,
            metadata={"fipt_id": fipt_id, "fraud_type": "payment_endpoint"}
        )

    def get_fipt_trust_level(
        self,
        issuer_lct: str,
        organization: str = "default"
    ) -> str:
        """
        Get trust level description for FIPT issuer.

        Args:
            issuer_lct: LCT of FIPT issuer
            organization: Organization context

        Returns:
            Trust level description
        """
        t3 = self.reputation_tracker.calculate_t3(issuer_lct, organization)

        if t3 >= 0.7:
            return f"High Trust (T3={t3:.2f}) - Expert/Master"
        elif t3 >= 0.5:
            return f"Trusted (T3={t3:.2f}) - Standard operations"
        elif t3 >= 0.3:
            return f"Developing (T3={t3:.2f}) - Limited operations"
        else:
            return f"Low Trust (T3={t3:.2f}) - Novice"


# Example usage
if __name__ == "__main__":
    from reputation_tracker import set_reputation_tracker

    print("=" * 80)
    print("FIPT + Reputation Integration - Demo")
    print("=" * 80)

    # Create system
    reputation = ReputationTracker()
    set_reputation_tracker(reputation)
    fipt_system = ReputationGatedFIPT(reputation)

    print("\nScenario: Reputation-gated FIPT creation\n")

    # Agent 1: New agent (no reputation)
    print("1. New agent attempts to create FIPT:")
    agent_new = "lct:org:new_vendor"
    org = "test_org"

    can_create, reason = fipt_system.can_create_fipt(agent_new, org)
    print(f"   Can create: {can_create}")
    print(f"   Reason: {reason}")

    # Build reputation for agent
    print("\n2. Agent builds reputation through successful actions:")
    for i in range(5):
        reputation.record_event(
            agent_lct=agent_new,
            behavior_type=BehaviorType.SUCCESSFUL_ACTION,
            organization=org
        )

    t3 = reputation.calculate_t3(agent_new, org)
    print(f"   T3 after 5 actions: {t3:.3f}")
    print(f"   Trust level: {fipt_system.get_fipt_trust_level(agent_new, org)}")

    # Try again
    print("\n3. Agent attempts FIPT creation again:")
    can_create, reason = fipt_system.can_create_fipt(agent_new, org)
    print(f"   Can create: {can_create}")
    print(f"   Reason: {reason}")

    # Create FIPT
    print("\n4. Create FIPT with reputation check:")
    fipt, message = fipt_system.create_fipt_with_reputation_check(
        issuer_lct=agent_new,
        subject_entity="vendor",
        counterparty_entity="customer",
        payment_context=PaymentContext(
            invoice_ids=["INV-001"],
            currency="USD"
        ),
        payment_endpoint=PaymentEndpoint(
            type="bank_account",
            routing="021000021",
            account="987654321"
        ),
        organization=org
    )

    if fipt:
        print(f"   ✅ {message}")
        print(f"   FIPT ID: {fipt.fipt_id}")

    # Verify with reputation
    print("\n5. Verify FIPT including issuer reputation:")
    verified, verify_message = fipt_system.verify_fipt_with_reputation(fipt, org)
    print(f"   Verified: {verified}")
    print(f"   Message: {verify_message}")

    # High-value payment scenario
    print("\n6. High-value payment attempt ($75,000):")
    from fipt import PaymentAmountRange
    high_value_context = PaymentContext(
        invoice_ids=["INV-BIG"],
        currency="USD",
        amount_range=PaymentAmountRange(70000, 80000)
    )

    can_create_high, reason_high = fipt_system.can_create_fipt(
        agent_new, org, payment_amount=75000
    )
    print(f"   Can create high-value FIPT: {can_create_high}")
    print(f"   Reason: {reason_high}")

    # Build more reputation
    print("\n7. Agent builds more reputation (witness verifications):")
    for i in range(10):
        reputation.record_event(
            agent_lct=agent_new,
            behavior_type=BehaviorType.WITNESS_VERIFICATION,
            organization=org
        )

    t3_after = reputation.calculate_t3(agent_new, org)
    print(f"   T3 after attestations: {t3_after:.3f}")
    print(f"   Trust level: {fipt_system.get_fipt_trust_level(agent_new, org)}")

    # Try high-value again
    print("\n8. High-value payment attempt again:")
    can_create_high2, reason_high2 = fipt_system.can_create_fipt(
        agent_new, org, payment_amount=75000
    )
    print(f"   Can create: {can_create_high2}")
    print(f"   Reason: {reason_high2}")

    # Fraudulent FIPT scenario
    print("\n9. Fraudulent FIPT reporting:")
    bad_actor = "lct:org:fraudster"

    # Bad actor creates FIPT somehow
    print(f"   Bad actor {bad_actor} attempts fraud...")

    # System detects and reports
    fipt_system.report_fraudulent_fipt(
        issuer_lct=bad_actor,
        fipt_id="fipt:fraudulent123",
        reporter_lct=agent_new,
        organization=org,
        description="Payment endpoint changed to attacker account"
    )

    bad_t3 = reputation.calculate_t3(bad_actor, org)
    print(f"   ✅ Fraud reported - bad actor T3: {bad_t3:.3f}")
    print(f"   Trust level: {fipt_system.get_fipt_trust_level(bad_actor, org)}")

    print("\n" + "=" * 80)
    print("FIPT + Reputation Integration: OPERATIONAL")
    print("=" * 80)
    print("\nKey Capabilities:")
    print("  ✅ Reputation-gated FIPT creation")
    print("  ✅ High-value payment thresholds")
    print("  ✅ Reputation-aware FIPT verification")
    print("  ✅ Fraud reporting with reputation penalties")
    print("  ✅ Trust level assessment")
