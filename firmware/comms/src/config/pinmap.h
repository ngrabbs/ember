/*
 * Comms board pin assignments.
 *
 * Source of truth is the rev 0.9 Pico pin table in
 * hardware/comms/design/schematic_guide.md ("Sheet 5: Digital Control"),
 * cross-checked against hardware/comms/kicad/Digital_Control.kicad_sch.
 *
 * v0.1 proto: Raspberry Pi Pico module on the comms PCB. The board is
 * a Pico *module* carrier, so GP25 (onboard LED) and the module's own
 * USB are both available for bring-up. Bare-RP2040 flight redesign is
 * deferred until the RF chain is validated.
 *
 * Where the imported KiCad (rev 0.5) and the schematic guide (rev 0.9)
 * disagree, the guide wins and the difference is called out inline.
 */

#pragma once

#include "hardware/i2c.h"
#include "hardware/spi.h"

/* ── Housekeeping ──────────────────────────────────────────── */

/* Pico module onboard LED. Not on the comms schematic — it lives on
 * the module, so it is the one indicator that works on a bare Pico
 * as well as on the populated board. */
#define COMMS_LED_GPIO              25

/* ── I2C0 → Si5351A clock generator ────────────────────────── */

/* Guide rev 0.8 moved I2C from GP8/GP9 to GP20/GP21 to shorten the
 * run to the Si5351A on the right-hand side of the board. Both are
 * I2C0 alternate-function pins. Bus pull-ups are R1/R2 = 4.7k on the
 * Clock Gen sheet, so no internal pull-ups are required (we still
 * enable them — harmless in parallel with 4.7k, and it keeps the bus
 * defined if the board is unpopulated). */
#define COMMS_I2C_INSTANCE          i2c0
#define COMMS_I2C_SDA_GPIO          20
#define COMMS_I2C_SCL_GPIO          21
#define COMMS_I2C_HZ                (400 * 1000)  /* 400 kHz — bench-validated in bringup/si5351a_bringup_log.md */

/* ── I2C1 → IHU housekeeping link (BENCH ONLY) ─────────────── */

/* A bench harness, not a flight interface. Read this before wiring
 * anything or believing anything below.
 *
 * This board revision does NOT bring I2C back to the CSKB stack bus.
 * The IHU link on the schematic is SPI (H1.21-H1.24 plus COMMS_IRQ on
 * H1.16), per system/interfaces/comms_to_ihu.md, and the intended
 * flight path is CAN on H1.51/H1.52 — see the Iteration 2 section of
 * system/interfaces/board_to_board.md. Neither of those exists in
 * firmware yet.
 *
 * What this is: a two-jumper link between two Pico modules on a desk,
 * so the IHU has something real to talk to while the CAN transport is
 * designed. It answers at COMMS_HK_I2C_ADDR with the register map in
 * firmware/shared/comms_hk_proto.h. That map is also the seed for the
 * CAN 0x300-0x3FF "communications status" message group, so the
 * telemetry schema survives even though this transport will not.
 *
 * Bench wiring:
 *   IHU GP4 (SDA) ── comms GP14
 *   IHU GP5 (SCL) ── comms GP15
 *   grounds tied
 *
 * Why i2c1 and not i2c0: i2c0/GP20/GP21 is this board's master bus to
 * the Si5351A. The RP2040 I2C block cannot be master and slave at the
 * same time, so hanging the IHU off i2c0 would mean flipping the
 * peripheral between modes and dropping any IHU transaction that
 * arrived mid-flip. i2c1 on GP14/GP15 (both J3 spares, both i2c1
 * alternate-function pins) keeps the two completely independent.
 *
 * NOTHING HERE IMPLIES A BOARD CHANGE. GP14/GP15 are jumper points on
 * a Pico module, not a proposed net. Do not add pull-ups for this —
 * the IHU's internal ones carry a desk-length link fine. */
#define COMMS_HK_I2C_INSTANCE       i2c1
#define COMMS_HK_I2C_SDA_GPIO       14
#define COMMS_HK_I2C_SCL_GPIO       15

/* Slave mode has no baud generator of its own — the master clocks the
 * bus. The RP2040 I2C block still needs a configured rate to size its
 * internal hold/setup timings, and it must be at least as fast as the
 * master will ever clock us. The IHU runs its bus at 100 kHz; 400 kHz
 * here leaves headroom if that is raised later. */
