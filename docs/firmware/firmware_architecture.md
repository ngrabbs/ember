# Firmware architecture

[Topic guide](README.md)

Use the [IHU firmware guide](../../firmware/ihu/README.md) for housekeeping
implementation and the [transceiver firmware guide](../../firmware/transceiver/README.md) for comms
control. Shared behavior belongs in the [operations draft](../architecture/operations/README.md)
and [system interfaces](../../system/README.md).

The [IHU FreeRTOS migration plan](rtos_design.md) reviews AMSAT rt-ihu and
proposes task/resource ownership and staged acceptance gates. It is a proposal;
the active firmware still uses the Pico SDK main loop.
