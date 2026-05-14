"""Round-trip tests for R6 component from_dict() methods.

Validates from_dict(x.to_dict()) == x for all 12 R6 component classes.
Follows N1 (security.py) precedent — PR #119.
"""

from __future__ import annotations

from web4.r6 import (
    ActionStatus,
    Constraint,
    ContributingFactor,
    Precedent,
    ProofOfAgency,
    Reference,
    Request,
    ResourceRequirements,
    Result,
    Role,
    Rules,
    TensorDelta,
    WitnessAttestation,
)
from web4.trust import T3, V3


class TestConstraintRoundTrip:
    def test_basic(self) -> None:
        c = Constraint(constraint_type="rate_limit", threshold=100)
        assert Constraint.from_dict(c.to_dict()) == c

    def test_hard_default(self) -> None:
        c = Constraint(constraint_type="witness_quorum", threshold=3.0)
        assert c.hard is True
        assert Constraint.from_dict(c.to_dict()) == c

    def test_soft_constraint(self) -> None:
        c = Constraint(constraint_type="rate_limit", threshold=100, hard=False)
        assert c.hard is False
        assert Constraint.from_dict(c.to_dict()) == c

    def test_float_value(self) -> None:
        c = Constraint(constraint_type="atp_minimum", threshold=50.5)
        assert Constraint.from_dict(c.to_dict()) == c

    def test_legacy_value_key(self) -> None:
        """from_dict accepts legacy 'value' key for backward compatibility."""
        d = {"type": "atp_minimum", "value": 42}
        c = Constraint.from_dict(d)
        assert c.threshold == 42.0
        assert c.hard is True


class TestRulesRoundTrip:
    def test_empty(self) -> None:
        r = Rules()
        assert Rules.from_dict(r.to_dict()) == r

    def test_full(self) -> None:
        r = Rules(
            law_hash="abc123",
            society="test-society",
            constraints=[
                Constraint("rate_limit", 100.0),
                Constraint("atp_minimum", 10.0),
            ],
            permissions=["read", "write"],
            prohibitions=["delete"],
        )
        assert Rules.from_dict(r.to_dict()) == r


class TestRoleRoundTrip:
    def test_minimal(self) -> None:
        role = Role(actor="actor-1", role_lct="role-1")
        assert Role.from_dict(role.to_dict()) == role

    def test_with_tensors(self) -> None:
        role = Role(
            actor="actor-1",
            role_lct="role-1",
            paired_at="2026-01-01T00:00:00Z",
            t3_in_role=T3(talent=0.8, training=0.7, temperament=0.9),
            v3_in_role=V3(valuation=0.6, veracity=0.5, validity=0.4),
        )
        assert Role.from_dict(role.to_dict()) == role

    def test_without_v3(self) -> None:
        role = Role(
            actor="a1",
            role_lct="r1",
            t3_in_role=T3(talent=0.5, training=0.5, temperament=0.5),
        )
        assert Role.from_dict(role.to_dict()) == role


class TestProofOfAgencyRoundTrip:
    def test_minimal(self) -> None:
        poa = ProofOfAgency(grant_id="g1")
        assert ProofOfAgency.from_dict(poa.to_dict()) == poa

    def test_full(self) -> None:
        poa = ProofOfAgency(
            grant_id="g1",
            inclusion_proof="proof-data",
            scope="read:data",
            audience=["aud1", "aud2"],
        )
        assert ProofOfAgency.from_dict(poa.to_dict()) == poa


class TestRequestRoundTrip:
    def test_minimal(self) -> None:
        req = Request(action="test")
        assert Request.from_dict(req.to_dict()) == req

    def test_full(self) -> None:
        poa = ProofOfAgency(grant_id="g1", scope="full")
        req = Request(
            action="analyze_dataset",
            target="dataset-42",
            parameters={"depth": 3, "mode": "fast"},
            atp_stake=5.0,
            nonce="nonce-123",
            constraints={"timeout": 60},
            proof_of_agency=poa,
        )
        assert Request.from_dict(req.to_dict()) == req

    def test_without_proof(self) -> None:
        req = Request(action="query", target="t1", atp_stake=1.0)
        assert Request.from_dict(req.to_dict()) == req


class TestPrecedentRoundTrip:
    def test_basic(self) -> None:
        p = Precedent(action_hash="h1", outcome="success", relevance=0.95)
        assert Precedent.from_dict(p.to_dict()) == p

    def test_minimal(self) -> None:
        p = Precedent(action_hash="h1")
        assert Precedent.from_dict(p.to_dict()) == p


