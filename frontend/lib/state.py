"""st.session_state helpers. Session-only — nothing here survives a restart
(see gap #2/"no persisted dismiss state" in docs/PRD-dashboard-vision.md)."""

from __future__ import annotations

import streamlit as st


def current_ae() -> str | None:
    return st.session_state.get("current_ae")


def set_current_ae(ae: str) -> None:
    st.session_state["current_ae"] = ae


def get_insights_cache() -> list[dict] | None:
    return st.session_state.get("insights_cache")


def set_insights_cache(data: list[dict]) -> None:
    st.session_state["insights_cache"] = data


def get_dismissed() -> set[str]:
    return st.session_state.setdefault("dismissed_flags", set())


def dismiss(flag_key: str) -> None:
    get_dismissed().add(flag_key)


def get_chat_history(key: str) -> list[dict]:
    return st.session_state.setdefault(f"chat::{key}", [])


def clear_chat_history(key: str) -> None:
    st.session_state[f"chat::{key}"] = []


def get_citations_store(key: str) -> dict[int, list]:
    """Citations for a chat, keyed by the assistant message's index in that
    same chat's history list. Kept separate from the history list itself —
    not as an extra key on the message dict — because those dicts get fed
    straight back to the Anthropic API as conversation history on later
    turns, and the API rejects any key outside {role, content}."""
    return st.session_state.setdefault(f"citations::{key}", {})


def set_citations(key: str, index: int, citations: list) -> None:
    get_citations_store(key)[index] = citations
