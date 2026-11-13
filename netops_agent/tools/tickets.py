import json
import os

import requests

from netops_agent.config import DATA_DIR
from netops_agent.schemas import Ticket


def is_github_ref(ref: str) -> bool:
    """'1', '#1' and 'GH-1' mean a GitHub issue. Anything else is a local ticket."""
    ref = ref.upper().replace("GH-", "").lstrip("#")
    return ref.isdigit()


def get_ticket(ticket_id: str) -> Ticket:
    """Load a local ticket from data/tickets/*.json."""
    for path in (DATA_DIR / "tickets").glob("*.json"):
        data = json.loads(path.read_text())
        if data["ticket_id"] == ticket_id:
            return Ticket(**data)
    raise LookupError(f"Ticket {ticket_id} not found locally")


def fetch_github_issue(ref: str) -> dict:
    """Fetch one issue from GitHub. Needs GITHUB_REPO in .env, e.g. user/repo."""
    repo = os.getenv("GITHUB_REPO")
    if not repo:
        raise LookupError("GITHUB_REPO is not set in .env")
    number = ref.upper().replace("GH-", "").lstrip("#")

    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/repos/{repo}/issues/{number}"
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 404:
        raise LookupError(f"GitHub issue {number} not found in {repo}")
    resp.raise_for_status()
    issue = resp.json()
    if "pull_request" in issue:
        raise LookupError(f"#{number} is a pull request, not an issue")
    return issue
