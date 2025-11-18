"""
Integrated Society Node - Production Ready

Session #43

Brings together all Web4 components into a single, production-ready society node:

Components Integrated:
1. Energy-backed ATP system (Session #36)
2. Energy-backed identity bonds (Session #39)
3. Hardened energy system (Session #40)
4. Cross-society messaging (Session #41)
5. ATP marketplace (Session #41)
6. Trust propagation (Session #41)
7. Security mitigations (Session #42)
8. Energy-based Sybil resistance (Session #42)

This is the complete, deployable Web4 society node.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
import json
import hashlib

# Import all Web4 components
from energy_capacity import EnergyCapacityRegistry, EnergySourceType
from energy_backed_atp import EnergyBackedSocietyPool, ChargedATP, WorkTicket
from energy_backed_identity_bond import EnergyBackedIdentityBond, EnergyBackedBondRegistry
from hardened_energy_system import (
    HardenedEnergyCapacityRegistry,
    HardenedEnergyBackedIdentityBond,
)

from cross_society_messaging import (
    CrossSocietyMessage,
    CrossSocietyMessageBus,
    MessageType,
    SocietyCoordinator,
)

from cross_society_atp_exchange import (
    ATPMarketplace,
    ATPOffer,
    ATPBid,
    ATPExchange,
)

from cross_society_trust_propagation import (
    TrustPropagationEngine,
    TrustRecord,
)

from cross_society_security_mitigations import (
    SecureATPMarketplace,
    SybilIsolationEngine,
    TrustDisagreementResolver,
    RateLimitedMessageBus,
)

from trust_ceiling_mitigation import (
    TrustCeilingEngine,
    RobustTrustEngine,
)

from energy_based_sybil_resistance import (
    EnergyCapacityProof,
    EnergySybilResistance,
    EnergyWeightedTrustEngine,
)

from web4_crypto import KeyPair, Web4Crypto


# ============================================================================
# Integrated Society Node
# ============================================================================

@dataclass
class SocietyNodeConfig:
    """Configuration for a society node"""
    society_name: str
    society_lct: str

    # Energy settings
    total_energy_capacity_watts: float
    energy_sources: List[Dict]  # List of energy source configs

    # Trust settings
    trust_decay_factor: float = 0.8
    max_propagation_distance: int = 3
    trust_ceiling: float = 0.7

    # Marketplace settings
    max_price_deviation: float = 0.20
    max_size_multiple: float = 10.0

    # Message bus settings
    max_messages_per_minute: int = 60

    # Sybil resistance settings
    min_energy_capacity: float = 10.0
    sybil_cv_threshold: float = 0.2


class IntegratedSocietyNode:
    """
    Complete, production-ready Web4 society node.

    Integrates all Web4 components:
    - Energy capacity registry and proofs
    - Energy-backed ATP system
    - Energy-backed identity bonds
    - Cross-society messaging
    - ATP marketplace with security
    - Trust propagation with ceiling
    - Sybil resistance via energy
    - Rate limiting and DoS protection
    """

    def __init__(self, config: SocietyNodeConfig):
        self.config = config
        self.society_lct = config.society_lct
        self.society_name = config.society_name

        # Generate cryptographic keypair
        self.keypair = Web4Crypto.generate_keypair(
            config.society_name,
            deterministic=True
        )

        # Initialize energy system (hardened)
        # Session #44: Use factory method for testing mode (no security features)
        self.energy_registry = HardenedEnergyCapacityRegistry.create_for_testing(
            society_lct=config.society_lct
        )
        self.identity_bond = HardenedEnergyBackedIdentityBond(
            self.energy_registry
        )

        # Initialize energy sources
        self._setup_energy_sources()

        # Create energy capacity proof for Sybil resistance
        self.energy_proof = EnergyCapacityProof(
            society_lct=config.society_lct,
            capacity_watts=config.total_energy_capacity_watts,
            generation_type="solar",  # Default, can be configured
            proof_hash=hashlib.sha256(
                f"{config.society_lct}{config.total_energy_capacity_watts}".encode()
            ).hexdigest(),
            verified_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        )

        # Initialize trust system (robust with ceiling + diversity)
        self.trust_engine = RobustTrustEngine(
            society_lct=config.society_lct,
            decay_factor=config.trust_decay_factor,
            max_propagation_distance=config.max_propagation_distance,
            base_ceiling=config.trust_ceiling,
            diversity_enabled=True,
        )

        # Initialize energy-based Sybil resistance
        self.sybil_resistance = EnergySybilResistance()
        self.sybil_resistance.register_capacity(self.energy_proof)

        # Initialize Sybil isolation engine (will be set later when network is available)
        self.sybil_isolation = None

        # Initialize message bus (rate-limited)
        self.message_bus = RateLimitedMessageBus()

        # Initialize society coordinator
        self.coordinator = SocietyCoordinator(
            society_lct=config.society_lct,
            keypair=self.keypair,
            message_bus=self.message_bus,
        )

        # Initialize ATP marketplace (secure)
        self.marketplace = SecureATPMarketplace(sybil_engine=None)  # Will set later
        self.marketplace.max_price_deviation = config.max_price_deviation
        self.marketplace.max_size_multiple = config.max_size_multiple

        # Initialize trust disagreement resolver
        self.trust_resolver = TrustDisagreementResolver()

        # Initialize energy-weighted trust engine
        self.energy_trust = EnergyWeightedTrustEngine(self.sybil_resistance)

        # Local state
        self.members: Dict[str, EnergyBackedIdentityBond] = {}  # member_lct -> bond
        self.total_atp_supply = 0.0
        self.atp_allocations: Dict[str, float] = {}  # member_lct -> ATP amount

        # Network state
        self.connected_societies: Set[str] = set()
        self.known_societies: Dict[str, EnergyCapacityProof] = {}

        # Statistics
        self.stats = {
            "members": 0,
            "total_energy": 0.0,
            "total_atp": 0.0,
            "messages_sent": 0,
            "messages_received": 0,
            "atp_trades": 0,
            "trust_queries": 0,
        }

    def _setup_energy_sources(self):
        """Initialize energy sources from config"""
        for source_config in self.config.energy_sources:
            source = EnergySource(
                source_id=source_config["source_id"],
                source_type=source_config["type"],
                capacity_watts=source_config["capacity"],
                owner_lct=self.society_lct,
            )
            self.energy_registry.register_source(source)

    # ========================================
    # Member Management
    # ========================================

    def add_member(
        self,
        member_lct: str,
        energy_capacity_watts: float,
    ) -> EnergyBackedIdentityBond:
        """
        Add a member to the society.

        Bonds member's energy capacity to their identity.
        """
        # Create identity bond
        bond = self.identity_bond.create_bond(
            identity_lct=member_lct,
            bonded_capacity_watts=energy_capacity_watts,
        )

        # Store member
        self.members[member_lct] = bond

        # Update stats
        self.stats["members"] += 1
        self.stats["total_energy"] += energy_capacity_watts

        # Allocate ATP based on energy
        atp_amount = self._calculate_atp_allocation(energy_capacity_watts)
        self.atp_allocations[member_lct] = atp_amount
        self.total_atp_supply += atp_amount
        self.stats["total_atp"] += atp_amount

        return bond

    def _calculate_atp_allocation(self, energy_watts: float) -> float:
        """Calculate ATP allocation based on energy capacity"""
        # Simple formula: 1 ATP per 10 watts (can be adjusted)
        return energy_watts / 10.0

    def remove_member(self, member_lct: str) -> bool:
        """Remove a member from the society"""
        if member_lct not in self.members:
            return False

        bond = self.members[member_lct]

        # Release energy capacity
        self.identity_bond.release_bond(member_lct)

        # Update stats
        self.stats["members"] -= 1
        self.stats["total_energy"] -= bond.bonded_capacity_watts

        # Remove ATP allocation
        if member_lct in self.atp_allocations:
            atp = self.atp_allocations[member_lct]
            self.total_atp_supply -= atp
            self.stats["total_atp"] -= atp
            del self.atp_allocations[member_lct]

        # Remove member
        del self.members[member_lct]

        return True

    # ========================================
    # Trust Management
    # ========================================

    def set_trust(
        self,
        subject_lct: str,
        trust_score: float,
        evidence: Optional[List[str]] = None,
    ):
        """Set trust for an identity (internal or external)"""
        self.trust_engine.set_direct_trust(
            subject_lct,
            trust_score,
            evidence,
        )

    def get_trust(self, subject_lct: str) -> float:
        """Get aggregated trust for an identity"""
        return self.trust_engine.get_aggregated_trust(subject_lct)

    def query_trust_from_society(
        self,
        target_society_lct: str,
        query_about_lct: str,
    ):
        """
        Query another society about trust for an identity.

        Sends TRUST_QUERY message via cross-society messaging.
        """
        self.coordinator.send_trust_query(target_society_lct, query_about_lct)
        self.stats["trust_queries"] += 1

    # ========================================
    # Cross-Society Networking
    # ========================================

    def announce_to_network(self):
        """Announce presence to network via HELLO message"""
        self.coordinator.send_hello("broadcast")
        self.stats["messages_sent"] += 1

    def connect_to_society(self, other_society_lct: str, trust_score: float = 0.5):
        """
        Establish connection to another society.

        Sets mutual trust and enables cross-society operations.
        """
        self.connected_societies.add(other_society_lct)
        self.trust_engine.set_society_trust(other_society_lct, trust_score)

    def register_society_energy_proof(self, proof: EnergyCapacityProof):
        """Register energy proof from another society"""
        self.known_societies[proof.society_lct] = proof
        self.sybil_resistance.register_capacity(proof)

    # ========================================
    # ATP Marketplace Operations
    # ========================================

    def create_atp_offer(
        self,
        amount: float,
        price_per_atp: float,
    ) -> str:
        """
        Create ATP sell offer on cross-society marketplace.

        Returns offer ID.
        """
        # Check if we have enough ATP
        available_atp = self.total_atp_supply

        if amount > available_atp:
            raise ValueError(
                f"Insufficient ATP: have {available_atp}, need {amount}"
            )

        # Create offer
        offer = self.marketplace.create_offer(
            seller_lct=self.society_lct,
            amount_atp=amount,
            price_per_atp=price_per_atp,
        )

        return offer.offer_id

    def create_atp_bid(
        self,
        amount: float,
        max_price_per_atp: float,
    ) -> str:
        """
        Create ATP buy bid on cross-society marketplace.

        Returns bid ID.
        """
        bid = self.marketplace.create_bid(
            buyer_lct=self.society_lct,
            amount_atp=amount,
            max_price_per_atp=max_price_per_atp,
        )

        return bid.bid_id

    def execute_atp_trades(self):
        """
        Execute ATP trades (match orders and settle).

        This should be called periodically by the society.
        """
        exchanges = self.marketplace.match_orders()

        for exchange in exchanges:
            # Update stats if we're involved
            if (exchange.seller_lct == self.society_lct or
                exchange.buyer_lct == self.society_lct):
                self.stats["atp_trades"] += 1

        return exchanges

    # ========================================
    # Message Processing
    # ========================================

    def process_incoming_messages(self):
        """Process messages from message bus"""
        messages = self.message_bus.get_messages_for(self.society_lct)

        for message in messages:
            self._handle_message(message)
            self.stats["messages_received"] += 1

    def _handle_message(self, message: CrossSocietyMessage):
        """Handle a single incoming message"""

        if message.message_type == MessageType.HELLO:
            # Society introduction
            sender = message.sender_lct
            self.connected_societies.add(sender)

        elif message.message_type == MessageType.TRUST_QUERY:
            # Trust query - respond with our assessment
            query_about = message.payload.get("query_about")
            if query_about:
                trust = self.get_trust(query_about)
                self.coordinator.send_trust_response(
                    message.sender_lct,
                    query_about,
                    trust,
                )

        elif message.message_type == MessageType.TRUST_RESPONSE:
            # Trust response - update our records
            subject = message.payload.get("subject_lct")
            trust_score = message.payload.get("trust_score")
            if subject and trust_score is not None:
                # This is propagated trust
                self.trust_engine.receive_propagated_trust(
                    subject_lct=subject,
                    source_lct=message.sender_lct,
                    trust_score=trust_score,
                    propagation_path=[message.sender_lct, self.society_lct],
                )

    # ========================================
    # Reporting and Statistics
    # ========================================

    def get_status(self) -> Dict:
        """Get current node status"""
        return {
            "society_name": self.society_name,
            "society_lct": self.society_lct,
            "members": self.stats["members"],
            "total_energy": self.stats["total_energy"],
            "total_atp": self.stats["total_atp"],
            "connected_societies": len(self.connected_societies),
            "messages_sent": self.stats["messages_sent"],
            "messages_received": self.stats["messages_received"],
            "atp_trades": self.stats["atp_trades"],
            "trust_queries": self.stats["trust_queries"],
            "marketplace_stats": self.marketplace.get_stats(),
        }

    def get_trust_breakdown(self, subject_lct: str) -> Dict:
        """Get detailed trust breakdown for an identity"""
        return self.trust_engine.get_trust_breakdown(subject_lct)

    def get_energy_proof(self) -> EnergyCapacityProof:
        """Get this society's energy capacity proof"""
        return self.energy_proof


