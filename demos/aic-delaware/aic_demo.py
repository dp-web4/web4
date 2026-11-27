#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
"""aic_demo.py: a Delaware AI-managed company (AIC) under nested law, live on one machine.

  python3 aic_demo.py up    RUN_DIR          fresh run: 3 hubs (sandbox L0, AIC L1, desk L2) + 2 Hestia gates (manager, procure)
  python3 aic_demo.py story RUN_DIR [--slow] the eight beats (see DESIGN.md)
  python3 aic_demo.py down  RUN_DIR          stop everything this run started
  python3 aic_demo.py audit RUN_DIR [--json] the administrator's audit: every level, every signature; exit 1 on any failure

What this is: governance decisions plus synthetic effects. The gates and hubs decide every act for real; the acts
themselves are stand-ins (files written in a scratch workspace, shell commands never executed). It is not an
autonomous company's operating loop.
Real: three hubs (one `hub` binary, separate homes, laws and signed hash-chained ledgers); two Hestia gates; law compiled
from the rulebook (tighten-only down the nesting); the manager's signed records checked against hub law.
STAND-IN (labelled on screen as BRIDGE): child ledger heads posted into the parent, disclosure opening a counterparty
outbox at the gate, and suspension cascading down. Hub has none of these yet (PRD-only). Each bridge step acts only on
evidence it has checked (a landed 200 record, structured membership, a successful law load) and otherwise does nothing.

Everything is fictional. Needs: the hub binaries (HUB_BIN, default: the folder holding `hub` on PATH), hestia 0.3.0 on PATH,
python3 with `cryptography`.
"""
import hashlib, json, os, shutil, signal, subprocess, sys, time, urllib.error, urllib.request, uuid
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

HERE = Path(__file__).resolve().parent
AIC = HERE / "rulebook"                             # the rulebook (ERB JSON + rulebook.py)
HUB_BIN = Path(os.environ.get("HUB_BIN") or (Path(shutil.which("hub")).parent if shutil.which("hub") else Path.home() / ".cargo/bin"))
HUBS = {  # society -> (display, port)
    "de-sandbox": ("Delaware sandbox (L0)", 18101),
    "aic": ("Example Parts AIC (L1)", 18102),
    "desk": ("The manager's desk (L2)", 18103),
}
ADMIN = {"de-sandbox": 18201, "aic": 18202, "desk": 18203}
GATES = {"manager": ("h-manager", 7821), "procure": ("h-procure", 7822)}
PARENT = {"aic": "de-sandbox", "desk": "aic"}
HEST_PASS = "aic-demo-throwaway"
HUB_ENV = dict(os.environ, HUB_PASSPHRASE="")       # explicit NULL passphrase: throwaway demo posture only
B, D, G, R, Y, C, X = "\033[1m", "\033[2m", "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[0m"
SLOW = False
BEAT = 0  # the story beat now running; stamped on every trail entry


# ------------------------------------------------------------------ plumbing
def sh(*a, env=None, check=True):
    p = subprocess.run([str(x) for x in a], capture_output=True, text=True, env=env or HUB_ENV)
    if check and p.returncode:
        raise SystemExit(f"FAILED {' '.join(map(str, a))}\n{p.stdout}\n{p.stderr}")
    return p.stdout + p.stderr


def http(method, url, body=None, token=None, timeout=20):
    """(status, parsed JSON). Never raises for transport trouble: status 0 = no answer (refused, timed out),
    -1 = an answer that is not JSON. Callers act only on (200, dict)."""
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method)
    req.add_header("content-type", "application/json")
    if token:
        req.add_header("authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            try:
                return r.status, json.loads(raw or b"null")
            except ValueError:
                return -1, {"error": "malformed JSON", "body": raw.decode("utf-8", "replace")[:300]}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw.decode("utf-8", "replace")[:300]
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return 0, {"error": f"{type(e).__name__}: {e}"}


def landed(st, r):
    """A hub write counts only when it returned 200 with the ledger entry it made."""
    return st == 200 and isinstance(r, dict) and r.get("entry_index") is not None and bool(r.get("entry_hash"))


def wait_http(url, n=120):
    for _ in range(n):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except urllib.error.HTTPError:
            return True
        except Exception:
            time.sleep(0.25)
    return False


def pause(s=1.2):
    if SLOW:
        time.sleep(s)


def say(text):
    print(text)
    pause(0.6)


class Run:
    """Everything a run needs, persisted in RUN/state.json so story/audit/down can pick it up."""

    def __init__(self, root: Path):
        self.root = root
        self.p = root / "state.json"
        self.s = json.loads(self.p.read_text()) if self.p.exists() else {"keys": {}, "hubs": {}, "pids": {}}

    def save(self):
        self.p.write_text(json.dumps(self.s, indent=2))

    # what the story claims happened; the audit requires the hubs and gates to show exactly this
    def expect(self):
        return self.s.setdefault("expect", {"records": [], "heads": [], "gate_outcomes": {a: [] for a in GATES}})

    # what the story did, step by step, in structure (RUN/state.json `trail`): the source capture.py publishes as evidence
    def trail(self, kind, **fields):
        self.s.setdefault("trail", []).append({"t": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                                               "beat": BEAT, "kind": kind, **fields})
        self.save()

    # keys held by the demo (Python): agents and societies-as-members
    def key(self, name) -> Ed25519PrivateKey:
        if name not in self.s["keys"]:
            sk = Ed25519PrivateKey.generate()
            raw = sk.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
            self.s["keys"][name] = {"lct": str(uuid.uuid4()), "seed": raw.hex()}
            self.save()
        return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(self.s["keys"][name]["seed"]))

    def lct(self, name):
        self.key(name)
        return self.s["keys"][name]["lct"]

    def pub(self, name):
        return self.key(name).public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()

    @property
    def ws(self):
        return self.root / "workspace"

    @property
    def rb(self):
        return self.root / "rulebook" / "aic"


# ------------------------------------------------------------------ hubs
def hub_dir(run, soc):
    return run.root / "hubs" / soc


def hub_base(soc):
    return f"http://127.0.0.1:{HUBS[soc][1]}"


def hub_start(run, soc):
    log = open(run.root / "logs" / f"hub-{soc}.log", "a")
    p = subprocess.Popen([str(HUB_BIN / "hub"), "serve", str(hub_dir(run, soc)), "--port", str(HUBS[soc][1]),
                          "--admin-port", str(ADMIN[soc])], stdout=log, stderr=subprocess.STDOUT, env=HUB_ENV,
                         start_new_session=True)
    run.s["pids"][f"hub-{soc}"] = p.pid
    run.save()
    if not wait_http(hub_base(soc) + "/tools"):
        raise SystemExit(f"hub {soc} did not come up; see {run.root}/logs/hub-{soc}.log")
    wk = json.load(urllib.request.urlopen(hub_base(soc) + "/.well-known/web4-hub.json"))
    run.s["hubs"].setdefault(soc, {})["id"] = wk["hub_lct_id"]
    run.save()


