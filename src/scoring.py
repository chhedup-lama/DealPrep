"""Phase 1B scoring engine: turns a raw flag (from `tools._detect_flags`)
into a ranked, explainable insight — priority score, band, feed category,
a specific recommended action, and evidence chips.

Deterministic and rule-based end to end, same design principle as the flag
detection itself (`src/tools.py`): the LLM narrates and drafts, it never
decides what's risky or how risky it is (see PRD-phase1-dashboard.md §10,
Product Principle 5).

Adapted from the PRD's scoring tables (§10.3-10.6) in one deliberate way:
the PRD's "Time Urgency" dimension is defined in terms of calendar
time-to-call, but this schema has no calendar table (see
docs/data_dictionary.md) — the closest available signal is how soon the
account's nearest open opportunity closes. Day-based bands below are an
original adaptation of the PRD's hour-based bands, not a literal
implementation of it; real calendar awareness is Phase 2 (see roadmap).
"""

from __future__ import annotations

from datetime import date

Flag = dict
Account = dict

PRIORITY_BANDS: tuple[tuple[int, str], ...] = (
    (90, "Critical"),
    (70, "High"),
    (40, "Medium"),
    (0, "Low"),
)

# --- Time Urgency (proxy: days until nearest relevant close date) ---
_URGENCY_BANDS: tuple[tuple[int, int], ...] = (
    (3, 40),
    (14, 35),
    (30, 30),
    (60, 20),
    (90, 10),
)

# --- Deal Value ---
_DEAL_VALUE_BANDS: tuple[tuple[float, int], ...] = (
    (100_000, 30),
    (50_000, 20),
    (20_000, 10),
    (0, 5),
)

# --- Risk Severity per flag type (PRD §10.5, mapped onto this repo's flag types) ---
_RISK_SEVERITY: dict[str, int] = {
    "open_priority_ticket": 30,  # scaled down to 20 for P2 below
    "renewal_approaching": 25,
    "usage_decline": 25,  # scaled down to 15 below <20% MoM
    "competitor_mentioned": 20,
    "no_economic_buyer": 20,
    "no_champion": 15,
    "quiet_account": 15,
    "stalled_opportunity": 15,  # bumped to 20 below if past close date
}

# Flag types where relevant enablement content (playbook/battlecard/case
# study) plausibly exists — feeds the Actionability score.
_ENABLEMENT_LIKELY = {
    "competitor_mentioned",
    "renewal_approaching",
    "usage_decline",
    "no_economic_buyer",
    "no_champion",
    "stalled_opportunity",
}

CATEGORY_LABELS: dict[str, str] = {
    "high_risk_renewals": "High-Risk Renewals",
    "expansion_opportunities": "Expansion Opportunities",
    "discovery_calls": "Discovery Calls",
    "missing_stakeholders": "Missing Stakeholders",
    "support_risk": "Support Risk",
    "competitive_risk": "Competitive Risk",
    "monitor": "Monitor",
}


def nearest_open_opportunity(open_opportunities: list[dict], as_of: date) -> dict | None:
    dated = [o for o in open_opportunities if o.get("CLOSE_DATE")]
    if not dated:
        return None
    return min(dated, key=lambda o: abs((o["CLOSE_DATE"] - as_of).days))

def _flag_close_date(flag: Flag, open_opportunities: list[dict], as_of: date) -> date | None:
    if flag.get("close_date"):
        return flag["close_date"]
    nearest = nearest_open_opportunity(open_opportunities, as_of)
    return nearest["CLOSE_DATE"] if nearest else None


def _flag_deal_value(flag: Flag, account: Account, open_opportunities: list[dict]) -> float | None:
    if flag.get("amount_eur") is not None:
        return float(flag["amount_eur"])
    if open_opportunities:
        amounts = [o["AMOUNT_EUR"] for o in open_opportunities if o.get("AMOUNT_EUR")]
        if amounts:
            return float(max(amounts))
    if account.get("ARR_EUR") is not None:
        return float(account["ARR_EUR"])
    return None


def _time_urgency_score(close_date: date | None, as_of: date) -> int:
    if close_date is None:
        return 0
    days = (close_date - as_of).days
    if days < 0:
        return _URGENCY_BANDS[0][1]  # already overdue — as urgent as it gets
    for threshold, score in _URGENCY_BANDS:
        if days <= threshold:
            return score
    return 0


def _deal_value_score(amount: float | None) -> int:
    if amount is None:
        return 0
    for threshold, score in _DEAL_VALUE_BANDS:
        if amount >= threshold:
            return score
    return 0


def _account_importance_score(account: Account) -> int:
    arr = account.get("ARR_EUR") or 0
    segment = account.get("SEGMENT")
    if segment == "ENT" or arr >= 80_000:
        return 20
    if segment == "MM" or arr >= 30_000:
        return 10
    return 5


