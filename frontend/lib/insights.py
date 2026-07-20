"""Needs Attention: a portfolio-wide scan over everything an AE owns, turned
into scored, grouped insight cards (PRD-phase1-dashboard.md §8-10).

Naive per-account loop for Path A (see docs/FRONTEND-BUILD-PLAN.md) — the
production version batches these into set-based queries per PRD §9. This is
the known, intentional performance tradeoff of the demo path.
"""

from __future__ import annotations

from datetime import date

from src import scoring
from src.snowflake_client import get_connection
from src.tools import build_account_brief, list_accounts

PREPARE_NOW_CAP = 7


def _urgency_label(close_date: date | None, as_of: date) -> str | None:
    if close_date is None:
        return None
    days = (close_date - as_of).days
    if days < 0:
        return "Past close date"
    if days == 0:
        return "Closes today"
    if days == 1:
        return "Closes tomorrow"
    return f"Closes in {days} days"


def card_from_flag(account: dict, flag: dict, open_opportunities: list[dict], as_of: date, index: int) -> dict:
    """Shapes one flag into a scored insight card. Shared by the portfolio
    scan below and the account detail page (frontend/pages/2_Account_Detail.py),
    so both surfaces score and label a flag identically."""
    result = scoring.score_insight(flag, account, open_opportunities, as_of)
    return {
        "key": f"{account['ACCOUNT_ID']}::{flag['type']}::{index}",
        "account_id": account["ACCOUNT_ID"],
        "company_name": account["COMPANY_NAME"],
        "segment": account.get("SEGMENT"),
        "region": account.get("REGION"),
        "arr_eur": account.get("ARR_EUR"),
        "status": account.get("STATUS"),
        "flag": flag,
        "score": result["score"],
        "band": result["band"],
        "breakdown": result["breakdown"],
        "close_date": result["close_date"],
        "urgency_label": _urgency_label(result["close_date"], as_of),
        "deal_value": result["deal_value"],
        "category": scoring.category_for(flag, account),
        "recommended_action": scoring.recommended_action(flag, as_of),
        "evidence_chips": scoring.evidence_chips(flag),
    }


def get_insights_for_ae(owner_ae: str) -> list[dict]:
    """One scored insight card per flag, across every account the AE owns,
    sorted by priority score descending."""
    conn = get_connection()
    try:
        accounts = list_accounts(owner_ae, conn=conn)
        cards: list[dict] = []
        for acc in accounts:
            brief = build_account_brief(acc["ACCOUNT_ID"], conn=conn)
            flags = brief.get("flags", [])
            if not flags:
                continue
            account = brief["account"]
            open_opps = brief["open_opportunities"]
            as_of = date.fromisoformat(brief["as_of"])
            cards.extend(
                card_from_flag(account, flag, open_opps, as_of, i)
                for i, flag in enumerate(flags)
            )
    finally:
        conn.close()
    cards.sort(key=lambda c: c["score"], reverse=True)
    return cards


def group_insights(cards: list[dict]) -> dict:
    """Buckets scored cards into the PRD §9.1 feed layout: a capped
    'Prepare Now' section for the most urgent Critical-band items, the rest
    grouped by category, and a collapsed Monitor bucket for Low-band items."""
    prepare_now: list[dict] = []
    monitor: list[dict] = []
    by_category: dict[str, list[dict]] = {}

    for card in cards:
        if card["band"] == "Low":
            monitor.append(card)
        elif card["band"] == "Critical" and len(prepare_now) < PREPARE_NOW_CAP:
            prepare_now.append(card)
        else:
            by_category.setdefault(card["category"], []).append(card)

    return {
        "prepare_now": prepare_now,
        "by_category": by_category,
        "monitor": monitor,
    }
