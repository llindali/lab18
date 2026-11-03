---
name: buffett-investor
description: Use when asked to judge whether a US listed company's business meets Buffett-style quality criteria using five annual 10-K fiscal periods from SEC EDGAR; compute numbers in the bundled script and write a short source-constrained own/watch/pass memo.
---

# Buffett-inspired investor skill

Read the investor's philosophy at [FAskills Buffett page](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/warren_buffett.md) as a **reference only**. Do not install FAskills or use its paid data. Focus on consistent returns on equity, owner cash generation, durable economics, and caution about what financial statements cannot establish.

1. Ask for a ticker. Run `python .agents/skills/buffett-investor/sec_buffett.py TICKER` from the repository root, with `SEC_USER_AGENT` set to the student's real name and email (required by the SEC). Use only this script's printed results; do not calculate figures yourself or look up prices.
2. The script fetches keyless SEC EDGAR companyfacts and prints the last five 10-K fiscal years, the relevant XBRL tags, and three deterministic tests:
   - ROE >= 15% **every year** (fixed classroom rule, not Buffett's official universal rule);
   - owner earnings > 0 **every year**;
   - owner earnings rise from first to last year.
   Owner earnings is the classroom proxy: cash flow from operations less PP&E purchases. This differs from Buffett's nuanced maintenance-capex definition.
3. Write a concise Buffett-*inspired* business memo, **not an impersonated authentic Buffett communication**, in `memos/TICKER.md`. State **OWN THE BUSINESS**, **WATCH**, or **PASS**, with supporting printed numbers only. Address profitability, cash conversion, uncertainty about moat or management, and why the three checks do or do not settle the question. This is a quality judgment, **not a stock-price decision**. Do not use stock price, valuation, financial projections, market cap, or unverifiable claims.
4. If data is missing, say **not found**; if a calculated ratio or check cannot be determined, say **not known**. Never estimate or invent. Missing inputs must not be treated as failure or pass. With incomplete evidence, prefer **WATCH**. Negative or zero equity makes ROE **not known**.
5. Open `streamlit run app.py`, confirm the chart, five-year fact table, computed checks and memo. Its guard highlights any numerical token in the memo that was not printed by the program. Revise the memo until none remain. Memo may be edited interactively; save only when satisfied.
6. Test COST against the instructor table; all three checks should pass. Test JPM: missing capital spending, unknowable owner earnings and their two checks. Insert an unauthorized `40.0%` into COST's memo and confirm the app flags it. Do not paste reference numbers into the computation script.
7. Put one sentence at the end of the memo stating whether to trust this business-quality verdict and why.

Use the latest filed 10-K for duplicated observations, annual (roughly 365-day) periods for flow facts, and explicit XBRL metric tags. Do not silently replace missing values with approximations.
