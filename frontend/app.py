"""Home page: sidebar nav + AE picker, a ChatGPT-style centered hero with
the portfolio-wide chat, Get Insights triggered from the top right, and the
insight feed below (PRD §6.5)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from frontend.lib import feedback, nav, state
from frontend.lib.branding import inject_css, insight_card
from frontend.lib.insights import get_insights_for_ae, group_insights
from src.agent import build_client, final_text, run_turn

st.set_page_config(
    page_title="AE Call-Prep", page_icon="🧭", layout="wide", initial_sidebar_state="collapsed"
)
inject_css()

ae = nav.render_sidebar_nav("Home")

_, action_col = st.columns([5, 1])
with action_col:
    scan_clicked = st.button("Get Insights", type="primary", width="stretch")

if scan_clicked:
    with st.spinner("Scanning your accounts — checking deals, usage, tickets, and stakeholders..."):
        results = get_insights_for_ae(ae)
    state.set_insights_cache(results)

results = state.get_insights_cache()

st.markdown('<div class="hero-heading">What needs your attention today?</div>', unsafe_allow_html=True)

history_key = f"portfolio::{ae}"
history = state.get_chat_history(history_key)

for msg in history:
    role = "assistant" if msg["role"] == "assistant" else "user"
    text = final_text(msg) if role == "assistant" else msg["content"]
    with st.chat_message(role):
        st.write(text)

if prompt := st.chat_input("Ask a question about your accounts..."):
    history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            client = build_client()
            assistant_message = run_turn(client, history)
        st.write(final_text(assistant_message))
    history.append(assistant_message)

st.divider()


def _render_insight_card(card: dict) -> None:
    with st.container(border=True, key=f"card_{card['key']}"):
        insight_card(card)
        c1, c2, c3, c4 = st.columns(4, gap="small")
        with c1:
            if st.button("Open", key=f"view_{card['key']}"):
                st.session_state["selected_account_id"] = card["account_id"]
                st.switch_page("pages/2_Account_Detail.py")
        with c2:
            if st.button("Useful", key=f"useful_{card['key']}", help="Mark useful"):
                feedback.record(ae, card["account_id"], card["flag"]["type"], "useful")
                st.toast("Thanks — marked useful.")
        with c3:
            if st.button("Not useful", key=f"notuseful_{card['key']}", help="Mark not useful"):
                feedback.record(ae, card["account_id"], card["flag"]["type"], "not_useful")
                st.toast("Got it — marked not useful.")
        with c4:
            with st.popover("Dismiss"):
                reason = st.radio(
                    "Why dismiss this?",
                    ["Already handled", "Wrong / not relevant", "Other"],
                    key=f"reason_{card['key']}",
                )
                if st.button("Confirm", key=f"confirm_dismiss_{card['key']}"):
                    feedback.record(
                        ae, card["account_id"], card["flag"]["type"], "dismissed", reason=reason
                    )
                    state.dismiss(card["key"])
                    st.rerun()


def _render_card_grid(cards: list[dict]) -> None:
    cols = st.columns(2, gap="medium")
    for i, card in enumerate(cards):
        with cols[i % 2]:
            _render_insight_card(card)


if results is None:
    st.info("Click **Get Insights** to scan your book for anything that needs attention today.")
elif not results:
    st.success("✅ No flags across your book — you're clear.")
else:
    dismissed = state.get_dismissed()
    visible = [c for c in results if c["key"] not in dismissed]
    if not visible:
        st.success("✅ All flags dismissed — you're clear for now.")
    else:
        grouped = group_insights(visible)

        if grouped["prepare_now"]:
            st.markdown("#### 🔴 Prepare Now")
            st.caption("Highest-priority items — deal timing, value, risk, and actionability combined.")
            _render_card_grid(grouped["prepare_now"])

        for category, cards in grouped["by_category"].items():
            with st.expander(f"{category} ({len(cards)})"):
                _render_card_grid(cards)

        if grouped["monitor"]:
            with st.expander(f"Monitor — lower priority ({len(grouped['monitor'])})"):
                _render_card_grid(grouped["monitor"])

    precision = feedback.precision_by_flag_type()
    if precision:
        with st.expander("📊 Insight quality so far"):
            st.caption("Of the insights AEs have rated, how many were useful — by flag type.")
            for flag_type, counts in sorted(precision.items()):
                total = counts["useful"] + counts["not_useful"]
                pct = round(100 * counts["useful"] / total) if total else 0
                st.write(
                    f"**{flag_type.replace('_', ' ').title()}** — {pct}% useful "
                    f"({counts['useful']}/{total} rated)"
                )

st.divider()
st.caption("This is a working prototype, not a finished product.")
st.page_link(
    "pages/6_Roadmap.py",
    label="See what's built vs. what's next →",
    icon="🗺️",
)
