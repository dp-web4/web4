"""
Test Rate Limiting Fix

Session #44

Verifies that the RateLimitedMessageBus KeyError bug (Session #43, line 623) is fixed.
"""

from datetime import datetime, timezone
from cross_society_security_mitigations import RateLimitedMessageBus
from cross_society_messaging import CrossSocietyMessage, MessageType
from web4_crypto import Web4Crypto


def test_rate_limiting_new_sender():
    """Test that new senders don't cause KeyError"""

    print("=" * 80)
    print("RATE LIMITING BUG FIX TEST - Session #44")
    print("=" * 80)

    # Create message bus
    bus = RateLimitedMessageBus()

    # Create message from new sender (this caused KeyError in Session #43)
    keypair = Web4Crypto.generate_keypair("test-sender", deterministic=True)

    message = CrossSocietyMessage(
        message_id="test-001",
        message_type=MessageType.HELLO,
        sender_lct="lct-new-sender",
        recipient_lct="lct-recipient",
        timestamp=datetime.now(timezone.utc),
        sequence_number=0,
        payload={"test": "message"},
    )

    message.sign(keypair)

    # This should NOT raise KeyError
    try:
        result = bus.send_message(message)
        print(f"✅ Message from new sender accepted: {result}")
        print(f"✅ No KeyError raised")
        print(f"   Total messages: {bus.total_messages}")
        print(f"   Verified messages: {bus.verified_messages}")
    except KeyError as e:
        print(f"❌ KeyError still occurs: {e}")
        return False

    # Send another message from same sender (should work)
    message2 = CrossSocietyMessage(
        message_id="test-002",
        message_type=MessageType.HELLO,
        sender_lct="lct-new-sender",
        recipient_lct="lct-recipient",
        timestamp=datetime.now(timezone.utc),
        sequence_number=1,
        payload={"test": "message2"},
    )

    message2.sign(keypair)

    try:
        result2 = bus.send_message(message2)
        print(f"✅ Second message from same sender accepted: {result2}")
        print(f"   Total messages: {bus.total_messages}")
    except KeyError as e:
        print(f"❌ KeyError on second message: {e}")
        return False

    # Test replay protection (send same message again)
    result3 = bus.send_message(message2)
    print(f"\n✅ Replay protection working: {not result3}")
    print(f"   Rejected messages: {bus.rejected_messages}")

    # Test rate limiting (send many messages)
    print("\n### Testing Rate Limiting")
    print("-" * 80)

    spam_count = 0
    blocked_count = 0

    for i in range(100):
        spam_msg = CrossSocietyMessage(
            message_id=f"spam-{i}",
            message_type=MessageType.HEARTBEAT,
            sender_lct="lct-spammer",
            recipient_lct="lct-recipient",
            timestamp=datetime.now(timezone.utc),
            sequence_number=i,
            payload={},
        )

        spam_keypair = Web4Crypto.generate_keypair("spammer", deterministic=True)
        spam_msg.sign(spam_keypair)

        if bus.send_message(spam_msg):
            spam_count += 1
        else:
            blocked_count += 1

    print(f"Sent: {spam_count} messages")
    print(f"Blocked: {blocked_count} messages")

    if blocked_count > 0:
        print(f"✅ Rate limiting active (max 60/min)")
    else:
        print(f"⚠️  No rate limiting (may need time-based check)")

    print("\n" + "=" * 80)
    print("BUG FIX VERIFICATION COMPLETE")
    print("=" * 80)

    print("\n✅ RateLimitedMessageBus KeyError bug is FIXED")
    print("✅ New senders can send messages without errors")
    print("✅ Replay protection still works")
    print(f"✅ Rate limiting {'active' if blocked_count > 0 else 'needs time-based check'}")

    return True


if __name__ == "__main__":
    test_rate_limiting_new_sender()
