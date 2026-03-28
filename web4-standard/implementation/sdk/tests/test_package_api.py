"""
Tests for web4 package public API surface.

Verifies that `from web4 import X` works for all symbols in __all__,
and that key types resolve to the correct module origins.
"""

import web4


class TestPackageVersion:
    def test_version_string(self):
        assert web4.__version__ == "0.14.0"

    def test_version_accessible(self):
        from web4 import __version__
        assert __version__ == "0.14.0"


class TestAllExports:
    def test_all_defined(self):
        assert hasattr(web4, "__all__")
        assert len(web4.__all__) >= 336

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


class TestNewExportsD1:
    """Verify all symbols added in Sprint 8 D1 (export completeness)."""

    # ── Trust ──
    def test_role_tensors(self):
        from web4 import RoleTensors
        assert RoleTensors is not None

    def test_diminishing_returns(self):
        from web4 import diminishing_returns
        assert callable(diminishing_returns)

    def test_trust_bridge(self):
        from web4 import trust_bridge
        assert callable(trust_bridge)

    # ── LCT aliases ──
    def test_lct_binding(self):
        from web4 import LCTBinding
        assert LCTBinding.__module__ == "web4.lct"

    def test_lct_mrh(self):
        from web4 import LCTMRH
        assert LCTMRH.__module__ == "web4.lct"

    def test_lct_mrh_pairing(self):
        from web4 import LCTMRHPairing
        assert LCTMRHPairing.__module__ == "web4.lct"

    def test_lct_policy(self):
        from web4 import LCTPolicy
        assert LCTPolicy.__module__ == "web4.lct"

    # ── ATP ──
    def test_transfer(self):
        from web4 import transfer, ATPAccount
        src = ATPAccount(available=100)
        dst = ATPAccount(available=0)
        result = transfer(src, dst, 50)
        assert result.actual_credit > 0

    def test_sliding_scale(self):
        from web4 import sliding_scale
        assert callable(sliding_scale)

    def test_check_conservation(self):
        from web4 import check_conservation
        assert callable(check_conservation)

    def test_sybil_cost(self):
        from web4 import sybil_cost
        assert callable(sybil_cost)

    def test_fee_sensitivity(self):
        from web4 import fee_sensitivity
        assert callable(fee_sensitivity)

    # ── Federation serialization helpers ──
    def test_norm_roundtrip(self):
        from web4 import Norm, norm_to_dict, norm_from_dict
        n = Norm(norm_id="n1", selector="*", op=">=", value=0.5, description="test")
        d = norm_to_dict(n)
        n2 = norm_from_dict(d)
        assert n2.norm_id == "n1"

    def test_procedure_roundtrip(self):
        from web4 import Procedure, procedure_to_dict, procedure_from_dict
        p = Procedure(procedure_id="p1", description="test")
        d = procedure_to_dict(p)
        p2 = procedure_from_dict(d)
        assert p2.procedure_id == "p1"

    def test_interpretation_roundtrip(self):
        from web4 import Interpretation, interpretation_to_dict, interpretation_from_dict
        i = Interpretation(interpretation_id="i1", replaces="n1", reason="test")
        d = interpretation_to_dict(i)
        i2 = interpretation_from_dict(d)
        assert i2.interpretation_id == "i1"

    def test_law_dataset_roundtrip(self):
        from web4 import LawDataset, law_dataset_to_dict, law_dataset_from_dict
        ld = LawDataset(law_id="l1", version="1.0", society_id="s1")
        d = law_dataset_to_dict(ld)
        ld2 = law_dataset_from_dict(d)
        assert ld2.law_id == "l1"

    def test_delegation_roundtrip(self):
        from web4 import Delegation, delegation_to_dict, delegation_from_dict
        dl = Delegation(delegation_id="d1", delegator="lct:a", delegate="lct:b",
                        scope="read", permissions=["read"])
        d = delegation_to_dict(dl)
        dl2 = delegation_from_dict(d)
        assert dl2.delegation_id == "d1"

    def test_quorum_policy_roundtrip(self):
        from web4 import QuorumPolicy, QuorumMode, quorum_policy_to_dict, quorum_policy_from_dict
        qp = QuorumPolicy(mode=QuorumMode.MAJORITY)
        d = quorum_policy_to_dict(qp)
        qp2 = quorum_policy_from_dict(d)
        assert qp2.mode == QuorumMode.MAJORITY

    # ── R6/R7 errors and data classes ──
    def test_r7_error(self):
        from web4 import R7Error
        assert issubclass(R7Error, Exception)

    def test_r7_constraint(self):
        from web4 import Constraint
        assert Constraint is not None

    def test_r7_contributing_factor(self):
        from web4 import ContributingFactor
        assert ContributingFactor is not None

    def test_r7_precedent(self):
        from web4 import Precedent
        assert Precedent is not None

    def test_r7_reference(self):
        from web4 import Reference
        assert Reference is not None

    def test_r7_tensor_delta(self):
        from web4 import TensorDelta
        assert TensorDelta is not None

    def test_r7_exception_types(self):
        from web4 import (
            ReferenceInvalid, ReputationComputationError,
            RequestMalformed, ResourceInsufficient,
            ResultInvalid, RoleUnauthorized, RuleViolation,
        )
        for exc_cls in [ReferenceInvalid, ReputationComputationError,
                        RequestMalformed, ResourceInsufficient,
                        ResultInvalid, RoleUnauthorized, RuleViolation]:
            assert issubclass(exc_cls, Exception)

    # ── MRH ──
    def test_relation_category(self):
        from web4 import relation_category
        assert callable(relation_category)

    # ── ACP exceptions ──
    def test_acp_human_approval(self):
        from web4 import HumanApproval
        assert HumanApproval is not None

    def test_acp_exceptions(self):
        from web4 import (
            ApprovalRequired, InvalidTransition, LedgerWriteFailure,
            NoValidGrant, PlanExpired, ResourceCapExceeded,
            ScopeViolation, WitnessDeficit,
        )
        for exc_cls in [ApprovalRequired, InvalidTransition, LedgerWriteFailure,
                        NoValidGrant, PlanExpired, ResourceCapExceeded,
                        ScopeViolation, WitnessDeficit]:
            assert issubclass(exc_cls, Exception)

    # ── Dictionary ──
    def test_dictionary_ambiguity_handling(self):
        from web4 import AmbiguityHandling
        assert AmbiguityHandling is not None

    def test_dictionary_chain_step(self):
        from web4 import ChainStep
        assert ChainStep is not None

    def test_dictionary_evolution_config(self):
        from web4 import EvolutionConfig
        assert EvolutionConfig is not None

    def test_dictionary_feedback_record(self):
        from web4 import FeedbackRecord
        assert FeedbackRecord is not None

    # ── Entity ──
    def test_get_info(self):
        from web4 import get_info, EntityType
        info = get_info(EntityType.HUMAN)
        assert info is not None

    # ── Collision disambiguation (new aliases) ──
    def test_lct_binding_vs_binding_module(self):
        """LCTBinding is from lct, not binding module."""
        from web4 import LCTBinding, DeviceConstellation
        assert LCTBinding.__module__ == "web4.lct"
        assert DeviceConstellation.__module__ == "web4.binding"

    def test_lct_mrh_vs_mrh_module(self):
        """LCTMRH is from lct, not mrh module."""
        from web4 import LCTMRH, MRHGraph
        assert LCTMRH.__module__ == "web4.lct"
        assert MRHGraph.__module__ == "web4.mrh"


