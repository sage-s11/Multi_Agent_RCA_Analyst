import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from netops_agent.config import get_llm
from netops_agent.schemas import TriageJudgement
from netops_agent.state import AgentState
from netops_agent.tools import contacts, inventory, tickets
from netops_agent.tools.drafts import build_email
from netops_agent.tools.text import ascii_clean

TRIAGE_PROMPT = """You are a network operations triage assistant.
Scenario: interface admin up, line protocol down. Most likely a physical layer
problem, often a faulty or incompatible SFP.
Produce:
- remote_steps: CLI checks the NOC runs (Arista EOS syntax; include transceiver
  DOM/Rx power and far-end state; only commands you are sure exist).
- onsite_steps: physical actions for the site contact only (seating, polarity,
  SFP/patch cable swap, loopback). Nothing that needs CLI access.
Plain text only, no markdown. You do not write emails."""


def fetch_ticket_node(state: AgentState):
    try:
        return {"ticket": tickets.get_ticket(state["ticket_id"]).model_dump()}
    except LookupError as e:
        return {"error": str(e)}


def lookup_inventory_node(state: AgentState):
    try:
        device = inventory.get_device(state["ticket"]["hostname"])
        contact = contacts.get_site_contact(device.site_code)
    except LookupError as e:
        return {"error": str(e)}
    return {"device": device.model_dump(), "contact": contact.model_dump()}


def triage_node(state: AgentState):
    facts = {"ticket": state["ticket"], "device": state["device"]}
    llm = get_llm().with_structured_output(TriageJudgement)
    messages = [
        SystemMessage(content=TRIAGE_PROMPT),
        HumanMessage(content=json.dumps(facts)),
    ]

    last_err = None
    for attempt in range(3):
        try:
            j = llm.invoke(messages).model_dump()
            break
        except Exception as e:  # provider validation errors vary, so catch broadly here
            last_err = e
            print(f"[triage] attempt {attempt + 1} failed, retrying")
    else:
        return {"error": f"Triage failed after 3 attempts: {last_err}"}

    j["likely_cause"] = ascii_clean(j["likely_cause"])
    j["remote_steps"] = [ascii_clean(s) for s in j["remote_steps"]]
    j["onsite_steps"] = [ascii_clean(s) for s in j["onsite_steps"]]
    return {"judgement": j}


def draft_email_node(state: AgentState):
    return {"email": build_email(state["ticket"], state["contact"], state["judgement"]["onsite_steps"])}


def approve_email_node(state: AgentState):
    # Pauses the graph here until you resume with a decision.
    decision = interrupt({"email": state["email"], "remote_steps": state["judgement"]["remote_steps"]})
    return {"decision": decision}


def save_draft_node(state: AgentState):
    email = state["email"]
    if state["decision"].get("action") == "edit":
        email = {**email, "body": state["decision"]["body"]}
    path = Path("drafts") / f"{state['ticket_id']}.txt"
    path.write_text(f"To: {email['to']}\nSubject: {email['subject']}\n\n{email['body']}\n")
    return {"email": email}


def error_node(state: AgentState):
    print(f"[error] {state['error']}")
    return {}


def after_lookup(state: AgentState):
    return "error" if state.get("error") else "ok"


def after_approval(state: AgentState):
    return "save" if state["decision"].get("action") in ("approve", "edit") else "end"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("fetch_ticket", fetch_ticket_node)
    g.add_node("lookup_inventory", lookup_inventory_node)
    g.add_node("triage", triage_node)
    g.add_node("draft_email", draft_email_node)
    g.add_node("approve_email", approve_email_node)
    g.add_node("save_draft", save_draft_node)
    g.add_node("error", error_node)

    g.add_edge(START, "fetch_ticket")
    g.add_conditional_edges("fetch_ticket", after_lookup, {"ok": "lookup_inventory", "error": "error"})
    g.add_conditional_edges("lookup_inventory", after_lookup, {"ok": "triage", "error": "error"})
    g.add_conditional_edges("triage", after_lookup, {"ok": "draft_email", "error": "error"})
    g.add_edge("draft_email", "approve_email")
    g.add_conditional_edges("approve_email", after_approval, {"save": "save_draft", "end": END})
    g.add_edge("save_draft", END)
    g.add_edge("error", END)

    return g.compile(checkpointer=MemorySaver())