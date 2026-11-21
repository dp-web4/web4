#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
"""live_engine_probe.py: the conformance corpus and the priority/overlap counterexamples through the REAL engines.

  python3 aic_demo.py up PROBE_DIR && python3 tests/live_engine_probe.py PROBE_DIR; python3 aic_demo.py down PROBE_DIR

Use a fresh run folder of its own: this loads candidate and deliberately conflicting law into the run's hubs and gates.

Part A, corpus: every scenario in the rulebook, on the hub or gate of its society, loaded with the candidate projection.
  Real verdict vs the reference oracle. Hub verdicts are read from the status of a member-signed post:
  200 = allow, 202 = escalate (held), 403 = deny.
Part B, interactions: law the transpiler now REFUSES to compile (a less-strict child norm outranking a stricter
  ancestor), loaded anyway, to show what the engines do with it. Both engines evaluate one flattened law, so they
  follow the flattened oracle, not the level-by-level fold; that is why the compiler has to block these cases.
  Ties are reported, not asserted: neither engine documents its tie order.

Exit 1 if any corpus verdict or any asserted interaction differs from the oracle. Result: PROBE_DIR/probe.json.
"""
import copy
import json
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO))
sys.path.insert(0, str(DEMO / "tools"))
import aic_demo as D  # noqa: E402
import rulebook_to_web4 as T  # noqa: E402

SIGNER = {"de-sandbox": "society:aic", "aic": "manager", "desk": "procure"}
AGENT = {"h-manager": "manager", "h-procure": "procure"}
STATUS = {200: "allow", 202: "escalate", 403: "deny"}


def hub_verdict(run, soc, body):
    st, r = D.signed_event(run, soc, SIGNER[soc], {"action": "add_post", "topic_id": run.s["hubs"][soc]["topic"], "body": body})
    return STATUS.get(st, f"status {st}"), r


def load_hub_law(run, soc, norms, rb, tag):
    text, *_ = T.hub_law(rb, soc, norms, "candidate")
    path = run.root / f"probe-law-{soc}-{tag}.yaml"
    path.write_text(text)
    ok, n, out = D.hub_set_law(run, soc, path)
    if not ok:
        raise SystemExit(f"set-law failed on {soc} ({tag}): {out[:300]}")


def gate_verdict(gate, req):
    tool = req["tool"]
    target = req.get("command") if tool == "Bash" else req.get("target")
    aid, q = gate.ask(tool, target, {"command": target} if tool == "Bash" else {"file_path": target})
    d, rule, _ = D.verdict(q)
    gate.done(aid, d != "deny")
    return d, rule


