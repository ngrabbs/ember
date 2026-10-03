# Ground software

[System guide](../system/README.md) · [Ground station checklist](../system/ground_station/TODO.md)

- [Telemetry data flow](../docs/architecture/telemetry_data_flow.md): shared team reading, battery voltage/current walkthroughs, and definition ownership.
- [LTE-M telemetry bench](lte/README.md): Walter UE, LibreSDR/eNodeB inventory,
  recovered LTE configs, bring-up runbook, and spacecraft-channel checklist.
- [EMBER bench dictionary](ember/README.md): JSON definitions, host codec and
  wire vectors, generated MDB, simulator and verified Pico USB endpoint.
- [Yamcs ground lab](yamcs/README.md): EMBER command/telemetry loop and the
  preserved upstream reference, with reproducible software checks.
- [Pi preparation](../system/ground_station/pi_setup.md): OS and first-boot settings.
- [Dustin coordination](../system/ground_station/dustin_followup.md): remaining
  operations definitions and shared protocol decisions.

Application command and telemetry meanings come from the
[operations dictionaries](../docs/architecture/operations/Ground_Operations_Command_Telemetry/README.md).
The radio bridge and waveform implementation will carry that shared interface.
