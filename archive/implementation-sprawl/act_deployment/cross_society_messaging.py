"""
Cross-Society Messaging and Coordination - Session #41

Enables secure communication and coordination between multiple Web4 societies.

Key Features:
- Cryptographically signed messages
- Cross-society trust verification
- ATP exchange protocol
- Reputation propagation across society boundaries
- Multi-party coordination primitives

This builds on:
- Session #31: Cryptographic primitives
- Session #36: Energy-backed ATP
- Session #40: Hardened security system

Architecture:
  Society A <--messages--> Message Bus <--messages--> Society B
      |                                                      |
      +-- Trust verification                                |
      +-- ATP exchange                                      |
      +-- Reputation sync <--------------------------------+
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from enum import Enum
import hashlib
import json

# Crypto imports
from web4_crypto import KeyPair, Web4Crypto


# ============================================================================
# Message Types
# ============================================================================

class MessageType(Enum):
    """Types of cross-society messages"""
    HELLO = "hello"                    # Society introduction
    HEARTBEAT = "heartbeat"            # Liveness signal
    TRUST_QUERY = "trust_query"        # Query trust score for LCT
    TRUST_RESPONSE = "trust_response"  # Trust score response
    ATP_OFFER = "atp_offer"            # Offer ATP for sale
    ATP_BID = "atp_bid"                # Bid to buy ATP
    ATP_TRANSFER = "atp_transfer"      # Execute ATP transfer
    WORK_REQUEST = "work_request"      # Request work from another society
    WORK_RESPONSE = "work_response"    # Response to work request
    REPUTATION_SHARE = "reputation_share"  # Share reputation data


# ============================================================================
# Message Structure
# ============================================================================

@dataclass
class CrossSocietyMessage:
    """
    Cryptographically signed message between societies.

    All cross-society communication uses this structure.
    """
    # Header
    message_id: str                    # Unique message ID
    message_type: MessageType          # Type of message
    sender_lct: str                    # Sending society LCT
    recipient_lct: str                 # Receiving society LCT (or "broadcast")
    timestamp: datetime                # When message was created
    sequence_number: int               # Monotonic sequence number

    # Payload
    payload: Dict                      # Message-specific data

    # Security
    signature: str = ""                # Ed25519 signature
    sender_pubkey: str = ""            # Sender's public key for verification

    def to_dict(self) -> Dict:
        """Serialize message for signing/transmission"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_lct": self.sender_lct,
            "recipient_lct": self.recipient_lct,
            "timestamp": self.timestamp.isoformat(),
            "sequence_number": self.sequence_number,
            "payload": self.payload,
        }

    def sign(self, keypair: KeyPair):
        """Sign message with society's private key"""
        message_bytes = json.dumps(self.to_dict(), sort_keys=True).encode()
        signature_bytes = keypair.sign(message_bytes)
        self.signature = signature_bytes.hex()
        self.sender_pubkey = keypair.public_key.hex()

    def verify(self) -> bool:
        """Verify message signature"""
        if not self.signature or not self.sender_pubkey:
            return False

        message_bytes = json.dumps(self.to_dict(), sort_keys=True).encode()
        try:
            signature_bytes = bytes.fromhex(self.signature)
            pubkey_bytes = bytes.fromhex(self.sender_pubkey)

            # Create a temporary keypair for verification
            temp_keypair = KeyPair(
                private_key=b'\x00' * 32,  # Dummy, only need public
                public_key=pubkey_bytes,
                society_name="temp"
            )
            return temp_keypair.verify(message_bytes, signature_bytes)
        except:
            return False

    @staticmethod
    def generate_id(sender_lct: str, sequence: int) -> str:
        """Generate unique message ID"""
        data = f"{sender_lct}:{sequence}:{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# ============================================================================
# Message Bus
# ============================================================================

