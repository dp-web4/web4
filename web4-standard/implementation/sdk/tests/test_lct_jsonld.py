"""
LCT JSON-LD spec compliance tests.

Validates that LCT.to_jsonld() produces documents matching the canonical
structure defined in web4-standard/core-spec/LCT-linked-context-token.md §2.3.

Tests verify:
- Structural compliance (all required fields, correct nesting)
- Field naming (spec-compliant names)
- Roundtrip integrity (to_jsonld → from_jsonld → identical state)
- Optional section handling (attestations, lineage, birth certificate)
- Backward compatibility with SDK internal format (from_jsonld accepts both)
"""

import json

import pytest

from web4.lct import (
    LCT,
    Attestation,
    Binding,
    BirthCertificate,
    EntityType,
    LCT_JSONLD_CONTEXT,
    LineageEntry,
    MRH,
    MRHPairing,
    Policy,
    RevocationStatus,
)
from web4.trust import T3, V3


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def basic_lct():
    """Minimal LCT via create() factory."""
    return LCT.create(
        entity_type=EntityType.AI,
        public_key="mb64:testkey123456789",
        society="lct:web4:society:testnet",
        context="platform",
        witnesses=["lct:web4:witness:w1", "lct:web4:witness:w2", "lct:web4:witness:w3"],
        timestamp="2025-10-01T00:00:00Z",
        t3=T3(talent=0.85, training=0.92, temperament=0.78),
        v3=V3(valuation=0.89, veracity=0.91, validity=0.76),
    )


@pytest.fixture
def full_lct():
    """LCT with all optional fields populated."""
    lct = LCT.create(
        entity_type=EntityType.HUMAN,
        public_key="mb64:fullkey9876543210",
        society="lct:web4:society:mainnet",
        context="nation",
        witnesses=["lct:web4:witness:a", "lct:web4:witness:b"],
        timestamp="2025-10-01T00:00:00Z",
        t3=T3(talent=0.9, training=0.85, temperament=0.88),
        v3=V3(valuation=0.87, veracity=0.93, validity=0.80),
    )
    lct.add_attestation(
        witness="did:web4:key:attestor1",
        type="existence",
        claims={"observed_at": "2025-10-01T12:00:00Z", "method": "blockchain_transaction"},
        sig="cose:ES256:sig1",
        ts="2025-10-01T12:00:00Z",
    )
    lct.add_attestation(
        witness="did:web4:key:attestor2",
        type="quality",
        claims={"score": 0.95},
        sig="cose:ES256:sig2",
        ts="2025-10-02T00:00:00Z",
    )
    lct.lineage.append(LineageEntry(
        parent="lct:web4:mb32:previous123",
        reason="genesis",
        ts="2025-09-01T00:00:00Z",
    ))
    return lct


# ── §2.3 Required Structure Tests ────────────────────────────────


class TestJsonLdRequiredFields:
    """Verify all required fields per spec §2.3."""

    def test_has_context(self, basic_lct):
        doc = basic_lct.to_jsonld()
        assert "@context" in doc
        assert LCT_JSONLD_CONTEXT in doc["@context"]

    def test_has_identity_fields(self, basic_lct):
        doc = basic_lct.to_jsonld()
        assert "lct_id" in doc
        assert "subject" in doc
        assert doc["lct_id"].startswith("lct:web4:")
        assert doc["subject"].startswith("did:web4:")

    def test_has_binding(self, basic_lct):
        doc = basic_lct.to_jsonld()
        binding = doc["binding"]
        assert binding["entity_type"] == "ai"
        assert binding["public_key"] == "mb64:testkey123456789"
        assert binding["created_at"] == "2025-10-01T00:00:00Z"
        assert "binding_proof" in binding

    def test_has_mrh(self, basic_lct):
        doc = basic_lct.to_jsonld()
        mrh = doc["mrh"]
        assert "bound" in mrh
        assert "paired" in mrh
        assert "witnessing" in mrh
        assert "horizon_depth" in mrh
        assert "last_updated" in mrh

    def test_has_policy(self, basic_lct):
        doc = basic_lct.to_jsonld()
        policy = doc["policy"]
        assert "capabilities" in policy
        assert "constraints" in policy

    def test_has_t3_tensor(self, basic_lct):
        doc = basic_lct.to_jsonld()
        t3 = doc["t3_tensor"]
        assert t3["talent"] == 0.85
        assert t3["training"] == 0.92
        assert t3["temperament"] == 0.78
        assert "composite_score" in t3

    def test_has_v3_tensor(self, basic_lct):
        doc = basic_lct.to_jsonld()
        v3 = doc["v3_tensor"]
        assert v3["valuation"] == 0.89
        assert v3["veracity"] == 0.91
        assert v3["validity"] == 0.76
        assert "composite_score" in v3

    def test_has_revocation(self, basic_lct):
        doc = basic_lct.to_jsonld()
        rev = doc["revocation"]
        assert rev["status"] == "active"
        assert "ts" in rev
        assert "reason" in rev

    def test_composite_scores_computed(self, basic_lct):
        doc = basic_lct.to_jsonld()
        # Composite should be a weighted sum, not zero
        assert doc["t3_tensor"]["composite_score"] > 0
        assert doc["v3_tensor"]["composite_score"] > 0


