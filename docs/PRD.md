# PRD — DealPrep AI

## Conversational AE Call-Prep Assistant

**Status:** Case-study product PRD
**Product:** DealPrep AI
**Primary user:** Mid-market Account Executive, EMEA
**Context:** Personio Internal AI PM case study
**Owner:** Chhedup Lama
**Purpose:** Define the working prototype and the product path from prototype to production.

**Relationship to the rest of the repo:** This document is the canonical PRD
for the case-submission narrative itself, superseding the earlier draft at
`docs/PRD-dashboard-vision.md` (kept for its interview-quote evidence base,
now marked historical). The case-study deliverable itself is the
conversational agent in `src/` — see `docs/one-pager.md` for the as-built
scope and trade-offs. The dashboard described in §6.2, §13 (Phase 2), and
§14 of this PRD is already built as a demo-path Streamlit app in
`frontend/` (see `docs/FRONTEND-BUILD-PLAN.md` for the implementation
approach) — it is a stretch artifact extending past the brief, not the core
submission. **For the dashboard's own phase framing and scoring/feed
design, `docs/PRD-phase1-dashboard.md` is now canonical** — it supersedes
this document's §6.2/§13/§14 dashboard phase numbering with a more detailed
Phase 1/1B/1C/1D breakdown, all of which is now built.

---

## 1. Executive Summary

DealPrep AI is a conversational AI assistant that helps Account Executives prepare for renewal,
expansion, and discovery calls by combining structured account data with sales enablement guidance.

The product is designed for a mid-market AE who owns 30–40 accounts and has limited time to
prepare before customer and prospect calls. Today, preparation requires jumping between CRM data,
recent activities, product usage, support tickets, playbooks, battlecards, pricing notes, and case
studies. DealPrep AI brings that context into one trusted, multi-turn assistant.

For the case-study prototype, the product focuses on one core workflow:

The AE asks about an account.
The assistant retrieves account facts from Snowflake.
It retrieves guidance from enablement documents.
It returns an AE-ready call brief.
The AE can ask follow-up questions and drill deeper.

The key product principle is:

**Structured systems provide facts. Enablement documents provide guidance. The LLM
synthesizes and explains.**

The assistant should not invent deal facts or unsupported risks. It should clearly distinguish between
what is known from account data, what is recommended from sales guidance, and what is missing.

## 2. Problem

Account Executives spend a meaningful part of their week preparing for account calls.

They need to know:

- Who the account is
- What the current opportunity state is
- What has happened recently
- Who the key stakeholders are
- Whether the account is at risk
- Whether product usage is healthy
- Whether there are open support issues
- Which sales playbook applies
- Which objections may come up
- Which case study or battlecard is relevant
- What to say on the call

The problem is not simply that information exists in many places. The deeper issue is that AEs are
under time pressure and may miss the one signal that matters most before the call.

Examples:

- A renewal customer has declining product usage.
- A high-value opportunity has no Economic Buyer attached.
- A churn-risk account has an unresolved support ticket.
- A prospect fits the ICP but the decision process is unknown.
- A competitor was mentioned in a recent activity, but the AE has not reviewed the battlecard.

The assistant should reduce prep friction and help the AE enter the call with confidence.

## 3. Target Persona

### Primary Persona: Mid-Market AE

The primary user is a mid-market AE at Personio.

Profile:

- Around 18 months tenure
- EMEA region
- Owns 30–40 accounts
- Handles renewals, expansions, and discovery calls
- Has limited time to prepare
- Needs concise, reliable, account-specific answers
- Values practical call guidance over generic AI summaries
- Will quickly lose trust if the assistant states incorrect facts

### Scenario

Tomorrow, the AE has two important calls:

1. A renewal expansion call with a churn-risk customer.
2. A discovery call with a hot prospect.

She wants to quickly prepare for both and then ask follow-up questions.

## 4. Product Goal

DealPrep AI should help an AE prepare for account calls faster and better.

The assistant should answer:

- What is the current state of this account?
- Why does this account matter now?
- What are the main risks or opportunities?
- What has happened recently?
- Who are the key stakeholders?
- What should I say on the call?
- Which objections should I expect?
- Which playbook, battlecard, or case study is relevant?
- What should my next-best action be?

## 5. Non-Goals for the Case Prototype

