"""
Tests for web4.role — society role taxonomy per society-roles.md.

Tests cover:
1. SocietyRole enum — members, values, base-mandatory classification
2. SocietyRole descriptions — all roles have descriptions
3. RoleAssignment — construction, defaults, T3/V3
4. RoleAssignment.rotate() — entity rotation preserves role-LCT
5. RoleAssignment.add_holder() — committee/federation pattern
6. RoleAssignment.remove_holder() — holder removal
7. RoleAssignment.is_authorized() — primary + additional holders
8. RoleAssignment.to_dict() / from_dict() — round-trip serialization
9. bootstrap_society_roles() — solo-founder genesis produces 7 role assignments
10. bootstrap_society_roles() — custom role_lct_factory
11. BASE_MANDATORY_ROLES constant — correct count and membership
"""

from web4.role import (
    BASE_MANDATORY_ROLES,
    RoleAssignment,
    SocietyRole,
    bootstrap_society_roles,
    validate_minimum_viable,
)
from web4.trust import T3, V3

# ── SocietyRole enum ────────────────────────────────────────────


class TestSocietyRole:
    """Tests for the SocietyRole enum."""

    def test_has_seven_base_mandatory(self) -> None:
        """Spec requires exactly 7 base-mandatory roles."""
        base = [r for r in SocietyRole if r.is_base_mandatory]
        assert len(base) == 7

    def test_base_mandatory_members(self) -> None:
        """All 7 spec-defined base-mandatory roles are present."""
        expected = {
            "sovereign",
            "law_oracle",
            "policy_entity",
            "treasurer",
            "administrator",
            "archivist",
            "citizen",
        }
        actual = {r.value for r in SocietyRole if r.is_base_mandatory}
        assert actual == expected

    def test_context_mandatory_not_base(self) -> None:
        """Witness and Auditor are context-mandatory, not base-mandatory."""
        assert not SocietyRole.WITNESS.is_base_mandatory
        assert not SocietyRole.AUDITOR.is_base_mandatory

    def test_total_enum_members(self) -> None:
        """9 total roles: 7 base-mandatory + 2 context-mandatory."""
        assert len(SocietyRole) == 9

    def test_string_values(self) -> None:
        """All roles have snake_case string values for JSON serialization."""
        for role in SocietyRole:
            assert isinstance(role.value, str)
            assert role.value == role.value.lower()

    def test_str_enum_mixin(self) -> None:
        """SocietyRole is a str enum — value is accessible as string."""
        assert SocietyRole.SOVEREIGN.value == "sovereign"
        assert SocietyRole("sovereign") == SocietyRole.SOVEREIGN

    def test_all_roles_have_descriptions(self) -> None:
        """Every role has a non-empty human-readable description."""
        for role in SocietyRole:
            desc = role.description
            assert isinstance(desc, str)
            assert len(desc) > 10

    def test_sovereign_description(self) -> None:
        assert "charter" in SocietyRole.SOVEREIGN.description.lower()

    def test_treasurer_description(self) -> None:
        assert (
            "treasury" in SocietyRole.TREASURER.description.lower()
            or "atp" in SocietyRole.TREASURER.description.lower()
        )


# ── RoleAssignment ──────────────────────────────────────────────