# ── MRH Structure Tests ──────────────────────────────────────────


class TestJsonLdMRH:
    """Verify MRH entries are structured objects per spec §2.3."""

    def test_paired_are_objects(self, basic_lct):
        doc = basic_lct.to_jsonld()
        for entry in doc["mrh"]["paired"]:
            assert isinstance(entry, dict)
            assert "lct_id" in entry
            assert "pairing_type" in entry
            assert "permanent" in entry
            assert "ts" in entry

    def test_citizen_role_is_first_pairing(self, basic_lct):
        doc = basic_lct.to_jsonld()
        first = doc["mrh"]["paired"][0]
        assert first["pairing_type"] == "birth_certificate"
        assert first["permanent"] is True
        assert "citizen" in first["lct_id"]

    def test_bound_are_structured(self):
        """Bound entries should be objects with lct_id."""
        lct = LCT.create(entity_type=EntityType.AI, public_key="mb64:k1")
        lct.mrh.bound.append("lct:web4:hardware:tpm1")
        doc = lct.to_jsonld()
        bound = doc["mrh"]["bound"]
        assert len(bound) == 1
        assert bound[0] == {"lct_id": "lct:web4:hardware:tpm1"}

    def test_witnessing_are_structured(self):
        """Witnessing entries should be objects with lct_id."""
        lct = LCT.create(entity_type=EntityType.AI, public_key="mb64:k2")
        lct.add_witness("lct:web4:witness:oracle1")
        doc = lct.to_jsonld()
        witnessing = doc["mrh"]["witnessing"]
        assert len(witnessing) == 1
        assert witnessing[0] == {"lct_id": "lct:web4:witness:oracle1"}


# ── Birth Certificate Tests ──────────────────────────────────────


class TestJsonLdBirthCertificate:
    """Verify birth certificate uses spec field names."""

    def test_birth_context_field_name(self, basic_lct):
        """Spec uses 'birth_context', not 'context'."""
        doc = basic_lct.to_jsonld()
        bc = doc["birth_certificate"]
        assert "birth_context" in bc
        assert "context" not in bc
        assert bc["birth_context"] == "platform"

    def test_birth_certificate_fields(self, basic_lct):
        doc = basic_lct.to_jsonld()
        bc = doc["birth_certificate"]
        assert bc["issuing_society"] == "lct:web4:society:testnet"
        assert "citizen" in bc["citizen_role"]
        assert bc["birth_timestamp"] == "2025-10-01T00:00:00Z"
        assert len(bc["birth_witnesses"]) == 3

    def test_genesis_block_hash_included_when_set(self):
        lct = LCT(
            lct_id="lct:web4:ai:test",
            subject="did:web4:key:test",
            binding=Binding(entity_type=EntityType.AI, public_key="k", created_at="t"),
            birth_certificate=BirthCertificate(
                issuing_society="lct:web4:society:s1",
                citizen_role="lct:web4:role:citizen:platform",
                birth_timestamp="2025-01-01T00:00:00Z",
                genesis_block_hash="0xabc123",
            ),
        )
        doc = lct.to_jsonld()
        assert doc["birth_certificate"]["genesis_block_hash"] == "0xabc123"

    def test_genesis_block_hash_omitted_when_none(self, basic_lct):
        doc = basic_lct.to_jsonld()
        assert "genesis_block_hash" not in doc["birth_certificate"]

    def test_no_birth_certificate_when_absent(self):
        lct = LCT(
            lct_id="lct:web4:ai:test",
            subject="did:web4:key:test",
            binding=Binding(entity_type=EntityType.AI, public_key="k", created_at="t"),
        )
        doc = lct.to_jsonld()
        assert "birth_certificate" not in doc


