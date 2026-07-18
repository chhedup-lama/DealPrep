"""AE call-prep agent: Claude Opus 4.8 driven by the Anthropic SDK's tool runner
over a small set of Snowflake-backed tools plus a local enablement-doc search.
"""

from __future__ import annotations

import json
import os

import anthropic
from anthropic import beta_tool
from anthropic.types.beta import BetaTextBlock
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
6. For portfolio-wide questions that aren't about one specific account — \
   "what renewals are closing in the next 30 days," "what's my biggest open \
   deal," "how many accounts do I own" — call list_my_accounts or \
   list_my_opportunities instead of saying you can't do it. These only ever \
   cover the current AE's own book, never another AE's accounts, so there's \
   no privacy reason to hold back — filter/sort what they return yourself to \
   answer the actual question (e.g. TYPE = Renewal and CLOSE_DATE within 30 \
   days of today).

Style: default to short, direct answers — a few lines, not a report. The AE is \
prepping under time pressure and will skim past anything long. If you're not \
confident in a fact, say so plainly rather than guessing — a wrong fact costs \
more trust than an admitted gap. Never invent account data, numbers, or doc \
content that the tools didn't return. Never use emoji, anywhere, for any reason \
— headings, bullets, and emphasis should be plain Markdown (bold, headers, \
lists) with no leading or inline symbols. The dashboard renders its own \
monochrome icon system and an emoji breaks that visual consistency.

Grounding is mandatory, not a preference: every specific fact (a number, a \
date, a name, a quote) must come from a tool result you actually received in \
this conversation. If you don't yet know which account "this account" or "the \
account" refers to, or you'd otherwise have to guess, call \
ask_clarifying_question instead of answering — do not pick a plausible-sounding \
account or invent detail to fill the gap.
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


@beta_tool
def ask_clarifying_question(question: str) -> str:
    """Ask the AE a clarifying question instead of guessing. Call this when
    you don't have enough to answer without inventing something — e.g. it's
    unclear which account "this account" refers to, or a name doesn't
    resolve to anything.

    Args:
        question: The question to put to the AE, e.g. "Which account are you
            asking about?"
    """
    return "Asked the AE — wait for their reply, don't state account specifics until they answer."


TOOLS = [
    find_account,
    get_account_brief,
    get_activities,
    get_opportunities,
    get_usage_trend,
    get_tickets,
    get_contacts,
    search_enablement,
    ask_clarifying_question,
]

TOOLS_BY_NAME = {tool.name: tool for tool in TOOLS}

TOOL_SOURCE_LABELS: dict[str, str] = {
    "find_account": "Snowflake · Accounts",
    "get_account_brief": "Snowflake · Account Brief",
    "get_activities": "Snowflake · Activity Log",
    "get_opportunities": "Snowflake · Opportunities",
    "get_usage_trend": "Snowflake · Product Usage",
    "get_tickets": "Snowflake · Support Tickets",
    "get_contacts": "Snowflake · Contacts",
    "list_my_accounts": "Snowflake · My Accounts",
    "list_my_opportunities": "Snowflake · My Opportunities",
}


def _make_portfolio_tools(owner_ae: str) -> list:
    """Portfolio-wide tools scoped to exactly one AE's own book. `owner_ae`
    is bound here via closure, at call time, from the dashboard's own
    session state (frontend/lib/nav.py's AE picker) — it is never a
    parameter the model fills in. That's the actual security boundary: the
    model could ask for another AE's book in plain English, but there is no
    tool call it can make that would return one, regardless of what it
    requests. A system-prompt instruction alone wouldn't provide that
    guarantee; only binding the identity in code does."""

    @beta_tool(name="list_my_accounts")
    def list_my_accounts() -> str:
        """List every account the current AE owns: company name, status,
        segment, region, ARR, customer-since date. Use for portfolio-wide
        questions ("how many accounts do I have," "which are prospects") —
        never returns another AE's accounts."""
        return _json(tools.list_accounts(owner_ae))

    @beta_tool(name="list_my_opportunities")
    def list_my_opportunities(open_only: bool = True) -> str:
        """List every sales opportunity across every account the current AE
        owns: company, opportunity name, stage, amount, close date, type,
        days in stage. Use for portfolio-wide questions ("what renewals are
        closing in the next 30 days," "what's my biggest open deal") —
        never returns another AE's opportunities.

        Args:
            open_only: If true (default), exclude Closed Won / Closed Lost.
        """
        opps = tools.list_opportunities_for_ae(owner_ae)
        if open_only:
            opps = [o for o in opps if o["STAGE"] not in ("Closed Won", "Closed Lost")]
        return _json(opps)

    return [list_my_accounts, list_my_opportunities]


def _block_type(block) -> str | None:
    return block.get("type") if isinstance(block, dict) else getattr(block, "type", None)


def _block_attr(block, name: str):
    return block.get(name) if isinstance(block, dict) else getattr(block, name, None)


