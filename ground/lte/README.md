# Walter LTE-M operator runbook

Use this with the [ground demo checklist](../README.md#receive-lte). Run one
radio session at a time on the shared LibreSDR. On the Pi, check
`systemctl status ember-lte-listener`; the listener owns UDP 51000 and forwards
valid packets to Yamcs.

## Start the cell

Use the staged lab setup in `~/work/ember-lte`. For a fresh installation or
an alternate profile, follow the [engineering setup](diagnostics/BRINGUP.md#5-bring-up-lte-m)
and [inventory](INVENTORY.md). With LibreSDR free and the bench RF setup ready,
start the EPC, then the eNodeB in a second Pi terminal:

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

## Receive and stop

1. Once the cell is up, follow the [Walter bench check](../../firmware/walter/README.md#how-lte-telemetry-reaches-yamcs)
   to open a window, confirm registration and READY, and send `eps lte`.
2. In Yamcs **ember / realtime**, check **lte-tm-in** and look for a fresh
   `POWER_STATUS` in **Telemetry → Packets**. The Pi receiver log is
   `/var/lib/ember-lte-listener/packets.jsonl`.
3. Close the IHU window with `lte 0`, switch `lte_telem` off if you enabled
   it, then stop the eNodeB and EPC. Verify both cell processes exited.

[Engineering diagnostics](diagnostics/README.md) · [Open work](TODO.md)
