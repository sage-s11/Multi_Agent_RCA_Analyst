from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from netops_agent.agents.diagnostics_agent import run_diagnostics_agent
from netops_agent.agents.inventory_agent import run_inventory_agent
from netops_agent.agents.supervisor import route_from_supervisor, supervisor_node
from netops_agent.agents.ticket_agent import run_ticket_agent
from netops_agent.agents.triage_agent import run_triage_agent
from netops_agent.state import AgentState
from netops_agent.tools.drafts import build_email


def observed_text(diag: dict) -> str | None:
    if not diag.get("available"):
        return None
    text = f"admin-state {diag['admin_state']}, oper-state {diag['oper_state']}"
    if diag.get("reason"):
        text += f", reason {diag['reason']}"
    return text


def draft_email_node(state: AgentState):
    email = build_email(
        state["ticket"],
        state["contact"],
        state["judgement"]["onsite_steps"],
        state["judgement"]["runbook_used"],
        observed_text(state.get("diagnostics") or {}),
    )
    return {"email": email}


def approve_email_node(state: AgentState):
    diag = state.get("diagnostics") or {}
    decision = interrupt({
        "ticket": state["ticket"],
        "email": state["email"],
        "remote_steps": state["judgement"]["remote_steps"],
        "runbook_used": state["judgement"]["runbook_used"],
        "likely_cause": state["judgement"]["likely_cause"],
        "live_check": observed_text(diag) or diag.get("note", "not run"),
    })
    return {"decision": decision}


def save_draft_node(state: AgentState):
    email = state["email"]
    if state["decision"].get("action") == "edit":
        email = {**email, "body": state["decision"]["body"]}
    path = Path("drafts") / f"{state['ticket']['ticket_id']}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"To: {email['to']}\nSubject: {email['subject']}\n\n{email['body']}\n")
    return {"email": email}


def no_fault_node(state: AgentState):
    d = state["diagnostics"]
    print(f"[no fault] {d['hostname']} {d['interface']} is enabled and up on the device. "
          "No email drafted. The ticket may be stale or the link may have flapped.")
    return {}


def error_node(state: AgentState):
    print(f"[error] {state['error']}")
    return {}


def after_approval(state: AgentState):
    return "save" if state["decision"].get("action") in ("approve", "edit") else "end"


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("supervisor", supervisor_node)
    g.add_node("ticket_agent", run_ticket_agent)
    g.add_node("inventory_agent", run_inventory_agent)
    g.add_node("diagnostics_agent", run_diagnostics_agent)
    g.add_node("triage_agent", run_triage_agent)
    g.add_node("draft_email", draft_email_node)
    g.add_node("approve_email", approve_email_node)
    g.add_node("save_draft", save_draft_node)
    g.add_node("no_fault", no_fault_node)
    g.add_node("error", error_node)

    g.add_edge(START, "supervisor")
    g.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "ticket_agent": "ticket_agent",
            "inventory_agent": "inventory_agent",
            "diagnostics_agent": "diagnostics_agent",
            "triage_agent": "triage_agent",
            "draft_email": "draft_email",
            "no_fault": "no_fault",
            "error": "error",
        },
    )

    for worker in ("ticket_agent", "inventory_agent", "diagnostics_agent", "triage_agent"):
        g.add_edge(worker, "supervisor")

    g.add_edge("draft_email", "approve_email")
    g.add_conditional_edges("approve_email", after_approval, {"save": "save_draft", "end": END})
    g.add_edge("save_draft", END)
    g.add_edge("no_fault", END)
    g.add_edge("error", END)

    return g.compile(checkpointer=MemorySaver())