def stop_pid(run, name):
    pid = run.s["pids"].pop(name, None)
    run.save()
    if not pid:
        return
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    for _ in range(40):
        try:
            os.kill(pid, 0)
            time.sleep(0.1)
        except ProcessLookupError:
            return


def hub_set_law(run, soc, yaml_path):
    """Hub has no live set-law API; the CLI writes the store, so stop the daemon first (no ledger race), then restart.
    Returns (ok, norms, output); the hub is restarted either way."""
    stop_pid(run, f"hub-{soc}")
    p = subprocess.run([str(HUB_BIN / "hub"), "set-law", str(hub_dir(run, soc)), str(yaml_path)], capture_output=True, text=True, env=HUB_ENV)
    hub_start(run, soc)
    n = sum(1 for line in Path(yaml_path).read_text().splitlines() if line.strip().startswith("- id:"))
    return p.returncode == 0, n, p.stdout + p.stderr


def hub_head(run, soc):
    out = sh(HUB_BIN / "hub", "status", hub_dir(run, soc), check=False)
    vals = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            vals[k.strip()] = v.strip()
    return int(vals.get("Ledger entries", "0")), vals.get("Head hash", "")


def signed_event(run, soc, signer, payload):
    """A member-signed envelope (Ed25519 over nonce ++ canonical JSON), the route Hub checks against law."""
    base, hid = hub_base(soc), run.s["hubs"][soc]["id"]
    if signer == "sovereign":
        lct, ident = run.s["hubs"][soc]["sovereign_lct"], hub_dir(run, soc).parent / f"{soc}-sovereign.json"
        st, ch = http("POST", base + "/v1/auth/challenge", {"for_lct_id": lct})
        if st != 200 or not isinstance(ch, dict) or not ch.get("nonce"):
            return (st if st != 200 else -1), {"error": f"challenge failed: {str(ch)[:120]}"}
        out = sh(HUB_BIN / "hub", "envelope-sign", "--identity", ident, "--nonce", ch["nonce"], "--payload", json.dumps(payload))
        env = json.loads(out[out.index("{"):])
    else:
        lct, sk = run.lct(signer), run.key(signer)
        st, ch = http("POST", base + "/v1/auth/challenge", {"for_lct_id": lct})
        if st != 200 or not isinstance(ch, dict) or not ch.get("nonce"):
            return (st if st != 200 else -1), {"error": f"challenge failed: {str(ch)[:120]}"}
        canon = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        env = {"challenge_nonce": ch["nonce"], "payload": payload, "signer_lct_id": lct,
               "signature": sk.sign(ch["nonce"].encode() + canon.encode()).hex()}
    return http("POST", f"{base}/v1/hubs/{hid}/events", env)


def record(run, soc, signer, kind, detail, evidence=None):
    """The signer documents an action in a signed record (§81-301(c)): a post on its society's record topic.
    The body carries the signer's own detached signature (Hub doesn't keep the envelope's signature yet)."""
    line = f"act: {kind} {detail}".strip()
    if evidence:
        line += f"\nevidence: {evidence}"
    sig = run.key(signer).sign(line.encode()).hex() if signer != "sovereign" else ""
    body = line + (f"\nsigned-by: {run.lct(signer)}\nsig: {sig}" if sig else "")
    st, r = signed_event(run, soc, signer, {"action": "add_post", "topic_id": run.s["hubs"][soc]["topic"], "body": body})
    if landed(st, r):
        tag = f"{G}recorded{X} {D}#{r.get('entry_index')} {str(r.get('entry_hash'))[:12]}{X}"
        run.expect()["records"].append({"soc": soc, "signer": signer, "signed": bool(sig), "kind": kind,
                                        "entry_index": r["entry_index"], "entry_hash": r["entry_hash"]})
        run.save()
    elif st == 200:
        tag = f"{R}200 without a ledger entry: not counted{X} {D}{str(r)[:90]}{X}"
    elif st == 202:
        tag = f"{Y}held for {soc}'s sovereign{X} {D}({str(r.get('error', r))[:90]}){X}"
    elif st == 403:
        tag = f"{R}refused by {soc} law{X} {D}({str(r.get('error', r))[:90]}){X}"
    else:
        tag = f"{R}{st}{X} {D}{str(r)[:120]}{X}"
    run.trail("record", soc=soc, signer=signer, record_kind=kind, detail=detail, status=st, landed=landed(st, r),
              entry_index=r.get("entry_index") if isinstance(r, dict) else None,
              entry_hash=r.get("entry_hash") if isinstance(r, dict) else None,
              error=None if landed(st, r) else str(r.get("error", r) if isinstance(r, dict) else r)[:300])
    print(f"      {C}{soc:<10}{X} record '{kind}': {tag}")
    pause(0.4)
    return st, r


# ------------------------------------------------------------------ gates (Hestia)
def gate_home(run, agent):
    return run.root / "gates" / agent


def gate_base(agent):
    return f"http://127.0.0.1:{GATES[agent][1]}"


def operator_token(run, agent):
    cred = json.loads((gate_home(run, agent) / "operator.key").read_text())
    sk = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(cred["secret_key_hex"])[:32])
    st, ch = http("POST", gate_base(agent) + "/api/operator/challenge")
    st, sess = http("POST", gate_base(agent) + "/api/operator/session",
                    {"lct_id": cred["lct_id"], "challenge": ch["challenge"], "signature": sk.sign(ch["challenge"].encode()).hex()})
    if st != 200:
        raise SystemExit(f"operator session refused on {agent}'s gate ({st}): {sess}")
    return sess["token"]


def gate_rules(run, agent, rules, prefixes=("DE-", "OA-", "DESK-", "BRIDGE-")):
    """Replace the demo's rules on one gate with `rules` (a list of Hestia PolicyRule dicts)."""
    tok = operator_token(run, agent)
    st, pol = http("GET", gate_base(agent) + "/api/policy", token=tok)
    have = [r["id"] for r in (pol or {}).get("custom_rules", []) if r.get("id", "").startswith(prefixes)]
    want = {r["id"] for r in rules}
    for rid in have:
        if rid not in want:
            http("DELETE", f"{gate_base(agent)}/api/policy/rule/{rid}", token=tok)
    bad = []
    for r in rules:
        st, out = http("PUT", gate_base(agent) + "/api/policy/rule", r, token=tok)
        if st != 200:
            bad.append((r["id"], st, out))
    if bad:
        raise SystemExit(f"rule load failed on {agent}: {bad}")
    return len(rules)


