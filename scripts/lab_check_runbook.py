import sys

from netops_agent.tools.lab import run_cli
from netops_agent.tools.runbooks import get_steps, list_runbooks

# Runs every remote step of every Nokia runbook on a lab switch, so you can see
# which commands really work. Usage: python -m scripts.lab_check_runbook sw-blr-01 ethernet-1/1
hostname, interface = sys.argv[1], sys.argv[2]
for name in list_runbooks("nokia"):
    print(f"\n##### runbook: {name}")
    for command in get_steps(name, interface, "nokia")["remote_steps"]:
        print(f"\n$ {command}")
        try:
            out = run_cli(hostname, command).strip().splitlines()
            print("\n".join(out[:6]) or "(no output)")
            if len(out) > 6:
                print(f"... ({len(out) - 6} more lines)")
        except Exception as e:
            print(f"ERROR: {e}")
