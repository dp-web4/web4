#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
#
# Web4 Community Hub - first-day governance demo (native binary, no Docker).
#
# This is deliberately a THROWAWAY demo posture. It creates a fresh temporary hub,
# uses an explicit NULL passphrase so the daemon can boot without a separate unlock
# ceremony, seeds two members + skills + a public event, then exercises the live
# public/member-readable surfaces and verifies BOTH ledger integrity and the public
# decision-record linkage.
#
# The script is meant to answer a simple demo question:
#   "Can I create a community, add people, record governed activity, and show an
#    outside observer an auditable record without exposing private member facts?"
#
# Prerequisites:
#   - `hub` binary built and on PATH, OR set HUB=/absolute/path/to/hub
#   - python3
#   - curl
#
# Do NOT copy the NULL-passphrase posture into a real deployment.

set -euo pipefail

HUB="${HUB:-hub}"

if ! command -v "$HUB" >/dev/null 2>&1 && [ ! -x "$HUB" ]; then
    echo "error: '$HUB' is not executable or on PATH"
    echo "       set HUB=/absolute/path/to/hub or run cargo build --release first"
    exit 1
fi

# Explicit NULL key is intentional for this throwaway fixture. Hub distinguishes an
# explicit empty passphrase from an unset one; unset in a non-TTY script fails closed.
export HUB_PASSPHRASE=""

DEMO_ROOT="$(mktemp -d /tmp/web4-community-demo.XXXXXX)"
CHAPTER="$DEMO_ROOT/demo-chapter"
PORT=$(( ( RANDOM % 1000 ) + 18000 ))
BASE="http://127.0.0.1:$PORT"
DAEMON_PID=""

stop_daemon() {
    if [ -n "$DAEMON_PID" ]; then
        kill "$DAEMON_PID" 2>/dev/null || true
        wait "$DAEMON_PID" 2>/dev/null || true
        DAEMON_PID=""
    fi
}
trap stop_daemon EXIT INT TERM

