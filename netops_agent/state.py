from typing import TypedDict

class AgentState(TypedDict, total=False):
    ticket_id: str
    ticket: dict
    device: dict
    contact: dict
    judgement: dict
    email: dict
    decision: dict
    error: str
    next_step: str