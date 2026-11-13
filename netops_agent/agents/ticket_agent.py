import json
from langchain_core.messages import HumanMessage, SystemMessage
from netops_agent.config import DATA_DIR, get_llm
from netops_agent.schemas import Ticket
from netops_agent.state import AgentState
from netops_agent.tools.tickets import fetch_github_issue

PARSE_ISSUE_PROMPT = """Extract network ticket fields from this GitHub Issue into JSON.
Fields required:
- ticket_id (e.g., NET-001 or GH-1)
- title
- description
- severity: one of "low", "medium", "high", "critical"
- hostname (e.g., SW-BLR-01)
- interface (e.g., Ethernet1)
- created_at
Respond ONLY with valid JSON."""

def run_ticket_agent(state: AgentState) -> dict:
    ticket_id = state["ticket_id"]

    # 1. Try GitHub Issues first if configured and issue exists
    gh_issue = fetch_github_issue(ticket_id)
    if gh_issue:
        llm = get_llm().with_structured_output(Ticket, method="json_mode")
        issue_payload = {
            "number": gh_issue.get("number"),
            "title": gh_issue.get("title"),
            "body": gh_issue.get("body"),
            "created_at": gh_issue.get("created_at", ""),
        }
        messages = [
            SystemMessage(content=PARSE_ISSUE_PROMPT),
            HumanMessage(content=json.dumps(issue_payload)),
        ]
        try:
            parsed = llm.invoke(messages)
            return {"ticket": parsed.model_dump()}
        except Exception as e:
            return {"error": f"Failed to parse GitHub issue {ticket_id}: {e}"}

    # 2. Fallback to local JSON tickets in data/tickets/
    for path in (DATA_DIR / "tickets").glob("*.json"):
        data = json.loads(path.read_text())
        if data["ticket_id"] == ticket_id:
            return {"ticket": Ticket(**data).model_dump()}

    return {"error": f"Ticket {ticket_id} not found locally or on GitHub"}