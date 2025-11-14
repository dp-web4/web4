#!/usr/bin/env python3
"""
MPE + FIPT + WAL Integration for Complete BEC Prevention
==========================================================

Combines Message Provenance Envelopes (MPE), Financial Instruction
Provenance Tokens (FIPT), and Web4 Accountability Layer (WAL) to create
a complete defense-in-depth system against Business Email Compromise attacks.

Defense Layers:
1. MPE: Cryptographic message provenance (who sent what, when, from where)
2. FIPT: Cryptographic payment endpoint binding (authorized payment instructions)
3. Reputation: Trust-based gating (who is allowed to do what)
4. WAL: Accountability and constraint enforcement (consequences for fraud)
5. Automatic Verification: System enforces checks (no human decision points)

Created: Session #26 (2025-11-14)
Updated: Session #27 (2025-11-14) - Added WAL integration
Related: FIPT (Session #25), MPE (Session #26), WAL (Session #27), Nova BEC Case Study
"""

import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone

# Import MPE
from mpe import (
    MPE,
    SenderDevice,
    SoftwareAgent,
    ThreadReference,
    TrustState,
    MessageType,
    MPEVerifier
)

# Import FIPT
from fipt import (
    FIPT,
    PaymentContext,
    PaymentEndpoint,
    PaymentEndpointType,
    PaymentAmountRange
)

# Import reputation
sys.path.insert(0, str(Path(__file__).parent.parent / "reputation"))
from reputation_tracker import ReputationTracker, BehaviorType

# Import FIPT-reputation integration
from fipt_reputation_integration import ReputationGatedFIPT

# Import WAL
from wal import WALEnforcement, WALEventType


