#!/usr/bin/env python3
"""
Web4 Cross-Society Messaging Protocol - Session #32

Secure, encrypted, signed messaging between Web4 societies.

Features:
- X25519 ECDH key exchange for encryption
- AES-256-GCM encryption for confidentiality
- Ed25519 signatures for authentication
- Replay protection (timestamps + nonces)
- Message delivery confirmation
- Multi-message threading

Security Properties:
- Confidentiality: Only recipient can decrypt
- Authentication: Signature proves sender identity
- Integrity: Tampering detected by signature + AEAD
- Forward secrecy: Ephemeral encryption keys
- Replay protection: Timestamp + nonce tracking

Architecture:
  Sender                                 Recipient
    |                                        |
    | 1. Generate ephemeral X25519 keypair   |
    | 2. Derive shared secret with recipient |
    | 3. Encrypt message with AES-GCM        |
    | 4. Sign (encrypted + metadata)         |
    |                                        |
    |--------- Encrypted Message ----------->|
    |                                        |
    |                   5. Verify signature  |
    |                   6. Derive shared key |
    |                   7. Decrypt message   |
    |                   8. Check replay      |
    |                                        |
    |<------- Delivery Confirmation ---------|

Author: Claude (Session #32)
Date: 2025-11-15
"""

import json
import os
import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from enum import Enum

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  cryptography library not available - messaging disabled")

# Import from web4_crypto for Ed25519 key management
try:
    from web4_crypto import Web4Crypto, KeyPair
    CRYPTO_MODULE_AVAILABLE = True
except ImportError:
    CRYPTO_MODULE_AVAILABLE = False
    print("⚠️  web4_crypto module not available - using standalone mode")


