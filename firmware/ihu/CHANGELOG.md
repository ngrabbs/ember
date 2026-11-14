# IHU firmware changelog

## 0.27.0

- Report the IHU build identity and restore transceiver, payload, LTE CAN MCU and Walter firmware identities in
  FULL when the devices respond. BASIC retains its existing packet set.
- Keep the 0.26.1 USB console fixes and EPS diagnostics.

## 0.26.1

- Use CRLF for USB console records, group help and add read-only EPS diagnostics.

## 0.26.0

- Sample GPS for payload fire checks and forward the tagged result to Yamcs.