The case prototype intentionally does not include:

- Salesforce write-back
- Calendar integration
- Slack integration
- Email generation to customers
- Automated outbound communication
- Manager dashboard
- CSM collaboration workflow
- Mobile app
- Production-grade RBAC
- Enterprise AE account planning
- Fully automated evaluation suite
- Fine-tuning or custom model training

These are future production considerations, not required for proving the core assistant workflow.

## 6. Product Scope

### 6.1 Prototype Scope

The working prototype should support:

**Account Lookup**

The AE can ask about an account by name.

Example:

"Prep me for my renewal call with Fjord Systems."

The assistant should find the relevant account and retrieve account context.

**Renewal / Expansion Call Prep**

The assistant should summarize:

- Account overview
- Opportunity state
- Renewal or expansion context
- Deal value
- Key contacts
- Recent activities
- Product usage signals
- Support tickets
- Churn or renewal risk
- Relevant playbook guidance
- Suggested call plan
- Next-best action

**Discovery Call Prep**

The assistant should summarize:

- Prospect profile
- ICP fit
- Opportunity stage
- Known contacts
- Recent activities
- Unknown discovery gaps
- Likely pain points
- Relevant case study
- Suggested discovery questions
- Recommended next step

**Follow-Up Drilldowns**

The AE can ask follow-up questions such as:

- "Why is this account a churn risk?"
- "What did we last discuss?"
- "Who is the Economic Buyer?"
- "What objections should I prepare for?"
- "Which battlecard is relevant?"
- "Give me a five-minute call plan."
- "What should I avoid saying?"
- "Which case study should I use?"

The assistant should preserve account context across turns.

### 6.2 Future Product Scope

After the assistant is validated, DealPrep AI can evolve into a dashboard and insight feed.

Future capabilities:

- Generate Insights across the AE's book of accounts
- Calendar-aware prep prioritization
- Insight cards for high-risk accounts
- Account detail pages
- Manager rollups
- CSM collaboration
- Salesforce and Slack embedding

These are not part of the case prototype but show the path to production.

> **Repo note:** most of this section is already built as the demo-path
> Streamlit app in `frontend/` — Generate Insights, account detail pages, and
> account-scoped/portfolio-wide chat all exist today. Manager rollups, CSM
> collaboration, and Salesforce/Slack embedding remain future work (see §13
> Phase 2/3 below).

## 7. User Experience

### 7.1 Primary Interaction Model

The prototype is conversational.

The AE starts with a natural language request:

"Prep me for tomorrow's renewal expansion call with Fjord Systems."

The assistant responds with a structured call-prep brief.

The AE then drills deeper:

"Why is this account risky?"
"What should I open with?"
"Which objection handling guide applies?"

### 7.2 Standard Assistant Answer Format

For consistency and usability, the assistant should use this format for account prep answers:

1. Account snapshot
2. Why this matters now
3. Current opportunity / renewal state
4. Recent activity summary
5. Product usage and support signals
6. Key stakeholders
7. Risks and opportunities
8. Relevant enablement guidance
9. Recommended call plan
10. Next-best action
11. Data used / gaps

This format makes the answer useful under time pressure and prevents long generic AI responses.

### 7.3 Renewal Call Example

User:

"Prep me for my renewal expansion call with Fjord Systems."

Assistant should produce:

Account snapshot:
Fjord Systems is a mid-market customer with an upcoming renewal opportunity worth €82k.

Why this matters now:
The renewal is approaching and the account shows signs of churn risk.

Current state:
The opportunity is in negotiation. Product usage has declined recently and there is an unresolved
support issue.

Recent activity:
The last AE activity was 12 days ago. The customer raised concerns about payroll reliability.

Usage and support:
Usage is down 22% month-over-month. One P1 support ticket is still open.

Stakeholders:
Champion identified. Economic Buyer not recently engaged.

Main risk:
Do not lead with expansion before addressing the support concern.

Recommended call plan:

1. Acknowledge the open payroll issue.
2. Confirm the resolution path.
3. Ask whether the issue affects renewal confidence.
4. Re-engage the Economic Buyer.
5. Only then explore expansion.

Suggested opening:
"Before we discuss renewal and future plans, I want to acknowledge the payroll issue your team
raised last week..."

