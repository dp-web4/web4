from __future__ import annotations

"""Three-society federation/suppression demo.

Bootstraps the three-society world, runs the simulation for a number of
steps, and prints a summary of society-level trust and cross-society
suppression events.
"""

from engine.three_societies import bootstrap_three_societies_world
from engine.sim_loop import run_world
from engine.verify import verify_chain_structure


def main() -> None:
    world = bootstrap_three_societies_world()
    run_world(world, steps=40)

    print("=== Societies and Trust ===")
    for soc in world.societies.values():
        struct = verify_chain_structure(soc)
        t_axes = (soc.trust_axes or {}).get("T3") or {}
        composite = t_axes.get("composite", 0.0)
        print(f"Society: {soc.name} ({soc.society_lct})")
        print(f"  Blocks: {struct['block_count']}  Chain valid: {struct['valid']}")
        print(f"  Society trust (T3.composite): {composite:.2f}")

        suppression_events = [
            ev
            for b in soc.blocks
            for ev in b.get("events", [])
            if ev.get("type") in {"federation_throttle", "quarantine_request"}
        ]
        if suppression_events:
            print("  Suppression events:")
            for ev in suppression_events:
                print("   ", ev)


if __name__ == "__main__":
    main()