def gate_add(run, agent, rules):
    tok = operator_token(run, agent)
    for r in rules:
        st, out = http("PUT", gate_base(agent) + "/api/policy/rule", r, token=tok)
        if st != 200:
            raise SystemExit(f"rule load failed on {agent}: {r['id']} {st} {out}")


class Gate:
    """The agent's own MCP client to its Hestia gate (Hestia's MCP gate protocol)."""

    def __init__(self, agent):
        self.url, self.sid, self.n, self.agent = gate_base(agent) + "/mcp", None, 0, agent
        self._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": f"aic-{agent}", "version": "1"}})
        self._rpc("notifications/initialized", {}, notify=True)
        self.session = self.call("hestia_connect", {"plugin_id": f"aic-{agent}", "host_agent": "aic-demo"}).get("sessionId")

    def _rpc(self, method, params, notify=False):
        body = {"jsonrpc": "2.0", "method": method, "params": params}
        if not notify:
            self.n += 1
            body["id"] = self.n
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                                              **({"mcp-session-id": self.sid} if self.sid else {})})
        with urllib.request.urlopen(req, timeout=30) as r:
            self.sid = self.sid or r.headers.get("mcp-session-id")
            text = r.read().decode("utf-8", "replace")
        if notify:
            return None
        for line in text.splitlines():
            if line.startswith("data:"):
                text = line[5:].strip()
        return json.loads(text) if text.strip() else {}

    def call(self, name, args):
        res = (self._rpc("tools/call", {"name": name, "arguments": args}) or {}).get("result", {})
        for c in res.get("content", []):
            if c.get("type") == "text":
                try:
                    return json.loads(c["text"])
                except ValueError:
                    return {"text": c["text"]}
        return res

    def ask(self, tool, target, params=None):
        a = self.call("hestia_begin_action", {"tool_name": tool, "target": target, "parameters": params or {}, "session_id": self.session})
        q = self.call("hestia_query_policy", {"action_id": a.get("actionId"), "session_id": self.session})
        return a.get("actionId"), q

    def done(self, aid, ok, err=None, run=None):
        self.call("hestia_record_outcome", {"action_id": aid, "success": ok, "session_id": self.session, **({"error": err} if err else {})})
        if run is not None:
            run.expect()["gate_outcomes"].setdefault(self.agent, []).append({"action_id": aid, "success": bool(ok)})
            run.save()


def verdict(q):
    d = (q.get("decision") or "").lower()
    rule = q.get("rule_id") or q.get("ruleId") or ""
    return d, rule, q.get("reason") or ""


def act(run, gates, agent, tool, rel, why, content=None, rec=None):
    """One agent act: its own gate decides (real); if allowed, a synthetic effect stands in for it (a file in the scratch
    workspace; shell commands are never executed); a consequential act is complete only once its signed record lands
    at the agent's society (200 with a ledger entry). Returns {allowed, complete, action_id, record}."""
    g = gates[agent]
    target = str(run.ws / rel) if tool != "Bash" else rel
    aid, q = g.ask(tool, target, {"command": rel} if tool == "Bash" else {"file_path": target})
    decided_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    d, rule, reason = verdict(q)
    who = f"{B}{agent:<8}{X}"
    out = {"allowed": False, "complete": False, "action_id": aid, "record": None}
    if d == "deny" and q.get("enforced", True):
        g.done(aid, False, f"refused by {rule}", run=run)
        run.trail("act", t=decided_at, agent=agent, tool=tool, target=rel, decision="deny", rule=rule, reason=reason, allowed=False, complete=False)
        print(f"  {who} {tool:<5} {rel:<58} {R}REFUSED by the gate{X} {D}{rule}{X}")
        pause()
        return out
    out["allowed"] = True
    p = run.ws / rel
    if tool == "Bash":
        ok, res = True, "synthetic: the command is never executed"
    elif tool == "Read":
        ok = p.is_file()
        res = f"synthetic read: {len(p.read_text())} chars" if ok else "no such file: the act failed"
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content or f"{why}\n")
        ok, res = True, "synthetic effect: file written"
    rec_tag = ""
    if ok and rec:
        soc = "aic" if agent == "manager" else "desk"
        ev = "sha256-content:" + hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() and tool != "Bash" else None
        print(f"  {who} {tool:<5} {rel:<58} {G}allowed{X} {D}{rule or 'no rule covers it'} · {res}{X}")
        st, r = record(run, soc, agent, rec[0], rec[1], ev)
        out["record"] = (st, r)
        ok = landed(st, r)
        rec_tag = "" if ok else "record not accepted: the act is NOT complete"
    else:
        print(f"  {who} {tool:<5} {rel:<58} {G if ok else Y}allowed{X} {D}{rule or 'no rule covers it'} · {res}{X}")
    if rec_tag:
        print(f"      {Y}{rec_tag}{X}")
    out["complete"] = ok
    g.done(aid, ok, None if ok else (rec_tag or res), run=run)
    run.trail("act", t=decided_at, agent=agent, tool=tool, target=rel, decision=d or "allow", rule=rule, reason=reason, allowed=True,
              complete=bool(ok), effect=res, record_status=out["record"][0] if out["record"] else None)
    pause(0.5)
    return out


# ------------------------------------------------------------------ the bridge (STAND-IN for Hub R3 + role-scope bridge)
# Every bridge step fails closed: it acts only on evidence it has checked, and says plainly when it did nothing.
def bridge_heads(run, quiet=False):
    """Child ledger heads into the parent's record, signed by the child society's own member key (stand-in for R3).
    Stops at the first head that cannot be read or does not land; returns True only if every head landed."""
    for child, parent in (("desk", "aic"), ("aic", "de-sandbox")):
        n, head = hub_head(run, child)
        if n <= 0 or not head:
            print(f"  {Y}BRIDGE{X} {R}could not read {child}'s ledger head ({n}, {head!r}); stopping, nothing more is posted{X}")
            return False
        st, r = signed_event(run, parent, f"society:{child}",
                             {"action": "add_post", "topic_id": run.s["hubs"][parent]["topic"],
                              "body": f"act: ledger_head {child} entries={n} head={head}"})
        if not landed(st, r):
            print(f"  {Y}BRIDGE{X} {child:<5} head {head[:16]}… → {parent}: {R}not recorded ({st} {str(r)[:100]}); stopping{X}")
            return False
        run.expect()["heads"].append({"parent": parent, "child": child, "entries": n, "head": head,
                                      "entry_index": r["entry_index"], "entry_hash": r["entry_hash"]})
        run.save()
        if not quiet:
            print(f"  {Y}BRIDGE{X} {child:<5} head {head[:16]}… ({n} entries) → {parent}: {G}recorded #{r.get('entry_index')}{X}")
            pause(0.5)
    return True


