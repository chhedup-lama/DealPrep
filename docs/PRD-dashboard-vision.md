# PRD — AE Call-Prep Dashboard

**Status:** Superseded — kept as historical reference, not the canonical PRD.
See `docs/PRD.md` for the case-submission narrative, and
`docs/PRD-phase1-dashboard.md` for the current canonical dashboard PRD
(supersedes this document's phase framing — its Phase 1/1B/1C/1D track is
now built in `frontend/`). This draft is retained because the interview
quotes in §2 and the "known gaps" self-critique in §14 are evidence this
repo's PRD and roadmap decisions are grounded in, and aren't duplicated in
the newer documents.

**Owner:** Chhedup Lama
**Date:** 2026-07-15
**Relationship to the case submission:** This is a stretch artifact, not the
case deliverable. The actual submission is the conversational agent in
`src/` and `docs/one-pager.md`, which deliberately stayed inside the brief's
scope ("a conversational assistant, not a dashboard"). This document sketches
where that agent goes if it became a real internal product — the kind of
roadmap conversation the technical deep-dive is likely to pull on.

---

## 1. Executive summary

The CLI prototype proved something narrower and more useful than "an AE can
chat with an LLM about an account": a rule-based scan over Personio's own CRM
data can reliably surface the things an AE is *most likely to miss* — a
stalled deal, a renewal with no Economic Buyer, a customer whose usage just
dropped — and hand them off to an LLM only for narration and follow-up, not
detection. That split (deterministic signal, conversational delivery) is the
core of this product.

This PRD describes what that becomes as a daily-use tool: a dashboard an AE
opens each morning, a **Get Insights** action that scans their entire book of
accounts (not one account at a time, on request, like the CLI), master views
of the underlying data, a per-account detail page with an embedded chat
scoped to that account, and a portfolio-wide chat on the home page for
cross-account questions.

## 2. Problem & opportunity

The AE interviews (`data/enablement/13_ae_interview_notes.md`) are the
evidence base for this entire document. Three things came up unprompted,
across independent conversations:

> "The honest prep is more like 10 minutes. And in those 10 minutes I'm
> bouncing between Salesforce, Gong, the Drive folder where the battlecards
> live, and sometimes a Slack thread." — Lena

> "My problem isn't 'I don't have time to prep'... my problem is I don't
> notice the thing until it's too late." — pattern across Lena, Thomas, Ines

> "If a tool tells me a wrong fact, I lose three months of trust in it." —
> Sofia

