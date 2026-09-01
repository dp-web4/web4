#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
#
# Web4 Community Hub - first-day governance demo (native binary, no Docker).
#
# This is deliberately a THROWAWAY demo posture. It creates a fresh temporary hub,
# uses an explicit NULL passphrase so the daemon can boot without a separate unlock
# ceremony, seeds two members + skills + a public event, then exercises the live
# public/member-readable surfaces and verifies:
#
#   1. the CURRENT public-record ratchet rung: disclosed governance acts plus
#      ordinal accounting for compressed private spans; and
#   2. the full local ledger independently.
#
# Production still requires cryptographic hash-chain verification THROUGH withheld
# spans. That stronger requirement is tracked in web4#807. Do not describe this
# demo's span verification as satisfying that production property.
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

# 7. Public governance transparency. Since #802, the API windows over disclosed
# governance acts and compresses private runs into withheld_before spans. This is
# the current DEVELOPMENTAL ratchet rung: it proves ordinal accounting of the
# omitted range. Production hash-chain proof through each span remains #807.
banner "7. Exercise the PUBLIC decision record"
DECISIONS_JSON="$DEMO_ROOT/public-decisions.json"
DECISIONS_HTML="$DEMO_ROOT/public-decisions.html"
curl -fsS "$BASE/v1/hubs/$HUB_ID/decisions" > "$DECISIONS_JSON"
python3 -m json.tool < "$DECISIONS_JSON"

# Verify exactly what the current public response can prove:
# - disclosed rows are ordered newest-first;
# - every omitted/private index between disclosed rows is accounted for by an
#   exact counted span;
# - where two disclosed rows are actually adjacent, their hash link verifies;
# - the demo contains both a public governance act and private activity.
#
# Do NOT infer hash-chain verification through a compressed span. The response
# intentionally does not yet carry the hidden rows' opaque link evidence.
python3 - "$DECISIONS_JSON" "$DECISIONS_HTML" <<'PY'
import html
import json
import sys

src, dst = sys.argv[1:3]
with open(src, encoding="utf-8") as f:
    record = json.load(f)

decisions = record.get("decisions", [])
assert decisions, "public decision record is empty"
assert record.get("disclosed") == len(decisions), (
    "disclosed count must equal returned disclosed rows"
)

head = record.get("head_index")
assert head is not None, "public record did not report head_index"

withheld_total = 0
adjacent_links_verified = 0

for i, decision in enumerate(decisions):
    idx = decision["index"]
    span = decision.get("withheld_before")

    # withheld_before belongs to THIS disclosed row and describes the run between
    # it and the next MORE RECENT disclosed row, or the ledger head for row 0.
    newer_boundary = head if i == 0 else decisions[i - 1]["index"] - 1
    expected_from = idx + 1
    expected_count = max(0, newer_boundary - idx)

    if expected_count:
        assert span is not None, (
            f"indexes {expected_from}..{newer_boundary} are omitted without a span"
        )
        assert span["from_index"] == expected_from
        assert span["to_index"] == newer_boundary
        assert span["count"] == expected_count
        withheld_total += span["count"]
    else:
        assert span is None, f"unexpected withheld span attached to index {idx}"

    # When there is NO hidden row between two disclosed decisions, the ordinary
    # linear hash-chain relation is still directly checkable.
    if i > 0 and span is None:
        newer = decisions[i - 1]
        assert newer["prev_hash"] == decision["entry_hash"], (
            f"direct hash linkage broken between adjacent indexes "
            f"{newer['index']} and {decision['index']}"
        )
        adjacent_links_verified += 1

assert withheld_total == record.get("withheld_in_window", 0), (
    f"span accounting {withheld_total} != withheld_in_window "
    f"{record.get('withheld_in_window')}"
)
assert withheld_total > 0, "demo did not exercise a withheld/private span"

kinds = [d["kind"] for d in decisions]
assert "genesis" in kinds, "genesis is not visible in the public projection"
assert "event_recorded" in kinds, "recorded demo event is not visible in the public projection"

print(
    "public decision record developmental rung verified: "
    f"{len(decisions)} disclosed acts; "
    f"{withheld_total} private entries ordinally accounted in spans; "
    f"{adjacent_links_verified} direct disclosed-to-disclosed hash links verified"
)
print(
    "production ratchet remains web4#807: cryptographic hash-chain proof THROUGH "
    "withheld spans is not yet provided by this compact response"
)

def esc(value):
    return html.escape(str(value), quote=True)

def short(value):
    value = str(value)
    return value if len(value) <= 20 else value[:12] + "..." + value[-6:]

rows = []
for d in decisions:
    span = d.get("withheld_before")
    span_html = ""
    if span:
        span_html = f"""
      <div class="span">
        {esc(span['count'])} private entr{'y' if span['count'] == 1 else 'ies'} withheld
        (indexes {esc(span['from_index'])}-{esc(span['to_index'])}).
        This span proves accounted-for ordinal continuity at the current ratchet rung;
        production cryptographic proof through the span is tracked by web4#807.
      </div>
        """
    auth = "council-authorized" if d.get("council_authorized") else "ordinary governed act"
    rows.append(f"""
      <article class="decision">
        {span_html}
        <div class="meta">#{esc(d['index'])} &middot; {esc(d['timestamp'])} &middot; {esc(auth)}</div>
        <h2>{esc(d.get('kind', 'governed act').replace('_', ' '))}</h2>
        <p>{esc(d.get('detail') or '')}</p>
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
.decision {{ border:1px solid color-mix(in srgb, CanvasText 18%, transparent); border-left:5px solid #2b8a3e; border-radius:14px; padding:20px 22px; }}
.span {{ margin:-20px -22px 18px; padding:12px 22px; border-radius:9px 9px 0 0; background:color-mix(in srgb, CanvasText 7%, transparent); font-size:.88rem; line-height:1.45; opacity:.82; }}
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
  <p class="lede">Public-safe governance acts are described. Private activity is compressed into counted spans, so the visible record stays useful without pretending the private acts are public.</p>
  <section class="stats">
    <div class="stat"><strong>{esc(len(decisions))}</strong>public acts</div>
    <div class="stat"><strong>{esc(withheld_total)}</strong>private entries accounted</div>
    <div class="stat"><strong>{esc(record.get('total_entries', '?'))}</strong>ledger entries total</div>
  </section>
  <section class="timeline">{''.join(rows)}</section>
  <div class="note">
    <strong>Developmental evidence rung.</strong>
    This page was generated only after checking exact index/span accounting and every
    directly observable adjacent hash link. It does <em>not</em> claim cryptographic
    verification through compressed private spans. Production requires that stronger
    property (web4#807). The full local ledger is verified independently in the next step.
  </div>
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
echo "  - an anonymous observer can inspect disclosed governance acts"
echo "  - private activity is compactly and exactly accounted by index spans"
echo "  - direct hash adjacency is verified where no private span intervenes"
echo "  - production hash proof through private spans remains ratchet item #807"
echo "  - the full local ledger independently verifies"
echo ""
echo "Artifacts:"
echo "  hub directory:     $CHAPTER"
echo "  daemon log:        $DEMO_ROOT/serve.log"
echo "  public decisions:  $DECISIONS_JSON"
echo "  browser timeline:  file://$DECISIONS_HTML"
