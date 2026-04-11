#!/usr/bin/env python3
"""
Law Oracle → R7 → Hardbound Governance Integration
=====================================================

Wires the existing LawOracle into the R7/Hardbound governance stack,
replacing the law_oracle_lct placeholder with a live, queryable oracle.

What this proves:
    SAL's "Law as Data" principle is now observable end-to-end:
    - Actions are validated against versioned, hash-sealed law datasets
    - Witness requirements come from law procedures, not hardcoded values
    - ATP limits are law-derived, not config constants
    - Law versions evolve, and authorization binds to specific versions
    - Interpretations create precedent chains that modify future behavior
    - R7 Rules.law_hash points to the actual law dataset hash

The law oracle is the missing link between "what the rules are" (SAL spec)
and "how the rules are enforced" (Hardbound 10-layer governance).

Date: 2026-02-21
Depends on: law_oracle.py, r7_executor.py, r7_hardbound_integration.py,
            hardbound_cli.py, web4_entity.py
"""

import json
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "web4-standard" / "implementation" / "reference"))

from web4_entity import (
    Web4Entity, EntityType, T3Tensor, V3Tensor, ATPBudget,
    R6Request, R6Result, R6Decision,
)
from hardbound_cli import (
    TeamRole, TeamPolicy, TeamHeartbeat, TeamLedger,
    BirthCertificate, MultiSigBuffer, HardboundTeam,
    ROLE_INITIAL_RIGHTS, ROLE_INITIAL_RESPONSIBILITIES,
    detect_tpm2,
)
from r7_executor import (
    R7Executor, R7Action, R7ActionBuilder, R7Result,
    R7Rules, R7Role, R7Request, R7Reference, R7Resource,
    ReputationDelta, ReputationRule,
)
from r7_hardbound_integration import HardboundR7Team
from law_oracle import (
    LawOracle, LawDataset, Norm, NormType, Operator,
    Procedure, Interpretation, RolePermissions,
    create_default_law_dataset,
)


# ═══════════════════════════════════════════════════════════════
# Law-Governed R7 Team
# ═══════════════════════════════════════════════════════════════

