import sys

from netops_agent.tools.lab import classify, get_interface_state

hostname, interface = sys.argv[1], sys.argv[2]
state = get_interface_state(hostname, interface)
print(state)
print("classified as:", classify(state))
