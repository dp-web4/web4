from __future__ import annotations

"""Greedy treasurer adversarial scenario demo.

This CLI script:
- Bootstraps the home society world.
- Binds roles (auditor, law-oracle, treasurer) and pairs treasurer with a
  primary treasury LCT (via engine.scenarios and engine.roles).
- Simulates a "greedy" treasurer by appending treasury-related events.
- Applies a simple policy that responds by lowering trust, issuing an
  audit_request, and revoking the treasurer role.
- Runs the world for several ticks and prints resulting blocks and
  MRH/LCT context edges.

This is a first pass at an "immune system" loop for Web4 societies.
"""

from pprint import pprint

from engine.scenarios import bootstrap_home_society_world
from engine.sim_loop import run_world, tick_world
from engine.audit import request_audit
from engine.roles import revoke_role, make_role_lct


def main() -> None:
    world = bootstrap_home_society_world()

    # Convenience lookups
    root_society_lct = "lct:web4:society:home-root"
    treasury_lct = f"{root_society_lct}:treasury:primary"
    alice_lct = "lct:web4:agent:alice"
    bob_lct = "lct:web4:agent:bob"

    society = world.get_society(root_society_lct)
    assert society is not None, "Home society missing in bootstrap world"

    # Role LCTs (must match those constructed in scenarios.bind_role calls)
    treasurer_role_lct = make_role_lct(root_society_lct, "treasurer")

    # Simple parameters for the demo
    greedy_actions = 5
    abuse_threshold = 3
    audits_issued = 0
    revoked = False

    # Simulate a number of ticks with "greedy" treasurer behavior.
    for step in range(greedy_actions):
        # Treasurer attempts a questionable treasury transfer each step.
        event = {
            "type": "treasury_spend",
            "society_lct": root_society_lct,
            "treasury_lct": treasury_lct,
            "initiator_lct": bob_lct,
            "amount": 50.0,
            "reason": "suspicious self-allocation",
            "world_tick": world.tick,
        }
        society.pending_events.append(event)

        # After enough abuses, respond with an audit and eventual revocation.
        if step + 1 >= abuse_threshold and not revoked:
            # Issue an audit once when threshold is crossed.
            if audits_issued == 0:
                scope = {
                    "fields": ["trust_axes.T3.composite", "resources.ATP"],
                    "mrh": {
                        "deltaR": "local",
                        "deltaT": "session",
                        "deltaC": "agent-scale",
                    },
                }
                request_audit(
                    world=world,
                    society=society,
                    auditor_lct=alice_lct,
                    target_lct=bob_lct,
                    scope=scope,
                    reason="suspicious treasury activity by treasurer",
                    atp_allocation=10.0,
                )
                audits_issued += 1

            # Revoke the treasurer role after repeated abuse.
            if step + 1 == abuse_threshold:
                revoke_role(
                    world=world,
                    society=society,
                    role_lct=treasurer_role_lct,
                    subject_lct=bob_lct,
                    reason="treasurer revoked due to repeated suspicious spending",
                )
                revoked = True

        # Advance the world by one tick so events are sealed into blocks.
        tick_world(world)

    # Run a few extra ticks to ensure blocks are sealed.
    run_world(world, steps=10)

    print("=== World Tick ===")
    print(world.tick)

    print("\n=== Societies and Blocks ===")
    for s in world.societies.values():
        print(f"Society: {s.name} ({s.society_lct})")
        print(f"  Block interval (s): {s.block_interval_seconds}")
        print(f"  Blocks sealed: {len(s.blocks)}")
        for block in s.blocks:
            print("  - Block", block["index"], "@ t=", block["timestamp"])
            print("    header_hash:", block.get("header_hash"))
            print("    previous_hash:", block.get("previous_hash"))
            print("    signature:", block.get("signature"))
            print("    Events:")
            for ev in block["events"]:
                print("     ", ev)

    # Simple trust summaries for tuning.
    bob = world.agents.get(bob_lct)
    if bob and bob.trust_axes.get("T3"):
        print("\n=== Agent Trust (Bob) ===")
        print("  T3 composite:", bob.trust_axes["T3"].get("composite"))

    if society.trust_axes.get("T3"):
        print("\n=== Society Trust (Home Root) ===")
        print("  T3 composite:", society.trust_axes["T3"].get("composite"))

    print("\n=== MRH / LCT Context Edges ===")
    for edge in world.context_edges:
        print(
            f"  {edge.subject} --{edge.predicate}--> {edge.object} | MRH={edge.mrh}"
        )

    print("\n=== Policy and Treasury Enforcement Events ===")
    for block in society.blocks:
        for ev in block.get("events", []):
            etype = ev.get("type")
            if etype in {"treasury_spend_rejected", "role_revocation", "membership_revocation"}:
                print("  ", etype, "-", ev.get("reason"))


if __name__ == "__main__":
    main()
