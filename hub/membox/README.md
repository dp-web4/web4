# Hub member discovery — `find_members`

> The hub is the front door; **membot is the engine.**

Semantic member discovery for a Web4 hub. A member asks *"who can help me with
X?"* over the E2E channel; the hub gates + scopes the request and composes
membot's cartridge/membox search to return ranked member LCTs. The caller then
drives `request_intro` (next).

This is the **library** integration (Stage 1 of the membot green-light, forum:
`waving-cat-to-hub-membot-greenlight-2026-06-09.md`): the hub owns ingestion,
the front door, intros, and chapter-law gating; membot ships the cart format,
the pinned embedding model, and the 3-signal search (cosine + Hamming + keyword
rerank).

## Pieces

| File | Role |
|------|------|
| `ingest.py` | Reads hub members → free-form prose passages → embeds (pinned **nomic-embed-text-v1.5**) → writes a `.cart.npz` + a passage-index-aligned `members.json` (forward-compat tags). |
| `sidecar.py` | Long-lived localhost HTTP service. Mounts the cart + holds the model once. `POST /find_members {query, top_k, temperature}` → ranked `{member_lct, name, score, tags}`. `GET /health`. |
| `test_ingest.py` | Passage/tag contract tests (no model load). |

The Rust hub-side `find_members` channel tool (in `hub-daemon/src/rest.rs`)
calls the sidecar over localhost, gated by chapter law (`read:find_members`) and
bounded by tier (`ReadScope`). A `walk_members` slot is reserved for membot's
forthcoming Walk-as-MCP (register-and-gate, not reimplement).

## Locked v1 contract (the three adds)

1. **Model pinned** to `nomic-ai/nomic-embed-text-v1.5` (free via `cartridge_builder`).
2. **Forward-compat tags** per member (`member_lct`, `profile_version`,
   `last_pair_purpose`) so V3 trust feedback slots in without re-imprinting.
3. **Temperature knob from day one** — accepted at the API boundary now;
   precision-only until membot exposes settle-noise in search (then wired through).

Passage shape: `{Name}. {free-form skills/interests prose}. Recent pair purposes: {…}.`
Tuning: `top_k` 10–15, keyword rerank ~0.05/hit, hippocampus-walk off (single-passage profiles).

## Operate

```bash
# (re)build the cart from the live hub
membot/.venv/bin/python ingest.py --out /home/dp/web4-hub/membox-data --name web4-fleet-members
sudo systemctl restart web4-membox     # re-mount after re-ingest

# the sidecar runs as systemd web4-membox.service (port 8771, localhost)
systemctl status web4-membox
curl -s http://127.0.0.1:8771/health
```

**Data note:** discovery is only as rich as member profiles. Until members
declare skills/interests (MemberSkillDeclared / MemberProfileUpdated, e.g. via
Hestia), passages are name-only and matches are weak. The engine is live; the
data populates as members fill in.
