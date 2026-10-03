# LTE bench bring-up runbook

Status: OAI and srsEPC are built on the Pi; S1 setup works. Walter completed
LTE-M attach and reported registration, with IP 172.16.0.2 and bearer setup.
Experimental RAR release avoids the observed downlink-pool failure in bounded
runs. Reestablishment stability, PHY simulator regression, and UDP delivery
remain unresolved. See [latest results](results/2026-10-02-rar-release.md).

## 1. Access and inventory

```sh
ssh ngrabbs@ember-ground.local        # Pi / LibreSDR
ssh ngrabbs@192.168.1.252             # M75q / Walter
ssh dng@192.168.1.37                 # previous srsRAN / private SIM database
```

On the Pi:

```sh
hostname
uname -a
lsusb
lsusb -t
command -v uhd_find_devices uhd_usrp_probe
```

The SDR enumerates at 480 Mbps before controller firmware loads, then at 5000 Mbps. Enumeration alone does not
verify its FPGA, streaming, or RF operation. Start with discovery/probe.

## 2. Install radio utilities and stage the image

On the Pi, inspect package availability, then install UHD host utilities:

```sh
apt-cache policy uhd-host
sudo apt-get update
sudo apt-get install uhd-host
mkdir -p ~/work/ember-lte/images ~/work/ember-lte/private ~/work/ember-lte/logs
chmod 700 ~/work/ember-lte/private ~/work/ember-lte/logs
```

From the Mac, copy the user-identified FPGA image through a temporary directory:

```sh
task_lte_tmp=$(mktemp -d)
scp dng@192.168.1.37:/home/dng/Desktop/usrp_b210_fpga.bin "$task_lte_tmp/"
scp "$task_lte_tmp/usrp_b210_fpga.bin" ngrabbs@ember-ground.local:work/ember-lte/images/
rm -r "$task_lte_tmp"
```

On the Pi:

```sh
sha256sum ~/work/ember-lte/images/usrp_b210_fpga.bin
uhd_images_downloader --types "^b2xx_common_fw_default$" --install-location "$HOME/work/ember-lte/images"
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=usb --attr-match=idVendor=2500
export UHD_IMAGES_DIR="$HOME/work/ember-lte/images"
uhd_find_devices
uhd_usrp_probe --args "type=b200,fpga=$HOME/work/ember-lte/images/usrp_b210_fpga.bin"
```

Expected image hash is in [INVENTORY.md](INVENTORY.md). Record UHD version and
probe output. A probe may load volatile firmware/FPGA into the radio; it does
not start an LTE cell. If firmware is missing or image compatibility fails,
resolve that specific error and record any images added. Do not silently fall
back to a stock FPGA. Check USB permissions before running the probe as root.

## 3. Recover the ordinary LTE baseline (optional SIM7600 regression)

These configs are for the **previous ordinary LTE setup**, not Walter LTE-M.
The existing x1c build avoids rebuilding the full stack just to revisit it.
Run the EPC and eNodeB on the same host for these loopback bind addresses.
Moving one component to the Pi requires explicit address changes.

From the repository root on the Mac:

```sh
ssh dng@192.168.1.37 'mkdir -p ~/work/ember-lte/configs'
scp ground/lte/configs/srsran-4g/*.conf dng@192.168.1.37:work/ember-lte/configs/
ssh dng@192.168.1.37 'umask 077; cp ~/Desktop/srsRAN_4G/srsepc/user_db.csv ~/work/ember-lte/configs/user_db.csv'
```

Work in the staged copies. Review the band, antenna/conducted RF arrangement,
attenuation, and gains before starting a cell. Historical TX gain 80 is not a
first-start recommendation. An eNodeB starts transmitting when launched.

When the SDR is connected to x1c, set the staged `enb.conf` `[rf]` section:

```ini
device_name = UHD
device_args = type=b200,fpga=/home/dng/Desktop/usrp_b210_fpga.bin
```

Use the recovered version's existing binaries, in separate SSH terminals:

