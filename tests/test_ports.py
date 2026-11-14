from netops_agent.agents.ticket_agent import mentioned_ports


def test_same_port_different_spelling_is_one_port():
    assert len(mentioned_ports("Eth-1/1 down. ethernet-1/1 is the uplink")) == 1


def test_conflicting_ports_detected():
    ports = mentioned_ports("Interface Eth-1/1 down on SW-BLR-01\n\nethernet-1/2 is down")
    assert set(ports) == {"1/1", "1/2"}


def test_no_false_positive_on_hostnames():
    assert mentioned_ports("sw-blr-01 and sw-blr-02 are in site BLR") == {}


def test_arista_and_short_names():
    assert set(mentioned_ports("Ethernet2 on SW-DEL-01")) == {"2"}
    assert set(mentioned_ports("port e1-1 is down")) == {"1/1"}
