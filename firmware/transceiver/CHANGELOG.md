# Transceiver firmware changelog

## 0.38.0

- Answer read-only firmware identity requests over CAN during LINK_ACTIVE
  for the IHU FULL telemetry set.

## 0.37.3

- Service CAN while processing and printing USB receive diagnostics.
- Report transmit completion over CAN before writing the diagnostic line.

## 0.37.2

- Collect continuous ADC samples across overlapping receive windows.
- Report receive window, CRC and CAN forwarding diagnostics.
