"""Master view: Contacts / stakeholders (PRD §6.3)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import streamlit as st

from frontend.lib import nav
from frontend.lib.branding import inject_css, page_heading
from frontend.lib.data import list_contacts_for_ae
from frontend.lib.tables import render_table

st.set_page_config(
    page_title="Contacts — AE Call-Prep", page_icon="👥", layout="wide", initial_sidebar_state="collapsed"
)
inject_css()

ae = nav.render_sidebar_nav("Contacts")

page_heading("users", f"Contacts — {ae}")

contacts = list_contacts_for_ae(ae)
if not contacts:
    st.info("No contacts found for this AE.")
    st.stop()

df = pd.DataFrame(contacts)
persona_filter = st.multiselect("Persona type", sorted(df["PERSONA_TYPE"].dropna().unique()))

filtered = df.copy()
if persona_filter:
    filtered = filtered[filtered["PERSONA_TYPE"].isin(persona_filter)]

st.caption(f"{len(filtered)} of {len(df)} contacts")
st.caption(
    "Tip: filter to Economic Buyer / Champion to spot accounts missing a "
    "decision-maker across your whole book, not just one at a time."
)
render_table(
    filtered,
    hide=("CONTACT_ID",),
    widths={"COMPANY_NAME": "medium", "FULL_NAME": "medium", "EMAIL": "medium"},
)
