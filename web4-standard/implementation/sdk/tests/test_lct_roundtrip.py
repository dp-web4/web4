"""Round-trip tests for LCT module from_dict() methods.

Validates from_dict(x.to_dict()) round-trips for LCT and all nested types.
Follows N1-Q1 precedent (security, r6, reputation, protocol, acp).

Note: LCT.to_dict() is a subset format (no attestations, lineage, revocation_ts/reason,
hardware_anchor). The round-trip test verifies that from_dict faithfully reconstructs
all fields that to_dict produces. Tolerance of extra fields is tested separately.
"""
from __future__ import annotations

import pytest

from web4.lct import (
    LCT,
    MRH,
    Attestation,
    Binding,
    BirthCertificate,
    EntityType,
    LineageEntry,
    MRHPairing,
    Policy,
    RevocationStatus,
)
from web4.trust import T3, V3

# ── Binding ─────────────────────────────────────────────────────


class TestBindingRoundTrip:
    def test_basic(self) -> None:
        b = Binding(entity_type=EntityType.AI, public_key="pk1", created_at="2025-01-01T00:00:00Z")
        assert Binding.from_dict(b.__dict__ | {"entity_type": b.entity_type.value}) == b

    def test_from_lct_to_dict_format(self) -> None:
        """Binding dict as produced by LCT.to_dict()."""
        d = {"entity_type": "human", "public_key": "pk2", "created_at": "2025-06-01T00:00:00Z",
             "binding_proof": "sig:abc"}
        b = Binding.from_dict(d)
        assert b.entity_type == EntityType.HUMAN
        assert b.public_key == "pk2"
        assert b.binding_proof == "sig:abc"
        assert b.hardware_anchor is None

    def test_with_hardware_anchor(self) -> None:
        d = {"entity_type": "device", "public_key": "pk3", "created_at": "2025-01-01T00:00:00Z",
             "binding_proof": "", "hardware_anchor": "tpm:ek:abc"}
        b = Binding.from_dict(d)
        assert b.hardware_anchor == "tpm:ek:abc"


# ── MRHPairing ──────────────────────────────────────────────────


class TestMRHPairingRoundTrip:
    def test_basic(self) -> None:
        p = MRHPairing(lct_id="lct:1", pairing_type="birth_certificate", permanent=True, ts="2025-01-01T00:00:00Z")
        d = {"lct_id": p.lct_id, "pairing_type": p.pairing_type, "permanent": p.permanent, "ts": p.ts}
        assert MRHPairing.from_dict(d) == p

    def test_defaults(self) -> None:
        d = {"lct_id": "lct:2", "pairing_type": "role"}
        p = MRHPairing.from_dict(d)
        assert p.permanent is False
        assert p.ts == ""


# ── MRH ─────────────────────────────────────────────────────────


class TestMRHRoundTrip:
    def test_empty(self) -> None:
        m = MRH()
        d = {"bound": [], "paired": [], "witnessing": [], "horizon_depth": 3, "last_updated": ""}
        assert MRH.from_dict(d) == m

    def test_with_pairings(self) -> None:
        m = MRH(
            bound=["lct:bound1"],
            paired=[MRHPairing(lct_id="lct:role1", pairing_type="role", permanent=False, ts="2025-01-01T00:00:00Z")],
            witnessing=["lct:w1", "lct:w2"],
            horizon_depth=5,
            last_updated="2025-06-01T00:00:00Z",
        )
        d = {
            "bound": ["lct:bound1"],
            "paired": [
                {"lct_id": "lct:role1", "pairing_type": "role", "permanent": False, "ts": "2025-01-01T00:00:00Z"}
            ],
            "witnessing": ["lct:w1", "lct:w2"],
            "horizon_depth": 5,
            "last_updated": "2025-06-01T00:00:00Z",
        }
        assert MRH.from_dict(d) == m

    def test_defaults_from_empty(self) -> None:
        m = MRH.from_dict({})
        assert m.bound == []
        assert m.paired == []
        assert m.horizon_depth == 3


# ── BirthCertificate ────────────────────────────────────────────