def _extract_citations(trace: list) -> list[dict]:
    """Pairs every tool_use call in `trace` with its tool_result and turns
    each into a citation: the exact source and snippet behind a claim in
    the response, not just "trust me." `trace` is the slice of messages
    this turn added — see run_turn()/stream_turn(), which read it back out
    of the tool_runner's own internal message list (the only place the
    full call/result history survives; the runner itself only returns the
    final text turn).

    search_enablement results become one citation per doc section (source +
    heading + the actual excerpt); every other tool becomes one citation
    with the raw record(s) the tool returned, labeled by the Snowflake data
    it reads from. ask_clarifying_question is skipped — it's a control-flow
    tool, not a source."""
    tool_uses: dict[str, object] = {}
    for message in trace:
        content = message["content"] if isinstance(message, dict) else message.content
        if isinstance(content, str):
            continue
        for block in content:
            if _block_type(block) == "tool_use":
                tool_uses[_block_attr(block, "id")] = block

    citations: list[dict] = []
    for message in trace:
        content = message["content"] if isinstance(message, dict) else message.content
        if isinstance(content, str):
            continue
        for block in content:
            if _block_type(block) != "tool_result":
                continue
            tool_use = tool_uses.get(_block_attr(block, "tool_use_id"))
            if tool_use is None:
                continue
            name = _block_attr(tool_use, "name")
            if name == "ask_clarifying_question":
                continue

            raw = _block_attr(block, "content")
            try:
                result = json.loads(raw) if isinstance(raw, str) else raw
            except (json.JSONDecodeError, TypeError):
                result = raw

            if name == "search_enablement" and isinstance(result, list):
                for hit in result:
                    citations.append(
                        {
                            "tool": name,
                            "label": f"{hit.get('source', 'Enablement')} — {hit.get('section', '')}",
                            "detail": hit.get("text", ""),
                        }
                    )
            else:
                # Kept as the parsed object, not a JSON string: the AEs
                # reading this have zero interest in being technical, so
                # rendering it (frontend/lib/chat.py) reuses the same
                # plain-table/label formatting the rest of the dashboard
                # already shows CRM data in — a JSON blob would be the one
                # place in the whole app that looks like an API response.
                citations.append(
                    {
                        "tool": name,
                        "label": TOOL_SOURCE_LABELS.get(name, name),
                        "detail": result,
                    }
                )
    return citations


def _build_system(
    pinned_account_id: str | None = None,
    pinned_account_brief: dict | None = None,
) -> str:
    system = SYSTEM_PROMPT
    if pinned_account_id:
        system += (
            f"\n\nThe AE is currently viewing account {pinned_account_id} in the "
            "dashboard. Use this account_id directly for get_account_brief and "
            "the drill-down tools unless the AE clearly asks about a different "
            "account — you do not need to call find_account for this one."
        )
    if pinned_account_brief:
        # The dashboard already fetched this account's brief to render the
        # page, before the AE ever opens the chat. Handing it over here
        # skips a full get_account_brief tool round-trip (Claude call ->
        # Snowflake -> Claude call) on the most common path: open an
        # account, immediately ask about it.
        system += (
            "\n\nYou already have this account's brief below (fetched by the "
            "dashboard when the page loaded) — skip the get_account_brief call "
            "in step 2 above and lead your first response directly from these "
            "flags instead. Only call get_account_brief again if the AE asks "
            "you to refresh it.\n\n"
            f"Account brief:\n{_json(pinned_account_brief)}"
        )
    return system


def _has_tool_use(messages: list[dict]) -> bool:
    return any(
        m.get("role") == "assistant"
        and isinstance(m.get("content"), list)
        and any(getattr(block, "type", None) == "tool_use" for block in m["content"])
        for m in messages
    )


def _needs_grounding_gate(
    messages: list[dict],
    pinned_account_id: str | None,
    pinned_account_brief: dict | None,
) -> bool:
    """True the first time in a conversation the model would otherwise be
    free to answer with zero grounding: no account pinned by the dashboard,
    and no tool has ever been called yet. Without this, Claude will
    sometimes narrate a fully invented, plausible-sounding account analysis
    — specific numbers, dates, quotes — with no tool call behind any of it,
    especially for an ambiguous "why is this account a churn risk?" with no
    account established yet. A system-prompt request not to do this isn't
    enough; this makes it structurally impossible instead."""
    if pinned_account_id or pinned_account_brief:
        return False
    return not _has_tool_use(messages)


