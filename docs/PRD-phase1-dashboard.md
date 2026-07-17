# PRD — DealPrep AI: AE Call-Prep Dashboard & Assistant

**Status:** Canonical PRD for the dashboard build (`frontend/`) — supersedes
the phase framing in `docs/PRD-dashboard-vision.md` and `docs/PRD.md` §13
for anything dashboard-related. `docs/PRD.md` remains canonical for the
case-submission narrative itself (the conversational agent in `src/`).

**Owner:** Chhedup Lama
**Context:** Personio Internal AI PM case study
**Relationship to the case submission:** This is not the core case
deliverable. The core case deliverable remains the working conversational
agent. This PRD describes how that prototype evolves into a real internal
product for Account Executives — and, as of this build, most of its
"Phase 1" track (base dashboard + 1B scoring/grouping + 1C account-detail
intelligence + 1D trust loop) is implemented in `frontend/`.

---

## 1. Executive Summary

DealPrep AI is an internal AI assistant and dashboard that helps Account
Executives prepare for customer and prospect calls by combining CRM data,
product usage, support history, recent activity, sales playbooks,
battlecards, pricing guidance, and objection-handling content.

The prototype proves a narrower but important point: an AE should not have
to manually search Salesforce, usage dashboards, ticketing tools, and
enablement documents before every call. The assistant should surface the
most important risks, opportunities, and recommended actions before the AE
asks.

The dashboard layer sits on top of the conversational assistant. When an AE
clicks **Generate Insights**, the system scans their book of accounts,
prioritizes upcoming calls and risky accounts, and presents the most urgent
items as insight cards. Each card shows what matters, why it matters, how
urgent it is, and what the AE should do next. Clicking into a card opens a
detailed account-prep view with evidence, account history, stakeholders,
product usage, support issues, deal context, next-best action, and a
suggested call script. An account-scoped assistant then lets the AE drill
deeper.

The product principle is simple:

> Deterministic systems detect the signal.
> The LLM explains, summarizes, and helps the AE act.

This keeps the product trustworthy. The LLM should not invent risk. It
should explain risk using evidence from real account data and enablement
content.

## 2. Problem

Personio's Account Executives spend a meaningful amount of time preparing
for calls. The work is fragmented across Salesforce-style CRM data, recent
activities and meeting notes, opportunity stage and deal value, product
usage, support tickets, sales playbooks, competitive battlecards, pricing
guidance, objection-handling guides, and customer case studies.

Some of this prep is high-value thinking. But much of it is operational
friction. The bigger problem is not only "I don't have time to prep." It
is: **"I don't notice the important thing until it is too late."**

Examples:
- A renewal call is happening in three hours, but the AE has not seen that
  product usage dropped last month.
- A high-value expansion opportunity has no Economic Buyer attached.
- A churn-risk customer has an unresolved P1 support ticket.
- A competitor was mentioned in the last activity note, but the AE has not
  reviewed the battlecard.
- A discovery call with a hot prospect is tomorrow, but the AE has not
  mapped the prospect to the ICP.

The product opportunity is to build a trusted assistant that notices these
issues early, prioritizes them, and helps the AE prepare quickly.

## 3. Target Persona

**Primary — Mid-Market AE.** ~18 months tenure, EMEA, owns 30–40 accounts,
mix of renewals/expansions/discovery calls, works under time pressure, does
not want long paragraphs or generic AI summaries, loses trust quickly if
the assistant states incorrect facts.

**Secondary, out of scope for Phase 1 — Sales Manager.** Wants team-level
risk visibility: risky renewals, stalled high-value opportunities, missing
stakeholders, unresolved support issues across the team. Better suited to
Phase 2 once RBAC exists.

**Explicitly excluded in Phase 1 — Enterprise AE.** Fewer accounts, more
stakeholders, longer sales cycles, more complex stakeholder mapping, more
need for relationship intelligence than fast triage. The Phase 1 product
should not try to serve both mid-market and enterprise AE workflows with
the same UI.

## 4. Goals

**Product Goals**
1. Reduce account-call preparation time.
2. Surface high-risk accounts and upcoming-call risks before the AE misses them.
3. Prioritize accounts by urgency, deal value, account importance, and time left before the call.
4. Help AEs quickly understand current state, history, risks, and next-best action.
5. Provide trusted, evidence-backed recommendations.
6. Enable multi-turn drilldown through an account-scoped assistant.
7. Build a habit-forming daily workflow that AEs would actually use.

**User Goals** — the AE should be able to answer: Who am I speaking to?
What is the current state of this account? What has happened recently?
What are the biggest risks? What should I do before the call? What should
I say on the call? Which objection or competitor angle should I prepare
for? What is the next-best action after the call? Why is the assistant
recommending this?

