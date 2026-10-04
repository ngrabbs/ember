# Controller SWD access draft

2026-10-04. Added through Konnect to the disposable controller study. The fabricated Rev A files are unchanged. This extends the [controller support checkpoint](controller_support_draft.md).

This debug-only checkpoint is historical; see the [CAN-interface extension](controller_can_interface_draft.md) for the latest verification status.

## Logical interface

J1 is a generic five-contact logical placeholder with no assigned footprint or accepted physical connector. Its numbering is provisional and does not claim compatibility with a standard debugger cable. Select a low-profile connector or pogo/test-pad interface, then review the adapter, mating view, orientation and physical pad map before placement.

| J1 logical pin | Signal | Target endpoint |
|---|---|---|
| 1 | VTref | Essential +3V3 downstream of hardware interlocks |
| 2 | EPS_SWDIO | U1.24, PA13 |
| 3 | EPS_SWCLK | U1.25, PA14/BOOT0 |
| 4 | EPS_NRST | U1.6, PF2/NRST; existing C13 to ground |
| 5 | GND | Target logic ground |

ST's [AN5096 hardware-development guidance](https://www.st.com/resource/en/application_note/an5096-getting-started-with-stm32g0-mcus-hardware-development-stmicroelectronics.pdf) identifies PA13/PA14 for SWD and reset/supply access for the debugger. Physical MCU pins were queried from the previously verified GP candidate before wiring. No extra pull resistors or reset network changes were introduced.

VTref is for debugger target-voltage sensing. Use a probe/adapter configuration that does not inject power into the target. Debug signal injection can back-power an unpowered MCU; disconnect the probe for RBF/deployment isolation acceptance tests. A future dedicated service-power path must be explicitly interlocked and reviewed before implementation.

Keep PA13/PA14 available to SWD in firmware and preserve NRST reset input/output operation. Bench acceptance must demonstrate connect-under-reset and failed-image recovery, verify boot/security option bytes before programming, and measure unpowered leakage with the selected probe. These are requirements, not completed tests. A separate debug UART remains open; this addition does not allocate another UART or implement bootloader recovery.

## Verification and remaining limits

Saved/exported connectivity matches exact endpoint sets for all **13 named nets**: the previous 11 plus SWDIO and SWCLK. The supply, ground and reset nets gained only their intended J1 contacts. Konnect reports zero floating wire endpoints and zero merged named nets.

Direct ERC reports **24 errors, zero warnings**. The final saved report lists 22 unconnected pins and two undriven power pins (+3V3 and ground). The component/orphan queries and netlist identify 23 unfinished pins, including U1.18 (PA8), while the final ERC omits its unconnected-pin report. An earlier ERC response classified the same total as 23 unconnected and one undriven supply. This diagnostic coverage disagreement remains unresolved; the total does not establish acceptance. No power flags or no-connect markers were added to suppress unfinished work.

Geometry inspection resolved all 65 symbol bounds and flagged three power-symbol/pin-bound overlaps (the two CAN ground contacts and J1 VTref contact). Their intended connections and the rendered sheet were inspected. The new ground symbol was moved below J1 to separate its text from the value field. This is schematic readability evidence, not PCB clearance evidence.

Schematic mutations are file-based and were verified through fresh saved exports. Konnect's save_project command saves the live PCB through IPC; it was not used to save this standalone schematic or overwrite the separate package-comparison board. The scratch PCB remains unsynchronized and unsuitable for fabrication. Exact debug connector/footprint, supply isolation, firmware and bench acceptance remain open.

[Saved netlist](evidence/2026-10-04_controller_debug.net) · [verified endpoints](evidence/2026-10-04_controller_debug_verified.json) · [ERC](evidence/2026-10-04_controller_debug_erc.json) · [Konnect checks](evidence/2026-10-04_controller_debug_checks.json)

![Controller with logical SWD access](previews/controller_debug.png)

[PDF preview](previews/package_check_controller-debug-draft-final_1791120257.pdf).
