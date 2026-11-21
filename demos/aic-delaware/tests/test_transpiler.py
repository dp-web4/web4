# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
"""Counterexamples for tighten-only and for the compiler's blocker semantics (Nova's review of #994).

Each test mutates a copy of the demo rulebook in memory, so nothing on disk changes. The oracle used here is the
transpiler's reference oracle; tests/live_engine_probe.py runs the priority/overlap cases through the real engines.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO / "tools"))
import rulebook_to_web4 as T  # noqa: E402

RB_PATH = DEMO / "rulebook" / "effortless-rulebook" / "aic-rulebook.json"
EXC_PATH = DEMO / "rulebook" / "known-exceptions.json"
BASE = json.loads(RB_PATH.read_text(encoding="utf-8"))
WS = "/run/workspace"


def rulebook():
    return copy.deepcopy(BASE)


def norm(rb, nid):
    return next(n for n in rb["Norms"]["data"] if n["NormId"] == nid)


def add(rb, src, **kw):
    n = dict(norm(rb, src), **kw)
    rb["Norms"]["data"].append(n)
    return n


def kinds(findings):
    return [f[1] for f in findings if f[0] == "blocking"]


def gate(norms, tool, rel):
    """Decision of the flattened Hestia projection (what the gate runs) for one act."""
    cfg, ov = T.hestia_configs(norms, "candidate")
    return T.hestia_eval(cfg, ov, {"tool": tool, "target": f"{WS}/{rel}"})


def hub(norms, body):
    return T.hub_eval([n for n in norms if n["Surface"] == "hub-norm"], [], {"action": "add_post", "payload": {"body": body}})


class TightenOnly(unittest.TestCase):
    def test_clean_rulebook_has_no_tighten_only_findings(self):
        for soc in ("de-sandbox", "aic", "desk", "h-manager", "h-procure"):
            for mode in ("candidate", "ratified"):
                _, f = T.effective_norms(rulebook(), soc, mode)
                self.assertEqual(kinds(f), [], (soc, mode))

    def test_narrower_child_deny_cannot_replace_parent_deny(self):
        """Nova's negative test. The parent denies all counterparty contact without disclosure; a child deny that
        overrides it names one counterparty only. The parent must still deny all the others."""
        rb = rulebook()
        add(rb, "DE-DISCLOSE-FIRST", NormId="OA-DISCLOSE-METALS", Society="aic", Overrides="DE-DISCLOSE-FIRST",
            HestiaTargetPattern="**/counterparties/example-metals/outbox/**", Priority=95)
        norms, f = T.effective_norms(rb, "h-manager", "candidate")
        self.assertIn("ChildOverrideNotProvenNoLooser", kinds(f))
        ids = {n["NormId"] for n in norms}
        self.assertIn("DE-DISCLOSE-FIRST", ids)
        self.assertNotIn("OA-DISCLOSE-METALS", ids)
        for cp in ("example-castings", "example-freight", "example-metals"):
            self.assertEqual(gate(norms, "Write", f"counterparties/{cp}/outbox/hello.md"), ("deny", "DE-DISCLOSE-FIRST"), cp)
        # the counterexample is real: had the replacement been accepted (the old behaviour), castings would be open
        old = [n for n in norms if n["NormId"] != "DE-DISCLOSE-FIRST"] + [norm(rb, "OA-DISCLOSE-METALS")]
        self.assertEqual(gate(old, "Write", "counterparties/example-castings/outbox/hello.md")[0], "allow")

    def test_narrower_child_deny_cannot_replace_parent_hub_norm(self):
        rb = rulebook()
        add(rb, "DE-ESC-UNDISCLOSED-CONTACT", NormId="AIC-UNDISCLOSED-METALS", Society="aic", Overrides="DE-ESC-UNDISCLOSED-CONTACT",
            Value="^act: counterparty_contact_undisclosed example-metals\\b", Priority=90)
        norms, f = T.effective_norms(rb, "aic", "candidate")
        self.assertIn("ChildOverrideNotProvenNoLooser", kinds(f))
        self.assertEqual(hub(norms, "act: counterparty_contact_undisclosed example-freight"), ("deny", "DE-ESC-UNDISCLOSED-CONTACT"))
        self.assertEqual(hub(norms, "act: counterparty_contact_undisclosed example-metals"), ("deny", "DE-ESC-UNDISCLOSED-CONTACT"))

    def test_allow_side_higher_ranked_identical_allow_cannot_replace(self):
        """Allow-side variant: a child re-declares the parent's allow with the same predicate but a priority that
        outranks the disclosure deny. Severity ties, so the old code accepted it and opened the outbox undisclosed."""
        rb = rulebook()
        add(rb, "OA-LISTED-CASTINGS", NormId="DESK-LISTED-CASTINGS", Society="desk", Overrides="OA-LISTED-CASTINGS", Priority=99)
        norms, f = T.effective_norms(rb, "h-manager", "candidate")
        self.assertIn("ChildOverrideNotProvenNoLooser", kinds(f))
        self.assertEqual(gate(norms, "Write", "counterparties/example-castings/outbox/rfq.md"), ("deny", "DE-DISCLOSE-FIRST"))
        old = [n for n in norms if n["NormId"] != "OA-LISTED-CASTINGS"] + [norm(rb, "DESK-LISTED-CASTINGS")]
        self.assertEqual(gate(old, "Write", "counterparties/example-castings/outbox/rfq.md"), ("allow", "DESK-LISTED-CASTINGS"))

    def test_allow_side_narrower_or_broader_allow_cannot_replace(self):
        for pat in ("**/counterparties/example-castings/outbox/**", "**/counterparties/**"):
            rb = rulebook()
            add(rb, "OA-LISTED-CASTINGS", NormId="DESK-LISTED-X", Society="desk", Overrides="OA-LISTED-CASTINGS", HestiaTargetPattern=pat)
            norms, f = T.effective_norms(rb, "h-manager", "candidate")
            self.assertIn("ChildOverrideNotProvenNoLooser", kinds(f), pat)
            self.assertIn("OA-LISTED-CASTINGS", {n["NormId"] for n in norms})
            self.assertEqual(gate(norms, "Read", "counterparties/example-metals/notes.md"), ("deny", "OA-UNLISTED"), pat)

    def test_child_allow_outranking_parent_deny_is_blocking(self):
        """No Overrides at all: a plain child allow ranked above an ancestor deny on overlapping acts. The flattened
        law (what the engines run) loosens the parent; the strictest fold does not. Both the static check and the
        fold check catch it."""
        rb = rulebook()
        add(rb, "OA-LISTED-CASTINGS", NormId="OA-CASTINGS-OUTBOX", HestiaTargetPattern="**/counterparties/example-castings/outbox/**", Priority=99)
        norms, f = T.effective_norms(rb, "h-manager", "candidate")
        self.assertIn("ChildNormOutranksParent", kinds(f))
        req = {"tool": "Write", "target": f"{WS}/counterparties/example-castings/outbox/rfq.md"}
        cfg, ov = T.hestia_configs(norms, "candidate")
        self.assertEqual(T.hestia_eval(cfg, ov, req)[0], "allow")  # flattened: loosened
        self.assertEqual(T.fold_eval(norms, T.chain_of(rb, "h-manager"), "hestia", req)[0], "deny")  # fold: parent holds

    def test_priority_tie_counts_as_outranking(self):
        rb = rulebook()
        add(rb, "OA-LISTED-CASTINGS", NormId="OA-CASTINGS-TIE", HestiaTargetPattern="**/counterparties/example-castings/outbox/**", Priority=95)
        _, f = T.effective_norms(rb, "h-manager", "candidate")
        self.assertIn("ChildNormOutranksParent", kinds(f))

    def test_hub_child_allow_outranking_parent_deny_is_blocking(self):
        rb = rulebook()
        add(rb, "DE-ESC-UNDISCLOSED-CONTACT", NormId="AIC-CONTACT-OK", Society="aic", Decision="allow", Priority=95,
            Value="^act: counterparty_contact_undisclosed example-castings\\b")
        _, f = T.effective_norms(rb, "aic", "candidate")
        self.assertIn("ChildNormOutranksParent", kinds(f))

    def test_disjoint_tools_do_not_count_as_overlap(self):
        rb = rulebook()
        add(rb, "OA-NO-EGRESS-WEB", NormId="DESK-WEB-OK", Society="desk", Decision="allow", Priority=99, HestiaTools='["WebFetch"]')
        _, f = T.effective_norms(rb, "h-manager", "candidate")
        outranks = [d for s, k, d in f if k == "ChildNormOutranksParent" and "DESK-WEB-OK" in d]
        # DE-DISCLOSE-FIRST (Write/Edit) and OA-NO-TREASURY (Read/Write/Edit/Bash) share no tool with WebFetch
        self.assertFalse([d for d in outranks if "DE-DISCLOSE-FIRST" in d or "OA-NO-TREASURY" in d], outranks)
        # OA-NO-EGRESS-WEB (deny WebFetch/WebSearch, 94) does overlap, so that pair IS flagged
        self.assertTrue([d for d in outranks if "OA-NO-EGRESS-WEB" in d], outranks)

    def test_identical_or_broader_stricter_replacement_is_accepted(self):
        for kw in ({"Priority": 98},
                   {"Priority": 95, "HestiaTargetPattern": "**/counterparties/**", "HestiaTools": '["Write", "Edit", "Read"]'}):
            rb = rulebook()
            add(rb, "DE-DISCLOSE-FIRST", NormId="OA-DISCLOSE-ALL", Society="aic", Overrides="DE-DISCLOSE-FIRST", **kw)
            norms, f = T.effective_norms(rb, "h-manager", "candidate")
            self.assertNotIn("ChildOverrideNotProvenNoLooser", kinds(f), kw)
            ids = {n["NormId"] for n in norms}
            self.assertIn("OA-DISCLOSE-ALL", ids)
            self.assertNotIn("DE-DISCLOSE-FIRST", ids)
            self.assertEqual(gate(norms, "Write", "counterparties/example-freight/outbox/x.md"), ("deny", "OA-DISCLOSE-ALL"))

    def test_lower_priority_replacement_is_rejected(self):
        rb = rulebook()
        add(rb, "DE-DISCLOSE-FIRST", NormId="OA-DISCLOSE-LOW", Society="aic", Overrides="DE-DISCLOSE-FIRST", Priority=10)
        _, f = T.effective_norms(rb, "h-manager", "candidate")
        self.assertIn("ChildOverrideNotProvenNoLooser", kinds(f))

    def test_widening_override_is_rejected(self):
        """Clause 2.3 with its conflict overruled: an allow overriding the parent's deny."""
        rb = rulebook()
        norm(rb, "OA-REPEAT-NO-DISCLOSURE")["CompileMode"] = "shadow"
        norms, f = T.effective_norms(rb, "h-manager", "candidate")
        self.assertIn("ChildOverrideWidensParent", kinds(f))
        self.assertEqual(gate(norms, "Write", "counterparties/example-castings/outbox/x.md"), ("deny", "DE-DISCLOSE-FIRST"))

    def test_glob_cover_is_sound_on_edge_cases(self):
        self.assertTrue(T.glob_covers("**/counterparties/**", "**/counterparties/*/outbox/**"))
        self.assertTrue(T.glob_covers(None, "**/x/**"))
        self.assertFalse(T.glob_covers("a*b", "a*"))
        self.assertFalse(T.glob_covers("**/counterparties/*/outbox/**", "**/counterparties/**"))
        self.assertFalse(T.glob_covers("**/x?/**", "**/xa/**"))  # '?' patterns: equality only
        self.assertFalse(T.glob_covers("**/x/**", None))


