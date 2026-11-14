import json

from langchain_core.messages import HumanMessage, SystemMessage

from netops_agent.config import get_llm
from netops_agent.schemas import TriageChoice
from netops_agent.state import AgentState
from netops_agent.tools.runbooks import get_runbook, get_steps, list_runbooks, search_runbooks
from netops_agent.tools.text import ascii_clean

PROMPT = """You are a network operations triage assistant.
You are given a ticket, device details, the runbooks that were found for it and,
if present, observed_state: facts read live from the device.
Pick the ONE runbook that matches and explain the likely cause.
If observed_state is present, base the likely cause on it and do not claim any other check was done.
Respond ONLY with JSON with exactly these keys:
- runbook_used: the exact name of the matching runbook, one of the names provided
- likely_cause: one or two plain-text sentences, no markdown"""


def run_triage_agent(state: AgentState) -> dict:
    ticket, device = state["ticket"], state["device"]
    diag = state.get("diagnostics") or {}
    live = diag.get("available", False)
    vendor = device["vendor"]

    # 1. RETRIEVE: search this vendor's runbooks (with live facts if we have them)
    if live:
        query = (f"{ticket['title']}. Observed: admin-state {diag['admin_state']}, "
                 f"oper-state {diag['oper_state']}, reason {diag['reason']}")
    else:
        query = f"{ticket['title']}. {ticket['description']}"
    try:
        hits = search_runbooks(query[:1000], vendor, k=2)
        names = [name for name, _ in hits]
        print("[rag] retrieved:", [(n, round(s, 2)) for n, s in hits])

        # Observed facts beat a semantic guess: the device's state picks the runbook.
        if live:
            category = diag["category"]
            if category not in list_runbooks(vendor):
                return {"error": f"No '{category}' runbook for vendor {vendor}"}
            if names[0] != category:
                print(f"[rag] note: search preferred '{names[0]}', observed state says '{category}'. Using observed state.")
            names = [category]
        facts = {"ticket": ticket, "device": device,
                 "runbooks": {n: get_runbook(n, vendor) for n in names}}
    except LookupError as e:
        return {"error": str(e)}

    if live:
        facts["observed_state"] = {k: diag[k] for k in ("interface", "admin_state", "oper_state", "reason")}

    # 2. GENERATE: the LLM only chooses a runbook and explains the cause
    llm = get_llm().with_structured_output(TriageChoice, method="json_mode")
    messages = [SystemMessage(content=PROMPT), HumanMessage(content=json.dumps(facts))]

    for attempt in range(3):
        try:
            choice = llm.invoke(messages)
            if choice.runbook_used not in names:
                raise ValueError(f"LLM picked {choice.runbook_used!r}, expected one of {names}")
            # 3. The exact steps are copied from the runbook file by code
            steps = get_steps(choice.runbook_used, ticket["interface"], vendor)
            return {
                "judgement": {
                    "diagnosis_category": choice.runbook_used,
                    "runbook_used": choice.runbook_used,
                    "likely_cause": ascii_clean(choice.likely_cause),
                    "remote_steps": steps["remote_steps"],
                    "onsite_steps": steps["onsite_steps"],
                }
            }
        except Exception as e:
            print(f"[triage_agent] attempt {attempt + 1} failed: {e}")
    return {"error": "Triage failed after 3 attempts"}
