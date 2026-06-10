#!/usr/bin/env python3
"""Member-discovery sidecar — the engine behind the hub's find_members tool.

The nomic model is ~600 MB; reloading it per query is a non-starter. So this is
a long-lived localhost HTTP service that mounts the per-hub cart + holds the
loaded model once, and answers find_members. The Rust hub composes it: the hub
owns chapter-law gating + tier scoping; this just does the 3-signal semantic
search (cosine + Hamming + keyword rerank) membot ships.

Endpoints (localhost only — the hub mediates all external access):
  GET  /health                      -> {ok, cart, n_members, fingerprint}
  POST /find_members {query, top_k, temperature}
        -> {results: [{member_lct, name, score, tags}], total}

temperature is accepted now (locked v1 contract: ship the knob from day one)
but the underlying multi_cart.search doesn't expose settle-noise yet, so v1 is
precision-only (temperature is recorded + echoed, wired through when membot
exposes it). Reserved, not faked.
"""
import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MEMBOT_DIR = os.environ.get("MEMBOT_DIR", "/home/dp/ai-workspace/membot")
sys.path.insert(0, MEMBOT_DIR)

STATE = {"cart_id": None, "members": [], "fingerprint": None}


def load(cart_path: str, meta_path: str, cart_id: str):
    import multi_cart as mc
    res = mc.mount(cart_path, cart_id=cart_id, verify_integrity=True)
    with open(meta_path) as f:
        meta = json.load(f)
    STATE["cart_id"] = cart_id
    STATE["members"] = meta.get("members", [])
    STATE["fingerprint"] = meta.get("fingerprint")
    print(f"mounted {cart_id}: {res.get('n_patterns')} patterns, "
          f"{len(STATE['members'])} member records", flush=True)


def do_search(query: str, top_k: int) -> list[dict]:
    import multi_cart as mc
    res = mc.search(query, top_k=top_k, scope=STATE["cart_id"])
    out = []
    members = STATE["members"]
    for r in res.get("results", []):
        addr = r.get("local_addr")
        meta = members[addr] if isinstance(addr, int) and 0 <= addr < len(members) else {}
        out.append({
            "member_lct": meta.get("member_lct"),
            "name": meta.get("name"),
            "score": float(r.get("score", 0.0)),
            "tags": meta,
        })
    # Drop hits we couldn't attribute to a member_lct (defensive).
    return [r for r in out if r["member_lct"]]


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, body: dict):
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *a):  # quiet
        pass

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"ok": True, "cart": STATE["cart_id"],
                             "n_members": len(STATE["members"]),
                             "fingerprint": STATE["fingerprint"]})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/find_members":
            return self._json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._json(400, {"error": f"bad request: {e}"})
        query = (req.get("query") or "").strip()
        if not query:
            return self._json(400, {"error": "query is required"})
        top_k = int(req.get("top_k") or 12)          # contract default 10-15
        temperature = float(req.get("temperature") or 0.0)
        try:
            results = do_search(query, top_k)
        except Exception as e:
            return self._json(500, {"error": f"search failed: {e}"})
        self._json(200, {"results": results, "total": len(results),
                         "temperature": temperature})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/home/dp/web4-hub/membox-data")
    ap.add_argument("--name", default="web4-fleet-members")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8771)
    args = ap.parse_args()

    cart_path = os.path.join(args.data, f"{args.name}.cart.npz")
    meta_path = os.path.join(args.data, f"{args.name}.members.json")
    load(cart_path, meta_path, args.name)

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"membox sidecar on http://{args.host}:{args.port} "
          f"(POST /find_members, GET /health)", flush=True)
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
