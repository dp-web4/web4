"""Cross-language conformance tests for Society & Role operations.

Loads ``web4-standard/testing/conformance/society-roles.json`` and asserts
that the Python ``web4.role`` module produces the documented expected outputs.

The conformance vectors were shipped by the operator (commit 92454d6) and are
declared cross-language: "Any Web4 implementation MUST produce identical results
for these inputs."

Sprint 50 (PR #185) added ``SocietyRole``, ``RoleAssignment``, and
``bootstrap_society_roles``. Sprint 51 (PR #187) added
``validate_minimum_viable``. The role-related vectors are expected to pass
against this surface; lifecycle and authorization vectors that depend on
APIs not present in the Python SDK (combined 5-state phase enum, role-based
assigner permissions) are marked ``xfail`` with reasons citing the specific
audit divergence (P4) or missing surface — silent fixes are forbidden by
the Sprint 52 policy review.

Suite version: 0.1.0
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import pytest

from web4.role import (
    BASE_MANDATORY_ROLES,
    RoleAssignment,
    SocietyRole,
    bootstrap_society_roles,
    validate_minimum_viable,
)

CONFORMANCE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "testing", "conformance")


def _load_suite() -> Dict[str, Any]:
    path = os.path.join(CONFORMANCE_DIR, "society-roles.json")
    with open(path) as f:
        return json.load(f)


SUITE = _load_suite()


def _vec_by_id(category: str, vid: str) -> Dict[str, Any]:
    for v in SUITE[category]:
        if v["id"] == vid:
            return v
    raise KeyError(f"vector {vid!r} not in {category}")


# ── Bootstrap vectors ────────────────────────────────────────────


def test_soc_001_solo_founder_bootstrap() -> None:
    """soc-001: solo founder fills all 7 base-mandatory roles, each role has its own LCT."""
    vector = _vec_by_id("bootstrap_vectors", "soc-001")
    expected = vector["expected"]
    founder = vector["input"]["founder_lct"]

    assignments = bootstrap_society_roles(founder_lct_id=founder)

    assert len(assignments) == expected["role_count"]

    assigned_roles = [a.role.value for a in assignments]
    assert sorted(assigned_roles) == sorted(expected["roles_present"])

    if expected["all_roles_filled_by_founder"]:
        assert all(a.filling_entity_lct_id == founder for a in assignments)

    if expected["each_role_has_own_lct"]:
        role_lcts = {a.role_lct_id for a in assignments}
        # Each role's LCT must be distinct and must NOT equal the founder's LCT
        # (authority binds to role, not entity).
        assert len(role_lcts) == expected["role_count"]
        assert founder not in role_lcts


@pytest.mark.xfail(
    reason=(
        "soc-002 expects 5 combined states (genesis/bootstrap/operational/dormant/sunset). "
        "Python SDK splits this into SocietyPhase (3: genesis/bootstrap/operational) plus "
        "MetabolicState (separate axis). Sprint 49 audit P4 — operator decision pending."
    ),
    strict=True,
)
def test_soc_002_lifecycle_transitions() -> None:
    """soc-002: 5-state lifecycle transitions. xfail per audit P4."""
    from web4.society import SocietyPhase  # noqa: F401 (import only — vector references unsupported states)

    vector = _vec_by_id("bootstrap_vectors", "soc-002")
    # The vector enumerates transitions across 5 states the SDK does not
    # currently unify in a single enum. Touch each transition's "from" value
    # against SocietyPhase membership to force the assertion to fail with a
    # specific surface — strict xfail ensures we notice when the SDK gains a
    # combined enum.
    for transition in vector["transitions"]:
        SocietyPhase(transition["from"])
        SocietyPhase(transition["to"])


# ── Role vectors ─────────────────────────────────────────────────


def test_role_001_seven_base_mandatory() -> None:
    """role-001: BASE_MANDATORY_ROLES contains exactly the 7 named roles."""
    vector = _vec_by_id("role_vectors", "role-001")
    expected = vector["expected"]

    assert len(BASE_MANDATORY_ROLES) == expected["count"]

    role_values = [r.value for r in BASE_MANDATORY_ROLES]
    assert sorted(role_values) == sorted(expected["roles"])

    for role in BASE_MANDATORY_ROLES:
        assert role.is_base_mandatory is True


def test_role_002_rotation_preserves_role_lct() -> None:
    """role-002: rotate() changes filler, role-LCT stays the same."""
    vector = _vec_by_id("role_vectors", "role-002")
    inp = vector["input"]
    expected = vector["expected"]

    assignment = RoleAssignment(
        role=SocietyRole(inp["role"]),
        role_lct_id="lct:web4:role:policy_entity:001",
        filling_entity_lct_id=inp["initial_filler"],
        assigned_by="lct:web4:role:sovereign:001",
    )
    original_role_lct = assignment.role_lct_id

    assignment.rotate(new_entity_lct_id=inp["new_filler"], rotated_by="lct:web4:role:sovereign:001")

    if expected["role_lct_unchanged"]:
        assert assignment.role_lct_id == original_role_lct

    if expected["old_filler_no_longer_authorized"]:
        assert assignment.is_authorized(inp["initial_filler"]) is False

    if expected["new_filler_authorized"]:
        assert assignment.is_authorized(inp["new_filler"]) is True


def test_role_003_multi_holder_committee() -> None:
    """role-003: multiple holders all authorized; multi_holder flag set."""
    vector = _vec_by_id("role_vectors", "role-003")
    inp = vector["input"]
    expected = vector["expected"]

    assignment = RoleAssignment(
        role=SocietyRole(inp["role"]),
        role_lct_id="lct:web4:role:witness:001",
        filling_entity_lct_id=inp["primary"],
        assigned_by="lct:web4:role:sovereign:001",
    )
    for entity in inp["additional"]:
        assert assignment.add_holder(entity) is True

    assert assignment.multi_holder is expected["multi_holder"]
    assert len(assignment.all_holders) == expected["total_holders"]

    if expected["all_authorized"]:
        assert assignment.is_authorized(inp["primary"]) is True
        for entity in inp["additional"]:
            assert assignment.is_authorized(entity) is True


@pytest.mark.xfail(
    reason=(
        "role-004 expects a role-based assigner-permission table "
        "(only sovereign/administrator may assign). The Python SDK's role module "
        "(role.py) does not encode this rule; it lives in `assigned_by` data, not "
        "in a permission check. No specific audit item — surface gap surfaced by "
        "operator's conformance vector."
    ),
    strict=True,
)
def test_role_004_assign_role_authorization() -> None:
    """role-004: role-based assigner permissions. xfail — no SDK surface."""
    vector = _vec_by_id("role_vectors", "role-004")

    # If the SDK gains an `is_allowed_to_assign_roles(SocietyRole)` predicate,
    # this is where it would be exercised. For now, the absence of such a
    # predicate is the xfail.
    from web4.role import is_allowed_to_assign_roles  # noqa: F401 (intentional ImportError)

    for case in vector["cases"]:
        del case  # unreachable until SDK gains the surface


# ── Federation vectors ───────────────────────────────────────────


@pytest.mark.xfail(
    reason=(
        "fed-001 expects imperative join_federation/secede actions on a society. "
        "The Python SDK's federation.Society models hierarchy via the constructor "
        "parameter `parent=Society` and the `children` list — no top-level join/"
        "secede transitions. Different design axis; not a defect, but the conformance "
        "vector assumes the imperative shape used by the Rust SDK."
    ),
    strict=True,
)
def test_fed_001_federation_lifecycle() -> None:
    """fed-001: join/secede lifecycle. xfail — Python uses constructor-hierarchy pattern."""
    vector = _vec_by_id("federation_vectors", "fed-001")

    # If the SDK gains imperative join/secede on SocietyState, this is where the
    # transitions would be exercised against vector["steps"].
    from web4.society import join_federation, secede_from_federation  # noqa: F401

    for step in vector["steps"]:
        del step


# ── Minimum-viable vectors ───────────────────────────────────────


def test_mvs_001_differentiation_fails() -> None:
    """mvs-001: operational society with single filler fails differentiation check."""
    vector = _vec_by_id("minimum_viable_vectors", "mvs-001")
    expected = vector["expected"]

    # Build all 7 base-mandatory roles, all filled by the same entity.
    founder = "lct:web4:human:solo"
    roles = bootstrap_society_roles(founder_lct_id=founder)

    errors = validate_minimum_viable(roles, is_operational=True)

    if not expected["valid"]:
        assert errors  # non-empty
        joined = " ".join(errors).lower()
        assert expected["error_contains"].lower() in joined


def test_mvs_002_missing_base_mandatory_fails() -> None:
    """mvs-002: missing base-mandatory role fails validation."""
    vector = _vec_by_id("minimum_viable_vectors", "mvs-002")
    expected = vector["expected"]
    missing = vector["missing_role"]

    founder = "lct:web4:human:alice"
    roles = bootstrap_society_roles(founder_lct_id=founder)
    # Drop the archivist (or whichever role the vector names).
    roles = [r for r in roles if r.role.value != missing]

    errors = validate_minimum_viable(roles, is_operational=False)

    if not expected["valid"]:
        assert errors  # non-empty
        joined = " ".join(errors).lower()
        assert expected["error_contains"].lower() in joined


# ── Suite-level meta ─────────────────────────────────────────────


def test_suite_metadata() -> None:
    """The suite version and shape are part of the conformance contract."""
    assert SUITE["suite"] == "Society & Role Operations"
    assert SUITE["version"] == "0.1.0"

    assert len(SUITE["bootstrap_vectors"]) == 2
    assert len(SUITE["role_vectors"]) == 4
    assert len(SUITE["federation_vectors"]) == 1
    assert len(SUITE["minimum_viable_vectors"]) == 2


def test_all_vectors_have_ids() -> None:
    """Every vector must have a stable id for cross-language reference."""
    seen: List[str] = []
    for category in (
        "bootstrap_vectors",
        "role_vectors",
        "federation_vectors",
        "minimum_viable_vectors",
    ):
        for v in SUITE[category]:
            assert "id" in v, f"vector missing id in {category}: {v}"
            assert v["id"] not in seen, f"duplicate vector id: {v['id']}"
            seen.append(v["id"])