banner() {
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

banner "Web4 Community Hub - first-day governance demo"
echo "Demo dir: $DEMO_ROOT"
echo "Binary:   $HUB ($($HUB --version))"
echo "Posture:  throwaway explicit NULL passphrase"

# 1. Mint identities. Modern gen-lct output is the authoritative way to capture
# the public id: the files are encrypted vaults and MUST NOT be json.load()'d.
banner "1. Mint a Sovereign and two member identities"
"$HUB" gen-lct "$DEMO_ROOT/sovereign.json"
ALICE_ID=$("$HUB" gen-lct "$DEMO_ROOT/alice.json" | awk '/LCT id:/ {print $3}')
BOB_ID=$("$HUB" gen-lct "$DEMO_ROOT/bob.json" | awk '/LCT id:/ {print $3}')
[ -n "$ALICE_ID" ] && [ -n "$BOB_ID" ] || {
    echo "error: could not capture member LCT ids from hub gen-lct output" >&2
    exit 1
}
echo "Alice: $ALICE_ID"
echo "Bob:   $BOB_ID"

# 2. Create the society and seed member-visible state.
banner "2. Initialize the community and add members"
"$HUB" init "Demo Chapter" \
    --sovereign-lct "$DEMO_ROOT/sovereign.json" \
    --hub-dir "$CHAPTER"
"$HUB" add-member "$CHAPTER" "$ALICE_ID" --name "Alice"
"$HUB" add-member "$CHAPTER" "$BOB_ID" --name "Bob"
"$HUB" declare-skill "$CHAPTER" "$ALICE_ID" "Community governance"
"$HUB" declare-skill "$CHAPTER" "$BOB_ID" "Distributed systems"

# 3. Create a public-safe governance/activity beat. EventRecorded is intentionally
# classified for the public decision projection; attendee identities are not.
banner "3. Record a governed chapter event"
"$HUB" record-event "$CHAPTER" demo_night "First Demo Night" \
    --attended-by "$ALICE_ID,$BOB_ID"

# 4. Show the local/query plane before involving HTTP.
banner "4. Query the community locally"
"$HUB" query members "$CHAPTER"
echo ""
"$HUB" query skill "$CHAPTER" governance

# 5. Start the actual daemon. The explicit NULL passphrase makes this fixture
# directly runnable; a real encrypted deployment normally boots locked and is
# ignited separately with hub unlock. The operator plane is disabled so this
# throwaway smoke cannot collide with or impersonate a real local operator UI.
banner "5. Start the live daemon"
"$HUB" serve "$CHAPTER" --port "$PORT" --admin-port 0 > "$DEMO_ROOT/serve.log" 2>&1 &
DAEMON_PID=$!

ready=0
for ((i=0; i<40; i++)); do
    if curl -fsS "$BASE/tools" >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 0.25
done
if [ "$ready" -ne 1 ]; then
    echo "error: hub did not become ready at $BASE" >&2
    echo "--- serve.log ---" >&2
    cat "$DEMO_ROOT/serve.log" >&2 || true
    exit 1
fi

echo "Daemon PID: $DAEMON_PID"
echo "Public URL: $BASE"

# Discover the hub id from the canonical descriptor rather than guessing it from
# local filenames or CLI formatting.
WELL_KNOWN=$(curl -fsS "$BASE/.well-known/web4-hub.json")
HUB_ID=$(printf '%s' "$WELL_KNOWN" | python3 -c \
    'import json,sys; print(json.load(sys.stdin)["hub_lct_id"])')
[ -n "$HUB_ID" ] || { echo "error: discovery did not return hub_lct_id" >&2; exit 1; }
echo "Hub LCT:    $HUB_ID"

# 6. Current tool spelling: list_members. This replaces the old first-chapter
# script's stale query_chapter probe.
banner "6. Exercise the live member-readable surface"
echo "GET /tools/list_members"
curl -fsS "$BASE/tools/list_members" | python3 -m json.tool

# 7. Public governance transparency. The response intentionally includes withheld
# entries to preserve continuity without exposing private member facts.
banner "7. Exercise the PUBLIC decision record"
DECISIONS_JSON="$DEMO_ROOT/public-decisions.json"
DECISIONS_HTML="$DEMO_ROOT/public-decisions.html"
curl -fsS "$BASE/v1/hubs/$HUB_ID/decisions" > "$DECISIONS_JSON"
python3 -m json.tool < "$DECISIONS_JSON"

# Verify the property the public record promises, not merely that it returned 200.
# Decisions are newest-first. For each adjacent pair, newer.prev_hash must equal
# older.entry_hash. Require at least one disclosed act and at least one withheld act
# so the demo actually crosses the privacy boundary it is meant to demonstrate.
# Then render the VERIFIED JSON into a standalone browser page. The page has no
# independent data path: it is a presentation of the exact response just checked.
python3 - "$DECISIONS_JSON" "$DECISIONS_HTML" <<'PY'
import html
import json
import sys

src, dst = sys.argv[1:3]
with open(src, encoding="utf-8") as f:
    record = json.load(f)
decisions = record.get("decisions", [])
assert decisions, "public decision record is empty"
assert record.get("disclosed", 0) > 0, "demo has no publicly disclosed governance act"
assert record.get("withheld", 0) > 0, "demo did not exercise a withheld/private entry"

for newer, older in zip(decisions, decisions[1:]):
    assert newer["prev_hash"] == older["entry_hash"], (
        f"public chain linkage broken between indexes {newer['index']} and {older['index']}"
    )

kinds = [d["kind"] for d in decisions if d.get("disclosure") == "disclosed"]
assert "genesis" in kinds, "genesis is not visible in the public projection"
assert "event_recorded" in kinds, "recorded demo event is not visible in the public projection"

print(
    "public decision record verified: "
    f"{record['returned']} entries, {record['disclosed']} disclosed, "
    f"{record['withheld']} withheld; hash linkage intact across the window"
)

def esc(value):
    return html.escape(str(value), quote=True)

def short(value):
    value = str(value)
    return value if len(value) <= 20 else value[:12] + "..." + value[-6:]

rows = []
for d in decisions:
    disclosed = d.get("disclosure") == "disclosed"
    label = d.get("kind", "withheld") if disclosed else "private act withheld"
    detail = d.get("detail") if disclosed else (
        "The act stays private; its position and hash link remain public so it cannot be silently removed."
    )
    auth = "council-authorized" if d.get("council_authorized") else "ordinary governed act"
    rows.append(f"""
      <article class="decision {'public' if disclosed else 'withheld'}">
        <div class="meta">#{esc(d['index'])} &middot; {esc(d['timestamp'])} &middot; {esc(auth)}</div>
        <h2>{esc(label.replace('_', ' '))}</h2>
        <p>{esc(detail or '')}</p>
        <div class="hashes">
          <code>prev {esc(short(d['prev_hash']))}</code>
          <span>&rarr;</span>
          <code>this {esc(short(d['entry_hash']))}</code>
        </div>
      </article>
    """)

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Web4 Community Hub - Public Governance Record</title>
<style>
:root {{ color-scheme: light dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
body {{ margin:0; background:Canvas; color:CanvasText; }}
main {{ max-width:920px; margin:0 auto; padding:48px 24px 80px; }}
.eyebrow {{ text-transform:uppercase; letter-spacing:.12em; font-size:.78rem; opacity:.65; }}
h1 {{ font-size:clamp(2rem,6vw,4.5rem); line-height:.95; max-width:800px; margin:.4rem 0 1rem; }}
.lede {{ font-size:1.18rem; line-height:1.55; max-width:760px; opacity:.8; }}
.stats {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:32px 0; }}
.stat {{ border:1px solid color-mix(in srgb, CanvasText 18%, transparent); border-radius:14px; padding:18px; }}
.stat strong {{ display:block; font-size:2rem; }}
.timeline {{ display:grid; gap:14px; }}
.decision {{ border:1px solid color-mix(in srgb, CanvasText 18%, transparent); border-left-width:5px; border-radius:14px; padding:20px 22px; }}
.decision.public {{ border-left-color:#2b8a3e; }}
.decision.withheld {{ border-left-color:#777; opacity:.82; }}
.meta {{ font-size:.8rem; opacity:.62; }}
h2 {{ margin:.35rem 0 .5rem; font-size:1.2rem; text-transform:capitalize; }}
p {{ line-height:1.5; }}
.hashes {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; font-size:.82rem; opacity:.72; }}
code {{ font-family:ui-monospace, SFMono-Regular, Menlo, monospace; }}
.note {{ margin-top:34px; padding:18px 20px; border-radius:14px; background:color-mix(in srgb, CanvasText 7%, transparent); line-height:1.55; }}
@media (max-width:600px) {{ .stats {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<main>
  <div class="eyebrow">Web4 Community Hub</div>
  <h1>Public governance record</h1>
  <p class="lede">Consequential chapter acts are recorded in an append-only chain. Public-safe acts are described; private acts remain withheld. Both still carry the hash linkage needed to show that an inconvenient entry was not simply deleted.</p>
  <section class="stats">
    <div class="stat"><strong>{esc(record['returned'])}</strong>entries shown</div>
    <div class="stat"><strong>{esc(record['disclosed'])}</strong>public acts</div>
    <div class="stat"><strong>{esc(record['withheld'])}</strong>private acts withheld</div>
  </section>
  <section class="timeline">{''.join(rows)}</section>
  <div class="note"><strong>Verified before render.</strong> This page was generated only after the demo checked every adjacent hash link in the returned record, including links across withheld entries. The full local ledger is verified independently in the next demo step.</div>
</main>
</body>
</html>"""

with open(dst, "w", encoding="utf-8") as f:
    f.write(page)
print(f"human-readable governance timeline: file://{dst}")
PY

# 8. Verify the source ledger independently after stopping the daemon.
banner "8. Verify the underlying witnessed ledger"
stop_daemon
"$HUB" verify-ledger "$CHAPTER"

banner "Demo complete"
echo "The useful contrast is now visible in one run:"
echo "  - members and skills exist"
echo "  - governed activity is recorded"
echo "  - an anonymous observer can inspect the public decision record"
echo "  - private member facts remain withheld"
echo "  - hash linkage stays verifiable across withheld entries"
echo "  - the full local ledger independently verifies"
echo ""
echo "Artifacts:"
echo "  hub directory:     $CHAPTER"
echo "  daemon log:        $DEMO_ROOT/serve.log"
echo "  public decisions:  $DECISIONS_JSON"
echo "  browser timeline:  file://$DECISIONS_HTML"