class TestWitnessAttestationRoundTrip:
    def test_full(self) -> None:
        wa = WitnessAttestation(
            lct="witness-1",
            attestation="verified",
            signature="sig-data",
            timestamp="2026-01-01T00:00:00Z",
        )
        assert WitnessAttestation.from_dict(wa.to_dict()) == wa

    def test_minimal(self) -> None:
        wa = WitnessAttestation(lct="w1")
        assert WitnessAttestation.from_dict(wa.to_dict()) == wa


class TestReferenceRoundTrip:
    def test_empty(self) -> None:
        ref = Reference()
        assert Reference.from_dict(ref.to_dict()) == ref

    def test_full(self) -> None:
        ref = Reference(
            precedents=[
                Precedent(action_hash="h1", outcome="success", relevance=0.9),
                Precedent(action_hash="h2", outcome="failure", relevance=0.3),
            ],
            mrh_depth=3,
            relevant_entities=["e1", "e2"],
            witnesses=[
                WitnessAttestation(lct="w1", attestation="verified", signature="s1"),
            ],
        )
        assert Reference.from_dict(ref.to_dict()) == ref


class TestResourceRequirementsRoundTrip:
    def test_minimal(self) -> None:
        rr = ResourceRequirements()
        assert ResourceRequirements.from_dict(rr.to_dict()) == rr

    def test_with_escrow(self) -> None:
        rr = ResourceRequirements(
            required_atp=10.0,
            available_atp=20.0,
            escrow_amount=5.0,
            escrow_condition="result_verified",
        )
        assert ResourceRequirements.from_dict(rr.to_dict()) == rr

    def test_with_compute(self) -> None:
        rr = ResourceRequirements(
            required_atp=10.0,
            available_atp=20.0,
            compute={"cpu": "2_cores", "memory": "4GB"},
        )
        assert ResourceRequirements.from_dict(rr.to_dict()) == rr

    def test_full(self) -> None:
        rr = ResourceRequirements(
            required_atp=10.0,
            available_atp=20.0,
            compute={"cpu": "2_cores"},
            escrow_amount=5.0,
            escrow_condition="done",
        )
        assert ResourceRequirements.from_dict(rr.to_dict()) == rr


class TestResultRoundTrip:
    def test_pending(self) -> None:
        res = Result(status=ActionStatus.PENDING, output={"data": 42})
        assert Result.from_dict(res.to_dict()) == res

    def test_success_no_hash(self) -> None:
        res = Result(
            status=ActionStatus.SUCCESS,
            output={"score": 0.95},
            atp_consumed=3.0,
        )
        assert Result.from_dict(res.to_dict()) == res

    def test_failure_with_error(self) -> None:
        res = Result(
            status=ActionStatus.FAILURE,
            error="something went wrong",
            atp_consumed=1.0,
        )
        assert Result.from_dict(res.to_dict()) == res

    def test_with_attestations(self) -> None:
        wa = WitnessAttestation(lct="w1", attestation="verified")
        res = Result(
            status=ActionStatus.SUCCESS,
            output={"ok": True},
            atp_consumed=2.0,
            attestations=[wa],
        )
        assert Result.from_dict(res.to_dict()) == res

    def test_with_output_hash_via_dict(self) -> None:
        """Test Result with output_hash using dict comparison.

        Note: Result.to_dict() merges output_hash into the output dict,
        mutating self.output. We test via dict-to-dict comparison to
        verify from_dict() correctly separates them.
        """
        d = {
            "status": "success",
            "output": {"data": 42, "hash": "h123"},
            "resourceConsumed": {"atp": 3.0},
        }
        res = Result.from_dict(d)
        assert res.output == {"data": 42}
        assert res.output_hash == "h123"
        assert res.atp_consumed == 3.0


class TestTensorDeltaRoundTrip:
    def test_basic(self) -> None:
        td = TensorDelta(change=0.1, from_value=0.5, to_value=0.6)
        assert TensorDelta.from_dict(td.to_dict()) == td

    def test_negative(self) -> None:
        td = TensorDelta(change=-0.2, from_value=0.8, to_value=0.6)
        assert TensorDelta.from_dict(td.to_dict()) == td


class TestContributingFactorRoundTrip:
    def test_basic(self) -> None:
        cf = ContributingFactor(factor="quality", weight=0.8)
        assert ContributingFactor.from_dict(cf.to_dict()) == cf

    def test_zero_weight(self) -> None:
        cf = ContributingFactor(factor="neutral", weight=0.0)
        assert ContributingFactor.from_dict(cf.to_dict()) == cf
