"""
Tests for ATP/ADP JSON-LD serialization (A1).

Validates that to_jsonld() produces spec-compliant documents matching
the atp-adp-cycle spec, and that from_jsonld() round-trips cleanly.
"""

import json
import pytest

from web4.atp import (
    ATPAccount,
    TransferResult,
    ATP_JSONLD_CONTEXT,
    transfer,
)


# ── ATPAccount JSON-LD ──────────────────────────────────────────


class TestATPAccountJsonLd:
    """ATPAccount.to_jsonld() / from_jsonld() tests."""

    def test_context_and_type(self):
        """JSON-LD document has correct @context and @type."""
        acct = ATPAccount(available=100.0)
        doc = acct.to_jsonld()
        assert doc["@context"] == [ATP_JSONLD_CONTEXT]
        assert doc["@type"] == "ATPAccount"

    def test_minimal_account(self):
        """Default account serializes all required fields."""
        acct = ATPAccount()
        doc = acct.to_jsonld()
        assert doc["available"] == 0.0
        assert doc["locked"] == 0.0
        assert doc["adp"] == 0.0
        assert doc["initial_balance"] == 0.0
        assert doc["total"] == 0.0
        assert doc["energy_ratio"] == 0.5  # 0/0 → 0.5

    def test_funded_account(self):
        """Account with balance serializes correctly."""
        acct = ATPAccount(available=1000.0)
        doc = acct.to_jsonld()
        assert doc["available"] == 1000.0
        assert doc["initial_balance"] == 1000.0
        assert doc["total"] == 1000.0
        assert doc["energy_ratio"] == 1.0  # no ADP

    def test_locked_funds(self):
        """Locked funds appear in total but not available."""
        acct = ATPAccount(available=800.0, locked=200.0, initial_balance=1000.0)
        doc = acct.to_jsonld()
        assert doc["available"] == 800.0
        assert doc["locked"] == 200.0
        assert doc["total"] == 1000.0

    def test_energy_ratio_with_adp(self):
        """Energy ratio reflects ATP/ADP balance."""
        acct = ATPAccount(available=300.0, adp=700.0, initial_balance=1000.0)
        doc = acct.to_jsonld()
        assert doc["energy_ratio"] == pytest.approx(0.3)

    def test_roundtrip(self):
        """to_jsonld() → from_jsonld() preserves all fields."""
        original = ATPAccount(available=500.0, locked=100.0, adp=400.0,
                              initial_balance=1000.0)
        doc = original.to_jsonld()
        restored = ATPAccount.from_jsonld(doc)
        assert restored.available == original.available
        assert restored.locked == original.locked
        assert restored.adp == original.adp
        assert restored.initial_balance == original.initial_balance

    def test_roundtrip_ignores_computed(self):
        """from_jsonld() ignores computed fields (total, energy_ratio)."""
        doc = {
            "@context": [ATP_JSONLD_CONTEXT],
            "@type": "ATPAccount",
            "available": 100.0,
            "locked": 50.0,
            "adp": 0.0,
            "initial_balance": 150.0,
            "total": 999.0,  # wrong — should be ignored
            "energy_ratio": 0.0,  # wrong — should be ignored
        }
        acct = ATPAccount.from_jsonld(doc)
        assert acct.total == 150.0  # computed, not from doc
        assert acct.energy_ratio == 1.0  # computed, not from doc

    def test_string_roundtrip(self):
        """to_jsonld_string() → from_jsonld_string() round-trips."""
        original = ATPAccount(available=250.0, locked=50.0, adp=200.0)
        s = original.to_jsonld_string()
        restored = ATPAccount.from_jsonld_string(s)
        assert restored.available == original.available
        assert restored.locked == original.locked
        assert restored.adp == original.adp

    def test_string_is_valid_json(self):
        """to_jsonld_string() produces valid JSON."""
        acct = ATPAccount(available=100.0)
        s = acct.to_jsonld_string()
        parsed = json.loads(s)
        assert parsed["@type"] == "ATPAccount"

    def test_from_jsonld_defaults(self):
        """from_jsonld() handles missing optional fields gracefully."""
        doc = {"@context": [ATP_JSONLD_CONTEXT], "@type": "ATPAccount"}
        acct = ATPAccount.from_jsonld(doc)
        assert acct.available == 0.0
        assert acct.locked == 0.0
        assert acct.adp == 0.0

    def test_from_plain_dict(self):
        """from_jsonld() accepts plain dict without @context/@type."""
        doc = {"available": 500.0, "locked": 0.0, "adp": 100.0,
               "initial_balance": 600.0}
        acct = ATPAccount.from_jsonld(doc)
        assert acct.available == 500.0
        assert acct.adp == 100.0

    def test_after_lock_and_commit(self):
        """Serialization reflects state after lock+commit operations."""
        acct = ATPAccount(available=1000.0)
        acct.lock(200.0)
        acct.commit(200.0)
        doc = acct.to_jsonld()
        assert doc["available"] == 800.0
        assert doc["locked"] == 0.0
        assert doc["adp"] == 200.0
        assert doc["total"] == 800.0

    def test_after_recharge(self):
        """Serialization reflects state after recharge."""
        acct = ATPAccount(available=500.0, adp=500.0, initial_balance=1000.0)
        acct.recharge(rate=0.1)
        doc = acct.to_jsonld()
        assert doc["available"] == 600.0  # 500 + 100 (10% of initial)