Data used:
Snowflake account, opportunity, usage, ticket, activity, and contact records. Enablement guidance
from renewal playbook and objection-handling guide.

### 7.4 Discovery Call Example

User:

"Prep me for a discovery call with Brightwave GmbH."

Assistant should produce:

Account snapshot:
Brightwave GmbH is a hot mid-market prospect in EMEA with an open new-business opportunity.

Why this matters now:
The account appears to be a strong ICP fit, but the decision process and current HR stack are not yet
clear.

Current opportunity state:
The opportunity is in discovery with a potential value of €65k.

Known context:
Recent activity suggests interest in HR process automation and payroll simplification.

Discovery gaps:
Current HR system unknown.
Decision-maker not confirmed.
Buying timeline unclear.
Payroll complexity not yet qualified.

Recommended discovery questions:

1. What HR and payroll tools are you using today?
2. What breaks most often in your current process?
3. Who owns the decision for HR transformation?
4. What timeline are you working toward?
5. What would make this project urgent?

Relevant enablement:
Use the ICP guide and mid-market case study. Avoid pricing discussion until pain, timeline, and
decision process are qualified.

Next-best action:
Focus the call on qualification, business pain, and stakeholder mapping.

## 8. Data Source Strategy

The assistant should use each source for the right purpose.

| Question Type | Source of Truth |
|---|---|
| Account details | Snowflake |
| Contacts and stakeholders | Snowflake |
| Opportunity stage and value | Snowflake |
| Recent sales activity | Snowflake |
| Product usage | Snowflake |
| Support tickets | Snowflake |
| ICP fit guidance | Google Drive enablement docs |
| Sales playbook guidance | Google Drive enablement docs |
| Competitive positioning | Battlecards |
| Objection handling | Objection guide |
| Pricing approach | Pricing cheat sheet |
| Case study recommendation | Case studies |
| Final synthesis | LLM |

The LLM should synthesize and explain. It should not be the source of truth for account facts.

## 9. Functional Requirements

### 9.1 Account Search

The assistant must be able to find an account by name.

Acceptance criteria:

- If there is one strong match, use it.
- If there are multiple possible matches, ask the AE to clarify.
- If no account is found, say so clearly.

### 9.2 Account Brief Generation

The assistant must generate a call-prep brief using structured account data.

Acceptance criteria:

- Includes account summary
- Includes opportunity context
- Includes recent activity
- Includes contacts
- Includes usage where available
- Includes support tickets where available
- Includes risks and next-best action
- Identifies missing data honestly

### 9.3 Enablement Retrieval

The assistant must retrieve relevant sales guidance from documents.

Acceptance criteria:

- Uses playbook for deal-stage guidance
- Uses ICP document for discovery calls
- Uses battlecards when competitor is mentioned
- Uses objection guide for likely objections
- Uses case studies when relevant
- Does not invent enablement guidance

### 9.4 Multi-Turn Conversation

The assistant must preserve account context across turns.

Acceptance criteria:

- User does not need to repeat account name in every question
- Follow-up answers remain grounded in the selected account
- Assistant can answer drilldown questions
- Assistant can switch account if the user asks

### 9.5 Missing Data Handling

The assistant must handle incomplete data safely.

Acceptance criteria:

- If usage data is missing, it says usage data is not available.
- If no Economic Buyer is found, it says no Economic Buyer is recorded.
- If no support tickets exist, it says no open tickets were found.
- It does not fabricate missing CRM records.

### 9.6 Data Used / Evidence

Every substantial answer should include a brief "Data used" or "Evidence" section.

Example:

Data used:
- Account and opportunity records from Snowflake
- Recent activities from Snowflake
- Product usage table from Snowflake
- Support ticket table from Snowflake
- Renewal playbook and objection guide from enablement docs

For the prototype, exact document citations are a nice-to-have. The minimum bar is to identify which
data categories were used.

## 10. Technical Architecture

### 10.1 High-Level Architecture

```
User question
  ↓
Conversation state / account context
  ↓
Intent routing
  ↓
Snowflake tools for structured data
  +
RAG retrieval over enablement docs
  ↓
LLM synthesis
  ↓
AE-ready response with facts, guidance, next action, and data gaps
```

### 10.2 Components

**Snowflake Data Layer**

Responsible for retrieving structured CRM-style data.