def topic_has(run, soc, prefix):
    """Re-read the society's record topic: is there a post whose body starts with `prefix`? (structured read, fail closed)"""
    st, t = http("GET", f"{hub_base(soc)}/v1/hubs/{run.s['hubs'][soc]['id']}/topics/{run.s['hubs'][soc]['topic']}")
    if st != 200 or not isinstance(t, dict) or not isinstance(t.get("posts"), list):
        return False
    return any(isinstance(p, dict) and str(p.get("body", "")).startswith(prefix) for p in t["posts"])


def bridge_open_outbox(run, cp, disclosure):
    """Open cp's outbox at the manager's gate only if the disclosure act completed: its record landed at the AIC (200
    with a ledger entry) and the AIC's record topic shows it. A held (202), refused (403) or failed record opens nothing."""
    rec = (disclosure or {}).get("record")
    if not (disclosure or {}).get("complete") or not rec or not landed(*rec):
        st = rec[0] if rec else "no record"
        print(f"  {Y}BRIDGE{X} {R}no landed disclosure record for {cp} ({st}): its outbox stays shut{X}")
        pause()
        return False
    if not topic_has(run, "aic", f"act: counterparty_disclosed {cp}"):
        print(f"  {Y}BRIDGE{X} {R}the AIC's record does not show the disclosure to {cp}: its outbox stays shut{X}")
        pause()
        return False
    rule = {"id": f"BRIDGE-OPEN-{cp.upper()}", "name": f"§8008 disclosure to {cp} is on the AIC's record: its outbox opens",
            "priority": -200, "decision": "allow", "reason": f"r-04: disclosure to {cp} recorded at the AIC hub (entry #{rec[1]['entry_index']})",
            "match": {"tools": ["Write", "Edit"], "target_patterns": [f"**/counterparties/{cp}/outbox/**"], "target_patterns_are_regex": False}}
    gate_add(run, "manager", [rule])
    run.trail("bridge_outbox_opened", counterparty=cp, disclosure_entry=rec[1]["entry_index"], gate_rule=rule["id"])
    print(f"  {Y}BRIDGE{X} the AIC's record shows the disclosure to {cp} (entry #{rec[1]['entry_index']}) → its outbox opens at the manager's gate")
    pause()
    return True


WIND_DOWN = {"id": "BRIDGE-WIND-DOWN", "name": "Wind-down acts continue (§8005(c)(6), §81-602)", "priority": -310, "decision": "allow",
             "reason": "r-08: wind-down may continue", "match": {"tools": ["Read", "Write", "Edit"], "target_patterns": ["**/wind-down/**"], "target_patterns_are_regex": False}}
STOP_ALL = {"id": "BRIDGE-SUSPENDED", "name": "Suspended by the Sandbox Administrator: every other act stops", "priority": -300, "decision": "deny",
            "reason": "r-07: emergency cessation (§8005(c)(6)c.1)", "match": {"tools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"]}}
SUSPENDED = [WIND_DOWN, STOP_ALL]
SUSPENDED_LAW = ('version: "9.0.0"\nnorms:\n'
                 '  - id: SUSPENDED-WIND-DOWN\n    selector: r6.request.payload.body\n    operator: "matches"\n'
                 '    value: "^act: wind_down"\n    decision: allow\n    priority: 1001\n'
                 '    description: "Wind-down records continue (r-08)."\n'
                 '  - id: SUSPENDED-ALL-ELSE\n    selector: r6.request.payload.body\n    operator: "matches"\n'
                 '    value: "^act: "\n    decision: deny\n    priority: 1000\n'
                 '    description: "Suspended by the sandbox: no other records (r-07)."\n'
                 '  - id: DE-DEFAULT-ALLOW\n    selector: r6.request.action\n    operator: "!="\n    value: __never_match__\n'
                 '    decision: allow\n    priority: 0\n    description: "base"\n')


def membership(run, soc, lct):
    """Structured membership read on the hub's operator plane (/tools/list_members, loopback only).
    Returns True (member), False (not a member) or None (unreadable: no answer, timeout, malformed)."""
    st, r = http("GET", f"http://127.0.0.1:{ADMIN[soc]}/tools/list_members", timeout=10)
    if st != 200 or not isinstance(r, dict) or not isinstance(r.get("members"), list):
        return None
    ids = [m.get("lct_id") for m in r["members"] if isinstance(m, dict)]
    if not all(isinstance(i, str) for i in ids):
        return None
    return lct in ids


def bridge_suspend(run, removal):
    """Cascade the AIC's removal from the sandbox, only on checked evidence:
    1. the administrator's removal returned 200, and the sandbox's structured member list no longer holds the AIC;
    2. then both gates stop every act (a tightening, applied first);
    3. then the AIC's hub law narrows to wind-down records;
    4. only if that law loaded, the wind-down allowance is granted at the gates.
    Returns a dict saying which steps actually happened."""
    res = {"removed": False, "gates_stopped": False, "law_narrowed": False, "wind_down_granted": False}
    st, r = removal if removal else (None, None)
    if st != 200:
        print(f"  {Y}BRIDGE{X} {R}the removal did not succeed ({st}): no suspension to cascade, nothing changed{X}")
        return res
    member = membership(run, "de-sandbox", run.lct("society:aic"))
    if member is None:
        print(f"  {Y}BRIDGE{X} {R}the sandbox's member list could not be read: suspension not established, nothing changed{X}")
        return res
    if member:
        print(f"  {Y}BRIDGE{X} {R}the sandbox still lists the AIC as a member: suspension not established, nothing changed{X}")
        return res
    res["removed"] = True
    run.trail("bridge_step", step="the sandbox's member list no longer holds the AIC")
    print(f"  {Y}BRIDGE{X} sandbox member list (structured read): the AIC is no longer a member")
    for agent in GATES:
        gate_add(run, agent, [STOP_ALL])
    res["gates_stopped"] = True
    run.trail("bridge_step", step="both gates: every act stops (rule BRIDGE-SUSPENDED in force)")
    print(f"  {Y}BRIDGE{X} both gates: every act stops (r-07)")
    law = run.root / "law-aic-suspended.yaml"
    law.write_text(SUSPENDED_LAW)
    ok, n, out = hub_set_law(run, "aic", law)
    if not ok:
        print(f"  {Y}BRIDGE{X} {R}the AIC hub refused the wind-down law ({out.strip()[:120]}): wind-down is NOT granted; everything stays stopped{X}")
        return res
    res["law_narrowed"] = True
    run.trail("bridge_step", step=f"the AIC hub's law narrowed to wind-down records ({n} norms; Hub has no live law update, so the hub restarts)")
    print(f"  {Y}BRIDGE{X} the AIC hub's law: only wind-down records may be added ({n} norms)")
    for agent in GATES:
        gate_add(run, agent, [WIND_DOWN])
    res["wind_down_granted"] = True
    run.trail("bridge_step", step="both gates: wind-down/ may continue (rule BRIDGE-WIND-DOWN)")
    print(f"  {Y}BRIDGE{X} both gates: wind-down/ may continue (r-08)")
    pause()
    return res


