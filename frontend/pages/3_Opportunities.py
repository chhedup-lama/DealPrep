"""Master view: Opportunities (PRD §6.3)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import streamlit as st

from frontend.lib import nav
from frontend.lib.branding import inject_css, page_heading
from frontend.lib.data import list_opportunities_for_ae
from frontend.lib.tables import render_table

st.set_page_config(
    page_title="Opportunities — AE Call-Prep", page_icon="💼", layout="wide", initial_sidebar_state="collapsed"
)
inject_css()

ae = nav.render_sidebar_nav("Opportunities")

page_heading("briefcase", f"Opportunities — {ae}")

opps = list_opportunities_for_ae(ae)
if not opps:
    st.info("No opportunities found for this AE.")
    st.stop()

df = pd.DataFrame(opps)
stage_filter = st.multiselect("Stage", sorted(df["STAGE"].dropna().unique()))
type_filter = st.multiselect("Type", sorted(df["TYPE"].dropna().unique()))

filtered = df.copy()
if stage_filter:
    filtered = filtered[filtered["STAGE"].isin(stage_filter)]
if type_filter:
    filtered = filtered[filtered["TYPE"].isin(type_filter)]

st.caption(f"{len(filtered)} of {len(df)} opportunities")
render_table(
    filtered.sort_values("CLOSE_DATE"),
    hide=("OPPORTUNITY_ID",),
    widths={"COMPANY_NAME": "medium", "NAME": "medium"},
)