# ── TransferResult JSON-LD ──────────────────────────────────────


class TestTransferResultJsonLd:
    """TransferResult.to_jsonld() / from_jsonld() tests."""

    def test_context_and_type(self):
        """JSON-LD document has correct @context and @type."""
        result = TransferResult(fee=5.0, sender_balance=895.0,
                                receiver_balance=100.0, actual_credit=100.0)
        doc = result.to_jsonld()
        assert doc["@context"] == [ATP_JSONLD_CONTEXT]
        assert doc["@type"] == "TransferResult"

    def test_basic_transfer(self):
        """Basic transfer result serializes correctly."""
        result = TransferResult(fee=5.0, sender_balance=895.0,
                                receiver_balance=100.0, actual_credit=100.0)
        doc = result.to_jsonld()
        assert doc["fee"] == 5.0
        assert doc["sender_balance"] == 895.0
        assert doc["receiver_balance"] == 100.0
        assert doc["actual_credit"] == 100.0
        assert "overflow" not in doc  # zero overflow omitted

    def test_overflow_included(self):
        """Overflow is included when non-zero."""
        result = TransferResult(fee=5.0, sender_balance=895.0,
                                receiver_balance=100.0, actual_credit=80.0,
                                overflow=20.0)
        doc = result.to_jsonld()
        assert doc["overflow"] == 20.0

    def test_roundtrip(self):
        """to_jsonld() → from_jsonld() preserves all fields."""
        original = TransferResult(fee=10.0, sender_balance=890.0,
                                  receiver_balance=200.0, actual_credit=200.0,
                                  overflow=0.0)
        doc = original.to_jsonld()
        restored = TransferResult.from_jsonld(doc)
        assert restored.fee == original.fee
        assert restored.sender_balance == original.sender_balance
        assert restored.receiver_balance == original.receiver_balance
        assert restored.actual_credit == original.actual_credit
        assert restored.overflow == original.overflow

    def test_roundtrip_with_overflow(self):
        """Round-trip preserves overflow field."""
        original = TransferResult(fee=5.0, sender_balance=950.0,
                                  receiver_balance=50.0, actual_credit=30.0,
                                  overflow=20.0)
        doc = original.to_jsonld()
        restored = TransferResult.from_jsonld(doc)
        assert restored.overflow == 20.0

    def test_string_roundtrip(self):
        """to_jsonld_string() → from_jsonld_string() round-trips."""
        original = TransferResult(fee=2.5, sender_balance=947.5,
                                  receiver_balance=50.0, actual_credit=50.0)
        s = original.to_jsonld_string()
        restored = TransferResult.from_jsonld_string(s)
        assert restored.fee == original.fee
        assert restored.actual_credit == original.actual_credit

    def test_from_plain_dict(self):
        """from_jsonld() accepts plain dict without @context/@type."""
        doc = {"fee": 3.0, "sender_balance": 897.0,
               "receiver_balance": 100.0, "actual_credit": 100.0}
        result = TransferResult.from_jsonld(doc)
        assert result.fee == 3.0
        assert result.overflow == 0.0  # default

    def test_from_transfer_function(self):
        """Transfer function result serializes and round-trips."""
        sender = ATPAccount(available=1000.0)
        receiver = ATPAccount(available=0.0)
        result = transfer(sender, receiver, 100.0, fee_rate=0.05)
        doc = result.to_jsonld()
        assert doc["@type"] == "TransferResult"
        assert doc["fee"] == pytest.approx(5.0)
        assert doc["actual_credit"] == 100.0
        restored = TransferResult.from_jsonld(doc)
        assert restored.fee == result.fee

    def test_capped_transfer_serialization(self):
        """Transfer with max_balance cap produces overflow in JSON-LD."""
        sender = ATPAccount(available=1000.0)
        receiver = ATPAccount(available=90.0)
        result = transfer(sender, receiver, 100.0, fee_rate=0.05,
                          max_balance=100.0)
        doc = result.to_jsonld()
        assert doc["actual_credit"] == 10.0  # only 10 space
        assert doc["overflow"] == 90.0


