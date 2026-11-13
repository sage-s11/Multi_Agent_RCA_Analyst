import csv
from netops_agent.config import DATA_DIR
from netops_agent.schemas import Device


def get_device(hostname: str) -> Device:
    """Look up a device by hostname. Later: swap for NetBox."""
    with open(DATA_DIR / "inventory.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["hostname"].lower() == hostname.lower():
                return Device(**row)
    raise LookupError(f"Device {hostname} not found in inventory")