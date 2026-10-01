# Ground Pi preparation

[Ground station checklist](TODO.md) · [Ground software](../../ground/README.md)

The installed Pi and verified settings are in the [lab inventory](lab_inventory.md).

Flash **Raspberry Pi OS Lite (64-bit)** with Raspberry Pi Imager. The current
Debian 13 Trixie image supports Pi 4 and Pi 5. Use a Pi 5 with at least 4 GB RAM
and cooling if available; Pi 4 is suitable for initial software tests. Radio
performance and the complete service memory budget still need benchmarking.

In Imager, select the exact board model and storage device, then configure:

- Hostname: `ember-ground`.
- A normal user, preferably the same username used for SSH elsewhere.
- SSH enabled, using the laptop's public key if available.
- Local time zone and Wi-Fi credentials if Ethernet is unavailable.

Use an appropriate supply and a reliable microSD card (32 GB or larger is a
practical start); SSD storage can follow for the telemetry archive. Connect
Ethernet and leave SDR/Pico hardware disconnected for this first milestone.

After first boot, from the laptop:

```sh
ssh YOUR_USER@ember-ground.local
uname -m
free -h
cat /etc/os-release
df -h /
```

Expect `aarch64`. Record model, RAM, username and IP in the lab inventory before
installing services. Run normal OS updates, then install Git, Python 3 and Docker
Engine with its Compose plugin using the
[official Debian repository instructions](https://docs.docker.com/engine/install/debian/).
The installed Pi passed native ARM64 image and starter checks.

Start with the [software starter](../../ground/yamcs/README.md). The laptop is
the browser client; the Pi will host ground services. Direct SDR USB attachment
comes after the software and wired command loop pass.

Sources: [official OS images](https://www.raspberrypi.com/software/operating-systems/),
[Imager/first-boot guide](https://www.raspberrypi.com/documentation/computers/getting-started.html).
