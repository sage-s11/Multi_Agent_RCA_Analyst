from langchain_core.tools import tool
from netops_agent.config import get_llm


@tool
def get_device_info(hostname: str) -> str:
    """Look up a network device by hostname and return its site and role."""
    return f"{hostname}: Arista cEOS, site BLR, role access-switch"


llm = get_llm().bind_tools([get_device_info])

response = llm.invoke("Which site is SW-BLR-01 in?")
print("Text:", response.content)
print("Tool calls:", response.tool_calls)