The opportunity isn't "make Q&A faster." It's: build the thing that reliably
notices what a busy AE, working 30–40 accounts, structurally can't hold in
their head — and be right often enough that Marcus (explicitly skeptical,
"I'll try it once... if it doesn't earn its keep on the first interaction, I
won't come back") keeps using it.

## 3. Goals

- Cut real prep time for a portfolio of 30–40 accounts from ~30 min/week of
  scattered lookups to a few minutes of triaged, prioritized review.
- Surface the specific class of miss the interviews describe: stalled deals,
  missing decision-makers, usage decline, competitor activity — before the
  AE notices it themselves, not after.
- Preserve trust as the top design constraint: every surfaced insight must be
  traceable to real data, never an LLM guess.

## Non-goals (this phase)

- Not a CRM. Salesforce (or whatever CRM Personio actually runs) remains
  system of record; this tool reads it, never writes to it.
- Not built for the enterprise AE motion. Ines's interview is explicit that
  enterprise AEs (5 accounts, 12 stakeholders, 6-month cycles) have a
  different problem — "connecting dots across stakeholders," not "get
  context fast." Building one tool for both "is unlikely to land well," in
  her words. Out of scope here; see Phase 3.
- Not a communications platform. Sending anything to a customer (email,
  WhatsApp, SMS) is explicitly Phase 2, not Phase 1.
- No write-back to Snowflake/CRM in this phase — read-only.

## 4. Personas

**Primary — Mid-market AE.** The case's persona: ~18 months tenure, EMEA,
owns 30–40 accounts, mixed customer/prospect book. Matches Sofia's and
Thomas's interviews most closely. This PRD is written for her.

**Secondary, named but out of scope for Phase 1 — Sales Manager.** Wants a
rollup of team-level risk (which renewals are at risk this month, across
their reports' books), not per-account chat. This is a natural Phase 2 item
once RBAC exists — a Manager role that sees an aggregated insight feed across
their team's `OWNER_AE` accounts, not a redesign of the product.

**Explicitly excluded — Enterprise AE (Ines's shape).** Fewer accounts, more
stakeholders, longer cycles. Her own words: "don't try to build one thing for
both of us." Flagged as a Phase 3 candidate, not silently ignored.

## 5. Day in the life

1. **Login.** The AE authenticates; every view from here on is scoped to
   accounts where `OWNER_AE` matches her.
2. **Home dashboard.** Empty or stale until she clicks **Get Insights**.
3. **Get Insights.** One click triggers a scan across her entire book — every
   account she owns, run through the same rule-based flag logic the CLI
   already has (`build_account_brief()`'s six checks), in one batch rather
   than one account at a time. The dashboard populates with a prioritized
   feed: "3 accounts need attention today," each a compact card (account
   name, the flag, one line of why).
4. **Master views.** She can also browse the underlying data directly:
   Accounts (full list, filterable, flag badges), Opportunities, Contacts,
   Tickets — the same tables the CLI already queries, now as browsable lists
   instead of only reachable through a query the agent decides to run.
5. **Click into an account.** The account detail page opens: the brief at
   the top (same content the CLI leads with), tabs below for activity,
   opportunities, usage trend, tickets, and the stakeholder map.
6. **Chat, scoped to this account.** An embedded chat on the account page —
   same agent, same tools, but the account is already pinned, so she can just
   ask "what should I open with" without naming the account again.
7. **Back to the home page.** For a portfolio-wide question ("which of my
   renewals are at risk this month," "who am I meeting today that I haven't
   prepped for") she uses the generic home-page chat instead — broader tool
   access across her whole book, not pinned to one account.

## 6. Functional requirements

### 6.1 Auth & multi-AE scoping
- Login identifies the AE; every query (accounts, opportunities, activities,
  usage, tickets, contacts) is filtered by `OWNER_AE = <logged-in AE's
  email>`. The schema already carries this field on `CRM.ACCOUNTS` — no data
  model change needed, just an added `WHERE` clause plumbed through every
  existing query function in `src/tools.py`.

### 6.2 Get Insights (the new capability)
This is the one thing the CLI genuinely doesn't do today — the CLI computes
a brief for *one* account, on request. Get Insights computes it for *every*
account an AE owns, proactively, in one action.

- Triggered by an explicit button, not fully automatic (at least in Phase 1)
  — the AE decides when to run it, keeping cost and staleness predictable.
- Runs the same six deterministic flag checks from `build_account_brief()`
  (stalled opportunity, missing Economic Buyer/Champion on >€30k deals,
  usage decline, open P1/P2 ticket, quiet account, competitor mention)
  across the AE's full account list.
- **Deliberately rule-based, not an LLM call per account.** Running an LLM
  judgment over 30–40 accounts on every click would be slow, expensive, and
  — more importantly — inconsistent in a way that directly undermines
  Sofia's trust bar ("I'd rather it told me less and was right"). The LLM's
  job stays narration and chat, not detection.
- Output: a ranked feed. Accounts with more/higher-severity flags surface
  first. Each card names the flag plainly (no jargon), links to the account
  detail page, and can be dismissed or snoozed.

### 6.3 Master data views
- **Accounts** — full list scoped to the AE, filterable (status, segment,
  region, flag present/absent), sortable, with flag badges pulled from the
  latest Get Insights run.
- **Opportunities** — list view (stage, amount, close date, days in stage),
  filterable by stage/type.
- **Contacts** — stakeholder list, filterable by persona type (Economic
  Buyer / Champion / Influencer / Technical / User) — directly useful for
  spotting the "no Champion on this account" pattern across the whole book,
  not just one account at a time.
- **Tickets** — support ticket list, filterable by status/priority.

### 6.4 Account detail page
- Brief at the top (identical content/logic to what the CLI's
  `get_account_brief` tool returns), rendered as flag cards, not a text
  block.
- Tabs: Activity, Opportunities, Usage, Tickets, Contacts — each backed by
  the corresponding existing tool function (`get_activities`,
  `get_opportunities`, `get_usage_trend`, `get_tickets`, `get_contacts`).
- Embedded chat, pinned to this account's `account_id` — reuses `agent.py`'s
  tool set and system prompt unchanged; the only difference from the CLI is
  that the account is already resolved, so the first turn skips
  `find_account`.

### 6.5 Home-page generic chat
- Same underlying agent, but without an account pinned — can call
  `find_account` and reason across the AE's whole book. Handles portfolio
  questions the account-scoped chat structurally can't: "which of my
  renewals close this month," "do I have any accounts with an open P1 right
  now."

### 6.6 Insight feed lifecycle
- Each Get Insights run produces a feed the AE can dismiss (acknowledged,
  won't resurface unless the underlying condition changes) or leave open.
  Dismissal state matters for Phase 2 telemetry (did the AE act on the flag)
  and is worth capturing even though there's no notification system yet to
  act on it.

## 7. Information architecture

```
Home
├── Get Insights (action) → populates Insight Feed
├── Insight Feed (cards, ranked, dismissible)
├── Generic chat (portfolio-wide, unpinned)
└── Master views
    ├── Accounts (list) → Account Detail
    │                       ├── Brief (flags)
    │                       ├── Tabs: Activity / Opportunities / Usage / Tickets / Contacts
    │                       └── Account-scoped chat (pinned)
    ├── Opportunities (list)
    ├── Contacts (list)
    └── Tickets (list)
```

## 8. Design principles

Translated directly from the interview findings into UI rules, not left as
abstractions:

- **Flags, not paragraphs.** The insight feed and account brief render as
  short cards with a badge and one line, matching Thomas's "two lines...
  anything longer I'm going to skim." Long explanation lives one click away,
  not in the default view.
- **Show the reason, always.** Every flag card names *why* it fired (e.g.
  "usage down 17% MoM, Apr→May") — never a bare "this account needs
  attention." An unexplained flag is exactly the kind of thing that costs
  three months of trust if it's ever wrong.
- **Progressive disclosure.** Summary first everywhere — feed card → account
  brief → tab detail → chat drill-down. Nothing forces the AE through detail
  she didn't ask for.
- **The chat never contradicts the data views.** Both read from the same
  tool functions; the chat is a different way to ask, not a different source
  of truth.

## 9. Non-functional requirements

- **Performance.** A single `build_account_brief()` call issues roughly five
  Snowflake queries. Get Insights running that across 30–40 accounts is
  150–200 queries per click — needs batching (e.g. one set-based query per
  data type across all owned accounts, rather than looping the existing
  per-account functions) rather than a naive fan-out, or the button will
  feel slow. This is a real architectural change from the CLI's per-account
  query shape, not a minor optimization.
- **Security.** The CLI today runs on one shared Snowflake PAT for the whole
  team — fine for a prototype, not for a multi-AE product where `OWNER_AE`
  scoping is meant to be a real boundary. Production needs per-AE identity
  (or an application-layer service account with row-level enforcement) so
  scoping isn't just a `WHERE` clause an AE could bypass by asking the right
  question.
- **Observability.** Minimum bar: log which flags fired, which were
  dismissed, which account pages got opened from a flag — the raw material
  for the success metrics below, and for Phase 2 triggers.

## 10. Success metrics

- **Activation** — % of AEs who click Get Insights on a given work day.
- **Efficacy** — % of surfaced flags that lead to a follow-up action
  (account opened, chat drill-down, or — once available — a logged CRM
  activity) rather than being dismissed unread.
- **Efficiency** — self-reported prep-time reduction, sampled periodically
  (this is closer to Lena's actual "10 vs 30 minutes" framing than any
  system-measured proxy).
- **Retention** — the literal bar Marcus set: does an AE who tries it once
  come back the next day. This is the metric that matters most and the one
  most likely to catch a bad launch early.

## 11. Technical approach (high level)

- A thin API layer wrapping the existing `src/tools.py` query functions and
  `src/agent.py`'s tool-runner logic — the backend isn't rebuilt, it's
  exposed over HTTP instead of a CLI loop.
- Get Insights becomes a batch job (see Performance above) rather than N
  calls to the existing single-account function.
- Frontend framework is an open decision, deliberately not prescribed here —
  this PRD is scope and behavior, not a stack choice.
- Auth needs a real identity provider tied to `OWNER_AE`; out of scope to
  design in this document beyond noting the requirement.

## 12. Phased roadmap

**Phase 1 — this PRD.** Dashboard, Get Insights, master views, account
detail, account-scoped chat, home-page portfolio chat, multi-AE auth and
data scoping.

**Phase 2 — named explicitly per current ask:**
- **RBAC** — Manager/Admin roles beyond plain AE (unlocks the Sales Manager
  persona's team-rollup use case).
- **Triggers** — scheduled/proactive insight scans (not just on-click),
  push notifications when a new high-severity flag appears.
- **Communication channels** — WhatsApp, SMS, email. Two distinct use cases
  worth separating when this gets scoped for real: AE-facing nudges ("your
  Halcyon renewal just went quiet") versus any customer-facing channel,
  which is a materially different trust and compliance surface and should
  not be assumed to ship together.

**Phase 3 — candidates, explicitly flagged as open questions, not
commitments:**
- Enterprise AE variant (Ines's shape — different information architecture
  entirely, not a filtered version of this one).
- Delivery embedded in tools AEs already live in (Salesforce, Slack) instead
  of a standalone app — directly responsive to Lena's "bouncing between four
  tools" complaint, and possibly a bigger lever than anything in Phase 1 or 2.

## 13. Risks & open questions

- **Cost/latency at portfolio scale.** Mitigated in this design by keeping
  the scan itself rule-based (no LLM cost per account); the open question is
  whether the batched-query approach in §11 is fast enough for a
  synchronous button click or needs to become async with a "scanning..."
  state.
- **Data freshness.** The CLI computes "as of" from the latest activity date
  in the data on every call. A dashboard needs an explicit answer to "how
  stale can the insight feed be before it's shown" — not addressed here.
- **Shared-credential security gap.** Called out in §9 as a real gap, not
  hypothetical — today's prototype genuinely runs on one shared PAT.
- **Is a standalone app even the right call?** Lena's complaint is about
  tool sprawl, and this PRD proposes another tool. Phase 3's
  embed-in-Salesforce idea may be the more honest answer than a polished
  standalone dashboard — worth deciding before investing heavily in Phase 1
  frontend work.

## 14. Known gaps (self-critique)

Found in review, not yet resolved in the design above. Ordered roughly by
how much each would hurt the core loop if shipped unaddressed — the first
two are structural enough that they'd undermine the product even if
everything else in this PRD were built perfectly.

1. **No calendar/schedule awareness.** The case persona is defined by
   back-to-back calls, but Get Insights ranks purely by flag severity — it
   doesn't know she has Fjord in 20 minutes and Halcyon at 2pm. Without
   "what am I meeting today" as the primary lens, the AE still has to
   cross-reference her calendar against the feed by hand, which is close to
   the exact tool-sprawl problem this product exists to remove.
2. **No noise-control model for the insight feed.** Six independent flags,
   no weighting, no cap. If 25 of 35 accounts flag something, the feed
   becomes the wall of information the product was supposed to replace.
   Needs an explicit severity score and a cap on what surfaces by default,
   not just "more flags sort higher."
3. **No feedback loop for flag quality.** Nothing lets an AE mark a flag
   wrong or point out a miss. Flags are the entire value proposition — if
   precision drifts silently, the product rots without anyone noticing.
   Needs a correction mechanism and a tracked precision metric, not just the
   softer "% acted on" already in §10.
4. **No CSM in the picture.** The playbook is explicit that renewals are a
   joint AE + CSM motion ("CS owns the relationship, the AE leads the
   commercial conversation"), but this PRD has no CSM persona and no
   handling of what happens when a renewal flag duplicates or contradicts
   what the CSM already knows.
5. **Thomas's specific ask — distinguishing whose activity is whose — isn't
   modeled.** He wants "the activity from the SDR that touched the account,"
   distinct from his own notes. The Activity tab (§6.4) is generic; nothing
   surfaces *who* logged an activity.
6. **No empty/loading/error states defined.** Zero flags across the whole
   book, Snowflake down mid-scan, a slow Get Insights run — none of these
   have a designed UX. For a trust-sensitive tool, an ambiguous failure is
   worse than a missing feature.
7. **Phase 2 comms channels have no compliance story.** WhatsApp/SMS/email
   to customers across DACH/Nordics/Iberia/France is a GDPR consent surface
   with no mention anywhere in §12 — notable given Personio's own product is
   HR compliance software.
8. **Tool-sprawl mitigation is deferred to Phase 3 when a cheap Phase 1 fix
   exists.** §13 already admits Lena's complaint cuts against building a
   fifth tool. A plain "open in Salesforce" link-out from the account page
   costs almost nothing and answers the risk now instead of only naming it.
9. **No mobile consideration.** AEs prep in 10-minute gaps, often on the
   move. Nothing in §9 addresses phone/tablet use.
10. **No admin surface for flag thresholds.** The €30k MEDDIC cutoff,
    21-day quiet window, 10% usage-decline threshold, and 30-day stall are
    hardcoded constants today (`src/tools.py`). Sales ops will want to tune
    these without a code deploy — belongs with RBAC in Phase 2 but isn't
    named there yet.

If forced to fix only two before a v1 build: **#1 and #2**. They're the ones
most likely to make the core loop fail in practice rather than just feel
incomplete. #3 is the one most likely to come up if pushed on "how do you
know this stays good."

## 15. Appendix

- Data model reference: `docs/data_dictionary.md`
- Case submission this extends: `docs/one-pager.md`
- Frontend implementation plan: `docs/FRONTEND-BUILD-PLAN.md`
- Backend functions this PRD's features build directly on:
  `src/tools.py` (`find_account`, `build_account_brief`, `get_activities`,
  `get_opportunities`, `get_usage_trend`, `get_tickets`, `get_contacts`),
  `src/retrieval.py` (`search_enablement`), `src/agent.py` (tool
  definitions, system prompt — reused unchanged for both chat surfaces).