#define COMMS_HK_I2C_HZ             (400 * 1000)

/* ── SPI0 → IHU link (comms is the SLAVE) ──────────────────── */

/* Clustered on the left-hand side of the Pico (guide rev 0.7) to
 * shorten the CSKB routing. All four are SPI0 alternate-function
 * pins. Direction naming is from the IHU's point of view: the IHU is
 * master, so MOSI is an input here and MISO an output.
 *
 * Not initialised by v0.1 firmware — the pins are left as inputs
 * until the SPI transport task lands. */
#define COMMS_SPI_INSTANCE          spi0
#define COMMS_SPI_MISO_GPIO         4     /* CSKB H1.22 — comms → IHU */
#define COMMS_SPI_CS_N_GPIO         5     /* CSKB H1.24 — slave select from IHU */
#define COMMS_SPI_SCK_GPIO          6     /* CSKB H1.21 — clock from IHU */
#define COMMS_SPI_MOSI_GPIO         7     /* CSKB H1.23 — IHU → comms */

/* Data-ready interrupt to the IHU. Push-pull output, ACTIVE LOW,
 * normally held high; modelled on the AX5043 IRQ pattern in AMSAT
 * RT-IHU. The 10k pull-up lives on the IHU side (no pull-up on this
 * board), so firmware must drive this high at boot or the IHU sees a
 * spurious assert. */
#define COMMS_IRQ_GPIO              3
#define COMMS_IRQ_ASSERTED          0
#define COMMS_IRQ_DEASSERTED        1

/* ── TX path ───────────────────────────────────────────────── */

/* Baseband bit stream into the 74LVC1G86 XOR modulator (pin 2).
 * XOR'd against Si5351A CLK0 at 145.667 MHz, then tripled to 437 MHz.
 * Must be driven to a defined level at boot — a floating XOR input
 * puts random phase on the carrier. */
#define COMMS_BPSK_DATA_GPIO        16

/* ── Status / control indicators ───────────────────────────── */

/* KiCad Digital_Control.kicad_sch wires these to LEDs D10/D9 through
 * 330R (R23/R22). The all-UHF rebuild (see kicad_implementation_plan.md)
 * reuses TX_ACTIVE as the PE4259 T/R switch control line, with a
 * board pull-down so the switch defaults to RX at boot. Firmware
 * therefore drives TX_ACTIVE LOW at boot and keeps it low until a
 * transmit is actually commanded. */
#define COMMS_TX_ACTIVE_GPIO        10
#define COMMS_RX_ACTIVE_GPIO        11

/* Board power indicator D11 (330R, R24). The schematic guide rev 0.9
 * describes D3/"board power" as tied straight to the +3V3 rail; the
 * imported KiCad wires it to GP12 instead. Driving GP12 high is
 * correct for the KiCad wiring and harmless if the LED turns out to
 * be rail-tied (the pin is then simply unconnected). */
#define COMMS_PWR_IND_GPIO          12

/* ── RX path ───────────────────────────────────────────────── */

/* MCP6022 gain-stage output (gain = 11) into the RP2040 ADC.
 * Guide rev 0.9 moved this from ADC0 to ADC1, so the firmware uses
 * adc_select_input(1), not (0).
 *
 * The stage is biased to mid-supply for single-supply operation, so
 * with no signal present the ADC should read ~1.65 V. That makes it a
 * usable presence check for the analog RX chain: near 0 V or near
 * 3.3 V means the MCP6022 is unpowered, unpopulated, or its bias
 * network is wrong. */
#define COMMS_RX_BASEBAND_GPIO      27
#define COMMS_RX_BASEBAND_ADC_CH    1
#define COMMS_RX_BASEBAND_BIAS_V    1.65f   /* R10/R11 divider from +3V3 */
#define COMMS_RX_BASEBAND_TOL_V     0.35f   /* ±0.35 V before we call it a fault */

/* ── Board constants ───────────────────────────────────────── */

#define COMMS_ADC_VREF_V            3.3f
#define COMMS_ADC_FULL_SCALE        4096.0f  /* 12-bit */