class TestRoleAssignment:
    """Tests for the RoleAssignment dataclass."""

    def test_construction(self) -> None:
        """Basic construction with required fields."""
        ra = RoleAssignment(
            role=SocietyRole.SOVEREIGN,
            role_lct_id="role-lct-001",
            filling_entity_lct_id="entity-001",
            assigned_by="entity-001",
        )
        assert ra.role == SocietyRole.SOVEREIGN
        assert ra.role_lct_id == "role-lct-001"
        assert ra.filling_entity_lct_id == "entity-001"
        assert ra.assigned_by == "entity-001"

    def test_default_trust(self) -> None:
        """Default T3/V3 are neutral (0.5)."""
        ra = RoleAssignment(
            role=SocietyRole.CITIZEN,
            role_lct_id="role-lct-001",
            filling_entity_lct_id="entity-001",
            assigned_by="entity-001",
        )
        assert ra.role_trust.talent == 0.5
        assert ra.role_trust.training == 0.5
        assert ra.role_trust.temperament == 0.5
        assert ra.role_value.valuation == 0.5

    def test_default_not_multi_holder(self) -> None:
        """Default is single-holder."""
        ra = RoleAssignment(
            role=SocietyRole.CITIZEN,
            role_lct_id="role-lct-001",
            filling_entity_lct_id="entity-001",
            assigned_by="entity-001",
        )
        assert not ra.multi_holder
        assert ra.additional_holders == []

    def test_custom_trust(self) -> None:
        """Can set custom T3/V3 at construction."""
        ra = RoleAssignment(
            role=SocietyRole.TREASURER,
            role_lct_id="role-lct-001",
            filling_entity_lct_id="entity-001",
            assigned_by="entity-001",
            role_trust=T3(talent=0.9, training=0.8, temperament=0.7),
            role_value=V3(valuation=0.6, veracity=0.5, validity=0.4),
        )
        assert ra.role_trust.talent == 0.9
        assert ra.role_value.valuation == 0.6


class TestRoleAssignmentRotation:
    """Tests for role rotation — entity changes, role-LCT stays."""

    def test_rotate_changes_filler(self) -> None:
        """Rotation changes the filling entity."""
        ra = RoleAssignment(
            role=SocietyRole.POLICY_ENTITY,
            role_lct_id="role-lct-pe",
            filling_entity_lct_id="entity-a",
            assigned_by="sovereign-001",
        )
        ra.rotate("entity-b", "sovereign-001", "2026-05-14T00:00:00Z")
        assert ra.filling_entity_lct_id == "entity-b"

    def test_rotate_preserves_role_lct(self) -> None:
        """The role-LCT must NOT change during rotation — core invariant."""
        ra = RoleAssignment(
            role=SocietyRole.POLICY_ENTITY,
            role_lct_id="role-lct-pe",
            filling_entity_lct_id="entity-a",
            assigned_by="sovereign-001",
        )
        original_lct = ra.role_lct_id
        ra.rotate("entity-b", "sovereign-001")
        assert ra.role_lct_id == original_lct

    def test_rotate_updates_assigned_by(self) -> None:
        ra = RoleAssignment(
            role=SocietyRole.ADMINISTRATOR,
            role_lct_id="role-lct-admin",
            filling_entity_lct_id="entity-a",
            assigned_by="sovereign-001",
        )
        ra.rotate("entity-b", "admin-002")
        assert ra.assigned_by == "admin-002"

    def test_rotate_updates_timestamp(self) -> None:
        ra = RoleAssignment(
            role=SocietyRole.ARCHIVIST,
            role_lct_id="role-lct-arch",
            filling_entity_lct_id="entity-a",
            assigned_by="sovereign-001",
            assigned_at="2026-01-01T00:00:00Z",
        )
        ra.rotate("entity-b", "sovereign-001", "2026-06-01T00:00:00Z")
        assert ra.assigned_at == "2026-06-01T00:00:00Z"

    def test_rotate_preserves_trust(self) -> None:
        """Role trust metrics persist across rotation — it's the role's history."""
        ra = RoleAssignment(
            role=SocietyRole.TREASURER,
            role_lct_id="role-lct-tres",
            filling_entity_lct_id="entity-a",
            assigned_by="sovereign-001",
            role_trust=T3(talent=0.9, training=0.8, temperament=0.7),
        )
        ra.rotate("entity-b", "sovereign-001")
        assert ra.role_trust.talent == 0.9
        assert ra.role_trust.training == 0.8

    def test_authorization_after_rotation(self) -> None:
        """After rotation, old entity is NOT authorized; new entity IS."""
        ra = RoleAssignment(
            role=SocietyRole.POLICY_ENTITY,
            role_lct_id="role-lct-pe",
            filling_entity_lct_id="entity-a",
            assigned_by="sovereign-001",
        )
        assert ra.is_authorized("entity-a")
        assert not ra.is_authorized("entity-b")

        ra.rotate("entity-b", "sovereign-001")
        assert not ra.is_authorized("entity-a")
        assert ra.is_authorized("entity-b")