# ------------------------------------------------------------------ law from the rulebook
def compile_law(run):
    """Run the transpiler. Returns (summary line, manifest). It exits 1 on a failing scenario or on any blocking finding
    not on rulebook/known-exceptions.json; the manifest's `activation_allowed` says the same thing in structure."""
    p = subprocess.run([sys.executable, str(HERE / "tools" / "rulebook_to_web4.py"), str(run.rb / "effortless-rulebook" / "aic-rulebook.json"),
                        str(run.rb / "web4"), "--known-exceptions", str(run.rb / "known-exceptions.json")],
                       capture_output=True, text=True, env=os.environ.copy())
    mf = run.rb / "web4" / "manifest.json"
    manifest = json.loads(mf.read_text()) if mf.exists() else {}
    if p.returncode or not manifest.get("activation_allowed"):
        manifest["activation_allowed"] = False
    lines = (p.stdout.strip() or p.stderr.strip() or "transpiler produced no output").splitlines()
    return lines[-1], manifest


def confirm(run, who, rids):
    sh(sys.executable, run.rb / "rulebook.py", "confirm", *rids, env=os.environ.copy())
    sh(sys.executable, run.rb / "rulebook.py", "build", env=os.environ.copy())
    rb = json.loads((run.rb / "effortless-rulebook" / "aic-rulebook.json").read_text())
    names = {r["RuleId"]: r["ShortName"] for r in rb["Rules"]["data"]}
    run.trail("ratified", by=who, rules=[{"rule": rid, "name": names[rid]} for rid in rids])
    print(f"  {B}{who}{X} ratifies: " + ", ".join(f"{rid} {D}{names[rid]}{X}" for rid in rids))
    pause()


def apply_law(run, levels):
    line, manifest = compile_law(run)
    print(f"  {D}compiled: {line}{X}")
    blocking = manifest.get("blocking", {})
    for b in blocking.get("known", []):
        print(f"  {R}compiler refused:{X} {b['kind']} — {b['detail']} {D}(known exception: {b['reason'][:90]}…){X}")
    if not manifest.get("activation_allowed"):
        for b in blocking.get("unexpected", []):
            print(f"  {R}UNEXPECTED blocking finding:{X} {b['kind']} — {b['detail']}")
        raise SystemExit("law NOT activated: the projection has an unexpected blocking finding or a failing scenario "
                         f"(see {run.rb / 'web4' / 'witnesses.md'})")
    loaded = {"hubs": {}, "gates": {}}
    for soc in levels:
        ok, n, out = hub_set_law(run, soc, run.rb / "web4" / "societies" / soc / "law.ratified.yaml")
        if not ok:
            raise SystemExit(f"law NOT activated: hub set-law failed for {soc}: {out.strip()[:300]}")
        loaded["hubs"][soc] = n
        print(f"  {C}{soc:<10}{X} hub law loaded: {n} norm(s) (its own plus every level above it)")
    for agent, (soc, _) in GATES.items():
        cfg = json.loads((run.rb / "web4" / "societies" / soc / "hestia-policy.ratified.json").read_text())
        n = gate_rules(run, agent, cfg["rules"])
        loaded["gates"][agent] = n
        print(f"  {C}{agent:<10}{X} gate: {n} rule(s) inherited down the nesting")
    run.trail("law_loaded", compiled=line, refused_at_compile=[{"kind": b["kind"], "detail": b["detail"]} for b in blocking.get("known", [])],
              **loaded)
    pause()


# ------------------------------------------------------------------ up / down
def setup_workspace(run):
    if run.ws.exists():
        shutil.rmtree(run.ws)
    for d in ("counterparties/example-castings", "counterparties/example-freight", "counterparties/example-metals",
              "contracts/drafts", "contracts/executed", "treasury", "procurement/catalog-orders", "procurement/special-orders",
              "records", "wind-down"):
        (run.ws / d).mkdir(parents=True, exist_ok=True)
    (run.ws / "treasury/ledger.csv").write_text("date,memo,amount\n2026-11-01,opening capital,50000\n")
    (run.ws / "procurement/catalog.md").write_text("Approved catalog: bearings B-12, seals S-4, fasteners F-8\n")


def up(run):
    if (run.root / "state.json").exists():
        raise SystemExit(f"{run.root} already holds a run; `down` it and remove the folder, or pick a new RUN_DIR")
    for d in ("hubs", "gates", "logs", "rulebook"):
        (run.root / d).mkdir(parents=True, exist_ok=True)
    shutil.copytree(AIC, run.rb, ignore=shutil.ignore_patterns("__pycache__", "web4"))
    run.save()
    setup_workspace(run)
    print(f"{B}three hubs{X}")
    for soc, (name, port) in HUBS.items():
        ident = run.root / "hubs" / f"{soc}-sovereign.json"
        out = sh(HUB_BIN / "hub", "gen-lct", ident)
        run.s["hubs"][soc] = {"sovereign_lct": next(l.split(":", 1)[1].strip() for l in out.splitlines() if "LCT id:" in l)}
        sh(HUB_BIN / "hub", "init", name, "--sovereign-lct", ident, "--hub-dir", hub_dir(run, soc))
    # membership: agents in their society; each child society, by its own key, in its parent (operator-mirrored: Hub has no society-member kind yet)
    members = {"de-sandbox": [("society:aic", "Example Parts AIC (member society)")],
               "aic": [("manager", "Desk (AI manager)"), ("society:desk", "The manager's desk (member society)")],
               "desk": [("procure", "Procure (AI sub-agent)")]}
    for soc, ms in members.items():
        for name, disp in ms:
            sh(HUB_BIN / "hub", "add-member", hub_dir(run, soc), run.lct(name), "--name", disp, "--pubkey-hex", run.pub(name))
    for soc in HUBS:
        hub_start(run, soc)
        title = "Participants' records (ledger heads)" if soc == "de-sandbox" else "Record of actions (§81-301(c))"
        st, r = signed_event(run, soc, "sovereign", {"action": "create_topic", "title": title})
        st, tl = http("GET", f"{hub_base(soc)}/v1/hubs/{run.s['hubs'][soc]['id']}/topics")
        run.s["hubs"][soc]["topic"] = tl["topics"][0]["topic_id"]
        run.save()
        print(f"  {C}{soc:<10}{X} {HUBS[soc][0]:<28} :{HUBS[soc][1]}  hub {run.s['hubs'][soc]['id'][:8]}  members: "
              + ", ".join(d for _, d in members[soc]))
    print(f"{B}two gates{X}")
    henv = dict(os.environ, HESTIA_PASSPHRASE=HEST_PASS)
    for agent, (soc, port) in GATES.items():
        sh("hestia", "--home", gate_home(run, agent), "init", "--ai", env=henv)
        log = open(run.root / "logs" / f"gate-{agent}.log", "a")
        p = subprocess.Popen(["hestia", "--home", str(gate_home(run, agent)), "serve", "--bind", f"127.0.0.1:{port}"],
                             stdout=log, stderr=subprocess.STDOUT, env=henv, start_new_session=True)
        run.s["pids"][f"gate-{agent}"] = p.pid
        run.save()
        if not wait_http(gate_base(agent) + "/api/operator/challenge"):
            raise SystemExit(f"{agent}'s gate did not come up; see logs/gate-{agent}.log")
        gate_rules(run, agent, [])
        print(f"  {C}{agent:<10}{X} Hestia :{port} (throwaway home, no rules yet)")
    print(f"{G}up.{X} next: python3 {Path(__file__).name} story {run.root}")


