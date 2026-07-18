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

**Built past the brief:** a Streamlit dashboard (`frontend/`) that turns the
same agent and tools into a daily-workflow product, per `docs/PRD-phase1-dashboard.md`.
It reuses `src/agent.py`/`src/tools.py` unchanged — no forked logic, only a UI
layer on top:

- **Get Insights** — a portfolio-wide scan across everything the signed-in AE
  owns. Every flag becomes a scored insight card (`src/scoring.py`: time
  urgency, deal value, account importance, risk severity, actionability —
  five independently rule-based dimensions, summed into a Critical/High/
  Medium/Low band), grouped into a capped "Prepare Now" feed plus category
  buckets (High-Risk Renewals, Expansion, Discovery, Missing Stakeholders,
  Support Risk, Competitive Risk, Monitor).
- **Account Detail workspace** — why-flagged evidence cards, a templated
  current-state summary, a what-happened-so-far timeline, stakeholder-gap
  callouts, one specific recommended next-best action, an on-demand
  LLM-drafted call script (grounded in the account's own flags, via the same
  agent), proactively-surfaced relevant enablement, and drill-down tabs for
  Activity/Opportunities/Usage/Tickets/Contacts.
- **Trust loop** — Useful / Not useful on every insight card, plus a reasoned
  dismiss (already handled / wrong / other), logged to `data/feedback.jsonl`
  and rolled up into a live per-flag-type precision readout on the Home page.
- **Master data views**, streamed chat responses, and an AE picker standing
  in for auth.

This is the thing that turns the case's conversational proof-of-concept into
something an AE would plausibly open every morning, not a slide about future
vision.

**Cut, deliberately, from the case submission itself:**
- **The CLI remains the required deliverable.** The brief asks for
  "conversational, multi-turn" — `src/cli.py` satisfies that on its own, and
  is what the agent quality below was validated against. The dashboard is
  additional, not-required scope; see `docs/PRD-phase1-dashboard.md` and
  `docs/FRONTEND-BUILD-PLAN.md` for its own scope and trade-offs.
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
- **No batched insight queries.** Get Insights runs one `build_account_brief`
  call per account the AE owns — connection reuse alone cut a 41-account
  scan from 180s+ to ~12s, but it's still a naive per-account loop, not the
  set-based batched queries (one query per data type across all owned
  accounts) a production scan needs.
- **No real per-AE identity.** The sidebar AE picker is a stand-in for login
  — every AE reads through one shared Snowflake PAT today, scoped by an
  `OWNER_AE` filter in the query, not by an enforced identity boundary.
- **No calendar awareness.** The scoring model's "time urgency" dimension is
  proxied by days-to-nearest-open-close-date, because there's no calendar
  table in the schema — not an actual "this call is in 3 hours."
- **No automated eval harness.** Given the time budget, I validated with
  scripted multi-turn conversations against both scenarios named in the
  brief (see Quality) instead of building a scoring pipeline. The dashboard's
  useful/not-useful feedback loop is a first, live step toward a real signal
  here — not a substitute for one.

## Architecture & key technical choices

Plain Python + the Anthropic SDK's tool runner (`client.beta.messages.tool_runner`)
over Claude Opus 4.8 — no agent framework. Every tool call in a
transcript maps to a specific, readable function; nothing is hidden behind
framework machinery.

Three deliberately different layers, not two:

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
- **Scoring (`src/scoring.py`):** the dashboard's addition — turns a raw flag
  into a priority score, band, feed category, and a specific recommended
  action, all rule-based. Same principle as the flags themselves:
  deterministic systems detect and rank the signal; the LLM only narrates,
  summarizes, and drafts (chat answers, the on-demand call script) on top of
  what scoring and flagging already decided.

The system prompt encodes the interview findings directly: lead with the
brief before answering the literal question; default to a few lines, not a
report (Thomas: "two lines... anything longer I'm going to skim"); ground
pricing answers in deal context instead of pasting the cheat sheet (Thomas's
specific warning); cite the enablement docs rather than answer from memory;
say "I don't know" rather than guess.

Two latency choices worth calling out, both made after the CLI already
worked: **streamed responses** (`stream_turn` in `src/agent.py`, wired into
the dashboard's chat) so the AE sees text arrive progressively instead of
staring at a spinner; and **account-brief pinning** — when the dashboard has
already fetched an account's brief to render the page, it hands that JSON
straight into the system prompt instead of making the agent call
`get_account_brief` again, skipping a full Claude → Snowflake → Claude
round trip on the single most common path (open an account, immediately ask
about it).

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

The dashboard adds one more, smaller signal beyond hand-validation: every
insight card can be marked Useful / Not useful, and the Home page shows a
live "percent useful" per flag type from `data/feedback.jsonl`. It's a real
mechanism, not a mock — but it's only as good as the sample behind it, and
right now that sample is my own demo session, not a population of real AEs.

**What's missing for a real quality bar:** a small labeled eval set — maybe
10–15 accounts with a human-written "what should the AE know" reference
answer — scored by an LLM-judge rubric (or human review) on every prompt or
tool change, so iteration doesn't silently regress. Also missing: an
automated hallucination check (do the numbers in the model's answer actually
appear in the tool results it received), and enough real feedback-loop volume
to trust the precision numbers instead of just being reassured they exist.

## Path to production

- **Real usage telemetry, at real scale.** The feedback loop above is a
  first version of Marcus's point — "if it doesn't earn its keep on the
  first interaction, he won't come back" — but it needs a real AE
  population and a real backing store, not a JSONL file from one demo
  session.
- **Eval harness in CI** — labeled accounts + rubric, gating prompt/tool
  changes before they ship.
- **Swap keyword search for embeddings** once the enablement corpus grows
  past a handful of docs.
- **Batch the Get Insights scan** — set-based queries per account-owned data
  type instead of per-account loop, needed once a book is scanned on a
  schedule rather than on click.
- **Real calendar awareness** — replace the days-to-close-date urgency proxy
  with an actual next-meeting signal once a calendar data source exists.
- **Meet the AE where they work.** Lena's prep ritual already spans
  Salesforce, Gong, Drive, and Slack — a sixth standalone tool is friction,
  not relief. This belongs embedded in Salesforce or Slack, not a separate
  CLI/dashboard.
- **Per-AE identity**, not one shared PAT — the agent should only ever see
  accounts the logged-in AE owns, enforced at the identity layer, not just a
  `WHERE OWNER_AE = ...` clause.
- **Graceful degradation** — if Snowflake or the enablement store is down,
  the agent should say so and still be useful, not fail the whole
  conversation mid-call-prep.
- **Consider the enterprise variant as a separate roadmap item**, not a
  bolt-on — Ines's account shape (5 accounts, 12 stakeholders, 6-month
  cycles) needs a genuinely different tool, not more flags on this one.
- **Manager rollups, CSM collaboration, and admin-tunable flag thresholds**
  — named in `docs/PRD-phase1-dashboard.md`'s Phase 2/3, not attempted here;
  see `frontend/lib/roadmap.py` for the full staged list.
