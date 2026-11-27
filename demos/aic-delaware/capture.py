#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
"""capture.py: publish one real run of the demo as evidence, and the answers page built from it.

  python3 capture.py run [RUN_DIR]   a fresh run (up, story, audit), exported into evidence/, then down.
                                     RUN_DIR (default /tmp/aic-delaware-run) must not exist yet. Its path
                                     appears in the gates' signed records, so keep it neutral.
  python3 capture.py render          evidence/ + answers.md.in -> ANSWERS.md. No daemons.
                                     tests/test_evidence.py fails if ANSWERS.md is not what this renders.

`run` needs what aic_demo.py needs (hub binaries via HUB_BIN, hestia 0.3.0, python3 with cryptography).
Nothing secret is exported: the demo's keys stay in RUN_DIR/state.json and the hubs' vaults, which are not copied.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import check_evidence as CE

HERE = Path(__file__).resolve().parent
EV = HERE / "evidence"
TEMPLATE = HERE / "answers.md.in"
ANSWERS = HERE / "ANSWERS.md"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


# ------------------------------------------------------------------ run + export
def sh(*a, env=None, check=True):
    p = subprocess.run([str(x) for x in a], capture_output=True, text=True, env=env)
    if check and p.returncode:
        raise SystemExit(f"failed ({p.returncode}): {' '.join(map(str, a))}\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}")
    return p


def scrub(text, run_root):
    return ANSI.sub("", text).replace(str(run_root), "RUN")


def export(run_root, story_out):
    import aic_demo as D
    run = D.Run(run_root)
    if EV.exists():
        shutil.rmtree(EV)
    for d in ("hubs", "ledgers", "gates", "law"):
        (EV / d).mkdir(parents=True)
    w = lambda rel, obj: (EV / rel).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (EV / "story.txt").write_text(scrub(story_out, run_root), encoding="utf-8")
    shutil.copyfile(run_root / "audit.json", EV / "audit.json")
    w("expect.json", run.s["expect"])
    w("trail.json", json.loads(scrub(json.dumps(run.s["trail"], ensure_ascii=False), run_root)))

    hubs = {}
    for soc, (name, port) in D.HUBS.items():
        with urllib.request.urlopen(f"{D.hub_base(soc)}/.well-known/web4-hub.json", timeout=10) as r:
            desc = json.loads(r.read())
        w(f"hubs/{soc}.descriptor.json", desc)
        shutil.copyfile(D.hub_dir(run, soc) / "ledger.jsonl", EV / "ledgers" / f"{soc}.jsonl")
        hubs[soc] = {"name": name, "hub_id": run.s["hubs"][soc]["id"], "record_topic": run.s["hubs"][soc]["topic"]}
    w("hubs/hubs.json", hubs)

    henv = dict(os.environ, HESTIA_PASSPHRASE=D.HEST_PASS)
    for agent in D.GATES:
        st, c = D.http("GET", D.gate_base(agent) + "/api/chain?limit=5000", token=D.operator_token(run, agent))
        last = max(e["chain_position"] for e in c["entries"])
        seg = sh("hestia", "--home", D.gate_home(run, agent), "chain-export", "--from", 0, "--to", last, env=henv).stdout
        (EV / "gates" / f"{agent}.segment.json").write_text(seg, encoding="utf-8")
        s = json.loads(seg)
        keys = sorted({x["witness_public_key"] for x in s["signatures"]})
        anchors = {"chain_id": s["chain_id"], "witness_public_keys": keys, "end_hash": s["entries"][-1]["hash"]}
        w(f"gates/{agent}.anchors.json", anchors)
        args = ["hestia", "chain-verify", EV / "gates" / f"{agent}.segment.json", "--expect-chain-id", anchors["chain_id"],
                "--expect-end-hash", anchors["end_hash"]]
        for k in keys:
            args += ["--trusted-witness-key", k]
        v = sh(*args, check=False)
        w(f"gates/{agent}.verify.json", json.loads(v.stdout[v.stdout.index("{"):v.stdout.rindex("}") + 1]))
        if v.returncode:
            raise SystemExit(f"hestia chain-verify failed for {agent}'s gate:\n{v.stdout}\n{v.stderr}")

    proj = run.rb / "web4"
    shutil.copyfile(proj / "manifest.json", EV / "law" / "manifest.json")
    for soc in D.HUBS:
        shutil.copyfile(proj / "societies" / soc / "law.ratified.yaml", EV / "law" / f"{soc}.law.yaml")
    for agent, (gsoc, _) in D.GATES.items():
        shutil.copyfile(proj / "societies" / gsoc / "hestia-policy.ratified.json", EV / "law" / f"{agent}.gate-policy.json")
    shutil.copyfile(run_root / "law-aic-suspended.yaml", EV / "law" / "aic.suspended.law.yaml")
    w("law/clause-2.3-overruled.json", clause_2_3_overruled(run))

    w("versions.json", {
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hub": sh(D.HUB_BIN / "hub", "--version").stdout.strip(),
        "hestia": sh("hestia", "--version").stdout.strip(),
        "python": sys.version.split()[0],
        "cryptography": __import__("cryptography").__version__,
        "run_dir": str(run_root),
    })


def clause_2_3_overruled(run):
    """The member overrules the state's citation against clause 2.3 (Citations c-19 -> overruled), on a copy of the
    rulebook as ratified in the run. Does the compiler then let the clause loosen the parent's law?"""
    with tempfile.TemporaryDirectory() as t:
        rb = Path(t) / "aic"
        shutil.copytree(run.rb, rb, ignore=shutil.ignore_patterns("web4", "__pycache__"))
        sh(sys.executable, rb / "rulebook.py", "set", "Citations", "c-19", "Stance", "overruled")
        p = sh(sys.executable, HERE / "tools" / "rulebook_to_web4.py", rb / "effortless-rulebook" / "aic-rulebook.json",
               Path(t) / "out", "--known-exceptions", rb / "known-exceptions.json", check=False)
        mf = json.loads((Path(t) / "out" / "manifest.json").read_text())
        norm = next(n for n in json.loads((rb / "effortless-rulebook" / "aic-rulebook.json").read_text())["Norms"]["data"]
                    if n["NormId"] == "OA-REPEAT-NO-DISCLOSURE")
        return {"what": "Citations c-19 (the draft's §8008(a) / §81-205(d)(11), contradicting clause 2.3) set to 'overruled', then compiled",
                "norm_compile_mode_after_overrule": norm.get("CompileMode"),
                "compiler_exit_code": p.returncode, "activation_allowed": mf.get("activation_allowed"),
                "blocking": mf.get("blocking")}


