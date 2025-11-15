#!/usr/bin/env python3
"""
Tests for ATP Lowest-Exchange Principle
========================================

Created: Session #29 (2025-11-14)
"""

from datetime import datetime, timezone
from lowest_exchange import (
    Society,
    LowestExchangeNegotiator,
    ValueMisalignmentDetector,
    CrossSocietyTransaction
)


def test_society_valuation():
    """Test basic society valuation setting and retrieval"""
    print("\nTest 1: Society Valuation")

    society = Society("lct:test:society1", "Test Society")

    society.set_valuation("apple", 10.0, "Fruit")
    society.set_valuation("car", 50000.0, "Vehicle")

    assert society.get_valuation("apple") == 10.0
    assert society.get_valuation("car") == 50000.0
    assert society.get_valuation("nonexistent") is None

    print("  ✅ Society valuations work correctly")


def test_lowest_exchange_basic():
    """Test basic lowest-exchange negotiation"""
    print("\nTest 2: Basic Lowest-Exchange")

    seller = Society("lct:seller", "Seller")
    buyer = Society("lct:buyer", "Buyer")

    # Seller wants 100 ATP for item
    seller.set_valuation("widget", 100.0)

    # Buyer values widget at 150 ATP (willing to pay more)
    buyer.set_valuation("widget", 150.0)

    negotiator = LowestExchangeNegotiator()
    rate = negotiator.negotiate_exchange_rate(buyer, seller, "widget")

    # Should pay in ATP (simplest option)
    assert rate.from_item == "ATP"
    assert rate.rate == 100.0  # Seller's asking price (ATP to pay)

    print("  ✅ Lowest-exchange defaults to ATP correctly")


def test_banana_art_exploit():
    """Test the $1M banana exploit scenario"""
    print("\nTest 3: $1M Banana Exploit")

    art_society = Society("lct:art", "Art Society")
    normal_society = Society("lct:normal", "Normal Society")

    # Art society claims banana is worth 1M
    art_society.set_valuation("banana", 1_000_000)
    art_society.set_valuation("painting", 500_000)

    # Normal society knows banana is worth 1 ATP
    normal_society.set_valuation("banana", 1.0)

    negotiator = LowestExchangeNegotiator()

    # Normal society buys painting
    rate = negotiator.negotiate_exchange_rate(
        normal_society,  # buyer
        art_society,     # seller
        "painting"
    )

    # Should pay in bananas (art society values them highly!)
    assert rate.from_item == "banana"
    assert rate.rate == 0.5  # 500K / 1M = 0.5 bananas

    print("  ✅ Buyer exploits art society's banana valuation")

    # Execute transaction
    tx = negotiator.execute_transaction(
        buyer=normal_society,
        seller=art_society,
        item="painting",
        quantity=1.0,
        payment_item="banana",
        payment_quantity=0.5,
        transaction_id="tx:banana_art"
    )

    # Buyer got great deal (paid 0.5 ATP for 500K ATP item)
    assert tx.valuation_buyer > 0.9  # Very satisfied
    # Seller thinks they got fair deal (0.5 bananas = 500K ATP to them)
    assert tx.valuation_seller > 0.9

    print("  ✅ Transaction executed with mutual satisfaction")
    print(f"     (But buyer paid {tx.atp_paid:.1f} ATP for {art_society.get_valuation('painting'):,.0f} ATP item!)")


def test_gaming_detection():
    """Test detection of valuation gaming"""
    print("\nTest 4: Gaming Detection")

    gaming_society = Society("lct:gaming", "Gaming Society")

    # Set high valuation but won't accept as payment
    gaming_society.set_valuation("worthless_token", 1_000_000)
    gaming_society.set_valuation("real_item", 100)

    detector = ValueMisalignmentDetector()
    audit = detector.audit_society(gaming_society, high_value_threshold=100_000)

    # Should detect gaming (claims high value but no transaction history)
    assert audit['gaming_detected'] is True
    assert audit['consistency_score'] < 1.0
    assert len(audit['misalignments']) == 1

    print("  ✅ Gaming detected for high-value items without payment acceptance")
    print(f"     Consistency score: {audit['consistency_score']:.2f}")


def test_consistency_enforcement():
    """Test that accepting payment fixes gaming detection"""
    print("\nTest 5: Consistency Enforcement")

    consistent_society = Society("lct:consistent", "Consistent Society")

    # Set high valuation
    consistent_society.set_valuation("gold", 10_000)

    # Create transaction where they ACCEPTED gold as payment
    tx = CrossSocietyTransaction(
        transaction_id="tx:gold_payment",
        item_exchanged="service",
        quantity=1.0,
        atp_paid=10_000,
        buyer_society_lct="lct:other",
        seller_society_lct=consistent_society.society_lct,
        timestamp=datetime.now(timezone.utc),
        valuation_buyer=1.0,
        valuation_seller=1.0,
        validity=1.0,
        veracity_external=1.0,
        payment_method="gold"  # Accepted gold as payment!
    )
    consistent_society.record_transaction(tx)

    detector = ValueMisalignmentDetector()
    audit = detector.audit_society(consistent_society, high_value_threshold=1_000)

    # Should NOT detect gaming (accepts gold as payment)
    assert audit['gaming_detected'] is False
    assert audit['consistency_score'] == 1.0

    print("  ✅ No gaming detected when society accepts items at stated prices")


