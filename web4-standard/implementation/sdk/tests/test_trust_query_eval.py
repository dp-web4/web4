"""Tests for evaluate_trust_query() — the trust resolution pipeline.

Tests the composition of TrustQuery + TrustProfile + ATPAccount into
TrustQueryResponse, covering: ATP stake locking, role lookup, disclosure
level filtering, timestamp handling, and rejection paths.
"""

from web4 import (
    T3,
    V3,
    ATPAccount,
    DisclosureLevel,
    TrustProfile,
    TrustQuery,
    TrustQueryResponse,
    evaluate_trust_query,
)

# ── Helpers ─────────────────────────────────────────────────────


def _make_query(
    stake: int = 100,
    disclosure: DisclosureLevel = DisclosureLevel.PRECISE,
    role: str = "web4:Surgeon",
    validity: int = 3600,
    timestamp: str | None = "2025-09-14T12:00:00Z",
) -> TrustQuery:
    return TrustQuery(
        querier="lct:web4:alice",
        target_entity="lct:web4:bob",
        requested_role=role,
        intended_interaction="surgical-procedure",
        atp_stake=stake,
        validity_period=validity,
        signature="sig:test",
        disclosure_level=disclosure,
        timestamp=timestamp,
    )


def _make_profile(
    role: str = "web4:Surgeon",
    t3: T3 | None = None,
    v3: V3 | None = None,
) -> TrustProfile:
    profile = TrustProfile("lct:web4:bob")
    profile.set_role(role, t3=t3 or T3(0.95, 0.92, 0.88), v3=v3 or V3(0.8, 0.9, 0.85))
    return profile


# ── Basic approval flow ─────────────────────────────────────────


class TestApprovalFlow:
    """Test the happy path: valid query + sufficient ATP → APPROVED."""

    def test_basic_approval(self) -> None:
        query = _make_query()
        profile = _make_profile()
        atp = ATPAccount(available=500.0)

        result = evaluate_trust_query(query, profile, atp)

        assert result.is_approved
        assert result.status == "APPROVED"
        assert result.entity == "lct:web4:bob"
        assert result.role == "web4:Surgeon"
        assert result.stake_locked == 100

    def test_atp_locked_after_approval(self) -> None:
        atp = ATPAccount(available=500.0)
        evaluate_trust_query(_make_query(), _make_profile(), atp)

        assert atp.available == 400.0
        assert atp.locked == 100.0

    def test_t3_returned_precise(self) -> None:
        query = _make_query(disclosure=DisclosureLevel.PRECISE)
        profile = _make_profile(t3=T3(0.95, 0.92, 0.88))
        result = evaluate_trust_query(query, profile, ATPAccount(available=500.0))

        assert result.t3_in_role is not None
        assert result.t3_in_role.talent == 0.95
        assert result.t3_in_role.training == 0.92
        assert result.t3_in_role.temperament == 0.88

    def test_validity_until_computed(self) -> None:
        query = _make_query(validity=3600, timestamp="2025-09-14T12:00:00Z")
        result = evaluate_trust_query(query, _make_profile(), ATPAccount(available=500.0))

        assert result.validity_until == "2025-09-14T13:00:00Z"

    def test_commitment_message(self) -> None:
        query = _make_query(validity=3600)
        result = evaluate_trust_query(query, _make_profile(), ATPAccount(available=500.0))

        assert result.commitment == "Must engage within 3600 seconds or forfeit stake"

    def test_audit_log_populated(self) -> None:
        query = _make_query(timestamp="2025-09-14T12:00:00Z")
        result = evaluate_trust_query(query, _make_profile(), ATPAccount(available=500.0))

        assert result.audit_log is not None
        assert result.audit_log["querier"] == "lct:web4:alice"
        assert result.audit_log["target"] == "lct:web4:bob"
        assert result.audit_log["role"] == "web4:Surgeon"
        assert result.audit_log["stake"] == 100
        assert result.audit_log["timestamp"] == "2025-09-14T12:00:00Z"

    def test_matches_test_vector_valid_staked(self) -> None:
        """Verify against web4-standard/test-vectors/trust-query/valid-staked-query.json."""
        query = TrustQuery(
            querier="lct:web4:alice",
            target_entity="lct:web4:bob",
            requested_role="web4:Surgeon",
            intended_interaction="surgical-procedure",
            atp_stake=100,
            validity_period=3600,
            query_justification="Patient requiring surgery",
            disclosure_level=DisclosureLevel.PRECISE,
            signature="sig:test",
            timestamp="2025-09-14T12:00:00Z",
        )
        profile = _make_profile(t3=T3(0.95, 0.92, 0.88))
        atp = ATPAccount(available=500.0)

        result = evaluate_trust_query(query, profile, atp, timestamp="2025-09-14T12:00:00Z")

        assert result.status == "APPROVED"
        assert result.entity == "lct:web4:bob"
        assert result.role == "web4:Surgeon"
        assert result.t3_in_role is not None
        assert result.t3_in_role.talent == 0.95
        assert result.t3_in_role.training == 0.92
        assert result.t3_in_role.temperament == 0.88
        assert result.validity_until == "2025-09-14T13:00:00Z"
        assert result.stake_locked == 100
        assert result.commitment is not None
        assert "3600" in result.commitment


