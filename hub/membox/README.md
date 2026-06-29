# Hub member discovery — `find_members`

> The hub is the front door; **membot is the engine.**
>
> **The cart is a pure index — no member PII at rest.** It stores embeddings
> keyed to opaque member LCTs and nothing else. Names and profiles live once, in
> the hub's authoritative encrypted registry, and the hub re-attaches them at
> query time. Member prose exists only in RAM during embedding; it is never
> persisted.

Semantic member discovery for a Web4 hub. A member asks *"who can help me with
X?"* over the E2E channel; the hub gates + scopes the request and composes
membot's cartridge/membox search to return ranked member LCTs. The caller then
drives `request_intro` (next).

This is the **library** integration (Stage 1 of the membot green-light, forum:
`waving-cat-to-hub-membot-greenlight-2026-06-09.md`): the hub owns ingestion,
the front door, intros, and hub-law gating; membot ships the cart format,
the pinned embedding model, and the 3-signal search (cosine + Hamming + keyword
rerank).

## Pieces

| File | Role |
|------|------|
| `ingest.py` | Reads hub members → builds free-form prose passages → embeds (pinned **nomic-embed-text-v1.5**) → writes a `.cart.npz` whose stored "text" is the **opaque member LCT** (not the prose) + a passage-index-aligned `members.json` holding only `{member_lct, profile_version}`. The prose is used to compute embeddings in RAM and discarded. |
| `sidecar.py` | Long-lived localhost HTTP service. Mounts the cart + holds the model once. `POST /find_members {query, top_k, temperature}` → ranked `{member_lct, score}` (plus the echoed `temperature`) — no name, no tags. `GET /health` → `{ok, cart, n_members, fingerprint}`. |
| `test_ingest.py` | Passage/index contract tests (no model load). |

The Rust hub-side `find_members` channel tool (in `hub-daemon/src/rest.rs`)
calls the sidecar over localhost, gated by hub law (`read:find_members`) and
bounded by tier (`ReadScope`). A `walk_members` slot is reserved for membot's
forthcoming Walk-as-MCP (register-and-gate, not reimplement).

## Locked v1 contract (the three adds)

1. **Model pinned** to `nomic-ai/nomic-embed-text-v1.5` (free via `cartridge_builder`).
2. **Pure index, no PII at rest** — the cart stores the opaque `member_lct` as
   each passage's text; `members.json` carries only `{member_lct, profile_version}`
   (`profile_version` is a one-way sha256 prefix of the passage, so it changes
   exactly when a member's profile changes, without storing the content). The
   `find_members` response is just `{member_lct, score}`; the hub enriches it
   with name/profile from its encrypted registry.
3. **Temperature knob from day one** — accepted at the API boundary now;
   precision-only until membot exposes settle-noise in search (then wired through).

Passage shape (RAM only, fed to the embedder and discarded): `{Name}. {free-form
skills/interests prose}.`
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
