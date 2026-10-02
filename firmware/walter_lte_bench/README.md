# Walter native EPS LTE bench sender

Experimental standalone application using the same pinned PlatformIO 6.1.18,
espressif32 6.10.0 / Arduino 2.0.17 toolchain as the UART responder. Uses local
nonblocking AT orchestration, not the WalterModem library. Generated wire offsets
come from `ground/ember/dictionary.json`; preserve the repository directory layout.
Build passed; hardware upload, modem bring-up and LTE delivery remain pending.

COMMS UART0: Walter RX44/TX43, 115200 8N1. Modem UART1: RX14/TX48,
CTS47/RTS21, hardware flow control. GPIO45 active-low reset holds the modem off
at startup and at each RF-window deadline/error. An explicit framed request is
required to release reset. Pin functions checked against the
[pinned QuickSpot example](https://github.com/QuickSpot/walter-arduino/blob/c30b707f8d64b49daec80de6bccfc80c04e42d58/examples/passthrough/passthrough.ino)
and installed Arduino HardwareSerial API; vendor source is not incorporated.

This is a lab Band 13 / `srsapn` application using the modem's existing operator
selection and LTE-M configuration. It does not infer SIM identity or switch RAT.
Socket1 UDP destination `172.16.0.1:51000`, local port51001. AT commands follow
the previously exercised Sequans UE8.2.1.0 bench helper. Band/APN configuration
is written on each start; reset-off ends RF but does not restore those settings.
Original flash backup remains available per UART bench recovery instructions.

One admitted RF window, maximum120 seconds; repeated enable while active is
rejected and does not extend the deadline. Startup waits12 seconds, then configures
the modem, polls registration every3 seconds and opens the UDP socket. AT responses
are bounded2048 bytes. AT setup timeout6 seconds, socket/send timeout15 seconds.
Any timeout/overflow/setup error asserts modem reset; a pending packet outcome is
UNKNOWN. A send needs at least16 seconds remaining. One packet at a time; there is
no retransmission after rejection, timeout or uncertain outcome.

UART service types in `../comms_transport/lte_link.h`:

| Request / reply | Meaning |
|---|---|
| `0x10` / `0x11` | Four-byte big-endian RF-window seconds (0 stops); ACK is admission, not registration |
| `0x12` / `0x13` | Complete native telemetry packet; reply preserves exact bytes after modem final OK |
| `0x14` / `0x15` | Empty status query; 16-byte modem status |

HELLO establishes COMMS boot identity. Requests require matching sender, origin,
version and nonzero request ID. Native telemetry validates EMBER header, length,
source/target and CRC independently. Diagnostic ECHO remains available with the
radio off. `MODEM_ACCEPTED` means prompt, payload write and final OK; it never
means received by the ground station. The receiver and Yamcs archive supply that
proof separately. No uplink/flight-command service is implemented.

Status bytes: state, configuration step, last error, registered; then u32 RF
milliseconds remaining, modem-accepted count, rejection count, all big endian.
States0–7: OFF, BOOT_WAIT, CONFIGURE, REGISTER, SOCKET_CONFIG, SOCKET_OPEN,
READY, SEND (READY=6, SEND=7).
Errors0none/1modem rejection/2window deadline/3response overflow/4AT timeout.
Registration is the last successful CEREG query, not continuous radio health.
USB accepts `status` and `off`; raw modem responses/SIM details are not printed.

The host mock tests prompt/payload/final-OK correlation, BUSY, bounded windows,
setup timeout, packet timeout and NOT_READY. These do not qualify the modem or RF.

On m75q:

```sh
env PLATFORMIO_CORE_DIR=/media/ngrabbs/BACKUP-A/ember-walter-bridge/pio \
  TMPDIR=/media/ngrabbs/BACKUP-A/ember-walter-bridge/tmp \
  /media/ngrabbs/BACKUP-A/ember-walter-bridge/venv/bin/pio run \
  -d /media/ngrabbs/BACKUP-A/ember-walter-bridge/lte-work/firmware/walter_lte_bench
```

Upload with `-t upload --upload-port` and Walter's verified serial-by-id path
when its USB cable is connected. Do not target a Feather serial device.