# ── Optional Sections ────────────────────────────────────────────


class TestJsonLdOptionalSections:
    """Verify optional sections are included only when populated."""

    def test_attestations_included(self, full_lct):
        doc = full_lct.to_jsonld()
        assert "attestations" in doc
        assert len(doc["attestations"]) == 2
        a = doc["attestations"][0]
        assert a["witness"] == "did:web4:key:attestor1"
        assert a["type"] == "existence"
        assert "claims" in a
        assert a["sig"] == "cose:ES256:sig1"
        assert a["ts"] == "2025-10-01T12:00:00Z"

    def test_attestations_omitted_when_empty(self, basic_lct):
        doc = basic_lct.to_jsonld()
        assert "attestations" not in doc

    def test_lineage_included(self, full_lct):
        doc = full_lct.to_jsonld()
        assert "lineage" in doc
        assert len(doc["lineage"]) == 1
        le = doc["lineage"][0]
        assert le["parent"] == "lct:web4:mb32:previous123"
        assert le["reason"] == "genesis"
        assert le["ts"] == "2025-09-01T00:00:00Z"

    def test_lineage_omitted_when_empty(self, basic_lct):
        doc = basic_lct.to_jsonld()
        assert "lineage" not in doc


# ── Revocation ───────────────────────────────────────────────────


class TestJsonLdRevocation:
    """Verify revocation structure matches spec."""

    def test_active_revocation(self, basic_lct):
        doc = basic_lct.to_jsonld()
        rev = doc["revocation"]
        assert rev["status"] == "active"
        assert rev["ts"] is None
        assert rev["reason"] is None

    def test_revoked_lct(self):
        lct = LCT.create(entity_type=EntityType.AI, public_key="mb64:rk")
        lct.revoke(reason="compromised_key")
        doc = lct.to_jsonld()
        rev = doc["revocation"]
        assert rev["status"] == "revoked"
        assert rev["ts"] is not None
        assert rev["reason"] == "compromised_key"


# ── Hardware Anchor ──────────────────────────────────────────────


class TestJsonLdHardwareAnchor:
    """Verify hardware_anchor handling in binding."""

    def test_hardware_anchor_included(self):
        lct = LCT(
            lct_id="lct:web4:device:hw1",
            subject="did:web4:key:hw1",
            binding=Binding(
                entity_type=EntityType.DEVICE,
                public_key="mb64:hwkey",
                created_at="2025-01-01T00:00:00Z",
                hardware_anchor="eat:mb64:tpm2:intel:abc",
            ),
        )
        doc = lct.to_jsonld()
        assert doc["binding"]["hardware_anchor"] == "eat:mb64:tpm2:intel:abc"

    def test_hardware_anchor_omitted_when_none(self, basic_lct):
        doc = basic_lct.to_jsonld()
        assert "hardware_anchor" not in doc["binding"]


# ── Roundtrip Tests ──────────────────────────────────────────────