# ── Rejection: insufficient ATP ─────────────────────────────────


class TestRejectionInsufficientATP:
    """Test rejection when requester lacks ATP for the stake."""

    def test_rejected_insufficient_atp(self) -> None:
        query = _make_query(stake=100)
        atp = ATPAccount(available=50.0)

        result = evaluate_trust_query(query, _make_profile(), atp)

        assert not result.is_approved
        assert result.status == "REJECTED"
        assert result.error_code == "INSUFFICIENT_STAKE"

    def test_atp_unchanged_on_rejection(self) -> None:
        atp = ATPAccount(available=50.0)
        evaluate_trust_query(_make_query(stake=100), _make_profile(), atp)

        assert atp.available == 50.0
        assert atp.locked == 0.0

    def test_rejection_error_details(self) -> None:
        query = _make_query(stake=100)
        atp = ATPAccount(available=50.0)

        result = evaluate_trust_query(query, _make_profile(), atp)

        assert result.minimum_required == 100
        assert result.error_message is not None

    def test_exact_balance_succeeds(self) -> None:
        """Edge: exactly enough ATP should succeed."""
        query = _make_query(stake=100)
        atp = ATPAccount(available=100.0)

        result = evaluate_trust_query(query, _make_profile(), atp)

        assert result.is_approved
        assert atp.available == 0.0
        assert atp.locked == 100.0


# ── Disclosure levels ───────────────────────────────────────────


class TestDisclosureLevels:
    """Test disclosure level filtering of trust data."""

    def test_precise_returns_full_t3(self) -> None:
        query = _make_query(disclosure=DisclosureLevel.PRECISE)
        profile = _make_profile(t3=T3(0.9, 0.8, 0.7))
        result = evaluate_trust_query(query, profile, ATPAccount(available=500.0))

        assert result.t3_in_role is not None
        assert result.t3_in_role.talent == 0.9
        assert result.t3_in_role.training == 0.8
        assert result.t3_in_role.temperament == 0.7

    def test_range_returns_uniform_composite(self) -> None:
        """Range mode: dimensions hidden, composite exposed as uniform T3."""
        query = _make_query(disclosure=DisclosureLevel.RANGE)
        profile = _make_profile(t3=T3(0.9, 0.8, 0.7))
        result = evaluate_trust_query(query, profile, ATPAccount(available=500.0))

        assert result.t3_in_role is not None
        expected_composite = T3(0.9, 0.8, 0.7).composite
        assert result.t3_in_role.talent == expected_composite
        assert result.t3_in_role.training == expected_composite
        assert result.t3_in_role.temperament == expected_composite

    def test_binary_returns_no_t3(self) -> None:
        """Binary mode: no trust tensor in response."""
        query = _make_query(disclosure=DisclosureLevel.BINARY)
        result = evaluate_trust_query(query, _make_profile(), ATPAccount(available=500.0))

        assert result.is_approved
        assert result.t3_in_role is None


# ── Role lookup edge cases ──────────────────────────────────────


