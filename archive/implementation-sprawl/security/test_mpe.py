#!/usr/bin/env python3
"""
Tests for Web4 Message Provenance Envelope (MPE)
=================================================

Created: Session #26 (2025-11-14)
"""

from datetime import datetime, timezone
from mpe import (
    MPE,
    SenderDevice,
    SoftwareAgent,
    ThreadReference,
    TrustState,
    MessageType,
    MPEVerifier,
    MPEVerificationResult
)


def test_mpe_creation():
    """Test basic MPE creation"""
    print("\nTest 1: MPE Creation")

    device = SenderDevice(
        device_id="test-device-001",
        device_type="desktop",
        os_fingerprint="Ubuntu-22.04"
    )

    agent = SoftwareAgent(
        agent_id="web4-client",
        version="1.0.0"
    )

    trust = TrustState.from_t3(0.5, "test_org")

    message_content = "This is a test message."

    mpe = MPE.create(
        sender_lct="lct:org:test_sender",
        sender_device=device,
        software_agent=agent,
        message_content=message_content,
        trust_state=trust
    )

    assert mpe.mpe_id.startswith("mpe:")
    assert mpe.sender_lct == "lct:org:test_sender"
    assert mpe.signature is not None
    assert mpe.trust_state.trust_score == 0.5
    assert mpe.trust_state.trust_tier == "trusted"
    print("  ✅ MPE created successfully")
    print(f"     MPE ID: {mpe.mpe_id}")


def test_content_verification():
    """Test content hash verification"""
    print("\nTest 2: Content Verification")

    device = SenderDevice("dev1", "desktop", "Linux")
    agent = SoftwareAgent("agent1", "1.0.0")
    original_content = "Original message content"

    mpe = MPE.create(
        sender_lct="lct:org:sender",
        sender_device=device,
        software_agent=agent,
        message_content=original_content
    )

    # Verify with original content
    assert mpe.verify(original_content)
    print("  ✅ Original content verified")

    # Try to verify with tampered content
    tampered_content = "Tampered message content"
    assert not mpe.verify(tampered_content)
    print("  ✅ Tampered content rejected")


def test_trust_verification():
    """Test trust-based verification"""
    print("\nTest 3: Trust Verification")

    device = SenderDevice("dev1", "desktop", "Linux")
    agent = SoftwareAgent("agent1", "1.0.0")

    # High trust sender
    high_trust_mpe = MPE.create(
        sender_lct="lct:org:trusted_sender",
        sender_device=device,
        software_agent=agent,
        message_content="Message from trusted sender",
        trust_state=TrustState.from_t3(0.8)
    )

    assert high_trust_mpe.verify_sender_trust(0.5)
    print("  ✅ High trust sender verified (T3=0.8 >= 0.5)")

    # Low trust sender
    low_trust_mpe = MPE.create(
        sender_lct="lct:org:untrusted_sender",
        sender_device=device,
        software_agent=agent,
        message_content="Message from untrusted sender",
        trust_state=TrustState.from_t3(0.2)
    )

    assert not low_trust_mpe.verify_sender_trust(0.5)
    print("  ✅ Low trust sender rejected (T3=0.2 < 0.5)")


def test_financial_message_verification():
    """Test verification for financial messages (higher trust required)"""
    print("\nTest 4: Financial Message Verification")

    verifier = MPEVerifier(
        min_trust_for_standard=0.3,
        min_trust_for_financial=0.5
    )

    device = SenderDevice("dev1", "desktop", "Linux")
    agent = SoftwareAgent("agent1", "1.0.0")

    # Standard message from developing trust sender
    standard_content = "Regular business message"
    standard_mpe = MPE.create(
        sender_lct="lct:org:sender",
        sender_device=device,
        software_agent=agent,
        message_content=standard_content,
        trust_state=TrustState.from_t3(0.4)
    )

    # Should pass for standard message
    result = verifier.verify_mpe(standard_mpe, standard_content, is_financial=False)
    assert result.verified
    print("  ✅ Standard message from T3=0.4 sender accepted")

    # Should fail for financial message
    result = verifier.verify_mpe(standard_mpe, standard_content, is_financial=True)
    assert not result.verified
    assert not result.trust_sufficient
    print("  ✅ Financial message from T3=0.4 sender rejected")


