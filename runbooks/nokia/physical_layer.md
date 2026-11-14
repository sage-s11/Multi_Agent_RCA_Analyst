# Physical Layer Troubleshooting (Admin Up / Oper Down)

## Symptoms
Interface admin-state is enable but oper-state is down, for example reason lower-layer-down. No link to the far end.

## NOC Remote Steps (Nokia SR Linux)
1. `show interface <interface>`
2. `info from state interface <interface> oper-state`
3. `show system lldp neighbor`

## On-Site Physical Steps
1. Verify fiber/patch cable is firmly seated at both ends and on the patch panel.
2. Check Tx/Rx fiber polarity (roll the fiber pair if necessary).
3. Inspect and clean optical connectors and SFP transceiver ports.
4. Swap the SFP transceiver with a known-good compatible module.
5. Replace the patch cable or test the port with a physical fiber loopback plug.
