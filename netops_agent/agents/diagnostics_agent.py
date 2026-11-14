from netops_agent.state import AgentState
from netops_agent.tools.lab import classify, get_interface_state

LAB_VENDORS = ("nokia",)  # vendors we have live (read-only) access to


def run_diagnostics_agent(state: AgentState) -> dict:
    """Ask the device itself what the interface state is. Plain code, no LLM."""
    ticket, device = state["ticket"], state["device"]

    if device["vendor"].lower() not in LAB_VENDORS:
        note = f"No live access to {device['vendor']} devices"
        print(f"[diagnostics] skipped: {note}")
        return {"diagnostics": {"available": False, "note": note}}

    try:
        st = get_interface_state(device["hostname"], ticket["interface"])
    except Exception as e:
        # We expected live access, so a failure (wrong interface name, lab down) stops the run.
        return {"error": f"Live check failed on {device['hostname']} {ticket['interface']}: {e}"}

    category = classify(st)
    print(f"[diagnostics] {st['hostname']} {st['interface']}: admin {st['admin_state']}, "
          f"oper {st['oper_state']}, reason {st['reason']} -> {category}")
    return {"diagnostics": {"available": True, **st, "category": category}}
