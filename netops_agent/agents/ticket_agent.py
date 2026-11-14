import re

from langchain_core.messages import HumanMessage, SystemMessage

from netops_agent.config import get_llm
from netops_agent.schemas import Ticket, TicketFields
from netops_agent.state import AgentState
from netops_agent.tools.text import ascii_clean
from netops_agent.tools.tickets import fetch_github_issue, get_ticket, is_github_ref

PROMPT = """Read this network alert ticket.
Respond ONLY with JSON with exactly these keys:
- hostname: the device hostname exactly as written in the ticket (for example SW-BLR-01)
- interface: the interface name exactly as written in the ticket (for example Ethernet1)
- severity: one of low, medium, high, critical (use medium if the ticket does not say)"""


PORT = re.compile(r"\b(?:eth(?:ernet)?-?(\d+(?:/\d+)*)|e(\d+)-(\d+))\b", re.I)


def mentioned_ports(text: str) -> dict:
    """Return {normalized port: first spelling found}, e.g. {'1/1': 'Eth-1/1', '1/2': 'ethernet-1/2'}."""
    ports = {}
    for m in PORT.finditer(text):
        key = m.group(1) or f"{m.group(2)}/{m.group(3)}"
        ports.setdefault(key, m.group(0))
    return ports


def run_ticket_agent(state: AgentState) -> dict:
    ref = state["ticket_id"]

    # Local ticket: plain JSON file, no LLM needed.
    if not is_github_ref(ref):
        try:
            return {"ticket": get_ticket(ref).model_dump()}
        except LookupError as e:
            return {"error": str(e)}

    # GitHub issue: fetch it, then let the LLM read the free text.
    try:
        issue = fetch_github_issue(ref)
    except Exception as e:
        return {"error": f"Could not fetch GitHub issue {ref}: {e}"}

    title = issue["title"]
    body = issue.get("body") or ""
    text = ascii_clean(f"Title: {title}\n\n{body}")

    # Conflicting interfaces (for example title says 1/1, description says 1/2): stop and ask a human.
    ports = mentioned_ports(text)
    if len(ports) > 1:
        names = ", ".join(ports.values())
        return {"error": f"GitHub issue {ref} names more than one interface ({names}). Fix the ticket so it names a single interface."}

    llm = get_llm().with_structured_output(TicketFields, method="json_mode")
    messages = [SystemMessage(content=PROMPT), HumanMessage(content=text)]

    fields = None
    for attempt in range(3):
        try:
            fields = llm.invoke(messages)
            # Guard: the hostname must really appear in the ticket text.
            if ascii_clean(fields.hostname).lower() not in text.lower():
                raise ValueError(f"hostname {fields.hostname!r} is not in the ticket text")
            if ascii_clean(fields.interface).lower() not in text.lower():
                raise ValueError(f"interface {fields.interface!r} is not in the ticket text")
            break
        except Exception as e:
            print(f"[ticket_agent] attempt {attempt + 1} failed: {e}")
            fields = None
    if fields is None:
        return {"error": f"Could not read hostname/interface from GitHub issue {ref}"}

    # Everything exact comes from GitHub or from code. The LLM only read the free text.
    ticket = Ticket(
        ticket_id=f"GH-{issue['number']}",
        title=ascii_clean(title),
        description=ascii_clean(body),
        severity=fields.severity,
        hostname=ascii_clean(fields.hostname).strip(),
        interface=ascii_clean(fields.interface).strip(),
        created_at=issue["created_at"],
    )
    return {"ticket": ticket.model_dump()}
