"""Shared st.dataframe rendering so every table in the app fits its
container width instead of triggering Streamlit's horizontal scrollbar —
which reads as broken, not "there's more, scroll for it".

Two changes get every table there: drop the raw internal ID columns every
query returns (OPPORTUNITY_ID, CONTACT_ID, TICKET_ID) — they're SQL join
keys, not something an AE reading a call-prep table needs to see — and pin
an explicit width per column instead of letting Streamlit size each column
off its content, which is what pushes total table width past the
container in the first place.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_table(
    df: pd.DataFrame,
    hide: tuple[str, ...] = (),
    widths: dict[str, str] | None = None,
) -> None:
    shown = df.drop(columns=[c for c in hide if c in df.columns])
    widths = widths or {}
    column_config = {
        col: st.column_config.Column(
            label=col.replace("_", " ").title(),
            width=widths.get(col, "small"),
        )
        for col in shown.columns
    }
    st.dataframe(shown, width="stretch", hide_index=True, column_config=column_config)
