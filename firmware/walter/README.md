# Walter LTE-M firmware

Reserved for the spacecraft-side Walter application. No application source has
been imported or developed here yet. The attached board currently runs a modem
AT passthrough application whose source/build provenance is not yet located.

Bench procedures and the implementation checklist live in
[ground/lte](../../ground/lte/README.md).

When development begins, record the ESP32 toolchain, WalterModem library commit,
modem firmware, build/flash procedure, and power/reset behavior. Start with
sequenced UDP telemetry and reconnect handling, then integrate the shared EMBER
telemetry definitions. Keep SIM credentials and builds outside tracked source.
