#!/usr/bin/env python3
"""Zero-dependency regression: the public preview must not masquerade as a live community."""
from pathlib import Path
import unittest

PAGE = Path(__file__).with_name("index.html")

class PublicSiteTests(unittest.TestCase):
    def test_public_readable_without_js_or_login(self):
        html = PAGE.read_text()
        self.assertIn('<html lang="en">', html)
        self.assertIn('name="viewport"', html)
        self.assertNotIn("<script", html.lower())
        self.assertNotIn('type="password"', html.lower())

    def test_truthful_nonoperational_state(self):
        html = PAGE.read_text()
        self.assertIn("Preview, not a live community", html)
        self.assertIn("There is deliberately no fake Join button", html)
        self.assertIn("does not connect to a Hub daemon", html)
        self.assertNotIn("/admin/api/", html)
        self.assertNotIn("localStorage", html)

if __name__ == "__main__":
    unittest.main()