class CrossSocietyMessageBus:
    """
    Decentralized message bus for cross-society communication.

    Architecture:
    - No central server (fully distributed)
    - Each society reads/writes messages to shared channel
    - Could be implemented as: filesystem, git repo, IPFS, libp2p, etc.
    - For now: simple in-memory message passing
    """

    def __init__(self):
        # Messages indexed by recipient
        self.messages: Dict[str, List[CrossSocietyMessage]] = {}

        # Sequence tracking (prevent replay attacks)
        self.seen_sequences: Dict[str, Set[int]] = {}

        # Statistics
        self.total_messages = 0
        self.verified_messages = 0
        self.rejected_messages = 0

    def send_message(self, message: CrossSocietyMessage) -> bool:
        """
        Send message to recipient society.

        Returns True if message accepted, False if rejected.
        """

        # Verify signature
        if not message.verify():
            print(f"[MESSAGE_BUS] Rejected unsigned/invalid message from {message.sender_lct}")
            self.rejected_messages += 1
            return False

        # Check for replay (sequence number reuse)
        sender = message.sender_lct
        if sender in self.seen_sequences:
            if message.sequence_number in self.seen_sequences[sender]:
                print(f"[MESSAGE_BUS] Rejected replay attack from {sender} (seq {message.sequence_number})")
                self.rejected_messages += 1
                return False
        else:
            self.seen_sequences[sender] = set()

        # Accept message
        self.seen_sequences[sender].add(message.sequence_number)

        recipient = message.recipient_lct
        if recipient not in self.messages:
            self.messages[recipient] = []

        self.messages[recipient].append(message)
        self.total_messages += 1
        self.verified_messages += 1

        return True

    def receive_messages(
        self,
        recipient_lct: str,
        message_type: Optional[MessageType] = None,
    ) -> List[CrossSocietyMessage]:
        """
        Receive messages for a society.

        Optionally filter by message type.
        """
        if recipient_lct not in self.messages:
            return []

        messages = self.messages[recipient_lct]

        if message_type:
            messages = [m for m in messages if m.message_type == message_type]

        return messages

    def get_stats(self) -> Dict:
        """Get message bus statistics"""
        return {
            "total_messages": self.total_messages,
            "verified_messages": self.verified_messages,
            "rejected_messages": self.rejected_messages,
            "verification_rate": self.verified_messages / max(1, self.total_messages),
        }


# ============================================================================
# Society Coordinator
# ============================================================================

