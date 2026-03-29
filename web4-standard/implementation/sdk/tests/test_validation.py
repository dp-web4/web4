"""Tests for web4.validation — schema validation module."""

import importlib.resources
import pytest
from pathlib import Path
from web4.validation import (
    ValidationResult,
    ValidationError,
    SchemaValidationUnavailable,
    SchemaNotFound,
    validate,
    list_schemas,
    get_schema,
    get_schema_dir,
    _find_schema_dir_package,
    _find_schema_dir_repo,
    _schema_cache,
)


# ── Schema directory and listing ────────────────────────────────


class TestSchemaDir:
    """Tests for schema directory resolution."""

    def test_get_schema_dir_finds_schemas(self) -> None:
        d = get_schema_dir()
        assert d.is_dir()
        assert (d / "lct-jsonld.schema.json").exists()

    def test_get_schema_dir_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        d = get_schema_dir()
        monkeypatch.setenv("WEB4_SCHEMA_DIR", str(d))
        assert get_schema_dir() == d

    def test_get_schema_dir_bad_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WEB4_SCHEMA_DIR", "/nonexistent/path")
        with pytest.raises(SchemaNotFound, match="does not exist"):
            get_schema_dir()


class TestSchemaResolution:
    """Tests for the two schema resolution strategies."""

    def test_package_resolution_finds_bundled_schemas(self) -> None:
        """importlib.resources resolves web4.schemas package data."""
        result = _find_schema_dir_package()
        assert result is not None
        assert result.is_dir()
        assert (result / "lct-jsonld.schema.json").exists()

    def test_package_resolution_has_all_12_schemas(self) -> None:
        """All 12 schema files are present in the bundled package."""
        result = _find_schema_dir_package()
        assert result is not None
        json_files = sorted(f.name for f in result.iterdir() if f.suffix == ".json")
        assert len(json_files) == 12

    def test_repo_resolution_finds_schemas(self) -> None:
        """Filesystem walk fallback locates schemas in repo tree."""
        result = _find_schema_dir_repo()
        assert result is not None
        assert result.is_dir()
        assert (result / "lct-jsonld.schema.json").exists()

    def test_importlib_resources_accessible(self) -> None:
        """web4.schemas is a valid importlib.resources package."""
        ref = importlib.resources.files("web4.schemas")
        schema_path = Path(str(ref))
        assert schema_path.is_dir()


class TestListSchemas:
    """Tests for list_schemas()."""

    def test_returns_sorted_list(self) -> None:
        schemas = list_schemas()
        assert schemas == sorted(schemas)

    def test_contains_all_jsonld_schemas(self) -> None:
        schemas = list_schemas()
        expected = [
            "acp", "atp", "attestation-envelope", "capability",
            "dictionary", "entity", "lct", "r7-action", "t3v3",
        ]
        for name in expected:
            assert name in schemas, f"Missing schema: {name}"

    def test_contains_non_jsonld_schemas(self) -> None:
        schemas = list_schemas()
        assert "lct-raw" in schemas
        assert "t3v3-raw" in schemas
        assert "trust-query" in schemas

    def test_count(self) -> None:
        assert len(list_schemas()) == 12


class TestGetSchema:
    """Tests for get_schema()."""

    def test_loads_lct_schema(self) -> None:
        schema = get_schema("lct")
        assert "$schema" in schema or "type" in schema
        assert schema.get("title") or schema.get("type")

    def test_unknown_schema_raises(self) -> None:
        with pytest.raises(SchemaNotFound, match="Unknown schema"):
            get_schema("nonexistent")

    def test_caches_schema(self) -> None:
        _schema_cache.clear()
        s1 = get_schema("lct")
        s2 = get_schema("lct")
        assert s1 is s2

    def test_all_schemas_loadable(self) -> None:
        for name in list_schemas():
            schema = get_schema(name)
            assert isinstance(schema, dict)


# ── ValidationResult ────────────────────────────────────────────


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result_is_truthy(self) -> None:
        r = ValidationResult(valid=True, schema_name="lct")
        assert r
        assert r.valid
        assert r.errors == []

    def test_invalid_result_is_falsy(self) -> None:
        r = ValidationResult(valid=False, schema_name="lct", errors=["bad"])
        assert not r
        assert not r.valid
        assert len(r.errors) == 1


# ── Validation against SDK output ───────────────────────────────


