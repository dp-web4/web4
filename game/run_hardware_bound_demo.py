from __future__ import annotations

"""Hardware-bound Web4 game demo (v0).

This demo bootstraps a hardware-bound world, runs a few ticks, and
prints basic verification results for the society's microchain and
hardware binding invariants.

It is intentionally minimal and meant for manual inspection rather
than as a full test harness.
"""

from engine.hw_bootstrap import bootstrap_hardware_bound_world
from engine.sim_loop import run_world
from engine.verify import verify_chain_structure, verify_hardware_binding


def main() -> None:
    # Bootstrap a hardware-bound world with a single root society.
    result = bootstrap_hardware_bound_world()
    world = result.world
    root_society = world.get_society(result.society_lct)

    if root_society is None:
        print("[error] failed to locate root hardware-bound society")
        return

    print("=== Hardware-Bound World Bootstrap ===")
    print("  Hardware fingerprint:", root_society.hardware_fingerprint)
    print("  Society LCT:", root_society.society_lct)

    # Run a few ticks so that the society can potentially seal blocks
    # (depending on block_interval_seconds and pending events).
    run_world(world, steps=5)

    print("\n=== Chain Structure Verification ===")
    chain_result = verify_chain_structure(root_society)
    print("  valid:", chain_result["valid"])
    print("  errors:")
    for err in chain_result["errors"]:
        print("   -", err)
    print("  block_count:", chain_result["block_count"])

    print("\n=== Hardware Binding Verification ===")
    hw_result = verify_hardware_binding(root_society)
    print("  valid:", hw_result["valid"])
    print("  errors:")
    for err in hw_result["errors"]:
        print("   -", err)


if __name__ == "__main__":
    main()