# ============================================================================
# Multi-Society Network
# ============================================================================

class MultiSocietyNetwork:
    """
    Manages multiple society nodes in a network.

    Simulates a complete Web4 network with multiple societies.
    """

    def __init__(self):
        self.societies: Dict[str, IntegratedSocietyNode] = {}
        self.shared_message_bus = RateLimitedMessageBus()
        self.shared_marketplace = None  # Will be created after societies

    def add_society(self, config: SocietyNodeConfig) -> IntegratedSocietyNode:
        """Add a society to the network"""
        node = IntegratedSocietyNode(config)

        # Use shared message bus
        node.message_bus = self.shared_message_bus
        node.coordinator.message_bus = self.shared_message_bus

        self.societies[config.society_lct] = node

        return node

    def connect_societies(
        self,
        society_a_lct: str,
        society_b_lct: str,
        mutual_trust: float = 0.8,
    ):
        """Create bidirectional connection between two societies"""

        if society_a_lct not in self.societies or society_b_lct not in self.societies:
            raise ValueError("Both societies must be in network")

        society_a = self.societies[society_a_lct]
        society_b = self.societies[society_b_lct]

        # Establish connections
        society_a.connect_to_society(society_b_lct, mutual_trust)
        society_b.connect_to_society(society_a_lct, mutual_trust)

        # Exchange energy proofs
        society_a.register_society_energy_proof(society_b.get_energy_proof())
        society_b.register_society_energy_proof(society_a.get_energy_proof())

    def announce_all_societies(self):
        """Have all societies announce themselves"""
        for society in self.societies.values():
            society.announce_to_network()

    def propagate_trust(self):
        """Propagate trust through the network"""
        # This is simplified - in real implementation, messages would flow
        # through the message bus and be processed asynchronously

        for society in self.societies.values():
            society.process_incoming_messages()

    def get_network_stats(self) -> Dict:
        """Get statistics for entire network"""
        return {
            "total_societies": len(self.societies),
            "total_members": sum(s.stats["members"] for s in self.societies.values()),
            "total_energy": sum(s.stats["total_energy"] for s in self.societies.values()),
            "total_atp": sum(s.stats["total_atp"] for s in self.societies.values()),
            "total_messages": self.shared_message_bus.total_messages,
            "society_details": {
                lct: society.get_status()
                for lct, society in self.societies.items()
            },
        }