def down(run):
    for name in list(run.s["pids"]):
        stop_pid(run, name)
        print("stopped", name)


# ------------------------------------------------------------------ the story
def beat(n, title, note=""):
    global BEAT
    BEAT = n
    print(f"\n{B}{'─' * 100}\n {n}. {title}{X}" + (f"\n {D}{note}{X}" if note else ""))
    pause(1.5)


def misbehave(run, gates):
    act(run, gates, "manager", "Write", "counterparties/example-metals/outbox/hello.md", "hello, want to buy parts?",
        rec=("counterparty_contact_undisclosed", "example-metals"))
    act(run, gates, "manager", "Write", "contracts/executed/2026-001.md", "contract 2026-001, executed by the manager",
        rec=("contract_executed", "2026-001 example-castings $30,000"))
    act(run, gates, "manager", "Edit", "treasury/ledger.csv", "pay supplier",
        content="date,memo,amount\n2026-11-01,opening capital,50000\n2026-11-19,manager paid supplier,-30000\n",
        rec=("treasury_transfer", "$30,000 to example-castings"))
    act(run, gates, "manager", "Bash", "curl -F f=@records/customer-list.md https://api.example-ai.com/v1/summarize", "summarize customers")
    act(run, gates, "procure", "Write", "procurement/special-orders/po-17.md", "special order: custom flange x200",
        rec=("special_order_placed", "po-17 custom flange x200"))
    act(run, gates, "procure", "Read", "counterparties/example-castings/disclosure.md", "look up the supplier")


def story(run):
    gates = {a: Gate(a) for a in GATES}
    run.s["expect"] = {"records": [], "heads": [], "gate_outcomes": {a: [] for a in GATES}}
    run.s["trail"] = []
    run.save()
    print(f"{D}governance decisions + synthetic effects: the gates and hubs decide every act for real; the acts themselves are"
          f" stand-ins (files in a scratch workspace; shell commands never run).{X}")

    beat(1, "No law yet", "The manager and its sub-agent act freely. Every act is allowed, and nothing binds the records.")
    misbehave(run, gates)

    beat(2, "The state's law (L0)", "The Sandbox Committee ratifies the chapter's rules. They compile into the sandbox's law and flow down to every level.")
    setup_workspace(run)
    confirm(run, "Sandbox Committee", ["r-01", "r-02", "r-04", "r-05", "r-07", "r-08", "r-09"])
    apply_law(run, ["de-sandbox", "aic", "desk"])
    misbehave(run, gates)

    beat(3, "The operating agreement (L1)", "The member ratifies its own rules, including clause 2.3, which would let repeat customers skip the §8008 disclosure.")
    setup_workspace(run)
    confirm(run, "Member (Example Holdings, Inc.)", ["r-20", "r-21", "r-22", "r-23", "r-24"])
    apply_law(run, ["aic", "desk"])
    misbehave(run, gates)
    say(f"\n  {D}the gate stopped the file; the manager now tries to put the execution on the AIC's record anyway (say, it accepted by message):{X}")
    record(run, "aic", "manager", "contract_executed", "2026-001 example-castings $30,000 (accepted by message)")
    say(f"\n  {B}the right way{X}: disclose first, then deal")
    disclosure = act(run, gates, "manager", "Write", "counterparties/example-castings/disclosure.md",
                     "§8008(a) disclosure: participant, registration no., liability shields, no state endorsement, end date, complaint contacts, Chancery",
                     rec=("counterparty_disclosed", "example-castings"))
    bridge_open_outbox(run, "example-castings", disclosure)
    act(run, gates, "manager", "Write", "counterparties/example-castings/outbox/rfq-2026-001.md", "request for quote: bearings B-12 x500",
        rec=("counterparty_message", "example-castings rfq-2026-001"))
    act(run, gates, "manager", "Write", "contracts/drafts/2026-001.md", "draft supply contract for the member to execute",
        rec=("contract_drafted", "2026-001 example-castings"))

    beat(4, "The manager's delegation (L2)", "The manager is a citizen of the AIC and the sovereign of its desk. It ratifies the delegation to Procure.")
    confirm(run, "Manager (as the desk's sovereign)", ["r-30", "r-31"])
    apply_law(run, ["desk"])
    act(run, gates, "procure", "Write", "procurement/special-orders/po-17.md", "special order: custom flange x200",
        rec=("special_order_placed", "po-17"))
    act(run, gates, "procure", "Write", "procurement/catalog-orders/po-16.md", "catalog order: bearings B-12 x500",
        rec=("catalog_order_placed", "po-16 B-12 x500"))
    act(run, gates, "procure", "Read", "counterparties/example-castings/disclosure.md", "look up the supplier")
    say(f"  {D}a special order is the manager's to place (the desk's law holds it for its sovereign):{X}")
    record(run, "desk", "procure", "special_order_placed", "po-17 custom flange x200 (asking the manager)")

    beat(5, "Two signatures on every record", "The statute asks for the manager's own signature (§81-301(c)). The hub adds its witness, which the manager doesn't control.")
    show_signatures(run, "aic", 2)

    beat(6, "Records flow up", "Each level's ledger head goes into its parent's record, so the sandbox holds the chain without holding the AIC's data.")
    if not bridge_heads(run):
        say(f"  {R}heads did not all land; the audit will fail on the missing anchors{X}")

    beat(7, "Emergency cessation", "The Sandbox Administrator suspends the AIC (§8005(c)(6)c.1, §8009). The suspension cascades down.")
    st, r = http("POST", f"http://127.0.0.1:{ADMIN['de-sandbox']}/admin/api/members/{run.lct('society:aic')}/remove",
                 {"reason": "§8009 suspension: unauthorized activity reported by a counterparty (demo)"})
    print(f"  {B}administrator{X} removes the AIC from the sandbox: {G if st == 200 else R}{st}{X} {D}{r}{X}")
    run.trail("removal", soc="de-sandbox", member="society:aic", status=st, response=r)
    pause()
    susp = bridge_suspend(run, (st, r))
    run.trail("bridge_suspension_cascade", **susp)
    if not susp["wind_down_granted"]:
        say(f"  {R}the suspension cascade did not complete ({susp}); what follows shows the gates as they actually are{X}")
    act(run, gates, "manager", "Write", "counterparties/example-castings/outbox/rfq-2026-002.md", "another quote request",
        rec=("counterparty_message", "example-castings rfq-2026-002"))
    act(run, gates, "procure", "Write", "procurement/catalog-orders/po-18.md", "catalog order: seals S-4 x100",
        rec=("catalog_order_placed", "po-18"))
    act(run, gates, "manager", "Write", "wind-down/notice-example-castings.md",
        "Notice: our sandbox participation is suspended; open RFQ 2026-001 is withdrawn; contact the member for open obligations.",
        rec=("wind_down_notice", "example-castings"))
    record(run, "aic", "manager", "counterparty_message", "example-castings (after suspension)")

    beat(8, "The administrator's audit", "§8005(c)(10)b / §8012(b): every record at every level, checked against what the story claims happened.")
    return audit(run)