class TestJsonLdRoundtrip:
    """Verify to_jsonld → from_jsonld roundtrip preserves data."""

    def test_basic_roundtrip(self, basic_lct):
        doc = basic_lct.to_jsonld()
        restored = LCT.from_jsonld(doc)
        assert restored.lct_id == basic_lct.lct_id
        assert restored.subject == basic_lct.subject
        assert restored.binding.entity_type == basic_lct.binding.entity_type
        assert restored.binding.public_key == basic_lct.binding.public_key
        assert restored.t3.talent == basic_lct.t3.talent
        assert restored.t3.training == basic_lct.t3.training
        assert restored.t3.temperament == basic_lct.t3.temperament
        assert restored.v3.valuation == basic_lct.v3.valuation
        assert restored.revocation_status == basic_lct.revocation_status

    def test_full_roundtrip(self, full_lct):
        doc = full_lct.to_jsonld()
        restored = LCT.from_jsonld(doc)
        assert restored.lct_id == full_lct.lct_id
        assert len(restored.attestations) == 2
        assert restored.attestations[0].witness == "did:web4:key:attestor1"
        assert restored.attestations[1].type == "quality"
        assert len(restored.lineage) == 1
        assert restored.lineage[0].reason == "genesis"

    def test_birth_certificate_roundtrip(self, basic_lct):
        doc = basic_lct.to_jsonld()
        restored = LCT.from_jsonld(doc)
        assert restored.birth_certificate is not None
        assert restored.birth_certificate.issuing_society == basic_lct.birth_certificate.issuing_society
        assert restored.birth_certificate.context == "platform"  # birth_context → context
        assert len(restored.birth_certificate.birth_witnesses) == 3

    def test_mrh_roundtrip(self, basic_lct):
        basic_lct.mrh.bound.append("lct:web4:hardware:dev1")
        basic_lct.add_witness("lct:web4:witness:oracle1")
        doc = basic_lct.to_jsonld()
        restored = LCT.from_jsonld(doc)
        assert "lct:web4:hardware:dev1" in restored.mrh.bound
        assert "lct:web4:witness:oracle1" in restored.mrh.witnessing
        assert len(restored.mrh.paired) == len(basic_lct.mrh.paired)

    def test_revocation_roundtrip(self):
        lct = LCT.create(entity_type=EntityType.AI, public_key="mb64:rr")
        lct.revoke(reason="key_rotation")
        doc = lct.to_jsonld()
        restored = LCT.from_jsonld(doc)
        assert restored.revocation_status == RevocationStatus.REVOKED
        assert restored.revocation_ts is not None
        assert restored.revocation_reason == "key_rotation"

    def test_json_string_roundtrip(self, basic_lct):
        s = basic_lct.to_jsonld_string()
        restored = LCT.from_jsonld_string(s)
        assert restored.lct_id == basic_lct.lct_id
        assert restored.t3.talent == basic_lct.t3.talent

    def test_double_roundtrip_stable(self, full_lct):
        """Two roundtrips should produce identical JSON."""
        doc1 = full_lct.to_jsonld()
        restored1 = LCT.from_jsonld(doc1)
        doc2 = restored1.to_jsonld()
        assert json.dumps(doc1, sort_keys=True) == json.dumps(doc2, sort_keys=True)


# ── Cross-Format Compatibility ───────────────────────────────────


class TestFromJsonLdCompat:
    """Verify from_jsonld handles both spec and SDK formats."""

    def test_accepts_string_bound_entries(self):
        """SDK internal format uses plain strings for bound."""
        doc = {
            "lct_id": "lct:web4:ai:test",
            "subject": "did:web4:key:test",
            "binding": {"entity_type": "ai", "public_key": "k", "created_at": "t"},
            "mrh": {"bound": ["lct:web4:hw:1", "lct:web4:hw:2"]},
        }
        lct = LCT.from_jsonld(doc)
        assert lct.mrh.bound == ["lct:web4:hw:1", "lct:web4:hw:2"]

    def test_accepts_object_bound_entries(self):
        """Spec format uses structured objects for bound."""
        doc = {
            "lct_id": "lct:web4:ai:test",
            "subject": "did:web4:key:test",
            "binding": {"entity_type": "ai", "public_key": "k", "created_at": "t"},
            "mrh": {"bound": [
                {"lct_id": "lct:web4:hw:1", "type": "parent", "binding_context": "tpm"},
                {"lct_id": "lct:web4:hw:2"},
            ]},
        }
        lct = LCT.from_jsonld(doc)
        assert lct.mrh.bound == ["lct:web4:hw:1", "lct:web4:hw:2"]

    def test_accepts_context_field(self):
        """SDK format uses 'context', spec uses 'birth_context'."""
        doc = {
            "lct_id": "lct:web4:ai:test",
            "subject": "did:web4:key:test",
            "binding": {"entity_type": "ai", "public_key": "k", "created_at": "t"},
            "birth_certificate": {
                "issuing_society": "s1",
                "citizen_role": "r1",
                "birth_timestamp": "t1",
                "context": "network",
            },
        }
        lct = LCT.from_jsonld(doc)
        assert lct.birth_certificate.context == "network"

    def test_accepts_birth_context_field(self):
        """Spec format uses 'birth_context'."""
        doc = {
            "lct_id": "lct:web4:ai:test",
            "subject": "did:web4:key:test",
            "binding": {"entity_type": "ai", "public_key": "k", "created_at": "t"},
            "birth_certificate": {
                "issuing_society": "s1",
                "citizen_role": "r1",
                "birth_timestamp": "t1",
                "birth_context": "ecosystem",
            },
        }
        lct = LCT.from_jsonld(doc)
        assert lct.birth_certificate.context == "ecosystem"

    def test_accepts_string_witnessing_entries(self):
        doc = {
            "lct_id": "lct:web4:ai:test",
            "subject": "did:web4:key:test",
            "binding": {"entity_type": "ai", "public_key": "k", "created_at": "t"},
            "mrh": {"witnessing": ["lct:web4:witness:w1"]},
        }
        lct = LCT.from_jsonld(doc)
        assert lct.mrh.witnessing == ["lct:web4:witness:w1"]

    def test_accepts_object_witnessing_entries(self):
        doc = {
            "lct_id": "lct:web4:ai:test",
            "subject": "did:web4:key:test",
            "binding": {"entity_type": "ai", "public_key": "k", "created_at": "t"},
            "mrh": {"witnessing": [
                {"lct_id": "lct:web4:witness:w1", "role": "audit", "witness_count": 5},
            ]},
        }
        lct = LCT.from_jsonld(doc)
        assert lct.mrh.witnessing == ["lct:web4:witness:w1"]

    def test_ignores_context_header(self):
        """@context is metadata, not data — should be ignored on parse."""
        doc = {
            "@context": ["https://web4.io/contexts/lct.jsonld"],
            "lct_id": "lct:web4:ai:test",
            "subject": "did:web4:key:test",
            "binding": {"entity_type": "ai", "public_key": "k", "created_at": "t"},
        }
        lct = LCT.from_jsonld(doc)
        assert lct.lct_id == "lct:web4:ai:test"