class TestValidateLCT:
    """Validate LCT to_jsonld() output against the LCT schema."""

    def test_minimal_lct(self) -> None:
        from web4.lct import LCT, Binding, EntityType

        lct = LCT(
            lct_id="lct:test:minimal",
            subject="did:web4:test",
            binding=Binding(
                entity_type=EntityType.HUMAN,
                public_key="ed25519:testkey",
                created_at="2026-03-20T00:00:00Z",
            ),
        )
        result = validate(lct.to_jsonld(), "lct")
        assert result.valid, f"Errors: {result.errors}"

    def test_full_lct(self) -> None:
        from web4.lct import (
            LCT, BirthCertificate, Binding, MRH, MRHPairing,
            Policy, Attestation, LineageEntry, EntityType, T3, V3,
        )

        lct = LCT(
            lct_id="lct:web4:ai:full",
            subject="did:web4:alice",
            binding=Binding(
                entity_type=EntityType.AI,
                public_key="ed25519:fullkey",
                created_at="2026-03-20T12:00:00Z",
                binding_proof="cose:ES256:proof",
                hardware_anchor="tpm2",
            ),
            birth_certificate=BirthCertificate(
                issuing_society="lct:web4:society:genesis",
                citizen_role="lct:web4:role:citizen:platform",
                birth_timestamp="2026-03-20T12:00:00Z",
                birth_witnesses=["did:web4:bob"],
                genesis_block_hash="0xabc",
            ),
            mrh=MRH(
                bound=["lct:web4:hw:device1"],
                paired=[MRHPairing(
                    lct_id="lct:web4:role:citizen:platform",
                    pairing_type="birth_certificate",
                    permanent=True,
                    ts="2026-03-20T12:00:00Z",
                )],
                witnessing=["did:web4:witness1"],
                horizon_depth=3,
                last_updated="2026-03-20T12:00:00Z",
            ),
            policy=Policy(
                capabilities=["pairing:initiate"],
                constraints={"max_rate": 5000},
            ),
            t3=T3(talent=0.85, training=0.92, temperament=0.78),
            v3=V3(valuation=0.89, veracity=0.91, validity=0.76),
            attestations=[Attestation(
                witness="did:web4:bob",
                type="existence",
                claims={"observed_at": "2026-03-20T12:00:00Z"},
                sig="cose:ES256:sig",
                ts="2026-03-20T12:00:00Z",
            )],
            lineage=[LineageEntry(
                parent="lct:web4:ai:previous",
                reason="rotation",
                ts="2026-03-19T00:00:00Z",
            )],
        )
        result = validate(lct.to_jsonld(), "lct")
        assert result.valid, f"Errors: {result.errors}"

    def test_invalid_missing_required(self) -> None:
        doc = {"@context": ["https://web4.io/contexts/lct.jsonld"], "subject": "x"}
        result = validate(doc, "lct")
        assert not result.valid
        assert len(result.errors) > 0

    def test_invalid_bad_entity_type(self) -> None:
        doc = {
            "@context": ["https://web4.io/contexts/lct.jsonld"],
            "lct_id": "lct:bad",
            "subject": "did:web4:bad",
            "binding": {"entity_type": "not_real", "public_key": "k", "created_at": "t"},
            "mrh": {"bound": [], "paired": [], "witnessing": [], "horizon_depth": 1},
            "policy": {"capabilities": []},
            "t3_tensor": {"talent": 0.5, "training": 0.5, "temperament": 0.5, "composite_score": 0.5},
            "v3_tensor": {"valuation": 0.5, "veracity": 0.5, "validity": 0.5, "composite_score": 0.5},
            "revocation": {"status": "active"},
        }
        result = validate(doc, "lct")
        assert not result.valid


class TestValidateAttestationEnvelope:
    """Validate AttestationEnvelope to_jsonld() output."""

    def test_minimal_envelope(self) -> None:
        from web4.attestation import AttestationEnvelope, Proof

        env = AttestationEnvelope(
            entity_id="lct:test:soft",
            public_key="ed25519:softkey",
            proof=Proof(format="ecdsa_software", signature="sig", challenge="nonce"),
        )
        result = validate(env.to_jsonld(), "attestation-envelope")
        assert result.valid, f"Errors: {result.errors}"

    def test_full_tpm2_envelope(self) -> None:
        from web4.attestation import (
            AttestationEnvelope, AnchorInfo, Proof, PlatformState,
        )
        import time

        env = AttestationEnvelope(
            entity_id="lct:test:tpm",
            public_key="ed25519:tpmkey",
            anchor=AnchorInfo(
                type="tpm2", manufacturer="Intel",
                model="INTC TPM 2.0", firmware_version="1.38",
            ),
            proof=Proof(
                format="tpm2_quote", signature="sig",
                challenge="nonce", pcr_digest="sha256:digest",
                pcr_selection=[0, 7, 14],
            ),
            platform_state=PlatformState(
                available=True, boot_verified=True,
                pcr_values={0: "abc", 7: "def", 14: "ghi"},
            ),
            timestamp=time.time(),
            purpose="session_start",
            issuer="legion.local",
        )
        result = validate(env.to_jsonld(), "attestation-envelope")
        assert result.valid, f"Errors: {result.errors}"

    def test_invalid_missing_entity_id(self) -> None:
        doc = {
            "@context": ["https://web4.io/contexts/attestation-envelope.jsonld"],
            "@type": "AttestationEnvelope",
            "envelope_version": "0.1",
            "public_key": "k",
        }
        result = validate(doc, "attestation-envelope")
        assert not result.valid