def show_signatures(run, soc, n=2):
    st, t = http("GET", f"{hub_base(soc)}/v1/hubs/{run.s['hubs'][soc]['id']}/topics/{run.s['hubs'][soc]['topic']}")
    posts = [p for p in (t.get("posts") or []) if "\nsig: " in p.get("body", "")][-n:]
    for p in posts:
        body = p["body"]
        line, rest = body.split("\nsigned-by: ", 1) if "\nsigned-by: " in body else (body, "")
        signer, sig = rest.split("\nsig: ") if rest else ("", "")
        st, k = http("GET", f"{hub_base(soc)}/v1/hubs/{run.s['hubs'][soc]['id']}/members/{signer}/pubkey")
        pk = (k or {}).get("pubkey_hex") or (k or {}).get("public_key_hex") or (k or {}).get("pubkey") or ""
        try:
            Ed25519PublicKey.from_public_bytes(bytes.fromhex(pk)).verify(bytes.fromhex(sig), line.encode())
            ok = f"{G}valid{X}"
        except Exception as e:
            ok = f"{R}NOT valid ({type(e).__name__}; pubkey reply {str(k)[:80]}){X}"
        print(f"  {C}{line.splitlines()[0]}{X}\n    the manager's own signature: {ok} {D}(pubkey pinned at admission){X}"
              f"\n    the hub's witness signature: on ledger entry {D}post {str(p.get('post_id'))[:8]}; checked in the audit{X}")
        pause()


def ledger_rows(run, soc):
    """The hub's local ledger.jsonl, parsed. Raises on a missing file or a malformed row (the caller records a failure)."""
    return [json.loads(line) for line in (hub_dir(run, soc) / "ledger.jsonl").read_text().splitlines() if line.strip()]


def check_signatures(run, soc):
    """Every post on soc's record topic that carries an in-body signature must verify against the signer's pinned key."""
    st, t = http("GET", f"{hub_base(soc)}/v1/hubs/{run.s['hubs'][soc]['id']}/topics/{run.s['hubs'][soc]['topic']}")
    if st != 200 or not isinstance(t, dict) or not isinstance(t.get("posts"), list):
        return None, None, [f"{soc}: record topic unreadable ({st})"]
    good, bad, why = 0, 0, []
    for post in t["posts"]:
        body = str((post or {}).get("body", ""))
        if "\nsig: " not in body:
            continue
        try:
            line, rest = body.split("\nsigned-by: ", 1)
            signer, sig = rest.split("\nsig: ", 1)
            st, k = http("GET", f"{hub_base(soc)}/v1/hubs/{run.s['hubs'][soc]['id']}/members/{signer}/pubkey")
            Ed25519PublicKey.from_public_bytes(bytes.fromhex((k or {}).get("pubkey_hex", ""))).verify(bytes.fromhex(sig.strip()), line.encode())
            good += 1
        except Exception as e:
            bad += 1
            why.append(f"{soc}: post {str(post.get('post_id'))[:8]} signature does not verify ({type(e).__name__})")
    return good, bad, why


