"""Shared chat-turn rendering for the portfolio-wide (Home) and
account-scoped (Account Detail) chat surfaces. Both display the user's
message immediately, stream the assistant's reply as it arrives instead of
blocking on the full response, and append the exchange to session history.

Streaming doesn't reduce total latency — the model + tool-call round trip
still takes as long as it takes — but a reply that appears progressively
feels far faster in a live demo than a spinner followed by the whole
answer landing at once.
"""

from __future__ import annotations

from typing import Iterator

import anthropic
import pandas as pd
import streamlit as st

from frontend.lib import state
from frontend.lib.tables import render_table
from src.agent import final_text, stream_turn


def _render_account_brief(brief: dict) -> None:
    """get_account_brief's result is one nested dict (account fields, flags,
    open opportunities, contacts), not a flat table — the one tool shape
    that needs its own layout rather than going straight through
    render_table(). Every list-shaped part still goes through render_table
    so it looks like the rest of the dashboard's data, not a JSON dump."""
    if brief.get("as_of"):
        st.caption(f"As of {brief['as_of']}")
    if brief.get("account"):
        render_table(pd.DataFrame([brief["account"]]))
    if brief.get("flags"):
        st.markdown("**Flags:**")
        for flag in brief["flags"]:
            st.markdown(f"- {flag.get('detail', '')}")
    if brief.get("open_opportunities"):
        st.markdown("**Open opportunities:**")
        render_table(pd.DataFrame(brief["open_opportunities"]))
    if brief.get("contacts"):
        st.markdown("**Contacts:**")
        render_table(pd.DataFrame(brief["contacts"]))


def _render_citation_detail(citation: dict) -> None:
    tool, detail = citation["tool"], citation["detail"]
    if tool == "search_enablement":
        st.write(detail)
    elif tool == "get_account_brief" and isinstance(detail, dict):
        _render_account_brief(detail)
    elif isinstance(detail, list) and detail and isinstance(detail[0], dict):
        render_table(pd.DataFrame(detail))
    elif isinstance(detail, list):
        st.caption("No matching records found.")
    else:
        st.write(detail)


def _render_sources(citations: list, key: str) -> None:
    """A collapsed "Sources (N)" popover under an assistant message — closed
    by default, not a wall of citations nobody asked to see; opens next to
    the button on click. Each citation is the exact tool result a claim in
    the answer traces back to (src/agent.py's _extract_citations): the doc
    section + excerpt for search_enablement hits, or the same
    plain-table/label formatting the rest of the dashboard already renders
    CRM data in for everything else — these AEs have zero interest in
    reading a JSON blob, so nothing here should look like one."""
    if not citations:
        return
    with st.popover(f"Sources ({len(citations)})", key=key):
        for i, citation in enumerate(citations):
            if i:
                st.divider()
            st.markdown(f"**{citation['label']}**")
            _render_citation_detail(citation)


def render_chat_history(history: list[dict], key_prefix: str = "chat") -> None:
    """Renders every real, user-visible turn in `history`. Skips the
    grounding gate's internal tool_use/tool_result messages (src/agent.py's
    _run_grounding_gate) — those aren't something the AE said or something
    to show as an assistant reply, they're plumbing that happens to live in
    the same list so future turns keep the context. A user-role message
    whose content isn't a plain string is one of those tool_result entries;
    an assistant-role message with no text block is a tool-use-only step
    with nothing to display.

    Citations are looked up by index from a store kept separate from
    `history` itself (see render_chat_turn) — they can't live on the
    message dict, since that dict gets fed straight back to the Anthropic
    API as conversation history on later turns."""
    citations_store = state.get_citations_store(key_prefix)
    for i, msg in enumerate(history):
        if msg["role"] == "assistant":
            text = final_text(msg)
            if not text:
                continue
            with st.chat_message("assistant"):
                st.write(text)
                _render_sources(citations_store.get(i, []), key=f"sources_{key_prefix}_{i}")
        elif isinstance(msg["content"], str):
            with st.chat_message("user"):
                st.write(msg["content"])


def render_chat_turn(
    client: anthropic.Anthropic,
    history: list[dict],
    prompt: str,
    pinned_account_id: str | None = None,
    pinned_account_brief: dict | None = None,
    owner_ae: str | None = None,
    key_prefix: str = "chat",
) -> None:
    history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    result: dict = {}
    with st.chat_message("assistant"):
        gen = stream_turn(
            client,
            history,
            pinned_account_id=pinned_account_id,
            pinned_account_brief=pinned_account_brief,
            owner_ae=owner_ae,
            result=result,
        )
        st.write_stream(_with_lead_spinner(gen))
        # Store citations under the index this message is about to get once
        # appended below, then render — kept out of the message dict itself
        # (see state.get_citations_store's docstring for why).
        state.set_citations(key_prefix, len(history), result["citations"])
        _render_sources(result["citations"], key=f"sources_{key_prefix}_new_{len(history)}")
    history.append(result["message"])


def _with_lead_spinner(chunks: Iterator[str], message: str = "Thinking...") -> Iterator[str]:
    """Shows a spinner only for the gap before the first chunk arrives
    (e.g. while a tool call is in flight) — once text starts streaming,
    the spinner closes and the text itself is the feedback."""
    with st.spinner(message):
        try:
            first = next(chunks)
        except StopIteration:
            return
    yield first
    yield from chunks
