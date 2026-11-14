# Physical Layer Troubleshooting (Admin Up / Line Protocol Down)

## Symptoms
Interface status is `notconnect` or administratively up, line protocol down.

## NOC Remote Steps (Arista EOS)
1. `show interfaces <interface> status`
2. `show interfaces <interface> transceiver dom`
3. `show interfaces <interface> phy detail`
4. `show lldp neighbors <interface>`

## On-Site Physical Steps
1. Verify fiber/patch cable is firmly seated at both ends and on the patch panel.
2. Check Tx/Rx fiber polarity (roll the fiber pair if necessary).
3. Inspect and clean optical connectors and SFP transceiver ports.
4. Swap the SFP transceiver with a known-good compatible module.
5. Replace the patch cable or test the port with a physical fiber loopback plug.