Functions:

```
find_account(account_name)
get_account_overview(account_id)
get_contacts(account_id)
get_opportunities(account_id)
get_activities(account_id)
get_usage_trend(account_id)
get_tickets(account_id)
build_account_context(account_id)
```

**Enablement Retrieval Layer**

Responsible for retrieving relevant guidance from Google Drive documents.

Functions:

```
load_enablement_docs()
chunk_documents()
create_vector_index()
search_enablement(query)
```

**Agent Layer**

Responsible for:

- Understanding the user question
- Calling the right data tools
- Retrieving relevant enablement guidance
- Maintaining account context
- Producing the final answer

**Prompt Layer**

Responsible for answer discipline.

The system prompt should instruct the assistant to:

- Act as an AE call-prep assistant
- Use Snowflake for account facts
- Use enablement docs for guidance
- Separate facts from recommendations
- Be concise but useful
- Do not invent missing data
- Ask clarification when account identity is unclear

### 10.3 Why Not a Complex Autonomous Agent?

For this case, a lightweight tool-using assistant is better than a complex autonomous agent.

Reasons:

- Easier to explain in technical deep-dive
- Lower risk of unpredictable tool calls
- More reliable for CRM facts
- Better suited to 3–5 hour build scope
- Clear separation between retrieval and synthesis

A complex agent framework can be introduced later if the workflow requires planning across multiple
tasks.

> **Repo note:** `src/agent.py` implements this as-is — 8 parameterized tool
> functions over `client.beta.messages.tool_runner`, no framework, no
> vector search (keyword search is sufficient for an 8-document corpus). See
> `docs/one-pager.md` for the full as-built rationale.

## 11. Quality Bar

### 11.1 What "Good Enough" Means for Prototype

The prototype is good enough if:

1. The assistant runs reliably.
2. It can prepare an AE for both a renewal call and a discovery call.
3. Account facts are grounded in Snowflake.
4. Sales guidance is grounded in enablement documents.
5. It supports follow-up questions.
6. It handles missing data honestly.
7. It produces a useful call plan.
8. It can be explained clearly in code walkthrough.

### 11.2 Evaluation Dimensions

| Dimension | Question |
|---|---|
| Factual accuracy | Are account facts correct against Snowflake? |
| Grounding | Is the answer based on retrieved data/docs? |
| Usefulness | Would an AE use this before a call? |
| Completeness | Does it cover the key prep areas? |
| Conciseness | Is it scannable under time pressure? |
| Follow-up quality | Does it maintain account context? |
| Missing-data behavior | Does it avoid hallucinating? |
| Latency | Does it respond fast enough for prep? |

### 11.3 Prototype Eval Set

Use a small golden set of test questions.

Example eval questions:

1. "Prep me for a renewal call with [Account A]."
2. "Why is this account a churn risk?"
3. "Who are the key stakeholders?"
4. "What did we last discuss?"
5. "Are there open support issues?"
6. "Which objection should I prepare for?"
7. "Which competitor guidance is relevant?"
8. "Give me a five-minute call plan."
9. "Prep me for a discovery call with [Prospect B]."
10. "What are the biggest discovery gaps?"

Each answer can be manually scored for:

- Correct account facts
- Relevant enablement guidance
- Clear recommendation
- No unsupported claims

## 12. Success Metrics

### Prototype Success Metrics

For the case prototype:

- Runs end-to-end without manual intervention
- Correctly retrieves account data
- Correctly retrieves enablement guidance
- Produces usable call-prep summaries
- Handles at least two realistic demo flows
- Supports multi-turn follow-up
- Maintains trust by acknowledging missing data

### Production Success Metrics

For a real rollout:

**Activation**

- % of AEs who use the assistant weekly
- % of target AEs who complete first call prep

**Efficiency**

- Reduction in self-reported prep time
- Time from question to usable brief
- Reduction in manual lookup across systems

**Quality**

- % of answers rated useful
- % of answers with correct CRM facts
- Hallucination / unsupported claim rate
- Retrieval relevance score

**Adoption**

- Day 2 return after first use
- Weekly repeat usage
- Number of follow-up questions per session

**Business Impact**

Longer-term:

- Improved renewal preparedness
- Better stakeholder engagement
- Higher enablement content usage
- Better forecast hygiene
- Potential improvement in expansion conversion or churn-risk handling

