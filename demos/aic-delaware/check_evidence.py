#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
"""check_evidence.py: check the published run (evidence/) yourself, with nothing running.

  python3 check_evidence.py [EVIDENCE_DIR] [--json]

Needs python3 and the `cryptography` package. No hub, no gate, no network. Exit 1 on any failure.

What it checks, from the files alone:
  1. Each hub's ledger: every entry's SHA-256 is recomputed, every entry links to the one before it, and every
     entry carries a valid Ed25519 signature by the hub key that hub published (hubs/<level>.descriptor.json).
  2. The agents' own signatures: every record that carries one verifies against the key the agent was admitted
     with, read from the `member_added` entry on the same ledger (so the key is itself on the signed record).
  3. Ledger heads held by a parent: each one equals the child ledger's entry at that index.
  4. Every record the story counted as landed (expect.json) is in its ledger at the index and hash the hub returned.
  5. Each gate's record: the entries link by hash. The gate's own signatures need Hestia's verifier; the result
     captured at publish time is in gates/<agent>.verify.json, and the command is in ANSWERS.md.
  6. The administrator's audit from the run (audit.json) passed.

What it cannot tell you: that the hub key belongs to who it says (that needs the key from somewhere other than
this folder), or that the gates saw every act (assurance A1: cooperative agents, tamper-evident records).
"""
import hashlib
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

HERE = Path(__file__).resolve().parent
LEVELS = ("de-sandbox", "aic", "desk")
GATES = ("manager", "procure")


def _clear_last(line, key, value):
    """The line with the last `"key":"value"` replaced by `"key":""`: the hub hashes and signs its own serialization
    with these fields cleared, and the stored line is that serialization, so this needs no JSON re-encoding."""
    needle = f'"{key}":"{value}"'
    i = line.rfind(needle)
    if i < 0:
        raise ValueError(f"{key} not found as stored")
    return line[:i] + f'"{key}":""' + line[i + len(needle):]


def verify_signature(pubkey_hex, sig_hex, message):
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubkey_hex)).verify(bytes.fromhex(sig_hex), message)
        return True
    except Exception:
        return False


def check_ledger(path, hub_pubkey_hex):
    """Recompute every entry. Returns (rows, problems)."""
    rows, problems, prev = [], [], None
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            hash_input = _clear_last(line, "entry_hash", e["entry_hash"])
            sign_input = _clear_last(hash_input, "signature", e["signature"])
        except Exception as ex:
            problems.append(f"{path.name} line {n + 1}: unreadable ({type(ex).__name__})")
            continue
        if e.get("index") != len(rows):
            problems.append(f"{path.name} #{e.get('index')}: out of order (expected #{len(rows)})")
        if hashlib.sha256(hash_input.encode("utf-8")).hexdigest() != e["entry_hash"]:
            problems.append(f"{path.name} #{e['index']}: content does not match its entry hash")
        if prev is not None and e.get("prev_hash") != prev:
            problems.append(f"{path.name} #{e['index']}: does not link to the entry before it")
        if not verify_signature(hub_pubkey_hex, e["signature"], sign_input.encode("utf-8")):
            problems.append(f"{path.name} #{e['index']}: the hub's signature does not verify")
        prev = e["entry_hash"]
        rows.append(e)
    return rows, problems


def admitted_keys(rows):
    """member id -> (name, pubkey) from the ledger's own admission entries."""
    return {e["event"]["member_lct_id"]: (e["event"].get("member_name", ""), e["event"].get("member_pubkey_hex", ""))
            for e in rows if (e.get("event") or {}).get("kind") == "member_added"}


def split_signed_body(body):
    """'<line>\\nsigned-by: <id>\\nsig: <hex>' -> (line, id, sig), or None when the record carries no signature."""
    if "\nsigned-by: " not in body or "\nsig: " not in body:
        return None
    line, rest = body.split("\nsigned-by: ", 1)
    signer, sig = rest.split("\nsig: ", 1)
    return line, signer.strip(), sig.strip()


def posts(rows):
    return [e for e in rows if (e.get("event") or {}).get("kind") == "post_added"]


