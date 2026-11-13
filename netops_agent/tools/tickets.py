import json
from netops_agent.config import DATA_DIR
from netops_agent.schemas import Ticket


def get_ticket(ticket_id: str) -> Ticket:
    """Load a ticket by ID. Later: swap this body for a GitHub Issues call."""
    for path in (DATA_DIR / "tickets").glob("*.json"):
        data = json.loads(path.read_text())
        if data["ticket_id"] == ticket_id:
            return Ticket(**data)
    raise LookupError(f"Ticket {ticket_id} not found")