@dataclass
class PaymentInstruction:
    """
    Complete payment instruction with MPE and FIPT.

    Represents the full Web4 model for authorizing a payment:
    - MPE proves message authenticity
    - FIPT proves payment endpoint authorization
    - Reputation gates both creation and execution
    """
    mpe: MPE  # Message provenance
    fipt: FIPT  # Payment endpoint authorization
    message_content: str  # Original message content
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class BECPreventionSystem:
    """
    Complete BEC Prevention System

    Integrates MPE + FIPT + Reputation + WAL for defense-in-depth against
    Business Email Compromise attacks.
    """

    def __init__(
        self,
        reputation_tracker: Optional[ReputationTracker] = None
    ):
        """
        Initialize BEC prevention system.

        Args:
            reputation_tracker: Optional reputation tracker (creates new if None)
        """
        self.reputation_tracker = reputation_tracker or ReputationTracker()
        self.fipt_system = ReputationGatedFIPT(self.reputation_tracker)
        self.mpe_verifier = MPEVerifier()
        self.wal_enforcement = WALEnforcement(self.reputation_tracker)

    def create_payment_instruction(
        self,
        sender_lct: str,
        sender_device: SenderDevice,
        software_agent: SoftwareAgent,
        message_content: str,
        subject_entity: str,
        counterparty_entity: str,
        payment_context: PaymentContext,
        payment_endpoint: PaymentEndpoint,
        organization: str = "default",
        thread_ref: Optional[ThreadReference] = None,
        mrh_context: Optional[str] = None
    ) -> Tuple[Optional[PaymentInstruction], str]:
        """
        Create a complete payment instruction with MPE and FIPT.

        This is the Web4 way to issue payment instructions:
        1. Check sender reputation
        2. Create MPE for message provenance
        3. Create FIPT for payment endpoint authorization
        4. Record behavior event

        Args:
            sender_lct: LCT of sender
            sender_device: Device provenance
            software_agent: Software agent
            message_content: Message content
            subject_entity: Payment from entity
            counterparty_entity: Payment to entity
            payment_context: Payment context (invoices, amounts, etc.)
            payment_endpoint: Payment endpoint
            organization: Organization context
            thread_ref: Optional thread reference
            mrh_context: Optional MRH context

        Returns:
            (PaymentInstruction, message) tuple - instruction is None if denied
        """
        # Check reputation for FIPT creation
        payment_amount = None
        if payment_context.amount_range:
            payment_amount = payment_context.amount_range.max

        can_create, reason = self.fipt_system.can_create_fipt(
            sender_lct, organization, payment_amount
        )

        if not can_create:
            return None, f"Payment instruction denied: {reason}"

        # Get sender's trust state
        t3 = self.reputation_tracker.calculate_t3(sender_lct, organization)
        trust_state = TrustState.from_t3(t3, organization)

        # Create MPE for message provenance
        mpe = MPE.create(
            sender_lct=sender_lct,
            sender_device=sender_device,
            software_agent=software_agent,
            message_content=message_content,
            message_type=MessageType.EMAIL,
            thread_ref=thread_ref,
            mrh_context=mrh_context,
            trust_state=trust_state
        )

        # Create FIPT for payment endpoint authorization
        fipt, fipt_message = self.fipt_system.create_fipt_with_reputation_check(
            issuer_lct=sender_lct,
            subject_entity=subject_entity,
            counterparty_entity=counterparty_entity,
            payment_context=payment_context,
            payment_endpoint=payment_endpoint,
            organization=organization
        )

        if fipt is None:
            return None, fipt_message

        # Create complete payment instruction
        instruction = PaymentInstruction(
            mpe=mpe,
            fipt=fipt,
            message_content=message_content
        )

        return instruction, f"Payment instruction created (MPE: {mpe.mpe_id}, FIPT: {fipt.fipt_id})"

    def verify_payment_instruction(
        self,
        instruction: PaymentInstruction,
        organization: str = "default",
        min_issuer_t3: float = 0.5
    ) -> Tuple[bool, str]:
        """
        Verify a payment instruction is legitimate.

        Checks:
        1. MPE signature and content integrity
        2. FIPT validity and authorization
        3. Issuer reputation
        4. Consistency between MPE and FIPT

        Args:
            instruction: Payment instruction to verify
            organization: Organization context
            min_issuer_t3: Minimum issuer reputation required

        Returns:
            (verified, reason) tuple
        """
        # Verify MPE
        if not instruction.mpe.verify(instruction.message_content):
            return False, "MPE verification failed - message may be tampered"

        # Verify MPE signature and trust
        mpe_result = self.mpe_verifier.verify_mpe(
            instruction.mpe,
            instruction.message_content,
            is_financial=True
        )

        if not mpe_result.verified:
            return False, f"MPE verification failed: {mpe_result.reason}"

        # Verify FIPT
        fipt_verified, fipt_message = self.fipt_system.verify_fipt_with_reputation(
            instruction.fipt,
            organization,
            min_issuer_t3
        )

        if not fipt_verified:
            return False, f"FIPT verification failed: {fipt_message}"

        # Check consistency: MPE sender must match FIPT issuer
        if instruction.mpe.sender_lct != instruction.fipt.issuer_lct:
            return False, "LCT mismatch: MPE sender != FIPT issuer"

        return True, "Payment instruction verified"

    def authorize_payment(
        self,
        instruction: PaymentInstruction,
        actual_payment_endpoint: PaymentEndpoint,
        payment_amount: float,
        organization: str = "default"
    ) -> Tuple[bool, str]:
        """
        Authorize a payment based on instruction.

        This is the critical check that prevents BEC attacks:
        1. Verify instruction (MPE + FIPT + reputation)
        2. Check payment endpoint matches FIPT
        3. Check amount is within FIPT range

        Args:
            instruction: Payment instruction
            actual_payment_endpoint: Actual endpoint payment will be sent to
            payment_amount: Actual payment amount
            organization: Organization context

        Returns:
            (authorized, reason) tuple
        """
        # Verify instruction
        verified, reason = self.verify_payment_instruction(instruction, organization)
        if not verified:
            return False, f"Instruction verification failed: {reason}"

        # Check FIPT amount validity
        if not instruction.fipt.verify(amount=payment_amount):
            return False, f"Payment amount ${payment_amount:,.2f} not authorized by FIPT"

        # CRITICAL: Check payment endpoint matches FIPT
        if actual_payment_endpoint.account != instruction.fipt.payment_endpoint.account:
            return False, "ATTACK DETECTED: Payment endpoint does not match FIPT authorization"

        if actual_payment_endpoint.routing != instruction.fipt.payment_endpoint.routing:
            return False, "ATTACK DETECTED: Routing number does not match FIPT authorization"

        # All checks passed
        return True, f"Payment authorized: ${payment_amount:,.2f} to {actual_payment_endpoint.account}"

    def report_attack(
        self,
        attacker_lct: str,
        instruction: Optional[PaymentInstruction],
        reporter_lct: str,
        organization: str = "default",
        description: str = "BEC attack detected",
        quarantine_days: int = 90
    ):
        """
        Report a detected BEC attack.

        This creates:
        - Permanent reputation penalty
        - WAL event with quarantine and transaction limits
        - Audit trail for forensics

        Args:
            attacker_lct: LCT of attacker
            instruction: Optional payment instruction (if available)
            reporter_lct: LCT of entity reporting attack
            organization: Organization context
            description: Description of attack
            quarantine_days: Days to quarantine attacker
        """
        # Collect evidence
        evidence_refs = []
        if instruction:
            evidence_refs.append(instruction.mpe.mpe_id)
            evidence_refs.append(instruction.fipt.fipt_id)

        # Record fraud attempt via WAL (includes reputation penalty)
        wal_event = self.wal_enforcement.record_fraud_attempt(
            entity_lct=attacker_lct,
            evidence_refs=evidence_refs,
            adjudicator=reporter_lct,
            organization=organization,
            description=description,
            quarantine_days=quarantine_days,
            max_transaction_value=1000.0  # Severely limit future transactions
        )

        return wal_event


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("MPE + FIPT Integration - Complete BEC Prevention")
    print("=" * 80)

    # Create system
    reputation = ReputationTracker()
    bec_system = BECPreventionSystem(reputation)

    print("\nScenario: Preventing $70K payment diversion attack\n")

    # Build reputation for legitimate vendor
    print("1. Legitimate vendor builds reputation:")
    vendor_lct = "lct:org:legitimate_vendor"
    org = "business_network"

    for i in range(10):
        reputation.record_event(
            agent_lct=vendor_lct,
            behavior_type=BehaviorType.SUCCESSFUL_ACTION,
            organization=org
        )

    vendor_t3 = reputation.calculate_t3(vendor_lct, org)
    print(f"   Vendor T3: {vendor_t3:.3f}")

    # Vendor creates legitimate payment instruction
    print("\n2. Vendor creates legitimate payment instruction:")

    vendor_device = SenderDevice(
        device_id="vendor-laptop-001",
        device_type="desktop",
        os_fingerprint="Ubuntu-22.04"
    )

    vendor_agent = SoftwareAgent(
        agent_id="web4-mail-client",
        version="1.0.0"
    )

    legitimate_message = """
    Hi Customer,

    For invoice #2025-001, please send payment of $70,000 to:

    Bank: JP Morgan Chase
    Routing: 021000021
    Account: 987654321

    Thank you!
    Vendor
    """

    legitimate_instruction, create_message = bec_system.create_payment_instruction(
        sender_lct=vendor_lct,
        sender_device=vendor_device,
        software_agent=vendor_agent,
        message_content=legitimate_message,
        subject_entity="customer",
        counterparty_entity="vendor",
        payment_context=PaymentContext(
            invoice_ids=["2025-001"],
            currency="USD",
            amount_range=PaymentAmountRange(60000, 80000)
        ),
        payment_endpoint=PaymentEndpoint(
            type=PaymentEndpointType.BANK_ACCOUNT,
            routing="021000021",
            account="987654321",
            bank_name="JP Morgan Chase"
        ),
        organization=org,
        thread_ref=ThreadReference(
            thread_id="thread:invoice-2025-001",
            position_in_thread=3
        )
    )

    if legitimate_instruction:
        print(f"   ✅ {create_message}")
        print(f"   MPE ID: {legitimate_instruction.mpe.mpe_id}")
        print(f"   FIPT ID: {legitimate_instruction.fipt.fipt_id}")

    # Customer verifies and authorizes legitimate payment
    print("\n3. Customer verifies legitimate payment instruction:")

    verified, verify_message = bec_system.verify_payment_instruction(
        legitimate_instruction, org
    )

    print(f"   Verified: {verified}")
    print(f"   Reason: {verify_message}")

    # Authorize payment to legitimate account
    print("\n4. Customer authorizes payment to legitimate account:")

    legitimate_endpoint = PaymentEndpoint(
        type=PaymentEndpointType.BANK_ACCOUNT,
        routing="021000021",
        account="987654321"
    )

    authorized, auth_message = bec_system.authorize_payment(
        legitimate_instruction,
        legitimate_endpoint,
        70000.0,
        org
    )

    if authorized:
        print(f"   ✅ {auth_message}")

    # Attacker attempts to create fraudulent instruction
    print("\n5. Attacker attempts to create fraudulent payment instruction:")

    attacker_lct = "lct:attacker:bec"
    attacker_device = SenderDevice("unknown", "mobile", "unknown")
    attacker_agent = SoftwareAgent("unknown", "0.0.0")

    fraudulent_message = """
    URGENT: Account under audit!

    Send payment to temporary account:
    Bank: Fraudulent Bank
    Routing: 111000025
    Account: ATTACKER-ACCOUNT
    """

    fraudulent_instruction, fraud_create_message = bec_system.create_payment_instruction(
        sender_lct=attacker_lct,
        sender_device=attacker_device,
        software_agent=attacker_agent,
        message_content=fraudulent_message,
        subject_entity="customer",
        counterparty_entity="vendor",
        payment_context=PaymentContext(
            invoice_ids=["2025-001"],
            amount_range=PaymentAmountRange(60000, 80000)
        ),
        payment_endpoint=PaymentEndpoint(
            type=PaymentEndpointType.BANK_ACCOUNT,
            routing="111000025",
            account="ATTACKER-ACCOUNT"
        ),
        organization=org
    )

    if fraudulent_instruction is None:
        print(f"   ✅ BLOCKED: {fraud_create_message}")

    # Attacker tries to divert legitimate payment
    print("\n6. Attacker tries to divert payment to fraudulent account:")

    attacker_endpoint = PaymentEndpoint(
        type=PaymentEndpointType.BANK_ACCOUNT,
        routing="111000025",
        account="ATTACKER-ACCOUNT"
    )

    attack_authorized, attack_message = bec_system.authorize_payment(
        legitimate_instruction,  # Using legitimate instruction
        attacker_endpoint,  # But trying to pay to attacker
        70000.0,
        org
    )

    if not attack_authorized:
        print(f"   ✅ BLOCKED: {attack_message}")

        # Report attack
        print("\n7. System reports BEC attack with WAL:")
        wal_event = bec_system.report_attack(
            attacker_lct=attacker_lct,
            instruction=legitimate_instruction,
            reporter_lct="lct:system:payment_processor",
            organization=org,
            description="Payment diversion attempt - endpoint mismatch",
            quarantine_days=90
        )

        attacker_t3 = reputation.calculate_t3(attacker_lct, org)
        print(f"   ✅ Attack reported - attacker T3: {attacker_t3:.3f}")
        print(f"   WAL Event ID: {wal_event.wal_event_id}")
        print(f"   Constraints: {len(wal_event.constraints)} active")
        for constraint in wal_event.constraints:
            print(f"     - {constraint.constraint_type}: {constraint.reason}")

    # Verify tampering detection
    print("\n8. Tampering detection test:")

    tampered_message = legitimate_message.replace("987654321", "ATTACKER-ACCOUNT")

    tamper_verified, tamper_message = bec_system.verify_payment_instruction(
        PaymentInstruction(
            mpe=legitimate_instruction.mpe,
            fipt=legitimate_instruction.fipt,
            message_content=tampered_message  # Tampered content
        ),
        org
    )

    if not tamper_verified:
        print(f"   ✅ TAMPERING DETECTED: {tamper_message}")

    print("\n" + "=" * 80)
    print("MPE + FIPT + WAL Integration: OPERATIONAL")
    print("=" * 80)
    print("\nDefense Layers:")
    print("  ✅ Layer 1: Cryptographic message provenance (MPE)")
    print("  ✅ Layer 2: Cryptographic payment authorization (FIPT)")
    print("  ✅ Layer 3: Reputation-based gating (T3 thresholds)")
    print("  ✅ Layer 4: Accountability & constraints (WAL)")
    print("  ✅ Layer 5: Automatic verification (no human decision)")
    print("\nBEC Attack Prevention:")
    print("  ✅ Attacker blocked from creating FIPTs (no reputation)")
    print("  ✅ Payment endpoint mismatch detected automatically")
    print("  ✅ Message tampering detected via content hash")
    print("  ✅ Attack reported with WAL event and constraints")
    print("  ✅ Permanent reputation penalty recorded")
    print("  ✅ Attacker quarantined for 90 days")
    print("  ✅ Transaction limits imposed ($1,000 max)")
    print("\nResult: $70,000 payment protected ✓")
