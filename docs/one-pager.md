# AE Call-Prep Agent — One-Pager

## Scope: what I built, and what I cut

**Built:** a conversational agent for a mid-market AE (the brief's persona: ~18 months
tenure, EMEA, 30–40 accounts) prepping for an account call. It combines live
Snowflake CRM/product/support data with Personio's sales enablement docs
(playbook, ICP, battlecards, objection handling, pricing, case studies) behind
a single chat interface.

The centerpiece is a **proactive account brief**, not just Q&A. Five AE
interviews in the enablement folder converge on one point: the real pain
isn't "I can't find the fact," it's "I don't notice the thing until it's too
late" (Lena: a renewal quietly slipped for three months before she caught it;
Ines: lost a deal because nobody flagged a missing IT contact). So when the
AE opens an account, the agent leads with a short, deterministic brief that
flags: a stalled opportunity, a missing Economic Buyer or Champion on a >€30k
deal (straight from the playbook's own MEDDIC framework), month-over-month
usage decline, an open P1/P2 ticket, a quiet account with an open deal and no
recent activity, or a competitor mention in recent activity (which pulls the
matching battlecard automatically — Marcus's specific ask: "tell me it's
relevant, don't make me go find it"). From there it's a normal multi-turn
chat — the AE can drill into activities, opportunities, usage, tickets,
contacts, or ask the enablement docs directly ("what does the playbook say
about qualifying a deal in Demo stage?").

**Cut, deliberately, from the case submission itself:**
- **No web UI required.** The brief asks for "conversational, multi-turn" —
  the CLI chat loop (`src/cli.py`) satisfies that on its own, and is what the
  agent quality above was validated against. A Streamlit dashboard
  (`frontend/`) exists in this repo too, but it's a stretch artifact built on
  top of the same unchanged `src/agent.py`/`src/tools.py` — see
  `docs/PRD.md` and `docs/FRONTEND-BUILD-PLAN.md`. It demonstrates the
  product's path past the brief, not a requirement of it.
- **No vector/embedding search.** The enablement corpus is 8 short docs
  (~45KB). A simple header-chunked keyword search is fast, free, and fully
  inspectable — the right tool for this corpus size, not the general
  answer. Flagged below as the first thing to swap for production.
- **No free-form SQL tool.** The agent gets 8 parameterized query functions,
  not a text-to-SQL escape hatch. This trades some flexibility for
  predictability and a zero SQL-injection surface — every tool call is
  auditable in the transcript.
- **No enterprise variant.** Ines's interview is explicit that enterprise AEs
  have a different problem (connecting dots across 12 stakeholders on 5
  accounts, not fast context on 30) and that one product for both "is
  unlikely to land well." I scoped to the persona the brief names and didn't
  try to serve both.
- **No automated eval harness.** Given the time budget, I validated with
  scripted multi-turn conversations against both scenarios named in the
  brief (see Quality) instead of building a scoring pipeline — a real gap,
  addressed below.

## Architecture & key technical choices

Plain Python + the Anthropic SDK's tool runner (`client.beta.messages.tool_runner`)
over Claude Opus 4.8 — no agent framework. Every tool call in a
transcript maps to a specific, readable function; nothing is hidden behind
framework machinery.

Two data sources, two deliberately different tool shapes:

- **Structured (Snowflake):** a live PAT-authenticated connection and 8
  parameterized query functions (`find_account`, `get_account_brief`,
  `get_activities`, `get_opportunities`, `get_usage_trend`, `get_tickets`,
  `get_contacts`). `build_account_brief()` composes the others and runs the
  flag heuristics described above — as **plain rule-based logic, not an LLM
  judgment call.** That's intentional: Sofia's interview was unusually
  direct about trust — "if a tool tells me a wrong fact, I lose three months
  of trust in it... I'd rather it told me less and was right." Deterministic
  flags over the same data every time are auditable and don't hallucinate.
- **Unstructured (enablement docs):** local Markdown, chunked on `##`
  headers, ranked by simple word overlap. No embeddings, no vector DB —
  appropriately sized for 8 documents.

The system prompt encodes the interview findings directly: lead with the
brief before answering the literal question; default to a few lines, not a
report (Thomas: "two lines... anything longer I'm going to skim"); ground
pricing answers in deal context instead of pasting the cheat sheet (Thomas's
specific warning); cite the enablement docs rather than answer from memory;
say "I don't know" rather than guess.

## Quality: how I'd know it's good enough

Three concrete bars, not vibes:

1. **Every account fact the agent states must trace to a tool call result.**
   No invented numbers, dates, or contacts. I checked this by hand against
   the raw Snowflake data for each test account.
2. **The brief surfaces at least one thing the AE didn't already know**, for
   any account where the data actually supports one. Validated by picking
   accounts I'd pre-checked had a real signal (e.g. Halcyon Hospitality:
   17% MoM usage drop + a stalled renewal + no Economic Buyer + a HiBob
   mention, all real in the data) and confirming the agent surfaced all of
   it, unprompted.
3. **Answers stay short by default** and only expand when the AE drills in —
   checked qualitatively across every test conversation.

What I actually ran in the time available: full multi-turn conversations
against both scenarios named in the brief — a churn-risk renewal call
(Halcyon Hospitality: usage decline, stalled negotiation, missing
decision-makers, competitor mention all fired correctly) and a hot-prospect
discovery call (Fjord Logistics: missing Economic Buyer, Workday mention,
and the agent independently connected it to the "lost to Workday" case study
pattern in the enablement docs — that cross-reference wasn't hand-tuned, it
came from the model reasoning over what `search_enablement` returned).

**What's missing for a real quality bar:** a small labeled eval set — maybe
10–15 accounts with a human-written "what should the AE know" reference
answer — scored by an LLM-judge rubric (or human review) on every prompt or
tool change, so iteration doesn't silently regress. Also missing: an
automated hallucination check (do the numbers in the model's answer actually
appear in the tool results it received), and real usage signal — does the AE
act on a flag, ignore it, or correct it.

## Path to production

- **Real usage telemetry first.** Marcus's line matters most here: "if it
  doesn't earn its keep on the first interaction, he won't come back."
  Track which flags get surfaced and whether the AE follows up on them —
  that's the actual product signal, more than any offline eval.
- **Eval harness in CI** — labeled accounts + rubric, gating prompt/tool
  changes before they ship.
- **Swap keyword search for embeddings** once the enablement corpus grows
  past a handful of docs.
- **Meet the AE where they work.** Lena's prep ritual already spans
  Salesforce, Gong, Drive, and Slack — a fifth standalone tool is friction,
  not relief. This belongs embedded in Salesforce or Slack, not a separate
  CLI/app.
- **Per-AE identity**, not one shared PAT — the agent should only ever see
  accounts the logged-in AE owns.
- **Graceful degradation** — if Snowflake or the enablement store is down,
  the agent should say so and still be useful, not fail the whole
  conversation mid-call-prep.
- **Consider the enterprise variant as a separate roadmap item**, not a
  bolt-on — Ines's account shape (5 accounts, 12 stakeholders, 6-month
  cycles) needs a genuinely different tool, not more flags on this one.