def main(root):
    run = D.Run(Path(root).expanduser().resolve())
    if not run.s.get("hubs") or "manager" not in run.s.get("keys", {}):
        raise SystemExit(f"{run.root} is not an `up` run")
    rb = json.loads((run.rb / "effortless-rulebook" / "aic-rulebook.json").read_text())
    socs = T.by_id(rb, "Societies")
    gates = {a: D.Gate(a) for a in D.GATES}
    res = {"corpus": [], "interactions": [], "failures": []}

    # ---------------------------------------------------------------- A. corpus
    print(f"{D.B}A. the conformance corpus through the real hub and gates (candidate projection){D.X}")
    eff = {s: T.effective_norms(rb, s, "candidate")[0] for s in socs}
    for soc in ("de-sandbox", "aic", "desk"):
        load_hub_law(run, soc, eff[soc], rb, "corpus")
    for hearth, agent in AGENT.items():
        cfg, _ = T.hestia_configs(eff[hearth], "candidate")
        D.gate_rules(run, agent, cfg["rules"])
    for sc in rb["Scenarios"]["data"]:
        req, sid = json.loads(sc["Request"]), sc["Society"]
        norm = next(n for n in rb["Norms"]["data"] if n["NormId"] == sc["Norm"])
        if norm["CompileMode"] == "refused":
            continue
        if socs[sid]["LawSurface"] == "hub":
            oracle = T.hub_eval([n for n in eff[sid] if n["Surface"] == "hub-norm"], [], req)
            real, _ = hub_verdict(run, sid, req["payload"]["body"])
            real_rule = None
        else:
            cfg, ov = T.hestia_configs(eff[sid], "candidate")
            oracle = T.hestia_eval(cfg, ov, req)
            real, real_rule = gate_verdict(gates[AGENT[sid]], req)
        ok = real == oracle[0]
        res["corpus"].append({"case": sc["ScenarioId"], "society": sid, "oracle": oracle, "real": [real, real_rule], "ok": ok})
        if not ok:
            res["failures"].append(f"{sc['ScenarioId']}: oracle {oracle}, real {real} {real_rule or ''}")
        rule_note = "" if real_rule is None or real_rule == (oracle[1] or "") else f"  {D.D}(rule: real {real_rule or '-'}, oracle {oracle[1] or '-'}){D.X}"
        print(f"  {sc['ScenarioId']} {sid:<10} oracle {oracle[0]:<8} real {D.G if ok else D.R}{real}{D.X}{rule_note}")

    # ---------------------------------------------------------------- B. interactions
    print(f"\n{D.B}B. priority/overlap interactions the compiler now refuses, loaded anyway{D.X}")
    norms = T.by_id(rb, "Norms")

    def variant(src, **kw):
        n = copy.deepcopy(norms[src])
        n.update(kw)
        return n

    def record(case, oracle_flat, fold, real, assert_flat=True):
        ok = (real == oracle_flat) if assert_flat else True
        res["interactions"].append({"case": case, "flattened_oracle": oracle_flat, "fold": fold, "real": real,
                                    "asserted": assert_flat, "ok": ok})
        if not ok:
            res["failures"].append(f"{case}: flattened oracle {oracle_flat}, real {real}")
        mark = (D.G if ok else D.R) if assert_flat else D.Y
        print(f"  {case:<62} flattened {oracle_flat:<8} fold {fold:<8} real {mark}{real}{D.X}" + ("" if assert_flat else f" {D.D}(observed, not asserted){D.X}"))

    # B1 hestia: child allow (aic level) outranking the sandbox's disclosure deny
    hm = eff["h-manager"] + [variant("OA-LISTED-CASTINGS", NormId="OA-PROBE-CASTINGS-OUTBOX", Priority=99,
                                     HestiaTargetPattern="**/counterparties/example-castings/outbox/**")]
    chain = T.chain_of(rb, "h-manager")
    cfg, ov = T.hestia_configs(hm, "candidate")
    D.gate_rules(run, "manager", cfg["rules"])
    for cp in ("example-castings", "example-freight"):
        req = {"tool": "Write", "target": f"/home/aic/workspace/counterparties/{cp}/outbox/rfq.md"}
        record(f"hestia: child allow p99 vs parent deny p95, {cp} outbox", T.hestia_eval(cfg, ov, req)[0],
               T.fold_eval(hm, chain, "hestia", req)[0], gate_verdict(gates["manager"], req)[0])
    # B2 hestia: a tie (allow and deny, same priority, same target)
    hm2 = eff["h-manager"] + [variant("OA-LISTED-CASTINGS", NormId="OA-PROBE-TIE", Priority=95,
                                      HestiaTargetPattern="**/counterparties/*/outbox/**", HestiaTools='["Write", "Edit"]')]
    cfg, ov = T.hestia_configs(hm2, "candidate")
    D.gate_rules(run, "manager", cfg["rules"])
    req = {"tool": "Write", "target": "/home/aic/workspace/counterparties/example-castings/outbox/rfq.md"}
    real = gate_verdict(gates["manager"], req)
    record(f"hestia: allow p95 vs deny p95 tie (real rule {real[1] or '-'})", T.hestia_eval(cfg, ov, req)[0],
           T.fold_eval(hm2, chain, "hestia", req)[0], real[0], assert_flat=False)

    # B3 hub: child allow (aic) outranking the sandbox's undisclosed-contact deny
    aic = eff["aic"] + [variant("DE-ESC-UNDISCLOSED-CONTACT", NormId="AIC-PROBE-CONTACT-OK", Society="aic", Decision="allow", Priority=95,
                                Value="^act: counterparty_contact_undisclosed example-castings\\b")]
    load_hub_law(run, "aic", aic, rb, "outrank")
    hn = [n for n in aic if n["Surface"] == "hub-norm"]
    for cp in ("example-castings", "example-metals"):
        body = f"act: counterparty_contact_undisclosed {cp}"
        req = {"action": "post_added", "payload": {"body": body}}
        record(f"hub: child allow p95 vs parent deny p90, {cp}", T.hub_eval(hn, [], req)[0],
               T.fold_eval(aic, T.chain_of(rb, "aic"), "hub", req)[0], hub_verdict(run, "aic", body)[0])
    # B4 hub: child escalate outranking the parent deny
    aic = eff["aic"] + [variant("DE-ESC-UNDISCLOSED-CONTACT", NormId="AIC-PROBE-ESCALATE", Society="aic", Decision="escalate", Priority=95,
                                EscalateTo="sovereign", Value="^act: counterparty_contact_undisclosed example-freight\\b")]
    load_hub_law(run, "aic", aic, rb, "escalate")
    hn = [n for n in aic if n["Surface"] == "hub-norm"]
    body = "act: counterparty_contact_undisclosed example-freight"
    req = {"action": "post_added", "payload": {"body": body}}
    record("hub: child escalate p95 vs parent deny p90", T.hub_eval(hn, [], req)[0],
           T.fold_eval(aic, T.chain_of(rb, "aic"), "hub", req)[0], hub_verdict(run, "aic", body)[0])
    # B5 hub: a tie (allow and deny at the same priority)
    aic = eff["aic"] + [variant("DE-ESC-UNDISCLOSED-CONTACT", NormId="AIC-PROBE-TIE", Society="aic", Decision="allow", Priority=90,
                                Value="^act: counterparty_contact_undisclosed example-tie\\b")]
    load_hub_law(run, "aic", aic, rb, "tie")
    hn = [n for n in aic if n["Surface"] == "hub-norm"]
    body = "act: counterparty_contact_undisclosed example-tie"
    req = {"action": "post_added", "payload": {"body": body}}
    record("hub: allow p90 vs deny p90 tie", T.hub_eval(hn, [], req)[0],
           T.fold_eval(aic, T.chain_of(rb, "aic"), "hub", req)[0], hub_verdict(run, "aic", body)[0], assert_flat=False)

    res["ok"] = not res["failures"]
    (run.root / "probe.json").write_text(json.dumps(res, indent=2))
    n_ok = sum(1 for c in res["corpus"] if c["ok"])
    n_int = [i for i in res["interactions"] if i["asserted"]]
    print(f"\n  corpus: {n_ok}/{len(res['corpus'])} real verdicts match the oracle; "
          f"interactions: {sum(1 for i in n_int if i['ok'])}/{len(n_int)} asserted cases follow the flattened oracle"
          f" ({sum(1 for i in n_int if i['real'] != i['fold'])} of them differ from the fold, i.e. the engine would loosen the parent)")
    for f in res["failures"]:
        print(f"  {D.R}✗{D.X} {f}")
    print(f"  {D.G + 'PROBE PASS' if res['ok'] else D.R + 'PROBE FAIL'}{D.X} {D.D}({run.root / 'probe.json'}){D.X}")
    return res


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(0 if main(sys.argv[1])["ok"] else 1)
