# RTOS design

[Topic guide](README.md)

The [legacy IHU firmware guide](../../firmware/legacy_ihu/README.md) owns its FreeRTOS implementation.
The [legacy communications firmware](../../firmware/legacy_comms/README.md) also uses FreeRTOS.
The active [IHU firmware](../../firmware/ihu/README.md) is a
standalone Pico SDK application; it does not implement the production RTOS integration. Background material lives in [firmware research](../research/firmware_references.md).

The active [COMMS firmware](../../firmware/comms/README.md) also uses the standalone
Pico SDK runtime. The FreeRTOS applications remain reference prototypes.