def _run_grounding_gate(
    client: anthropic.Anthropic, messages: list[dict], available_tools: list
) -> dict | None:
    """Forces exactly one tool call before the model can say anything at
    all, via `tool_choice={"type": "any"}` — a real data/search tool, or
    `ask_clarifying_question` if it doesn't have enough to act on (e.g. no
    account named yet). Mutates `messages` in place with that forced
    call + its result, same as a normal tool round-trip, so the rest of the
    conversation (including future turns) has it as real history.

    `available_tools` is whatever this call's full toolset is — including
    the per-AE portfolio tools built by _make_portfolio_tools(), when an
    owner_ae is known — so a cold-start portfolio question ("what renewals
    are closing soon") can be answered by calling the right tool here
    instead of defaulting to ask_clarifying_question for lack of any better
    option.

    Returns the finished assistant message dict if the model asked a
    clarifying question instead of pulling data — that question *is* the
    whole answer, nothing left to generate. Returns None if a real tool
    ran instead; the caller should proceed to the normal tool_runner call
    to synthesize the answer from what it returned.
    """
    tools_by_name = {tool.name: tool for tool in available_tools}
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT
        + "\n\nYou haven't looked anything up yet this conversation. Call "
        "exactly one tool now — a data/search tool if you can act, or "
        "ask_clarifying_question if you don't have enough to go on. Do not "
        "answer in plain text.",
        tools=[tool.to_dict() for tool in available_tools],
        tool_choice={"type": "any", "disable_parallel_tool_use": True},
        messages=messages,
    )
    messages.append({"role": "assistant", "content": response.content})
    tool_use = next(block for block in response.content if block.type == "tool_use")

    if tool_use.name == "ask_clarifying_question":
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": tool_use.id, "content": "Asked the AE."}
                ],
            }
        )
        question = tool_use.input.get("question", "Which account are you asking about?")
        return {"role": "assistant", "content": [BetaTextBlock(type="text", text=question)]}

    result = tools_by_name[tool_use.name].call(tool_use.input)
    messages.append(
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": result}],
        }
    )
    return None


def run_turn(
    client: anthropic.Anthropic,
    messages: list[dict],
    pinned_account_id: str | None = None,
    owner_ae: str | None = None,
) -> dict:
    """Run one user turn (including any tool-calling loop) and return the
    assistant message dict to append to history.

    pinned_account_id: set on the account detail page so the agent already
    knows which account is in view and can skip find_account.
    owner_ae: the logged-in AE, if known — adds list_my_accounts /
    list_my_opportunities, scoped to exactly this AE's book (see
    _make_portfolio_tools). Omit it (e.g. from the CLI, which has no login)
    and those tools simply aren't offered.

    Note: unlike stream_turn(), this doesn't return citations — its callers
    (the CLI, the call-script draft button) feed the returned message
    straight back into `messages` on a later turn, and the Anthropic API
    rejects any message containing keys outside {role, content}. Citations
    have to live outside the message dict (see stream_turn's `result`
    out-param) for exactly that reason.
    """
    available_tools = TOOLS + (_make_portfolio_tools(owner_ae) if owner_ae else [])
    if _needs_grounding_gate(messages, pinned_account_id, None):
        gated = _run_grounding_gate(client, messages, available_tools)
        if gated is not None:
            return gated

    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=4096,
        system=_build_system(pinned_account_id),
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        tools=available_tools,
        messages=messages,
    )
    last = None
    for message in runner:
        last = message
    return {"role": "assistant", "content": last.content}


def stream_turn(
    client: anthropic.Anthropic,
    messages: list[dict],
    pinned_account_id: str | None = None,
    pinned_account_brief: dict | None = None,
    owner_ae: str | None = None,
    result: dict | None = None,
):
    """Streaming counterpart to run_turn(): yields assistant text as it
    arrives instead of blocking until the full response is ready. Same
    total latency under the hood, but a chat UI that shows text
    progressively feels far faster than one that shows a spinner then
    dumps the whole answer at once.

    owner_ae: the logged-in AE, if known — see run_turn()'s docstring;
    adds list_my_accounts/list_my_opportunities, scoped to exactly this
    AE's own book.

    If `result` is passed, sets result["message"] to the same
    {"role": "assistant", "content": [...]} dict run_turn() returns, once
    the stream is exhausted — the caller appends that to their own history
    after consuming the generator (e.g. via st.write_stream()). Also sets
    result["citations"] — kept as a sibling key, not merged into the message
    dict, since that dict gets fed back to the Anthropic API as `messages`
    on later turns, and the API rejects any key outside {role, content}.
    """
    available_tools = TOOLS + (_make_portfolio_tools(owner_ae) if owner_ae else [])
    before = len(messages)
    if _needs_grounding_gate(messages, pinned_account_id, pinned_account_brief):
        gated = _run_grounding_gate(client, messages, available_tools)
        if gated is not None:
            if result is not None:
                result["message"] = gated
                result["citations"] = []
            yield final_text(gated)
            return

    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=4096,
        system=_build_system(pinned_account_id, pinned_account_brief),
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        tools=available_tools,
        messages=messages,
        stream=True,
    )
    last_stream = None
    for message_stream in runner:
        last_stream = message_stream
        yield from message_stream.text_stream

    if result is not None and last_stream is not None:
        final = last_stream.get_final_message()
        result["message"] = {"role": "assistant", "content": final.content}
        result["citations"] = _extract_citations(runner._params["messages"][before:])


def final_text(assistant_message: dict) -> str:
    return "\n".join(
        block.text for block in assistant_message["content"] if block.type == "text"
    )


def build_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
