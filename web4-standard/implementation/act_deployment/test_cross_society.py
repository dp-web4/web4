"""
Unit Tests for Cross-Society Coordination

Session #41

Tests for:
- Cross-society messaging
- ATP exchange marketplace
- Trust propagation
"""

import unittest
from datetime import datetime, timezone, timedelta
import hashlib

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
    ExchangeStatus,
)

from cross_society_trust_propagation import (
    TrustPropagationEngine,
    CrossSocietyTrustNetwork,
    TrustRecord,
)

from web4_crypto import KeyPair, Web4Crypto


class TestCrossSocietyMessaging(unittest.TestCase):
    """Test secure cross-society messaging"""

    def setUp(self):
        self.message_bus = CrossSocietyMessageBus()
        self.sage_keypair = Web4Crypto.generate_keypair("sage", deterministic=True)
        self.legion_keypair = Web4Crypto.generate_keypair("legion", deterministic=True)

    def test_message_signature(self):
        """Test message signing and verification"""
        message = CrossSocietyMessage(
            message_id="test-001",
            message_type=MessageType.HELLO,
            sender_lct="lct-sage",
            recipient_lct="lct-legion",
            timestamp=datetime.now(timezone.utc),
            sequence_number=1,
            payload={"test": "data"},
        )

        # Sign message
        message.sign(self.sage_keypair)

        # Verify signature
        self.assertTrue(message.verify())
        self.assertIsNotNone(message.signature)
        self.assertIsNotNone(message.sender_pubkey)

    def test_replay_attack_prevention(self):
        """Test that replay attacks are blocked"""
        message = CrossSocietyMessage(
            message_id="test-002",
            message_type=MessageType.HELLO,
            sender_lct="lct-sage",
            recipient_lct="lct-legion",
            timestamp=datetime.now(timezone.utc),
            sequence_number=100,
            payload={},
        )

        message.sign(self.sage_keypair)

        # First send succeeds
        result1 = self.message_bus.send_message(message)
        self.assertTrue(result1)

        # Second send (replay) fails
        result2 = self.message_bus.send_message(message)
        self.assertFalse(result2)

        # Check stats
        self.assertEqual(self.message_bus.total_messages, 1)
        self.assertEqual(self.message_bus.rejected_messages, 1)

    def test_unsigned_message_rejected(self):
        """Test that unsigned messages are rejected"""
        message = CrossSocietyMessage(
            message_id="test-003",
            message_type=MessageType.HELLO,
            sender_lct="lct-attacker",
            recipient_lct="lct-legion",
            timestamp=datetime.now(timezone.utc),
            sequence_number=1,
            payload={},
        )

        # Don't sign message
        result = self.message_bus.send_message(message)

        self.assertFalse(result)
        self.assertEqual(self.message_bus.rejected_messages, 1)