class TestRoleAssignmentMultiHolder:
    """Tests for committee/federation pattern — multiple holders per role."""

    def test_add_holder(self) -> None:
        """Adding a holder enables multi_holder flag."""
        ra = RoleAssignment(
            role=SocietyRole.WITNESS,
            role_lct_id="role-lct-wit",
            filling_entity_lct_id="witness-a",
            assigned_by="sovereign-001",
        )
        assert not ra.multi_holder
        result = ra.add_holder("witness-b")
        assert result is True
        assert ra.multi_holder
        assert "witness-b" in ra.additional_holders

    def test_add_holder_duplicate_rejected(self) -> None:
        """Cannot add the same holder twice."""
        ra = RoleAssignment(
            role=SocietyRole.WITNESS,
            role_lct_id="role-lct-wit",
            filling_entity_lct_id="witness-a",
            assigned_by="sovereign-001",
        )
        ra.add_holder("witness-b")
        result = ra.add_holder("witness-b")
        assert result is False
        assert len(ra.additional_holders) == 1

    def test_add_primary_as_additional_rejected(self) -> None:
        """Cannot add the primary filler as an additional holder."""
        ra = RoleAssignment(
            role=SocietyRole.WITNESS,
            role_lct_id="role-lct-wit",
            filling_entity_lct_id="witness-a",
            assigned_by="sovereign-001",
        )
        result = ra.add_holder("witness-a")
        assert result is False

    def test_multiple_holders_all_authorized(self) -> None:
        """All holders (primary + additional) are authorized."""
        ra = RoleAssignment(
            role=SocietyRole.WITNESS,
            role_lct_id="role-lct-wit",
            filling_entity_lct_id="witness-a",
            assigned_by="sovereign-001",
        )
        ra.add_holder("witness-b")
        ra.add_holder("witness-c")
        assert ra.is_authorized("witness-a")
        assert ra.is_authorized("witness-b")
        assert ra.is_authorized("witness-c")
        assert not ra.is_authorized("witness-d")

    def test_remove_holder(self) -> None:
        """Removing a holder updates the list."""
        ra = RoleAssignment(
            role=SocietyRole.WITNESS,
            role_lct_id="role-lct-wit",
            filling_entity_lct_id="witness-a",
            assigned_by="sovereign-001",
        )
        ra.add_holder("witness-b")
        ra.add_holder("witness-c")
        result = ra.remove_holder("witness-b")
        assert result is True
        assert "witness-b" not in ra.additional_holders
        assert ra.is_authorized("witness-c")

    def test_remove_last_additional_clears_multi_holder(self) -> None:
        """Removing the last additional holder clears the multi_holder flag."""
        ra = RoleAssignment(
            role=SocietyRole.WITNESS,
            role_lct_id="role-lct-wit",
            filling_entity_lct_id="witness-a",
            assigned_by="sovereign-001",
        )
        ra.add_holder("witness-b")
        assert ra.multi_holder
        ra.remove_holder("witness-b")
        assert not ra.multi_holder

    def test_remove_nonexistent_holder(self) -> None:
        """Removing a non-holder returns False."""
        ra = RoleAssignment(
            role=SocietyRole.WITNESS,
            role_lct_id="role-lct-wit",
            filling_entity_lct_id="witness-a",
            assigned_by="sovereign-001",
        )
        result = ra.remove_holder("witness-x")
        assert result is False

    def test_all_holders_property(self) -> None:
        """all_holders returns primary + additional in order."""
        ra = RoleAssignment(
            role=SocietyRole.WITNESS,
            role_lct_id="role-lct-wit",
            filling_entity_lct_id="witness-a",
            assigned_by="sovereign-001",
        )
        ra.add_holder("witness-b")
        ra.add_holder("witness-c")
        assert ra.all_holders == ["witness-a", "witness-b", "witness-c"]


