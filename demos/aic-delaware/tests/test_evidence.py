# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
"""The published run (evidence/) and the answers page built from it (ANSWERS.md).

- The evidence verifies offline (check_evidence.py), and the checker fails on tampering, so a pass means something.
- ANSWERS.md is exactly what capture.py renders from the evidence: the page can't drift from the run it quotes.
- Nothing machine-local leaks into what is published.
No daemons. Needs `cryptography`."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO))
import capture as C  # noqa: E402
import check_evidence as CE  # noqa: E402

EV = DEMO / "evidence"


class PublishedEvidence(unittest.TestCase):
    def test_evidence_verifies_offline(self):
        res = CE.check(EV)
        self.assertTrue(res["ok"], res["failures"])
        self.assertEqual(set(res["ledgers"]), {"de-sandbox", "aic", "desk"})
        self.assertTrue(all(h["consistent"] for h in res["heads"]))
        self.assertEqual(len(res["heads"]), 2)
        self.assertGreater(res["agent_signatures"]["aic"]["valid"], 0)
        self.assertEqual(res["agent_signatures"]["aic"]["invalid"], 0)
        self.assertTrue(all(g["acts"] > 0 for g in res["gates"].values()))

    def test_answers_page_is_what_the_evidence_renders(self):
        self.assertEqual((DEMO / "ANSWERS.md").read_text(encoding="utf-8"), C.rendered(),
                         "ANSWERS.md is stale: run `python3 capture.py render`")

    def test_nothing_machine_local_is_published(self):
        for p in list(EV.rglob("*")) + [DEMO / "ANSWERS.md"]:
            if p.is_file():
                text = p.read_text(encoding="utf-8", errors="replace")
                for marker in ("/home/", "/Users/", "claude-1000", "C:\\\\"):
                    self.assertNotIn(marker, text, f"{p.relative_to(DEMO)} holds a machine-local path ({marker})")

    def test_no_secret_material_is_published(self):
        for p in EV.rglob("*"):
            if p.is_file():
                text = p.read_text(encoding="utf-8", errors="replace")
                for marker in ('"seed"', "private_key", "secret_hex", "PRIVATE KEY", "passphrase"):
                    self.assertNotIn(marker, text, f"{p.relative_to(DEMO)} mentions {marker}")


class CheckerFailsOnTampering(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ev = self.tmp / "evidence"
        shutil.copytree(EV, self.ev)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def lines(self, rel):
        return (self.ev / rel).read_text(encoding="utf-8").splitlines()

    def write(self, rel, lines):
        (self.ev / rel).write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_an_edited_record_fails(self):
        rows = self.lines("ledgers/aic.jsonl")
        i = next(n for n, l in enumerate(rows) if "act: counterparty_disclosed" in l)
        rows[i] = rows[i].replace("counterparty_disclosed", "counterparty_disclosed_", 1)
        self.write("ledgers/aic.jsonl", rows)
        res = CE.check(self.ev)
        self.assertFalse(res["ok"])
        self.assertTrue(any("does not match its entry hash" in f for f in res["failures"]))

    def test_a_rehashed_edit_still_fails_on_the_hub_signature(self):
        """Edit a record and recompute its entry hash: the hub's signature no longer verifies, and the next entry no
        longer links to it."""
        rows = self.lines("ledgers/aic.jsonl")
        i = next(n for n, l in enumerate(rows) if "act: counterparty_disclosed" in l)
        e = json.loads(rows[i])
        edited = rows[i].replace("counterparty_disclosed", "counterparty_ignored", 1)
        new_hash = __import__("hashlib").sha256(CE._clear_last(edited, "entry_hash", e["entry_hash"]).encode()).hexdigest()
        rows[i] = edited.replace(e["entry_hash"], new_hash)
        self.write("ledgers/aic.jsonl", rows)
        res = CE.check(self.ev)
        self.assertFalse(res["ok"])
        self.assertTrue(any("the hub's signature does not verify" in f for f in res["failures"]))
        self.assertTrue(any("does not link to the entry before it" in f for f in res["failures"]))

    def test_a_truncated_child_ledger_fails_the_parent_head(self):
        rows = self.lines("ledgers/desk.jsonl")
        self.write("ledgers/desk.jsonl", rows[:5])
        res = CE.check(self.ev)
        self.assertFalse(res["ok"])
        self.assertTrue(any("holds desk's head" in f for f in res["failures"]))

    def test_a_forged_agent_signature_fails(self):
        """Swap the manager's in-body signature for another record's: the agent-signature check names it, on top of the
        hub's own hash and signature checks."""
        rows = self.lines("ledgers/aic.jsonl")
        signed = [n for n, l in enumerate(rows) if "\\nsig: " in l]
        a, b = json.loads(rows[signed[0]]), json.loads(rows[signed[1]])
        sig_a = a["event"]["body"].rsplit("\nsig: ", 1)[1]
        sig_b = b["event"]["body"].rsplit("\nsig: ", 1)[1]
        rows[signed[0]] = rows[signed[0]].replace(sig_a, sig_b)
        self.write("ledgers/aic.jsonl", rows)
        res = CE.check(self.ev)
        self.assertFalse(res["ok"])
        self.assertTrue(any("the agent's own signature does not verify" in f for f in res["failures"]))

    def test_a_broken_gate_link_fails(self):
        seg = json.loads((self.ev / "gates" / "manager.segment.json").read_text())
        seg["entries"][5]["prev_hash"] = "00" * 32
        (self.ev / "gates" / "manager.segment.json").write_text(json.dumps(seg))
        res = CE.check(self.ev)
        self.assertFalse(res["ok"])
        self.assertTrue(any("gate manager" in f and "broken" in f for f in res["failures"]))

    def test_a_failed_audit_fails(self):
        audit = json.loads((self.ev / "audit.json").read_text())
        audit["ok"] = False
        (self.ev / "audit.json").write_text(json.dumps(audit))
        self.assertFalse(CE.check(self.ev)["ok"])


if __name__ == "__main__":
    unittest.main()
