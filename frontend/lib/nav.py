"""Left sidebar navigation — collapsed by default, expands on click, using
Streamlit's own native sidebar collapse/expand mechanism instead of a
hand-rolled fixed top bar. The prior fixed-position top bar went through
many rounds of CSS fixes (heights, z-index, :has() spacer tricks, absolute
positioning) that each fixed one visual bug and introduced or left another,
because they were all fighting Streamlit's own layout engine from outside
it. Streamlit's sidebar collapse/expand is native, well-tested, and needs
none of that — plain vertical stacking inside `st.sidebar`.

Icons are the shared set in frontend/lib/icons.py (Phosphor Icons' visual
language), injected via a CSS mask-image scoped to each item's own
container, since st.page_link's label can't hold raw HTML.

Every row — active or not — renders through the exact same st.page_link
call (disabled=True for the active one, styled to look non-interactive).
One widget type for every item, so there's no second DOM shape that can
end up a different size.

The AE picker (auth stand-in) sits at the bottom of the sidebar behind a
button showing the AE's email, opening a popover with the switcher —
mirroring the account-switcher pattern at the bottom of tools like
ChatGPT's own sidebar.

Also owns AE selection state — every page gets its own picker instead of
only Home's sidebar, so navigating straight to a page URL no longer hits
the old "pick an AE from Home first" dead end.
"""

from __future__ import annotations

import streamlit as st

from frontend.lib import icons, state
from frontend.lib.data import list_owner_aes

DEFAULT_AE = "lena.koehler@personio.de"

# (label, script path, icon name in frontend/lib/icons.py)
NAV_ITEMS: list[tuple[str, str, str]] = [
    ("Home", "app.py", "house"),
    ("Accounts", "pages/1_Accounts.py", "buildings"),
    ("Opportunities", "pages/3_Opportunities.py", "briefcase"),
    ("Contacts", "pages/4_Contacts.py", "users"),
    ("Tickets", "pages/5_Tickets.py", "ticket"),
    ("Roadmap", "pages/6_Roadmap.py", "map"),
]

_ACTIVE_ROW_CSS = """
div[class*="st-key-navicon_{icon}"] a {{
    background: #F5F0FC !important;
    color: #6C2BD9 !important;
    font-weight: 700 !important;
    opacity: 1 !important;
    cursor: default !important;
}}
div[class*="st-key-navicon_{icon}"] a::before {{
    background-color: #6C2BD9 !important;
}}
"""


def render_sidebar_nav(current: str | None) -> str:
    """Renders the sidebar and returns the active AE email, resolving a
    default on first load so every page works as a direct entry point."""
    owner_aes = list_owner_aes()
    if state.current_ae() not in owner_aes:
        state.set_current_ae(DEFAULT_AE if DEFAULT_AE in owner_aes else owner_aes[0])

    with st.sidebar:
        for label, path, icon_name in NAV_ITEMS:
            is_active = label == current
            with st.container(key=f"navicon_{icon_name}"):
                st.page_link(path, label=label, icon=None, disabled=is_active)
                mask_uri = icons.mask_data_uri(icon_name, "bold")
                active_css = _ACTIVE_ROW_CSS.format(icon=icon_name) if is_active else ""
                st.markdown(
                    f"""<style>
                    div[class*="st-key-navicon_{icon_name}"] a::before {{
                        mask-image: url("{mask_uri}");
                        -webkit-mask-image: url("{mask_uri}");
                    }}
                    {active_css}
                    </style>""",
                    unsafe_allow_html=True,
                )

        st.divider()
        selected = state.current_ae()
        with st.container(key="profile_menu"):
            with st.popover(selected, width="stretch"):
                st.caption("Logged in as")
                selected = st.selectbox(
                    "Logged in as",
                    owner_aes,
                    index=owner_aes.index(state.current_ae()),
                    label_visibility="collapsed",
                    key="sidebar_ae_picker",
                )

    if selected != state.current_ae():
        state.set_current_ae(selected)
        state.set_insights_cache(None)
        st.rerun()

    return state.current_ae()