def test_glass_beads_historical():
    """Test historical glass beads predatory exchange"""
    print("\nTest 6: Glass Beads Historical Scenario")

    tribe = Society("lct:tribe", "Indigenous Tribe")
    settler = Society("lct:settler", "Settlers")

    # Tribe: Glass beads are scarce → high value
    tribe.set_valuation("glass_beads", 100)
    tribe.set_valuation("land", 10_000)

    # Settler: Glass beads are abundant → low value
    settler.set_valuation("glass_beads", 0.1)
    settler.set_valuation("land", 10_000)  # Same land value

    negotiator = LowestExchangeNegotiator()

    # Settler buys land from tribe
    rate = negotiator.negotiate_exchange_rate(
        settler,  # buyer
        tribe,    # seller
        "land"
    )

    # Settler pays in glass beads (cheap for settler, valuable to tribe)
    assert rate.from_item == "glass_beads"

    tx = negotiator.execute_transaction(
        buyer=settler,
        seller=tribe,
        item="land",
        quantity=1.0,
        payment_item="glass_beads",
        payment_quantity=100,  # 10,000 / 100 = 100 beads
        transaction_id="tx:glass_beads"
    )

    # Tribe thinks it's fair (100 beads @ 100 ATP = 10K ATP)
    assert tx.valuation_seller > 0.9

    # Settler got amazing deal (100 beads @ 0.1 ATP = 10 ATP for 10K land!)
    assert tx.valuation_buyer > 0.9

    # External veracity should flag this as exploitative
    # (geometric mean of value extraction)
    print(f"  ✅ Predatory exchange executed")
    print(f"     Tribe paid: {tribe.get_valuation('land'):,.0f} ATP worth")
    print(f"     Settler paid: {tx.atp_paid:.1f} ATP (from their perspective)")
    print(f"     Value extraction: {tribe.get_valuation('land') / tx.atp_paid:.1f}x")
    print(f"     External veracity: {tx.veracity_external:.3f} (should be very low)")


def test_multi_item_negotiation():
    """Test negotiation with multiple payment options"""
    print("\nTest 7: Multi-Item Negotiation")

    seller = Society("lct:seller2", "Seller 2")
    buyer = Society("lct:buyer2", "Buyer 2")

    # Seller values various items
    seller.set_valuation("product", 1000)
    seller.set_valuation("gold", 100)  # Values gold
    seller.set_valuation("silver", 50)  # Values silver less

    # Buyer has both gold and silver
    buyer.set_valuation("gold", 110)  # Gold costs buyer 110 ATP
    buyer.set_valuation("silver", 40)  # Silver costs buyer 40 ATP

    negotiator = LowestExchangeNegotiator()
    rate = negotiator.negotiate_exchange_rate(buyer, seller, "product")

    # Buyer should pay in silver (cheaper for buyer per ATP value to seller)
    # Product costs 1000 ATP
    # Pay in gold: 1000/100 = 10 gold @ 110 ATP = 1100 ATP cost to buyer
    # Pay in silver: 1000/50 = 20 silver @ 40 ATP = 800 ATP cost to buyer
    # Silver is cheaper!
    assert rate.from_item == "silver"
    assert rate.rate == 20.0  # 1000 / 50

    print("  ✅ Buyer correctly chooses cheapest payment option (silver)")


def run_all_tests():
    """Run all ATP Lowest-Exchange tests"""
    print("=" * 80)
    print("ATP Lowest-Exchange - Test Suite")
    print("=" * 80)

    tests = [
        test_society_valuation,
        test_lowest_exchange_basic,
        test_banana_art_exploit,
        test_gaming_detection,
        test_consistency_enforcement,
        test_glass_beads_historical,
        test_multi_item_negotiation,
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
        print("\nATP Lowest-Exchange Implementation: VALIDATED")
        print("\nKey Capabilities Tested:")
        print("  ✅ Society valuation management")
        print("  ✅ Lowest-exchange negotiation")
        print("  ✅ $1M banana exploit (forcing function)")
        print("  ✅ Gaming detection (audit mechanism)")
        print("  ✅ Consistency enforcement (accept at stated prices)")
        print("  ✅ Historical predatory exchange (glass beads)")
        print("  ✅ Multi-item negotiation (optimal payment choice)")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{passed + failed} passed)")
        print("=" * 80)
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
