# Commanded payload fire check

**IHU0.13.0 / bridge0.4.0:** [quiet-output policy](../../docs/architecture/operations/04-ihu-runtime-policy.md).
Fire-check command replies remain available with all six streams OFF. Existing
0.12.0 OTA evidence below remains historical;0.13.0 has not been deployed.

Versions: IHU0.12.0, payload0.2.0, COMMS0.31.0, serial bridge0.3.0,
RF command bridge0.1.0; ground release1.6.0. This release uses an explicit
STATIC_STUB returning NO_FIRE. The camera/detection algorithm does not run.

Select PAYLOAD_FIRE_CHECK in the instance's realtime command page. Inspect
command history and Payload.opi: result, execution mode, reception timestamp,
and Payload.par for correlated transaction, payload boot and check_id.
No response or invalid data means UNKNOWN, never NO_FIRE. Results remain
historical observations; their timestamps matter. Both FIRE and NO_FIRE are
valid wire results, with explicit stub versus algorithm provenance.

Bench: Yamcs ember-bench → UDP10028 → m75q single-owner IHU console →
CAN0x740/0x741 → payload. Admission and final result are correlated separately.

Flight: Yamcs ember → UDP10029 on ground Pi → LibreSDR DBPSK uplink →
COMMS finite A window → CAN0x730/0x731 → IHU → payload CAN0x740/0x741.
COMMS returns the validated native IHU result in one DBPSK downlink;
LibreSDR decodes original bytes and forwards only the unique matching result
into flight UDP10019. USB is used to arm COMMS's bounded receive/reply window;
it carries neither the fire command nor its result. This is a bench-controlled
RF transaction, not an autonomous always-listening flight receiver.

The ground Pi's ember-fire-uplink service owns LibreSDR only during a command.
Do not run another radio owner concurrently. m75q ember-fire-arm owns only the
COMMS USB port during the finite window. ember-bench-bridge remains the sole
IHU serial owner. Services transmit nothing at boot. Each command permits one
burst at the previously measured OTA settings (434.99455MHz uplink,437MHz
downlink, gain70, amplitude0.20) and one finite capture. No application retries.
COMMS bounds its window to20s and at most one response. A missing result times
out after40s in Yamcs. Duplicate suppression lasts one service/MCU boot and is
not authentication or persistent replay protection. IHU/COMMS cache capacity
is16 accepted RF transactions per boot, then fails closed.

Before deployment preserve source, active service files, firmware flash backups,
Yamcs runtime/config/environment and the stopped archive volume. Use a clean
committed source identity for firmware exports. Rebuild IHU and COMMS separately;
never confuse the LTE Feather's historical filename with COMMS. Install the
payload runtime on .253, ground/ember plus fire-arm on .252, and ground/ember,
ground/bpsk plus fire-uplink on .251. Run prepare_operational.py against the
existing runtime, rebuild Java, install both display buckets and audit each
instance as release1.6.0. Preserve archive volumes and the previous manifests.
Stop RF/arming services before manually accessing their radio or COMMS port.

## Verified deployment

The October17 validation passed four Yamcs bench commands and two independent
Yamcs RF commands. The two RF result packets are byte-identical at COMMS,
ground decoding and the flight archive. All returned NO_FIRE/STATIC_STUB.
The initial failed trials are preserved with the timing/admission fixes in
[validation evidence](../../system/ground_station/evidence/fire-check-20261017/validation.json).
Services are enabled and idle after testing; COMMS TX/RX are off, clocks disabled.
Firmware exports report clean identities; final MCU SHAs and rollback locations
are retained in that evidence. Both1.6.0 ground manifests pass MATCH.