Do not claim direct revenue impact in the prototype. Treat it as a future measurement goal.

## 13. Roadmap

### Phase 0 — Case Prototype: Conversational Assistant

Goal:

Prove that an AE can use a conversational assistant to prepare for realistic account calls.

Included:

- Python-based working assistant
- Snowflake connection
- Enablement document retrieval
- Account prep for renewal and discovery calls
- Multi-turn follow-up
- Basic evidence / data-used section
- README and one-pager

Cut:

- Dashboard
- Calendar
- CRM write-back
- RBAC
- Notifications
- Manager views
- Customer-facing communication

*(Repo status: built — `src/`, `docs/one-pager.md`.)*

### Phase 1 — Production V1: Trusted AE Assistant

Goal:

Turn the prototype into a secure internal tool for a pilot AE group.

Included:

- Authentication
- Per-AE account scoping
- Robust account matching
- Better error handling
- Observability and traces
- Feedback buttons
- Saved call briefs
- Salesforce link-out
- Improved document ingestion pipeline
- Golden-set evals

Why this phase matters:

Before adding dashboards or proactive workflows, the core assistant must be trusted.

### Phase 2 — Generate Insights Dashboard

Goal:

Move from reactive Q&A to proactive account prioritization.

Included:

- Dashboard home page
- Generate Insights button
- Insight cards
- Account priority scoring
- Renewal-risk and discovery-prep groups
- Account detail page
- Account-scoped chat
- Portfolio-wide chat

Important note:

This is not the case prototype. This is the product evolution after validating that the assistant
produces useful and trusted account prep.

*(Repo status: built as a demo-path Streamlit app — `frontend/`, per
`docs/FRONTEND-BUILD-PLAN.md` "Path A". Not yet production-shaped: no real
auth, naive per-account insight scan rather than batched queries, no
persisted dismiss/snooze state. See §14 known gaps below.)*

**Generate Insights Concept**

When the AE clicks Generate Insights, the system scans their owned accounts and returns a ranked
feed.

The feed groups accounts into:

- Prepare now
- High-risk renewals
- Discovery calls
- Expansion opportunities
- Missing stakeholders
- Support risk
- Competitive risk
- Monitor

Each card shows:

- Account name
- Priority
- Urgency
- Deal value
- Risk tags
- One-line insight
- Recommended action
- Evidence chips
- CTA to open account detail

### Phase 3 — Workflow Integration and Team Expansion

Goal:

Embed DealPrep AI into the AE's daily workflow and expand to adjacent users.

Included:

- Calendar integration
- Slack or email notifications
- Salesforce embedded experience
- Manager dashboard
- CSM collaboration
- Admin threshold controls
- Role-based permissions
- Team-level risk rollups

This phase addresses the risk that a standalone tool becomes another destination.

### Phase 4 — Enterprise and Advanced Intelligence

Goal:

Explore whether DealPrep AI should support enterprise account planning.

Included:

- Enterprise AE workflow
- Buying committee mapping
- Relationship intelligence
- Long-cycle opportunity planning
- Multi-stakeholder activity summaries
- Account-plan generation
- Advanced risk prediction

This should be treated as a separate product discovery track, not a simple extension of mid-market AE
call prep.

## 14. Future Generate Insights UX

This section is intentionally future-facing.

### 14.1 Insight Card Example — Renewal Risk

**Critical — Prepare Now**

**Fjord Systems**
Renewal call today · €82k ARR · Churn risk

**Why it matters:** Usage dropped 22% month-over-month and a P1 payroll ticket is still open.

**Recommended action:** Start with the support issue, confirm resolution path, and only then discuss
renewal or expansion.

Tags:
Renewal Risk · Usage Decline · Open P1 · High ARR

CTA:
Open Account Prep

### 14.2 Insight Card Example — Discovery Prep

**High — Discovery Prep**
**Brightwave GmbH**
Discovery call tomorrow · €65k pipeline · Strong ICP fit

**Why it matters:** The account matches Personio's mid-market ICP, but decision process and current
HR stack are unknown.

**Recommended action:** Use the call to qualify HR complexity, buying timeline, decision stakeholders,
and current system pain.

Tags:
Hot Prospect · ICP Fit · Discovery · Missing Decision Process

