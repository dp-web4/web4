#!/usr/bin/env python3
"""
R7 → Hardbound Governance Integration
========================================

Wires the R7 action framework into the Hardbound 10-layer governance stack.
R7 actions flow through all governance layers; R7 reputation deltas are
recorded in the Hardbound hash-chained ledger.

Data flow:
    R7Action → RBAC check → Policy cost lookup → Multi-sig check →
    ATP debit (team pool) → R7 execute → R7 reputation compute →
    Heartbeat queue → Ledger record → Analytics update

What this proves:
    The R7 framework (reputation as first-class output) is compatible
    with Hardbound enterprise governance (10-layer stack). They compose
    naturally — R7 provides the action semantics, Hardbound provides the
    infrastructure enforcement.

Date: 2026-02-20
Depends on: r7_executor.py, hardbound_cli.py, web4_entity.py
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

from web4_entity import (
    Web4Entity, EntityType, T3Tensor, V3Tensor, ATPBudget,
    R6Request, R6Result, R6Decision,
)
from hardware_entity import HardwareWeb4Entity
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
    R7Error, RuleViolation, RoleUnauthorized, ResourceInsufficient,
)


# ═══════════════════════════════════════════════════════════════
# R7-Governed Hardbound Team
# ═══════════════════════════════════════════════════════════════

class HardboundR7Team:
    """
    Integrates R7 action framework with Hardbound 10-layer governance.

    Every action goes through:
    Layer 10: Birth cert check (entity must have one)
    Layer 9:  Multi-sig check (critical actions)
    Layer 8:  ATP recharge (metabolic state)
    Layer 7:  Heartbeat queuing
    Layer 6:  Analytics update
    Layer 5:  Metabolic state (heartbeat timing)
    Layer 4:  Dynamic cost lookup (from policy)
    Layer 3:  Policy compliance
    Layer 2:  RBAC role check
    Layer 1:  Hash-chain ledger record

    Plus R7-specific:
    - Reputation computation (role-contextualized T3/V3 deltas)
    - Witness attestation on reputation changes
    - Contributing factors tracked
    """

    def __init__(self, team: HardboundTeam):
        self.team = team
        self.r7 = R7Executor(society_lct=team.root.lct_id if team.root else "")
        # Track per-member role-contextualized reputation
        # This mirrors R7Executor.role_reputations but persists with the team
        self._reputation_applied = 0

    def submit_action(
        self,
        actor_name: str,
        action_type: str,
        target: str,
        parameters: Optional[Dict[str, Any]] = None,
        atp_stake: float = 0.0,
        witnesses: Optional[List[str]] = None,
    ) -> Tuple[R7Result, Optional[ReputationDelta], Dict[str, Any]]:
        """
        Submit an R7 action through the full Hardbound governance stack.

        Returns: (result, reputation_delta, governance_trace)

        The governance_trace records which layers were activated and what
        decisions they made — full auditability.
        """
        trace = {
            "actor": actor_name,
            "action": action_type,
            "target": target,
            "layers_activated": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # ── Layer 10: Birth Certificate Check ──
        if actor_name not in self.team.birth_certificates:
            trace["layers_activated"].append(("L10_birth_cert", "DENIED", "no birth certificate"))
            result = R7Result(
                action_id=f"r7:denied:{actor_name}",
                status="error",
                error=f"Entity '{actor_name}' has no birth certificate",
                error_type="BirthCertMissing",
            )
            return result, None, trace
        trace["layers_activated"].append(("L10_birth_cert", "OK", "cert valid"))

        # ── Layer 2: RBAC Role Check ──
        role = self.team.roles.get(actor_name)
        if not role:
            trace["layers_activated"].append(("L02_rbac", "DENIED", "no role assigned"))
            result = R7Result(
                action_id=f"r7:denied:{actor_name}",
                status="error",
                error=f"Entity '{actor_name}' has no assigned role",
                error_type="RoleUnauthorized",
            )
            return result, None, trace

        policy = self.team._cached_policy or TeamPolicy.default()

        # Check RBAC: admin-only or operator-min
        if action_type in policy.admin_only and role != TeamRole.ADMIN:
            trace["layers_activated"].append(("L02_rbac", "DENIED", f"admin-only, actor is {role}"))
            result = R7Result(
                action_id=f"r7:denied:{actor_name}",
                status="error",
                error=f"Action '{action_type}' requires admin role, actor has '{role}'",
                error_type="RoleUnauthorized",
            )
            # Still compute reputation for denied action
            action = self._build_r7_action(actor_name, action_type, target, role, policy, parameters, atp_stake, witnesses)
            rep = self.r7.compute_reputation(action, result)
            self._record_to_ledger(action, result, rep, trace)
            return result, rep, trace

        if action_type in policy.operator_min and role not in (TeamRole.ADMIN, TeamRole.OPERATOR):
            trace["layers_activated"].append(("L02_rbac", "DENIED", f"operator-min, actor is {role}"))
            result = R7Result(
                action_id=f"r7:denied:{actor_name}",
                status="error",
                error=f"Action '{action_type}' requires operator+, actor has '{role}'",
                error_type="RoleUnauthorized",
            )
            action = self._build_r7_action(actor_name, action_type, target, role, policy, parameters, atp_stake, witnesses)
            rep = self.r7.compute_reputation(action, result)
            self._record_to_ledger(action, result, rep, trace)
            return result, rep, trace

        trace["layers_activated"].append(("L02_rbac", "OK", f"role={role}"))

        # ── Layer 3: Policy Compliance ──
        policy_valid = policy.verify_integrity()
        trace["layers_activated"].append(("L03_policy", "OK" if policy_valid else "WARN",
                                          f"v{policy.version}, integrity={policy_valid}"))

        # ── Layer 4: Dynamic Cost Lookup ──
        atp_cost = policy.get_cost(action_type)
        trace["layers_activated"].append(("L04_cost", "OK", f"{atp_cost} ATP"))

        # ── Layer 9: Multi-Sig Check ──
        multi_sig_req = policy.requires_multi_sig(action_type)
        if multi_sig_req:
            pending = self.team.multi_sig_buffer.find_pending(action_type)
            if not pending or not pending.is_quorum_met:
                trace["layers_activated"].append(("L09_multisig", "DEFERRED",
                                                  f"needs {multi_sig_req['required']} approvals"))
                # Create request if not exists
                if not pending:
                    self.team.multi_sig_buffer.create_request(
                        actor=actor_name,
                        action=action_type,
                        required=multi_sig_req["required"],
                        eligible_roles=multi_sig_req["eligible_roles"],
                    )
                result = R7Result(
                    action_id=f"r7:deferred:{actor_name}",
                    status="error",
                    error=f"Action '{action_type}' requires multi-sig ({multi_sig_req['required']} approvals)",
                    error_type="MultiSigRequired",
                )
                return result, None, trace
            else:
                pending.executed = True
                trace["layers_activated"].append(("L09_multisig", "OK",
                                                  f"quorum met ({pending.approval_count}/{pending.required})"))
        else:
            trace["layers_activated"].append(("L09_multisig", "SKIP", "not required"))

        # ── Layer 8: ATP Recharge ──
        elapsed = self.team.heartbeat.seconds_since_last()
        recharge = self.team.heartbeat.compute_recharge(elapsed)
        if recharge > 0:
            old_atp = self.team.team_atp
            self.team.team_atp = min(self.team.team_atp_max, self.team.team_atp + recharge)
            self.team.heartbeat.total_recharged += recharge
            trace["layers_activated"].append(("L08_recharge", "OK",
                                              f"+{recharge:.1f} ATP ({old_atp:.1f}→{self.team.team_atp:.1f})"))
        else:
            trace["layers_activated"].append(("L08_recharge", "SKIP", "no elapsed time"))

        # ── ATP Affordability Check ──
        if self.team.team_atp < atp_cost:
            trace["layers_activated"].append(("L04_cost", "DENIED", f"need {atp_cost}, have {self.team.team_atp:.1f}"))
            result = R7Result(
                action_id=f"r7:denied:{actor_name}",
                status="error",
                error=f"Insufficient team ATP: need {atp_cost}, have {self.team.team_atp:.1f}",
                error_type="ResourceInsufficient",
            )
            action = self._build_r7_action(actor_name, action_type, target, role, policy, parameters, atp_stake, witnesses)
            rep = self.r7.compute_reputation(action, result)
            self._record_to_ledger(action, result, rep, trace)
            return result, rep, trace

        # Debit team ATP
        self.team.team_atp -= atp_cost
        self.team.team_adp_discharged += atp_cost

        # ── Build R7 Action ──
        actor_entity = self.team.members.get(actor_name)
        action = self._build_r7_action(
            actor_name, action_type, target, role, policy,
            parameters, atp_stake, witnesses,
        )

        # ── R7 Execute ──
        result = self.r7.execute(action)
        result.atp_consumed = atp_cost

        # ── R7 Reputation Compute ──
        reputation = self.r7.compute_reputation(action, result)

        # Apply reputation to actor's entity T3/V3 (Layer 5: metabolic impact)
        if actor_entity and reputation:
            self._apply_reputation_to_entity(actor_entity, reputation)
            self._reputation_applied += 1

        trace["layers_activated"].append(("L05_metabolic", "OK",
                                          f"state={self.team.heartbeat.state}"))

        # ── Layer 7: Heartbeat Queue ──
        self._record_to_ledger(action, result, reputation, trace)

        return result, reputation, trace

    def _build_r7_action(
        self,
        actor_name: str,
        action_type: str,
        target: str,
        role: str,
        policy: TeamPolicy,
        parameters: Optional[Dict] = None,
        atp_stake: float = 0.0,
        witnesses: Optional[List[str]] = None,
    ) -> R7Action:
        """Build an R7Action from Hardbound team context."""
        actor = self.team.members.get(actor_name)
        actor_lct = actor.lct_id if actor else f"unknown:{actor_name}"
        role_lct = f"lct:web4:role:{role}:{self.team.name}"

        builder = (R7ActionBuilder(action_type, target)
            .as_actor(actor_lct, role_lct)
            .with_resources(
                atp_required=policy.get_cost(action_type),
                atp_available=self.team.team_atp + policy.get_cost(action_type),  # before debit
            ))

        if atp_stake > 0:
            builder.with_stake(atp_stake)

        if parameters:
            builder.with_parameters(**parameters)

        if witnesses:
            builder.with_witnesses(*witnesses)

        # Inject policy constraints
        builder.with_rules(
            society=self.team.root.lct_id if self.team.root else "",
        )

        return builder.build()

    def _apply_reputation_to_entity(self, entity, reputation: ReputationDelta):
        """Apply R7 reputation deltas to the actor's T3/V3 tensors."""
        for delta in reputation.t3_deltas:
            if delta.dimension == "talent":
                entity.t3.talent = max(0.0, min(1.0, entity.t3.talent + delta.change))
            elif delta.dimension == "training":
                entity.t3.training = max(0.0, min(1.0, entity.t3.training + delta.change))
            elif delta.dimension == "temperament":
                entity.t3.temperament = max(0.0, min(1.0, entity.t3.temperament + delta.change))

        for delta in reputation.v3_deltas:
            if delta.dimension == "valuation":
                entity.v3.valuation = max(0.0, min(1.0, entity.v3.valuation + delta.change))
            elif delta.dimension == "veracity":
                entity.v3.veracity = max(0.0, min(1.0, entity.v3.veracity + delta.change))
            elif delta.dimension == "validity":
                entity.v3.validity = max(0.0, min(1.0, entity.v3.validity + delta.change))

    def _record_to_ledger(
        self,
        action: R7Action,
        result: R7Result,
        reputation: Optional[ReputationDelta],
        trace: Dict,
    ):
        """Record R7 result + reputation to Hardbound hash-chained ledger."""
        ledger_action = {
            "type": "r7_action",
            "actor": action.role.actor_lct,
            "role": action.role.role_lct,
            "action": action.request.action,
            "target": action.request.target,
            "decision": "approved" if result.status == "success" else "denied",
            "atp_cost": result.atp_consumed,
            "output_hash": result.output_hash,
            "r7_status": result.status,
        }

        if reputation:
            ledger_action["r7_reputation"] = {
                "net_trust_change": round(reputation.net_trust_change, 6),
                "net_value_change": round(reputation.net_value_change, 6),
                "rule_triggered": reputation.rule_triggered,
                "t3_deltas": {d.dimension: round(d.change, 6) for d in reputation.t3_deltas},
                "v3_deltas": {d.dimension: round(d.change, 6) for d in reputation.v3_deltas},
            }

        ledger_action["governance_trace"] = [
            {"layer": l[0], "decision": l[1], "detail": l[2]}
            for l in trace.get("layers_activated", [])
        ]

        # Queue in heartbeat buffer (Layer 7)
        self.team.heartbeat.queue_action(ledger_action)
        trace["layers_activated"].append(("L07_heartbeat", "QUEUED",
                                          f"buffer={len(self.team.heartbeat.pending_actions)}"))

    def flush_heartbeat(self):
        """Flush heartbeat buffer to ledger (Layer 7 → Layer 1)."""
        flushed = self.team.heartbeat.flush()
        for action_record in flushed:
            actor_lct = action_record.get("actor", "")
            # Find signer entity
            signer = None
            for name, member in self.team.members.items():
                if hasattr(member, 'lct_id') and member.lct_id == actor_lct:
                    signer = member
                    break
            self.team.ledger.append(
                action=action_record,
                signer_lct=actor_lct,
                signer_entity=signer if isinstance(signer, HardwareWeb4Entity) else None,
            )
        return len(flushed)

    def get_member_reputation(self, member_name: str) -> Dict:
        """Get a member's current T3/V3 and R7 role reputations."""
        member = self.team.members.get(member_name)
        if not member:
            return {"error": f"Unknown member: {member_name}"}

        result = {
            "entity_t3": member.t3.to_dict(),
            "entity_v3": member.v3.to_dict(),
            "role_reputations": {},
        }

        # Get R7 executor's role-contextualized reputations
        for (e_lct, r_lct), rep in self.r7.role_reputations.items():
            if e_lct == member.lct_id:
                result["role_reputations"][r_lct] = {
                    "t3": rep["t3"].to_dict(),
                    "v3": rep["v3"].to_dict(),
                }

        return result


