import json
from langchain_core.messages import HumanMessage, SystemMessage
from netops_agent.config import get_llm
from netops_agent.schemas import TriageJudgement
from netops_agent.state import AgentState
from netops_agent.tools.runbooks import get_all_runbooks_text
from netops_agent.tools.text import ascii_clean

TRIAGE_PROMPT = """You are a network operations RCA & triage assistant.

You are given:
1. A network ticket and device details.
2. Local standard operating runbooks.

Select the matching runbook and produce a JSON object with:
- diagnosis_category: one of "physical_layer", "admin_down", "err_disabled", "unknown"
- runbook_used: name of the runbook you followed (e.g., "physical_layer")
- likely_cause: brief plain-text explanation of the root cause
- remote_steps: list of CLI checks the NOC runs, taken from the runbook with <interface> replaced by the actual interface name
- onsite_steps: list of physical actions for the site contact, taken from the runbook

Use plain text only inside string values (no markdown). Respond ONLY with valid JSON."""

def run_triage_agent(state: AgentState) -> dict:
    runbooks_text = get_all_runbooks_text()
    facts = {
        "ticket": state["ticket"],
        "device": state["device"],
        "available_runbooks": runbooks_text,
    }

    llm = get_llm().with_structured_output(TriageJudgement, method="json_mode")
    messages = [
        SystemMessage(content=TRIAGE_PROMPT),
        HumanMessage(content=json.dumps(facts)),
    ]

    last_err = None
    for attempt in range(3):
        try:
            j = llm.invoke(messages).model_dump()
            break
        except Exception as e:
            last_err = e
            print(f"[triage] attempt {attempt + 1} failed, retrying")
    else:
        return {"error": f"Triage failed after 3 attempts: {last_err}"}

    j["likely_cause"] = ascii_clean(j["likely_cause"])
    j["remote_steps"] = [ascii_clean(s) for s in j["remote_steps"]]
    j["onsite_steps"] = [ascii_clean(s) for s in j["onsite_steps"]]
    return {"judgement": j}