class TestATPMarketplace(unittest.TestCase):
    """Test ATP exchange marketplace"""

    def setUp(self):
        self.marketplace = ATPMarketplace()

    def test_create_offer(self):
        """Test creating ATP sell offer"""
        offer = self.marketplace.create_offer(
            seller_lct="lct-sage",
            amount_atp=1000.0,
            price_per_atp=0.01,
            currency="ATP",
        )

        self.assertEqual(offer.seller_lct, "lct-sage")
        self.assertEqual(offer.amount_atp, 1000.0)
        self.assertEqual(offer.price_per_atp, 0.01)
        self.assertEqual(offer.status, ExchangeStatus.PENDING)

        # Check reserved ATP
        self.assertEqual(self.marketplace.reserved_atp["lct-sage"], 1000.0)

    def test_create_bid(self):
        """Test creating ATP buy bid"""
        bid = self.marketplace.create_bid(
            buyer_lct="lct-legion",
            amount_atp=500.0,
            max_price_per_atp=0.012,
            currency="ATP",
        )

        self.assertEqual(bid.buyer_lct, "lct-legion")
        self.assertEqual(bid.amount_atp, 500.0)
        self.assertEqual(bid.max_price_per_atp, 0.012)
        self.assertEqual(bid.status, ExchangeStatus.PENDING)

    def test_order_matching(self):
        """Test matching bids and offers"""
        # Create offer (seller wants 0.01 per ATP)
        offer = self.marketplace.create_offer(
            seller_lct="lct-sage",
            amount_atp=1000.0,
            price_per_atp=0.01,
            currency="ATP",
        )

        # Create bid (buyer willing to pay up to 0.012)
        bid = self.marketplace.create_bid(
            buyer_lct="lct-legion",
            amount_atp=1000.0,
            max_price_per_atp=0.012,
            currency="ATP",
        )

        # Match orders
        exchanges = self.marketplace.match_orders()

        self.assertEqual(len(exchanges), 1)

        exchange = exchanges[0]
        self.assertEqual(exchange.seller_lct, "lct-sage")
        self.assertEqual(exchange.buyer_lct, "lct-legion")
        self.assertEqual(exchange.amount_atp, 1000.0)
        self.assertEqual(exchange.price_per_atp, 0.01)  # Seller's price
        self.assertEqual(exchange.status, ExchangeStatus.MATCHED)

        # Check offer and bid status
        self.assertEqual(offer.status, ExchangeStatus.MATCHED)
        self.assertEqual(bid.status, ExchangeStatus.MATCHED)

    def test_order_no_match(self):
        """Test that mismatched orders don't match"""
        # Create offer (seller wants 0.02)
        self.marketplace.create_offer(
            seller_lct="lct-sage",
            amount_atp=1000.0,
            price_per_atp=0.02,
            currency="ATP",
        )

        # Create bid (buyer only willing to pay 0.01)
        self.marketplace.create_bid(
            buyer_lct="lct-legion",
            amount_atp=1000.0,
            max_price_per_atp=0.01,
            currency="ATP",
        )

        # No match
        exchanges = self.marketplace.match_orders()
        self.assertEqual(len(exchanges), 0)

    def test_atomic_settlement(self):
        """Test commit-reveal atomic settlement"""
        # Create and match order
        offer = self.marketplace.create_offer(
            seller_lct="lct-sage",
            amount_atp=100.0,
            price_per_atp=0.01,
            currency="ATP",
        )

        bid = self.marketplace.create_bid(
            buyer_lct="lct-legion",
            amount_atp=100.0,
            max_price_per_atp=0.01,
            currency="ATP",
        )

        exchanges = self.marketplace.match_orders()
        exchange_id = exchanges[0].exchange_id

        # Initiate settlement
        self.assertTrue(self.marketplace.initiate_settlement(exchange_id))

        # Commit phase
        seller_secret = "seller-proof-abc123"
        buyer_secret = "buyer-proof-xyz789"

        seller_commitment = hashlib.sha256(seller_secret.encode()).hexdigest()
        buyer_commitment = hashlib.sha256(buyer_secret.encode()).hexdigest()

        self.assertTrue(self.marketplace.commit_seller(exchange_id, seller_commitment))
        self.assertTrue(self.marketplace.commit_buyer(exchange_id, buyer_commitment))

        # Reveal phase
        self.assertTrue(self.marketplace.reveal_seller(exchange_id, seller_secret))
        self.assertTrue(self.marketplace.reveal_buyer(exchange_id, buyer_secret))

        # Check completion
        exchange = self.marketplace.exchanges[exchange_id]
        self.assertEqual(exchange.status, ExchangeStatus.COMPLETED)
        self.assertIsNotNone(exchange.completed_at)

    def test_cancel_offer(self):
        """Test canceling an offer"""
        offer = self.marketplace.create_offer(
            seller_lct="lct-sage",
            amount_atp=100.0,
            price_per_atp=0.01,
            currency="ATP",
        )

        # Check reserved ATP
        self.assertEqual(self.marketplace.reserved_atp["lct-sage"], 100.0)

        # Cancel
        self.assertTrue(self.marketplace.cancel_offer(offer.offer_id))

        # Check status
        self.assertEqual(offer.status, ExchangeStatus.CANCELLED)

        # Check ATP released
        self.assertEqual(self.marketplace.reserved_atp["lct-sage"], 0.0)


