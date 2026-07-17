"""Account-scoped query functions backing the agent's tools.

Two layers:
  - thin SQL wrappers (find_account, get_* ) for drill-down follow-ups
  - build_account_brief(), which composes them and runs deterministic
    heuristics to flag what an AE might miss (stalled deals, usage drops,
    open P1/P2s, quiet accounts, missing MEDDIC roles, competitor mentions).

The heuristics are plain rules over the data, not an LLM call — findings
need to be auditable and consistent, since a wrong flag costs AE trust
faster than a missing one.
"""

from __future__ import annotations

from datetime import date

import snowflake.connector

from src.snowflake_client import run_query

Conn = snowflake.connector.SnowflakeConnection | None

OPEN_STAGES = ("Discovery", "Qualification", "Demo", "Proposal", "Negotiation")
MEDDIC_THRESHOLD_EUR = 30_000
STALLED_DAYS_IN_STAGE = 30
QUIET_ACCOUNT_DAYS = 21
USAGE_DECLINE_PCT = 0.10
ACTIVITY_LOOKBACK_DAYS = 60
RENEWAL_APPROACHING_DAYS = 30


def _as_of_date(conn: Conn = None) -> date:
    """Latest activity date in the data, used as 'today' for recency checks."""
    rows = run_query(
        "SELECT MAX(ACTIVITY_DATE) AS D FROM PERSONIO.CRM.ACTIVITIES", conn=conn
    )
    return rows[0]["D"]


def find_account(query: str) -> list[dict]:
    """Resolve a company name (full or partial) to account records."""
    return run_query(
        """
        SELECT ACCOUNT_ID, COMPANY_NAME, STATUS, SEGMENT, REGION, OWNER_AE
        FROM PERSONIO.CRM.ACCOUNTS
        WHERE COMPANY_NAME ILIKE %s
        ORDER BY COMPANY_NAME
        LIMIT 10
        """,
        (f"%{query}%",),
    )


def list_accounts(owner_ae: str, conn: Conn = None) -> list[dict]:
    """All accounts owned by a given AE — the frontend's master account list."""
    return run_query(
        """
        SELECT ACCOUNT_ID, COMPANY_NAME, STATUS, SEGMENT, REGION, ARR_EUR, CUSTOMER_SINCE
        FROM PERSONIO.CRM.ACCOUNTS
        WHERE OWNER_AE = %s
        ORDER BY COMPANY_NAME
        """,
        (owner_ae,),
        conn=conn,
    )


def list_owner_aes() -> list[str]:
    """Distinct AE identities present in the data — stands in for a login picker."""
    rows = run_query(
        "SELECT DISTINCT OWNER_AE FROM PERSONIO.CRM.ACCOUNTS ORDER BY OWNER_AE"
    )
    return [r["OWNER_AE"] for r in rows]


def list_opportunities_for_ae(owner_ae: str) -> list[dict]:
    """Portfolio-wide opportunities master view."""
    return run_query(
        """
        SELECT o.OPPORTUNITY_ID, a.COMPANY_NAME, o.NAME, o.STAGE, o.AMOUNT_EUR,
               o.CLOSE_DATE, o.TYPE, o.DAYS_IN_STAGE
        FROM PERSONIO.CRM.OPPORTUNITIES o
        JOIN PERSONIO.CRM.ACCOUNTS a ON a.ACCOUNT_ID = o.ACCOUNT_ID
        WHERE a.OWNER_AE = %s
        ORDER BY o.CLOSE_DATE
        """,
        (owner_ae,),
    )


def list_contacts_for_ae(owner_ae: str) -> list[dict]:
    """Portfolio-wide stakeholder master view."""
    return run_query(
        """
        SELECT c.CONTACT_ID, a.COMPANY_NAME, c.FULL_NAME, c.ROLE_TITLE,
               c.PERSONA_TYPE, c.EMAIL, c.LAST_INTERACTION
        FROM PERSONIO.CRM.CONTACTS c
        JOIN PERSONIO.CRM.ACCOUNTS a ON a.ACCOUNT_ID = c.ACCOUNT_ID
        WHERE a.OWNER_AE = %s
        ORDER BY c.LAST_INTERACTION DESC NULLS LAST
        """,
        (owner_ae,),
    )


def list_tickets_for_ae(owner_ae: str) -> list[dict]:
    """Portfolio-wide support ticket master view."""
    return run_query(
        """
        SELECT t.TICKET_ID, a.COMPANY_NAME, t.STATUS, t.PRIORITY, t.SUBJECT,
               t.CREATED_DATE, t.RESOLVED_DATE
        FROM PERSONIO.SUPPORT.TICKETS t
        JOIN PERSONIO.CRM.ACCOUNTS a ON a.ACCOUNT_ID = t.ACCOUNT_ID
        WHERE a.OWNER_AE = %s
        ORDER BY t.CREATED_DATE DESC
        """,
        (owner_ae,),
    )


