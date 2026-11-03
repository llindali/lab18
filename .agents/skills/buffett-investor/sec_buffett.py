"""SEC EDGAR 10-K-only Buffett classroom metrics. No paid APIs, no guessed data."""
import argparse
import os
import re
from datetime import date

import requests

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
TAGS = {
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"),
    "net_income": ("NetIncomeLoss",),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",),
    "capital_spending": ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"),
    "equity": ("StockholdersEquity",),
}


def sec_session():
    agent = os.getenv("SEC_USER_AGENT", "").strip()
    if not agent or "@" not in agent or not re.search(r"\S+@\S+\.\S+", agent):
        raise ValueError("Set SEC_USER_AGENT to your real name and email before requesting SEC data.")
    session = requests.Session()
    session.headers.update({"User-Agent": agent, "Accept-Encoding": "gzip, deflate"})
    return session


def fetch_company(ticker, session=None):
    session = session or sec_session()
    response = session.get(TICKERS_URL, timeout=30)
    response.raise_for_status()
    lookup = response.json()
    match = next((row for row in lookup.values() if row["ticker"].upper() == ticker.upper()), None)
    if match is None:
        raise ValueError(f"Ticker {ticker.upper()} not found in SEC company_tickers.json")
    response = session.get(FACTS_URL.format(cik=int(match["cik_str"])), timeout=30)
    response.raise_for_status()
    return response.json()


def observations(companyfacts, tags, annual):
    """Yield observations with requested tag in precedence order (form 10-K only)."""
    taxonomy = companyfacts.get("facts", {}).get("us-gaap", {})
    for tag in tags:
        items = taxonomy.get(tag, {}).get("units", {}).get("USD", [])
        for item in items:
            if item.get("form") != "10-K" or "end" not in item or "val" not in item:
                continue
            if annual:
                if "start" not in item:
                    continue
                try:
                    days = (date.fromisoformat(item["end"]) - date.fromisoformat(item["start"])).days
                except ValueError:
                    continue
                if not 330 <= days <= 380:
                    continue
            else:
                if "start" in item:  # balance-sheet item must be an instant
                    continue
            yield tag, item


def choose(companyfacts, tags, end, annual):
    """Respect tag priority, then latest filing for the same end/period."""
    for tag in tags:
        possible = [(t, d) for t, d in observations(companyfacts, (tag,), annual) if d["end"] == end]
        if possible:
            t, entry = max(possible, key=lambda x: (x[1].get("filed", ""), x[1].get("accn", "")))
            return {"value": entry["val"], "tag": t, "filed": entry.get("filed")}
    return {"value": None, "tag": "not found", "filed": None}


def compute(companyfacts):
    """Convert EDGAR facts to five fiscal year-end rows without imputing gaps."""
    candidates = set()
    for _, item in observations(companyfacts, TAGS["net_income"], True):
        candidates.add(item["end"])
    # Prefer net-income annual dates to avoid non-year-end revenue instants.
    ends = sorted(candidates, reverse=True)[:5]
    rows = []
    for end in sorted(ends):
        metrics = {name: choose(companyfacts, tags, end, name not in ("equity",))
                   for name, tags in TAGS.items()}
        ni = metrics["net_income"]["value"]
        eq = metrics["equity"]["value"]
        ocf = metrics["operating_cash_flow"]["value"]
        capex = metrics["capital_spending"]["value"]
        roe = None if ni is None or eq is None or eq <= 0 else ni / eq * 100
        owner = None if ocf is None or capex is None else ocf - capex
        metrics["roe"] = {"value": roe, "tag": f"{metrics['net_income']['tag']} / {metrics['equity']['tag']}" if roe is not None else "not known"}
        metrics["owner_earnings"] = {"value": owner, "tag": f"{metrics['operating_cash_flow']['tag']} - {metrics['capital_spending']['tag']}" if owner is not None else "not known"}
        rows.append({"fy_end": end, "metrics": metrics})
    if len(rows) != 5:
        raise ValueError(f"Expected 5 annual 10-K fiscal years; found {len(rows)}. No figures inferred.")
    roes = [row["metrics"]["roe"]["value"] for row in rows]
    owners = [row["metrics"]["owner_earnings"]["value"] for row in rows]
    checks = {
        "ROE >= 15% every year": check_all(roes, lambda n: n >= 15),
        "Owner earnings positive every year": check_all(owners, lambda n: n > 0),
        "Owner earnings grew first to last": ("not known" if owners[0] is None or owners[-1] is None
                                               else "pass" if owners[-1] > owners[0] else "fail"),
    }
    return {"company": companyfacts.get("entityName", "Unknown company"), "rows": rows, "checks": checks}


def check_all(values, predicate):
    if any(v is not None and not predicate(v) for v in values):
        return "fail"
    if any(v is None for v in values):
        return "not known"
    return "pass"


def formatted(name, value):
    if value is None:
        return "not known" if name == "roe" else "not found"
    if name == "roe":
        return f"{value:.1f}%"
    return f"{value / 1_000_000:,.0f}"


def printed_numbers(result):
    """Numeric tokens genuinely printed by the calculation output (including dates/check threshold)."""
    allowed = {"15"}
    for row in result["rows"]:
        allowed.update(re.findall(r"\d+", row["fy_end"]))
        for name, item in row["metrics"].items():
            if item["value"] is not None:
                val = formatted(name, item["value"])
                allowed.add(normalize_number(val))
                if name == "roe":
                    allowed.add(normalize_number(val[:-1]))
    return allowed


def normalize_number(token):
    return token.strip().replace(",", "").replace("%", "").lstrip("+")


NUMBER_TOKEN = re.compile(r"(?<![A-Za-z\d_])[-+]?\d[\d,]*(?:\.\d+)?%?(?![A-Za-z\d_])")


def unsupported_numbers(memo, result):
    allowed = printed_numbers(result)
    return sorted({token for token in NUMBER_TOKEN.findall(memo)
                   if normalize_number(token) not in allowed})


def render(result):
    print(f"Company: {result['company']} | SEC EDGAR 10-K | USD millions except ROE")
    for row in result["rows"]:
        print(f"Fiscal-year end: {row['fy_end']}")
        for name, item in row["metrics"].items():
            print(f"  {name}: {formatted(name, item['value'])} | XBRL: {item['tag']}")
    print("Checks (ROE >= 15% is a classroom design threshold):")
    for name, verdict in result["checks"].items():
        print(f"  {name}: {verdict}")


def main():
    parser = argparse.ArgumentParser(description="Buffett investor skill: deterministic 10-K facts")
    parser.add_argument("ticker", help="US listed ticker (e.g. COST or JPM)")
    args = parser.parse_args()
    render(compute(fetch_company(args.ticker)))


if __name__ == "__main__":
    main()