# ── Dataclass Tests ──────────────────────────────────────────────


class TestNewDataclasses:
    """Test the new Attestation and LineageEntry types."""

    def test_attestation_creation(self):
        a = Attestation(
            witness="did:web4:key:w1",
            type="existence",
            claims={"method": "observation"},
            sig="cose:ES256:abc",
            ts="2025-01-01T00:00:00Z",
        )
        assert a.witness == "did:web4:key:w1"
        assert a.type == "existence"
        assert a.claims["method"] == "observation"

    def test_attestation_defaults(self):
        a = Attestation(witness="w", type="t")
        assert a.claims == {}
        assert a.sig == ""
        assert a.ts == ""

    def test_lineage_entry_creation(self):
        le = LineageEntry(
            parent="lct:web4:mb32:prev",
            reason="rotation",
            ts="2025-06-01T00:00:00Z",
        )
        assert le.parent == "lct:web4:mb32:prev"
        assert le.reason == "rotation"

    def test_add_attestation_method(self):
        lct = LCT.create(entity_type=EntityType.AI, public_key="mb64:k")
        att = lct.add_attestation(
            witness="did:web4:key:oracle",
            type="quality",
            claims={"score": 0.95},
        )
        assert len(lct.attestations) == 1
        assert att.witness == "did:web4:key:oracle"
        assert att.ts != ""  # auto-populated

    def test_birth_certificate_genesis_block_hash(self):
        bc = BirthCertificate(
            issuing_society="s",
            citizen_role="r",
            birth_timestamp="t",
            genesis_block_hash="0xdeadbeef",
        )
        assert bc.genesis_block_hash == "0xdeadbeef"

    def test_birth_certificate_genesis_block_hash_default_none(self):
        bc = BirthCertificate(
            issuing_society="s",
            citizen_role="r",
            birth_timestamp="t",
        )
        assert bc.genesis_block_hash is None

    def test_revoke_with_reason(self):
        lct = LCT.create(entity_type=EntityType.AI, public_key="mb64:rk")
        lct.revoke(reason="compromised")
        assert lct.revocation_status == RevocationStatus.REVOKED
        assert lct.revocation_reason == "compromised"
        assert lct.revocation_ts is not None

    def test_revoke_without_reason(self):
        lct = LCT.create(entity_type=EntityType.AI, public_key="mb64:rk")
        lct.revoke()
        assert lct.revocation_status == RevocationStatus.REVOKED
        assert lct.revocation_reason is None


# ── Spec §2.3 Canonical Example ──────────────────────────────────


