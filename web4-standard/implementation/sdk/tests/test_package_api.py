"""
Tests for web4 package public API surface.

Verifies that `from web4 import X` works for all symbols in __all__,
and that key types resolve to the correct module origins.
"""

import web4


class TestPackageVersion:
    def test_version_string(self):
        assert web4.__version__ == "0.10.0"

    def test_version_accessible(self):
        from web4 import __version__
        assert __version__ == "0.10.0"


class TestAllExports:
    def test_all_defined(self):
        assert hasattr(web4, "__all__")
        assert len(web4.__all__) > 200

    def test_all_symbols_resolve(self):
        """Every name in __all__ must be importable from web4."""
        missing = []
        for name in web4.__all__:
            if not hasattr(web4, name):
                missing.append(name)
        assert missing == [], f"Symbols in __all__ but not importable: {missing}"

    def test_no_extra_public_symbols(self):
        """__all__ should include all public re-exported types (not private/internal)."""
        # Spot-check key types are in __all__
        expected = [
            "T3", "V3", "LCT", "ATPAccount", "R7Action",
            "Society", "MRHGraph", "ACPStateMachine",
            "W4ID", "Web4URI", "MCPSession",
        ]
        for name in expected:
            assert name in web4.__all__, f"{name} missing from __all__"


class TestTrustImports:
    def test_t3(self):
        from web4 import T3
        t = T3()
        assert 0.0 <= t.talent <= 1.0

    def test_v3(self):
        from web4 import V3
        v = V3()
        assert 0.0 <= v.veracity <= 1.0

    def test_trust_profile(self):
        from web4 import TrustProfile
        assert TrustProfile is not None

    def test_compute_team_t3(self):
        from web4 import compute_team_t3, TrustProfile, T3
        p1 = TrustProfile("a")
        p1.set_role("analyst", T3(0.8, 0.9, 0.7))
        p2 = TrustProfile("b")
        p2.set_role("analyst", T3(0.6, 0.7, 0.8))
        result = compute_team_t3([p1, p2], role="analyst")
        assert isinstance(result, T3)


class TestLCTImports:
    def test_lct_create(self):
        from web4 import LCT, EntityType
        lct = LCT.create(EntityType.HUMAN, "pubkey123")
        assert lct.lct_id.startswith("lct:")

    def test_entity_type(self):
        from web4 import EntityType
        assert EntityType.HUMAN.value == "human"

    def test_birth_certificate(self):
        from web4 import BirthCertificate
        assert BirthCertificate is not None


class TestATPImports:
    def test_atp_account(self):
        from web4 import ATPAccount
        acct = ATPAccount(available=1000)
        assert acct.available == 1000

    def test_energy_ratio(self):
        from web4 import energy_ratio
        assert callable(energy_ratio)


class TestFederationImports:
    def test_federation_society(self):
        from web4 import FederationSociety
        s = FederationSociety("soc:1", "Test")
        assert s.name == "Test"

    def test_law_dataset(self):
        from web4 import LawDataset
        law = LawDataset(law_id="l1", version="1.0", society_id="s1")
        assert law.hash  # content-addressed hash computed

    def test_citizenship_status(self):
        from web4 import CitizenshipStatus
        assert CitizenshipStatus.ACTIVE.value == "active"

    def test_quorum_policy(self):
        from web4 import QuorumPolicy, QuorumMode
        qp = QuorumPolicy(mode=QuorumMode.MAJORITY)
        assert qp.mode == QuorumMode.MAJORITY


class TestR7Imports:
    def test_r7_action(self):
        from web4 import R7Action, Rules, Role, Request, ResourceRequirements, build_action
        action = build_action(
            actor="lct:alice",
            role_lct="lct:role:analyst",
            action="analyze",
            permissions=["analyze"],
        )
        assert isinstance(action, R7Action)

    def test_action_status(self):
        from web4 import ActionStatus
        assert ActionStatus.SUCCESS.value == "success"


class TestMRHImports:
    def test_mrh_graph(self):
        from web4 import MRHGraph, MRHNode
        g = MRHGraph()
        g.add_node(MRHNode("n1", "test"))
        assert g.get_node("n1") is not None


class TestACPImports:
    def test_acp_state_machine(self):
        from web4 import ACPStateMachine, ACPState
        # Verify the class and state enum are importable and correct
        assert ACPState.IDLE is not None
        assert ACPStateMachine is not None

    def test_proof_of_agency(self):
        from web4 import ProofOfAgency
        assert ProofOfAgency.__module__ == "web4.acp"


class TestDictionaryImports:
    def test_dictionary_type(self):
        from web4 import DictionaryType
        assert DictionaryType.DOMAIN.value == "domain"


