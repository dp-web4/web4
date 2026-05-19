"""Quickstart for the web4 Python SDK v0.28.0.

Demonstrates the three behavioral composition points of the current SDK:

    generate(type) -> from_jsonld(doc)   # JSON-LD roundtrip (23 types)
    evaluate_trust_query(...)            # direct trust resolution
    process_action_outcome(...)          # action consequence pipeline

Runs offline. No network, no external services. Prints a readable summary of
what happened at each step. Intended as living documentation — if the SDK
surface changes in a breaking way, this file stops running.

Run:

    pip install -e web4-standard/implementation/sdk/
    python web4-standard/implementation/sdk/examples/quickstart.py
"""

from __future__ import annotations

import web4
from web4.atp import ATPAccount
from web4.r6 import (
    ActionStatus,
    R7Action,
    Reference,
    Request,
    ResourceRequirements,
    Result,
    Role,
    Rules,
)
from web4.reputation import ReputationEngine
from web4.trust import T3, V3, DisclosureLevel, TrustProfile, TrustQuery

SEP = "-" * 68


def step_roundtrip() -> None:
    """generate() minimal LCT -> from_jsonld() -> to_jsonld() fidelity."""
    print(SEP)
    print("1. JSON-LD dispatcher roundtrip")
    print(SEP)

    doc = web4.generate("LinkedContextToken")
    print(f"  generate('LinkedContextToken') @type: {doc.get('@type')}")
    print(f"  fields: {sorted(k for k in doc if not k.startswith('@'))}")

    obj = web4.from_jsonld(doc)
    print(f"  from_jsonld -> {type(obj).__name__}")

    # Roundtrip fidelity: to_jsonld must reproduce the dispatched document.
    out = obj.to_jsonld()
    assert out == doc, "LCT roundtrip lost information"
    print("  to_jsonld() == generate() document: OK")
    print()


def step_trust_query() -> None:
    """Direct trust resolution via evaluate_trust_query()."""
    print(SEP)
    print("2. Direct trust resolution (evaluate_trust_query)")
    print(SEP)

    querier = "lct:web4:agent:alice"
    target = "lct:web4:agent:bob"
    role = "data-analyst"

    # Target exposes a tensor for the role being queried.
    profile = TrustProfile(entity_id=target)
    profile.set_role(
        role,
        t3=T3(talent=0.82, training=0.75, temperament=0.68),
        v3=V3(valuation=0.70, veracity=0.88, validity=0.74),
    )

    # Requester stakes ATP. lock() succeeds only if available >= stake.
    # TrustQuery enforces a minimum stake (see web4/trust.py).
    requester_atp = ATPAccount(available=50.0)

    query = TrustQuery(
        querier=querier,
        target_entity=target,
        requested_role=role,
        intended_interaction="review",
        atp_stake=10,
        validity_period=3600,
        signature="sig:demo",
        disclosure_level=DisclosureLevel.RANGE,
    )

    response = web4.evaluate_trust_query(query, profile, requester_atp)
    print(f"  role:          {role}")
    print(f"  status:        {response.status}")
    print(f"  approved:      {response.is_approved}")
    if response.is_approved:
        t3 = response.t3_in_role
        assert t3 is not None
        print(f"  t3_in_role:    talent={t3.talent:.3f} training={t3.training:.3f} temperament={t3.temperament:.3f}")
        print(f"  stake locked:  {response.stake_locked}")
        print(f"  commitment:    {response.commitment}")
    print(f"  account: locked={requester_atp.locked} available={requester_atp.available}")
    print()


def step_action_outcome() -> None:
    """Action consequence pipeline via process_action_outcome()."""
    print(SEP)
    print("3. Action consequence pipeline (process_action_outcome)")
    print(SEP)

    actor = "lct:web4:agent:alice"
    role_lct = "lct:web4:role:data-analyst"

    # Profile before the action.
    profile = TrustProfile(entity_id=actor)
    profile.set_role(
        role_lct,
        t3=T3(talent=0.60, training=0.60, temperament=0.60),
        v3=V3(valuation=0.60, veracity=0.60, validity=0.60),
    )

    account = ATPAccount(available=100.0)
    stake = 10.0
    account.lock(stake)

    action = R7Action(
        rules=Rules(law_hash="law:v1", society="web4:demo"),
        role=Role(actor=actor, role_lct=role_lct),
        request=Request(action="analyze", target="dataset:demo", atp_stake=stake),
        reference=Reference(mrh_depth=1),
        resource=ResourceRequirements(required_atp=stake),
        result=Result(status=ActionStatus.SUCCESS, atp_consumed=stake, output={"rows": 42}),
    )

    engine = ReputationEngine()
    outcome = web4.process_action_outcome(action, engine, profile, account)

    t3_after = outcome.updated_t3
    v3_after = outcome.updated_v3
    print(f"  action status:  {action.result.status.value}")
    print(f"  ATP settled:    committed={outcome.atp_committed:.1f} rolled_back={outcome.atp_rolled_back:.1f}")
    print(
        f"  T3 after:       talent={t3_after.talent:.3f}"
        f" training={t3_after.training:.3f}"
        f" temperament={t3_after.temperament:.3f}"
    )
    print(
        f"  V3 after:       valuation={v3_after.valuation:.3f}"
        f" veracity={v3_after.veracity:.3f}"
        f" validity={v3_after.validity:.3f}"
    )
    if outcome.delta is not None:
        print(f"  reputation delta: {outcome.delta}")
    print(f"  account: available={account.available:.1f} adp={account.adp:.1f}")
    print()


def main() -> None:
    print(f"web4 SDK v{web4.__version__} quickstart")
    print()
    step_roundtrip()
    step_trust_query()
    step_action_outcome()
    print("Quickstart complete.")


if __name__ == "__main__":
    main()
