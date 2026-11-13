# Err-Disabled Interface

## Symptoms
Interface status is `errdisabled`.

## NOC Remote Steps (Arista EOS)
1. `show interfaces status errdisabled`
2. `show logging | include <interface>`
3. `show spanning-tree interface <interface> detail`

## On-Site Physical Steps
1. Check for unauthorized switches, hubs, or accidental cable loops connected to the port.
2. Disconnect suspect end-user equipment before NOC resets the port.