# ── Schema Validation ───────────────────────────────────────────


class TestATPSchemaValidation:
    """Validate JSON-LD output against the JSON Schema."""

    @pytest.fixture(autouse=True)
    def _load_schema(self):
        """Load the ATP JSON-LD schema if jsonschema is available."""
        try:
            import jsonschema
            import os
            schema_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "..",
                "schemas", "atp-jsonld.schema.json"
            )
            with open(schema_path) as f:
                self.schema = json.load(f)
            self.has_jsonschema = True
        except (ImportError, FileNotFoundError):
            self.has_jsonschema = False

    def _validate(self, doc):
        """Validate document against schema."""
        if not self.has_jsonschema:
            pytest.skip("jsonschema not installed")
        import jsonschema
        jsonschema.validate(doc, self.schema)

    def test_account_validates(self):
        """ATPAccount.to_jsonld() output validates against schema."""
        acct = ATPAccount(available=1000.0, locked=200.0, adp=300.0,
                          initial_balance=1500.0)
        self._validate(acct.to_jsonld())

    def test_minimal_account_validates(self):
        """Default ATPAccount validates against schema."""
        self._validate(ATPAccount().to_jsonld())

    def test_transfer_result_validates(self):
        """TransferResult.to_jsonld() output validates against schema."""
        result = TransferResult(fee=5.0, sender_balance=895.0,
                                receiver_balance=100.0, actual_credit=100.0)
        self._validate(result.to_jsonld())

    def test_transfer_with_overflow_validates(self):
        """TransferResult with overflow validates against schema."""
        result = TransferResult(fee=5.0, sender_balance=950.0,
                                receiver_balance=50.0, actual_credit=30.0,
                                overflow=20.0)
        self._validate(result.to_jsonld())

    def test_schema_rejects_extra_fields(self):
        """Schema rejects documents with additional properties."""
        if not self.has_jsonschema:
            pytest.skip("jsonschema not installed")
        import jsonschema
        doc = ATPAccount(available=100.0).to_jsonld()
        doc["extra_field"] = "should fail"
        with pytest.raises(jsonschema.ValidationError):
            self._validate(doc)

    def test_schema_rejects_missing_required(self):
        """Schema rejects documents missing required fields."""
        if not self.has_jsonschema:
            pytest.skip("jsonschema not installed")
        import jsonschema
        doc = ATPAccount(available=100.0).to_jsonld()
        del doc["available"]
        with pytest.raises(jsonschema.ValidationError):
            self._validate(doc)
