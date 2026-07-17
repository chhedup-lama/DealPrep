# AE Call-Prep Agent (Personio case study)

A conversational assistant that helps an Account Executive prepare for an
account call. It combines live CRM/product/support data from Snowflake with
Personio's sales enablement content (playbook, ICP, battlecards, objection
handling, pricing, case studies) into a single chat interface — multi-turn,
so the AE can ask a question and drill into specifics.

**Status:** working prototype. See `docs/one-pager.md` for scope, architecture,
and quality notes.

## Setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # fill in your Snowflake PAT and Anthropic API key
```

## Run the agent

```
python -m src.cli
```

Ask about any account by name, e.g. "What should I know before my call with
Brightline Retail?" or "I have a renewal with Halcyon Hospitality tomorrow."
The agent resolves the account, pulls a proactive brief (flagging things like
stalled deals, usage decline, missing decision-makers, and competitor
mentions), and answers follow-ups by drilling into activities, opportunities,
usage, tickets, contacts, or the enablement docs. Type `quit` to exit.

## Stretch: Streamlit dashboard

The case submission is the CLI agent above. `frontend/` is an additional,
not-required demo that reuses the same `src/agent.py`/`src/tools.py`
unchanged behind a Get-Insights dashboard (ranked risk feed, account/
opportunity/contact/ticket views, account-scoped and portfolio-wide chat).
See `docs/PRD.md` for the product vision it implements and
`docs/FRONTEND-BUILD-PLAN.md` for the build approach.

```
streamlit run frontend/app.py
```

## Data exploration

The sandbox schema was inspected once, up front, before designing the query
tools:

```
python scripts/explore_data.py
```

This writes `docs/data_dictionary.md` with every table, its columns/types, a
row count, and sample rows across the `CRM`, `PRODUCT`, and `SUPPORT` schemas.
No need to re-run it unless the sandbox data changes.

## Enablement content

The sales enablement docs (from the provided Google Drive folder) live under
`data/enablement/` as Markdown. The agent's `search_enablement` tool does
keyword search over these — see `data/enablement/README.md`.

## Layout

```
src/
  snowflake_client.py   PAT-auth connection helper
  tools.py              account-scoped Snowflake queries + heuristic flags (build_account_brief)
  retrieval.py           keyword search over the enablement docs
  agent.py               system prompt, tool definitions, Claude tool-runner loop
  cli.py                 terminal chat loop
frontend/                 stretch: Streamlit dashboard over the same src/ modules (see above)
scripts/explore_data.py  one-off schema/data assessment
data/enablement/         local copies of the Drive sales-enablement docs
docs/
  PRD.md                  canonical product PRD (case scope + production vision)
  one-pager.md            case submission: what was built, cut, and why
  data_dictionary.md      generated Snowflake schema reference
  PRD-dashboard-vision.md historical draft, superseded by PRD.md
  FRONTEND-BUILD-PLAN.md  build plan the frontend/ implementation follows
```