```sh
# Terminal 1: EPC
cd ~/work/ember-lte/configs
sudo /home/dng/Desktop/srsRAN_4G/build/srsepc/src/srsepc epc.conf
```

```sh
# Terminal 2: eNodeB, after RF setup review
cd ~/work/ember-lte/configs
sudo /home/dng/Desktop/srsRAN_4G/build/srsenb/src/srsenb enb.conf
```

Review `/tmp/epc.log` and `/tmp/enb.log` privately. Validate SIM7600 attach,
assigned address, and traffic to SGi `172.16.0.1`. External internet access
requires separate routing/NAT configuration; it is unnecessary for a local
telemetry receiver. Stop each foreground application with Ctrl-C.

Pi deployment needs an aarch64 build; the existing x1c binaries are x86_64.

## 4. Inspect Walter without changing radio configuration

On the M75q, pyserial is already installed. Ensure no other process owns the
port. Open its stable by-id path at 115200 baud and query:

```text
AT
AT+CGMM
AT+CGMR
AT+CFUN?
AT+CPIN?
AT+CEREG?
```

Opening USB serial produced a reset during inventory, and the application
resets the modem on boot. Allow at least 10 seconds before queries. Use the
Sequans AT reference for the installed firmware before changing functionality,
RAT, bands, PLMN, or APN. Do not assume USB is a direct modem interface: the
ESP32 passthrough bridges it to the modem UART.

Latest verified state: GM02SP UE8.2.1.0, LTE-M selected, SIM READY in CFUN 4
(no RF), and IMSI matched privately to HSS record 4. The user has attached LTE
and GPS antennas. APN context 1 is now `srsapn`. CFUN 0 is the stopped state.
Do not publish the subscriber credentials.

## 5. Bring up LTE-M

Build both applications using [BUILD.md](configs/oai/BUILD.md). Stage the OAI
example as `~/work/ember-lte/configs/enb.band13.emtc.conf`, alongside `epc.conf`
and the private HSS database. Run `scripts/smoke-s1.py` first: this uses simulated
radio, does not transmit, and validates S1 setup only.

After checking antennas, band and bench RF setup, a bounded hardware attempt
uses two terminals on the Pi:

```sh
cd ~/work/ember-lte/configs
sudo timeout --signal=INT --kill-after=5 150 \
  ../srsRAN_4G/build-epc/srsepc/src/srsepc epc.conf
```

```sh
cd ~/work/ember-lte/openairinterface5g/build-lte
sudo env UHD_IMAGES_DIR=/home/ngrabbs/work/ember-lte/images \
  timeout --signal=INT --kill-after=5 140 ./lte-softmodem \
  -O /home/ngrabbs/work/ember-lte/configs/enb.band13.emtc.conf \
  --parallel-config PARALLEL_SINGLE_THREAD --worker-config WORKER_DISABLE
```

This starts RF transmission. The current candidate is band 13, DL 751 MHz,
UL 782 MHz, 50 PRB, PLMN 999/70. The logged UHD gains are TX 29.75 dB and
RX 35 dB; these values do not establish radiated power. Preserve logs privately.
Timeout exit 124 is expected. Verify processes stopped afterward.

On Walter, wait 12 seconds after opening the serial port, then issue each command
only after its final OK/ERROR response:

```text
AT+CMEE=2
AT+CFUN=0
AT+CGDCONT=1,"IP","srsapn"
AT+CEREG=2
AT+CFUN=1
AT+COPS=1,2,"99970"
AT+CEREG?
AT+CSQ
AT+CGATT?
AT+CGPADDR=1
AT+CFUN=0
```

Allow network selection a long bounded timeout. If it remains pending, do not
stack other commands behind it. Reopen/reset the passthrough and explicitly
confirm CFUN 0 before leaving the hardware unattended. Signal value 99 and
CESQ 255 mean unknown/unavailable, not measured signal strength. A smaller
ordinary LTE bandwidth does not enable Cat-M1.

