"""Offline checks for SEC selection, missing facts, and unsupported-number detection."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".agents/skills/buffett-investor"))
from sec_buffett import check_all, choose, compute, unsupported_numbers


def fact(val, end, start=None, filed="2026-10-01"):
    d = {"val": val, "end": end, "filed": filed, "form": "10-K"}
    if start:
        d["start"] = start
    return d


class Lab18Tests(unittest.TestCase):
    def test_latest_filing_and_tag_precedence(self):
        cf = {"facts": {"us-gaap": {
            "Revenues": {"units": {"USD": [fact(500, "2026-08-30", "2025-09-01")]}},
            "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [
                fact(100, "2026-08-30", "2025-09-01", "2026-09-01"),
                fact(101, "2026-08-30", "2025-09-01", "2026-10-01")]}}}}}
        self.assertEqual(choose(cf, ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"),
                                "2026-08-30", True)["value"], 101)

    def test_missing_and_negative_equity(self):
        ends = ["2022-08-28", "2023-09-03", "2024-09-01", "2025-08-31", "2026-08-30"]
        starts = ["2021-08-30", "2022-08-29", "2023-09-04", "2024-09-02", "2025-09-01"]
        rows = lambda annual: [fact(1_000_000, e, s if annual else None)
                               for e, s in zip(ends, starts)]
        cf = {"entityName": "Synthetic", "facts": {"us-gaap": {
            "NetIncomeLoss": {"units": {"USD": rows(True)}},
            "StockholdersEquity": {"units": {"USD": [dict(r, val=-1) for r in rows(False)]}},
            "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": rows(True)}}}}}
        r = compute(cf)
        self.assertEqual(r["checks"]["ROE >= 15% every year"], "not known")
        self.assertEqual(r["checks"]["Owner earnings positive every year"], "not known")
        self.assertIsNone(r["rows"][0]["metrics"]["owner_earnings"]["value"])

    def test_memo_guard(self):
        result = {"rows": [{"fy_end": "2026-08-30", "metrics": {
            "roe": {"value": 25.8}, "owner_earnings": {"value": 9_382_000_000}}}]}
        self.assertEqual(unsupported_numbers("ROE 25.8% and owner earnings 9,382", result), [])
        self.assertEqual(unsupported_numbers("ROE 40.0%", result), ["40.0%"])


if __name__ == "__main__":
    unittest.main()
