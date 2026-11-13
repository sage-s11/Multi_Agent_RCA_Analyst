import pytest
from netops_agent.tools.tickets import get_ticket
from netops_agent.tools.inventory import get_device
from netops_agent.tools.contacts import get_site_contact


def test_get_ticket():
    t = get_ticket("NET-001")
    assert t.hostname == "SW-BLR-01"
    assert t.interface == "Ethernet1"


def test_get_device_case_insensitive():
    d = get_device("sw-blr-01")
    assert d.site_code == "BLR"


def test_get_site_contact():
    c = get_site_contact("BLR")
    assert c.contact_email == "asha.rao@example.com"


def test_missing_device_raises():
    with pytest.raises(LookupError):
        get_device("NOPE-99")