Acceptance sequence:

1. Walter discovers a cell advertising Cat-M1 support.
2. Random access and RRC connection complete.
3. SIM authentication and registration succeed.
4. A conventional IP bearer is established and Walter receives an address.
5. Sequenced UDP telemetry reaches the ground receiver.
6. Reset/reconnect tests reproduce the same result.

Record versions, payload/rate/duration, loss, RTT, signal metrics, and recovery
behavior. Label historical, newly measured, and simulated evidence separately.

## Repeating the receive-only checks

Copy `scripts/probe-radio.sh` and `scripts/benchmark-rx.sh` to the Pi and run
them there. Both verify the custom FPGA checksum and select it explicitly.
The benchmark exercises one RX channel at 15.36 Msps for 10 seconds. It does
not verify full-duplex operation or eNodeB real-time performance.

## Independent RF diagnostics

See [HackRF results](results/2026-10-01-hackrf-lte.md). The latest experiments
reached LTE synchronization and exercised LTE-M random access, then encountered
OAI scheduler/resource assertions. A completed attach is still outstanding.

On M75q, with the eNodeB already running and its readiness confirmed:

```sh
mkdir -p /media/ngrabbs/BACKUP-A/ember-lte/captures
umask 077
hackrf_transfer -r /media/ngrabbs/BACKUP-A/ember-lte/captures/lte-on.cs8 \
  -f 751000000 -s 16000000 -n 32000000 -a 0 -p 0 -l 32 -g 32
```

This is two seconds of receive-only I/Q. Capture another sample after the cell
stops, at identical receiver settings. Remove DC before comparing spectra and
check ADC rail clipping. Keep raw I/Q outside Git. Use the large external drive
rather than M75q's nearly full root filesystem.

On the Pi, `scripts/check-tx-rx.py --transmit` runs a bounded tone self-check;
`--tx-gain 49.75 --duration 5` reproduces the longer test. It transmits at
751.125 MHz, uses the custom FPGA, and leaves no continuous TX running. Its
same-radio measurement includes internal coupling and is not calibrated power.

The offline helper expects cf32 at 1.92 Msps. Build on the Pi:

```sh
task_srs="$HOME/work/ember-lte/srsRAN_4G"
cc -O2 -I "$task_srs/lib/include" -I "$task_srs/build-epc/lib/include" \
  "$HOME/work/ember-lte/decode-mib-file.c" \
  "$task_srs/build-epc/lib/src/phy/libsrsran_phy.a" \
  -lfftw3f -lstdc++ -lm -lpthread -o "$HOME/work/ember-lte/decode-mib-file"
timeout 12 "$HOME/work/ember-lte/decode-mib-file" input-1m92.cf32 0
```

Only result 1 establishes CRC-validated PBCH/MIB decoding. This helper has not
yet obtained that result on the short HackRF capture. Frequency correction must
be measured for the capture, not assumed to always be 6.8 kHz.

## Controlled Walter OFF/ON tests

These helpers reproduce the 2026-10-02 comparison and transmit when the Pi
helper runs. They assume the already built binaries, private EPC configuration,
custom FPGA image, and current bench setup. Keep Thingy powered down.
From the EMBER repository root on the Mac:

```sh
scp ground/lte/scripts/run-radio-check.py ground/lte/scripts/summarize-ra-log.py \
  ngrabbs@ember-ground.local:work/ember-lte/
scp ground/lte/scripts/walter-radio-check.py \
  ngrabbs@192.168.1.252:work/ember-lte/
scp ground/lte/configs/oai/enb.band13.emtc.tx30.conf.example \
  ngrabbs@ember-ground.local:work/ember-lte/configs/enb.band13.emtc.tx30.conf
```

Confirm no prior eNodeB/EPC or serial client is running. First prepare Walter
OFF and wait for `CFUN 0 confirmed`, then run the baseline:

