import pytest

from netops_agent.tools.runbooks import get_steps, list_runbooks


def test_nokia_steps():
    s = get_steps("physical_layer", "ethernet-1/1", "Nokia")
    assert s["remote_steps"][0] == "show interface ethernet-1/1"
    assert len(s["onsite_steps"]) == 5


def test_arista_steps():
    s = get_steps("physical_layer", "Ethernet1", "arista")
    assert s["remote_steps"][0] == "show interfaces Ethernet1 status"


def test_vendor_filter():
    assert "err_disabled" in list_runbooks("arista")
    assert "err_disabled" not in list_runbooks("nokia")


def test_unknown_vendor():
    with pytest.raises(LookupError):
        list_runbooks("cisco")