def get_account_core(account_id: str, conn: Conn = None) -> dict | None:
    rows = run_query(
        "SELECT * FROM PERSONIO.CRM.ACCOUNTS WHERE ACCOUNT_ID = %s",
        (account_id,),
        conn=conn,
    )
    return rows[0] if rows else None


def get_contacts(account_id: str, conn: Conn = None) -> list[dict]:
    return run_query(
        """
        SELECT CONTACT_ID, FULL_NAME, ROLE_TITLE, PERSONA_TYPE, EMAIL, LAST_INTERACTION
        FROM PERSONIO.CRM.CONTACTS
        WHERE ACCOUNT_ID = %s
        ORDER BY LAST_INTERACTION DESC NULLS LAST
        """,
        (account_id,),
        conn=conn,
    )


def get_opportunities(
    account_id: str, open_only: bool = False, conn: Conn = None
) -> list[dict]:
    sql = """
        SELECT OPPORTUNITY_ID, NAME, STAGE, AMOUNT_EUR, CLOSE_DATE, TYPE,
               DAYS_IN_STAGE, WON_LOST_REASON
        FROM PERSONIO.CRM.OPPORTUNITIES
        WHERE ACCOUNT_ID = %s
    """
    if open_only:
        sql += " AND STAGE NOT IN ('Closed Won', 'Closed Lost')"
    sql += " ORDER BY CLOSE_DATE"
    return run_query(sql, (account_id,), conn=conn)


def get_activities(account_id: str, days: int = 60, conn: Conn = None) -> list[dict]:
    return run_query(
        """
        SELECT ACTIVITY_DATE, ACTIVITY_TYPE, SUBJECT, SUMMARY, OPPORTUNITY_ID, CONTACT_ID
        FROM PERSONIO.CRM.ACTIVITIES
        WHERE ACCOUNT_ID = %s
          AND ACTIVITY_DATE >= DATEADD(day, %s, (SELECT MAX(ACTIVITY_DATE) FROM PERSONIO.CRM.ACTIVITIES))
        ORDER BY ACTIVITY_DATE DESC
        """,
        (account_id, -days),
        conn=conn,
    )


def get_usage_trend(account_id: str, months: int = 6, conn: Conn = None) -> list[dict]:
    return run_query(
        """
        SELECT MONTH, MONTHLY_ACTIVE_USERS, LOGINS, PAYROLL_RUNS,
               PERFORMANCE_CYCLES_ACTIVE, RECRUITING_MODULE_ACTIVE, PERFORMANCE_MODULE_ACTIVE
        FROM PERSONIO.PRODUCT.USAGE
        WHERE ACCOUNT_ID = %s
        ORDER BY MONTH DESC
        LIMIT %s
        """,
        (account_id, months),
        conn=conn,
    )


def get_tickets(account_id: str, conn: Conn = None) -> list[dict]:
    return run_query(
        """
        SELECT TICKET_ID, STATUS, PRIORITY, SUBJECT, SUMMARY, CREATED_DATE, RESOLVED_DATE
        FROM PERSONIO.SUPPORT.TICKETS
        WHERE ACCOUNT_ID = %s
        ORDER BY CREATED_DATE DESC
        """,
        (account_id,),
        conn=conn,
    )


COMPETITORS = ("workday", "hibob")