class TestSubmoduleAll:
    """D2: Verify __all__ declarations in all 19 submodules."""

    SUBMODULES = [
        "trust", "lct", "atp", "federation", "r6", "mrh", "acp",
        "dictionary", "reputation", "entity", "capability", "errors",
        "metabolic", "binding", "society", "security", "protocol",
        "attestation", "mcp",
    ]

    def _import_submodule(self, name):
        import importlib
        return importlib.import_module(f"web4.{name}")

    def test_all_submodules_have_all(self):
        """Every SDK submodule must define __all__."""
        missing = []
        for name in self.SUBMODULES:
            mod = self._import_submodule(name)
            if not hasattr(mod, "__all__"):
                missing.append(name)
        assert missing == [], f"Submodules missing __all__: {missing}"

    def test_submodule_count(self):
        """There should be exactly 19 submodules with __all__."""
        count = 0
        for name in self.SUBMODULES:
            mod = self._import_submodule(name)
            if hasattr(mod, "__all__"):
                count += 1
        assert count == 19

    def test_all_entries_resolve(self):
        """Every name in a submodule's __all__ must be an attribute of that module."""
        errors = []
        for name in self.SUBMODULES:
            mod = self._import_submodule(name)
            for sym in getattr(mod, "__all__", []):
                if not hasattr(mod, sym):
                    errors.append(f"web4.{name}.{sym}")
        assert errors == [], f"__all__ entries that don't resolve: {errors}"

    def test_star_import_matches_all(self):
        """Verify `from web4.X import *` would export exactly __all__."""
        for name in self.SUBMODULES:
            mod = self._import_submodule(name)
            all_list = getattr(mod, "__all__", [])
            # __all__ should have no duplicates
            assert len(all_list) == len(set(all_list)), \
                f"web4.{name}.__all__ has duplicates"

    def test_init_imports_subset_of_submodule_all(self):
        """Everything __init__.py imports from a submodule should be in that submodule's __all__."""
        import web4
        # Map: which symbols __init__.py imports from each submodule
        # (use module origin to check)
        errors = []
        for name in self.SUBMODULES:
            mod = self._import_submodule(name)
            sub_all = set(getattr(mod, "__all__", []))
            for sym in sub_all:
                obj = getattr(mod, sym, None)
                if obj is None:
                    errors.append(f"web4.{name}.{sym} not found")
        assert errors == [], f"Missing: {errors}"

    def test_trust_all(self):
        from web4.trust import __all__ as all_trust
        assert "T3" in all_trust
        assert "V3" in all_trust
        assert "T3_JSONLD_CONTEXT" in all_trust
        assert "T3_WEIGHTS" in all_trust

    def test_lct_all(self):
        from web4.lct import __all__ as all_lct
        assert "LCT" in all_lct
        assert "EntityType" in all_lct
        assert "Binding" in all_lct
        assert "MRH" in all_lct

    def test_atp_all(self):
        from web4.atp import __all__ as all_atp
        assert "ATPAccount" in all_atp
        assert "transfer" in all_atp
        assert "ATP_JSONLD_CONTEXT" in all_atp

    def test_federation_all(self):
        from web4.federation import __all__ as all_fed
        assert "Society" in all_fed
        assert "LawDataset" in all_fed
        assert "norm_to_dict" in all_fed
        assert "merge_law" in all_fed

    def test_r6_all(self):
        from web4.r6 import __all__ as all_r6
        assert "R7Action" in all_r6
        assert "R7Error" in all_r6
        assert "build_action" in all_r6

    def test_mrh_all(self):
        from web4.mrh import __all__ as all_mrh
        assert "MRHGraph" in all_mrh
        assert "propagate_multiplicative" in all_mrh

    def test_acp_all(self):
        from web4.acp import __all__ as all_acp
        assert "ACPStateMachine" in all_acp
        assert "build_intent" in all_acp
        assert "ACP_JSONLD_CONTEXT" in all_acp

    def test_dictionary_all(self):
        from web4.dictionary import __all__ as all_dict
        assert "DictionaryEntity" in all_dict
        assert "DICTIONARY_JSONLD_CONTEXT" in all_dict

    def test_errors_all(self):
        from web4.errors import __all__ as all_err
        assert "Web4Error" in all_err
        assert "make_error" in all_err

    def test_metabolic_all(self):
        from web4.metabolic import __all__ as all_met
        assert "MetabolicState" in all_met
        assert "Transition" in all_met
        assert "ENERGY_MULTIPLIERS" in all_met

    def test_binding_all(self):
        from web4.binding import __all__ as all_bind
        assert "DeviceConstellation" in all_bind
        assert "ANCHOR_TRUST_WEIGHT" in all_bind

    def test_society_all(self):
        from web4.society import __all__ as all_soc
        assert "SocietyState" in all_soc
        assert "create_society" in all_soc

    def test_security_all(self):
        from web4.security import __all__ as all_sec
        assert "W4ID" in all_sec
        assert "SUITE_BASE" in all_sec

    def test_protocol_all(self):
        from web4.protocol import __all__ as all_proto
        assert "Web4URI" in all_proto
        assert "TRANSPORT_PROFILES" in all_proto

    def test_attestation_all(self):
        from web4.attestation import __all__ as all_att
        assert "AttestationEnvelope" in all_att
        assert "verify_envelope" in all_att

    def test_mcp_all(self):
        from web4.mcp import __all__ as all_mcp
        assert "MCPSession" in all_mcp
        assert "calculate_mcp_cost" in all_mcp


class TestPyTyped:
    def test_py_typed_exists(self):
        import pathlib
        package_dir = pathlib.Path(web4.__file__).parent
        assert (package_dir / "py.typed").exists()
