import os
import re
import subprocess

from netops_agent import config  # noqa: F401  (importing it loads .env)

# Read-only guard: only "show ..." and "info from state ..." commands are allowed.
ALLOWED = re.compile(r"^(show|info from state)\s+[A-Za-z0-9_./ -]+$")


def container_for(hostname: str) -> str:
    """Containerlab names containers clab-<labname>-<node>. Node names are lowercase."""
    lab = os.getenv("CLAB_LAB_NAME", "blr")
    return f"clab-{lab}-{hostname.lower()}"


def run_cli(hostname: str, command: str, timeout: int = 20) -> str:
    """Run one read-only SR Linux CLI command on a lab switch and return the text."""
    if not ALLOWED.match(command):
        raise ValueError(f"Command not allowed (read-only commands only): {command!r}")
    result = subprocess.run(
        ["docker", "exec", container_for(hostname), "sr_cli", command],
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{command!r} failed on {hostname}: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout


def parse_interface_state(admin_raw: str, oper_raw: str, show_raw: str) -> dict:
    admin = re.search(r"admin-state\s+(\S+)", admin_raw)
    oper = re.search(r"oper-state\s+(\S+)", oper_raw)
    if not admin or not oper:
        raise RuntimeError(f"Could not read interface state. Raw output: {admin_raw!r} / {oper_raw!r}")
    reason = re.search(r"\bis (?:up|down), reason (\S+)", show_raw)
    return {
        "admin_state": admin.group(1),
        "oper_state": oper.group(1),
        "reason": reason.group(1) if reason else None,
    }


def get_interface_state(hostname: str, interface: str) -> dict:
    admin_raw = run_cli(hostname, f"info from state interface {interface} admin-state")
    oper_raw = run_cli(hostname, f"info from state interface {interface} oper-state")
    show_raw = run_cli(hostname, f"show interface {interface}")
    state = parse_interface_state(admin_raw, oper_raw, show_raw)
    return {"hostname": hostname, "interface": interface, **state}


def classify(state: dict) -> str:
    """Turn the observed state into a runbook name. Plain code, no LLM."""
    if state["admin_state"] != "enable":
        return "admin_down"
    if state["oper_state"] != "up":
        return "physical_layer"
    return "healthy"
