import csv
from netops_agent.config import DATA_DIR
from netops_agent.schemas import SiteContact


def get_site_contact(site_code: str) -> SiteContact:
    """Look up site contact details. Later: swap for NetBox."""
    with open(DATA_DIR / "contacts.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["site_code"].upper() == site_code.upper():
                return SiteContact(**row)
    raise LookupError(f"No contact found for site {site_code}")