import json

from langchain_core.messages import HumanMessage, SystemMessage

from netops_agent.config import get_llm
from netops_agent.schemas import TriageChoice
from netops_agent.state import AgentState
from netops_agent.tools.runbooks import get_runbook, get_steps, search_runbooks
from netops_agent.tools.text import ascii_clean

PROMPT = """You are a network operations triage assistant.
You are given a ticket, device details, and the runbooks that a search found for it.
Pick the ONE runbook that matches the ticket and explain the likely cause.
Respond ONLY with JSON with exactly these keys:
- runbook_used: the exact name of the matching runbook, one of the names provided
- likely_cause: one or two plain-text sentences, no markdown"""


def run_triage_agent(state: AgentState) -> dict:
    ticket = state["ticket"]

    # 1. RETRIEVE: search the runbooks with the ticket text
    query = f"{ticket['title']}. {ticket['description']}"[:1000]
    hits = search_runbooks(query, k=2)
    names = [name for name, _ in hits]
    print("[rag] retrieved:", [(n, round(s, 2)) for n, s in hits])

    # 2. GENERATE: the LLM only chooses a runbook and explains the cause
    facts = {
        "ticket": ticket,
        "device": state["device"],
        "runbooks": {n: get_runbook(n) for n in names},
    }
    llm = get_llm().with_structured_output(TriageChoice, method="json_mode")
    messages = [SystemMessage(content=PROMPT), HumanMessage(content=json.dumps(facts))]

    for attempt in range(3):
        try:
            choice = llm.invoke(messages)
            if choice.runbook_used not in names:
                raise ValueError(f"LLM picked {choice.runbook_used!r}, expected one of {names}")
            # 3. The exact steps are copied from the runbook file by code
            steps = get_steps(choice.runbook_used, ticket["interface"])
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