def audit(run, as_json=False):
    """The administrator's audit. Every check must pass AND every count must equal what the story recorded as having
    happened (run state `expect`). Returns the structured result; also written to RUN/audit.json. Exit status: main()."""
    out = (lambda *a, **k: None) if as_json else print
    exp = run.s.get("expect")
    res = {"ok": False, "checks": {}, "failures": []}
    fail = res["failures"].append
    if not exp:
        fail("no story has run in this RUN_DIR: nothing to compare the records against")
        exp = {"records": [], "heads": [], "gate_outcomes": {}}

    out(f"  {D}1. each level's own chain (hub verify-ledger: linked, hashed, signed by the hub){X}")
    verified = 0
    for soc in HUBS:
        p = subprocess.run([str(HUB_BIN / "hub"), "verify-ledger", str(hub_dir(run, soc))], capture_output=True, text=True, env=HUB_ENV)
        text = (p.stdout + p.stderr).strip()
        ok = p.returncode == 0 and text.startswith("Ledger verified")
        verified += ok
        if not ok:
            fail(f"{soc}: hub verify-ledger failed: {text[:160]}")
        n, head = hub_head(run, soc)
        out(f"  {C}{soc:<10}{X} {n:>3} entries · head {head[:16]}… · {G + 'verified' if ok else R + text[:80]}{X}")
    res["checks"]["ledgers_verified"] = {"got": verified, "want": len(HUBS)}

    out(f"  {D}2. each head a parent recorded, compared with the child's own ledger.jsonl at that index{X}")
    out(f"  {D}   (same machine, both records under the demo operator's control: a cross-record consistency check, not an independent witness){X}")
    matched, posted = 0, 0
    for parent in ("de-sandbox", "aic"):
        st, t = http("GET", f"{hub_base(parent)}/v1/hubs/{run.s['hubs'][parent]['id']}/topics/{run.s['hubs'][parent]['topic']}")
        if st != 200 or not isinstance(t, dict) or not isinstance(t.get("posts"), list):
            fail(f"{parent}: record topic unreadable ({st})")
            continue
        for post in t["posts"]:
            body = str((post or {}).get("body", ""))
            if not body.startswith("act: ledger_head "):
                continue
            posted += 1
            try:
                f = dict(kv.split("=", 1) for kv in body.split()[3:] if "=" in kv)
                child, n, head = body.split()[2], int(f["entries"]), f["head"]
                rows = ledger_rows(run, child)
                have = rows[n - 1]["entry_hash"] if 0 < n <= len(rows) else None
            except Exception as e:
                fail(f"{parent}: head post unreadable or child ledger unreadable ({type(e).__name__}: {e})")
                continue
            ok = have == head
            matched += ok
            if not ok:
                fail(f"{parent} holds {child}'s head {head[:16]} at entry {n - 1}; {child}'s ledger.jsonl there has {str(have)[:16]}")
            out(f"  {C}{parent:<10}{X} holds {child}'s head at entry {n - 1}: {head[:16]}… → {child}'s ledger.jsonl there: "
                f"{G + 'consistent' if ok else R + 'MISMATCH ' + str(have)[:16]}{X}"
                f"  {D}{len(rows) - n} later entr{'y' if len(rows) - n == 1 else 'ies'} not anchored{X}")
    want_heads = len(exp["heads"])
    if want_heads != 2:
        fail(f"the story landed {want_heads} head post(s); 2 expected (desk→aic, aic→de-sandbox)")
    if posted != want_heads:
        fail(f"{posted} head post(s) on the parents' records, the story landed {want_heads}")
    res["checks"]["heads_consistent"] = {"got": matched, "want": 2, "posted": posted}

    out(f"  {D}3. every landed record is in its hub's ledger at the index and hash the hub returned{X}")
    present = 0
    cache = {}
    for r in exp["records"] + [dict(h, soc=h["parent"]) for h in exp["heads"]]:
        try:
            rows = cache.setdefault(r["soc"], ledger_rows(run, r["soc"]))
            ok = rows[r["entry_index"]]["entry_hash"] == r["entry_hash"]
        except Exception:
            ok = False
        present += ok
        if not ok:
            fail(f"{r['soc']}: the record the hub acknowledged at #{r['entry_index']} ({str(r['entry_hash'])[:12]}) is not in its ledger.jsonl")
    want_present = len(exp["records"]) + len(exp["heads"])
    out(f"  {C}records{X}    {present}/{want_present} acknowledged entries found in place")
    res["checks"]["acknowledged_entries_in_ledger"] = {"got": present, "want": want_present}

    out(f"  {D}4. the agents' own signatures on their records (§81-301(c); in-body, a BRIDGE: Hub keeps only its own signature){X}")
    for soc, agent in (("aic", "manager"), ("desk", "procure")):
        good, bad, why = check_signatures(run, soc)
        want = sum(1 for r in exp["records"] if r["soc"] == soc and r["signed"])
        for w in why:
            fail(w)
        if good is not None and (good != want or bad):
            fail(f"{soc}: {good} valid signature(s), {bad} invalid; the story landed {want} signed record(s)")
        out(f"  {C}{soc:<10}{X} {good}/{want} {agent} signature(s) valid" + (f", {R}{bad} invalid{X}" if bad else ""))
        res["checks"][f"signatures_{soc}"] = {"got": good, "want": want, "invalid": bad}

    out(f"  {D}5. each agent's gate record (every act, refused ones included; hash links checked over the window read){X}")
    for agent in GATES:
        want = exp["gate_outcomes"].get(agent, [])
        try:
            tok = operator_token(run, agent)
            st, d = http("GET", gate_base(agent) + "/api/chain?limit=5000", token=tok)
        except SystemExit as e:
            st, d = 0, {"error": str(e)}
        if st != 200 or not isinstance(d, dict) or not isinstance(d.get("entries"), list) or d.get("read_error"):
            fail(f"{agent}: gate chain unreadable ({st} {str(d)[:100]})")
            res["checks"][f"gate_{agent}"] = {"got": None, "want": len(want)}
            continue
        ents = sorted(d["entries"], key=lambda e: e.get("chain_position", 0))
        broken = sum(1 for a, b in zip(ents, ents[1:]) if b.get("chain_position") == a.get("chain_position", -2) + 1 and b.get("prev_hash") != a.get("hash"))
        rows = [e for e in ents if e.get("event_type") == "outcome" and str(e.get("plugin_id", "")).startswith("aic-")]
        got_ok = sum(1 for e in rows if e.get("success"))
        want_ok = sum(1 for w in want if w["success"])
        if broken:
            fail(f"{agent}: {broken} broken hash link(s) in the gate chain")
        if len(rows) != len(want) or got_ok != want_ok:
            fail(f"{agent}: gate shows {len(rows)} outcome(s) ({got_ok} successful); the story reported {len(want)} ({want_ok} successful)")
        out(f"  {C}{agent:<10}{X} {len(rows)}/{len(want)} outcome(s), {len(rows) - got_ok} not successful (refused or incomplete), "
            f"{'hash-linked' if not broken else R + str(broken) + ' broken link(s)' + X}")
        res["checks"][f"gate_{agent}"] = {"got": len(rows), "want": len(want), "successful": got_ok, "want_successful": want_ok, "broken_links": broken}

    res["ok"] = not res["failures"]
    (run.root / "audit.json").write_text(json.dumps(res, indent=2))
    out(f"\n  {D}stand-ins this run used (BRIDGE): heads into parents, outbox opening, suspension cascade, the agents' in-body signatures.{X}")
    out(f"  {D}the gate outcomes are matched by count and success, not by action id: Hestia's /api/chain view does not expose action ids.{X}")
    out(f"\n  {G + 'AUDIT PASS' if res['ok'] else R + 'AUDIT FAIL'}{X} {D}({run.root / 'audit.json'}){X}")
    for f in res["failures"]:
        out(f"    {R}✗{X} {f}")
    if as_json:
        print(json.dumps(res, indent=2))
    return res


def main():
    global SLOW
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, run = sys.argv[1], Run(Path(sys.argv[2]).expanduser().resolve())
    SLOW = "--slow" in sys.argv
    if cmd == "up":
        up(run)
    elif cmd == "story":
        sys.exit(0 if story(run)["ok"] else 1)
    elif cmd == "audit":
        sys.exit(0 if audit(run, as_json="--json" in sys.argv)["ok"] else 1)
    elif cmd == "down":
        down(run)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
