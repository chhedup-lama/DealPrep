"""Home page: sidebar nav + AE picker, and a Chat / Get Insights tab toggle
mirroring ChatGPT's own Chat/Work switcher — a ChatGPT-style centered hero
with the portfolio-wide chat under "Chat", the insight feed under
"Get Insights" (PRD §6.5)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from frontend.lib import feedback, icons, nav, state
from frontend.lib.branding import PURPLE, inject_css, insight_card
from frontend.lib.chat import render_chat_history, render_chat_turn
from frontend.lib.insights import get_insights_for_ae, group_insights
from src.agent import build_client

st.set_page_config(
    page_title="AE Call-Prep", page_icon="🧭", layout="wide", initial_sidebar_state="collapsed"
)
inject_css()

ae = nav.render_sidebar_nav("Home")

tab_chat, tab_insights = st.tabs(["Chat", "Get Insights"])

with tab_chat:
    st.markdown(
        '<div class="hero-heading">What needs your attention today?</div>', unsafe_allow_html=True
    )

    history_key = f"portfolio::{ae}"
    history = state.get_chat_history(history_key)

    render_chat_history(history, key_prefix=f"portfolio_{ae}")

    with st.container(key="chat_input_row"):
        with st.form(key="portfolio_chat_form", clear_on_submit=True, border=False):
            input_col, send_col = st.columns([6, 1])
            with input_col:
                prompt = st.text_input(
                    "Ask DealPrep AI",
                    placeholder="Ask DealPrep AI...",
                    label_visibility="collapsed",
                )
            with send_col:
                submitted = st.form_submit_button("Send")

    if submitted and prompt:
        render_chat_turn(build_client(), history, prompt, owner_ae=ae, key_prefix=f"portfolio_{ae}")
        # render_chat_turn() draws the new turn right where it's called —
        # after the input row above, since this custom pill input (unlike
        # st.chat_input) isn't pinned to the bottom of the page. Without a
        # rerun, the fresh exchange stays stuck below the input box until
        # the next message is sent. Rerunning immediately re-draws
        # everything from the history loop above, in the right order, the
        # same way it will look from then on — matching the ChatGPT/Claude
        # convention of the newest message always appearing above the box
        # you type into, not below it.
        st.rerun()

with tab_insights:
    _, action_col = st.columns([5, 1])
    with action_col:
        scan_clicked = st.button("Get Insights", type="primary", width="stretch")

    if scan_clicked:
        with st.spinner("Scanning your accounts — checking deals, usage, tickets, and stakeholders..."):
            results = get_insights_for_ae(ae)
        state.set_insights_cache(results)

    results = state.get_insights_cache()

    st.divider()

    def _render_insight_card(card: dict) -> None:
        with st.container(border=True, key=f"card_{card['key']}"):
            insight_card(card)
            with st.container(key=f"cardactions_{card['key']}"):
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
        cols = st.columns(3, gap="medium")
        for i, card in enumerate(cards):
            with cols[i % 3]:
                _render_insight_card(card)

    # Icon per insight-tab, same shared Phosphor-style glyph set used
    # everywhere else in the app (nav, page headings, buttons) — baked as a
    # solid-color PNG-equivalent data URI via icons.image_data_uri() since
    # st.tabs labels only support Markdown (incl. images), not raw HTML/CSS
    # masks, so the currentColor mask trick used elsewhere doesn't apply here.
    TAB_ICONS = {
        "Prepare Now": "clock",
        "High-Risk Renewals": "warning",
        "Expansion Opportunities": "arrow-up",
        "Discovery Calls": "phone",
        "Missing Stakeholders": "users",
        "Support Risk": "ticket",
        "Competitive Risk": "shield",
        "Monitor": "eye",
    }

    def _tab_label(name: str, count: int | None) -> str:
        icon_uri = icons.image_data_uri(TAB_ICONS.get(name, "clock"), color=PURPLE)
        suffix = f" ({count})" if count is not None else ""
        return f"![]({icon_uri}) {name}{suffix}"

    if results is None:
        st.info("Click **Get Insights** to scan your book for anything that needs attention today.")
    elif not results:
        st.success("No flags across your book — you're clear.")
    else:
        dismissed = state.get_dismissed()
        visible = [c for c in results if c["key"] not in dismissed]
        if not visible:
            st.success("All flags dismissed — you're clear for now.")
        else:
            grouped = group_insights(visible)

            sections: list[tuple[str, list[dict], str | None]] = []
            if grouped["prepare_now"]:
                sections.append((
                    "Prepare Now",
                    grouped["prepare_now"],
                    "Highest-priority items — deal timing, value, risk, and actionability combined.",
                ))
            for category, cards in grouped["by_category"].items():
                sections.append((category, cards, None))
            if grouped["monitor"]:
                sections.append(("Monitor", grouped["monitor"], "Lower priority — worth a glance."))

            with st.container(key="insight_tabs"):
                tab_objs = st.tabs(
                    [
                        _tab_label(name, None if name == "Prepare Now" else len(cards))
                        for name, cards, _ in sections
                    ]
                )
            for tab, (_, cards, caption) in zip(tab_objs, sections):
                with tab:
                    if caption:
                        st.caption(caption)
                    _render_card_grid(cards)

        precision = feedback.precision_by_flag_type()
        if precision:
            with st.expander("Insight quality so far"):
                st.caption("Of the insights AEs have rated, how many were useful — by flag type.")
                for flag_type, counts in sorted(precision.items()):
                    total = counts["useful"] + counts["not_useful"]
                    pct = round(100 * counts["useful"] / total) if total else 0
                    st.write(
                        f"**{flag_type.replace('_', ' ').title()}** — {pct}% useful "
                        f"({counts['useful']}/{total} rated)"
                    )