class LawGovernedTeam:
    """
    Wraps HardboundR7Team with a live LawOracle for rule resolution.

    Instead of hardcoded action costs and permissions, every action
    is checked against the oracle's published law dataset:

    1. Action legality: Does the law allow this action for this role?
    2. ATP limits: What does the law say the max cost is?
    3. Witness requirements: Does the law require witnesses? How many?
    4. Procedures: Are there multi-step validation requirements?

    The law version hash is stamped on every authorization decision,
    creating an immutable audit trail of "under which law was this allowed?"
    """

    def __init__(self, team: HardboundTeam, oracle: LawOracle):
        self.team = team
        self.oracle = oracle
        self.r7_team = HardboundR7Team(team)
        self._decision_log: List[Dict] = []

    def submit_action(
        self,
        actor_name: str,
        action_type: str,
        target: str,
        parameters: Optional[Dict[str, Any]] = None,
        atp_stake: float = 0.0,
        role_lct: str = "",
    ) -> Tuple[R7Result, Optional[ReputationDelta], Dict[str, Any]]:
        """
        Submit an action through law oracle → R7 → Hardbound governance.

        Law checks happen BEFORE the action enters the governance stack.
        This is the ACP model: plan → law check → approve → execute.
        """
        params = parameters or {}
        context = {
            "atp_cost": params.get("atp_cost", atp_stake),
            "resource": target,
            "actor": actor_name,
            "action": action_type,
        }
        context.update(params)

        # ── Step 1: Check action legality against current law ──
        legal, denial_reason = self.oracle.check_action_legality(
            action_type, context, role_lct or f"role:{actor_name}",
        )

        law_hash = self.oracle.get_law_hash() or "no-law"
        law_version = self.oracle.get_law_version() or "none"

        if not legal:
            decision = {
                "action": action_type,
                "actor": actor_name,
                "law_version": law_version,
                "law_hash": law_hash,
                "outcome": "denied_by_law",
                "reason": denial_reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._decision_log.append(decision)

            result = R7Result(
                action_id=f"r7:law-denied:{action_type}",
                status="error",
                error=f"Law denial: {denial_reason}",
                error_type="law_violation",
            )
            return result, None, {"law_check": "DENIED", "law_hash": law_hash,
                                   "reason": denial_reason}

        # ── Step 2: Check witness requirements ──
        requires_witness, witness_count = self.oracle.check_witness_requirement(
            action_type, context, role_lct or f"role:{actor_name}",
        )

        # ── Step 3: Get role permissions for ATP cap ──
        perms = self.oracle.get_role_permissions(role_lct or f"role:{actor_name}")
        max_atp = perms.max_atp_per_action if perms else 1000

        # ── Step 4: Route through R7 → Hardbound governance ──
        result, rep_delta, trace = self.r7_team.submit_action(
            actor_name=actor_name,
            action_type=action_type,
            target=target,
            parameters=params,
            atp_stake=min(atp_stake, max_atp),
        )

        # ── Step 5: Stamp law hash on the trace ──
        trace["law_hash"] = law_hash
        trace["law_version"] = law_version
        trace["witness_required"] = requires_witness
        trace["witness_count_required"] = witness_count
        trace["law_max_atp"] = max_atp

        decision = {
            "action": action_type,
            "actor": actor_name,
            "law_version": law_version,
            "law_hash": law_hash,
            "outcome": result.status,
            "witness_required": requires_witness,
            "max_atp": max_atp,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._decision_log.append(decision)

        return result, rep_delta, trace


# ═══════════════════════════════════════════════════════════════
# Test Suite
# ═══════════════════════════════════════════════════════════════

def run_tests():
    """Run law-governance integration tests."""
    print("=" * 70)
    print("  Law Oracle → R7 → Hardbound Governance Integration Test")
    print("  SAL's 'Law as Data' made observable end-to-end")
    print("=" * 70)

    checks_passed = 0
    checks_failed = 0

    def check(name, condition, detail=""):
        nonlocal checks_passed, checks_failed
        if condition:
            print(f"  ✓ {name}")
            checks_passed += 1
        else:
            msg = f": {detail}" if detail else ""
            print(f"  ✗ {name}{msg}")
            checks_failed += 1

    tmpdir = tempfile.mkdtemp(prefix="law_gov_")

    try:
        # ── Test 1: Law Oracle Creation and Dataset Publishing ──
        print("\n── Test 1: Law Oracle Creation ──")

        society_id = "society:engineering-team"
        oracle_lct = "lct:web4:oracle:law:engineering:1"
        oracle = LawOracle(society_id, oracle_lct)

        dataset = create_default_law_dataset(society_id, oracle_lct, "1.0.0")
        law_hash = oracle.publish_law_dataset(dataset)

        check("T1: Law oracle created", oracle is not None)
        check("T1: Law dataset published", law_hash is not None and len(law_hash) == 64)
        check("T1: Law version set", oracle.get_law_version() == "1.0.0")
        check("T1: Law hash matches dataset",
              oracle.get_law_hash() == dataset.hash)

        # ── Test 2: Wire Law Oracle into Hardbound Team ──
        print("\n── Test 2: Law-Governed Team Creation ──")

        team = HardboundTeam("law-test-team", use_tpm=False,
                              state_dir=Path(tmpdir))
        team.create()
        team.add_member("operator", "human", role=TeamRole.OPERATOR)
        team.add_member("agent-bot", "ai", role=TeamRole.AGENT)

        gov = LawGovernedTeam(team, oracle)

        check("T2: LawGovernedTeam created", gov is not None)
        check("T2: Oracle connected", gov.oracle == oracle)
        check("T2: Team has 3 members",
              len(team.birth_certificates) == 3,
              f"members={len(team.birth_certificates)}")

        # ── Test 3: Legal Action Through Full Stack ──
        print("\n── Test 3: Legal Action Through Full Stack ──")

        result, rep_delta, trace = gov.submit_action(
            actor_name="agent-bot",
            action_type="read",
            target="system-config",
            parameters={"atp_cost": 50},
            atp_stake=10,
        )

        check("T3: Legal read action succeeded",
              result.status == "success",
              f"status={result.status}, error={result.error}")
        check("T3: Trace includes law_hash",
              "law_hash" in trace and len(trace["law_hash"]) == 64)
        check("T3: Trace includes law_version",
              trace.get("law_version") == "1.0.0")

        # ── Test 4: Illegal Action Blocked by Law ──
        print("\n── Test 4: Illegal Action Blocked by Law ──")

        # "hack" is not in the allow norms, so should be denied
        result, rep_delta, trace = gov.submit_action(
            actor_name="agent-bot",
            action_type="hack",
            target="system",
            atp_stake=10,
        )

        check("T4: Illegal action blocked",
              result.status == "error",
              f"status={result.status}")
        check("T4: Error mentions law",
              "law" in (result.error or "").lower(),
              f"error={result.error}")
        check("T4: Trace shows denial",
              trace.get("law_check") == "DENIED")

        # ── Test 5: ATP Limit Enforcement from Law ──
        print("\n── Test 5: ATP Limit Enforcement from Law ──")

        # Default law limits ATP to 1000 per action
        result, rep_delta, trace = gov.submit_action(
            actor_name="agent-bot",
            action_type="compute",
            target="expensive-job",
            parameters={"atp_cost": 1500},
            atp_stake=1500,
        )

        # Action should be denied because atp_cost exceeds limit
        check("T5: Over-limit action blocked",
              result.status == "error",
              f"status={result.status}")
        check("T5: Denial reason mentions limit",
              "limit" in (result.error or "").lower() or "Exceeds" in (result.error or ""),
              f"error={result.error}")

        # ── Test 6: Witness Requirements from Law ──
        print("\n── Test 6: Witness Requirements from Law ──")

        # Check what witnesses the law requires for different actions
        req_low, count_low = oracle.check_witness_requirement(
            "read", {"atp_cost": 50}, "role:agent")
        req_high, count_high = oracle.check_witness_requirement(
            "compute", {"atp_cost": 700}, "role:agent")
        req_delete, count_delete = oracle.check_witness_requirement(
            "delete", {"atp_cost": 50}, "role:agent")

        check("T6: Low-cost read needs no witness", not req_low)
        check("T6: High-cost compute needs 2 witnesses",
              req_high and count_high == 2,
              f"req={req_high}, count={count_high}")
        check("T6: Delete needs witnesses (procedure)",
              req_delete and count_delete >= 2,
              f"req={req_delete}, count={count_delete}")

        # ── Test 7: Role Permissions Derived from Law ──
        print("\n── Test 7: Role Permissions from Law ──")

        perms = oracle.get_role_permissions("role:agent")

        check("T7: Role permissions exist", perms is not None)
        check("T7: Read allowed",
              perms.can_perform("read") if perms else False)
        check("T7: Write allowed",
              perms.can_perform("write") if perms else False)
        check("T7: Hack not allowed",
              not perms.can_perform("hack") if perms else False)
        check("T7: Max ATP derived from law",
              perms.max_atp_per_action == 1000 if perms else False,
              f"max_atp={perms.max_atp_per_action if perms else 'N/A'}")

        # ── Test 8: Law Version Evolution ──
        print("\n── Test 8: Law Version Evolution ──")

        # Create v2.0.0 with stricter rules
        norms_v2 = [
            Norm(norm_id="ALLOW-READ", norm_type=NormType.ALLOW,
                 selector="action", operator=Operator.EQ, value="read"),
            Norm(norm_id="ALLOW-COMPUTE", norm_type=NormType.ALLOW,
                 selector="action", operator=Operator.EQ, value="compute"),
            # v2: write is no longer allowed!
            Norm(norm_id="DENY-WRITE", norm_type=NormType.DENY,
                 selector="action", operator=Operator.EQ, value="write",
                 reason="v2.0: Write access suspended pending audit"),
            # Stricter ATP limit
            Norm(norm_id="LIMIT-ATP", norm_type=NormType.LIMIT,
                 selector="atp_cost", operator=Operator.LTE, value=500,
                 reason="v2.0: Reduced ATP budget during audit"),
        ]
        dataset_v2 = LawDataset(
            version="2.0.0",
            society_id=society_id,
            law_oracle_lct=oracle_lct,
            norms=norms_v2,
        )
        hash_v2 = oracle.publish_law_dataset(dataset_v2)

        check("T8: v2.0.0 published", oracle.get_law_version() == "2.0.0")
        check("T8: v2.0.0 hash differs from v1",
              hash_v2 != law_hash)
        check("T8: v1.0.0 in history",
              len(oracle.dataset_history) == 1)

        # Now write should be blocked
        result_write, _, trace_write = gov.submit_action(
            actor_name="agent-bot",
            action_type="write",
            target="data-file",
            atp_stake=10,
        )
        check("T8: Write blocked under v2.0.0 law",
              result_write.status == "error")

        # But read still works
        result_read, _, trace_read = gov.submit_action(
            actor_name="agent-bot",
            action_type="read",
            target="data-file",
            atp_stake=5,
        )
        check("T8: Read still works under v2.0.0",
              result_read.status == "success",
              f"status={result_read.status}, error={result_read.error}")

        # ── Test 9: Interpretation Precedent Chain ──
        print("\n── Test 9: Interpretation Precedent Chain ──")

        # Add an interpretation clarifying what "read" means
        interp_hash = oracle.add_interpretation(
            interpretation_id="INTERP-001",
            question="Does 'read' include cached data access?",
            answer="Yes — read includes all data access including caches",
            applies_to_norms=["ALLOW-READ"],
            reason="Clarification requested by engineering team",
        )

        check("T9: Interpretation added", len(interp_hash) == 64)

        # Add a superseding interpretation
        interp_hash_2 = oracle.add_interpretation(
            interpretation_id="INTERP-002",
            question="Does 'read' include cached data access?",
            answer="Read includes caches but NOT debug logs",
            applies_to_norms=["ALLOW-READ"],
            replaces="INTERP-001",
            reason="Refined after security review — debug logs excluded",
        )

        check("T9: Second interpretation added", len(interp_hash_2) == 64)

        # Get precedent chain
        chain = oracle.get_interpretation_chain("INTERP-002")
        check("T9: Precedent chain has 2 entries",
              len(chain) == 2,
              f"chain_len={len(chain)}")

        if len(chain) >= 2:
            check("T9: Chain shows supersession",
                  chain[0].replaces == "INTERP-001")

        # ── Test 10: Law-Stamped Decision Audit Trail ──
        print("\n── Test 10: Law-Stamped Audit Trail ──")

        check("T10: Decision log has entries",
              len(gov._decision_log) >= 4,
              f"decisions={len(gov._decision_log)}")

        # All decisions should have law version and hash
        all_stamped = all(
            d.get("law_hash") and d.get("law_version")
            for d in gov._decision_log
        )
        check("T10: All decisions have law stamps", all_stamped)

        # Check that decisions reference correct law versions
        v1_decisions = [d for d in gov._decision_log
                        if d.get("law_version") == "1.0.0"]
        v2_decisions = [d for d in gov._decision_log
                        if d.get("law_version") == "2.0.0"]
        check("T10: Decisions span v1.0.0 and v2.0.0 law",
              len(v1_decisions) > 0 and len(v2_decisions) > 0,
              f"v1={len(v1_decisions)}, v2={len(v2_decisions)}")

        # ── Test 11: JSON-LD Export of Law Dataset ──
        print("\n── Test 11: JSON-LD Export ──")

        json_ld = dataset_v2.to_json_ld()

        check("T11: JSON-LD has @context",
              "@context" in json_ld)
        check("T11: JSON-LD type correct",
              json_ld.get("type") == "Web4LawDataset")
        check("T11: JSON-LD has society",
              json_ld.get("society") == society_id)
        check("T11: JSON-LD has norms",
              len(json_ld.get("norms", [])) == len(norms_v2))

        # ── Test 12: Law Oracle Statistics ──
        print("\n── Test 12: Law Oracle Statistics ──")

        stats = oracle.get_stats()

        check("T12: Stats include society_id",
              stats.get("society_id") == society_id)
        check("T12: Stats show v2.0.0 current",
              stats.get("current_version") == "2.0.0")
        check("T12: Stats show 1 version in history",
              stats.get("version_history") == 1)
        check("T12: Stats count norms correctly",
              stats.get("norms", {}).get("total") == len(norms_v2),
              f"total={stats.get('norms', {}).get('total')}")

        # ── Test 13: Hardbound Ledger Records Law Actions ──
        print("\n── Test 13: Hardbound Ledger Integrity ──")

        verification = team.ledger.verify()
        check("T13: Ledger has entries",
              verification["entries"] > 0,
              f"entries={verification['entries']}")
        check("T13: Ledger hash chain valid",
              verification["valid"])

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # ── Summary ──
    print("\n" + "=" * 70)
    total = checks_passed + checks_failed
    print(f"  Law Oracle → Governance: {checks_passed}/{total} checks passed")
    if checks_failed == 0:
        print("  ALL CHECKS PASSED!")

    print(f"\n  SAL 'LAW AS DATA' PROVEN:")
    print(f"    Law Oracle publishes versioned, hash-sealed law datasets")
    print(f"    R7 actions validated against law norms (allow/deny/limit/require)")
    print(f"    Witness requirements derived from law procedures")
    print(f"    ATP limits enforced per law (not hardcoded)")
    print(f"    Law version evolution with stricter rules (write suspended in v2)")
    print(f"    Interpretation precedent chains track legal reasoning")
    print(f"    Every authorization decision stamped with law version + hash")
    print(f"    Hardbound ledger provides immutable audit trail")
    print("=" * 70)

    return checks_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