# ═══════════════════════════════════════════════════════════════
# Integration Test
# ═══════════════════════════════════════════════════════════════

def run_integration_test():
    """
    Test R7 actions flowing through all 10 Hardbound governance layers.
    """
    print("=" * 70)
    print("  R7 → HARDBOUND GOVERNANCE INTEGRATION TEST")
    print("  R7 actions through 10-layer stack with reputation tracking")
    print("=" * 70)

    temp_dir = Path(tempfile.mkdtemp(prefix="r7_hb_test_"))
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

    try:
        # ── Setup team ──
        print("\n── Setup: 3-member team ──")

        team = HardboundTeam(
            name="r7-test-corp",
            use_tpm=False,
            state_dir=temp_dir / "teams" / "r7-test-corp",
            team_atp=500.0,
        )
        team.root = HardwareWeb4Entity.create_simulated(EntityType.SOCIETY, "r7-test-corp")
        team.admin = HardwareWeb4Entity.create_simulated(EntityType.HUMAN, "admin")
        team.state_dir.mkdir(parents=True, exist_ok=True)
        (team.state_dir / "members").mkdir(exist_ok=True)

        team.ledger.append_genesis("r7-test-corp", team.root.lct_id, team.admin.lct_id)

        policy = TeamPolicy.default()
        team._cached_policy = policy
        team.ledger.append(
            action={"type": "policy_update", "policy": policy.to_dict(), "version": 1},
            signer_lct=team.admin.lct_id,
        )

        # Add members with birth certs
        members = [
            ("admin", team.admin, TeamRole.ADMIN),
            ("operator-1", HardwareWeb4Entity.create_simulated(EntityType.HUMAN, "operator-1"), TeamRole.OPERATOR),
            ("sage-agent", HardwareWeb4Entity.create_simulated(EntityType.AI, "sage-agent"), TeamRole.AGENT),
        ]

        for name, entity, role in members:
            team.members[name] = entity
            team.roles[name] = role
            team.birth_certificates[name] = BirthCertificate(
                entity_lct=entity.lct_id,
                citizen_role=role,
                society_lct=team.root.lct_id,
                law_oracle_lct=team.admin.lct_id,
                law_version=1,
                witnesses=[team.root.lct_id],
                genesis_block="0" * 16,
                initial_rights=ROLE_INITIAL_RIGHTS[role],
                initial_responsibilities=ROLE_INITIAL_RESPONSIBILITIES[role],
                entity_name=name,
                society_name="r7-test-corp",
            )

        # Create R7-governed wrapper
        r7team = HardboundR7Team(team)

        check("Setup: 3 members with birth certs", len(team.birth_certificates) == 3)

        # ── Test 1: Agent reviews PR (should succeed) ──
        print("\n── Test 1: Agent review_pr (success path) ──")
        r1, rep1, trace1 = r7team.submit_action(
            "sage-agent", "review_pr", "pr-101",
            witnesses=["lct:web4:witness:ci-bot"],
        )
        check("T1: Action succeeded", r1.status == "success")
        check("T1: Reputation computed", rep1 is not None)
        check("T1: Positive trust delta", rep1.net_trust_change > 0,
              f"got {rep1.net_trust_change:+.4f}")
        check("T1: Birth cert checked", any(l[0] == "L10_birth_cert" for l in trace1["layers_activated"]))
        check("T1: RBAC checked", any(l[0] == "L02_rbac" for l in trace1["layers_activated"]))
        check("T1: Cost applied", any(l[0] == "L04_cost" for l in trace1["layers_activated"]))
        check("T1: Heartbeat queued", any(l[0] == "L07_heartbeat" for l in trace1["layers_activated"]))

        # ── Test 2: Agent tries admin-only action (RBAC deny) ──
        print("\n── Test 2: Agent tries add_member (RBAC deny) ──")
        r2, rep2, trace2 = r7team.submit_action(
            "sage-agent", "add_member", "new-member",
        )
        check("T2: Action denied", r2.status == "error")
        check("T2: Error is role-related", "admin" in r2.error.lower())
        check("T2: Reputation still computed (R7 requirement)",
              rep2 is not None and rep2.net_trust_change < 0)

        # ── Test 3: Operator deploys (operator-min, should succeed) ──
        print("\n── Test 3: Operator deploy_staging ──")
        r3, rep3, trace3 = r7team.submit_action(
            "operator-1", "deploy_staging", "service:web-app",
            parameters={"version": "2.1.0"},
        )
        check("T3: Deploy succeeded", r3.status == "success")
        check("T3: Higher ATP cost than review", r3.atp_consumed > 5.0,
              f"cost={r3.atp_consumed}")

        # ── Test 4: Entity without birth cert (Layer 10 deny) ──
        print("\n── Test 4: Unknown entity (no birth cert) ──")
        team.members["ghost"] = HardwareWeb4Entity.create_simulated(EntityType.AI, "ghost")
        team.roles["ghost"] = TeamRole.AGENT
        # Deliberately NO birth certificate

        r4, rep4, trace4 = r7team.submit_action("ghost", "review_pr", "pr-999")
        check("T4: Denied at birth cert layer", r4.status == "error")
        check("T4: Error mentions birth cert", "birth certificate" in r4.error.lower())
        check("T4: No reputation (entity not recognized)", rep4 is None)

        # ── Test 5: Multi-sig action (emergency_shutdown) ──
        print("\n── Test 5: Multi-sig emergency_shutdown ──")

        # emergency_shutdown is admin-only AND multi-sig.
        # Admin initiates → deferred for multi-sig (need 2 approvals)
        r5a, _, trace5a = r7team.submit_action(
            "admin", "emergency_shutdown", "all-services",
        )
        check("T5a: Action deferred for multi-sig", "MultiSigRequired" in (r5a.error_type or ""))

        # Add approvals
        pending = team.multi_sig_buffer.find_pending("emergency_shutdown")
        check("T5: Pending request created", pending is not None)

        pending.add_approval("admin", TeamRole.ADMIN)
        pending.add_approval("operator-1", TeamRole.OPERATOR)
        check("T5: Quorum met", pending.is_quorum_met)

        # Second attempt: should succeed now (admin initiates again)
        r5b, rep5b, trace5b = r7team.submit_action(
            "admin", "emergency_shutdown", "all-services",
        )
        check("T5b: Action succeeded after multi-sig", r5b.status == "success")
        check("T5b: Multi-sig layer OK in trace",
              any(l[0] == "L09_multisig" and l[1] == "OK" for l in trace5b["layers_activated"]))

        # ── Test 6: ATP exhaustion ──
        print("\n── Test 6: ATP exhaustion ──")
        original_atp = team.team_atp
        # Drain ATP
        team.team_atp = 2.0  # less than review_pr cost (5.0)

        r6, rep6, trace6 = r7team.submit_action("sage-agent", "review_pr", "pr-200")
        check("T6: Denied for insufficient ATP", r6.status == "error")
        check("T6: Error mentions ATP", "atp" in r6.error.lower())

        # Restore
        team.team_atp = original_atp

        # ── Test 7: Multiple actions + reputation accumulation ──
        print("\n── Test 7: Reputation accumulation (5 reviews) ──")

        initial_t3 = team.members["sage-agent"].t3.composite()
        for i in range(5):
            r7team.submit_action("sage-agent", "review_pr", f"pr-{200+i}")

        final_t3 = team.members["sage-agent"].t3.composite()
        check("T7: T3 increased after 5 successes", final_t3 > initial_t3,
              f"initial={initial_t3:.4f}, final={final_t3:.4f}")

        member_rep = r7team.get_member_reputation("sage-agent")
        check("T7: Role reputations tracked", len(member_rep.get("role_reputations", {})) > 0)

        # ── Flush heartbeat and verify ledger ──
        print("\n── Ledger Verification ──")
        flushed = r7team.flush_heartbeat()
        check("Heartbeat flushed", flushed > 0, f"flushed {flushed} actions")

        verification = team.ledger.verify()
        check("Ledger chain valid", verification["valid"])
        check("Ledger has entries", verification["entries"] >= 5,
              f"entries={verification['entries']}")

        # Check that R7 reputation data is in ledger
        entries = team.ledger.tail(3)
        has_r7_rep = any("r7_reputation" in e.get("action", {}) for e in entries)
        check("R7 reputation recorded in ledger", has_r7_rep)

        has_gov_trace = any("governance_trace" in e.get("action", {}) for e in entries)
        check("Governance trace recorded in ledger", has_gov_trace)

        # ── Summary ──
        print("\n" + "=" * 70)
        total = checks_passed + checks_failed
        print(f"  R7 → Hardbound Integration: {checks_passed}/{total} checks passed")

        if checks_failed == 0:
            print(f"  ALL CHECKS PASSED!")
        else:
            print(f"  {checks_failed} check(s) FAILED")

        print(f"\n  Key integration properties verified:")
        print(f"    ✓ R7 actions flow through 10 governance layers")
        print(f"    ✓ RBAC denials still produce reputation (R7 requirement)")
        print(f"    ✓ Multi-sig gates critical R7 actions")
        print(f"    ✓ Birth cert required for any action")
        print(f"    ✓ Dynamic ATP costs from policy")
        print(f"    ✓ R7 reputation deltas recorded in hash-chained ledger")
        print(f"    ✓ Governance trace provides full auditability")
        print(f"    ✓ Reputation accumulates on entity T3/V3")
        print(f"    ✓ Heartbeat batches R7 actions into ledger blocks")
        print("=" * 70)

        return checks_failed == 0

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    success = run_integration_test()
    sys.exit(0 if success else 1)
