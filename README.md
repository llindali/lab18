# FIN 43900 — Lab 18: Legend Investor as Skill

Buffett-inspired business-quality analysis using SEC EDGAR 10-K XBRL facts. Code computes the numbers and three checks; AI writes the judgment. No FAskills installation or paid APIs.

## Run

1. Install packages: `pip install -r requirements.txt`
2. Set your actual identifying SEC User-Agent (required by the SEC):
   - PowerShell: `$env:SEC_USER_AGENT="Your Name your-email@school.edu"`
   - macOS/Linux: `export SEC_USER_AGENT="Your Name your-email@school.edu"`
3. Run the skill's numbers: `python .agents/skills/buffett-investor/sec_buffett.py COST`
4. Run the app: `streamlit run app.py`
5. Use the Buffett skill to write or update `memos/COST.md` using **only** the displayed computed values.

The app opens with COST. Enter JPM to inspect missing capital spending; missing inputs stay **not found** and dependent checks **not known**. To test the memo guard, insert an unsupported number such as `40.0%` into the COST memo using the app editor; it should be flagged immediately. The original saved memo is not overwritten unless you click Save.

## Files

- [Skill instructions](.agents/skills/buffett-investor/SKILL.md)
- [SEC EDGAR computation script](.agents/skills/buffett-investor/sec_buffett.py)
- [Streamlit app](app.py)
- [Costco memo](memos/COST.md)
- [Dependencies](requirements.txt)

The fixed COST memo is based on the professor's supplied reference table; independently verify against live EDGAR on your machine. The script never uses the reference figures as its data source. 10-K only, one-year flow observations, latest filing for duplicate periods, five fiscal year-ends, no guesses. Threshold of ROE >= 15% is the prescribed classroom design choice; this is not a valuation or price recommendation.

**Source:** [Week 11 Lab 18](https://github.com/CinderZhang/FIN43900-Fall2026/blob/main/lessons/week-11/lab-18-legend-investor-as-skill.md). Classroom discussion, partner code explanation, Brightspace quiz, and personal checkout are left for class.
