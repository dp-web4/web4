#!/usr/bin/env python3
"""Tests for the ingestion passage/tag contract (no model load — pure shape).

Run: membot/.venv/bin/python -m pytest web4/hub/membox/test_ingest.py
 or: python3 web4/hub/membox/test_ingest.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from ingest import member_passage, member_tags  # noqa: E402


def test_passage_is_prose_not_schema():
    m = {
        "lct_id": "657b6bc9-ada",
        "name": "Ada",
        "skills": ["diffusion fine-tuning", "eval design"],
        "profile": {"interests": "mechanistic interpretability"},
    }
    p = member_passage(m)
    # Prose, member's own words — no "Skills:"/"Interests:" schema labels.
    assert p.startswith("Ada. ")
    assert "diffusion fine-tuning" in p and "mechanistic interpretability" in p
    assert "Skills:" not in p and "Interests:" not in p


def test_pair_purpose_tail_when_known():
    m = {"lct_id": "x", "name": "Bem", "skills": ["Rust"],
         "profile": {"last_pair_purpose": "co-debugging a ledger sync"}}
    p = member_passage(m)
    assert p.endswith("Recent pair purposes: co-debugging a ledger sync.")


def test_name_only_when_no_profile():
    m = {"lct_id": "y", "name": "sprout", "skills": [], "profile": {}}
    assert member_passage(m) == "sprout."


def test_tags_carry_forward_compat_provenance():
    m = {"lct_id": "657b6bc9", "name": "Ada", "skills": ["x"],
         "profile": {"last_pair_purpose": "thing"}}
    t = member_tags(m, member_passage(m))
    # The three forward-compat fields Waving Cat asked for (item 2).
    assert t["member_lct"] == "657b6bc9"
    assert t["name"] == "Ada"
    assert t["last_pair_purpose"] == "thing"
    assert len(t["profile_version"]) == 12  # content hash → changes with profile


def test_profile_version_changes_with_content():
    m1 = {"lct_id": "z", "name": "C", "skills": ["a"], "profile": {}}
    m2 = {"lct_id": "z", "name": "C", "skills": ["a", "b"], "profile": {}}
    assert member_tags(m1, member_passage(m1))["profile_version"] != \
        member_tags(m2, member_passage(m2))["profile_version"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
