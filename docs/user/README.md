# EMBER operator guides

[Documentation home](../README.md) · [Review and evidence limits](../review/README.md)

Use the guide for the application actually running on your board. These guides
cover implemented bench behavior as reviewed on October 4, 2026. They do not
establish approved flight procedures. Code and configuration were checked;
existing hardware evidence is linked with its date. No hardware was reflashed
or live service changed during this documentation review.

| Task or interface | Guide | Identify it by |
|---|---|---|
| Use IHU debug UART | [FreeRTOS IHU debug UART](ihu-debug-uart.md) | 3.3 V UART adapter on Pico GP0/GP1; `ihu>` prompt |
| Use the newer IHU CAN bench | [CAN Feather USB console](ihu-can-console.md) | USB text console; `STATUS role=IHU_MCU fw=can-bench-v2` |
| Monitor or command through Yamcs | [Yamcs operation and available features](yamcs.md) | Instance and processor selected in the web header |
| Power up the demo ground Pi | [Pi readiness and hotspot](../../ground/pi/README.md) | Ethernet first; `EMBER-Ground` fallback Wi-Fi |
| Send an EPS observation over LTE | [Step-by-step LTE walkthrough](lte-eps-walkthrough.md) | IHU → CAN → Walter → ground Pi → `ember-lte` |

The dedicated spare Pico used for Yamcs command tests is a third application,
[usb_bench](../../firmware/usb_bench/README.md). Its USB stream carries binary
packets; opening it as an interactive text console conflicts with the bridge.

## Choose a first task

- **Inspect the FreeRTOS IHU:** connect the UART, run `help`, `stats`, then
  `eps raw` or `eps json`. Use `quiet` if background text obscures your capture.
- **Inspect the CAN IHU:** open its USB text console, run `status` and `help`.
  `eps json` observes the charger; `eps adc on` changes ADC configuration.
- **Check Yamcs commanding:** choose `ember` / `realtime`, verify that its command
  endpoint is the simulator or spare USB Pico, send `PING`, then inspect that
  command's history for the correlated result.
- **Watch native EPS over UHF:** choose `ember-uhf` / `realtime` and open EPS.
  Use the [UHF service runbook](../../ground/uhf/SERVICES.md) for the optional
  bench; native cadence is armed separately and no RF command uplink is configured.
- **Watch native EPS over LTE:** choose `ember-lte` / `realtime` and open EPS.
  Follow the [LTE runbook](../../ground/lte/BRINGUP.md) when preparing a bounded
  bench session. Commanding is not configured on this instance.

## Meaning of status

“Implemented” means behavior exists in the reviewed source. “Recorded hardware
validation” applies to the linked run and image. “Draft” describes proposed
mission behavior. A saved display value or old successful test is not evidence
that the current hardware is connected. Inspect timestamps, boot identity,
quality and current link/packet activity before acting on a reading.
