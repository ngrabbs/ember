# Retired USB Pico bench setup

The standalone binary USB Pico application and its build helper were removed.
They are available in [Git history](https://github.com/ngrabbs/ember/blob/ae5fc3d2fa53ee071c4b79e2851cbe8c079365d1/firmware/usb_bench/README.md).
This was a separate Pico demonstration, not the current IHU USB console path.

Dated [hardware validation](usb_validation.md) retains the image hash, device
identity, flash preservation and command/response observations. The portable
[command engine](../../firmware/shared/ember_protocol/README.md) remains in use
by IHU and host tests; the old standalone endpoint is no longer built here.

For current operation use the [IHU console guide](../../docs/user/ihu-can-console.md),
[payload guide](../../docs/user/payload.md), and
[Yamcs environments/serial ownership](../../ground/yamcs/OPERATIONAL.md).
The IHU uses text console commands through the sole-owner serial bridge, not
the retired spare Pico's binary USB transport.