class TestTrustPropagation(unittest.TestCase):
    """Test cross-society trust propagation"""

    def test_direct_trust(self):
        """Test setting direct trust"""
        engine = TrustPropagationEngine("lct-sage")

        record = engine.set_direct_trust(
            "lct-alice",
            0.95,
            evidence=["Completed 10 work requests"],
        )

        self.assertEqual(record.subject_lct, "lct-alice")
        self.assertEqual(record.trust_score, 0.95)
        self.assertEqual(len(record.evidence), 1)

        # Get trust
        trust = engine.get_aggregated_trust("lct-alice")
        self.assertEqual(trust, 0.95)

    def test_trust_propagation_one_hop(self):
        """Test trust propagation over one hop"""
        network = CrossSocietyTrustNetwork()

        # Create two societies
        network.add_society("lct-sage")
        network.add_society("lct-legion")
        network.connect_societies("lct-sage", "lct-legion")

        # SAGE trusts Legion
        network.set_society_trust("lct-legion", "lct-sage", 0.9)

        # SAGE trusts Alice
        network.set_identity_trust("lct-sage", "lct-alice", 0.95)

        # Propagate
        network.propagate_all()

        # Legion should receive propagated trust
        legion_engine = network.engines["lct-legion"]
        trust = legion_engine.get_aggregated_trust("lct-alice")

        # Trust should be decayed (0.95 * 0.8 = 0.76)
        self.assertGreater(trust, 0.75)
        self.assertLess(trust, 0.96)

    def test_trust_propagation_two_hops(self):
        """Test trust propagation over two hops"""
        network = CrossSocietyTrustNetwork()

        # Create three societies: SAGE → Legion → CBP
        network.add_society("lct-sage")
        network.add_society("lct-legion")
        network.add_society("lct-cbp")

        network.connect_societies("lct-sage", "lct-legion")
        network.connect_societies("lct-legion", "lct-cbp")

        # Set society trust
        network.set_society_trust("lct-legion", "lct-sage", 0.9)
        network.set_society_trust("lct-cbp", "lct-legion", 0.9)

        # SAGE trusts Alice
        network.set_identity_trust("lct-sage", "lct-alice", 0.95)

        # First propagation (SAGE → Legion)
        network.propagate_all()

        # Legion should have trust
        legion_trust = network.engines["lct-legion"].get_aggregated_trust("lct-alice")
        self.assertGreater(legion_trust, 0.5)

        # Check Legion received propagated trust
        breakdown = network.engines["lct-legion"].get_trust_breakdown("lct-alice")
        self.assertGreater(len(breakdown["propagated_trust"]), 0)

        # Second propagation (Legion → CBP)
        network.propagate_all()

        # CBP should have received propagated trust
        cbp_trust = network.engines["lct-cbp"].get_aggregated_trust("lct-alice")
        self.assertGreater(cbp_trust, 0.5)

        # Check CBP's trust breakdown shows 2-hop propagation
        cbp_breakdown = network.engines["lct-cbp"].get_trust_breakdown("lct-alice")
        self.assertGreater(len(cbp_breakdown["propagated_trust"]), 0)

        # Verify path length is 2 hops
        prop_record = cbp_breakdown["propagated_trust"][0]
        self.assertEqual(prop_record["propagation_distance"], 2)

    def test_trust_aggregation(self):
        """Test aggregating trust from multiple sources"""
        network = CrossSocietyTrustNetwork()

        # Create three societies
        network.add_society("lct-sage")
        network.add_society("lct-legion")
        network.add_society("lct-cbp")

        # Create triangle (CBP receives from both SAGE and Legion)
        network.connect_societies("lct-sage", "lct-cbp")
        network.connect_societies("lct-legion", "lct-cbp")

        network.set_society_trust("lct-cbp", "lct-sage", 0.9)
        network.set_society_trust("lct-cbp", "lct-legion", 0.9)

        # Both SAGE and Legion trust Alice
        network.set_identity_trust("lct-sage", "lct-alice", 0.9)
        network.set_identity_trust("lct-legion", "lct-alice", 0.85)

        # Propagate
        network.propagate_all()

        # CBP should aggregate both sources
        cbp_trust = network.engines["lct-cbp"].get_aggregated_trust("lct-alice")

        breakdown = network.engines["lct-cbp"].get_trust_breakdown("lct-alice")
        self.assertEqual(len(breakdown["propagated_trust"]), 2)

        # Aggregated should be weighted average
        self.assertGreater(cbp_trust, 0.5)

    def test_default_trust(self):
        """Test default trust for unknown identities"""
        engine = TrustPropagationEngine("lct-sage")

        # Unknown identity
        trust = engine.get_aggregated_trust("lct-unknown")

        # Should return neutral default (0.5)
        self.assertEqual(trust, 0.5)


def run_tests():
    """Run all tests"""
    print("=" * 80)
    print("CROSS-SOCIETY COORDINATION TESTS - Session #41")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestCrossSocietyMessaging))
    suite.addTests(loader.loadTestsFromTestCase(TestATPMarketplace))
    suite.addTests(loader.loadTestsFromTestCase(TestTrustPropagation))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED")
        print(f"\nTests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")

        print("\n✅ Cross-Society Coordination Verified:")
        print("  - Secure messaging with signature verification")
        print("  - Replay attack prevention")
        print("  - ATP marketplace order matching")
        print("  - Atomic settlement (commit-reveal)")
        print("  - Trust propagation across hops")
        print("  - Trust aggregation from multiple sources")
    else:
        print("\n❌ SOME TESTS FAILED")

    return result


if __name__ == "__main__":
    run_tests()
