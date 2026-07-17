"""Master view: Accounts (PRD §6.3)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import streamlit as st

from frontend.lib import nav, state
from frontend.lib.branding import inject_css, page_heading
from frontend.lib.data import list_accounts

st.set_page_config(
    page_title="Accounts — AE Call-Prep", page_icon="📇", layout="wide", initial_sidebar_state="collapsed"
)
inject_css()

ae = nav.render_sidebar_nav("Accounts")

page_heading("buildings", f"Accounts — {ae}")

accounts = list_accounts(ae)
df = pd.DataFrame(accounts)

if df.empty:
    st.info("No accounts found for this AE.")
    st.stop()

flagged_ids = set()
insights = state.get_insights_cache()
if insights:
    flagged_ids = {a["account_id"] for a in insights}

col1, col2, col3 = st.columns(3)
with col1:
    status_filter = st.multiselect("Status", sorted(df["STATUS"].dropna().unique()))
with col2:
    segment_filter = st.multiselect("Segment", sorted(df["SEGMENT"].dropna().unique()))
with col3:
    region_filter = st.multiselect("Region", sorted(df["REGION"].dropna().unique()))

filtered = df.copy()
if status_filter:
    filtered = filtered[filtered["STATUS"].isin(status_filter)]
if segment_filter:
    filtered = filtered[filtered["SEGMENT"].isin(segment_filter)]
if region_filter:
    filtered = filtered[filtered["REGION"].isin(region_filter)]

st.caption(f"{len(filtered)} of {len(df)} accounts")

for _, row in filtered.iterrows():
    c1, c2, c3, c4, c5 = st.columns([0.4, 3, 1.2, 1.2, 1])
    if row["ACCOUNT_ID"] in flagged_ids:
        c1.markdown('<span class="status-dot"></span>', unsafe_allow_html=True)
    c2.write(f"**{row['COMPANY_NAME']}**")
    c3.write(row["STATUS"])
    c4.write(f"{row['SEGMENT']} · {row['REGION']}")
    if c5.button("Open", key=f"open_{row['ACCOUNT_ID']}"):
        st.session_state["selected_account_id"] = row["ACCOUNT_ID"]
        st.switch_page("pages/2_Account_Detail.py")
