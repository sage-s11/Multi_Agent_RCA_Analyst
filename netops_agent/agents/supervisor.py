from netops_agent.state import AgentState


def supervisor_node(state: AgentState) -> dict:
    """Decide which agent or step should run next based on current state."""
    if state.get("error"):
        return {"next_step": "error"}
    if not state.get("ticket"):
        return {"next_step": "ticket_agent"}
    if not state.get("device") or not state.get("contact"):
        return {"next_step": "inventory_agent"}
    if "diagnostics" not in state:
        return {"next_step": "diagnostics_agent"}
    if state["diagnostics"].get("category") == "healthy":
        return {"next_step": "no_fault"}
    if not state.get("judgement"):
        return {"next_step": "triage_agent"}
    return {"next_step": "draft_email"}


def route_from_supervisor(state: AgentState) -> str:
    return state["next_step"]
