# Runtime design

[Topic guide](README.md)

The active [IHU](../../firmware/ihu/README.md) and
[transceiver](../../firmware/transceiver/README.md) applications use the Pico SDK runtime.
The earlier FreeRTOS prototypes and kernel were removed; inspect
[Git history](https://github.com/ngrabbs/ember/tree/e133cf204a10ed47e703e5e5a81f17a4241268de/firmware)
for that implementation. General RTOS background remains in
[firmware research](../research/firmware_references.md).
