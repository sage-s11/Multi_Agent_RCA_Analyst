import pytest

from netops_agent.tools import lab

# Real output copied from the SR Linux lab (far end disabled)
SHOW_DOWN = """====================================================================================================================
ethernet-1/1 is down, reason lower-layer-down
--------------------------------------------------------------------------------------------------------------------
====================================================================================================================
"""
SHOW_UP = """====================================================================================================================
ethernet-1/2 is up, speed 25G, type None
--------------------------------------------------------------------------------------------------------------------
====================================================================================================================
"""
ADMIN_ENABLE = "    admin-state enable\n"
OPER_DOWN = "    oper-state down\n"
OPER_UP = "    oper-state up\n"


def test_parse_down_with_reason():
    s = lab.parse_interface_state(ADMIN_ENABLE, OPER_DOWN, SHOW_DOWN)
    assert s == {"admin_state": "enable", "oper_state": "down", "reason": "lower-layer-down"}
    assert lab.classify(s) == "physical_layer"


def test_parse_up():
    s = lab.parse_interface_state(ADMIN_ENABLE, OPER_UP, SHOW_UP)
    assert s["reason"] is None
    assert lab.classify(s) == "healthy"


def test_admin_disabled_is_admin_down():
    s = {"admin_state": "disable", "oper_state": "down", "reason": None}
    assert lab.classify(s) == "admin_down"


def test_garbage_output_raises():
    with pytest.raises(RuntimeError):
        lab.parse_interface_state("error: unknown", "", "")


def test_write_commands_are_blocked():
    for cmd in ["set / interface ethernet-1/1 admin-state disable",
                "show interface ethernet-1/1; reboot",
                "enter candidate", "show version | grep x"]:
        with pytest.raises(ValueError):
            lab.run_cli("sw-blr-01", cmd)


def test_container_name():
    assert lab.container_for("SW-BLR-01") == "clab-blr-sw-blr-01"