class TestValidateT3V3:
    """Validate T3/V3 to_jsonld() output."""

    def test_t3_valid(self) -> None:
        from web4.trust import T3
        t3 = T3(talent=0.8, training=0.9, temperament=0.7)
        result = validate(t3.to_jsonld(), "t3v3")
        assert result.valid, f"Errors: {result.errors}"

    def test_v3_valid(self) -> None:
        from web4.trust import V3
        v3 = V3(valuation=0.85, veracity=0.9, validity=0.75)
        result = validate(v3.to_jsonld(), "t3v3")
        assert result.valid, f"Errors: {result.errors}"


class TestValidateATP:
    """Validate ATP to_jsonld() output."""

    def test_atp_account(self) -> None:
        from web4.atp import ATPAccount
        acct = ATPAccount(available=100.0)
        result = validate(acct.to_jsonld(), "atp")
        assert result.valid, f"Errors: {result.errors}"


class TestValidateACP:
    """Validate ACP to_jsonld() output."""

    def test_agent_plan(self) -> None:
        from web4.acp import AgentPlan, PlanStep, Trigger, TriggerKind

        plan = AgentPlan(
            plan_id="plan:test:001",
            principal="lct:web4:human:alice",
            agent="lct:web4:ai:agent1",
            grant_id="grant:001",
            steps=[PlanStep(step_id="step1", mcp_tool="test.tool", args={"q": "v"})],
            triggers=[Trigger(kind=TriggerKind.MANUAL)],
        )
        result = validate(plan.to_jsonld(), "acp")
        assert result.valid, f"Errors: {result.errors}"


class TestValidateEntity:
    """Validate Entity to_jsonld() output."""

    def test_entity_valid(self) -> None:
        from web4.entity import get_info, entity_registry_to_jsonld
        from web4.lct import EntityType

        info = get_info(EntityType.AI)
        result = validate(info.to_jsonld(), "entity")
        assert result.valid, f"Errors: {result.errors}"

    def test_entity_registry_valid(self) -> None:
        from web4.entity import entity_registry_to_jsonld

        doc = entity_registry_to_jsonld()
        result = validate(doc, "entity")
        assert result.valid, f"Errors: {result.errors}"


class TestValidateCapability:
    """Validate Capability to_jsonld() output."""

    def test_framework_valid(self) -> None:
        from web4.capability import capability_framework_to_jsonld
        doc = capability_framework_to_jsonld()
        result = validate(doc, "capability")
        assert result.valid, f"Errors: {result.errors}"


class TestValidateDictionary:
    """Validate Dictionary to_jsonld() output."""

    def test_dictionary_spec_valid(self) -> None:
        from web4.dictionary import DictionarySpec

        spec = DictionarySpec(source_domain="medical", target_domain="legal")
        result = validate(spec.to_jsonld(), "dictionary")
        assert result.valid, f"Errors: {result.errors}"

    def test_dictionary_entity_valid(self) -> None:
        from web4.dictionary import DictionaryEntity

        entity = DictionaryEntity.create(
            source_domain="medical",
            target_domain="legal",
            public_key="mb64dictkey",
        )
        result = validate(entity.to_jsonld(), "dictionary")
        assert result.valid, f"Errors: {result.errors}"


class TestValidateR7Action:
    """Validate R7Action to_jsonld() output."""

    def test_r7action_valid(self) -> None:
        from web4.r6 import build_action

        action = build_action(
            actor="lct:web4:human:alice",
            role_lct="lct:web4:role:analyst",
            action="analyze",
            target="dataset:test",
            available_atp=50.0,
            permissions=["analyze"],
        )
        result = validate(action.to_jsonld(), "r7-action")
        assert result.valid, f"Errors: {result.errors}"


# ── Error handling ──────────────────────────────────────────────


class TestErrorHandling:
    """Tests for error paths and edge cases."""

    def test_raise_on_error(self) -> None:
        doc = {"bad": "document"}
        with pytest.raises(ValidationError) as exc_info:
            validate(doc, "lct", raise_on_error=True)
        assert exc_info.value.result.schema_name == "lct"
        assert len(exc_info.value.result.errors) > 0

    def test_unknown_schema_name(self) -> None:
        with pytest.raises(SchemaNotFound, match="Unknown schema"):
            validate({}, "nonexistent")

    def test_schema_dir_override(self) -> None:
        d = get_schema_dir()
        from web4.lct import LCT, Binding, EntityType
        lct = LCT(
            lct_id="lct:test:override",
            subject="did:web4:test",
            binding=Binding(
                entity_type=EntityType.HUMAN,
                public_key="ed25519:testkey",
                created_at="2026-03-20T00:00:00Z",
            ),
        )
        result = validate(lct.to_jsonld(), "lct", schema_dir=d)
        assert result.valid