class TestRoleLookup:
    """Test role lookup behavior via TrustProfile."""

    def test_unknown_role_returns_default_t3(self) -> None:
        """Querying a role not in the profile returns default T3 (0.5, 0.5, 0.5)."""
        query = _make_query(role="web4:UnknownRole")
        profile = _make_profile(role="web4:Surgeon")  # different role
        result = evaluate_trust_query(query, profile, ATPAccount(available=500.0))

        assert result.is_approved
        assert result.t3_in_role is not None
        assert result.t3_in_role.talent == 0.5
        assert result.t3_in_role.training == 0.5
        assert result.t3_in_role.temperament == 0.5

    def test_multiple_roles_returns_correct_one(self) -> None:
        """Profile with multiple roles returns the queried one."""
        profile = TrustProfile("lct:web4:bob")
        profile.set_role("web4:Surgeon", t3=T3(0.95, 0.92, 0.88))
        profile.set_role("web4:Mechanic", t3=T3(0.6, 0.7, 0.8))

        query = _make_query(role="web4:Mechanic")
        result = evaluate_trust_query(query, profile, ATPAccount(available=500.0))

        assert result.t3_in_role is not None
        assert result.t3_in_role.talent == 0.6
        assert result.t3_in_role.training == 0.7
        assert result.t3_in_role.temperament == 0.8


# ── Timestamp handling ──────────────────────────────────────────


class TestTimestampHandling:
    """Test timestamp and validity_until computation."""

    def test_no_timestamp_no_validity_until(self) -> None:
        query = _make_query(timestamp=None)
        result = evaluate_trust_query(query, _make_profile(), ATPAccount(available=500.0))

        assert result.validity_until is None

    def test_explicit_timestamp_override(self) -> None:
        query = _make_query(timestamp="2025-09-14T12:00:00Z")
        result = evaluate_trust_query(
            query, _make_profile(), ATPAccount(available=500.0),
            timestamp="2025-09-14T15:00:00Z",
        )

        # Explicit timestamp overrides query timestamp
        assert result.validity_until == "2025-09-14T16:00:00Z"
        assert result.audit_log is not None
        assert result.audit_log["timestamp"] == "2025-09-14T15:00:00Z"

    def test_various_validity_periods(self) -> None:
        for period, expected_until in [
            (300, "2025-09-14T12:05:00Z"),
            (86400, "2025-09-15T12:00:00Z"),
        ]:
            query = _make_query(validity=period)
            result = evaluate_trust_query(query, _make_profile(), ATPAccount(available=500.0))
            assert result.validity_until == expected_until


# ── Response serialization round-trip ───────────────────────────


class TestResponseRoundTrip:
    """Verify evaluate_trust_query output round-trips via to_dict/from_dict."""

    def test_approved_response_round_trips(self) -> None:
        result = evaluate_trust_query(
            _make_query(), _make_profile(), ATPAccount(available=500.0),
        )
        d = result.to_dict()
        restored = TrustQueryResponse.from_dict(d)

        assert restored.status == result.status
        assert restored.entity == result.entity
        assert restored.role == result.role
        assert restored.stake_locked == result.stake_locked
        if result.t3_in_role is not None:
            assert restored.t3_in_role is not None
            assert restored.t3_in_role.talent == result.t3_in_role.talent

    def test_rejected_response_round_trips(self) -> None:
        result = evaluate_trust_query(
            _make_query(stake=100), _make_profile(), ATPAccount(available=10.0),
        )
        d = result.to_dict()
        restored = TrustQueryResponse.from_dict(d)

        assert restored.status == "REJECTED"
        assert restored.error_code == result.error_code


# ── ATP accounting correctness ──────────────────────────────────


class TestATPAccounting:
    """Verify ATP mutations are correct."""

    def test_multiple_queries_drain_atp(self) -> None:
        atp = ATPAccount(available=250.0)

        evaluate_trust_query(_make_query(stake=100), _make_profile(), atp)
        assert atp.available == 150.0
        assert atp.locked == 100.0

        evaluate_trust_query(_make_query(stake=100), _make_profile(), atp)
        assert atp.available == 50.0
        assert atp.locked == 200.0

        # Third query should fail
        result = evaluate_trust_query(_make_query(stake=100), _make_profile(), atp)
        assert not result.is_approved
        assert atp.available == 50.0  # unchanged

    def test_minimum_stake_query(self) -> None:
        """Minimum stake (10 ATP) works."""
        query = _make_query(stake=10)
        atp = ATPAccount(available=10.0)

        result = evaluate_trust_query(query, _make_profile(), atp)

        assert result.is_approved
        assert atp.available == 0.0
        assert atp.locked == 10.0
