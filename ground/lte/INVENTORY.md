# Bench inventory — 2026-10-01

| Role | Host | Observed state |
|---|---|---|
| Ground radio | `ngrabbs@ember-ground.local`, `192.168.1.251` | Pi 5, aarch64, Debian 13; LibreSDR enumerates as `2500:0020` Ettus USRP B210; initial USB 480 Mbps, then 5000 Mbps after firmware loading; UHD 4.8 installed; native OAI and srsEPC builds complete |
| Walter controller | `ngrabbs@192.168.1.252` | `m75q`, Ubuntu; Walter USB serial `/dev/ttyACM0`; account has dialout access |
| Previous LTE lab | `dng@192.168.1.37` | `x1c`; source `/home/dng/Desktop/srsRAN_4G`; built eNB/EPC binaries present |

## Previous ordinary LTE baseline

- Git commit `ec29b0c1f`, description `release_23_11-6-gec29b0c1f`.
- Upstream `https://github.com/srsRAN/srsRAN_4G.git`.
- Build cache finds UHD; SoapySDR not found.
- PLMN MCC `999`, MNC `70`; TAC `0x0007`; APN `srsapn`.
- `n_prb = 50`; primary cell downlink EARFCN `3350`.
- Recovered gains: TX `80`, RX `40`. These are historical settings, not
  calibrated output power or recommended first-start values.
- EPC bind `127.0.1.100`, eNB bind `127.0.1.1`; SGi `172.16.0.1`.
- Private database `/home/dng/Desktop/srsRAN_4G/srsepc/user_db.csv` contains four
  records. Walter's installed SIM matches record 4 (Milenage), checked privately.
- Saved `first_ping.log` reports five packets sent/received to `172.16.0.2`,
  zero loss. This is historical evidence, not a new hardware validation.

Tracked config copies rewrite host-specific file paths to sibling config names.
The EPC copy also suppresses HSS debug and hex dumps. Original config hashes are
in `configs/srsran-4g/source-sha256.json`; they describe source bytes before edits.

## LibreSDR FPGA image

Source: `dng@192.168.1.37:/home/dng/Desktop/usrp_b210_fpga.bin`

Size: `2858228` bytes.

SHA-256:

```text
7f0e329b4724e0d919a06b9924aaa3c77305b6f25038deebd6171657ac7c8a99
```

This is the user-identified image for LibreSDR. UHD probe, streaming, and OAI
initialization on the Pi succeeded with this image. Do not substitute a stock image
without recording and verifying that change.

## Walter observation

Stable USB path:
`/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_24:58:7C:6F:0C:24-if00`

Serial: 115200 baud. Existing application announces Walter GM02SP passthrough,
based on the QuickSpot WalterModem passthrough example. Source location and
build provenance are unknown; no flashing was performed.

| Query | Response |
|---|---|
| `AT` | `OK` |
| `AT+CGMM` | `GM02SP` |
| `AT+CGMR` | `UE8.2.1.0` |
| `AT+CFUN?` | `+CFUN: 0` |
| `AT+CPIN?` | `ERROR` |
| `AT+CEREG?` | `+CEREG: 1,0` |

USB serial observation produced an ESP32 reset banner and the application's
modem reset sequence. Opening the port may reset this application; account for
boot time. Minimum-functionality state means the CPIN error does not establish
that the SIM is absent or defective. Later CFUN 4 no-RF queries returned
CPIN READY and a matching HSS identity. The table records the initial inventory,
not the latest SIM state.

## Completed ground-radio bring-up

See [2026-10-01 results](results/2026-10-01-ground-radio.md) for successful
custom FPGA initialization, USB 3 operation, and the receive-only benchmark.

## Independent receiver and comparison UE

On M75q, HackRF One (VID/PID 1d50:6089, serial suffix 31805783) is now available
as an independent receive-only instrument. Firmware 2024.02.1, host tools
2023.01.1. Raw I/Q lives on `/media/ngrabbs/BACKUP-A/ember-lte/captures`.

Thingy:91 X enumerates as Nordic USB 1915:910a, with by-id serial interfaces
ending `if01` and `if04`. Neither answered the short AT probe; application/modem
firmware and SIM state remain unknown. No flashing was performed. Walter's tty
number changed after reconnect; always use its stable Espressif by-id path.

See [independent RF/access results](results/2026-10-01-hackrf-lte.md) for
measured synchronization and the OAI LTE-M scheduler failures.

On 2026-10-02, with Thingy powered down, experimental OAI Msg3 cleanup and
Msg4 retry patches reached Walter RRC Setup Complete, accepted SIM authentication,
and NAS Security Mode Complete. Additional RAR release and lifecycle candidates
are applied on the Pi. Walter subsequently completed LTE-M attach and reported
registration; modem PDP context 1 returned 172.16.0.2. UDP delivery and PHY
regression remain unresolved. Walter is restored to CFUN 0 after each bounded
trial. See [latest results](results/2026-10-02-rar-release.md).

On 2026-10-02 the user increased Walter–LibreSDR antenna separation to roughly
six to eight feet. The gain-35, TX-59.75 run did not complete RRC setup. A
follow-up at TX gain 69.75, with RX still 35, completed attach and bearer setup
but delivered no UDP packet. All tests were bounded and Walter was restored to
CFUN 0. See [separation comparison](results/2026-10-02-separated-antennas.md).
