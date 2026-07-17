"""Master view: Support tickets (PRD §6.3)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import streamlit as st

from frontend.lib import nav
from frontend.lib.branding import inject_css, page_heading
from frontend.lib.data import list_tickets_for_ae
from frontend.lib.tables import render_table

st.set_page_config(
    page_title="Tickets — AE Call-Prep", page_icon="🎫", layout="wide", initial_sidebar_state="collapsed"
)
inject_css()

ae = nav.render_sidebar_nav("Tickets")

page_heading("ticket", f"Support Tickets — {ae}")

tickets = list_tickets_for_ae(ae)
if not tickets:
    st.info("No tickets found for this AE.")
    st.stop()

df = pd.DataFrame(tickets)
status_filter = st.multiselect("Status", sorted(df["STATUS"].dropna().unique()))
priority_filter = st.multiselect("Priority", sorted(df["PRIORITY"].dropna().unique()))

filtered = df.copy()
if status_filter:
    filtered = filtered[filtered["STATUS"].isin(status_filter)]
if priority_filter:
    filtered = filtered[filtered["PRIORITY"].isin(priority_filter)]

st.caption(f"{len(filtered)} of {len(df)} tickets")
render_table(
    filtered.sort_values("CREATED_DATE", ascending=False),
    hide=("TICKET_ID",),
    widths={"COMPANY_NAME": "medium", "SUBJECT": "medium"},
)
