#!/usr/bin/env python3
"""
Web4 Messaging Security Test Suite - Session #32

Comprehensive security validation for cross-society messaging:
1. Eavesdropping resistance (encryption)
2. MITM attack prevention (signature verification)
3. Replay attack prevention (message ID tracking)
4. Message tampering detection
5. Key compromise scenarios

Author: Claude (Session #32)
Date: 2025-11-15
"""

import json
import asyncio
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
import secrets

from web4_messaging import (
    Web4MessageSender,
    Web4MessageReceiver,
    Web4MessagingCrypto,
    MessageType,
    MessagePriority,
    EncryptedMessage
)
from web4_crypto import Web4Crypto, KeyPair


class MessagingSecurityTests:
    """Security test suite for Web4 messaging"""

    def __init__(self):
        self.test_dir = Path("/tmp/web4_messaging_security_tests")
        self.setup_test_environment()

    def setup_test_environment(self):
        """Create clean test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # Create test societies
        self.legion_ed25519 = Web4Crypto.generate_keypair("Legion", deterministic=True)
        self.legion_x25519_private, self.legion_x25519_public = Web4MessagingCrypto.generate_ephemeral_keypair()
        self.legion_lct = Web4Crypto.generate_lct(self.legion_ed25519.public_key, "Legion")

        self.cbp_ed25519 = Web4Crypto.generate_keypair("cbp", deterministic=True)
        self.cbp_x25519_private, self.cbp_x25519_public = Web4MessagingCrypto.generate_ephemeral_keypair()
        self.cbp_lct = Web4Crypto.generate_lct(self.cbp_ed25519.public_key, "cbp")

        # Attacker keys
        self.attacker_ed25519 = Web4Crypto.generate_keypair("Attacker", deterministic=True)
        self.attacker_x25519_private, self.attacker_x25519_public = Web4MessagingCrypto.generate_ephemeral_keypair()
        self.attacker_lct = Web4Crypto.generate_lct(self.attacker_ed25519.public_key, "Attacker")

    async def test_eavesdropping_resistance(self):
        """
        Test 1: Eavesdropping Resistance

        Attack: Passive eavesdropper captures encrypted message.
        Defense: Only recipient with correct X25519 private key can decrypt.
        """
        print("\n" + "=" * 70)
        print("Test 1: Eavesdropping Resistance")
        print("=" * 70)

        # Setup
        legion_outbox = self.test_dir / "legion_outbox"
        cbp_inbox = self.test_dir / "cbp_inbox"
        legion_outbox.mkdir(parents=True, exist_ok=True)
        cbp_inbox.mkdir(parents=True, exist_ok=True)

        legion_sender = Web4MessageSender(
            sender_lct=self.legion_lct,
            signing_keypair=self.legion_ed25519,
            message_dir=legion_outbox
        )

        # Legion sends secret message to cbp
        secret_payload = {
            "secret": "This is a confidential resource allocation plan",
            "atp_budget": 10000,
            "targets": ["critical_research", "high_priority_compute"]
        }

        encrypted_msg = legion_sender.send_message(
            recipient_lct=self.cbp_lct,
            recipient_x25519_public_key=self.cbp_x25519_public,
            payload=secret_payload,
            message_type=MessageType.DIRECT,
            priority=MessagePriority.URGENT
        )

        print(f"\n📤 Legion sends secret message to cbp")
        print(f"   Message ID: {encrypted_msg.message_id}")
        print(f"   Encrypted: {encrypted_msg.encrypted_payload_hex[:64]}...")

        # ATTACK: Eavesdropper captures message
        message_file = legion_outbox / f"message_{encrypted_msg.message_id}.json"
        with open(message_file, 'r') as f:
            captured_data = json.load(f)

        print(f"\n🎭 Eavesdropper captures message")
        print(f"   Can see: sender_lct, recipient_lct, timestamp")
        print(f"   Cannot decrypt: {captured_data['encrypted_payload_hex'][:64]}...")

        # Try to decrypt without correct key (should fail)
        try:
            # Attacker tries with wrong X25519 key
            ephemeral_public = bytes.fromhex(captured_data['ephemeral_public_key_hex'])
            shared_secret = Web4MessagingCrypto.derive_shared_secret(
                self.attacker_x25519_private,  # WRONG KEY
                ephemeral_public
            )
            context = f"{encrypted_msg.sender_lct}:{encrypted_msg.recipient_lct}:{encrypted_msg.message_id}".encode()
            wrong_key = Web4MessagingCrypto.derive_encryption_key(shared_secret, context)

            ciphertext = bytes.fromhex(captured_data['encrypted_payload_hex'])
            nonce = bytes.fromhex(captured_data['nonce_hex'])

            # This should fail or produce garbage
            plaintext = Web4MessagingCrypto.decrypt_message(ciphertext, wrong_key, nonce)
            decrypted = json.loads(plaintext.decode('utf-8'))
            print(f"\n❌ VULNERABILITY: Attacker decrypted message!")
            print(f"   Decrypted: {decrypted}")
            return "FAILED"

        except Exception as e:
            print(f"\n✅ DEFENSE SUCCESSFUL!")
            print(f"   Attacker's decryption failed: {type(e).__name__}")
            print(f"   Message content remains confidential")

        # Legitimate recipient CAN decrypt
        cbp_receiver = Web4MessageReceiver(
            recipient_lct=self.cbp_lct,
            x25519_private_key=self.cbp_x25519_private,
            signing_keypair=self.cbp_ed25519,
            inbox_dir=cbp_inbox
        )

        shutil.copy(message_file, cbp_inbox / f"message_{encrypted_msg.message_id}.json")

        sender_keys = {self.legion_lct: self.legion_ed25519.public_key}
        decrypted_messages = cbp_receiver.receive_messages(sender_keys)

        if decrypted_messages and decrypted_messages[0].payload == secret_payload:
            print(f"\n✅ Legitimate recipient (cbp) decrypted successfully")
            print(f"   Secret message received intact")
            return "PASSED"
        else:
            print(f"\n❌ FAILED: Legitimate recipient couldn't decrypt")
            return "FAILED"

    async def test_mitm_attack_prevention(self):
        """
        Test 2: Man-in-the-Middle Attack Prevention

        Attack: MITM intercepts message, modifies it, re-encrypts with recipient's key.
        Defense: Signature verification detects modification.
        """
        print("\n" + "=" * 70)
        print("Test 2: MITM Attack Prevention")
        print("=" * 70)

        # Setup
        legion_outbox = self.test_dir / "legion_outbox_mitm"
        cbp_inbox = self.test_dir / "cbp_inbox_mitm"
        legion_outbox.mkdir(parents=True, exist_ok=True)
        cbp_inbox.mkdir(parents=True, exist_ok=True)

        legion_sender = Web4MessageSender(
            sender_lct=self.legion_lct,
            signing_keypair=self.legion_ed25519,
            message_dir=legion_outbox
        )

        # Legion sends legitimate message
        original_payload = {
            "action": "approve",
            "atp_transfer": 100
        }

        encrypted_msg = legion_sender.send_message(
            recipient_lct=self.cbp_lct,
            recipient_x25519_public_key=self.cbp_x25519_public,
            payload=original_payload,
            message_type=MessageType.REQUEST
        )

        print(f"\n📤 Legion sends: {original_payload}")

        # ATTACK: MITM intercepts and modifies
        message_file = legion_outbox / f"message_{encrypted_msg.message_id}.json"
        with open(message_file, 'r') as f:
            intercepted_data = json.load(f)

        print(f"\n🎭 MITM intercepts message")

        # Attacker modifies the encrypted payload
        # (Decrypt with Legion's intention, re-encrypt with malicious content)
        malicious_payload = {
            "action": "approve",
            "atp_transfer": 10000  # CHANGED: 100 -> 10000!
        }

        # MITM encrypts malicious payload with cbp's public key
        ephemeral_private, ephemeral_public = Web4MessagingCrypto.generate_ephemeral_keypair()
        shared_secret = Web4MessagingCrypto.derive_shared_secret(
            ephemeral_private,
            self.cbp_x25519_public
        )
        context = f"{self.legion_lct}:{self.cbp_lct}:{encrypted_msg.message_id}".encode()
        malicious_key = Web4MessagingCrypto.derive_encryption_key(shared_secret, context)

        malicious_plaintext = json.dumps(malicious_payload, sort_keys=True).encode('utf-8')
        malicious_ciphertext, malicious_nonce = Web4MessagingCrypto.encrypt_message(
            malicious_plaintext,
            malicious_key
        )

        # Replace encrypted payload (but keep original signature!)
        intercepted_data['encrypted_payload_hex'] = malicious_ciphertext.hex()
        intercepted_data['ephemeral_public_key_hex'] = ephemeral_public.hex()
        intercepted_data['nonce_hex'] = malicious_nonce.hex()

        print(f"   Modified payload to: {malicious_payload}")
        print(f"   Kept Legion's signature (now invalid)")

        # Write modified message
        modified_file = cbp_inbox / f"message_{encrypted_msg.message_id}.json"
        with open(modified_file, 'w') as f:
            json.dump(intercepted_data, f)

        # cbp receives modified message
        cbp_receiver = Web4MessageReceiver(
            recipient_lct=self.cbp_lct,
            x25519_private_key=self.cbp_x25519_private,
            signing_keypair=self.cbp_ed25519,
            inbox_dir=cbp_inbox
        )

        sender_keys = {self.legion_lct: self.legion_ed25519.public_key}
        decrypted_messages = cbp_receiver.receive_messages(sender_keys)

        if not decrypted_messages:
            print(f"\n✅ DEFENSE SUCCESSFUL!")
            print(f"   Signature verification failed")
            print(f"   Modified message REJECTED")
            return "PASSED"
        else:
            print(f"\n❌ VULNERABILITY: Modified message accepted!")
            print(f"   Received: {decrypted_messages[0].payload}")
            return "FAILED"

    async def test_replay_attack_prevention(self):
        """
        Test 3: Replay Attack Prevention

        Attack: Capture old message and replay it later.
        Defense: Message ID tracking prevents duplicate processing.
        """
        print("\n" + "=" * 70)
        print("Test 3: Replay Attack Prevention")
        print("=" * 70)

        # Setup
        legion_outbox = self.test_dir / "legion_outbox_replay"
        cbp_inbox = self.test_dir / "cbp_inbox_replay"
        legion_outbox.mkdir(parents=True, exist_ok=True)
        cbp_inbox.mkdir(parents=True, exist_ok=True)

        legion_sender = Web4MessageSender(
            sender_lct=self.legion_lct,
            signing_keypair=self.legion_ed25519,
            message_dir=legion_outbox
        )

        cbp_receiver = Web4MessageReceiver(
            recipient_lct=self.cbp_lct,
            x25519_private_key=self.cbp_x25519_private,
            signing_keypair=self.cbp_ed25519,
            inbox_dir=cbp_inbox
        )

        # Send legitimate message
        payment_payload = {
            "action": "transfer_atp",
            "amount": 100,
            "recipient": self.cbp_lct
        }

        encrypted_msg = legion_sender.send_message(
            recipient_lct=self.cbp_lct,
            recipient_x25519_public_key=self.cbp_x25519_public,
            payload=payment_payload,
            message_type=MessageType.REQUEST
        )

        print(f"\n📤 Legion sends payment: {payment_payload}")

        # Deliver to cbp
        message_file = legion_outbox / f"message_{encrypted_msg.message_id}.json"
        shutil.copy(message_file, cbp_inbox / f"message_{encrypted_msg.message_id}.json")

        # First reception
        sender_keys = {self.legion_lct: self.legion_ed25519.public_key}
        first_batch = cbp_receiver.receive_messages(sender_keys)

        if first_batch:
            print(f"✅ cbp received first payment (legitimate)")
            print(f"   Message ID: {first_batch[0].message_id}")
            print(f"   Processed messages: {len(cbp_receiver.processed_messages)}")

        # ATTACK: Capture and replay same message
        print(f"\n🎭 Attacker captures message and replays it")

        with open(message_file, 'r') as f:
            captured_message = json.load(f)

        # Replay same message (try to get duplicate payment)
        replay_file = cbp_inbox / f"message_{encrypted_msg.message_id}_replayed.json"
        with open(replay_file, 'w') as f:
            json.dump(captured_message, f)

        # Second reception (replay attempt)
        second_batch = cbp_receiver.receive_messages(sender_keys)

        if not second_batch:
            print(f"\n✅ DEFENSE SUCCESSFUL!")
            print(f"   Replay detected via message ID tracking")
            print(f"   Duplicate message REJECTED")
            print(f"   No duplicate payment processed")
            return "PASSED"
        else:
            print(f"\n❌ VULNERABILITY: Replay succeeded!")
            print(f"   Duplicate payment accepted: {second_batch[0].payload}")
            return "FAILED"

    async def test_message_tampering_detection(self):
        """
        Test 4: Message Tampering Detection

        Attack: Modify message content (encrypted payload).
        Defense: AEAD authentication tag detects tampering.
        """
        print("\n" + "=" * 70)
        print("Test 4: Message Tampering Detection")
        print("=" * 70)

        # Setup
        legion_outbox = self.test_dir / "legion_outbox_tamper"
        cbp_inbox = self.test_dir / "cbp_inbox_tamper"
        legion_outbox.mkdir(parents=True, exist_ok=True)
        cbp_inbox.mkdir(parents=True, exist_ok=True)

        legion_sender = Web4MessageSender(
            sender_lct=self.legion_lct,
            signing_keypair=self.legion_ed25519,
            message_dir=legion_outbox
        )

        # Send message
        original_payload = {
            "vote": "approve",
            "proposal_id": "proposal_123"
        }

        encrypted_msg = legion_sender.send_message(
            recipient_lct=self.cbp_lct,
            recipient_x25519_public_key=self.cbp_x25519_public,
            payload=original_payload,
            message_type=MessageType.REQUEST
        )

        print(f"\n📤 Legion votes: {original_payload}")

        # ATTACK: Tamper with encrypted payload
        message_file = legion_outbox / f"message_{encrypted_msg.message_id}.json"
        with open(message_file, 'r') as f:
            data = json.load(f)

        print(f"\n🎭 Attacker tampers with encrypted payload")

        # Flip random bits in ciphertext
        ciphertext_bytes = bytes.fromhex(data['encrypted_payload_hex'])
        tampered_bytes = bytearray(ciphertext_bytes)
        tampered_bytes[10] ^= 0xFF  # Flip bits
        tampered_bytes[20] ^= 0xFF
        data['encrypted_payload_hex'] = tampered_bytes.hex()

        print(f"   Modified encrypted payload (flipped bits)")

        # Write tampered message
        tampered_file = cbp_inbox / f"message_{encrypted_msg.message_id}.json"
        with open(tampered_file, 'w') as f:
            json.dump(data, f)

        # cbp tries to receive
        cbp_receiver = Web4MessageReceiver(
            recipient_lct=self.cbp_lct,
            x25519_private_key=self.cbp_x25519_private,
            signing_keypair=self.cbp_ed25519,
            inbox_dir=cbp_inbox
        )

        sender_keys = {self.legion_lct: self.legion_ed25519.public_key}
        decrypted_messages = cbp_receiver.receive_messages(sender_keys)

        if not decrypted_messages:
            print(f"\n✅ DEFENSE SUCCESSFUL!")
            print(f"   AES-GCM authentication detected tampering")
            print(f"   Tampered message REJECTED")
            return "PASSED"
        else:
            print(f"\n❌ VULNERABILITY: Tampered message accepted!")
            print(f"   Received: {decrypted_messages[0].payload}")
            return "FAILED"

    async def test_sender_spoofing_prevention(self):
        """
        Test 5: Sender Spoofing Prevention

        Attack: Attacker claims to be Legion, signs with own key.
        Defense: Signature verification with Legion's public key fails.
        """
        print("\n" + "=" * 70)
        print("Test 5: Sender Spoofing Prevention")
        print("=" * 70)

        # Setup
        attacker_outbox = self.test_dir / "attacker_outbox"
        cbp_inbox = self.test_dir / "cbp_inbox_spoof"
        attacker_outbox.mkdir(parents=True, exist_ok=True)
        cbp_inbox.mkdir(parents=True, exist_ok=True)

        # ATTACK: Attacker creates sender claiming to be Legion
        attacker_sender = Web4MessageSender(
            sender_lct=self.legion_lct,  # SPOOFED: Claims to be Legion
            signing_keypair=self.attacker_ed25519,  # But signs with attacker's key
            message_dir=attacker_outbox
        )

        malicious_payload = {
            "action": "transfer_all_atp",
            "recipient": self.attacker_lct,
            "message": "This is totally from Legion, trust me"
        }

        print(f"\n🎭 Attacker spoofs message from Legion")
        print(f"   Claims to be: {self.legion_lct}")
        print(f"   Actually signs with: Attacker's key")
        print(f"   Malicious payload: {malicious_payload}")

        spoofed_msg = attacker_sender.send_message(
            recipient_lct=self.cbp_lct,
            recipient_x25519_public_key=self.cbp_x25519_public,
            payload=malicious_payload,
            message_type=MessageType.REQUEST,
            priority=MessagePriority.URGENT
        )

        # Deliver to cbp
        message_file = attacker_outbox / f"message_{spoofed_msg.message_id}.json"
        shutil.copy(message_file, cbp_inbox / f"message_{spoofed_msg.message_id}.json")

        # cbp receives with Legion's REAL public key
        cbp_receiver = Web4MessageReceiver(
            recipient_lct=self.cbp_lct,
            x25519_private_key=self.cbp_x25519_private,
            signing_keypair=self.cbp_ed25519,
            inbox_dir=cbp_inbox
        )

        sender_keys = {
            self.legion_lct: self.legion_ed25519.public_key  # Legion's REAL key
        }

        decrypted_messages = cbp_receiver.receive_messages(sender_keys)

        if not decrypted_messages:
            print(f"\n✅ DEFENSE SUCCESSFUL!")
            print(f"   Signature verification failed")
            print(f"   Spoofed message REJECTED")
            print(f"   Attacker cannot impersonate Legion")
            return "PASSED"
        else:
            print(f"\n❌ VULNERABILITY: Spoofed message accepted!")
            print(f"   Received: {decrypted_messages[0].payload}")
            return "FAILED"


async def run_all_tests():
    """Run complete security test suite"""
    print("=" * 70)
    print("WEB4 MESSAGING SECURITY TEST SUITE - Session #32")
    print("=" * 70)

    tests = MessagingSecurityTests()

    results = {
        "Eavesdropping Resistance": await tests.test_eavesdropping_resistance(),
        "MITM Attack Prevention": await tests.test_mitm_attack_prevention(),
        "Replay Attack Prevention": await tests.test_replay_attack_prevention(),
        "Message Tampering Detection": await tests.test_message_tampering_detection(),
        "Sender Spoofing Prevention": await tests.test_sender_spoofing_prevention()
    }

    # Summary
    print("\n" + "=" * 70)
    print("SECURITY TEST SUMMARY")
    print("=" * 70)

    for test_name, result in results.items():
        status = "✅ PASSED" if result == "PASSED" else "❌ FAILED"
        print(f"  {test_name:40s} {status}")

    print()

    all_passed = all(r == "PASSED" for r in results.values())

    if all_passed:
        print("🔐 ALL SECURITY TESTS PASSED!")
        print()
        print("Validated:")
        print("  ✅ Eavesdropping resistance (X25519 + AES-GCM encryption)")
        print("  ✅ MITM prevention (Ed25519 signature verification)")
        print("  ✅ Replay prevention (message ID tracking)")
        print("  ✅ Tamper detection (AEAD authentication)")
        print("  ✅ Spoofing prevention (public key verification)")
        print()
        print("Web4 messaging is cryptographically secure!")
    else:
        print("⚠️  SOME TESTS FAILED - VULNERABILITIES DETECTED")

    return all_passed


if __name__ == "__main__":
    asyncio.run(run_all_tests())
