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

    def test_costco_instructor_reference(self):
        # Fixture taken from the published Lab 18 table (USD millions);
        # verifies the calculations, not the live SEC endpoint.
        years = [
            ("2022-08-28", "2021-08-30", 226954, 5844, 7392, 3891, 20642, 3501),
            ("2023-09-03", "2022-08-29", 242290, 6292, 11068, 4323, 25058, 6745),
            ("2024-09-01", "2023-09-04", 254453, 7367, 11339, 4710, 23622, 6629),
            ("2025-08-31", "2024-09-02", 275235, 8099, 13335, 5498, 29164, 7837),
            ("2026-08-30", "2025-09-01", 303154, 9226, 15817, 6435, 35803, 9382),
        ]
        def flow(column):
            return [fact(rec[column] * 1_000_000, rec[0], rec[1]) for rec in years]
        def instant(column):
            return [fact(rec[column] * 1_000_000, rec[0]) for rec in years]
        data = {"entityName": "Costco", "facts": {"us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": flow(2)}},
            "NetIncomeLoss": {"units": {"USD": flow(3)}},
            "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": flow(4)}},
            "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": flow(5)}},
            "StockholdersEquity": {"units": {"USD": instant(6)}},
        }}}
        result = compute(data)
        self.assertEqual(list(result["checks"].values()), ["pass", "pass", "pass"])
        for expected, actual in zip(years, result["rows"]):
            self.assertEqual(actual["fy_end"], expected[0])
            self.assertAlmostEqual(actual["metrics"]["owner_earnings"]["value"] / 1e6, expected[7])
            self.assertAlmostEqual(actual["metrics"]["roe"]["value"], expected[3] / expected[6] * 100)


if __name__ == "__main__":
    unittest.main()
