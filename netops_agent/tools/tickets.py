import json
import os
import requests
from netops_agent.config import DATA_DIR
from netops_agent.schemas import Ticket

def get_ticket(ticket_id: str) -> Ticket:
    """Load a ticket from local JSON first, or fetch from GitHub Issues."""
    # 1. Check local JSON files (e.g., NET-001, NET-002)
    for path in (DATA_DIR / "tickets").glob("*.json"):
        data = json.loads(path.read_text())
        if data["ticket_id"] == ticket_id:
            return Ticket(**data)

    # 2. If not local, try GitHub Issues API
    raw = fetch_github_issue(ticket_id)
    if raw:
        # Return a partial dict/Ticket or let ticket_agent parse raw body
        return Ticket(**raw)

    raise LookupError(f"Ticket {ticket_id} not found")

def fetch_github_issue(issue_ref: str) -> dict | None:
    """Fetch an issue from GitHub REST API if GITHUB_REPO is configured."""
    repo = os.getenv("GITHUB_REPO")
    if not repo:
        return None

    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Support issue numbers like "1" or "#1", or search by title like "NET-001"
    issue_num = issue_ref.lstrip("#")
    if issue_num.isdigit():
        url = f"https://api.github.com/repos/{repo}/issues/{issue_num}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None

    # Otherwise search issues in the repo matching the ticket_id in title
    url = f"https://api.github.com/repos/{repo}/issues"
    resp = requests.get(url, headers=headers, params={"state": "open"}, timeout=10)
    if resp.status_code == 200:
        for issue in resp.json():
            if issue_ref.lower() in issue.get("title", "").lower():
                return issue
    return None