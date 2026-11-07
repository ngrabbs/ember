# EMBER

**Emission Monitoring for Burn Event Recognition** is a Mississippi State ECE
capstone project building a CubeSat-class wildfire detection instrument and
ground station. A narrowband camera payload looks for the potassium emission
signature of flaming vegetation and reports detections for downlink.
[Mission scope](docs/architecture/project_scope.md) ·
[Payload instrument](https://github.com/ngrabbs/koenig_wildfire)

## System at a glance

```text
Spacecraft side                                           Ground side

EPS charger ── I²C ── IHU
                      ├─ CAN A ─ UHF COMMS ── UHF ─────── UHF SDR ──────┐
Payload Pi ── CAN A ──┤                                                 ├─ Yamcs
                      └─ CAN ─ Walter MCU                               │
                               └─ UART ─ Walter ─ LTE-M ─ LTE network ──┘
```

The diagram shows data paths exercised in bench setups. The EPS also supplies
power through the [CubeSat Kit Bus](system/interfaces/cskb_pinmap.md).
Flight operation and redundant CAN failover are still open.

**[Wire the boards](system/interfaces/README.md)** ·
**[Receive telemetry](docs/comms/README.md)** ·
**[Operate in Yamcs](docs/user/yamcs.md)**

[All docs](docs/README.md) · [Open work](TODO.md) · [License](LICENSE)
