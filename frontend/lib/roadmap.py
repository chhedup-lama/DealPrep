"""Structured roadmap data for the Roadmap page — what's built, what's next.

Mirrors `docs/PRD-phase1-dashboard.md` (the current canonical dashboard
PRD — supersedes the phase framing in `docs/PRD-dashboard-vision.md` and
`docs/PRD.md` §13). Kept as data here (not hardcoded HTML) so it's one
place to update if the roadmap changes. `phase` is one of
"mvp" / "phase2" / "phase3" — see frontend/lib/branding.py for the tag
styling. There's no "phase1" bucket anymore: everything in the new PRD's
Phase 1 track (base dashboard + 1B scoring/grouping + 1C account-detail
intelligence + 1D trust loop) is built.
"""

from __future__ import annotations

ROADMAP: list[dict] = [
    # --- Built now: the full Phase 1 track (base + 1B + 1C + 1D) ---
    {
        "title": "Portfolio-wide Get Insights scan, scored and grouped",
        "phase": "mvp",
        "detail": "Every flag across an AE's book becomes a scored insight card (time urgency, deal value, account importance, risk severity, actionability) and is grouped into Prepare Now / High-Risk Renewals / Expansion / Discovery / Missing Stakeholders / Support Risk / Competitive Risk / Monitor.",
        "source": "PRD-phase1-dashboard.md §8-9 (Phase 1B)",
    },
    {
        "title": "Priority scoring + capped Prepare Now feed",
        "phase": "mvp",
        "detail": "Deterministic 5-dimension score → Critical/High/Medium/Low bands, with the top Critical items capped to 7 in a dedicated Prepare Now section instead of a flat list.",
        "source": "PRD-phase1-dashboard.md §10 (Phase 1B)",
    },
    {
        "title": "Account Detail Intelligence workspace",
        "phase": "mvp",
        "detail": "Why-flagged evidence cards, a templated current-state summary, a what-happened-so-far timeline, stakeholder gap callouts, a single specific next-best action, an on-demand LLM-drafted call script, and proactively-surfaced relevant enablement.",
        "source": "PRD-phase1-dashboard.md §11 (Phase 1C)",
    },
    {
        "title": "Useful / not-useful feedback + precision tracking",
        "phase": "mvp",
        "detail": "Useful / Not useful on every insight card, a reasoned dismiss (already handled / wrong / other), logged to a local feedback file and rolled up into a per-flag-type 'useful' rate on the home page.",
        "source": "PRD-phase1-dashboard.md Phase 1D",
    },
    {
        "title": "Master data views (Accounts, Opportunities, Contacts, Tickets)",
        "phase": "mvp",
        "detail": "Filterable, scoped to the logged-in AE via OWNER_AE.",
        "source": "PRD-phase1-dashboard.md §12.4",
    },
    {
        "title": "Account-scoped and portfolio-wide chat",
        "phase": "mvp",
        "detail": "Same agent and tools as the CLI, reused unchanged for both chat surfaces.",
        "source": "PRD-phase1-dashboard.md §12.5 / §12.6",
    },
    {
        "title": "AE picker (auth stand-in)",
        "phase": "mvp",
        "detail": "Real per-AE login is a named Phase 2 gap below — this switches the active OWNER_AE for the demo.",
        "source": "Build plan, Path A limitations",
    },

    # --- Phase 2: Team, Workflow, and Proactive Triggers ---
    {
        "title": "Calendar / schedule awareness",
        "phase": "phase2",
        "detail": "The single biggest structural gap: today's urgency score proxies 'how soon' with days-to-close-date, not an actual calendar. Needs a new data source not in the current schema.",
        "source": "PRD-phase1-dashboard.md §8.2",
    },
    {
        "title": "Manager RBAC + team-level risk dashboard",
        "phase": "phase2",
        "detail": "Manager/Admin roles beyond plain AE — unlocks a team-level insight rollup across reports' books.",
        "source": "PRD-phase1-dashboard.md Phase 2",
    },
    {
        "title": "Scheduled scans + proactive notifications",
        "phase": "phase2",
        "detail": "Get Insights today is on-click only. Proactive, scheduled scans with Slack/email nudges when a new high-severity flag appears.",
        "source": "PRD-phase1-dashboard.md Phase 2",
    },
    {
        "title": "CSM collaboration on renewals",
        "phase": "phase2",
        "detail": "Renewals are a joint AE + CSM motion in the playbook, but there's no CSM persona or handoff surface yet.",
        "source": "PRD-phase1-dashboard.md Phase 2",
    },
    {
        "title": "Admin surface for flag thresholds",
        "phase": "phase2",
        "detail": "The €30k MEDDIC cutoff, 21-day quiet window, 10% usage-decline threshold, 30-day stall, and the scoring weights themselves are hardcoded constants today. Sales ops needs to tune these without a code deploy.",
        "source": "PRD-phase1-dashboard.md Phase 2",
    },
    {
        "title": "\"Open in Salesforce\" link-out + Salesforce write-back",
        "phase": "phase2",
        "detail": "A direct answer to tool-sprawl risk; write-back (notes/tasks) only once explicitly approved.",
        "source": "PRD-phase1-dashboard.md Phase 2",
    },
    {
        "title": "Real per-AE Snowflake identity",
        "phase": "phase2",
        "detail": "Today's prototype runs on one shared PAT for the whole team. OWNER_AE scoping needs to be a real enforced boundary, not just a WHERE clause.",
        "source": "PRD-phase1-dashboard.md §14 (NFR — Security)",
    },
    {
        "title": "Batched Get Insights queries",
        "phase": "phase2",
        "detail": "Connection reuse already cut a scan from 180s+ to ~12s. Set-based batched queries (one query per data type across all owned accounts) is the next step down, needed at production scale.",
        "source": "PRD-phase1-dashboard.md §14 (NFR — Performance)",
    },

    # --- Phase 3: Embedded and Enterprise Variants ---
    {
        "title": "Salesforce embedded experience + Slack assistant",
        "phase": "phase3",
        "detail": "Meet the AE where they already work instead of adding a fifth standalone tool — directly responsive to the tool-sprawl risk named throughout this PRD.",
        "source": "PRD-phase1-dashboard.md Phase 3",
    },
    {
        "title": "Calendar-native prep brief + mobile-friendly experience",
        "phase": "phase3",
        "detail": "AEs prep in 10-minute gaps, often on the move. Nothing today addresses phone/tablet use or a calendar-embedded brief.",
        "source": "PRD-phase1-dashboard.md Phase 3",
    },
    {
        "title": "Enterprise AE variant",
        "phase": "phase3",
        "detail": "Fewer accounts, more stakeholders, longer cycles — needs a genuinely different information architecture (buying-committee graph, account-plan intelligence), not a filtered version of this one.",
        "source": "PRD-phase1-dashboard.md Phase 3",
    },
]


def by_phase(phase: str) -> list[dict]:
    return [item for item in ROADMAP if item["phase"] == phase]
