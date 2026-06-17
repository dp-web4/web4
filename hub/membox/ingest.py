#!/usr/bin/env python3
"""Build a per-hub member-discovery cart from the hub's live membership.

The hub is the front door; membot is the engine. This is the ingestion half:
it reads the hub's members, turns each into a free-form prose passage, embeds
them with membot's pinned model, and writes a `.cart.npz` the sidecar serves.

Per the locked v1 contract (forum: waving-cat-to-hub greenlight, 2026-06-09):
  - Model PINNED to nomic-ai/nomic-embed-text-v1.5 (we get this for free by
    using membot's cartridge_builder.embed_texts — same model as Membot/Studio).
  - Passage shape is PROSE, not schema: "{Name}. {free-form skills/interests}.
    Recent pair purposes: {…}." — honors "skills stay plain language".
  - Forward-compat provenance carried alongside the cart (member_lct,
    profile_version, last_pair_purpose) so V3 trust feedback slots in later
    without re-imprinting. We keep it in a sidecar JSON keyed by passage index
    (local_addr) rather than the cart's fixed hippocampus struct.

Usage:
  membot/.venv/bin/python ingest.py \
      --members-url http://127.0.0.1:8770/tools/list_members \
      --out /home/dp/web4-hub/membox-data \
      --name web4-fleet-members
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request

# membot ships the cart format + embedding pipeline; we compose it as a library.
MEMBOT_DIR = os.environ.get("MEMBOT_DIR", "/home/dp/ai-workspace/membot")
sys.path.insert(0, MEMBOT_DIR)


def fetch_members(url: str) -> list[dict]:
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.loads(r.read().decode())
    return data.get("members", [])


def member_passage(m: dict) -> str:
    """Free-form prose an LLM-reader could synthesize naturally. We concatenate
    the member's own words (skills + profile free-text), NOT schema fields."""
    name = m.get("name") or str(m.get("lct_id", "unknown"))[:8]
    prose_parts: list[str] = []
    skills = m.get("skills") or []
    if skills:
        prose_parts.append(", ".join(skills))
    profile = m.get("profile") or {}
    # profile values are free-text prose (interests, etc.). Skip the pair-purpose
    # key — it has its own slot in the passage tail.
    for k, v in profile.items():
        if k == "last_pair_purpose":
            continue
        if v:
            prose_parts.append(v)
    prose = ". ".join(p for p in prose_parts if p)
    passage = f"{name}." if not prose else f"{name}. {prose}."
    pair_purpose = profile.get("last_pair_purpose")
    if pair_purpose:
        passage += f" Recent pair purposes: {pair_purpose}."
    return passage


def member_index_entry(m: dict, passage: str) -> dict:
    """The cart is a pure INDEX, not a copy of member data. We persist only the
    minimal map: passage-index → member_lct, plus a content-hash for cache
    invalidation. NO name, profile text, skills, or pair purpose — those live
    once in the hub's (encrypted) registry and are re-attached by the hub at
    query time. `profile_version` is a one-way sha256 of the passage (changes
    exactly when a member's profile changes), not the content itself."""
    return {
        "member_lct": m.get("lct_id"),
        "profile_version": hashlib.sha256(passage.encode()).hexdigest()[:12],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--members-url", default="http://127.0.0.1:8770/tools/list_members")
    ap.add_argument("--out", default="/home/dp/web4-hub/membox-data")
    ap.add_argument("--name", default="web4-fleet-members")
    ap.add_argument("--members-json", help="read members from a file instead of the hub (for tests/demo)")
    args = ap.parse_args()

    if args.members_json:
        with open(args.members_json) as f:
            members = json.load(f).get("members", [])
    else:
        members = fetch_members(args.members_url)

    if not members:
        print("no members to ingest — nothing to do", file=sys.stderr)
        return 1

    import cartridge_builder as cb

    # The member prose is used ONLY to compute embeddings — it exists in RAM for
    # the duration of this process and is never persisted. The cart stores the
    # opaque member_lct as each passage's "text", so the cart on disk is a pure
    # index (embeddings + lct ids), carrying no member PII at rest.
    passages = [member_passage(m) for m in members]
    index = [member_index_entry(m, p) for m, p in zip(members, passages)]
    cart_text = [str(m.get("lct_id") or "") for m in members]

    print(f"embedding {len(passages)} member passages with pinned Nomic model...", flush=True)
    embeddings = cb.embed_texts(passages)

    os.makedirs(args.out, exist_ok=True)
    # Persist the cart with opaque LCTs as the stored text — NOT the prose.
    cart_path, size_mb, fingerprint = cb.save_cartridge(args.out, args.name, embeddings, cart_text)

    # Slim index sidecar, passage-index aligned (== local_addr in search
    # results): maps a hit back to its member_lct. No names / profile text — the
    # hub re-attaches those from its authoritative encrypted registry.
    meta_path = os.path.join(args.out, f"{args.name}.members.json")
    with open(meta_path, "w") as f:
        json.dump({"fingerprint": fingerprint, "members": index}, f, indent=2)
    tags = index  # for the summary print below

    print(f"cart:  {cart_path}  ({size_mb:.2f} MB, fingerprint {fingerprint})")
    print(f"meta:  {meta_path}  ({len(tags)} members)")
    populated = sum(1 for m in members if (m.get("skills") or m.get("profile")))
    print(f"members: {len(members)} total, {populated} with declared skills/profile")
    if populated == 0:
        print("NOTE: no member has declared skills/interests yet — passages are "
              "name-only. Discovery works but is weak until members populate "
              "profiles (MemberProfileUpdated / declare-skill via Hestia).",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
