"""Lab 18: SEC-sourced financial facts, Buffett checks and memo audit."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "buffett-investor"))
from sec_buffett import (compute, fetch_company, formatted, printed_numbers,
                         unsupported_numbers, render)

st.set_page_config(page_title="Buffett Investor Skill", layout="wide")
st.title("Buffett Investor Skill")
st.caption("Data from SEC EDGAR; built with AI help, a learning demonstration, not investment advice.")

ticker = st.text_input("Ticker", value="COST").strip().upper()
if not ticker:
    st.stop()


@st.cache_data(ttl=3600, show_spinner=False)
def get_result(symbol):
    return compute(fetch_company(symbol))


try:
    result = get_result(ticker)
except Exception as exc:
    st.error(f"Cannot load verified 10-K data: {exc}")
    st.stop()

st.subheader(result["company"])
data = []
for row in result["rows"]:
    record = {"Fiscal year end": row["fy_end"]}
    record.update({name.replace("_", " ").title(): formatted(name, metric["value"])
                   for name, metric in row["metrics"].items()})
    data.append(record)
table = pd.DataFrame(data)
st.dataframe(table, hide_index=True, use_container_width=True)

graph = pd.DataFrame([
    {"Fiscal year": row["fy_end"], "Owner earnings": (row["metrics"]["owner_earnings"]["value"] / 1e6
       if row["metrics"]["owner_earnings"]["value"] is not None else None),
     "Net income": (row["metrics"]["net_income"]["value"] / 1e6
       if row["metrics"]["net_income"]["value"] is not None else None)}
    for row in result["rows"]
]).set_index("Fiscal year")
st.subheader("Owner earnings and net income (USD millions)")
st.line_chart(graph)

st.subheader("Buffett's three checks")
for label, status in result["checks"].items():
    st.write(f"**{label}:** {status}")

with st.expander("Computed data and XBRL provenance"):
    for row in result["rows"]:
        st.markdown(f"**{row['fy_end']}**")
        for key, metric in row["metrics"].items():
            st.text(f"{key}: {formatted(key, metric['value'])} | XBRL: {metric['tag']}")

st.subheader("Buffett-inspired business memo")
memo_path = ROOT / "memos" / f"{ticker}.md"
memo_path.parent.mkdir(parents=True, exist_ok=True)
saved = memo_path.read_text(encoding="utf-8") if memo_path.exists() else (
    f"# {ticker} — Buffett-inspired business memo\n\nWATCH — Memo not written yet. "
    "Use the investor skill to write a memo using only computed facts.\n"
)
memo = st.text_area("Memo (edit to test unsupported-number detection)", value=saved,
                    height=290, key=f"memo_{ticker}")
flagged = unsupported_numbers(memo, result)
if flagged:
    st.error("Numbers not printed by the calculation script: " + ", ".join(flagged))
else:
    st.success("Memo number audit passed: all detected numbers appear in the script output.")
st.markdown(memo)
if st.button("Save memo", disabled=bool(flagged)):
    memo_path.write_text(memo, encoding="utf-8")
    st.success(f"Saved {memo_path.relative_to(ROOT)}")