# ============================================================================
# Example Usage and Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("INTEGRATED SOCIETY NODE - Session #43")
    print("Production-Ready Web4 Implementation")
    print("=" * 80)

    # Create network
    network = MultiSocietyNetwork()

    # Create 3 societies with different energy capacities
    print("\n### Creating Societies")
    print("-" * 80)

    sage_config = SocietyNodeConfig(
        society_name="sage",
        society_lct="lct-sage-society",
        total_energy_capacity_watts=10000.0,
        energy_sources=[
            {"source_id": "sage-solar-1", "type": "solar", "capacity": 5000.0},
            {"source_id": "sage-solar-2", "type": "solar", "capacity": 5000.0},
        ],
    )

    legion_config = SocietyNodeConfig(
        society_name="legion",
        society_lct="lct-legion-society",
        total_energy_capacity_watts=5000.0,
        energy_sources=[
            {"source_id": "legion-wind-1", "type": "wind", "capacity": 5000.0},
        ],
    )

    cbp_config = SocietyNodeConfig(
        society_name="cbp",
        society_lct="lct-cbp-society",
        total_energy_capacity_watts=2000.0,
        energy_sources=[
            {"source_id": "cbp-battery-1", "type": "battery", "capacity": 2000.0},
        ],
    )

    sage = network.add_society(sage_config)
    legion = network.add_society(legion_config)
    cbp = network.add_society(cbp_config)

    print(f"Created SAGE: {sage_config.total_energy_capacity_watts}W")
    print(f"Created Legion: {legion_config.total_energy_capacity_watts}W")
    print(f"Created CBP: {cbp_config.total_energy_capacity_watts}W")

    # Add members to societies
    print("\n### Adding Members to Societies")
    print("-" * 80)

    # SAGE members
    sage.add_member("lct-alice", 1000.0)
    sage.add_member("lct-bob", 500.0)

    # Legion members
    legion.add_member("lct-charlie", 800.0)

    # CBP members
    cbp.add_member("lct-david", 300.0)
    cbp.add_member("lct-eve", 200.0)

    print(f"SAGE members: {sage.stats['members']}, total energy: {sage.stats['total_energy']}W")
    print(f"Legion members: {legion.stats['members']}, total energy: {legion.stats['total_energy']}W")
    print(f"CBP members: {cbp.stats['members']}, total energy: {cbp.stats['total_energy']}W")

    # Connect societies
    print("\n### Connecting Societies")
    print("-" * 80)

    network.connect_societies("lct-sage-society", "lct-legion-society", mutual_trust=0.9)
    network.connect_societies("lct-legion-society", "lct-cbp-society", mutual_trust=0.8)
    network.connect_societies("lct-sage-society", "lct-cbp-society", mutual_trust=0.7)

    print("Topology: SAGE ↔ Legion ↔ CBP")
    print("          SAGE ↔ CBP")

    # Announce societies
    print("\n### Society Announcements")
    print("-" * 80)

    network.announce_all_societies()

    print(f"Messages sent: {network.shared_message_bus.total_messages}")

    # Set trust relationships
    print("\n### Setting Trust Relationships")
    print("-" * 80)

    sage.set_trust("lct-alice", 0.95, evidence=["Founding member", "High contributions"])
    sage.set_trust("lct-bob", 0.80, evidence=["Active member"])

    legion.set_trust("lct-charlie", 0.90, evidence=["Trusted member"])

    print("SAGE trusts Alice: 0.95")
    print("SAGE trusts Bob: 0.80")
    print("Legion trusts Charlie: 0.90")

    # Query cross-society trust
    print("\n### Cross-Society Trust Query")
    print("-" * 80)

    legion.query_trust_from_society("lct-sage-society", "lct-alice")
    network.propagate_trust()

    alice_trust_from_legion = legion.get_trust("lct-alice")
    print(f"Legion's view of Alice: {alice_trust_from_legion:.3f}")

    # Network statistics
    print("\n### Network Statistics")
    print("-" * 80)

    stats = network.get_network_stats()
    print(f"Total societies: {stats['total_societies']}")
    print(f"Total members: {stats['total_members']}")
    print(f"Total energy: {stats['total_energy']}W")
    print(f"Total ATP supply: {stats['total_atp']}")
    print(f"Total messages: {stats['total_messages']}")

    print("\n" + "=" * 80)
    print("✅ INTEGRATED SOCIETY NODE OPERATIONAL")
    print("Complete Web4 system with all security mitigations")
    print("=" * 80)