CTA:
Open Discovery Prep

### 14.3 Account Detail Page

When the AE opens a card, the detail page should show:

1. Why this was flagged
2. Current account state
3. What has happened so far
4. Stakeholder map
5. Opportunity state
6. Usage and support signals
7. Relevant enablement
8. Recommended next-best action
9. Suggested call script
10. Evidence trail
11. Account-scoped assistant

This becomes the full call-prep workspace.

## 15. Risks and Mitigations

**Risk 1: Assistant gives incorrect facts**

This is the biggest risk.

Mitigation:

- Use Snowflake as source of truth
- Show data used
- Avoid unsupported claims
- Say when data is missing
- Add golden-set evals
- Log and review bad answers

**Risk 2: Too generic to be useful**

The assistant may produce generic sales advice.

Mitigation:

- Always include account-specific facts
- Retrieve relevant enablement guidance
- Use standard answer format
- Ask follow-up questions when context is missing

**Risk 3: Too much scope**

The product could become dashboard, CRM, sales coach, manager tool, and Slack bot all at once.

Mitigation:

- Case prototype remains conversational
- Production V1 focuses on trusted assistant
- Dashboard comes only after assistant validation
- Manager/CSM workflows are later phases

**Risk 4: Calendar awareness missing**

The case persona has back-to-back calls, but calendar data is not part of the provided dataset.

Mitigation:

- Do not claim live calendar integration in the prototype
- Simulate call timing only if needed for demo
- Add calendar integration as Phase 3 production feature

**Risk 5: Standalone product may create tool sprawl**

AEs already use multiple tools.

Mitigation:

- Add Salesforce link-out early
- Consider Salesforce/Slack embedding after validation
- Keep the assistant fast and focused

## 16. Product Principles

1. **Trust beats coverage.**
   Better to answer fewer things correctly than many things unreliably.
2. **Facts and recommendations must be separated.**
   CRM facts are not the same as AI advice.
3. **The assistant should be useful under time pressure.**
   Answers must be structured and scannable.
4. **The AE stays in control.**
   No automatic customer communication or CRM updates in the prototype.
5. **LLM synthesizes; systems provide truth.**
   Account data comes from Snowflake. Sales guidance comes from documents.
6. **Follow-up is core to the experience.**
   The product is not just a static brief. It should support drilldown.
7. **Scope discipline matters.**
   Build the narrow workflow well before expanding to dashboards and automation.

## 17. What I Would Say in the Interview

Use this framing:

"For the case submission, I focused on the core conversational assistant because that is what the brief
asked for. The assistant retrieves structured account facts from Snowflake, retrieves sales guidance
from enablement documents, and synthesizes an AE-ready call brief with follow-up support. I
intentionally cut dashboarding, calendar integration, write-back, and notifications because those are
production features. My product vision is that, once the assistant is trusted, this evolves into a
Generate Insights dashboard that proactively prioritizes high-risk renewals and discovery prep across
an AE's book of accounts."

This answer shows:

- You respected the assignment.
- You made scope trade-offs.
- You understand production evolution.
- You are not overbuilding.
- You can think like a builder PM.

## 18. Final MVP Definition

### Case MVP

The case MVP is successful if the AE can ask:

"Prep me for my call with this account."

And receive:

- Correct account facts
- Relevant recent activity
- Opportunity context
- Usage/support signals
- Stakeholder context
- Relevant playbook guidance
- Risks and opportunities
- Suggested call plan
- Next-best action
- Honest data gaps
- Follow-up support

### Future Product MVP

The future product MVP is successful if the AE opens DealPrep AI in the morning and immediately
knows:

- Which accounts need attention
- Which calls need prep
- Why they matter
- What action to take
- Where the evidence comes from

## 19. Submission Alignment

The case asks for:

1. A working agent.
2. A short one-pager explaining approach.
3. A live demo.
4. A technical deep-dive.

This PRD supports that by defining:

- The user problem
- The prototype scope
- The architecture
- The data-source strategy
- The assistant behavior
- The quality bar
- The cuts and trade-offs
- The path to production

The actual submission should still be:

- GitHub repo
- Colab or Python app
- README
- One-pager
- Demo script
- Sample eval questions

The PRD is a support artifact for how you think as a PM, not a replacement for the working prototype.
