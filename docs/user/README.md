# EMBER operator guides

[Documentation home](../README.md) · [Review and evidence limits](../review/README.md)

Use the guide for the application actually running on your board. Each guide
names its applicable versions and validation dates. Source implementation,
dated hardware evidence and current live reception are separate checks.

| Task or interface | Guide | Identify it by |
|---|---|---|
| Compare transmission contents and cadence | [Transmission matrix](ihu-can-console.md#transmission-matrix) | UHF/LTE packets, RF replies, bench forwarding and wired streams |
| Use the active IHU | [IHU USB console](ihu-can-console.md) | `firmware/ihu`; USB text console; `STATUS role=IHU_MCU fw=0.13.0` |
| Use or diagnose the Pi payload | [Payload commands and operations](payload.md) | Pi 4 / LC2502 CAN A; payload 0.2.0; node 4 |
| Monitor or command through Yamcs | [Yamcs operation and available features](yamcs.md) | Instance and processor selected in the web header |
| Power up the demo ground Pi | [Pi readiness and hotspot](../../ground/pi/README.md) | Ethernet first; `EMBER-Ground` fallback Wi-Fi |
| Send an EPS observation over LTE | [Step-by-step LTE walkthrough](lte-eps-walkthrough.md) | IHU → CAN → Walter → ground Pi → `ember` |

The dedicated spare Pico used for Yamcs command tests is a third application,
[usb_bench](../../firmware/usb_bench/README.md). Its USB stream carries binary
packets; opening it as an interactive text console conflicts with the bridge.

Use `ember` / `realtime` for RF and `ember-bench` / `realtime` for the IHU
serial bridge. See [deployment and history](../../ground/yamcs/OPERATIONAL.md).

## Choose a first task

- **Inspect the CAN IHU:** open its USB text console, run `status` and `help`.
  `eps json` observes the charger; `eps adc on` changes ADC configuration.
- **Check Yamcs payload commanding:** use `ember-bench` / `realtime` for serial/CAN
  commands or `ember` / `realtime` for the RF fire-check path. See the
  [payload guide](payload.md) and inspect correlated command/result history.
- **Watch native telemetry over UHF:** use `ember` / `realtime` and prepare the
  [ground receiver](../../ground/yamcs/OPERATIONAL.md). The
  [transmission matrix](ihu-can-console.md#transmission-matrix) lists the IHU
  output gates, single sends, bounded runs and packet contents.
- **Watch native EPS over LTE:** choose `ember` / `realtime` and open EPS.
  Follow the [LTE runbook](../../ground/lte/BRINGUP.md) when preparing a bounded
  bench session. The LTE link is receive-only; USB and payload commands have separate routes.

## Meaning of status

“Implemented” means behavior exists in the reviewed source. “Recorded hardware
validation” applies to the linked run and image. “Draft” describes proposed
mission behavior. A saved display value or old successful test is not evidence
that the current hardware is connected. Inspect timestamps, boot identity,
quality and current link/packet activity before acting on a reading.
