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
import streamlit as st

from src.agent import stream_turn


def render_chat_turn(
    client: anthropic.Anthropic,
    history: list[dict],
    prompt: str,
    pinned_account_id: str | None = None,
    pinned_account_brief: dict | None = None,
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
            result=result,
        )
        st.write_stream(_with_lead_spinner(gen))
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