**Business Goals** — improve renewal/expansion preparation, reduce missed
risk signals, increase AE productivity, improve consistency of sales
execution, increase enablement content usage, create a foundation for
future internal AI workflows across GTM teams.

## 5. Non-Goals

- **Not a CRM.** Salesforce remains system of record; DealPrep AI reads
  data but does not write back in Phase 1.
- **Not a fully autonomous sales agent.** No emailing customers, updating
  CRM records, negotiating pricing, or making commercial decisions.
- **Not a generic chatbot.** Specifically an AE call-prep assistant
  grounded in account data and enablement content.
- **Not a replacement for AE judgment.** The AE remains accountable for
  customer communication and commercial strategy.
- **Not enterprise AE workflow in Phase 1.**

## 6. Product Overview

**Product Name:** DealPrep AI

**Positioning:** DealPrep AI helps Account Executives prepare for renewal,
expansion, and discovery calls by combining account data, product usage,
support signals, recent activity, and sales enablement guidance into a
trusted conversational briefing.

## 7. Core User Journey

1. **AE opens dashboard** — home view scoped to accounts owned by that AE.
2. **AE clicks "Generate Insights"** — scans the AE's book of accounts (and,
   in a production version, calendar-aware upcoming calls) for calls
   happening soon, high-value opportunities, renewal/churn risk, stalled
   deals, missing stakeholders, usage decline, support escalations, recent
   competitor mentions, quiet accounts, open next steps, and relevant
   playbook/battlecard needs.
3. **Insight feed appears** — a prioritized feed of cards grouped by
   urgency and action type: Prepare now, High-risk renewals, Expansion
   opportunities, Discovery calls, Missing stakeholders, Support risk,
   Competitive risk, Low priority/monitor.
4. **AE clicks an insight card** — opens an account-detail page: why
   flagged, time left before the call, current account state, deal/renewal
   context, recent activity summary, key contacts and stakeholder gaps,
   product usage trends, support-ticket summary, revenue/deal value, risk
   drivers, recommended next-best action, suggested call script, evidence
   trail, account-scoped assistant.
5. **AE asks follow-ups** — "Why is this churn risk high?", "What did we
   last discuss?", "Who should I involve?", "What objection should I
   expect?", "Give me a better opening for this call.", "What should I send
   after the call?", "Which case study should I use?" The assistant answers
   using account context and enablement content.

## 8. Generate Insights — Core Capability

**Purpose:** converts a scattered account book into a prioritized action
feed. The AE should not need to ask "Which accounts should I worry about?"
— the product should proactively answer "These are the accounts you need
to care about first, here is why, and here is what to do."

**Inputs:**
- CRM/Snowflake data — accounts, contacts, opportunities, activities,
  product usage, support tickets, account owner, opportunity amount/stage,
  renewal date, close date, last activity date, contact roles, competitor
  mentions.
- Calendar data (Phase 1B or production) — upcoming calls, call time,
  account associated with call, participants, meeting title/type, time left
  before call. *(Not available in the current Snowflake sandbox — see
  `docs/data_dictionary.md`. This build proxies time-urgency with
  days-to-nearest-close-date instead; real calendar integration is
  Phase 2.)*
- Enablement content — sales playbook, ICP document, competitive
  battlecards, objection-handling guide, pricing cheat sheet, customer case
  studies.

**Output:** a ranked set of insight cards, each with account name, insight
title, priority badge, urgency level, time left before call, account
importance, deal value, risk type, one-line summary, recommended action,
evidence chips, and a CTA to open account details.

## 9. Insight Feed UX

**9.1 Feed Grouping** — Prepare Now (calls happening soon), High-Risk
Renewals (usage decline, open P1/P2, no recent activity, negative
sentiment, renewal close date approaching, missing Economic Buyer,
competitor mention), Expansion Opportunities (high usage, multiple active
teams, positive engagement, expansion opp open, pricing/packaging fit,
relevant case study), Discovery Calls (hot prospect, good ICP fit, recent
activity, competitor mention, high opp value, missing discovery info),
Missing Stakeholders (no Economic Buyer/Champion/Technical Buyer, unknown
decision process, single-threaded relationship), Monitor (lower-priority,
no immediate action).

**9.2 Insight Card Design** — Priority Badge (Critical/High/Medium/Low),
Urgency, Account Importance (Strategic/High ARR/Standard), Deal Value, Risk
Tags, Snippet (one short sentence), Recommended Action (one clear next
step), Evidence Chips (Usage, Ticket, Activity, Opportunity, Playbook), CTA
(Open prep brief).