class TestReputationImports:
    def test_reputation_engine(self):
        from web4 import ReputationEngine
        engine = ReputationEngine()
        assert engine is not None


class TestEntityImports:
    def test_behavioral_mode(self):
        from web4 import BehavioralMode
        assert BehavioralMode.RESPONSIVE.value == "responsive"

    def test_is_agentic(self):
        from web4 import is_agentic, EntityType
        assert is_agentic(EntityType.AI)


class TestCapabilityImports:
    def test_capability_level(self):
        from web4 import CapabilityLevel
        assert CapabilityLevel.HARDWARE.value in ("hardware", 5)

    def test_assess_level(self):
        from web4 import assess_level
        assert callable(assess_level)


class TestErrorImports:
    def test_error_code(self):
        from web4 import ErrorCode
        assert ErrorCode.BINDING_INVALID.value == "W4_ERR_BINDING_INVALID"

    def test_web4_error(self):
        from web4 import Web4Error, ErrorCode
        err = Web4Error(ErrorCode.BINDING_INVALID)
        assert "BINDING_INVALID" in str(err.code)


class TestMetabolicImports:
    def test_metabolic_state(self):
        from web4 import MetabolicState
        assert MetabolicState.ACTIVE.value == "active"

    def test_metabolic_transition_alias(self):
        from web4 import MetabolicTransition
        assert MetabolicTransition is not None


class TestBindingImports:
    def test_anchor_type(self):
        from web4 import AnchorType
        assert AnchorType.TPM2.value == "tpm2"

    def test_device_constellation(self):
        from web4 import DeviceConstellation
        assert DeviceConstellation is not None


class TestSocietyImports:
    def test_create_society(self):
        from web4 import create_society
        state = create_society(
            "soc:test", "TestSociety",
            founders=["lct:founder1", "lct:founder2"],
            timestamp="2026-01-01T00:00:00Z",
        )
        assert state.society_id == "soc:test"

    def test_society_phase(self):
        from web4 import SocietyPhase
        assert SocietyPhase.OPERATIONAL.value == "operational"


class TestSecurityImports:
    def test_w4id(self):
        from web4 import W4ID, parse_w4id
        w = parse_w4id("did:web4:key:abc123")
        assert isinstance(w, W4ID)

    def test_crypto_suite(self):
        from web4 import SUITE_BASE, CryptoSuiteId
        assert SUITE_BASE.suite_id == CryptoSuiteId.W4_BASE_1


class TestProtocolImports:
    def test_web4_uri(self):
        from web4 import Web4URI
        uri = Web4URI(w4id="did:web4:key:abc123", path="/tools/test")
        assert uri.w4id == "did:web4:key:abc123"

    def test_transport(self):
        from web4 import Transport
        assert Transport.TLS_1_3.value == "tls_1.3"

    def test_handshake_phase(self):
        from web4 import HandshakePhase
        assert HandshakePhase is not None


class TestMCPImports:
    def test_mcp_session(self):
        from web4 import MCPSession
        assert MCPSession is not None

    def test_mcp_resource_requirements_alias(self):
        """MCPResourceRequirements is the mcp version, disambiguated from r6."""
        from web4 import MCPResourceRequirements, ResourceRequirements
        assert MCPResourceRequirements.__module__ == "web4.mcp"
        assert ResourceRequirements.__module__ == "web4.r6"

    def test_mcp_proof_of_agency_alias(self):
        """MCPProofOfAgency is the mcp version, ProofOfAgency is from acp."""
        from web4 import MCPProofOfAgency, ProofOfAgency
        assert MCPProofOfAgency.__module__ == "web4.mcp"
        assert ProofOfAgency.__module__ == "web4.acp"


class TestCollisionDisambiguation:
    """Verify that naming collisions between modules are properly resolved."""

    def test_resource_requirements(self):
        """r6.ResourceRequirements vs mcp.ResourceRequirements."""
        from web4 import ResourceRequirements, MCPResourceRequirements
        assert ResourceRequirements is not MCPResourceRequirements

    def test_proof_of_agency(self):
        """acp.ProofOfAgency vs mcp.ProofOfAgency."""
        from web4 import ProofOfAgency, MCPProofOfAgency
        assert ProofOfAgency is not MCPProofOfAgency

    def test_federation_society_alias(self):
        """federation.Society exported as FederationSociety to avoid collision with society module."""
        from web4 import FederationSociety
        from web4.federation import Society
        assert FederationSociety is Society

    def test_society_direct_import(self):
        """from web4 import Society must work (documented in docstring)."""
        from web4 import Society
        from web4.federation import Society as FedSociety
        assert Society is FedSociety


class TestPyTyped:
    def test_py_typed_exists(self):
        import pathlib
        package_dir = pathlib.Path(web4.__file__).parent
        assert (package_dir / "py.typed").exists()
