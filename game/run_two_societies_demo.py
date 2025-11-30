from __future__ import annotations

"""Two-society federation demo.

This CLI script bootstraps a world with two federated societies and
prints a summary of their chains and MRH/LCT context.
"""

from engine.two_societies import bootstrap_two_societies_world
from engine.sim_loop import run_world
from engine.verify import verify_chain_structure, verify_stub_signatures


def main() -> None:
    world = bootstrap_two_societies_world()

    # Run a few ticks so membership/role events are sealed into blocks.
    run_world(world, steps=20)

    print("=== Societies ===")
    for soc in world.societies.values():
        print(f"Society: {soc.name} ({soc.society_lct})")
        struct = verify_chain_structure(soc)
        sigs = verify_stub_signatures(soc)
        print(f"  Blocks: {struct['block_count']}")
        print(f"  Chain structure valid: {struct['valid']}")
        if struct["errors"]:
            print("  Structure errors:")
            for err in struct["errors"]:
                print("    -", err)
        print(f"  Signatures present: {sigs['valid']}")
        if soc.trust_axes.get("T3"):
            print("  T3 composite:", soc.trust_axes["T3"].get("composite"))

    print("\n=== MRH / LCT Context Edges ===")
    for edge in world.context_edges:
        print(
            f"  {edge.subject} --{edge.predicate}--> {edge.object} | MRH={edge.mrh}"
        )


if __name__ == "__main__":
    main()
