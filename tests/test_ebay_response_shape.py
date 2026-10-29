"""Fail-closed regression tests for eBay Browse search response shape.

Offline only: no HTTP requests, API credentials, or production data.
Run: python3 -m unittest discover -s tests -p 'test_ebay_response_shape.py'
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app"))

from schnapper.ebay import EbayFehler, zeilen_aus_antwort


class BrowseResponseShapeTests(unittest.TestCase):
    def test_zero_results_may_omit_item_list(self):
        rows, notes = zeilen_aus_antwort({"total": 0})
        self.assertEqual((rows, notes), ([], []))

    def test_zero_results_may_have_null_item_list(self):
        rows, notes = zeilen_aus_antwort({"total": 0, "itemSummaries": None})
        self.assertEqual((rows, notes), ([], []))

    def test_positive_total_without_item_list_is_error(self):
        with self.assertRaises(EbayFehler):
            zeilen_aus_antwort({"total": 2})

    def test_positive_total_with_null_item_list_is_error(self):
        with self.assertRaises(EbayFehler):
            zeilen_aus_antwort({"total": 2, "itemSummaries": None})

    def test_unknown_total_without_item_list_is_error(self):
        with self.assertRaises(EbayFehler):
            zeilen_aus_antwort({})

    def test_boolean_or_string_zero_without_list_is_error(self):
        for total in (False, "0", 0.0):
            with self.subTest(total=total), self.assertRaises(EbayFehler):
                zeilen_aus_antwort({"total": total})

    def test_explicit_empty_list_still_accepted(self):
        rows, notes = zeilen_aus_antwort({"total": 0, "itemSummaries": []})
        self.assertEqual((rows, notes), ([], []))

    def test_explicit_empty_list_with_positive_total_is_error(self):
        # Regression: the prior guard covered missing/null lists only.
        with self.assertRaises(EbayFehler):
            zeilen_aus_antwort({"total": 2, "itemSummaries": []})

    def test_explicit_empty_list_requires_strict_integer_zero(self):
        for total in (None, False, "0", 0.0, -1):
            with self.subTest(total=total), self.assertRaises(EbayFehler):
                zeilen_aus_antwort({"total": total, "itemSummaries": []})

    def test_explicit_empty_list_without_total_is_error(self):
        with self.assertRaises(EbayFehler):
            zeilen_aus_antwort({"itemSummaries": []})


if __name__ == "__main__":
    unittest.main()