class SocietyCoordinator:
    """
    Manages cross-society coordination for a single society.

    Responsibilities:
    - Send/receive messages via message bus
    - Maintain cross-society trust relationships
    - Coordinate ATP exchanges
    - Propagate reputation data
    """

    def __init__(
        self,
        society_lct: str,
        keypair: KeyPair,
        message_bus: CrossSocietyMessageBus,
    ):
        self.society_lct = society_lct
        self.keypair = keypair
        self.message_bus = message_bus

        # State
        self.sequence_number = 0
        self.known_societies: Set[str] = set()
        self.trust_cache: Dict[str, float] = {}  # lct -> trust score
        self.atp_offers: List[Dict] = []
        self.atp_bids: List[Dict] = []

    def send_hello(self, recipient_lct: str = "broadcast"):
        """Send HELLO message to introduce society"""
        message = CrossSocietyMessage(
            message_id=CrossSocietyMessage.generate_id(self.society_lct, self.sequence_number),
            message_type=MessageType.HELLO,
            sender_lct=self.society_lct,
            recipient_lct=recipient_lct,
            timestamp=datetime.now(timezone.utc),
            sequence_number=self.sequence_number,
            payload={
                "introduction": f"Hello from {self.society_lct}",
                "capabilities": ["atp_exchange", "work_requests", "trust_queries"],
            }
        )

        message.sign(self.keypair)
        self.sequence_number += 1

        success = self.message_bus.send_message(message)
        if success:
            print(f"[{self.society_lct}] Sent HELLO to {recipient_lct}")

        return success

    def send_trust_query(self, target_lct: str, query_about: str):
        """Query another society's trust score for a given LCT"""
        message = CrossSocietyMessage(
            message_id=CrossSocietyMessage.generate_id(self.society_lct, self.sequence_number),
            message_type=MessageType.TRUST_QUERY,
            sender_lct=self.society_lct,
            recipient_lct=target_lct,
            timestamp=datetime.now(timezone.utc),
            sequence_number=self.sequence_number,
            payload={
                "query_about": query_about,
                "context": "general",
            }
        )

        message.sign(self.keypair)
        self.sequence_number += 1

        success = self.message_bus.send_message(message)
        if success:
            print(f"[{self.society_lct}] Sent TRUST_QUERY to {target_lct} about {query_about}")

        return success

    def send_trust_response(self, requester_lct: str, query_about: str, trust_score: float):
        """Respond to trust query with trust score"""
        message = CrossSocietyMessage(
            message_id=CrossSocietyMessage.generate_id(self.society_lct, self.sequence_number),
            message_type=MessageType.TRUST_RESPONSE,
            sender_lct=self.society_lct,
            recipient_lct=requester_lct,
            timestamp=datetime.now(timezone.utc),
            sequence_number=self.sequence_number,
            payload={
                "query_about": query_about,
                "trust_score": trust_score,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        message.sign(self.keypair)
        self.sequence_number += 1

        success = self.message_bus.send_message(message)
        if success:
            print(f"[{self.society_lct}] Sent TRUST_RESPONSE to {requester_lct}: {trust_score:.2f}")

        return success

    def send_atp_offer(self, amount: float, price_per_atp: float):
        """Offer ATP for sale"""
        message = CrossSocietyMessage(
            message_id=CrossSocietyMessage.generate_id(self.society_lct, self.sequence_number),
            message_type=MessageType.ATP_OFFER,
            sender_lct=self.society_lct,
            recipient_lct="broadcast",
            timestamp=datetime.now(timezone.utc),
            sequence_number=self.sequence_number,
            payload={
                "amount_atp": amount,
                "price_per_atp": price_per_atp,
                "total_price": amount * price_per_atp,
                "currency": "external_currency",  # Could be fiat, other crypto, etc.
            }
        )

        message.sign(self.keypair)
        self.sequence_number += 1

        success = self.message_bus.send_message(message)
        if success:
            print(f"[{self.society_lct}] Offered {amount} ATP @ {price_per_atp} each")

        return success

    def process_messages(self):
        """Process incoming messages"""
        messages = self.message_bus.receive_messages(self.society_lct)

        for message in messages:
            # Record known society
            self.known_societies.add(message.sender_lct)

            # Handle by type
            if message.message_type == MessageType.HELLO:
                self._handle_hello(message)
            elif message.message_type == MessageType.TRUST_QUERY:
                self._handle_trust_query(message)
            elif message.message_type == MessageType.TRUST_RESPONSE:
                self._handle_trust_response(message)
            elif message.message_type == MessageType.ATP_OFFER:
                self._handle_atp_offer(message)

    def _handle_hello(self, message: CrossSocietyMessage):
        """Handle HELLO message"""
        print(f"[{self.society_lct}] Received HELLO from {message.sender_lct}")
        print(f"  Capabilities: {message.payload.get('capabilities', [])}")

    def _handle_trust_query(self, message: CrossSocietyMessage):
        """Handle trust query by sending trust score"""
        query_about = message.payload["query_about"]
        print(f"[{self.society_lct}] Received TRUST_QUERY from {message.sender_lct} about {query_about}")

        # In real system, would query actual trust graph
        # For demo, return random trust score
        trust_score = 0.7  # Default moderate trust

        self.send_trust_response(message.sender_lct, query_about, trust_score)

    def _handle_trust_response(self, message: CrossSocietyMessage):
        """Handle trust response by caching trust score"""
        query_about = message.payload["query_about"]
        trust_score = message.payload["trust_score"]

        print(f"[{self.society_lct}] Received TRUST_RESPONSE: {query_about} = {trust_score:.2f}")

        self.trust_cache[query_about] = trust_score

    def _handle_atp_offer(self, message: CrossSocietyMessage):
        """Handle ATP offer"""
        amount = message.payload["amount_atp"]
        price = message.payload["price_per_atp"]

        print(f"[{self.society_lct}] Received ATP_OFFER from {message.sender_lct}:")
        print(f"  Amount: {amount} ATP @ {price} each")

        self.atp_offers.append({
            "seller": message.sender_lct,
            "amount": amount,
            "price": price,
            "timestamp": message.timestamp,
        })


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("CROSS-SOCIETY MESSAGING - Session #41")
    print("Decentralized Coordination Between Web4 Societies")
    print("=" * 80)

    # Create message bus (shared infrastructure)
    message_bus = CrossSocietyMessageBus()

    # Create keypairs for societies
    sage_keypair = Web4Crypto.generate_keypair("sage", deterministic=True)
    legion_keypair = Web4Crypto.generate_keypair("legion", deterministic=True)
    cbp_keypair = Web4Crypto.generate_keypair("cbp", deterministic=True)

    # Create coordinators
    sage = SocietyCoordinator(
        society_lct="lct-sage-society",
        keypair=sage_keypair,
        message_bus=message_bus,
    )

    legion = SocietyCoordinator(
        society_lct="lct-legion-society",
        keypair=legion_keypair,
        message_bus=message_bus,
    )

    cbp = SocietyCoordinator(
        society_lct="lct-cbp-society",
        keypair=cbp_keypair,
        message_bus=message_bus,
    )

    # ========================================
    # Scenario 1: Society Discovery
    # ========================================

    print("\n### Scenario 1: Society Discovery (HELLO messages)")
    print("-" * 80)

    sage.send_hello()
    legion.send_hello()
    cbp.send_hello()

    # Each society processes HELLOs
    sage.process_messages()
    legion.process_messages()
    cbp.process_messages()

    print(f"\nSAGE knows: {sage.known_societies}")
    print(f"Legion knows: {legion.known_societies}")
    print(f"CBP knows: {cbp.known_societies}")

    # ========================================
    # Scenario 2: Cross-Society Trust Queries
    # ========================================

    print("\n### Scenario 2: Cross-Society Trust Queries")
    print("-" * 80)

    # Legion queries SAGE about Alice's trust
    legion.send_trust_query("lct-sage-society", "lct-alice")

    # SAGE processes query and responds
    sage.process_messages()

    # Legion receives trust score
    legion.process_messages()

    print(f"\nLegion's trust cache: {legion.trust_cache}")

    # ========================================
    # Scenario 3: ATP Market
    # ========================================

    print("\n### Scenario 3: ATP Marketplace")
    print("-" * 80)

    # SAGE offers ATP for sale
    sage.send_atp_offer(amount=1000.0, price_per_atp=0.01)

    # Legion offers ATP for sale
    legion.send_atp_offer(amount=500.0, price_per_atp=0.015)

    # CBP sees both offers
    cbp.process_messages()

    print(f"\nCBP sees ATP offers:")
    for offer in cbp.atp_offers:
        print(f"  {offer['seller']}: {offer['amount']} ATP @ {offer['price']}")

    # ========================================
    # Scenario 4: Message Bus Security
    # ========================================

    print("\n### Scenario 4: Message Bus Security (Signature Verification)")
    print("-" * 80)

    # Create legitimate message
    good_message = CrossSocietyMessage(
        message_id="test-001",
        message_type=MessageType.HELLO,
        sender_lct="lct-sage-society",
        recipient_lct="lct-legion-society",
        timestamp=datetime.now(timezone.utc),
        sequence_number=100,
        payload={"test": "legitimate"},
    )
    good_message.sign(sage_keypair)

    # Try to send legitimate message
    success1 = message_bus.send_message(good_message)
    print(f"Legitimate message: {'✓ Accepted' if success1 else '✗ Rejected'}")

    # Create unsigned message (attack)
    bad_message = CrossSocietyMessage(
        message_id="test-002",
        message_type=MessageType.HELLO,
        sender_lct="lct-attacker",
        recipient_lct="lct-legion-society",
        timestamp=datetime.now(timezone.utc),
        sequence_number=101,
        payload={"test": "malicious"},
    )
    # Don't sign it!

    # Try to send unsigned message
    success2 = message_bus.send_message(bad_message)
    print(f"Unsigned message: {'✓ Accepted' if success2 else '✗ Rejected'}")

    # Try replay attack (reuse sequence number)
    replay_message = CrossSocietyMessage(
        message_id="test-003",
        message_type=MessageType.HELLO,
        sender_lct="lct-sage-society",
        recipient_lct="lct-legion-society",
        timestamp=datetime.now(timezone.utc),
        sequence_number=100,  # Same as before!
        payload={"test": "replay"},
    )
    replay_message.sign(sage_keypair)

    success3 = message_bus.send_message(replay_message)
    print(f"Replay attack: {'✓ Accepted' if success3 else '✗ Rejected'}")

    # ========================================
    # Summary
    # ========================================

    print("\n### Summary")
    print("-" * 80)

    stats = message_bus.get_stats()
    print(f"Total messages: {stats['total_messages']}")
    print(f"Verified: {stats['verified_messages']}")
    print(f"Rejected: {stats['rejected_messages']}")
    print(f"Verification rate: {stats['verification_rate']:.1%}")

    print("\n" + "=" * 80)
    print("✅ CROSS-SOCIETY MESSAGING OPERATIONAL")
    print("Societies can now coordinate securely!")
    print("=" * 80)