class CompilerExit(unittest.TestCase):
    def run_t(self, rb, exc=True):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "rb.json"
            src.write_text(json.dumps(rb), encoding="utf-8")
            args = [sys.executable, str(DEMO / "tools" / "rulebook_to_web4.py"), str(src), str(Path(t) / "out")]
            if exc:
                args += ["--known-exceptions", str(EXC_PATH)]
            p = subprocess.run(args, capture_output=True, text=True)
            mf = json.loads((Path(t) / "out" / "manifest.json").read_text())
            return p.returncode, mf, p.stderr

    def test_clean_rulebook_with_allowlist_exits_0(self):
        code, mf, _ = self.run_t(rulebook())
        self.assertEqual(code, 0)
        self.assertTrue(mf["activation_allowed"])
        self.assertEqual([b["kind"] for b in mf["blocking"]["known"]], ["NormRefusedRuleConflicted"])
        self.assertEqual(mf["blocking"]["unexpected"], [])

    def test_known_conflict_without_allowlist_exits_1(self):
        code, mf, err = self.run_t(rulebook(), exc=False)
        self.assertEqual(code, 1)
        self.assertFalse(mf["activation_allowed"])
        self.assertIn("NormRefusedRuleConflicted", err)

    def test_unexpected_blocking_exits_1_even_with_allowlist(self):
        rb = rulebook()
        add(rb, "DE-DISCLOSE-FIRST", NormId="OA-DISCLOSE-METALS", Society="aic", Overrides="DE-DISCLOSE-FIRST",
            HestiaTargetPattern="**/counterparties/example-metals/outbox/**")
        code, mf, err = self.run_t(rb)
        self.assertEqual(code, 1)
        self.assertFalse(mf["activation_allowed"])
        self.assertIn("ChildOverrideNotProvenNoLooser", err)

    def test_overruled_clause_2_3_is_not_covered_by_its_allowlist_entry(self):
        rb = rulebook()
        norm(rb, "OA-REPEAT-NO-DISCLOSURE")["CompileMode"] = "shadow"
        code, mf, _ = self.run_t(rb)
        self.assertEqual(code, 1)
        self.assertIn("ChildOverrideWidensParent", [b["kind"] for b in mf["blocking"]["unexpected"]])

    def test_allowlist_entry_needs_a_reason(self):
        with tempfile.TemporaryDirectory() as t:
            bad = Path(t) / "exc.json"
            bad.write_text(json.dumps({"exceptions": [{"kind": "NormRefusedRuleConflicted", "norm": "OA-REPEAT-NO-DISCLOSURE"}]}))
            with self.assertRaises(SystemExit):
                T.load_exceptions(bad)

    def test_corpus_flattened_equals_fold(self):
        code, mf, _ = self.run_t(rulebook())
        self.assertNotIn("FlattenedLawDiffersFromFold", [b["kind"] for b in mf["blocking"]["unexpected"]])


if __name__ == "__main__":
    unittest.main()