```sh
ssh ngrabbs@192.168.1.252 'python3 ~/work/ember-lte/walter-radio-check.py'
ssh ngrabbs@ember-ground.local \
  'python3 ~/work/ember-lte/run-radio-check.py control-off --seconds 40'
```

For ON, start the Pi command in terminal 1. After its steady-state message,
run terminal 2. Wait for both to finish before starting another test:

```sh
# Terminal 1
ssh ngrabbs@ember-ground.local \
  'python3 ~/work/ember-lte/run-radio-check.py control-on --seconds 90'
```

```sh
# Terminal 2
ssh ngrabbs@192.168.1.252 \
  'python3 ~/work/ember-lte/walter-radio-check.py --enable-seconds 35'
```

The serial helper resets the existing passthrough on opening, waits 12 seconds,
then sets CFUN 0, band 13, APN, and enables RF for the bounded interval. It
restores the full standard band list and confirms CFUN 0 afterward. This
requires the current GM02SP passthrough and persisted manual PLMN selection;
it is not a generic Walter firmware installer. Its COPS query must show the
expected manual-selection state from the bench preparation.

Pi logs are private and UTC-stamped. Use unique run labels to avoid overwriting
evidence. Existing labels from 2026-10-02 are recorded in the results document.
An assertion is not a successful timeout. The Msg3-only patch retains the Msg4
assertion; the newer [Msg4 candidate](patches/README.md#msg4-retry-candidate)
replaces that path with bounded retries. Downlink allocation failures remain.

```sh
ssh ngrabbs@ember-ground.local \
  'python3 ~/work/ember-lte/summarize-ra-log.py ~/work/ember-lte/logs/control-on-oai.log'
```

To reproduce the cleanup comparison, make a runtime copy with only
`mac_log_level="debug"` changed and select it using `--config` on the Pi
helper. Keep the runtime profile and source patch state explicit in results.

The tracked `ceonlydiag` and `ce300diag` example profiles preserve subsequent
tests with TX attenuation 40, MAC-debug logging, and increased PRACH detection
thresholds. Stage without `.example` and select with `--config`. They are
diagnostic profiles, not validated defaults. The [latest results](results/2026-10-02-msg4-authentication.md)
list their exact differences and authentication milestones.

## Numbered UDP bench trial

This uses Walter's existing serial passthrough and modem socket commands; no
firmware flashing is needed. The commands follow the pinned vendor
[Walter socket implementation](https://github.com/QuickSpot/walter-arduino/blob/c30b707f8d64b49daec80de6bccfc80c04e42d58/src/proto/WalterSocket.cpp).
Only the modem sends to the EPC gateway; the M75q does not send test datagrams
to the ground receiver. Payloads are JSON with run ID, sequence, and M75q UTC
send timestamp, padded to 128 bytes. Host clocks have not been validated for
one-way latency.

Stage the helpers and selected diagnostic profile from the repository root:

```sh
scp ground/lte/scripts/udp-bench-receiver.py ngrabbs@ember-ground.local:work/ember-lte/
scp ground/lte/scripts/walter-radio-check.py ngrabbs@192.168.1.252:work/ember-lte/
scp ground/lte/configs/oai/enb.band13.emtc.ce300tx30diag.conf.example \
  ngrabbs@ember-ground.local:work/ember-lte/configs/enb.band13.emtc.ce300tx30diag.conf
```

Confirm no prior receiver, eNodeB/EPC, or serial client is running. Use a new
run ID for each trial. In three terminals, start the receiver first, then the
cell, then enable Walter after steady-state operation is reported:

```sh
ssh ngrabbs@ember-ground.local \
  'python3 ~/work/ember-lte/udp-bench-receiver.py udp-example --count 10 --seconds 150'
ssh ngrabbs@ember-ground.local \
  'python3 ~/work/ember-lte/run-radio-check.py udp-example --seconds 140 --config enb.band13.emtc.ce300tx30diag.conf'
ssh ngrabbs@192.168.1.252 \
  'python3 ~/work/ember-lte/walter-radio-check.py --enable-seconds 100 --udp-count 10 --run-id udp-example'
```

After registration, the sender queries PDP/IP state and CSQ, configures UDP
socket 1 on PDP context 1, and sends to 172.16.0.1:51000 from local port 51001.
It waits for each data prompt, sends exactly 128 bytes, and waits for the final
result before the next command. It requests a one-second pause between sends;
actual spacing also includes command/response time. A rejected or pending
command stops the trial. Recovery reopens/reset the passthrough, confirms
CFUN 0, and restores the full standard band list.

Compare modem-accepted sends with receiver sequence numbers, not the requested
count alone. A modem `OK` does not prove delivery. The receiver reports unique
packets, missing sequence numbers against the requested count, duplicates,
out-of-order arrivals, byte lengths, source IPs, and receive span. It stops when
all expected packets arrive or its deadline expires; duplicates after that stop
are unobserved. Sender failures and unsent packets must not be presented as
measured packet loss. This initial test does not measure RTT, downlink telemetry,
or one-way latency. Keep complete logs private and save sanitized counts here.

For the first demonstrated telemetry configuration, apply all six patches in
order and select `enb.band13.emtc.ce300tx20diag.conf`; see the
[first UDP results](results/2026-10-02-uplink-telemetry.md). This is not yet a
repeatable or stable-link acceptance result.

Add `--socket-diagnostics` to the Walter command for optional `SQNSS?` queries
before/after sends and registration/PDP queries after a completed send error.
A completed error from a status query is recorded without aborting the send
loop; a pending response still stops commands. This modem returned status-query
errors even while UDP packets were successfully delivered.

For packet-path diagnosis, install `tcpdump` on the Pi and start a bounded
capture before starting the cell, in a separate terminal. Use a fresh run ID
and keep the capture private:

```sh
ssh ngrabbs@ember-ground.local \
  'umask 077; sudo -n timeout --signal=INT --kill-after=5 160 tcpdump -i any -nn -s 0 -U -w ~/work/ember-lte/private/udp-example.pcap "udp port 2152 or udp port 51000"'
```

Compare matching run IDs/sequences inside GTP-U with SGi and receiver output;
total GTP packet count can include unrelated traffic. Confirm Walter's CFUN 0
restoration and both network process exits after every trial.

For a bounded retry/queue-settling experiment, add `--send-retries 3
--settle-seconds 15` to the Walter command and use `--enable-seconds 120`.
Retries apply only to completed pre-prompt `operation not supported` errors,
with a two-second wait and at most three additional attempts. Payload submission,
generic errors, and pending responses are never automatically retried. The
settling wait is capped by the remaining enable deadline and does not prove
that the modem queue drained. These controls do not fix the network's observed
signaling-bearer failures. See [repeat results](results/2026-10-02-repeatability-release.md).

The current Pi has eight candidates, including downlink retry MCS retention and
new-bearer PDCP security initialization. The normal binary SHA-256 is
`5c5de8e17db509b35823f401b99c7fdbe28144307da0be24fbc777c569768e11`.
See the [security comparison](results/2026-10-02-srb2-security.md) for six EPS
deliveries across two windows; repeat reliability before qualifying this build.
For release tracing, select `enb.band13.emtc.ce300tx20rrcdiag.conf`; it adds
RLC/RRC debug logging to the same RF settings. Keep the selected patch set and
profile explicit in every result. Run sender retry checks locally with:

```sh
python3 -m unittest discover -s ground/lte/scripts/tests -v
```

For optional per-bearer STATUS and compact CE HARQ tracing, use the separate
[diagnostic procedure](diagnostics/README.md). Its two profiles lower MAC log
volume and optionally reduce RX gain by 10 dB. Apply the temporary trace only
after the selected candidate set, and reverse it/rebuild when finished. The ordinary
RA summarizer's debug-only DTX count is unavailable with these MAC-info profiles.
See [RLC trace results](results/2026-10-02-rlc-status.md) for the observed failure
at the RRC Security Mode Command.