Example:
> **Critical — Prepare Now — Fjord Systems** — Renewal call in 3 hours ·
> €82k ARR · Churn risk. **Why it matters:** Usage dropped 22%
> month-over-month and a P1 payroll ticket is still open. **Recommended
> action:** Open with the support issue, confirm resolution path, then
> reframe renewal around payroll reliability and adoption recovery. Tags:
> Renewal Risk, Usage Decline, Open P1, High ARR, Call Today.

## 10. Scoring and Prioritization

Without a scoring model, the insight feed becomes noisy. If 25 of 35
accounts show some kind of flag, the AE is back to manual triage. The
product needs a transparent, deterministic (not ML) scoring model.

**Priority Score = Time Urgency + Deal Value + Account Importance + Risk
Severity + Actionability.**

**Time Urgency** — <1hr: 40, 1–4hr: 35, today: 30, tomorrow: 20, this week:
10, no scheduled call: 0. *(This build's day-based adaptation —
`src/scoring.py` — see note under §8 Inputs.)*

**Deal Value** — >€100k: 30, €50–100k: 20, €20–50k: 10, <€20k: 5.

**Risk Severity** — Open P1 ticket: 30, Usage decline >20%: 25, Renewal in
next 30 days: 25, Competitor mention: 20, No Economic Buyer: 20, No
Champion: 15, No activity in 21 days: 15, Opportunity stalled >30 days: 15.

**Actionability** — Clear next action available: 15, Relevant battlecard
exists: 10, Relevant case study exists: 10, Pricing objection guidance
exists: 10, No clear action: 0.

**Priority Bands** — 90+: Critical, 70–89: High, 40–69: Medium, <40: Low.

## 11. Account Detail Page

When the AE clicks a card, the account detail page should answer: "What do
I need to know before I get on this call?"

**Sections:** Header (account name, segment, region, owner AE,
ARR/opportunity value, renewal/close date, call time, time left before
call, priority score, risk level, open-in-Salesforce link); Why This Was
Flagged (evidence, not vague AI reasoning); Current State; What Has
Happened So Far; Key Stakeholders (highlighting gaps); Product Usage and
Adoption; Support and Risk; Opportunity and Revenue Context; Recommended
Next-Best Action (specific, not "follow up with the customer"); Suggested
Call Script; Relevant Enablement; Evidence Panel; Account-Scoped Assistant.

## 12. Functional Requirements

- **Auth & scoping** — login identifies AE; queries filtered by OWNER_AE;
  account lists scoped to the logged-in AE; future RBAC for
  Sales Manager/Admin.
- **Generate Insights** — click-triggered scan of owned accounts,
  calendar-aware urgency where available, deterministic rule checks, ranked
  and grouped cards with evidence, dismiss/snooze.
- **Insight Cards** — urgency, priority, account importance, deal value,
  reason, recommended action, tags, evidence chips, click-through to
  account detail.
- **Master Views** — Accounts, Opportunities, Contacts, Tickets, each
  filterable and scoped to the AE.
- **Account Detail Page** — brief, current state, why flagged, activity
  timeline, opportunities, usage trend, support tickets,
  contacts/stakeholders, next-best action, call script, evidence,
  account-scoped assistant.
- **Home-Page Portfolio Chat** — not pinned to a single account; answers
  cross-account questions like "Which of my renewals are at risk this
  month?" or "Where should I spend my next hour?"

## 13. Known Gaps Converted into Product Phases

**Phase 0 — Case Prototype.** Conversational assistant, account lookup,
structured data retrieval, enablement retrieval, renewal/discovery prep,
follow-up questions, simple quality guardrails. No dashboard, no calendar,
no proactive insight feed, no RBAC, no write-back, no production auth, no
full eval suite. *(Built — `src/`.)*

**Phase 1 — Dashboard MVP.** AE login and scoping, home dashboard, Generate
Insights button, insight feed, basic card ranking, account detail page,
master data views, account-scoped chat, portfolio-wide chat. *(Built —
`frontend/`.)*

**Phase 1B — World-Class Insight Feed.** Calendar awareness (proxied — see
§8), noise control, urgency scoring, feed grouping, priority bands,
time-left-before-call logic, deal value and account importance,
actionability scoring. Cap the default feed to the top 5–7 items, group
lower-priority items separately, explain why each card appears. *(Built —
`src/scoring.py`, `frontend/lib/insights.py`.)*

**Phase 1C — Account Detail Intelligence.** Current state, account
history, stakeholder map, product usage, support risk, opportunity state,
revenue context, recommended next-best action, suggested call script,
relevant enablement, evidence panel, account-scoped assistant. *(Built —
`frontend/pages/2_Account_Detail.py`.)*

