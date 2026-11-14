# Administratively Down Interface

## Symptoms
Interface status is `disabled` or administratively down.

## NOC Remote Steps (Arista EOS)
1. `show running-config interfaces <interface>`
2. `show logging | include <interface>`
3. `show accounting logs | include <interface>`

## On-Site Physical Steps
1. Confirm with local site staff if physical maintenance or cable tracing is in progress before re-enabling the port.