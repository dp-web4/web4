"""Offline conformance for transport-neutral notice reply addresses.

Run: python3 -m unittest discover -s hub/mesh -p 'test_*.py'
"""
import unittest
from reply_target import InvalidNoticeAddress, ReplyTarget, select_reply_target


class ReplyTargetTests(unittest.TestCase):
    CANONICAL = "lct:web4:mb32:b" + "a" * 52

    def test_legacy_router_only(self):
        self.assertEqual(
            select_reply_target({"from": "router-member-uuid"}),
            ReplyTarget("hub_member", "router-member-uuid"),
        )

    def test_child_author_does_not_reply_to_router(self):
        self.assertEqual(
            select_reply_target({"from": "router-member-uuid", "from_lct": self.CANONICAL}),
            ReplyTarget("canonical_lct", self.CANONICAL),
        )

    def test_present_but_malformed_author_is_never_a_fallback(self):
        for bad in [None, "", "router-member-uuid", "lct:web4:member:legacy", 7,
                    "lct:web4:mb32:b" + "0" * 52, self.CANONICAL + "suffix"]:
            with self.subTest(bad=bad):
                with self.assertRaises(InvalidNoticeAddress):
                    select_reply_target({"from": "router-member-uuid", "from_lct": bad})

    def test_missing_or_ambiguous_transport_sender_is_refused(self):
        for bad in [None, "", " ", " router ", 7]:
            with self.subTest(bad=bad):
                with self.assertRaises(InvalidNoticeAddress):
                    select_reply_target({"from": bad, "from_lct": self.CANONICAL})

    def test_empty_notice_and_invalid_shape_fail_closed(self):
        with self.assertRaises(InvalidNoticeAddress):
            select_reply_target({})


if __name__ == "__main__":
    unittest.main()