**Phase 1D — Trust and Quality Loop.** Useful/Not useful on cards, wrong
reason feedback, already-handled dismissal reason, precision tracking by
flag type. Core metric: of the insights shown, how many did the AE agree
were useful, correct, and worth acting on? *(Built —
`frontend/lib/feedback.py`.)*

**Phase 2 — Team, Workflow, and Proactive Triggers.** Manager RBAC,
team-level risk dashboard, scheduled scans, proactive notifications, Slack
or email nudges, CSM collaboration layer, admin threshold settings,
Salesforce link-outs, Salesforce write-back for notes/tasks if approved,
real calendar integration, real per-AE Snowflake identity, batched
Get Insights queries. *(Not built — roadmap only.)*

**Phase 3 — Embedded and Enterprise Variants.** Salesforce embedded
experience, Slack assistant, calendar-native prep brief, mobile-friendly
experience, enterprise AE variant, multi-stakeholder relationship mapping,
account-plan intelligence, buying committee graph, long-cycle deal
strategy support. *(Not built — roadmap only.)*

## 14. Non-Functional Requirements

**Performance** — Generate Insights cannot run hundreds of slow
account-level queries one by one; at production scale needs set-based
batched queries. Target: under 10s for the prototype path, under 3s for
production after optimization/caching. *(This build keeps the naive
per-account loop — see `docs/FRONTEND-BUILD-PLAN.md` Path A — batching is
Phase 2.)*

**Security** — no shared credentials in production; per-user identity;
row-level access control; AE sees only owned accounts; manager sees only
team accounts; audit logs; no customer-facing actions without explicit
approval. *(This build still runs on one shared Snowflake PAT — a named
Phase 2 gap.)*

**Trust** — no unsupported claims; every insight shows evidence; missing
data acknowledged; facts separated from recommendations; the LLM is never
the sole detector of risk; recommendations are traceable.

**Observability** — track insights generated, cards opened/dismissed,
feedback given, chat follow-ups, time to first useful answer, query/
retrieval failures, LLM latency, cost per insight generation.

## 15. Success Metrics

**Activation** — % of AEs who click Generate Insights on a workday; % who
open at least one insight card; % who use account-scoped chat.
**Usefulness** — % of cards marked useful; % leading to drilldown/account
open; % dismissed as not useful.
**Efficiency** — self-reported prep-time reduction; time from dashboard
open to first useful prep; reduction in manual lookup.
**Quality** — flag precision by category; false positive/negative rate;
grounded-answer rate; missing-data handling rate.
**Retention** — Day 2 return after first use; weekly active AE rate;
repeat Generate Insights usage.

The most important early metric: **does an AE who tries it once come back
the next day?**

## 16. Risks and Open Questions

1. **Too many alerts** — mitigated by prioritizing top 5–7 cards, grouping
   lower-priority items, snooze/dismiss, and usefulness feedback.
2. **Incorrect facts destroy trust** — mitigated by showing evidence,
   deterministic rules for flags, separating facts from recommendations,
   avoiding unsupported claims, and the feedback loop.
3. **Standalone dashboard may increase tool sprawl** — mitigated by a
   Salesforce link-out in Phase 2, embedding in Phase 3.
4. **Calendar awareness is essential** — mitigated (partially, in this
   build) by proxying urgency with close-date proximity; full calendar
   integration is Phase 2.
5. **CSM context missing for renewals** — CSM collaboration layer is
   Phase 2.
6. **Compliance risk in outbound communication** — Phase 1 stays read-only;
   customer-facing comms are separate future scope with approval/consent
   workflows.

## 17. Product Principles

1. **Flags, not paragraphs.**
2. **Show the reason, always.**
3. **Progressive disclosure** — card → account detail → evidence → chat drilldown.
4. **Facts before advice.**
5. **LLM explains; rules detect.**
6. **The AE remains in control** — no automatic customer communication or
   CRM write-back in Phase 1.
7. **Trust beats coverage** — fewer correct insights beat many questionable
   ones.

## 18. MVP Definition

A strong MVP includes: Generate Insights button, top prioritized insight
cards, basic scoring model, account detail page, evidence-backed
recommendations, account-scoped assistant, portfolio-wide assistant,
dismiss/useful feedback, Salesforce link-out (Phase 2), basic calendar
awareness if available (Phase 2). A weak MVP would be a generic chatbot
only, long unstructured summaries, no prioritization, no evidence, no
urgency, no account-detail drilldown, no feedback loop — none of which
describes this build.
