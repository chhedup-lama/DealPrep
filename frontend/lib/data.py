"""Cached wrappers around the read-mostly src.tools queries used directly
by pages (not the agent's own tool calls — those stay uncached, see below).

Every widget interaction in Streamlit — clicking a button, a tab, a
selectbox — reruns the entire page script from top to bottom. Without
caching, that meant re-opening a fresh Snowflake PAT connection (a real
network round-trip auth handshake, not free) and re-running the same
queries on nearly every click, since e.g. `nav.render_sidebar_nav()` calls
`list_owner_aes()` at the top of every single page. That's what made
clicking around feel slow, independent of anything LLM-related.

`st.cache_data` fixes this the standard Streamlit way: fetch once per TTL
window, reuse the result across reruns. The underlying data (accounts,
opportunities, activity) doesn't change fast enough during a demo for a
5-minute staleness window to matter, and `get_insights_for_ae` already has
its own explicit re-scan-on-click invalidation (frontend/lib/insights.py +
state.py), so it's deliberately not wrapped here — caching it too would
fight that.

Not a fix for chat latency — the agent's own tool calls
(`src/agent.py` -> `src/tools.py` directly) don't go through this cache,
since that path also has to work from the framework-agnostic CLI
(`src/cli.py`), which has no Streamlit runtime to cache against. A slow
first response in a new conversation is model + tool-call latency, not
this.
"""

from __future__ import annotations

import streamlit as st

from src import tools

CACHE_TTL = 300  # seconds


@st.cache_data(ttl=CACHE_TTL)
def list_owner_aes() -> list[str]:
    return tools.list_owner_aes()


@st.cache_data(ttl=CACHE_TTL)
def list_accounts(owner_ae: str) -> list[dict]:
    return tools.list_accounts(owner_ae)


@st.cache_data(ttl=CACHE_TTL)
def list_opportunities_for_ae(owner_ae: str) -> list[dict]:
    return tools.list_opportunities_for_ae(owner_ae)


@st.cache_data(ttl=CACHE_TTL)
def list_contacts_for_ae(owner_ae: str) -> list[dict]:
    return tools.list_contacts_for_ae(owner_ae)


@st.cache_data(ttl=CACHE_TTL)
def list_tickets_for_ae(owner_ae: str) -> list[dict]:
    return tools.list_tickets_for_ae(owner_ae)


@st.cache_data(ttl=CACHE_TTL)
def get_account_core(account_id: str) -> dict | None:
    return tools.get_account_core(account_id)


@st.cache_data(ttl=CACHE_TTL)
def build_account_brief(account_id: str) -> dict:
    return tools.build_account_brief(account_id)


@st.cache_data(ttl=CACHE_TTL)
def get_activities(account_id: str, days: int = 90) -> list[dict]:
    return tools.get_activities(account_id, days=days)


@st.cache_data(ttl=CACHE_TTL)
def get_opportunities(account_id: str) -> list[dict]:
    return tools.get_opportunities(account_id)


@st.cache_data(ttl=CACHE_TTL)
def get_usage_trend(account_id: str, months: int = 12) -> list[dict]:
    return tools.get_usage_trend(account_id, months=months)


@st.cache_data(ttl=CACHE_TTL)
def get_tickets(account_id: str) -> list[dict]:
    return tools.get_tickets(account_id)


@st.cache_data(ttl=CACHE_TTL)
def get_contacts(account_id: str) -> list[dict]:
    return tools.get_contacts(account_id)
