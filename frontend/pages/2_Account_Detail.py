"""Account detail: call-prep workspace (PRD-phase1-dashboard.md §11, Phase 1C).

Why-flagged evidence, current state, timeline, stakeholder gaps, a single
recommended next-best action, an on-demand call script, relevant enablement,
drill-down tabs, and the account-scoped chat.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import streamlit as st

from frontend.lib import feedback, icons, nav, state
from frontend.lib.branding import inject_css, insight_card, page_heading, priority_pill
from frontend.lib.chat import render_chat_turn
from frontend.lib.data import (
    build_account_brief,
    get_account_core,
    get_activities,
    get_contacts,
    get_opportunities,
    get_tickets,
    get_usage_trend,
)
from frontend.lib.insights import card_from_flag
from frontend.lib.tables import render_table
from src import retrieval, scoring
from src.agent import build_client, final_text, run_turn

st.set_page_config(
    page_title="Account — AE Call-Prep", page_icon="🏢", layout="wide", initial_sidebar_state="collapsed"
)
inject_css()

ae = nav.render_sidebar_nav(None)

account_id = st.session_state.get("selected_account_id")
if not account_id:
    st.warning("Open an account from Home or the Accounts list first.")
    st.stop()

account = get_account_core(account_id)
if account is None:
    st.error(f"No account found for {account_id}")
    st.stop()

with st.spinner("Loading brief..."):
    brief = build_account_brief(account_id)

as_of = date.fromisoformat(brief["as_of"])
open_opportunities = brief["open_opportunities"]
flags = brief["flags"]
cards = sorted(
    (card_from_flag(account, flag, open_opportunities, as_of, i) for i, flag in enumerate(flags)),
    key=lambda c: c["score"],
    reverse=True,
)

# Everything below reuses these five fetches instead of re-querying per section/tab.
activities = get_activities(account_id, days=90)
opportunities = get_opportunities(account_id)
usage = get_usage_trend(account_id, months=12)
tickets = get_tickets(account_id)
contacts = get_contacts(account_id)

page_heading("buildings", account["COMPANY_NAME"])

header_bits = [account["STATUS"].title(), account["SEGMENT"], account["REGION"]]
if account.get("ARR_EUR"):
    header_bits.append(f"ARR €{account['ARR_EUR']:,.0f}")
header_html = " · ".join(header_bits)
if cards:
    header_html += f" &nbsp; {priority_pill(cards[0]['band'])} score {cards[0]['score']}"
    if cards[0]["urgency_label"]:
        header_html += f" &nbsp; · {cards[0]['urgency_label']}"
st.markdown(header_html, unsafe_allow_html=True)

st.divider()

# --- Why this was flagged (evidence-backed, one card per flag) ---
if cards:
    st.markdown("#### Why this was flagged")
    cols = st.columns(2, gap="medium") if len(cards) > 1 else [st.container()]
    for i, card in enumerate(cards):
        with cols[i % len(cols)]:
            with st.container(border=True, key=f"card_{card['key']}"):
                insight_card(card)
                evidence_ids = [
                    v for k, v in card["flag"].items()
                    if k in ("opportunity_id", "ticket_id") and v
                ]
                if evidence_ids:
                    st.caption(f"Evidence record(s): {' · '.join(evidence_ids)}")
                c1, c2, _ = st.columns([1, 1, 3], gap="small")
                with c1:
                    if st.button("Useful", key=f"useful_{card['key']}", help="Mark useful"):
                        feedback.record(ae, account_id, card["flag"]["type"], "useful")
                        st.toast("Thanks — marked useful.")
                with c2:
                    if st.button("Not useful", key=f"notuseful_{card['key']}", help="Mark not useful"):
                        feedback.record(ae, account_id, card["flag"]["type"], "not_useful")
                        st.toast("Got it — marked not useful.")
else:
    st.success("No flags on this account right now.")

# --- Current state ---
nearest_opp = scoring.nearest_open_opportunity(open_opportunities, as_of)
state_bits = [f"{account['COMPANY_NAME']} is a {account['STATUS']} {account['SEGMENT']} account"]
if nearest_opp:
    state_bits.append(
        f" with a €{(nearest_opp['AMOUNT_EUR'] or 0):,.0f} {nearest_opp['TYPE'].lower()} opportunity "
        f"closing {nearest_opp['CLOSE_DATE']}."
    )
else:
    state_bits.append(".")
usage_flag = next((c for c in cards if c["flag"]["type"] == "usage_decline"), None)
if usage_flag:
    state_bits.append(" Product usage has declined recently.")
elif usage:
    state_bits.append(" Product usage looks stable.")
open_tickets = [t for t in tickets if t["STATUS"] != "Resolved"]
if open_tickets:
    state_bits.append(f" {len(open_tickets)} support ticket(s) currently open.")
else:
    state_bits.append(" No open support tickets.")

st.markdown("#### Current state")
st.write("".join(state_bits))

# --- What has happened so far ---
st.markdown("#### What has happened so far")
timeline = []
if activities:
    a = activities[0]
    timeline.append(f"Last activity: **{a['ACTIVITY_DATE']}** — {a['SUBJECT']}: {a['SUMMARY']}")
else:
    timeline.append("No activity logged in the last 90 days.")
if tickets:
    t = tickets[0]
    timeline.append(f"Most recent ticket: '{t['SUBJECT']}' ({t['STATUS']}, opened {t['CREATED_DATE']})")
if len(usage) >= 2:
    latest, prev = usage[0], usage[1]
    delta = latest["MONTHLY_ACTIVE_USERS"] - prev["MONTHLY_ACTIVE_USERS"]
    direction = "up" if delta >= 0 else "down"
    timeline.append(
        f"Monthly active users {direction} {abs(delta)} ({prev['MONTH']} → {latest['MONTH']})."
    )
decision_makers = [c for c in contacts if c["PERSONA_TYPE"] in ("Economic Buyer", "Champion")]
if decision_makers:
    for dm in decision_makers:
        last = dm["LAST_INTERACTION"] or "never"
        timeline.append(f"{dm['PERSONA_TYPE']} ({dm['FULL_NAME']}) last engaged: {last}")
else:
    timeline.append("No Economic Buyer or Champion on file.")
for line in timeline:
    st.markdown(f"- {line}")

# --- Key stakeholders ---
st.markdown("#### Key stakeholders")
personas_present = {c["PERSONA_TYPE"] for c in contacts}
for role in ("Economic Buyer", "Champion", "Technical"):
    if role in personas_present:
        names = ", ".join(c["FULL_NAME"] for c in contacts if c["PERSONA_TYPE"] == role)
        icon = icons.svg("check", "bold", 15, "#16A34A")
        detail = names
    else:
        icon = icons.svg("warning", "bold", 15, "#CA8A04")
        detail = "none on file"
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:6px;margin:0.2rem 0;">'
        f'{icon}<span><b>{role}</b>: {detail}</span></div>',
        unsafe_allow_html=True,
    )

# --- Recommended next-best action ---
st.markdown("#### Recommended next-best action")
if cards:
    st.info(cards[0]["recommended_action"])
else:
    st.success("No urgent action — this account looks healthy. Standard check-in cadence is fine.")

# --- Suggested call script ---
st.markdown("#### Suggested call script")
script_key = f"call_script::{account_id}"
with st.container(key="draft_script_btn"):
    draft_clicked = st.button("Draft opening & call script")
if draft_clicked:
    top_flags = "; ".join(c["flag"]["detail"] for c in cards[:3]) or "no active flags"
    prompt = (
        f"Draft a short opening line and a 4-5 point call script for my upcoming call with "
        f"{account['COMPANY_NAME']}. Key things to account for: {top_flags}. "
        "Keep it grounded in the account data — pull in any relevant battlecard, objection "
        "handling, or case study guidance if it applies."
    )
    with st.spinner("Drafting..."):
        client = build_client()
        msg = run_turn(client, [{"role": "user", "content": prompt}], pinned_account_id=account_id)
    st.session_state[script_key] = final_text(msg)
if st.session_state.get(script_key):
    st.markdown(st.session_state[script_key])

# --- Relevant enablement ---
st.markdown("#### Relevant enablement")
competitor_flag = next((c for c in cards if c["flag"]["type"] == "competitor_mentioned"), None)
if competitor_flag:
    query = f"{competitor_flag['flag']['competitor']} battlecard objection"
elif any(c["flag"]["type"] in ("renewal_approaching", "usage_decline") for c in cards):
    query = "renewal risk retention playbook"
elif any(c["flag"]["type"] in ("no_economic_buyer", "no_champion") for c in cards):
    query = "MEDDIC economic buyer champion"
elif cards:
    query = "sales playbook deal stage"
else:
    query = "sales playbook"
hits = retrieval.search_enablement(query, top_k=3)
if hits:
    for hit in hits:
        with st.expander(f"{hit['source']} — {hit['section']}"):
            st.write(hit["text"])
else:
    st.caption("No matching enablement content found.")

st.divider()

tab_activity, tab_opps, tab_usage, tab_tickets, tab_contacts = st.tabs(
    ["Activity", "Opportunities", "Usage", "Tickets", "Contacts"]
)

with tab_activity:
    if activities:
        render_table(
            pd.DataFrame(activities),
            hide=("OPPORTUNITY_ID", "CONTACT_ID"),
            widths={"SUBJECT": "medium", "SUMMARY": "large"},
        )
    else:
        st.caption("No activity in the last 90 days.")

with tab_opps:
    if opportunities:
        render_table(
            pd.DataFrame(opportunities),
            hide=("OPPORTUNITY_ID",),
            widths={"NAME": "medium", "WON_LOST_REASON": "medium"},
        )
    else:
        st.caption("No opportunities on file.")

with tab_usage:
    if usage:
        df = pd.DataFrame(usage).sort_values("MONTH")
        st.line_chart(df.set_index("MONTH")[["MONTHLY_ACTIVE_USERS", "LOGINS"]])
        render_table(df)
    else:
        st.caption("No product usage on file (prospect).")

with tab_tickets:
    if tickets:
        render_table(
            pd.DataFrame(tickets),
            hide=("TICKET_ID",),
            widths={"SUBJECT": "medium", "SUMMARY": "large"},
        )
    else:
        st.caption("No support tickets.")

with tab_contacts:
    if contacts:
        render_table(
            pd.DataFrame(contacts),
            hide=("CONTACT_ID",),
            widths={"FULL_NAME": "medium", "EMAIL": "medium"},
        )
    else:
        st.caption("No contacts on file.")

st.divider()
st.markdown("#### Ask about this account")

history_key = f"account::{account_id}"
history = state.get_chat_history(history_key)

for msg in history:
    role = "assistant" if msg["role"] == "assistant" else "user"
    text = final_text(msg) if role == "assistant" else msg["content"]
    with st.chat_message(role):
        st.write(text)

if prompt := st.chat_input(f"Ask about {account['COMPANY_NAME']}..."):
    render_chat_turn(
        build_client(), history, prompt, pinned_account_id=account_id, pinned_account_brief=brief
    )
