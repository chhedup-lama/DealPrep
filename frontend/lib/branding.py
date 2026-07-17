"""Personio-inspired visual polish on top of the Streamlit theme in
.streamlit/config.toml. Colors are eyeballed from personio.com and the
in-app screenshot shared for reference, not sampled from design assets —
close enough for a demo, not a pixel-accurate brand implementation.
"""

from __future__ import annotations

import streamlit as st

from frontend.lib import icons

PURPLE = "#6C2BD9"
PURPLE_LIGHT = "#F5F0FC"
BLACK = "#111111"
GRAY = "#6B7280"

PRIORITY_COLORS = {
    "Critical": "#DC2626",
    "High": "#EA580C",
    "Medium": "#CA8A04",
    "Low": GRAY,
}

PHASE_COLORS = {
    "mvp": "#16A34A",
    "phase2": "#7C3AED",
    "phase3": "#6B7280",
}

PHASE_LABELS = {
    "mvp": "✅ Built (Phase 1)",
    "phase2": "🔮 Phase 2",
    "phase3": "🚀 Phase 3 — candidate",
}

def inject_css() -> None:
    thumbs_up_mask = icons.mask_data_uri("thumbs-up", "regular")
    arrow_up_mask = icons.mask_data_uri("arrow-up", "bold")

    st.markdown(
        f"""
        <style>
        .stApp {{ font-family: -apple-system, "Segoe UI", Inter, Helvetica, Arial, sans-serif; }}

        /* Sidebar nav (frontend/lib/nav.py) — Streamlit's own native
        collapse/expand, not a hand-rolled fixed bar. Plain vertical
        stacking inside st.sidebar needs none of the fixed-position/
        z-index/spacer-column CSS the old top bar did. */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FFFFFF, {PURPLE_LIGHT} 140%);
        }}

        /* Every nav row — active or not — renders through the exact same
        st.page_link <a> element (see nav.py); the active one just gets
        disabled=True plus a color override injected per-item. One shared
        base rule for all of them means there's no second DOM shape that
        can drift out of alignment. Icon injected via ::before mask since
        st.page_link's label can't hold raw HTML: 20px container, 8px
        icon-to-label gap, vertically centered, monochrome via
        currentColor. */
        div[class*="st-key-navicon_"] [data-testid="stPageLink"] a {{
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            width: 100% !important;
            border-radius: 8px !important;
            padding: 0.5rem 0.75rem !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            white-space: nowrap;
            text-decoration: none !important;
            border: none !important;
            box-sizing: border-box !important;
            background: transparent !important;
            color: {BLACK} !important;
        }}
        div[class*="st-key-navicon_"] [data-testid="stPageLink"] a:hover {{
            background: {PURPLE_LIGHT} !important;
        }}
        div[class*="st-key-navicon_"] [data-testid="stPageLink"] a::before {{
            content: '';
            display: inline-block;
            width: 20px;
            height: 20px;
            flex-shrink: 0;
            background-color: currentColor;
            -webkit-mask-repeat: no-repeat;
            mask-repeat: no-repeat;
            -webkit-mask-position: center;
            mask-position: center;
            -webkit-mask-size: 18px 18px;
            mask-size: 18px 18px;
        }}
        div[class*="st-key-navicon_"] [data-testid="stPageLink"] {{
            width: 100%;
        }}

        /* AE picker trigger at the sidebar's bottom — a plain full-width
        button showing the AE's email, opening a popover with the switcher. */
        [class*="st-key-profile_menu"] button {{
            width: 100% !important;
            justify-content: flex-start !important;
            font-size: 0.82rem !important;
            border-radius: 8px !important;
        }}

        /* Chat / Get Insights tab toggle on the home page, restyled from
        Streamlit's default underlined tabs into a centered rounded pill
        segmented control (personio/chatgpt-style). Targets the standard
        ARIA tab roles rather than generated class names, since those are
        stable across Streamlit versions. */
        [data-testid="stTabs"] [role="tablist"] {{
            justify-content: center;
            gap: 0.2rem;
            background: #F3F4F6;
            border-radius: 999px;
            padding: 0.25rem;
            width: fit-content;
            margin: 1rem auto 0;
            border-bottom: none !important;
        }}
        [data-testid="stTabs"] [role="tab"] {{
            border-radius: 999px !important;
            border: none !important;
            padding: 0.45rem 1.4rem !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            color: {GRAY} !important;
            background: transparent !important;
        }}
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
            background: white !important;
            color: {BLACK} !important;
            box-shadow: 0 1px 3px rgba(17,17,17,0.12) !important;
        }}
        [data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
            display: none !important;
        }}

        /* Centered ChatGPT-style hero heading + input on the Chat tab. */
        .hero-heading {{
            font-size: 1.7rem;
            font-weight: 700;
            color: {BLACK};
            text-align: center;
            margin: 10vh 0 1.5rem;
        }}
        div[class*="st-key-chat_input_row"] {{
            max-width: 640px;
            margin: 0 auto;
        }}
        div[class*="st-key-chat_input_row"] [data-testid="stTextInput"] input {{
            border-radius: 999px !important;
            padding: 0.85rem 1.25rem !important;
            border: 1px solid #E5E7EB !important;
            box-shadow: 0 2px 10px rgba(17,17,17,0.06) !important;
        }}
        div[class*="st-key-chat_input_row"] [data-testid="stFormSubmitButton"] button {{
            border-radius: 999px !important;
            background: {BLACK} !important;
            border: none !important;
            width: 2.6rem !important;
            height: 2.6rem !important;
            padding: 0 !important;
            color: transparent !important;
            font-size: 0 !important;
            position: relative !important;
        }}
        div[class*="st-key-chat_input_row"] [data-testid="stFormSubmitButton"] button::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 18px;
            height: 18px;
            transform: translate(-50%, -50%);
            background-color: white;
            -webkit-mask: url("{arrow_up_mask}") no-repeat center / 18px 18px;
            mask: url("{arrow_up_mask}") no-repeat center / 18px 18px;
        }}

        /* Primary CTA buttons — black, pill-shaped, matches personio.com's "Book your demo" */
        div.stButton > button[kind="primary"] {{
            background-color: {BLACK};
            color: white;
            border-radius: 999px;
            border: none;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
        }}
        div.stButton > button[kind="primary"]:hover {{
            background-color: #2a2a2a;
            color: white;
        }}

        /* Secondary buttons — purple outline pill */
        div.stButton > button[kind="secondary"] {{
            border-radius: 999px;
            border: 1px solid {PURPLE};
            color: {PURPLE};
        }}

        .flag-card {{
            border: 1px solid #E5E7EB;
            border-left: 4px solid var(--flag-color, {PURPLE});
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.6rem;
            background: white;
        }}
        .flag-card .flag-account {{
            font-weight: 700;
            color: {BLACK};
        }}
        .flag-card .flag-detail {{
            color: {GRAY};
            font-size: 0.92rem;
        }}

        .pill {{
            display: inline-block;
            border-radius: 999px;
            padding: 0.15rem 0.65rem;
            font-size: 0.78rem;
            font-weight: 600;
            color: white;
            margin-right: 0.3rem;
        }}

        .chip {{
            display: inline-block;
            border-radius: 999px;
            padding: 0.1rem 0.55rem;
            font-size: 0.72rem;
            font-weight: 600;
            color: {GRAY};
            border: 1px solid #E5E7EB;
            margin-right: 0.3rem;
            margin-top: 0.3rem;
        }}

        .insight-card-inner {{
            border-left: 3px solid var(--flag-color, {PURPLE});
            padding: 0.1rem 0 0.1rem 0.75rem;
        }}
        .insight-card-inner .flag-account {{
            font-weight: 700;
            font-size: 1rem;
            color: {BLACK};
            line-height: 1.3;
        }}
        .insight-meta {{
            color: {GRAY};
            font-size: 0.8rem;
            margin-top: 0.1rem;
        }}
        .insight-detail {{
            color: #374151;
            font-size: 0.87rem;
            line-height: 1.45;
            margin-top: 0.55rem;
        }}
        .insight-action-box {{
            margin-top: 0.55rem;
            background: {PURPLE_LIGHT};
            border-radius: 8px;
            padding: 0.45rem 0.65rem;
            font-size: 0.83rem;
            line-height: 1.4;
            color: {BLACK};
        }}
        .insight-action-box .label {{
            display: block;
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: {PURPLE};
            margin-bottom: 0.15rem;
        }}
        .insight-chips {{
            margin-top: 0.5rem;
        }}

        /* Compact, uniform action-row buttons inside insight card containers
        only (scoped via the container's key= -> st-key-card_* class), so
        this doesn't affect unrelated buttons like Get Insights or
        master-view Open buttons. Owns the full button style (not just
        size) and covers the popover trigger too, which Streamlit doesn't
        wrap in the same element as a plain st.button. */
        div[class*="st-key-card_"] button {{
            border-radius: 999px !important;
            border: 1px solid {PURPLE} !important;
            background: white !important;
            color: {PURPLE} !important;
            padding: 0.25rem 0.7rem !important;
            min-height: 2.1rem !important;
            font-size: 0.82rem !important;
            white-space: nowrap !important;
        }}
        div[class*="st-key-card_"] button:hover {{
            background: {PURPLE_LIGHT} !important;
        }}

        /* Useful / Not useful feedback buttons — icon-only, same shared
        icon system (regular weight, since feedback is a secondary action
        relative to primary nav). Text label stays in the DOM for
        accessibility (aria-label, tooltip) but is visually hidden; the
        icon is the same thumbs-up glyph mirrored vertically for "not
        useful" via a CSS transform, not a second hand-drawn icon. */
        [class*="st-key-useful_"] button,
        [class*="st-key-notuseful_"] button {{
            position: relative !important;
            color: transparent !important;
            font-size: 0 !important;
            min-width: 2.4rem !important;
        }}
        [class*="st-key-useful_"] button::before,
        [class*="st-key-notuseful_"] button::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 18px;
            height: 18px;
            background-color: {PURPLE};
            -webkit-mask: url("{thumbs_up_mask}") no-repeat center / 18px 18px;
            mask: url("{thumbs_up_mask}") no-repeat center / 18px 18px;
        }}
        [class*="st-key-useful_"] button::before {{
            transform: translate(-50%, -50%);
        }}
        [class*="st-key-notuseful_"] button::before {{
            transform: translate(-50%, -50%) scaleY(-1);
        }}

        .hero-panel {{
            background: linear-gradient(135deg, {PURPLE_LIGHT}, #EDE4FB);
            border-radius: 16px;
            padding: 1.5rem 1.75rem;
            margin-bottom: 1.25rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def priority_pill(band: str) -> str:
    color = PRIORITY_COLORS.get(band, GRAY)
    return f'<span class="pill" style="background:{color};">{band}</span>'


def insight_card(card: dict) -> None:
    """Renders one scored insight card's content (PRD-phase1-dashboard.md
    §9.2): priority badge, deal timing/value, the flag itself, a
    recommended-action callout, and evidence chips. Callers wrap this in
    `st.container(border=True, key=f"card_{card['key']}")` alongside the
    action-button row so the whole thing reads as one bordered card instead
    of a floating HTML block with disconnected buttons below it."""
    color = PRIORITY_COLORS.get(card["band"], GRAY)

    meta_bits = []
    if card.get("urgency_label"):
        clock = icons.svg("clock", "regular", 14, GRAY)
        meta_bits.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;">'
            f'{clock}{card["urgency_label"]}</span>'
        )
    if card.get("deal_value"):
        meta_bits.append(f"€{card['deal_value']:,.0f}")
    if card.get("segment"):
        meta_bits.append(card["segment"])
    meta_line = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(meta_bits)

    chips_html = "".join(f'<span class="chip">{c}</span>' for c in card.get("evidence_chips", []))

    st.markdown(
        f"""
        <div class="insight-card-inner" style="--flag-color:{color};">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem;">
                <div>
                    <div class="flag-account">{card['company_name']}</div>
                    <div class="insight-meta">{meta_line}</div>
                </div>
                {priority_pill(card['band'])}
            </div>
            <div class="insight-detail">{card['flag']['detail']}</div>
            <div class="insight-action-box">
                <span class="label">Recommended</span>{card['recommended_action']}
            </div>
            <div class="insight-chips">{chips_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def phase_pill(phase: str) -> str:
    color = PHASE_COLORS.get(phase, GRAY)
    label = PHASE_LABELS.get(phase, phase)
    return f'<span class="pill" style="background:{color};">{label}</span>'


def roadmap_card(title: str, phase: str, detail: str, source: str | None = None) -> None:
    color = PHASE_COLORS.get(phase, GRAY)
    source_html = f'<div class="flag-detail" style="margin-top:0.3rem;"><i>{source}</i></div>' if source else ""
    st.markdown(
        f"""
        <div class="flag-card" style="--flag-color:{color};">
            <div class="flag-account">{title}</div>
            {phase_pill(phase)}
            <div class="flag-detail" style="margin-top:0.3rem;">{detail}</div>
            {source_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