def test_account_change_blocking():
    """Test blocking of account change from low-trust sender"""
    print("\nTest 5: Account Change Blocking")

    verifier = MPEVerifier()
    device = SenderDevice("dev1", "desktop", "Linux")
    agent = SoftwareAgent("agent1", "1.0.0")

    # Message from trusted (but not expert) sender
    message_content = "Please change payment account to..."
    mpe = MPE.create(
        sender_lct="lct:org:sender",
        sender_device=device,
        software_agent=agent,
        message_content=message_content,
        trust_state=TrustState.from_t3(0.6)  # Trusted but not expert
    )

    # Account changes require expert level (T3 >= 0.7)
    should_block, reason = verifier.should_block_action(
        mpe,
        message_content,
        action_type="account_change"
    )

    assert should_block
    assert "expert-level trust" in reason
    print("  ✅ Account change blocked for T3=0.6 sender")
    print(f"     Reason: {reason}")


def test_thread_reference():
    """Test thread/conversation tracking"""
    print("\nTest 6: Thread Reference")

    device = SenderDevice("dev1", "desktop", "Linux")
    agent = SoftwareAgent("agent1", "1.0.0")

    thread_ref = ThreadReference(
        thread_id="thread:conversation-001",
        parent_message_id="msg:parent-123",
        root_message_id="msg:root-100",
        position_in_thread=5
    )

    mpe = MPE.create(
        sender_lct="lct:org:sender",
        sender_device=device,
        software_agent=agent,
        message_content="Reply in thread",
        thread_ref=thread_ref
    )

    assert mpe.thread_ref is not None
    assert mpe.thread_ref.thread_id == "thread:conversation-001"
    assert mpe.thread_ref.position_in_thread == 5
    print("  ✅ Thread reference preserved")
    print(f"     Thread: {mpe.thread_ref.thread_id}")
    print(f"     Position: {mpe.thread_ref.position_in_thread}")


def test_device_attribution():
    """Test device and software attribution"""
    print("\nTest 7: Device Attribution")

    device = SenderDevice(
        device_id="laptop-abc-123",
        device_type="laptop",
        os_fingerprint="macOS-14.0-arm64",
        metadata={"manufacturer": "Apple", "model": "MacBook Pro"}
    )

    agent = SoftwareAgent(
        agent_id="web4-mail-client",
        version="2.1.0",
        agent_type="user_client",
        metadata={"build": "release"}
    )

    mpe = MPE.create(
        sender_lct="lct:org:sender",
        sender_device=device,
        software_agent=agent,
        message_content="Test message"
    )

    assert mpe.sender_device.device_id == "laptop-abc-123"
    assert mpe.sender_device.os_fingerprint == "macOS-14.0-arm64"
    assert mpe.software_agent.version == "2.1.0"
    print("  ✅ Device attribution recorded")
    print(f"     Device: {mpe.sender_device.device_id}")
    print(f"     OS: {mpe.sender_device.os_fingerprint}")
    print(f"     Agent: {mpe.software_agent.agent_id} v{mpe.software_agent.version}")


def test_message_types():
    """Test different message types"""
    print("\nTest 8: Message Types")

    device = SenderDevice("dev1", "server", "Linux")
    agent = SoftwareAgent("api-gateway", "1.0.0", "automated_agent")

    # Email message
    email_mpe = MPE.create(
        sender_lct="lct:org:sender",
        sender_device=device,
        software_agent=agent,
        message_content="Email content",
        message_type=MessageType.EMAIL
    )
    assert email_mpe.message_type == MessageType.EMAIL
    print("  ✅ Email message type")

    # API call message
    api_mpe = MPE.create(
        sender_lct="lct:org:sender",
        sender_device=device,
        software_agent=agent,
        message_content='{"action": "query", "data": "..."}',
        message_type=MessageType.API_CALL
    )
    assert api_mpe.message_type == MessageType.API_CALL
    print("  ✅ API call message type")

    # Chat message
    chat_mpe = MPE.create(
        sender_lct="lct:org:sender",
        sender_device=device,
        software_agent=agent,
        message_content="Chat message",
        message_type=MessageType.CHAT
    )
    assert chat_mpe.message_type == MessageType.CHAT
    print("  ✅ Chat message type")


