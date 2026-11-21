# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
"""Negative controls for the driver (Nova's review of #994): bridges fail closed, acts are complete only when their
record lands, and the audit fails (structured result, exit 1) on tampering. The HTTP layer, the hub CLI and the gates
are mocked, so no daemon is needed. Needs `cryptography` (the driver's only dependency)."""
import io
import json
import socket
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

DEMO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO))
import aic_demo as D  # noqa: E402

AIC_LCT_KEY = "society:aic"


def make_run(tmp):
    run = D.Run(Path(tmp))
    run.s["hubs"] = {s: {"id": f"hub-{s}", "topic": f"topic-{s}", "sovereign_lct": "sov"} for s in D.HUBS}
    run.s["expect"] = {"records": [], "heads": [], "gate_outcomes": {a: [] for a in D.GATES}}
    run.save()
    return run


def quiet(fn, *a, **k):
    with redirect_stdout(io.StringIO()):
        return fn(*a, **k)


LANDED = (200, {"entry_index": 7, "entry_hash": "abc123"})


class Http(unittest.TestCase):
    def test_timeout_is_status_0_not_an_exception(self):
        with mock.patch.object(D.urllib.request, "urlopen", side_effect=socket.timeout("timed out")):
            st, r = D.http("GET", "http://127.0.0.1:1/x")
        self.assertEqual(st, 0)
        self.assertIn("timed out", r["error"])

    def test_refused_connection_is_status_0(self):
        with mock.patch.object(D.urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")):
            self.assertEqual(D.http("GET", "http://127.0.0.1:1/x")[0], 0)

    def test_malformed_200_is_status_minus_1(self):
        class R:
            status = 200
            def read(self): return b"<html>not json"
            def __enter__(self): return self
            def __exit__(self, *a): return False
        with mock.patch.object(D.urllib.request, "urlopen", return_value=R()):
            self.assertEqual(D.http("GET", "http://127.0.0.1:1/x")[0], -1)

    def test_landed_needs_200_and_an_entry(self):
        self.assertTrue(D.landed(*LANDED))
        self.assertFalse(D.landed(200, {}))
        self.assertFalse(D.landed(202, LANDED[1]))
        self.assertFalse(D.landed(200, "ok"))


class OutboxBridge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = make_run(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def attempt(self, disclosure, topic=(200, {"posts": [{"body": "act: counterparty_disclosed example-castings\nsig: x"}]})):
        with mock.patch.object(D, "gate_add") as ga, mock.patch.object(D, "http", return_value=topic):
            ok = quiet(D.bridge_open_outbox, self.run, "example-castings", disclosure)
        return ok, ga

    def test_refused_disclosure_opens_nothing(self):
        ok, ga = self.attempt({"allowed": True, "complete": False, "record": (403, {"error": "refused by law"})})
        self.assertFalse(ok)
        ga.assert_not_called()

    def test_held_disclosure_opens_nothing(self):
        ok, ga = self.attempt({"allowed": True, "complete": False, "record": (202, {"error": "held"})})
        self.assertFalse(ok)
        ga.assert_not_called()

    def test_gate_refused_disclosure_opens_nothing(self):
        ok, ga = self.attempt({"allowed": False, "complete": False, "record": None})
        self.assertFalse(ok)
        ga.assert_not_called()

    def test_200_without_entry_opens_nothing(self):
        ok, ga = self.attempt({"allowed": True, "complete": True, "record": (200, {})})
        self.assertFalse(ok)
        ga.assert_not_called()

    def test_landed_but_absent_from_topic_opens_nothing(self):
        ok, ga = self.attempt({"allowed": True, "complete": True, "record": LANDED}, topic=(200, {"posts": []}))
        self.assertFalse(ok)
        ga.assert_not_called()

    def test_landed_but_topic_unreadable_opens_nothing(self):
        for topic in ((0, {"error": "timeout"}), (-1, {"error": "malformed JSON"}), (200, {"posts": "nope"})):
            ok, ga = self.attempt({"allowed": True, "complete": True, "record": LANDED}, topic=topic)
            self.assertFalse(ok, topic)
            ga.assert_not_called()

    def test_landed_and_on_record_opens_the_outbox(self):
        ok, ga = self.attempt({"allowed": True, "complete": True, "record": LANDED})
        self.assertTrue(ok)
        ga.assert_called_once()
        self.assertEqual(ga.call_args[0][2][0]["id"], "BRIDGE-OPEN-EXAMPLE-CASTINGS")


class HeadsBridge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = make_run(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_failed_head_post_stops(self):
        for bad in ((403, {"error": "refused"}), (202, {"error": "held"}), (0, {"error": "timeout"}), (200, {})):
            self.run.s["expect"]["heads"] = []
            with mock.patch.object(D, "hub_head", return_value=(5, "ab" * 32)), \
                 mock.patch.object(D, "signed_event", return_value=bad) as se:
                ok = quiet(D.bridge_heads, self.run)
            self.assertFalse(ok, bad)
            self.assertEqual(se.call_count, 1, "must stop at the first failed post")
            self.assertEqual(self.run.s["expect"]["heads"], [])

    def test_unreadable_head_posts_nothing(self):
        with mock.patch.object(D, "hub_head", return_value=(0, "")), mock.patch.object(D, "signed_event") as se:
            self.assertFalse(quiet(D.bridge_heads, self.run))
        se.assert_not_called()

    def test_both_heads_land(self):
        with mock.patch.object(D, "hub_head", return_value=(5, "ab" * 32)), mock.patch.object(D, "signed_event", return_value=LANDED):
            self.assertTrue(quiet(D.bridge_heads, self.run))
        self.assertEqual([(h["child"], h["parent"]) for h in self.run.s["expect"]["heads"]], [("desk", "aic"), ("aic", "de-sandbox")])


class SuspendBridge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = make_run(self.tmp.name)
        self.aic = self.run.lct(AIC_LCT_KEY)

    def tearDown(self):
        self.tmp.cleanup()

    def attempt(self, removal, members, law_ok=True):
        with mock.patch.object(D, "http", return_value=members), \
             mock.patch.object(D, "gate_add") as ga, \
             mock.patch.object(D, "hub_set_law", return_value=(law_ok, 3, "" if law_ok else "law rejected")) as sl:
            res = quiet(D.bridge_suspend, self.run, removal)
        granted = [r["id"] for c in ga.call_args_list for r in c[0][2]]
        return res, granted, sl

    def test_failed_removal_changes_nothing(self):
        for removal in ((500, {"error": "boom"}), (0, {"error": "timeout"}), (403, "no"), None):
            res, granted, sl = self.attempt(removal, (200, {"members": []}))
            self.assertEqual(granted, [], removal)
            sl.assert_not_called()
            self.assertFalse(any(res.values()))

    def test_malformed_or_timed_out_member_list_changes_nothing(self):
        for members in ((0, {"error": "timed out"}), (-1, {"error": "malformed JSON"}), (200, {"members": "x"}),
                        (200, {"nope": []}), (200, {"members": [{"lct_id": 5}]}), (404, {"error": "not found"})):
            res, granted, sl = self.attempt((200, {"ok": True}), members)
            self.assertEqual(granted, [], members)
            sl.assert_not_called()
            self.assertFalse(res["removed"])

    def test_still_a_member_changes_nothing(self):
        res, granted, _ = self.attempt((200, {}), (200, {"members": [{"lct_id": self.aic}]}))
        self.assertEqual(granted, [])
        self.assertFalse(res["removed"])

    def test_membership_is_structured_not_substring(self):
        # the AIC's id appearing in some other member's text is not membership
        res, granted, _ = self.attempt((200, {}), (200, {"members": [{"lct_id": "someone-else", "name": f"formerly {self.aic}"}]}))
        self.assertTrue(res["removed"])

    def test_failed_law_update_grants_no_wind_down(self):
        res, granted, _ = self.attempt((200, {}), (200, {"members": []}), law_ok=False)
        self.assertEqual(granted, ["BRIDGE-SUSPENDED", "BRIDGE-SUSPENDED"])  # both gates stopped, nothing allowed
        self.assertTrue(res["gates_stopped"])
        self.assertFalse(res["law_narrowed"])
        self.assertFalse(res["wind_down_granted"])

    def test_full_cascade(self):
        res, granted, _ = self.attempt((200, {}), (200, {"members": []}))
        self.assertEqual(granted, ["BRIDGE-SUSPENDED", "BRIDGE-SUSPENDED", "BRIDGE-WIND-DOWN", "BRIDGE-WIND-DOWN"])
        self.assertTrue(all(res.values()))


class FakeGate:
    agent = "manager"

    def __init__(self, decision="allow"):
        self.decision, self.outcomes = decision, []

    def ask(self, tool, target, params=None):
        return "a1", {"decision": self.decision, "rule_id": "R"}

    def done(self, aid, ok, err=None, run=None):
        self.outcomes.append((aid, ok, err))
        if run is not None:
            run.expect()["gate_outcomes"].setdefault(self.agent, []).append({"action_id": aid, "success": bool(ok)})


class Act(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = make_run(self.tmp.name)
        self.run.ws.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_read_of_missing_file_fails(self):
        g = FakeGate()
        out = quiet(D.act, self.run, {"manager": g}, "manager", "Read", "nope/missing.md", "look")
        self.assertTrue(out["allowed"])
        self.assertFalse(out["complete"])
        self.assertFalse(g.outcomes[-1][1])

    def test_consequential_act_incomplete_unless_record_lands(self):
        for st in ((202, {"error": "held"}), (403, {"error": "refused"}), (0, {"error": "timeout"}), (200, {})):
            g = FakeGate()
            with mock.patch.object(D, "record", return_value=st):
                out = quiet(D.act, self.run, {"manager": g}, "manager", "Write", "contracts/drafts/x.md", "draft", rec=("contract_drafted", "x"))
            self.assertTrue(out["allowed"], st)
            self.assertFalse(out["complete"], st)
            self.assertFalse(g.outcomes[-1][1], st)

    def test_consequential_act_complete_when_record_lands(self):
        g = FakeGate()
        with mock.patch.object(D, "record", return_value=LANDED):
            out = quiet(D.act, self.run, {"manager": g}, "manager", "Write", "contracts/drafts/x.md", "draft", rec=("contract_drafted", "x"))
        self.assertTrue(out["complete"])
        self.assertTrue(g.outcomes[-1][1])

    def test_refused_act_is_neither_allowed_nor_complete(self):
        g = FakeGate("deny")
        with mock.patch.object(D, "record") as rec:
            out = quiet(D.act, self.run, {"manager": g}, "manager", "Write", "treasury/ledger.csv", "pay", rec=("treasury_transfer", "x"))
        self.assertEqual((out["allowed"], out["complete"]), (False, False))
        rec.assert_not_called()


class Audit(unittest.TestCase):
    """A fake, internally consistent run: three ledgers, two anchored heads, signed records, gate outcomes."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = run = make_run(self.tmp.name)
        self.ledgers = {}
        for soc, n in (("de-sandbox", 4), ("aic", 12), ("desk", 6)):
            (D.hub_dir(run, soc)).mkdir(parents=True)
            self.ledgers[soc] = [{"index": i, "entry_hash": f"{soc}-{i:02d}" + "0" * 40} for i in range(n)]
            self.write_ledger(soc)
        self.posts = {"aic": [], "desk": [], "de-sandbox": []}
        exp = run.s["expect"]
        for i, (soc, signer) in enumerate([("aic", "manager")] * 9 + [("desk", "procure")] * 3):
            line = f"act: thing_{i} detail"
            sig = run.key(signer).sign(line.encode()).hex()
            self.posts[soc].append({"post_id": f"p{i}", "body": f"{line}\nsigned-by: {run.lct(signer)}\nsig: {sig}"})
            idx = len([r for r in exp["records"] if r["soc"] == soc])
            exp["records"].append({"soc": soc, "signer": signer, "signed": True, "kind": f"thing_{i}",
                                   "entry_index": idx, "entry_hash": self.ledgers[soc][idx]["entry_hash"]})
        # heads: desk's head (5 entries) into aic at aic#10; aic's head (10 entries) into de-sandbox at #3
        for child, parent, n, at in (("desk", "aic", 5, 10), ("aic", "de-sandbox", 10, 3)):
            head = self.ledgers[child][n - 1]["entry_hash"]
            self.posts[parent].append({"post_id": f"h-{child}", "body": f"act: ledger_head {child} entries={n} head={head}"})
            exp["heads"].append({"parent": parent, "child": child, "entries": n, "head": head,
                                 "entry_index": at, "entry_hash": self.ledgers[parent][at]["entry_hash"]})
        exp["gate_outcomes"] = {"manager": [{"action_id": "m1", "success": True}, {"action_id": "m2", "success": False}],
                                "procure": [{"action_id": "p1", "success": True}]}
        self.chain = {"manager": [True, False], "procure": [True]}
        self.verify_out = {s: "Ledger verified: ok" for s in D.HUBS}
        run.save()

    def tearDown(self):
        self.tmp.cleanup()

    def write_ledger(self, soc):
        (D.hub_dir(self.run, soc) / "ledger.jsonl").write_text("\n".join(json.dumps(r) for r in self.ledgers[soc]) + "\n")

    def fake_http(self, method, url, body=None, token=None, timeout=20):
        for soc in D.HUBS:
            if url.endswith(f"/topics/topic-{soc}"):
                return 200, {"posts": self.posts[soc]}
        if "/members/" in url and url.endswith("/pubkey"):
            lct = url.split("/members/")[1].split("/")[0]
            for name in ("manager", "procure"):
                if self.run.lct(name) == lct:
                    return 200, {"pubkey_hex": self.run.pub(name)}
            return 404, {"error": "no such member"}
        if "/api/chain" in url:
            agent = next(a for a, (_, port) in D.GATES.items() if f":{port}/" in url)
            ents, h = [], "genesis"
            for i, ok in enumerate(self.chain[agent]):
                ents.append({"chain_position": i, "hash": f"h{i}", "prev_hash": h, "event_type": "outcome",
                             "plugin_id": f"aic-{agent}", "success": ok})
                h = f"h{i}"
            return 200, {"entries": ents, "read_error": None}
        return 404, {"error": url}

    def fake_run(self, args, **kw):
        soc = next(s for s in D.HUBS if str(D.hub_dir(self.run, s)) == args[2])
        out = self.verify_out[soc]
        return SimpleNamespace(returncode=0 if out.startswith("Ledger verified") else 1, stdout=out, stderr="")

    def audit(self):
        with mock.patch.object(D, "http", side_effect=self.fake_http), \
             mock.patch.object(D.subprocess, "run", side_effect=self.fake_run), \
             mock.patch.object(D, "hub_head", side_effect=lambda run, soc: (len(self.ledgers[soc]), self.ledgers[soc][-1]["entry_hash"])), \
             mock.patch.object(D, "operator_token", return_value="tok"):
            return quiet(D.audit, self.run)

    def test_consistent_run_passes_with_expected_counts(self):
        res = self.audit()
        self.assertEqual(res["failures"], [])
        self.assertTrue(res["ok"])
        c = res["checks"]
        self.assertEqual(c["ledgers_verified"], {"got": 3, "want": 3})
        self.assertEqual((c["heads_consistent"]["got"], c["heads_consistent"]["want"]), (2, 2))
        self.assertEqual((c["signatures_aic"]["got"], c["signatures_aic"]["want"]), (9, 9))
        self.assertTrue(json.loads((self.run.root / "audit.json").read_text())["ok"])

    def test_tampered_child_ledger_fails(self):
        self.ledgers["desk"][4]["entry_hash"] = "f" * 46  # the entry desk's anchored head points at
        self.write_ledger("desk")
        res = self.audit()
        self.assertFalse(res["ok"])
        self.assertTrue(any("desk's ledger.jsonl there has" in f for f in res["failures"]), res["failures"])

    def test_tampered_acknowledged_record_fails(self):
        self.ledgers["aic"][2]["entry_hash"] = "e" * 46
        self.write_ledger("aic")
        res = self.audit()
        self.assertFalse(res["ok"])
        self.assertTrue(any("not in its ledger.jsonl" in f for f in res["failures"]), res["failures"])

    def test_bad_in_body_signature_fails(self):
        body = self.posts["aic"][3]["body"]
        sig = body.rsplit("\nsig: ", 1)[1]
        self.posts["aic"][3]["body"] = body.replace(sig, ("0" if sig[0] != "0" else "1") + sig[1:])
        res = self.audit()
        self.assertFalse(res["ok"])
        self.assertEqual(res["checks"]["signatures_aic"]["invalid"], 1)

    def test_missing_signed_record_fails_on_count(self):
        self.posts["aic"].pop(0)
        res = self.audit()
        self.assertFalse(res["ok"])
        self.assertEqual((res["checks"]["signatures_aic"]["got"], res["checks"]["signatures_aic"]["want"]), (8, 9))

    def test_failed_verify_ledger_fails(self):
        self.verify_out["aic"] = "Ledger broken at entry 3: hash mismatch"
        res = self.audit()
        self.assertFalse(res["ok"])
        self.assertEqual(res["checks"]["ledgers_verified"]["got"], 2)

    def test_missing_gate_outcome_fails(self):
        self.chain["manager"] = [True]
        self.assertFalse(self.audit()["ok"])

    def test_missing_head_fails(self):
        self.run.s["expect"]["heads"].pop()
        self.posts["de-sandbox"] = []
        res = self.audit()
        self.assertFalse(res["ok"])
        self.assertTrue(any("2 expected" in f for f in res["failures"]), res["failures"])

    def test_no_story_fails(self):
        self.run.s.pop("expect")
        self.assertFalse(self.audit()["ok"])

    def test_audit_command_exits_nonzero_on_failure(self):
        self.verify_out["desk"] = "Ledger broken"
        with mock.patch.object(D, "http", side_effect=self.fake_http), \
             mock.patch.object(D.subprocess, "run", side_effect=self.fake_run), \
             mock.patch.object(D, "hub_head", side_effect=lambda run, soc: (len(self.ledgers[soc]), self.ledgers[soc][-1]["entry_hash"])), \
             mock.patch.object(D, "operator_token", return_value="tok"), \
             mock.patch.object(sys, "argv", ["aic_demo.py", "audit", str(self.run.root), "--json"]):
            buf = io.StringIO()
            with redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
                D.main()
        self.assertEqual(cm.exception.code, 1)
        self.assertFalse(json.loads(buf.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
