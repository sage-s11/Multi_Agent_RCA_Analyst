import json
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from netops_agent.config import get_llm
from netops_agent.schemas import TriageJudgement, TriageReport
from netops_agent.tools import tickets, inventory, contacts
from netops_agent.tools.text import ascii_clean


@tool
def fetch_ticket(ticket_id: str) -> str:
    """Fetch a ticket by ID (e.g. NET-001). Returns hostname, interface and alert details."""
    return tickets.get_ticket(ticket_id).model_dump_json()


@tool
def lookup_device(hostname: str) -> str:
    """Look up a device in inventory by hostname. Returns vendor, model, role, site code."""
    return inventory.get_device(hostname).model_dump_json()


@tool
def lookup_site_contact(site_code: str) -> str:
    """Look up the site contact by site code (e.g. BLR). Returns name, email, phone."""
    return contacts.get_site_contact(site_code).model_dump_json()


TOOLS = {t.name: t for t in (fetch_ticket, lookup_device, lookup_site_contact)}

SYSTEM_PROMPT = """You are a network operations triage assistant.
Given a ticket ID, do the following in order:
1. Fetch the ticket.
2. Look up the device from the ticket's hostname.
3. Look up the site contact using the device's site code.
Never invent hostnames, contacts or emails. Use only tool results.

Triage knowledge for 'admin up, line protocol down':
- Most likely a physical layer problem, often a faulty or incompatible SFP.
- Steps: confirm state with show interfaces; check far-end admin and line state;
  check cable/fiber seating and Tx/Rx polarity; check transceiver type, speed and
  wavelength match and DOM Rx power; swap SFP or patch cable; escalate to the site
  contact for on-site hands.
The draft email asks the site contact for on-site physical checks. It is a draft only.

Email rules:    You produce remote_steps (CLI checks the NOC runs) and onsite_steps (physical
   checks for the site contact: seating, polarity, SFP/patch cable swap, loopback).
   Plain text only, no markdown. You do not write the email."""


def run(ticket_id: str, max_steps: int = 8) -> TriageReport:
    llm = get_llm()
    llm_with_tools = llm.bind_tools(list(TOOLS.values()))
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Triage ticket {ticket_id}."),
    ]

    for _ in range(max_steps):
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        if not response.tool_calls:
            break
        for call in response.tool_calls:
            try:
                result = TOOLS[call["name"]].invoke(call["args"])
            except Exception as e:
                result = f"ERROR: {e}"
            messages.append(ToolMessage(content=result, tool_call_id=call["id"], name=call["name"]))

    messages.append(HumanMessage(content="Now produce the final triage report."))
    facts = {}
    for m in messages:
        if isinstance(m, ToolMessage) and not m.content.startswith("ERROR"):
            facts[m.name] = json.loads(m.content)

    missing = {"fetch_ticket", "lookup_device", "lookup_site_contact"} - facts.keys()
    if missing:
        raise RuntimeError(f"Agent did not complete lookups: {missing}")

    messages.append(HumanMessage(content="Now produce your triage judgement."))
    judgement = llm.with_structured_output(TriageJudgement).invoke(messages)

    t, c = facts["fetch_ticket"], facts["lookup_site_contact"]

    # --- new: build the email in code ---
    subject = f"Request for on-site physical checks - {t['ticket_id']} ({t['hostname']} {t['interface']})"
    steps = "\n".join(f"{i}. {ascii_clean(s)}" for i, s in enumerate(judgement.onsite_steps, 1))
    body = (
        f"Hi {c['contact_name']},\n\n"
        f"We have an alert on {t['hostname']} ({t['interface']}): the interface is "
        f"administratively up but the line protocol is down.\n\n"
        f"Could you please arrange the following on-site checks:\n{steps}\n\n"
        f"Please reply with the results.\n\nBest regards,\nNetwork Operations"
    )

    return TriageReport(
        ticket_id=t["ticket_id"],
        hostname=t["hostname"],
        interface=t["interface"],
        site_code=facts["lookup_device"]["site_code"],
        site_contact_name=c["contact_name"],
        site_contact_email=c["contact_email"],
        diagnosis_category=judgement.diagnosis_category,
        likely_cause=ascii_clean(judgement.likely_cause),
        remote_steps=[ascii_clean(s) for s in judgement.remote_steps],
        onsite_steps=[ascii_clean(s) for s in judgement.onsite_steps],
        draft_email_subject=subject,
        draft_email_body=body,
    )