def _detect_flags(
    as_of: date,
    opportunities: list[dict],
    activities: list[dict],
    usage: list[dict],
    tickets: list[dict],
    contacts: list[dict],
) -> list[dict]:
    flags: list[dict] = []

    def _opp_refs(opp: dict) -> dict:
        return {
            "opportunity_id": opp["OPPORTUNITY_ID"],
            "opportunity_name": opp["NAME"],
            "opportunity_type": opp["TYPE"],
            "amount_eur": opp["AMOUNT_EUR"],
            "close_date": opp["CLOSE_DATE"],
            "days_in_stage": opp["DAYS_IN_STAGE"],
        }

    for opp in opportunities:
        if opp["STAGE"] in ("Closed Won", "Closed Lost"):
            continue
        overdue = opp["CLOSE_DATE"] is not None and opp["CLOSE_DATE"] < as_of
        stalled = (opp["DAYS_IN_STAGE"] or 0) > STALLED_DAYS_IN_STAGE
        if overdue or stalled:
            reason = "past its close date" if overdue else f"{opp['DAYS_IN_STAGE']} days in {opp['STAGE']}"
            flags.append(
                {
                    "type": "stalled_opportunity",
                    "detail": f"'{opp['NAME']}' is {reason}.",
                    **_opp_refs(opp),
                }
            )
        if (
            opp["TYPE"] == "Renewal"
            and opp["CLOSE_DATE"] is not None
            and 0 <= (opp["CLOSE_DATE"] - as_of).days <= RENEWAL_APPROACHING_DAYS
        ):
            days_left = (opp["CLOSE_DATE"] - as_of).days
            flags.append(
                {
                    "type": "renewal_approaching",
                    "detail": f"'{opp['NAME']}' renews in {days_left} day{'s' if days_left != 1 else ''}.",
                    **_opp_refs(opp),
                }
            )
        if (opp["AMOUNT_EUR"] or 0) >= MEDDIC_THRESHOLD_EUR:
            personas = {c["PERSONA_TYPE"] for c in contacts}
            if "Economic Buyer" not in personas:
                flags.append(
                    {
                        "type": "no_economic_buyer",
                        "detail": f"No Economic Buyer contact on file for '{opp['NAME']}' (>€30k deal).",
                        **_opp_refs(opp),
                    }
                )
            if "Champion" not in personas:
                flags.append(
                    {
                        "type": "no_champion",
                        "detail": f"No Champion contact on file for '{opp['NAME']}'.",
                        **_opp_refs(opp),
                    }
                )

    has_open_opp = any(o["STAGE"] not in ("Closed Won", "Closed Lost") for o in opportunities)
    if has_open_opp:
        last_activity = activities[0]["ACTIVITY_DATE"] if activities else None
        days_quiet = None if last_activity is None else (as_of - last_activity).days
        if last_activity is None or days_quiet > QUIET_ACCOUNT_DAYS:
            flags.append(
                {
                    "type": "quiet_account",
                    "detail": f"No activity logged in the last {QUIET_ACCOUNT_DAYS}+ days despite an open opportunity.",
                    "days_since_activity": days_quiet,
                }
            )

    if len(usage) >= 2:
        latest, prev = usage[0], usage[1]
        for metric in ("MONTHLY_ACTIVE_USERS", "LOGINS"):
            if prev[metric] and latest[metric] < prev[metric] * (1 - USAGE_DECLINE_PCT):
                pct = round(100 * (1 - latest[metric] / prev[metric]))
                flags.append(
                    {
                        "type": "usage_decline",
                        "detail": f"{metric.replace('_', ' ').title()} dropped {pct}% month over month ({prev['MONTH']} -> {latest['MONTH']}).",
                        "pct_change": pct,
                        "metric": metric,
                    }
                )

    for t in tickets:
        if t["STATUS"] == "In Progress" and t["PRIORITY"] in ("P1", "P2"):
            flags.append(
                {
                    "type": "open_priority_ticket",
                    "detail": f"Open {t['PRIORITY']} ticket: '{t['SUBJECT']}'.",
                    "ticket_id": t["TICKET_ID"],
                    "priority": t["PRIORITY"],
                    "days_open": (as_of - t["CREATED_DATE"]).days if t["CREATED_DATE"] else None,
                }
            )

    mentioned = set()
    for a in activities:
        summary = (a["SUMMARY"] or "").lower()
        for comp in COMPETITORS:
            if comp in summary:
                mentioned.add(comp)
    for comp in mentioned:
        flags.append(
            {
                "type": "competitor_mentioned",
                "detail": f"Recent activity references {comp.title()} — relevant battlecard available via search_enablement.",
                "competitor": comp.title(),
            }
        )

    return flags


def build_account_brief(account_id: str, conn: Conn = None) -> dict:
    """The agent's primary entry point when an AE opens an account.

    Pass `conn` when calling this in a loop (e.g. a portfolio-wide scan) so
    every account reuses one Snowflake connection instead of opening a fresh
    one per query — see get_insights_for_ae() in frontend/lib/insights.py.
    """
    account = get_account_core(account_id, conn=conn)
    if account is None:
        return {"error": f"No account found with id {account_id}"}

    as_of = _as_of_date(conn=conn)
    contacts = get_contacts(account_id, conn=conn)
    opportunities = get_opportunities(account_id, conn=conn)
    activities = get_activities(account_id, days=ACTIVITY_LOOKBACK_DAYS, conn=conn)
    usage = get_usage_trend(account_id, months=6, conn=conn)
    tickets = get_tickets(account_id, conn=conn)

    flags = _detect_flags(as_of, opportunities, activities, usage, tickets, contacts)

    return {
        "as_of": str(as_of),
        "account": account,
        "flags": flags,
        "open_opportunities": [o for o in opportunities if o["STAGE"] not in ("Closed Won", "Closed Lost")],
        "recent_activity_count": len(activities),
        "open_ticket_count": sum(1 for t in tickets if t["STATUS"] != "Resolved"),
        "contacts": contacts,
    }
