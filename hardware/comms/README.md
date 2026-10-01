# Communications hardware

EMBER's documented radio design is **437 MHz BPSK TX / 435 MHz RX**, half duplex
through one antenna connector, J9. It retains the low-power ADL5602 transmitter;
RF performance and manufacturing readiness remain open.

Start with the [design overview](design/overview.md), then the
[current work list](TODO.md). Recorded ERC/DRC results are dated evidence, not a
fresh validation of the working board.

| Need | Go to |
|---|---|
| Understand the circuit | [Design guide](design/README.md) |
| Open the board | [KiCad project](kicad/README.md) |
| Resolve exact parts and availability | [BOM and sourcing](bom/README.md) |
| Run prototype tests | [Bring-up guide](bringup/README.md) |
| Check package audits or prior verification | [Verification records](verification/README.md) |
| Reproduce RF screening | [Analysis workspace](design/analysis/README.md) |
| Find old fabrication outputs | [Release records](releases/README.md) |

## Keeping this folder useful

Current decisions belong in `design/`; remaining work belongs in `TODO.md`.
Keep package acceptance and significant verification evidence in `verification/`,
procurement evidence in `bom/`, and measurements in `bringup/`. Completed repair
narratives and intermediate synchronization previews belong in Git history.

Local Konnect state, editor caches, and disposable exports are ignored. Keep
source projects, libraries, simulation inputs, acceptance evidence, and intentional
release bundles tracked. Put new disposable analysis output in `design/analysis/output/`.

[System interfaces](../../system/README.md) · [Documentation home](../../docs/README.md)