class TestSpecCanonicalExample:
    """Validate against the spec's §2.3 canonical JSON example."""

    def test_matches_spec_structure(self):
        """Build an LCT that should produce output matching spec §2.3."""
        lct = LCT(
            lct_id="lct:web4:mb32:example",
            subject="did:web4:key:z6MkExample",
            binding=Binding(
                entity_type=EntityType.HUMAN,
                public_key="mb64:coseKey",
                created_at="2025-10-01T00:00:00Z",
                binding_proof="cose:Sig_structure",
                hardware_anchor="eat:mb64:hw:tpm2",
            ),
            birth_certificate=BirthCertificate(
                issuing_society="lct:web4:society:mainnet",
                citizen_role="lct:web4:role:citizen:nation",
                birth_timestamp="2025-10-01T00:00:00Z",
                birth_witnesses=["lct:web4:witness:1", "lct:web4:witness:2", "lct:web4:witness:3"],
                context="nation",
                genesis_block_hash="0xgenesishash",
            ),
            mrh=MRH(
                bound=["lct:web4:hardware:tpm1"],
                paired=[MRHPairing(
                    lct_id="lct:web4:role:citizen:nation",
                    pairing_type="birth_certificate",
                    permanent=True,
                    ts="2025-10-01T00:00:00Z",
                )],
                witnessing=["lct:web4:witness:oracle1"],
                horizon_depth=3,
                last_updated="2025-10-01T00:00:00Z",
            ),
            policy=Policy(
                capabilities=["pairing:initiate", "metering:grant", "write:lct", "witness:attest"],
                constraints={"region": ["us-west", "eu-central"], "max_rate": 5000},
            ),
            t3=T3(talent=0.85, training=0.92, temperament=0.78),
            v3=V3(valuation=0.89, veracity=0.91, validity=0.76),
            attestations=[
                Attestation(
                    witness="did:web4:key:z6MkAttestor",
                    type="existence",
                    claims={"observed_at": "2025-10-01T00:00:00Z", "method": "blockchain_transaction"},
                    sig="cose:ES256:signature",
                    ts="2025-10-01T00:00:00Z",
                ),
            ],
            lineage=[
                LineageEntry(
                    parent="lct:web4:mb32:previous",
                    reason="genesis",
                    ts="2025-09-01T00:00:00Z",
                ),
            ],
        )

        doc = lct.to_jsonld()

        # Structural checks matching spec §2.3
        assert doc["@context"] == [LCT_JSONLD_CONTEXT]
        assert doc["lct_id"] == "lct:web4:mb32:example"
        assert doc["subject"] == "did:web4:key:z6MkExample"

        # Binding
        assert doc["binding"]["hardware_anchor"] == "eat:mb64:hw:tpm2"
        assert doc["binding"]["entity_type"] == "human"

        # Birth certificate with spec field names
        bc = doc["birth_certificate"]
        assert bc["birth_context"] == "nation"
        assert bc["genesis_block_hash"] == "0xgenesishash"
        assert len(bc["birth_witnesses"]) == 3

        # MRH — structured entries
        assert doc["mrh"]["bound"][0] == {"lct_id": "lct:web4:hardware:tpm1"}
        assert doc["mrh"]["witnessing"][0] == {"lct_id": "lct:web4:witness:oracle1"}
        assert doc["mrh"]["paired"][0]["permanent"] is True

        # Policy
        assert "pairing:initiate" in doc["policy"]["capabilities"]
        assert doc["policy"]["constraints"]["max_rate"] == 5000

        # Tensors
        assert doc["t3_tensor"]["talent"] == 0.85
        assert doc["v3_tensor"]["veracity"] == 0.91

        # Attestations
        assert len(doc["attestations"]) == 1
        assert doc["attestations"][0]["type"] == "existence"

        # Lineage
        assert len(doc["lineage"]) == 1
        assert doc["lineage"][0]["reason"] == "genesis"

        # Revocation
        assert doc["revocation"]["status"] == "active"

    def test_valid_json_serialization(self):
        """to_jsonld output must be valid JSON."""
        lct = LCT.create(entity_type=EntityType.AI, public_key="mb64:k")
        s = lct.to_jsonld_string()
        parsed = json.loads(s)
        assert parsed["@context"] == [LCT_JSONLD_CONTEXT]

    def test_to_dict_backward_compat(self):
        """to_dict() should NOT be affected by new fields."""
        lct = LCT.create(entity_type=EntityType.AI, public_key="mb64:k")
        d = lct.to_dict()
        # to_dict should NOT have @context (backward compat)
        assert "@context" not in d
        # to_dict uses 'context' not 'birth_context'
        assert "context" in d["birth_certificate"]
        assert "birth_context" not in d["birth_certificate"]


# ── Context File Consistency (B2) ─────────────────────────────────


import pathlib