class TestBirthCertificateRoundTrip:
    def test_basic(self) -> None:
        bc = BirthCertificate(
            issuing_society="lct:web4:society:genesis",
            citizen_role="lct:web4:role:citizen:platform",
            birth_timestamp="2025-01-01T00:00:00Z",
            birth_witnesses=["lct:w1", "lct:w2"],
            birth_context="platform",
        )
        d = {
            "issuing_society": bc.issuing_society,
            "citizen_role": bc.citizen_role,
            "birth_timestamp": bc.birth_timestamp,
            "birth_witnesses": list(bc.birth_witnesses),
            "birth_context": bc.birth_context,
        }
        assert BirthCertificate.from_dict(d) == bc

    def test_with_genesis_hash(self) -> None:
        d = {
            "issuing_society": "s1", "citizen_role": "r1", "birth_timestamp": "2025-01-01T00:00:00Z",
            "genesis_block_hash": "0xabc123",
        }
        bc = BirthCertificate.from_dict(d)
        assert bc.genesis_block_hash == "0xabc123"

    def test_defaults(self) -> None:
        d = {"issuing_society": "s1", "citizen_role": "r1", "birth_timestamp": "2025-01-01T00:00:00Z"}
        bc = BirthCertificate.from_dict(d)
        assert bc.birth_witnesses == []
        assert bc.birth_context == "platform"
        assert bc.genesis_block_hash is None


# ── Attestation ─────────────────────────────────────────────────


class TestAttestationRoundTrip:
    def test_basic(self) -> None:
        a = Attestation(witness="lct:w1", type="identity_verification",
                        claims={"verified": True}, sig="sig:abc", ts="2025-01-01T00:00:00Z")
        d = {"witness": a.witness, "type": a.type, "claims": dict(a.claims), "sig": a.sig, "ts": a.ts}
        assert Attestation.from_dict(d) == a

    def test_defaults(self) -> None:
        d = {"witness": "lct:w1", "type": "presence"}
        a = Attestation.from_dict(d)
        assert a.claims == {}
        assert a.sig == ""
        assert a.ts == ""


# ── LineageEntry ────────────────────────────────────────────────


class TestLineageEntryRoundTrip:
    def test_basic(self) -> None:
        le = LineageEntry(parent="lct:parent1", reason="genesis", ts="2025-01-01T00:00:00Z")
        d = {"parent": le.parent, "reason": le.reason, "ts": le.ts}
        assert LineageEntry.from_dict(d) == le

    def test_defaults(self) -> None:
        d = {"parent": "lct:p1", "reason": "rotation"}
        le = LineageEntry.from_dict(d)
        assert le.ts == ""


# ── Policy ──────────────────────────────────────────────────────


class TestPolicyRoundTrip:
    def test_basic(self) -> None:
        p = Policy(capabilities=["read", "write"], constraints={"max_rate": 100})
        d = {"capabilities": list(p.capabilities), "constraints": dict(p.constraints)}
        assert Policy.from_dict(d) == p

    def test_empty(self) -> None:
        p = Policy.from_dict({})
        assert p.capabilities == []
        assert p.constraints == {}


# ── LCT ─────────────────────────────────────────────────────────