def run_and_export(run_root):
    if run_root.exists():
        raise SystemExit(f"{run_root} exists; pick a fresh RUN_DIR")
    demo = [sys.executable, str(HERE / "aic_demo.py")]
    try:
        sh(*demo, "up", run_root)
        story = sh(*demo, "story", run_root, check=False)
        if story.returncode:
            raise SystemExit(f"the story's audit failed; nothing exported\n{ANSI.sub('', story.stdout)[-3000:]}")
        export(run_root, story.stdout)
    finally:
        sh(*demo, "down", run_root, check=False)
    render()
    res = CE.check(EV)
    print(f"exported to {EV}; offline checks: {'PASS' if res['ok'] else 'FAIL'}")
    if not res["ok"]:
        sys.exit(1)


# ------------------------------------------------------------------ the answers page
def load():
    j = lambda rel: json.loads((EV / rel).read_text(encoding="utf-8"))
    ledgers = {lvl: [json.loads(l) for l in (EV / "ledgers" / f"{lvl}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
               for lvl in CE.LEVELS}
    return {"trail": j("trail.json"), "audit": j("audit.json"), "versions": j("versions.json"), "expect": j("expect.json"),
            "ledgers": ledgers, "check": CE.check(EV), "o23": j("law/clause-2.3-overruled.json"),
            "manifest": j("law/manifest.json"), "seg": {a: j(f"gates/{a}.segment.json") for a in CE.GATES},
            "verify": {a: j(f"gates/{a}.verify.json") for a in CE.GATES}, "anchors": {a: j(f"gates/{a}.anchors.json") for a in CE.GATES}}


def wrap_entry(e):
    """A ledger entry, pretty-printed, with the long hex values kept whole."""
    return json.dumps(e, indent=2, ensure_ascii=False)


def blocks(d):
    tr, ck, L = d["trail"], d["check"], d["ledgers"]
    acts = [t for t in tr if t["kind"] == "act"]
    recs = [t for t in tr if t["kind"] == "record"]
    keys = CE.admitted_keys(L["aic"])
    manager_id = next(k for k, (n, _) in keys.items() if "manager" in n.lower())
    disclosure = next(e for e in CE.posts(L["aic"]) if e["event"]["body"].startswith("act: counterparty_disclosed"))
    admission = next(e for e in L["aic"] if (e.get("event") or {}).get("kind") == "member_added"
                     and e["event"]["member_lct_id"] == manager_id)
    line, signer, sig = CE.split_signed_body(disclosure["event"]["body"])
    b = {}
    b["captured"] = (f"{d['versions']['captured_at'][:10]}, `{d['versions']['hub']}`, `{d['versions']['hestia']}`")
    b["record_entry"] = wrap_entry(disclosure)
    b["record_index"] = str(disclosure["index"])
    b["admission_index"] = str(admission["index"])
    b["manager_key"] = admission["event"]["member_pubkey_hex"]
    b["manager_id"] = manager_id
    b["hub_key_aic"] = ck["ledgers"]["aic"]["hub_pubkey_hex"]
    b["signed_line"] = line
    sa, sd = ck["agent_signatures"]["aic"], ck["agent_signatures"]["desk"]
    count = lambda c: f"all {c['valid']}" if not c["invalid"] else f"{c['valid']} of {c['valid'] + c['invalid']}"
    b["sig_counts"] = f"{count(sa)} of the manager's signed records and {count(sd)} of its sub-agent's verify"
    b["ledger_counts"] = ", ".join(f"{lvl} {l['entries']} entries" for lvl, l in ck["ledgers"].items())

    g = ck["gates"]
    refused = [a for a in acts if not a["allowed"]]
    b["gate_counts"] = (f"The manager's gate recorded {g['manager']['acts']} acts, {g['manager']['not_successful']} of them refused "
                        f"or incomplete; the sub-agent's gate {g['procure']['acts']}, {g['procure']['not_successful']} refused or incomplete. "
                        f"{len(refused)} of those acts were refused outright, so they exist only in the gates' records: "
                        f"nothing happened, and the agent itself wrote nothing about them.")
    ref = next(e for e in d["seg"]["manager"]["entries"] if e.get("event_type") == "policy_decision"
               and (e.get("event_data") or {}).get("decision") == "deny")
    ed = ref["event_data"]
    show = {"timestamp": ref["timestamp"], "event_type": ref["event_type"],
            "event_data (selected fields)": {k: ed.get(k) for k in ("plugin_id", "tool_name", "target", "decision", "enforced",
                                                                     "rule_id", "rule_name", "reason")},
            "prev_hash": ref["prev_hash"], "hash": ref["hash"]}
    b["gate_refusal_entry"] = json.dumps(show, indent=2, ensure_ascii=False)
    gif = [e["event_data"] for e in d["seg"]["manager"]["entries"] if e.get("event_type") == "gate_integrity_finding"]
    b["gate_integrity"] = (f"\"{gif[0].get('reason')}\" (status: {gif[0].get('status')})" if gif else "none")
    b["gate_witness_manager"] = ", ".join(d["anchors"]["manager"]["witness_public_keys"])

    rows = ["| beat | agent | act | target | gate | rule | outcome |", "|---|---|---|---|---|---|---|"]
    for a in acts:
        target = a["target"] if len(a["target"]) <= 56 else a["target"][:53] + "..."
        effect = str(a.get("effect", "")).replace("synthetic effect: ", "").replace("synthetic: ", "").replace("synthetic read: ", "read ")
        if not a["allowed"]:
            outcome = "nothing happened"
        elif a.get("record_status") is not None:
            outcome = f"{effect}; record landed" if a["complete"] else f"{effect}; NOT complete: record {a['record_status']}"
        else:
            outcome = effect if a["complete"] else f"failed: {effect}"
        rows.append(f"| {a['beat']} | {a['agent']} | {a['tool']} | `{target}` | {'**refused**' if not a['allowed'] else 'allowed'} | "
                    f"{a['rule'] or '(no rule covers it)'} | {outcome} |")
    b["act_table"] = "\n".join(rows)

    held = [r for r in recs if not r["landed"]]
    b["held_records"] = "\n".join(f"- Beat {r['beat']}, `{r['record_kind']}` from {r['signer']} to {r['soc']}: **{r['status']}**, "
                                  f"\"{r['error']}\"" for r in held)

    ll = [t for t in tr if t["kind"] == "law_loaded"]
    first_ref = ll[0]["refused_at_compile"][0] if ll and ll[0]["refused_at_compile"] else {"kind": "?", "detail": "?"}
    b["clause23_refused"] = f"`{first_ref['kind']}`: {first_ref['detail']}"
    o = d["o23"]
    unexp = (o.get("blocking") or {}).get("unexpected") or []
    b["clause23_overruled"] = "\n".join(f"- `{u['kind']}`: {u['detail']}" for u in unexp) or "- (no unexpected finding)"
    b["clause23_overruled_exit"] = (f"exit code {o['compiler_exit_code']}, activation allowed: "
                                    f"{str(o['activation_allowed']).lower()}")
    b["law_levels"] = "; ".join(f"beat {t['beat']}: " + ", ".join(f"{k} {v} norms" for k, v in t["hubs"].items()) for t in ll)

    rem = next(t for t in tr if t["kind"] == "removal")
    t0 = datetime.fromisoformat(rem["t"])
    after = sorted((t for t in tr if t["beat"] == 7 and t["kind"] in ("act", "record", "bridge_step")), key=lambda t: t["t"])
    lines = [f"| +0 ms | administrator removes the AIC from the sandbox | {rem['status']} `{json.dumps(rem['response'])}` |"]
    since = lambda t: int((datetime.fromisoformat(t["t"]) - t0).total_seconds() * 1000)
    for t in after:
        ms = since(t)
        if t["kind"] == "bridge_step":
            what, res = f"BRIDGE: {t['step']}", "done"
        elif t["kind"] == "act":
            what = f"{t['agent']} {t['tool']} `{t['target']}`"
            res = f"**refused** by {t['rule']}" if not t["allowed"] else f"allowed by {t['rule']}"
        else:
            what = f"{t['signer']} records `{t['record_kind']}` at {t['soc']}"
            res = f"landed #{t['entry_index']}" if t["landed"] else f"**{t['status']}**: {t['error']}"
        lines.append(f"| +{ms} ms | {what} | {res} |")
    b["cease_table"] = "| when | what | result |\n|---|---|---|\n" + "\n".join(lines)
    stop = next((t for t in after if t["kind"] == "bridge_step" and "every act stops" in t["step"]), None)
    narrowed = next((t for t in after if t["kind"] == "bridge_step" and "narrowed" in t["step"]), None)
    b["stop_ms"] = str(since(stop)) if stop else "n/a"
    b["narrow_ms"] = str(since(narrowed) - since(stop)) if stop and narrowed else "n/a"

    heads = ck["heads"]
    b["heads"] = "\n".join(f"- {h['parent']} entry #{h['parent_entry']} holds `{h['head']}`, {h['child']}'s entry #{h['child_entry']}: "
                           f"{'matches' if h['consistent'] else 'DOES NOT MATCH'}. {h['later_entries_not_anchored']} later "
                           f"{h['child']} entr{'y' if h['later_entries_not_anchored'] == 1 else 'ies'} not anchored."
                           for h in heads)
    aic_tail = next((h["later_entries_not_anchored"] for h in heads if h["child"] == "aic"), 0)
    b["aic_unanchored"] = str(aic_tail)
    head_post = next(e for e in CE.posts(L["de-sandbox"]) if e["event"]["body"].startswith("act: ledger_head "))
    b["head_post"] = head_post["event"]["body"]

    au = d["audit"]["checks"]
    b["audit_summary"] = "\n".join(f"- `{k}`: {json.dumps(v)}" for k, v in au.items())
    b["audit_ok"] = "passed" if d["audit"]["ok"] else "FAILED"
    b["verify_status"] = ", ".join(f"{a}: {d['verify'][a]['status']} ({d['verify'][a]['checked_entries']} entries, "
                                   f"{d['verify'][a]['signed_valid']} signatures valid, links intact: "
                                   f"{str(d['verify'][a]['link_intact']).lower()})" for a in CE.GATES)
    b["verify_limits"] = "\n".join(f"- {x}" for x in d["verify"]["manager"].get("limitations", []))
    an = d["anchors"]["manager"]
    b["gate_verify_cmd"] = (f"hestia chain-verify evidence/gates/manager.segment.json --expect-chain-id {an['chain_id']} "
                            f"--expect-end-hash {an['end_hash']} --trusted-witness-key {an['witness_public_keys'][0]}")
    return b


def render():
    b = blocks(load())
    text = TEMPLATE.read_text(encoding="utf-8")
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", text)) - set(b))
    if missing:
        raise SystemExit(f"answers.md.in uses unknown blocks: {missing}")
    out = re.sub(r"\{\{(\w+)\}\}", lambda m: b[m.group(1)], text)
    ANSWERS.write_text(out, encoding="utf-8")
    return out


def rendered():
    """What ANSWERS.md should hold, without writing it (for the test)."""
    b = blocks(load())
    return re.sub(r"\{\{(\w+)\}\}", lambda m: b[m.group(1)], TEMPLATE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    if len(sys.argv) >= 2 and sys.argv[1] == "run":
        run_and_export(Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/aic-delaware-run").resolve())
    elif len(sys.argv) >= 2 and sys.argv[1] == "render":
        render()
        print(f"wrote {ANSWERS}")
    else:
        sys.exit(__doc__)
