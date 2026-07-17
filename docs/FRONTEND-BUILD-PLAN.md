# Frontend Build Plan — AE Call-Prep Dashboard

**Status:** Implementation plan, not yet built
**Relationship to other docs:** Implements `docs/PRD-dashboard-vision.md`
§6 (functional requirements), reusing `src/tools.py` and `src/agent.py`
unchanged as the backend.

---

## Two paths, pick one deliberately

There are two honest ways to build this, and they trade off differently. Both
are described here so the choice is explicit rather than accidental.

| | **Path A — Demo/fast** | **Path B — Production-shaped** |
|---|---|---|
| Stack | Streamlit (Python only) | FastAPI backend + React/TS frontend |
| New service to run | None — one `streamlit run` process | Two processes (API + web app) |
| Reuses `src/tools.py` / `src/agent.py` | Directly, in-process, no changes | Through a thin HTTP wrapper |
| Auth | Stubbed (a dropdown to pick an AE) | Real (matches PRD §6.1) |
| Get Insights performance | Naive per-account loop, visibly slow at 30+ accounts | Batched queries per PRD §9 |
| Effort | Hours | Days-to-weeks |
| Right for | Showing the *idea* working end-to-end — a live demo artifact | An actual internal tool Personio would run |

**Recommendation: build Path A now.** It's the one that's actually achievable
given where this project is, and it proves every functional requirement in
PRD §6 works against real data — which is the thing worth demonstrating.
Path B is documented below as the real target architecture, not as this
week's task.

---

## Path A — Streamlit demo

### Why Streamlit specifically
It's Python-only, so `build_account_brief()`, `run_turn()`, and every
existing tool function get called in-process — no API layer to build first.
Streamlit's `st.chat_message` / `st.chat_input` map directly onto the
existing multi-turn `messages` list pattern in `src/cli.py`. This is the
fastest path to a clickable version of every screen in PRD §5–§6, not a
toy — it's a legitimate way to demo an internal tool.

### What it deliberately doesn't solve
Per the two-path table above: no real auth, no batched Get Insights (a
30-account scan will visibly take tens of seconds — acceptable for a demo,
called out live rather than hidden), no persisted dismiss/snooze state
(session-only), single AE session at a time. These map directly to gaps #1,
#2, #6, #9, #10 in the PRD's "Known gaps" section — Path A doesn't close
them, it makes them visible and demoable rather than invisible.

### Structure

```
frontend/
  app.py                 entry point — Home page (Get Insights + insight feed + portfolio chat)
  pages/
    1_Accounts.py         master view: accounts list, filters, flag badges
    2_Account_Detail.py   brief + tabs + account-scoped chat (account_id via query param)
    3_Opportunities.py    master view
    4_Contacts.py          master view
    5_Tickets.py           master view
  lib/
    insights.py            get_insights_for_ae(owner_ae) -> loops build_account_brief() per account
    state.py                st.session_state helpers (chat history per page, dismissed flags)
```

Everything under `lib/` calls straight into the existing `src/tools.py`,
`src/retrieval.py`, and `src/agent.py` — no duplication of query or agent
logic, only UI-layer code is new.

### Milestones

1. **`get_insights_for_ae(owner_ae)`** in `lib/insights.py` — loops
   `find_account`-scoped account list (add an `OWNER_AE` filter to
   `find_account`/a new `list_accounts(owner_ae)` in `src/tools.py`), calls
   `build_account_brief()` per account, returns accounts with ≥1 flag,
   sorted by flag count. *(Naive version of PRD §6.2 — batching deferred to
   Path B.)*
2. **Home page** (`app.py`) — AE picker (stand-in for auth), **Get Insights**
   button wired to milestone 1, renders results as flag cards. Below it, a
   portfolio chat using `st.chat_input` wired to `agent.run_turn()` with no
   account pinned — this is PRD §6.5.
3. **Accounts master view** (`pages/1_Accounts.py`) — table from
   `list_accounts(owner_ae)`, filter widgets (status/segment/region), flag
   badge column sourced from the last Get Insights run
   (`st.session_state`). Click-through to Account Detail.
4. **Account Detail page** (`pages/2_Account_Detail.py`) — reads
   `account_id` from the URL query param, renders `build_account_brief()` as
   flag cards, then `st.tabs` for Activity / Opportunities / Usage / Tickets
   / Contacts, each backed by the matching `src/tools.py` function. Chat at
   the bottom via `st.chat_input`, `agent.run_turn()` with the account's
   first turn pre-seeded so it skips `find_account` — this is PRD §6.4.
5. **Remaining master views** (Opportunities, Contacts, Tickets) — same
   pattern as milestone 3, simpler (no flag badges).
6. **Empty/loading/error states** — addresses gap #6 directly: a spinner
   during the Get Insights scan (it's slow in this path, so this matters
   more here than it will in Path B), an explicit "no flags — you're clear"
   empty state, and a visible error banner if a Snowflake call fails instead
   of a stack trace.

Milestones 1–4 alone already demonstrate every core loop in the PRD's day-in-
-the-life narrative (§5) end to end. 5–6 round it out.

### New backend surface needed

One addition to `src/tools.py`, nothing else changes:

```python
def list_accounts(owner_ae: str) -> list[dict]:
    return run_query(
        "SELECT ACCOUNT_ID, COMPANY_NAME, STATUS, SEGMENT, REGION "
        "FROM PERSONIO.CRM.ACCOUNTS WHERE OWNER_AE = %s ORDER BY COMPANY_NAME",
        (owner_ae,),
    )
```

Everything else — `build_account_brief`, `get_activities`,
`get_opportunities`, `get_usage_trend`, `get_tickets`, `get_contacts`,
`search_enablement`, `run_turn` — is called as-is.

---

## Path B — Production-shaped (FastAPI + React)

Documented for completeness / the technical deep-dive, not scheduled.

- **Backend:** FastAPI wrapping `src/tools.py` and `src/agent.py` behind
  REST endpoints (`GET /accounts`, `GET /accounts/{id}/brief`,
  `POST /insights/scan`, `POST /chat`). The insight scan endpoint replaces
  milestone 1's per-account loop with the batched, set-based queries called
  for in PRD §9 (one query per data type across all owned accounts, not N
  queries per account).
- **Frontend:** React + TypeScript, matching the IA in PRD §7 as real routed
  pages instead of Streamlit's multipage convention.
- **Auth:** a real identity provider issuing a session tied to `OWNER_AE`,
  replacing Path A's AE picker.
- **Migration path from A to B:** Path A's `lib/insights.py` and the chat
  wiring port almost directly into FastAPI route handlers — the Streamlit
  build isn't throwaway, it's the reference implementation for what each
  endpoint needs to return.

---

## Recommended next step

Build Path A, milestones 1–4, against the existing Snowflake sandbox and
enablement docs already in this repo. That's a working, clickable dashboard
demonstrating the full day-in-the-life flow from the PRD, buildable directly
on top of what already exists in `src/`.