class TestLCTRoundTrip:
    def test_to_dict_from_dict_roundtrip(self) -> None:
        """Core test: from_dict(to_dict()) produces equivalent dict output."""
        lct = LCT.create(
            entity_type=EntityType.AI,
            public_key="mb64:testkey123456789",
            society="lct:web4:society:testnet",
            context="platform",
            witnesses=["lct:w1", "lct:w2"],
            timestamp="2025-10-01T00:00:00Z",
            t3=T3(talent=0.85, training=0.92, temperament=0.78),
            v3=V3(valuation=0.89, veracity=0.91, validity=0.76),
        )
        d = lct.to_dict()
        restored = LCT.from_dict(d)
        assert restored.to_dict() == d

    def test_minimal_lct(self) -> None:
        """LCT without birth certificate."""
        lct = LCT(
            lct_id="lct:test:1",
            subject="did:web4:key:abc",
            binding=Binding(entity_type=EntityType.HUMAN, public_key="pk1", created_at="2025-01-01T00:00:00Z"),
        )
        d = lct.to_dict()
        restored = LCT.from_dict(d)
        assert restored.to_dict() == d
        assert restored.birth_certificate is None

    def test_revoked_lct(self) -> None:
        """Revocation status round-trips."""
        lct = LCT(
            lct_id="lct:test:2",
            subject="did:web4:key:def",
            binding=Binding(entity_type=EntityType.SERVICE, public_key="pk2", created_at="2025-01-01T00:00:00Z"),
            revocation_status=RevocationStatus.REVOKED,
        )
        d = lct.to_dict()
        restored = LCT.from_dict(d)
        assert restored.revocation_status == RevocationStatus.REVOKED

    def test_suspended_lct(self) -> None:
        lct = LCT(
            lct_id="lct:test:3",
            subject="did:web4:key:ghi",
            binding=Binding(entity_type=EntityType.DEVICE, public_key="pk3", created_at="2025-01-01T00:00:00Z"),
            revocation_status=RevocationStatus.SUSPENDED,
        )
        d = lct.to_dict()
        restored = LCT.from_dict(d)
        assert restored.revocation_status == RevocationStatus.SUSPENDED

    def test_custom_tensors(self) -> None:
        """T3/V3 values preserved through round-trip."""
        lct = LCT(
            lct_id="lct:test:4",
            subject="did:web4:key:jkl",
            binding=Binding(entity_type=EntityType.AI, public_key="pk4", created_at="2025-01-01T00:00:00Z"),
            t3=T3(talent=0.1, training=0.2, temperament=0.3),
            v3=V3(valuation=0.4, veracity=0.5, validity=0.6),
        )
        d = lct.to_dict()
        restored = LCT.from_dict(d)
        assert restored.t3.talent == pytest.approx(0.1)
        assert restored.t3.training == pytest.approx(0.2)
        assert restored.t3.temperament == pytest.approx(0.3)
        assert restored.v3.valuation == pytest.approx(0.4)
        assert restored.v3.veracity == pytest.approx(0.5)
        assert restored.v3.validity == pytest.approx(0.6)

    def test_mrh_with_pairings(self) -> None:
        """MRH pairings preserved."""
        lct = LCT(
            lct_id="lct:test:5",
            subject="did:web4:key:mno",
            binding=Binding(entity_type=EntityType.ORGANIZATION, public_key="pk5", created_at="2025-01-01T00:00:00Z"),
            mrh=MRH(
                bound=["lct:bound1"],
                paired=[
                    MRHPairing(lct_id="lct:role1", pairing_type="role", permanent=True, ts="2025-01-01T00:00:00Z"),
                    MRHPairing(
                        lct_id="lct:role2", pairing_type="delegation", permanent=False, ts="2025-06-01T00:00:00Z"
                    ),
                ],
                witnessing=["lct:w1"],
                horizon_depth=4,
                last_updated="2025-06-01T00:00:00Z",
            ),
        )
        d = lct.to_dict()
        restored = LCT.from_dict(d)
        assert restored.to_dict() == d
        assert len(restored.mrh.paired) == 2
        assert restored.mrh.paired[0].permanent is True

    def test_policy_with_constraints(self) -> None:
        """Policy capabilities and constraints round-trip."""
        lct = LCT(
            lct_id="lct:test:6",
            subject="did:web4:key:pqr",
            binding=Binding(entity_type=EntityType.AI, public_key="pk6", created_at="2025-01-01T00:00:00Z"),
            policy=Policy(
                capabilities=["exist", "interact", "accumulate_reputation", "vote"],
                constraints={"max_rate": 100, "zone": "platform"},
            ),
        )
        d = lct.to_dict()
        restored = LCT.from_dict(d)
        assert restored.to_dict() == d

    def test_tolerant_of_attestations(self) -> None:
        """from_dict() parses attestations if present (forward-compatible)."""
        d = {
            "lct_id": "lct:test:7",
            "subject": "did:web4:key:stu",
            "binding": {"entity_type": "ai", "public_key": "pk7", "created_at": "2025-01-01T00:00:00Z",
                        "binding_proof": ""},
            "revocation": {"status": "active"},
            "attestations": [
                {"witness": "lct:w1", "type": "presence", "claims": {}, "sig": "", "ts": "2025-01-01T00:00:00Z"},
            ],
        }
        lct = LCT.from_dict(d)
        assert len(lct.attestations) == 1
        assert lct.attestations[0].witness == "lct:w1"

    def test_tolerant_of_lineage(self) -> None:
        """from_dict() parses lineage if present (forward-compatible)."""
        d = {
            "lct_id": "lct:test:8",
            "subject": "did:web4:key:vwx",
            "binding": {"entity_type": "human", "public_key": "pk8", "created_at": "2025-01-01T00:00:00Z",
                        "binding_proof": ""},
            "revocation": {"status": "active"},
            "lineage": [
                {"parent": "lct:parent1", "reason": "genesis", "ts": "2025-01-01T00:00:00Z"},
            ],
        }
        lct = LCT.from_dict(d)
        assert len(lct.lineage) == 1
        assert lct.lineage[0].reason == "genesis"

    def test_all_entity_types(self) -> None:
        """All EntityType values round-trip through from_dict."""
        for et in EntityType:
            lct = LCT(
                lct_id=f"lct:test:{et.value}",
                subject=f"did:web4:key:{et.value}",
                binding=Binding(entity_type=et, public_key="pk", created_at="2025-01-01T00:00:00Z"),
            )
            d = lct.to_dict()
            restored = LCT.from_dict(d)
            assert restored.binding.entity_type == et