class TestRoleAssignmentSerialization:
    """Tests for to_dict() / from_dict() round-trip."""

    def test_round_trip(self) -> None:
        """to_dict → from_dict produces equivalent object."""
        original = RoleAssignment(
            role=SocietyRole.TREASURER,
            role_lct_id="role-lct-tres",
            filling_entity_lct_id="entity-001",
            assigned_by="sovereign-001",
            assigned_at="2026-05-14T06:00:00Z",
            role_trust=T3(talent=0.9, training=0.8, temperament=0.7),
            role_value=V3(valuation=0.6, veracity=0.5, validity=0.4),
            multi_holder=False,
        )
        d = original.to_dict()
        restored = RoleAssignment.from_dict(d)
        assert restored.role == original.role
        assert restored.role_lct_id == original.role_lct_id
        assert restored.filling_entity_lct_id == original.filling_entity_lct_id
        assert restored.assigned_by == original.assigned_by
        assert restored.assigned_at == original.assigned_at
        assert restored.role_trust.talent == original.role_trust.talent
        assert restored.role_trust.training == original.role_trust.training
        assert restored.role_trust.temperament == original.role_trust.temperament
        assert restored.role_value.valuation == original.role_value.valuation
        assert restored.multi_holder == original.multi_holder

    def test_round_trip_with_holders(self) -> None:
        """Round-trip preserves additional_holders."""
        original = RoleAssignment(
            role=SocietyRole.WITNESS,
            role_lct_id="role-lct-wit",
            filling_entity_lct_id="witness-a",
            assigned_by="sovereign-001",
        )
        original.add_holder("witness-b")
        original.add_holder("witness-c")

        d = original.to_dict()
        restored = RoleAssignment.from_dict(d)
        assert restored.multi_holder is True
        assert restored.additional_holders == ["witness-b", "witness-c"]

    def test_to_dict_role_value(self) -> None:
        """to_dict stores role as string value, not enum."""
        ra = RoleAssignment(
            role=SocietyRole.SOVEREIGN,
            role_lct_id="role-lct-001",
            filling_entity_lct_id="entity-001",
            assigned_by="entity-001",
        )
        d = ra.to_dict()
        assert d["role"] == "sovereign"
        assert isinstance(d["role"], str)

    def test_from_dict_minimal(self) -> None:
        """from_dict works with minimal required fields."""
        d = {
            "role": "citizen",
            "role_lct_id": "role-lct-cit",
            "filling_entity_lct_id": "entity-001",
            "assigned_by": "sovereign-001",
        }
        ra = RoleAssignment.from_dict(d)
        assert ra.role == SocietyRole.CITIZEN
        assert ra.role_trust.talent == 0.5  # default
        assert ra.multi_holder is False


# ── bootstrap_society_roles ─────────────────────────────────────