def test_serialization():
    """Test MPE serialization to dict/JSON"""
    print("\nTest 9: Serialization")

    device = SenderDevice("dev1", "desktop", "Linux")
    agent = SoftwareAgent("agent1", "1.0.0")

    mpe = MPE.create(
        sender_lct="lct:org:sender",
        sender_device=device,
        software_agent=agent,
        message_content="Test message",
        trust_state=TrustState.from_t3(0.6)
    )

    # Convert to dict
    mpe_dict = mpe.to_dict()
    assert "mpe_id" in mpe_dict
    assert "sender_lct" in mpe_dict
    assert "sender_device" in mpe_dict
    assert "trust_state" in mpe_dict
    print("  ✅ MPE serialized to dict")

    # Convert to JSON
    mpe_json = mpe.to_json()
    assert "mpe_id" in mpe_json
    assert "content_hash" in mpe_json
    print("  ✅ MPE serialized to JSON")


def test_bec_attack_scenario():
    """Test complete BEC attack prevention scenario"""
    print("\nTest 10: BEC Attack Prevention Scenario")

    verifier = MPEVerifier()

    # Legitimate vendor MPE
    vendor_device = SenderDevice("vendor-laptop", "desktop", "Ubuntu-22.04")
    vendor_agent = SoftwareAgent("web4-mail", "1.0.0")
    vendor_trust = TrustState.from_t3(0.7, "business_network")

    legitimate_message = """
    Please send payment to:
    Bank: Chase
    Account: 987654321
    """

    vendor_mpe = MPE.create(
        sender_lct="lct:org:legitimate_vendor",
        sender_device=vendor_device,
        software_agent=vendor_agent,
        message_content=legitimate_message,
        trust_state=vendor_trust
    )

    # Verify legitimate message
    result = verifier.verify_mpe(vendor_mpe, legitimate_message, is_financial=True)
    assert result.verified
    assert result.is_safe_for_high_impact_action()
    print("  ✅ Legitimate vendor message verified")

    # Attacker MPE (compromised email, but no Web4 trust)
    attacker_device = SenderDevice("unknown", "mobile", "unknown")
    attacker_agent = SoftwareAgent("unknown", "0.0.0")
    attacker_trust = TrustState.from_t3(0.0, "business_network")

    fraudulent_message = """
    URGENT: Account under audit!
    Send payment to:
    Bank: Fraudulent Bank
    Account: ATTACKER-ACCOUNT
    """

    attacker_mpe = MPE.create(
        sender_lct="lct:attacker:spoofed",
        sender_device=attacker_device,
        software_agent=attacker_agent,
        message_content=fraudulent_message,
        trust_state=attacker_trust
    )

    # Verify attacker message is blocked
    result = verifier.verify_mpe(attacker_mpe, fraudulent_message, is_financial=True)
    assert not result.verified
    assert not result.is_safe_for_high_impact_action()
    print("  ✅ Attacker message blocked (insufficient trust)")

    # Check account change is blocked
    should_block, reason = verifier.should_block_action(
        attacker_mpe,
        fraudulent_message,
        action_type="account_change"
    )
    assert should_block
    print("  ✅ Account change blocked")

    # Verify tampering detection
    tampered = legitimate_message.replace("987654321", "ATTACKER")
    tamper_result = verifier.verify_mpe(vendor_mpe, tampered, is_financial=True)
    assert not tamper_result.verified
    print("  ✅ Message tampering detected")


def run_all_tests():
    """Run all MPE tests"""
    print("=" * 80)
    print("Web4 MPE - Test Suite")
    print("=" * 80)

    tests = [
        test_mpe_creation,
        test_content_verification,
        test_trust_verification,
        test_financial_message_verification,
        test_account_change_blocking,
        test_thread_reference,
        test_device_attribution,
        test_message_types,
        test_serialization,
        test_bec_attack_scenario,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n  ❌ FAILED: {test_func.__name__}")
            print(f"     Error: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n  ❌ ERROR: {test_func.__name__}")
            print(f"     Error: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 80)
    if failed == 0:
        print(f"✅ ALL TESTS PASSED ({passed}/{passed + failed})")
        print("=" * 80)
        print("\nMPE Implementation: VALIDATED")
        print("\nKey Capabilities Tested:")
        print("  ✅ MPE creation and ID generation")
        print("  ✅ Content hash verification (tampering detection)")
        print("  ✅ Trust-based sender verification")
        print("  ✅ Financial message trust thresholds")
        print("  ✅ Account change blocking (expert-level required)")
        print("  ✅ Thread/conversation tracking")
        print("  ✅ Device and software attribution")
        print("  ✅ Multiple message types (email, API, chat)")
        print("  ✅ Serialization (dict/JSON)")
        print("  ✅ Complete BEC attack prevention")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{passed + failed} passed)")
        print("=" * 80)
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