def check(ev):
    res = {"ok": False, "ledgers": {}, "agent_signatures": {}, "heads": [], "counted_records": {}, "gates": {},
           "audit_ok": None, "failures": []}
    fail = res["failures"].extend
    ledgers = {}
    for lvl in LEVELS:
        desc = json.loads((ev / "hubs" / f"{lvl}.descriptor.json").read_text())
        rows, problems = check_ledger(ev / "ledgers" / f"{lvl}.jsonl", desc["hub_pubkey_hex"])
        fail(problems)
        ledgers[lvl] = rows
        res["ledgers"][lvl] = {"entries": len(rows), "problems": len(problems), "head": rows[-1]["entry_hash"] if rows else None,
                               "hub_pubkey_hex": desc["hub_pubkey_hex"]}

    for lvl in ("aic", "desk"):
        keys = admitted_keys(ledgers[lvl])
        good = bad = 0
        for e in posts(ledgers[lvl]):
            parts = split_signed_body(e["event"].get("body", ""))
            if not parts:
                continue
            line, signer, sig = parts
            name, pk = keys.get(signer, ("", ""))
            if signer != e["event"].get("posted_by"):
                fail([f"{lvl} #{e['index']}: signed by {signer[:8]} but posted by {str(e['event'].get('posted_by'))[:8]}"])
            if pk and verify_signature(pk, sig, line.encode("utf-8")):
                good += 1
            else:
                bad += 1
                fail([f"{lvl} #{e['index']}: the agent's own signature does not verify against its admitted key"])
        res["agent_signatures"][lvl] = {"valid": good, "invalid": bad}

    for parent in ("de-sandbox", "aic"):
        for e in posts(ledgers[parent]):
            body = e["event"].get("body", "")
            if not body.startswith("act: ledger_head "):
                continue
            try:
                child = body.split()[2]
                f = dict(kv.split("=", 1) for kv in body.split()[3:] if "=" in kv)
                n, head = int(f["entries"]), f["head"]
                have = ledgers[child][n - 1]["entry_hash"] if 0 < n <= len(ledgers[child]) else None
            except Exception as ex:
                fail([f"{parent} #{e['index']}: unreadable head record ({type(ex).__name__})"])
                continue
            ok = have == head
            if not ok:
                fail([f"{parent} #{e['index']} holds {child}'s head at entry {n - 1}, but {child}'s ledger there differs"])
            res["heads"].append({"parent": parent, "parent_entry": e["index"], "child": child, "child_entry": n - 1,
                                 "head": head, "consistent": ok, "later_entries_not_anchored": len(ledgers[child]) - n})

    exp = json.loads((ev / "expect.json").read_text())
    for r in exp["records"] + [dict(h, soc=h["parent"]) for h in exp["heads"]]:
        rows = ledgers[r["soc"]]
        ok = 0 <= r["entry_index"] < len(rows) and rows[r["entry_index"]]["entry_hash"] == r["entry_hash"]
        c = res["counted_records"].setdefault(r["soc"], {"found": 0, "counted": 0})
        c["counted"] += 1
        c["found"] += ok
        if not ok:
            fail([f"{r['soc']}: the record counted at #{r['entry_index']} is not in the ledger as acknowledged"])

    for agent in GATES:
        seg = json.loads((ev / "gates" / f"{agent}.segment.json").read_text())
        ents = seg["entries"]
        broken = sum(1 for a, b in zip(ents, ents[1:]) if b.get("prev_hash") != a.get("hash"))
        outcomes = [e.get("event_data") or {} for e in ents if e.get("event_type") == "outcome"]
        outcomes = [o for o in outcomes if str(o.get("plugin_id", "")).startswith("aic-")]
        verified = json.loads((ev / "gates" / f"{agent}.verify.json").read_text())
        if broken:
            fail([f"gate {agent}: {broken} broken hash link(s)"])
        if verified.get("status") != "valid":
            fail([f"gate {agent}: the captured Hestia verification is not 'valid'"])
        res["gates"][agent] = {"entries": len(ents), "broken_links": broken, "acts": len(outcomes),
                               "not_successful": sum(1 for e in outcomes if not e.get("success")),
                               "hestia_verify_at_capture": verified.get("status")}

    audit = json.loads((ev / "audit.json").read_text())
    res["audit_ok"] = bool(audit.get("ok"))
    if not res["audit_ok"]:
        fail(["audit.json: the run's own audit did not pass"])
    res["ok"] = not res["failures"]
    return res


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ev = Path(args[0]) if args else HERE / "evidence"
    res = check(ev)
    if "--json" in sys.argv:
        print(json.dumps(res, indent=2))
    else:
        for lvl, l in res["ledgers"].items():
            print(f"ledger {lvl:<10} {l['entries']:>3} entries, hashes + links + hub signatures: "
                  f"{'all valid' if not l['problems'] else str(l['problems']) + ' problem(s)'}")
        for lvl, s in res["agent_signatures"].items():
            print(f"agent signatures on {lvl:<5} {s['valid']} valid, {s['invalid']} invalid (keys from the ledger's admission entries)")
        for h in res["heads"]:
            print(f"head of {h['child']} held by {h['parent']} (#{h['parent_entry']}): "
                  f"{'matches' if h['consistent'] else 'DOES NOT MATCH'} {h['child']} entry {h['child_entry']}; "
                  f"{h['later_entries_not_anchored']} later entr{'y' if h['later_entries_not_anchored'] == 1 else 'ies'} not anchored")
        for soc, c in res["counted_records"].items():
            print(f"counted records on {soc:<10} {c['found']}/{c['counted']} in place")
        for agent, g in res["gates"].items():
            print(f"gate {agent:<8} {g['entries']} entries, {g['acts']} acts ({g['not_successful']} refused or incomplete), "
                  f"links {'intact' if not g['broken_links'] else 'BROKEN'}, Hestia verify at capture: {g['hestia_verify_at_capture']}")
        print(f"run audit: {'passed' if res['audit_ok'] else 'FAILED'}")
        print("\nEVIDENCE CHECKS PASS" if res["ok"] else "\nEVIDENCE CHECKS FAIL")
        for f in res["failures"]:
            print("  x", f)
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