class TestBootstrapSocietyRoles:
    """Tests for solo-founder genesis role creation."""

    def test_produces_seven_assignments(self) -> None:
        """Bootstrap creates exactly 7 role assignments (one per base-mandatory)."""
        assignments = bootstrap_society_roles("founder-001")
        assert len(assignments) == 7

    def test_all_base_mandatory_roles_covered(self) -> None:
        """All 7 base-mandatory roles are represented."""
        assignments = bootstrap_society_roles("founder-001")
        roles = {a.role for a in assignments}
        expected = {
            SocietyRole.SOVEREIGN,
            SocietyRole.LAW_ORACLE,
            SocietyRole.POLICY_ENTITY,
            SocietyRole.TREASURER,
            SocietyRole.ADMINISTRATOR,
            SocietyRole.ARCHIVIST,
            SocietyRole.CITIZEN,
        }
        assert roles == expected

    def test_founder_fills_all_roles(self) -> None:
        """The solo founder is the filling entity for every role."""
        assignments = bootstrap_society_roles("founder-001")
        for a in assignments:
            assert a.filling_entity_lct_id == "founder-001"

    def test_founder_is_assigner(self) -> None:
        """The solo founder assigned all roles (self-bootstrapped)."""
        assignments = bootstrap_society_roles("founder-001")
        for a in assignments:
            assert a.assigned_by == "founder-001"

    def test_each_role_has_unique_lct(self) -> None:
        """Each role gets its own LCT ID — different from each other and from the founder."""
        assignments = bootstrap_society_roles("founder-001")
        lct_ids = [a.role_lct_id for a in assignments]
        assert len(set(lct_ids)) == 7  # all unique
        for lct_id in lct_ids:
            assert lct_id != "founder-001"  # different from founder

    def test_default_lct_ids_are_deterministic(self) -> None:
        """Default LCT IDs encode the role for debuggability."""
        assignments = bootstrap_society_roles("founder-001")
        sovereign = next(a for a in assignments if a.role == SocietyRole.SOVEREIGN)
        assert sovereign.role_lct_id == "founder-001:role:sovereign"

    def test_custom_lct_factory(self) -> None:
        """Custom role_lct_factory is called for each role."""
        counter = {"n": 0}

        def factory() -> str:
            counter["n"] += 1
            return f"custom-lct-{counter['n']}"

        assignments = bootstrap_society_roles("founder-001", role_lct_factory=factory)
        assert assignments[0].role_lct_id == "custom-lct-1"
        assert assignments[6].role_lct_id == "custom-lct-7"
        assert counter["n"] == 7

    def test_timestamp_propagated(self) -> None:
        """Timestamp is set on all assignments."""
        ts = "2026-05-14T06:00:00Z"
        assignments = bootstrap_society_roles("founder-001", timestamp=ts)
        for a in assignments:
            assert a.assigned_at == ts

    def test_default_trust_neutral(self) -> None:
        """Bootstrap roles start with neutral T3/V3 (0.5)."""
        assignments = bootstrap_society_roles("founder-001")
        for a in assignments:
            assert a.role_trust.talent == 0.5
            assert a.role_value.valuation == 0.5


# ── BASE_MANDATORY_ROLES constant ──────────────────────────────


class TestBaseMandatoryRolesConstant:
    """Tests for the BASE_MANDATORY_ROLES module-level constant."""

    def test_count(self) -> None:
        assert len(BASE_MANDATORY_ROLES) == 7

    def test_all_base_mandatory(self) -> None:
        for role in BASE_MANDATORY_ROLES:
            assert role.is_base_mandatory

    def test_context_mandatory_excluded(self) -> None:
        assert SocietyRole.WITNESS not in BASE_MANDATORY_ROLES
        assert SocietyRole.AUDITOR not in BASE_MANDATORY_ROLES


# ── validate_minimum_viable ───────────────────────────────────


def _make_assignment(
    role: SocietyRole, filler: str = "entity-001"
) -> RoleAssignment:
    """Helper to create a minimal RoleAssignment for testing."""
    return RoleAssignment(
        role=role,
        role_lct_id=f"role-lct-{role.value}",
        filling_entity_lct_id=filler,
        assigned_by=filler,
    )