CONTEXT_FILE = (
    pathlib.Path(__file__).resolve().parents[3]
    / "schemas" / "contexts" / "lct.jsonld"
)


class TestLCTContextFileConsistency:
    """Verify lct.jsonld context file covers all to_jsonld() output fields."""

    @pytest.fixture(autouse=True)
    def load_context(self):
        assert CONTEXT_FILE.exists(), f"Missing context file: {CONTEXT_FILE}"
        self.context = json.loads(CONTEXT_FILE.read_text())["@context"]

    def test_context_has_version(self):
        assert self.context.get("@version") == 1.1

    def test_context_has_web4_namespace(self):
        assert "web4" in self.context
        assert self.context["web4"] == "https://web4.io/ns/"

    def test_context_has_type_definition(self):
        assert "LinkedContextToken" in self.context

    def test_top_level_fields_covered(self):
        """All top-level to_jsonld() keys (except @context) must be in context."""
        required_keys = [
            "lct_id", "subject", "binding", "mrh", "policy",
            "t3_tensor", "v3_tensor", "revocation",
        ]
        for key in required_keys:
            assert key in self.context, f"Missing context term: {key}"

    def test_optional_top_level_fields_covered(self):
        optional_keys = ["birth_certificate", "attestations", "lineage"]
        for key in optional_keys:
            assert key in self.context, f"Missing context term: {key}"

    def test_binding_subfields_covered(self):
        binding_keys = [
            "entity_type", "public_key", "created_at",
            "binding_proof", "hardware_anchor",
        ]
        for key in binding_keys:
            assert key in self.context, f"Missing binding term: {key}"

    def test_birth_certificate_subfields_covered(self):
        bc_keys = [
            "issuing_society", "citizen_role", "birth_timestamp",
            "birth_witnesses", "birth_context", "genesis_block_hash",
        ]
        for key in bc_keys:
            assert key in self.context, f"Missing birth_certificate term: {key}"

    def test_mrh_subfields_covered(self):
        mrh_keys = [
            "bound", "paired", "witnessing",
            "horizon_depth", "last_updated",
        ]
        for key in mrh_keys:
            assert key in self.context, f"Missing MRH term: {key}"

    def test_pairing_subfields_covered(self):
        pairing_keys = ["pairing_type", "permanent", "ts"]
        for key in pairing_keys:
            assert key in self.context, f"Missing pairing term: {key}"

    def test_tensor_subfields_covered(self):
        tensor_keys = [
            "talent", "training", "temperament",
            "valuation", "veracity", "validity", "composite_score",
        ]
        for key in tensor_keys:
            assert key in self.context, f"Missing tensor term: {key}"

    def test_attestation_subfields_covered(self):
        att_keys = ["witness", "type", "claims", "sig", "ts"]
        for key in att_keys:
            assert key in self.context, f"Missing attestation term: {key}"

    def test_lineage_subfields_covered(self):
        lin_keys = ["parent", "reason"]
        for key in lin_keys:
            assert key in self.context, f"Missing lineage term: {key}"

    def test_revocation_subfields_covered(self):
        rev_keys = ["status"]
        for key in rev_keys:
            assert key in self.context, f"Missing revocation term: {key}"

    def test_full_lct_all_keys_in_context(self):
        """Create a full LCT, to_jsonld(), verify all output keys are in context."""
        lct = LCT.create(
            entity_type=EntityType.HUMAN,
            public_key="mb64:ctxtest",
            society="lct:web4:society:ctx",
            context="platform",
            witnesses=["lct:web4:witness:w1"],
            t3=T3(talent=0.8, training=0.9, temperament=0.7),
            v3=V3(valuation=0.85, veracity=0.9, validity=0.8),
        )
        lct.add_attestation(
            witness="lct:web4:witness:w1", type="identity",
            claims={"verified": True}, sig="sig123", ts="2025-01-01",
        )
        lct.lineage.append(LineageEntry(
            parent="lct:old", reason="upgrade", ts="2025-01-01",
        ))
        doc = lct.to_jsonld()

        # User-data dicts whose keys are NOT schema terms
        data_containers = {"claims", "constraints"}

        def _check_keys(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.startswith("@"):
                        continue
                    if any(path.endswith(c) for c in data_containers):
                        continue
                    assert k in self.context, (
                        f"Key '{k}' (at {path}) not in context file"
                    )
                    _check_keys(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for item in obj:
                    _check_keys(item, path)

        _check_keys(doc)