def _risk_severity_score(flag: Flag, as_of: date) -> int:
    flag_type = flag["type"]
    base = _RISK_SEVERITY.get(flag_type, 10)
    if flag_type == "open_priority_ticket" and flag.get("priority") != "P1":
        return 20
    if flag_type == "usage_decline" and (flag.get("pct_change") or 0) < 20:
        return 15
    if flag_type == "stalled_opportunity":
        close_date = flag.get("close_date")
        if close_date is not None and close_date < as_of:
            return 20
    return base


def _actionability_score(flag: Flag) -> int:
    score = 15  # a specific recommended action is always generated below
    if flag["type"] in _ENABLEMENT_LIKELY:
        score += 10
    return score


def band_for_score(score: int) -> str:
    for threshold, band in PRIORITY_BANDS:
        if score >= threshold:
            return band
    return "Low"


def score_insight(
    flag: Flag,
    account: Account,
    open_opportunities: list[dict],
    as_of: date,
) -> dict:
    """Score one flag into a priority score + band + explainable breakdown."""
    close_date = _flag_close_date(flag, open_opportunities, as_of)
    deal_value = _flag_deal_value(flag, account, open_opportunities)

    breakdown = {
        "time_urgency": _time_urgency_score(close_date, as_of),
        "deal_value": _deal_value_score(deal_value),
        "account_importance": _account_importance_score(account),
        "risk_severity": _risk_severity_score(flag, as_of),
        "actionability": _actionability_score(flag),
    }
    score = sum(breakdown.values())
    return {
        "score": score,
        "band": band_for_score(score),
        "breakdown": breakdown,
        "close_date": close_date,
        "deal_value": deal_value,
    }


def category_for(flag: Flag, account: Account) -> str:
    flag_type = flag["type"]
    if flag_type in ("renewal_approaching", "usage_decline", "quiet_account"):
        return CATEGORY_LABELS["high_risk_renewals"]
    if flag_type == "open_priority_ticket":
        return CATEGORY_LABELS["support_risk"]
    if flag_type == "competitor_mentioned":
        return CATEGORY_LABELS["competitive_risk"]
    if flag_type in ("no_economic_buyer", "no_champion"):
        return CATEGORY_LABELS["missing_stakeholders"]
    if flag_type == "stalled_opportunity":
        opp_type = flag.get("opportunity_type")
        if opp_type == "Renewal":
            return CATEGORY_LABELS["high_risk_renewals"]
        if opp_type == "New Business" and account.get("STATUS") == "prospect":
            return CATEGORY_LABELS["discovery_calls"]
        if opp_type in ("Expansion", "New Business"):
            return CATEGORY_LABELS["expansion_opportunities"]
    return CATEGORY_LABELS["monitor"]


def recommended_action(flag: Flag, as_of: date | None = None) -> str:
    flag_type = flag["type"]
    name = flag.get("opportunity_name")

    if flag_type == "stalled_opportunity":
        overdue = flag.get("close_date") is not None and as_of is not None and flag["close_date"] < as_of
        if overdue:
            return (
                f"'{name}' is past its close date — reconfirm the timeline with the buyer "
                "before it slips further, or requalify the deal."
            )
        return (
            f"Reconnect on '{name}': confirm what's blocking it at "
            f"{flag.get('days_in_stage', 'many')} days in stage and get a firm next step."
        )
    if flag_type == "renewal_approaching":
        return (
            f"Confirm renewal intent on '{name}' and surface any blockers before the "
            f"{flag.get('close_date')} close date — loop in the Economic Buyer if they've gone quiet."
        )
    if flag_type == "no_economic_buyer":
        return f"Identify and engage an Economic Buyer on '{name}' before advancing — deals this size stall without one."
    if flag_type == "no_champion":
        return f"Find and confirm a Champion on '{name}' who can advocate internally between calls."
    if flag_type == "usage_decline":
        return (
            f"Ask directly about the {flag.get('pct_change')}% usage drop before discussing "
            "expansion — confirm whether it's seasonal or an adoption problem."
        )
    if flag_type == "open_priority_ticket":
        return (
            f"Acknowledge the open {flag.get('priority')} ticket first, confirm the resolution "
            "owner and timeline, and only then move to commercial topics."
        )
    if flag_type == "quiet_account":
        return (
            f"Re-establish contact — no activity logged in {flag.get('days_since_activity', '20+')} "
            "days despite an open deal. A short check-in is overdue."
        )
    if flag_type == "competitor_mentioned":
        return f"Pull the {flag.get('competitor')} battlecard before the call and be ready to address it directly."
    return "Review this account before the next call."


def evidence_chips(flag: Flag) -> list[str]:
    flag_type = flag["type"]
    chips_map: dict[str, list[str]] = {
        "stalled_opportunity": ["Opportunity"],
        "renewal_approaching": ["Opportunity"],
        "no_economic_buyer": ["Opportunity", "Contacts"],
        "no_champion": ["Opportunity", "Contacts"],
        "quiet_account": ["Activity"],
        "usage_decline": ["Usage"],
        "open_priority_ticket": ["Ticket"],
        "competitor_mentioned": ["Activity", "Playbook"],
    }
    return chips_map.get(flag_type, [])
