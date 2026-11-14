# Administratively Down Interface

## Symptoms
Interface admin-state is disable. The port was shut down by configuration.

## NOC Remote Steps (Nokia SR Linux)
1. `show interface <interface>`
2. `info from state interface <interface> admin-state`
3. `info from running interface <interface>`

## On-Site Physical Steps
1. Confirm with local site staff if physical maintenance or cable tracing is in progress before re-enabling the port.
