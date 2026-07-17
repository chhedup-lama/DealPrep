"""Roadmap: what's built vs. what's next, tagged MVP / Phase 2 / Phase 3.

Renders frontend/lib/roadmap.py, which mirrors docs/PRD-phase1-dashboard.md
— this page exists so the product's phase boundaries are visible in-product,
not just in a doc nobody opens. The full Phase 1 track (base dashboard +
1B scoring/grouping + 1C account-detail intelligence + 1D trust loop) is
built; only Phase 2+ remain as roadmap, not code.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from frontend.lib import nav
from frontend.lib.branding import inject_css, roadmap_card
from frontend.lib.roadmap import by_phase

st.set_page_config(
    page_title="Roadmap — AE Call-Prep", page_icon="🗺️", layout="wide", initial_sidebar_state="collapsed"
)
inject_css()

nav.render_sidebar_nav("Roadmap")

st.markdown("### 🗺️ Roadmap")
st.caption(
    "What's built, what's next — kept honest on purpose. Full detail in "
    "`docs/PRD-phase1-dashboard.md`."
)

tab_mvp, tab_p2, tab_p3 = st.tabs(
    ["✅ Built (Phase 1 — full track)", "🔮 Phase 2", "🚀 Phase 3"]
)

with tab_mvp:
    st.caption("What you're clicking through right now — base dashboard + scoring/grouping + account-detail intelligence + the feedback loop.")
    for item in by_phase("mvp"):
        roadmap_card(item["title"], "mvp", item["detail"], item["source"])

with tab_p2:
    st.caption("Team, Workflow, and Proactive Triggers — bigger lifts: new integrations, new personas, or real auth. Not built.")
    for item in by_phase("phase2"):
        roadmap_card(item["title"], "phase2", item["detail"], item["source"])

with tab_p3:
    st.caption("Embedded and Enterprise Variants — candidates, explicitly not commitments. Not built.")
    for item in by_phase("phase3"):
        roadmap_card(item["title"], "phase3", item["detail"], item["source"])