class TestValidateMinimumViable:
    """Tests for validate_minimum_viable() — inter-society-protocol.md §6.2."""

    def test_bootstrap_roles_pass_non_operational(self) -> None:
        """Solo-founder bootstrap passes when not yet operational."""
        roles = bootstrap_society_roles("founder-001")
        errors = validate_minimum_viable(roles, is_operational=False)
        assert errors == []

    def test_empty_roles_fails(self) -> None:
        """Empty role list should report all 7 base-mandatory as missing."""
        errors = validate_minimum_viable([])
        assert len(errors) == 7
        for role in BASE_MANDATORY_ROLES:
            assert any(role.value in e for e in errors)

    def test_missing_one_base_mandatory(self) -> None:
        """Missing a single base-mandatory role is reported."""
        roles = [
            _make_assignment(r)
            for r in BASE_MANDATORY_ROLES
            if r != SocietyRole.TREASURER
        ]
        errors = validate_minimum_viable(roles)
        assert len(errors) == 1
        assert "treasurer" in errors[0]

    def test_missing_multiple_base_mandatory(self) -> None:
        """Multiple missing base-mandatory roles are all reported."""
        roles = [_make_assignment(SocietyRole.SOVEREIGN)]
        errors = validate_minimum_viable(roles)
        assert len(errors) == 6  # 7 - 1

    def test_operational_solo_founder_fails_differentiation(self) -> None:
        """Solo-founder (1 entity filling all roles) fails operational checks."""
        roles = bootstrap_society_roles("founder-001")
        errors = validate_minimum_viable(roles, is_operational=True)
        # Should fail on: differentiation (1 filler < 2) and witnessing (no Witness/Auditor)
        assert len(errors) == 2
        assert any("2 distinct" in e for e in errors)
        assert any("witnessing" in e.lower() or "Witness" in e for e in errors)

    def test_operational_with_differentiation_and_witness(self) -> None:
        """Differentiated society with witnessing passes all checks."""
        roles = [_make_assignment(r, "entity-001") for r in BASE_MANDATORY_ROLES]
        # Add Witness filled by a different entity
        roles.append(_make_assignment(SocietyRole.WITNESS, "entity-002"))
        errors = validate_minimum_viable(roles, is_operational=True)
        assert errors == []

    def test_operational_auditor_satisfies_witnessing(self) -> None:
        """Auditor role satisfies witnessing requirement (not just Witness)."""
        roles = [_make_assignment(r, "entity-001") for r in BASE_MANDATORY_ROLES]
        roles.append(_make_assignment(SocietyRole.AUDITOR, "entity-002"))
        errors = validate_minimum_viable(roles, is_operational=True)
        assert errors == []

    def test_operational_differentiation_only(self) -> None:
        """Differentiated but no witness/auditor fails witnessing check only."""
        # Two different entities fill base-mandatory roles
        roles = []
        for i, r in enumerate(BASE_MANDATORY_ROLES):
            filler = "entity-001" if i < 4 else "entity-002"
            roles.append(_make_assignment(r, filler))
        errors = validate_minimum_viable(roles, is_operational=True)
        assert len(errors) == 1
        assert "witnessing" in errors[0].lower() or "Witness" in errors[0]

    def test_operational_witness_but_no_differentiation(self) -> None:
        """Witness exists but all roles filled by same entity — fails differentiation."""
        roles = [_make_assignment(r, "entity-001") for r in BASE_MANDATORY_ROLES]
        # Witness also filled by the same entity
        roles.append(_make_assignment(SocietyRole.WITNESS, "entity-001"))
        errors = validate_minimum_viable(roles, is_operational=True)
        assert len(errors) == 1
        assert "2 distinct" in errors[0]

    def test_non_operational_skips_differentiation_and_witness(self) -> None:
        """Non-operational: differentiation and witnessing are not checked."""
        roles = bootstrap_society_roles("founder-001")
        # All 7 base-mandatory filled by one entity, no witness
        errors = validate_minimum_viable(roles, is_operational=False)
        assert errors == []

    def test_both_witness_and_auditor(self) -> None:
        """Having both Witness and Auditor is fine — more than sufficient."""
        roles = [_make_assignment(r, "entity-001") for r in BASE_MANDATORY_ROLES]
        roles.append(_make_assignment(SocietyRole.WITNESS, "entity-002"))
        roles.append(_make_assignment(SocietyRole.AUDITOR, "entity-003"))
        errors = validate_minimum_viable(roles, is_operational=True)
        assert errors == []

    def test_duplicate_roles_still_count(self) -> None:
        """Multiple assignments for the same role don't cause issues."""
        roles = [_make_assignment(r, "entity-001") for r in BASE_MANDATORY_ROLES]
        # Duplicate Citizen assignment (e.g., second citizen)
        roles.append(_make_assignment(SocietyRole.CITIZEN, "entity-002"))
        roles.append(_make_assignment(SocietyRole.WITNESS, "entity-002"))
        errors = validate_minimum_viable(roles, is_operational=True)
        assert errors == []