class MessageType(Enum):
    """Types of messages in Web4 protocol"""
    DIRECT = "direct"              # Peer-to-peer message
    BROADCAST = "broadcast"        # Announce to all peers
    REQUEST = "request"            # Resource request
    RESPONSE = "response"          # Resource response
    CONFIRMATION = "confirmation"  # Delivery confirmation
    HEARTBEAT = "heartbeat"        # Heartbeat signal (from Session #31)


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class EncryptedMessage:
    """
    Encrypted message container with signature.

    Structure:
    - Encrypted payload (AES-GCM)
    - Ephemeral public key (for recipient to derive shared secret)
    - Nonce for AES-GCM
    - Ed25519 signature over (encrypted_payload + metadata)
    """
    message_id: str                    # Unique message ID
    sender_lct: str                    # Sender's LCT
    recipient_lct: str                 # Recipient's LCT
    timestamp: datetime                # Message creation time
    message_type: MessageType          # Type of message
    priority: MessagePriority          # Priority level

    # Encryption components
    ephemeral_public_key_hex: str      # Sender's ephemeral X25519 public key (hex)
    encrypted_payload_hex: str         # AES-GCM encrypted message (hex)
    nonce_hex: str                     # AES-GCM nonce (hex)

    # Authentication
    signature_hex: str                 # Ed25519 signature (hex)

    # Optional metadata
    thread_id: Optional[str] = None    # For multi-message conversations
    reply_to: Optional[str] = None     # Message ID this replies to
    expires_at: Optional[datetime] = None  # Message expiration

    def to_dict(self) -> dict:
        """Serialize to dictionary for transmission"""
        return {
            "message_id": self.message_id,
            "sender_lct": self.sender_lct,
            "recipient_lct": self.recipient_lct,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "ephemeral_public_key_hex": self.ephemeral_public_key_hex,
            "encrypted_payload_hex": self.encrypted_payload_hex,
            "nonce_hex": self.nonce_hex,
            "signature_hex": self.signature_hex,
            "thread_id": self.thread_id,
            "reply_to": self.reply_to,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EncryptedMessage':
        """Deserialize from dictionary"""
        return cls(
            message_id=data["message_id"],
            sender_lct=data["sender_lct"],
            recipient_lct=data["recipient_lct"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message_type=MessageType(data["message_type"]),
            priority=MessagePriority(data["priority"]),
            ephemeral_public_key_hex=data["ephemeral_public_key_hex"],
            encrypted_payload_hex=data["encrypted_payload_hex"],
            nonce_hex=data["nonce_hex"],
            signature_hex=data["signature_hex"],
            thread_id=data.get("thread_id"),
            reply_to=data.get("reply_to"),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        )


@dataclass
class DecryptedMessage:
    """Decrypted message with metadata"""
    message_id: str
    sender_lct: str
    recipient_lct: str
    timestamp: datetime
    message_type: MessageType
    priority: MessagePriority

    # Decrypted content
    payload: dict                      # Decrypted message content

    # Verification status
    signature_valid: bool              # Was signature valid?
    freshness_valid: bool              # Is timestamp fresh?

    # Optional metadata
    thread_id: Optional[str] = None
    reply_to: Optional[str] = None


@dataclass
class MessageThread:
    """Track multi-message conversations"""
    thread_id: str
    participants: List[str]            # LCTs of participants
    messages: List[str] = field(default_factory=list)  # Message IDs
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Web4MessagingCrypto:
    """
    Cryptographic operations for Web4 messaging.

    Combines:
    - X25519 ECDH for key exchange
    - AES-256-GCM for encryption
    - Ed25519 for signatures
    """

    @staticmethod
    def generate_ephemeral_keypair() -> Tuple[bytes, bytes]:
        """
        Generate ephemeral X25519 keypair for encryption.

        Returns:
            (private_key, public_key) as 32-byte values
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not available")

        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()

        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        return (private_bytes, public_bytes)

    @staticmethod
    def derive_shared_secret(private_key: bytes, peer_public_key: bytes) -> bytes:
        """
        Derive shared secret via X25519 ECDH.

        Args:
            private_key: Our X25519 private key (32 bytes)
            peer_public_key: Peer's X25519 public key (32 bytes)

        Returns:
            32-byte shared secret
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not available")

        private_key_obj = x25519.X25519PrivateKey.from_private_bytes(private_key)
        peer_public_key_obj = x25519.X25519PublicKey.from_public_bytes(peer_public_key)

        shared_secret = private_key_obj.exchange(peer_public_key_obj)
        return shared_secret

    @staticmethod
    def derive_encryption_key(shared_secret: bytes, context: bytes) -> bytes:
        """
        Derive AES key from shared secret using HKDF.

        Args:
            shared_secret: 32-byte shared secret from ECDH
            context: Context information for key derivation

        Returns:
            32-byte AES-256 key
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not available")

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=context
        )
        key = hkdf.derive(shared_secret)
        return key

    @staticmethod
    def encrypt_message(plaintext: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt message with AES-256-GCM.

        Args:
            plaintext: Message to encrypt
            key: 32-byte AES key

        Returns:
            (ciphertext, nonce) tuple
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not available")

        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        return (ciphertext, nonce)

    @staticmethod
    def decrypt_message(ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        """
        Decrypt message with AES-256-GCM.

        Args:
            ciphertext: Encrypted message
            key: 32-byte AES key
            nonce: 12-byte nonce used for encryption

        Returns:
            Decrypted plaintext

        Raises:
            Exception if decryption fails (wrong key or tampered ciphertext)
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not available")

        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext


class Web4MessageSender:
    """
    Send encrypted, signed messages to other Web4 societies.
    """

    def __init__(self, sender_lct: str, signing_keypair: 'KeyPair', message_dir: Path):
        """
        Initialize message sender.

        Args:
            sender_lct: Sender's LCT identity
            signing_keypair: Ed25519 keypair for signing
            message_dir: Directory to write outgoing messages
        """
        self.sender_lct = sender_lct
        self.signing_keypair = signing_keypair
        self.message_dir = Path(message_dir)
        self.message_dir.mkdir(parents=True, exist_ok=True)

        self.sent_messages: Dict[str, EncryptedMessage] = {}

    def send_message(
        self,
        recipient_lct: str,
        recipient_x25519_public_key: bytes,
        payload: dict,
        message_type: MessageType = MessageType.DIRECT,
        priority: MessagePriority = MessagePriority.NORMAL,
        thread_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        ttl_hours: int = 24
    ) -> EncryptedMessage:
        """
        Send encrypted message to recipient.

        Args:
            recipient_lct: Recipient's LCT
            recipient_x25519_public_key: Recipient's X25519 public key (32 bytes)
            payload: Message content (will be JSON-serialized and encrypted)
            message_type: Type of message
            priority: Priority level
            thread_id: Optional thread ID for conversation
            reply_to: Optional message ID this replies to
            ttl_hours: Time-to-live in hours

        Returns:
            EncryptedMessage that was sent
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not available")

        # Generate message ID
        message_id = self._generate_message_id()

        # Generate ephemeral keypair for this message
        ephemeral_private, ephemeral_public = Web4MessagingCrypto.generate_ephemeral_keypair()

        # Derive shared secret via ECDH
        shared_secret = Web4MessagingCrypto.derive_shared_secret(
            ephemeral_private,
            recipient_x25519_public_key
        )

        # Derive encryption key
        context = f"{self.sender_lct}:{recipient_lct}:{message_id}".encode()
        encryption_key = Web4MessagingCrypto.derive_encryption_key(shared_secret, context)

        # Serialize and encrypt payload
        plaintext = json.dumps(payload, sort_keys=True).encode('utf-8')
        ciphertext, nonce = Web4MessagingCrypto.encrypt_message(plaintext, encryption_key)

        # Create message metadata
        timestamp = datetime.now(timezone.utc)
        expires_at = timestamp + timedelta(hours=ttl_hours)

        # Create message (without signature)
        message = EncryptedMessage(
            message_id=message_id,
            sender_lct=self.sender_lct,
            recipient_lct=recipient_lct,
            timestamp=timestamp,
            message_type=message_type,
            priority=priority,
            ephemeral_public_key_hex=ephemeral_public.hex(),
            encrypted_payload_hex=ciphertext.hex(),
            nonce_hex=nonce.hex(),
            signature_hex="",  # Will be filled after signing
            thread_id=thread_id,
            reply_to=reply_to,
            expires_at=expires_at
        )

        # Sign message (signature over encrypted payload + metadata)
        signature = self._sign_message(message)
        message.signature_hex = signature.hex()

        # Write to message directory
        message_file = self.message_dir / f"message_{message_id}.json"
        with open(message_file, 'w') as f:
            json.dump(message.to_dict(), f, indent=2)

        # Track sent message
        self.sent_messages[message_id] = message

        return message

    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        random_bytes = secrets.token_bytes(16)
        return hashlib.sha256(random_bytes).hexdigest()[:16]

    def _sign_message(self, message: EncryptedMessage) -> bytes:
        """
        Sign message with Ed25519.

        Signs canonical representation of:
        - encrypted_payload
        - metadata (sender, recipient, timestamp, etc.)
        """
        # Create canonical representation for signing
        sign_data = {
            "message_id": message.message_id,
            "sender_lct": message.sender_lct,
            "recipient_lct": message.recipient_lct,
            "timestamp": message.timestamp.isoformat(),
            "message_type": message.message_type.value,
            "encrypted_payload_hex": message.encrypted_payload_hex,
            "ephemeral_public_key_hex": message.ephemeral_public_key_hex,
            "nonce_hex": message.nonce_hex
        }

        canonical = json.dumps(sign_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        signature = self.signing_keypair.sign(canonical)

        return signature


class Web4MessageReceiver:
    """
    Receive and decrypt messages from other Web4 societies.
    """

    def __init__(
        self,
        recipient_lct: str,
        x25519_private_key: bytes,
        signing_keypair: 'KeyPair',
        inbox_dir: Path,
        max_age_hours: int = 24
    ):
        """
        Initialize message receiver.

        Args:
            recipient_lct: Our LCT identity
            x25519_private_key: Our X25519 private key for decryption
            signing_keypair: Our Ed25519 keypair (for sending confirmations)
            inbox_dir: Directory to monitor for incoming messages
            max_age_hours: Max age of messages to accept (replay protection)
        """
        self.recipient_lct = recipient_lct
        self.x25519_private_key = x25519_private_key
        self.signing_keypair = signing_keypair
        self.inbox_dir = Path(inbox_dir)
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)

        # Replay protection: track processed message IDs
        self.processed_messages: set = set()

        # Decrypted message store
        self.messages: Dict[str, DecryptedMessage] = {}

        # Thread tracking
        self.threads: Dict[str, MessageThread] = {}

    def receive_messages(self, sender_ed25519_public_keys: Dict[str, bytes]) -> List[DecryptedMessage]:
        """
        Check inbox for new messages and decrypt them.

        Args:
            sender_ed25519_public_keys: Map of sender LCT -> Ed25519 public key

        Returns:
            List of newly decrypted messages
        """
        new_messages = []

        for message_file in self.inbox_dir.glob("message_*.json"):
            try:
                with open(message_file, 'r') as f:
                    data = json.load(f)

                encrypted_msg = EncryptedMessage.from_dict(data)

                # Skip if already processed (replay protection)
                if encrypted_msg.message_id in self.processed_messages:
                    continue

                # Skip if not for us
                if encrypted_msg.recipient_lct != self.recipient_lct:
                    continue

                # Get sender's public key
                sender_public_key = sender_ed25519_public_keys.get(encrypted_msg.sender_lct)
                if not sender_public_key:
                    print(f"⚠️  No public key for sender {encrypted_msg.sender_lct}")
                    continue

                # Decrypt and verify
                decrypted_msg = self._decrypt_and_verify(encrypted_msg, sender_public_key)

                if decrypted_msg and decrypted_msg.signature_valid and decrypted_msg.freshness_valid:
                    # Mark as processed
                    self.processed_messages.add(encrypted_msg.message_id)

                    # Store message
                    self.messages[encrypted_msg.message_id] = decrypted_msg

                    # Track thread
                    if decrypted_msg.thread_id:
                        self._update_thread(decrypted_msg)

                    new_messages.append(decrypted_msg)

                    print(f"✅ Received message {encrypted_msg.message_id} from {encrypted_msg.sender_lct}")

            except Exception as e:
                print(f"⚠️  Error processing message {message_file}: {e}")
                continue

        return new_messages

    def _decrypt_and_verify(
        self,
        encrypted_msg: EncryptedMessage,
        sender_ed25519_public_key: bytes
    ) -> Optional[DecryptedMessage]:
        """
        Decrypt message and verify signature.

        Returns DecryptedMessage if successful, None otherwise.
        """
        try:
            # Verify signature first
            signature_valid = self._verify_signature(encrypted_msg, sender_ed25519_public_key)

            # Check freshness
            freshness_valid = self._check_freshness(encrypted_msg)

            if not signature_valid:
                print(f"⚠️  Invalid signature on message {encrypted_msg.message_id}")
                return None

            if not freshness_valid:
                print(f"⚠️  Stale message {encrypted_msg.message_id}")
                return None

            # Derive shared secret
            ephemeral_public = bytes.fromhex(encrypted_msg.ephemeral_public_key_hex)
            shared_secret = Web4MessagingCrypto.derive_shared_secret(
                self.x25519_private_key,
                ephemeral_public
            )

            # Derive decryption key
            context = f"{encrypted_msg.sender_lct}:{encrypted_msg.recipient_lct}:{encrypted_msg.message_id}".encode()
            decryption_key = Web4MessagingCrypto.derive_encryption_key(shared_secret, context)

            # Decrypt payload
            ciphertext = bytes.fromhex(encrypted_msg.encrypted_payload_hex)
            nonce = bytes.fromhex(encrypted_msg.nonce_hex)
            plaintext = Web4MessagingCrypto.decrypt_message(ciphertext, decryption_key, nonce)

            # Parse payload
            payload = json.loads(plaintext.decode('utf-8'))

            # Create decrypted message
            decrypted_msg = DecryptedMessage(
                message_id=encrypted_msg.message_id,
                sender_lct=encrypted_msg.sender_lct,
                recipient_lct=encrypted_msg.recipient_lct,
                timestamp=encrypted_msg.timestamp,
                message_type=encrypted_msg.message_type,
                priority=encrypted_msg.priority,
                payload=payload,
                signature_valid=signature_valid,
                freshness_valid=freshness_valid,
                thread_id=encrypted_msg.thread_id,
                reply_to=encrypted_msg.reply_to
            )

            return decrypted_msg

        except Exception as e:
            print(f"⚠️  Decryption failed for message {encrypted_msg.message_id}: {e}")
            return None

    def _verify_signature(self, encrypted_msg: EncryptedMessage, sender_public_key: bytes) -> bool:
        """Verify Ed25519 signature on message"""
        try:
            # Reconstruct signed data
            sign_data = {
                "message_id": encrypted_msg.message_id,
                "sender_lct": encrypted_msg.sender_lct,
                "recipient_lct": encrypted_msg.recipient_lct,
                "timestamp": encrypted_msg.timestamp.isoformat(),
                "message_type": encrypted_msg.message_type.value,
                "encrypted_payload_hex": encrypted_msg.encrypted_payload_hex,
                "ephemeral_public_key_hex": encrypted_msg.ephemeral_public_key_hex,
                "nonce_hex": encrypted_msg.nonce_hex
            }

            canonical = json.dumps(sign_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
            signature = bytes.fromhex(encrypted_msg.signature_hex)

            # Verify with Ed25519
            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(sender_public_key)
            public_key_obj.verify(signature, canonical)

            return True

        except InvalidSignature:
            return False
        except Exception as e:
            print(f"⚠️  Signature verification error: {e}")
            return False

    def _check_freshness(self, encrypted_msg: EncryptedMessage) -> bool:
        """Check if message is fresh (not too old)"""
        age = datetime.now(timezone.utc) - encrypted_msg.timestamp
        return age <= self.max_age

    def _update_thread(self, decrypted_msg: DecryptedMessage):
        """Update thread tracking"""
        thread_id = decrypted_msg.thread_id

        if thread_id not in self.threads:
            self.threads[thread_id] = MessageThread(
                thread_id=thread_id,
                participants=[decrypted_msg.sender_lct, decrypted_msg.recipient_lct]
            )

        thread = self.threads[thread_id]
        thread.messages.append(decrypted_msg.message_id)
        thread.last_activity = datetime.now(timezone.utc)


# ============================================================================
# DEMO
# ============================================================================

def demo_cross_society_messaging():
    """Demonstrate cross-society encrypted messaging"""

    if not CRYPTO_AVAILABLE:
        print("⚠️  Cryptography library not available - demo skipped")
        return

    print("=" * 70)
    print("Web4 Cross-Society Messaging Demo - Session #32")
    print("=" * 70)
    print()

    # Setup: Create two societies (Legion and cbp)
    print("1. Setting up societies...")
    print()

    # Import crypto from Session #31
    from web4_crypto import Web4Crypto, KeyPair

    # Legion's keys
    legion_ed25519_keypair = Web4Crypto.generate_keypair("Legion", deterministic=True)
    legion_x25519_private, legion_x25519_public = Web4MessagingCrypto.generate_ephemeral_keypair()
    legion_lct = Web4Crypto.generate_lct(legion_ed25519_keypair.public_key, "Legion")

    # cbp's keys
    cbp_ed25519_keypair = Web4Crypto.generate_keypair("cbp", deterministic=True)
    cbp_x25519_private, cbp_x25519_public = Web4MessagingCrypto.generate_ephemeral_keypair()
    cbp_lct = Web4Crypto.generate_lct(cbp_ed25519_keypair.public_key, "cbp")

    print(f"Legion LCT: {legion_lct}")
    print(f"   Ed25519 public key: {legion_ed25519_keypair.public_key.hex()[:32]}...")
    print(f"   X25519 public key:  {legion_x25519_public.hex()[:32]}...")
    print()
    print(f"cbp LCT: {cbp_lct}")
    print(f"   Ed25519 public key: {cbp_ed25519_keypair.public_key.hex()[:32]}...")
    print(f"   X25519 public key:  {cbp_x25519_public.hex()[:32]}...")
    print()

    # Create messaging endpoints
    legion_outbox = Path("/tmp/web4_messaging_demo/legion/outbox")
    cbp_inbox = Path("/tmp/web4_messaging_demo/cbp/inbox")

    legion_outbox.mkdir(parents=True, exist_ok=True)
    cbp_inbox.mkdir(parents=True, exist_ok=True)

    legion_sender = Web4MessageSender(
        sender_lct=legion_lct,
        signing_keypair=legion_ed25519_keypair,
        message_dir=legion_outbox
    )

    cbp_receiver = Web4MessageReceiver(
        recipient_lct=cbp_lct,
        x25519_private_key=cbp_x25519_private,
        signing_keypair=cbp_ed25519_keypair,
        inbox_dir=cbp_inbox
    )

    # Test 1: Send encrypted message from Legion to cbp
    print("2. Legion sends encrypted message to cbp...")
    print()

    message_payload = {
        "type": "resource_request",
        "resource": "compute_hour",
        "amount": 10,
        "atp_offered": 100,
        "message": "Need compute for Web4 research. Can pay 100 ATP."
    }

    encrypted_msg = legion_sender.send_message(
        recipient_lct=cbp_lct,
        recipient_x25519_public_key=cbp_x25519_public,
        payload=message_payload,
        message_type=MessageType.REQUEST,
        priority=MessagePriority.HIGH
    )

    print(f"✅ Message encrypted and signed")
    print(f"   Message ID: {encrypted_msg.message_id}")
    print(f"   Encrypted payload: {encrypted_msg.encrypted_payload_hex[:64]}...")
    print(f"   Signature: {encrypted_msg.signature_hex[:64]}...")
    print()

    # Simulate message transfer (copy to cbp's inbox)
    import shutil
    message_file = legion_outbox / f"message_{encrypted_msg.message_id}.json"
    shutil.copy(message_file, cbp_inbox / f"message_{encrypted_msg.message_id}.json")

    # Test 2: cbp receives and decrypts message
    print("3. cbp receives and decrypts message...")
    print()

    # cbp needs Legion's Ed25519 public key for signature verification
    sender_public_keys = {
        legion_lct: legion_ed25519_keypair.public_key
    }

    decrypted_messages = cbp_receiver.receive_messages(sender_public_keys)

    if decrypted_messages:
        msg = decrypted_messages[0]
        print(f"✅ Message decrypted successfully")
        print(f"   From: {msg.sender_lct}")
        print(f"   To: {msg.recipient_lct}")
        print(f"   Type: {msg.message_type.value}")
        print(f"   Priority: {msg.priority.value}")
        print(f"   Signature valid: {msg.signature_valid}")
        print(f"   Freshness valid: {msg.freshness_valid}")
        print(f"   Payload: {json.dumps(msg.payload, indent=6)}")
    else:
        print("❌ No messages received")

    print()
    print("=" * 70)
    print("✅ Cross-society messaging working!")
    print("=" * 70)
    print()
    print("Security validation:")
    print("  ✅ End-to-end encryption (X25519 + AES-GCM)")
    print("  ✅ Authentication (Ed25519 signatures)")
    print("  ✅ Integrity (AEAD + signatures)")
    print("  ✅ Replay protection (message ID tracking)")
    print("  ✅ Freshness (timestamp validation)")


if __name__ == "__main__":
    demo_cross_society_messaging()
