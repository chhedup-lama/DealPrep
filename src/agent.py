"""AE call-prep agent: Claude Opus 4.8 driven by the Anthropic SDK's tool runner
over a small set of Snowflake-backed tools plus a local enablement-doc search.
"""

from __future__ import annotations

import json
import os

import anthropic
from anthropic import beta_tool
from dotenv import load_dotenv

from src import retrieval, tools

load_dotenv()

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """\
You are a call-prep assistant for Personio Account Executives. An AE is about \
to get on a call with one of their accounts and wants context fast.

When the AE names or opens an account:
1. Call find_account if you only have a company name, to resolve it to an account_id.
2. Call get_account_brief first. It returns core account facts plus a list of \
   "flags" — stalled opportunities, usage decline, open priority tickets, quiet \
   accounts, missing MEDDIC roles (Economic Buyer / Champion), and competitor \
   mentions in recent activity. Lead your first response with a short, scannable \
   summary built from those flags — this is the thing the AE is least likely to \
   have already noticed themselves. Skip flags that didn't fire; don't pad the \
   summary with data that has nothing interesting to say.
2. If the brief mentions a competitor (e.g. Workday, HiBob) or the AE asks about \
   one, call search_enablement for the matching battlecard and surface the \
   relevant talk track — don't make the AE ask for it separately.
3. For playbook, ICP, objection-handling, pricing, or case-study questions, call \
   search_enablement rather than answering from memory, and ground your answer in \
   what it returns.
4. When asked about pricing, use search_enablement's pricing content as context \
   for a specific, deal-relevant answer — never paste the pricing table verbatim.
5. Use the other tools (get_activities, get_opportunities, get_usage_trend, \
   get_tickets, get_contacts) for drill-down follow-ups once the AE asks for \
   specifics.

Style: default to short, direct answers — a few lines, not a report. The AE is \
prepping under time pressure and will skim past anything long. If you're not \
confident in a fact, say so plainly rather than guessing — a wrong fact costs \
more trust than an admitted gap. Never invent account data, numbers, or doc \
content that the tools didn't return.
"""


def _json(obj) -> str:
    return json.dumps(obj, default=str)


@beta_tool
def find_account(query: str) -> str:
    """Search accounts by company name (full or partial match, case-insensitive).

    Args:
        query: Company name or partial name, e.g. "Brightline" or "Fjord Logistics".
    """
    return _json(tools.find_account(query))


@beta_tool
def get_account_brief(account_id: str) -> str:
    """Get a proactive brief for an account: core facts, open opportunities, and
    flags for things an AE might miss (stalled deals, usage decline, open
    priority tickets, a quiet account, missing Economic Buyer/Champion contacts,
    competitor mentions). Call this first whenever the AE starts talking about a
    specific account.

    Args:
        account_id: The ACC-#### account id. Use find_account first if you only
            have a company name.
    """
    return _json(tools.build_account_brief(account_id))


@beta_tool
def get_activities(account_id: str, days: int = 60) -> str:
    """Get recent CRM activity log (emails, calls, meetings, notes) for an account.

    Args:
        account_id: The ACC-#### account id.
        days: How many days back to look. Defaults to 60.
    """
    return _json(tools.get_activities(account_id, days=days))


@beta_tool
def get_opportunities(account_id: str, open_only: bool = False) -> str:
    """Get sales opportunities for an account (stage, amount, close date, type).

    Args:
        account_id: The ACC-#### account id.
        open_only: If true, exclude Closed Won / Closed Lost opportunities.
    """
    return _json(tools.get_opportunities(account_id, open_only=open_only))


@beta_tool
def get_usage_trend(account_id: str, months: int = 6) -> str:
    """Get monthly product usage (active users, logins, payroll runs, module
    adoption) for an account, most recent month first.

    Args:
        account_id: The ACC-#### account id.
        months: How many months of history to return. Defaults to 6.
    """
    return _json(tools.get_usage_trend(account_id, months=months))


@beta_tool
def get_tickets(account_id: str) -> str:
    """Get support tickets for an account (status, priority, subject, dates).

    Args:
        account_id: The ACC-#### account id.
    """
    return _json(tools.get_tickets(account_id))


@beta_tool
def get_contacts(account_id: str) -> str:
    """Get the stakeholder map for an account: contacts with role, persona type
    (Economic Buyer / Champion / Influencer / Technical / User), and last
    interaction date.

    Args:
        account_id: The ACC-#### account id.
    """
    return _json(tools.get_contacts(account_id))


@beta_tool
def search_enablement(query: str, top_k: int = 3) -> str:
    """Search Personio's sales enablement content: sales playbook, ICP,
    competitive battlecards (Workday, HiBob), objection handling guide, pricing
    cheat sheet, and customer case studies. Returns the most relevant sections
    with their source document and heading.

    Args:
        query: What to search for, e.g. "Workday objection" or "renewal timing".
        top_k: How many sections to return. Defaults to 3.
    """
    return _json(retrieval.search_enablement(query, top_k=top_k))


TOOLS = [
    find_account,
    get_account_brief,
    get_activities,
    get_opportunities,
    get_usage_trend,
    get_tickets,
    get_contacts,
    search_enablement,
]


def run_turn(
    client: anthropic.Anthropic,
    messages: list[dict],
    pinned_account_id: str | None = None,
) -> dict:
    """Run one user turn (including any tool-calling loop) and return the
    assistant message dict to append to history.

    pinned_account_id: set on the account detail page so the agent already
    knows which account is in view and can skip find_account.
    """
    system = SYSTEM_PROMPT
    if pinned_account_id:
        system += (
            f"\n\nThe AE is currently viewing account {pinned_account_id} in the "
            "dashboard. Use this account_id directly for get_account_brief and "
            "the drill-down tools unless the AE clearly asks about a different "
            "account — you do not need to call find_account for this one."
        )

    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=4096,
        system=system,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        tools=TOOLS,
        messages=messages,
    )
    last = None
    for message in runner:
        last = message
    return {"role": "assistant", "content": last.content}


def final_text(assistant_message: dict) -> str:
    return "\n".join(
        block.text for block in assistant_message["content"] if block.type == "text"
    )


def build_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
