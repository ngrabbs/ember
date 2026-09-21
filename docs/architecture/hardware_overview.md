# Hardware guide

[Architecture](README.md) · [System interfaces](../../system/README.md)

Use the board's own folder for implementation and bring-up. Use the
[canonical pin map](../../system/interfaces/cskb_pinmap.md) for every shared
stack signal. Board status and open work stay in the owning documents and
[project TODO](../../TODO.md).

| Area | Start here |
|---|---|
| Electrical power | [EPS](../../hardware/eps/README.md) |
| Housekeeping computer | [IHU](../../hardware/ihu/README.md) |
| Radio | [Communications](../../hardware/comms/README.md) |
| Compute carrier | [Payload compute](../../hardware/payload_compute/README.md) |
| Optical instrument | [Payload instrument reference](../research/k_line_detection.md) |
| Experimental S-band work | [S-band payload](../../hardware/payload_exp_sband_tx/README.md) |
| Shared layout conventions | [Hardware references](../hardware/README.md) |

The compute-carrier documents describe the Jetson carrier; instrument development
also uses a Raspberry Pi in its separate repository. These are distinct documented
contexts, not interchangeable hardware configurations.
