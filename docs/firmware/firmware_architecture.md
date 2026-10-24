# Firmware architecture

[Topic guide](README.md)

Use the [IHU firmware guide](../../firmware/ihu/README.md) for housekeeping
implementation and the [transceiver firmware guide](../../firmware/transceiver/README.md) for comms
control. Shared behavior belongs in the [operations draft](../architecture/operations/README.md)
and [system interfaces](../../system/README.md).

The [IHU FreeRTOS architecture and migration record](rtos_design.md) reviews
AMSAT rt-ihu and records the 0.15.0 candidate's six static tasks, single
application actor, bounded services and remaining hardware acceptance gates.
`firmware/ihu/app.c` owns policy/protocol/telemetry state;
`firmware/ihu/runtime.c` owns RTOS services. Other MCU applications retain their
existing runtimes. The candidate is deployed on the bench with initial smoke checks passed; full
hardware/RF acceptance remains pending.
