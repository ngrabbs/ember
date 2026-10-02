# LTE bench bring-up runbook

Status: inventory and AT queries have been performed. The installation, radio
probe, eNodeB startup, and LTE-M attach steps below have **not** been executed.

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

The current SDR enumerates as B210 at 480 Mbps. Enumeration alone does not
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

Latest results: GM02SP, UE8.2.1.0, CFUN 0, CPIN ERROR, CEREG 1,0. Determine SIM
readiness in the appropriate functionality state; no SIM failure is diagnosed.
Compare IMSI/authentication details locally with the private HSS database.
Do not put those credentials in shell command history or tracked files.

## 5. Bring up LTE-M

There is no verified LTE-M launch configuration here yet. Use the
[TODO](TODO.md) to pin an OAI revision, verify eMTC operation and UHD hardware
support, and choose an EPC. Store the working config and exact build/launch
commands once reproduced. A narrower legacy LTE bandwidth does not enable
Cat-M1, and these srsRAN configs must not be presented as Walter-ready.

Acceptance sequence:

1. Walter discovers a cell advertising Cat-M1 support.
2. Random access and RRC connection complete.
3. SIM authentication and registration succeed.
4. A conventional IP bearer is established and Walter receives an address.
5. Sequenced UDP telemetry reaches the ground receiver.
6. Reset/reconnect tests reproduce the same result.

Record versions, payload/rate/duration, loss, RTT, signal metrics, and recovery
behavior. Label historical, newly measured, and simulated evidence separately.
