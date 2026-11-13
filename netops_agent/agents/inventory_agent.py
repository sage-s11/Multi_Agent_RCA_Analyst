from netops_agent.state import AgentState
from netops_agent.tools import contacts, inventory

def run_inventory_agent(state: AgentState) -> dict:
    hostname = state["ticket"]["hostname"]
    try:
        device = inventory.get_device(hostname)
        contact = contacts.get_site_contact(device.site_code)
        return {
            "device": device.model_dump(),
            "contact": contact.model_dump(),
        }
    except LookupError as e:
        return {"error": str(e)}