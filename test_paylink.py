#!/usr/bin/env python3
"""Minimal tests for paylink (stdlib unittest)."""
import unittest

import paylink


class TestPaylink(unittest.TestCase):
    def test_normalize(self):
        a = "0xbAd41cF0f0d5442f9A53630F8081BFd257DA019b"
        self.assertEqual(paylink._normalize_address(a), a)
        with self.assertRaises(ValueError):
            paylink._normalize_address("not-an-address")

    def test_atomic(self):
        self.assertEqual(paylink.usd_to_atomic("5"), 5_000_000)
        self.assertEqual(paylink.usd_to_atomic("7.50"), 7_500_000)
        self.assertEqual(paylink.usd_to_atomic("0.01"), 10_000)

    def test_eip681(self):
        to = "0xbAd41cF0f0d5442f9A53630F8081BFd257DA019b"
        uri = paylink.eip681_usdc_transfer(to, "5")
        self.assertIn("@8453/transfer", uri)
        self.assertIn("uint256=5000000", uri)
        self.assertIn(paylink.USDC_BASE, uri)
        self.assertIn(to, uri)

    def test_bundle(self):
        b = paylink.build_bundle(
            "0xbAd41cF0f0d5442f9A53630F8081BFd257DA019b", "3"
        )
        self.assertEqual(b["amount_atomic"], 3_000_000)
        self.assertTrue(b["eip681"].startswith("ethereum:"))
        self.assertIn("metamask.app.link", b["metamask_deeplink"])


if __name__ == "__main__":
    unittest.main()
