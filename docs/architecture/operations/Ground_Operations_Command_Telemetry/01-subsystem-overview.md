# Ground Operations & Test - Subsystem Overview

**Status:** Draft 0.2

## Purpose

Provides the operator interface used to monitor, command, and test EMBER while supporting autonomous spacecraft operation and event-driven reporting.

EMBER is intended to operate autonomously during normal mission operations. Ground Operations does not continuously command the spacecraft to perform its mission. Instead, EMBER automatically performs scheduled mission activities, monitors system health, generates telemetry, and reports significant events such as fire detections and faults.

Ground Operations provides the operator with spacecraft status, alerts, telemetry, and event information while retaining the ability to issue commands when manual control, testing, configuration, recovery, or on-demand information is required.

## Primary Responsibilities

- Ground operator console
- Spacecraft monitoring and status display
- Event and alert display
- Command generation
- On-demand status and telemetry requests
- Telemetry and event decoding
- Command, telemetry, and event logging
- Command dictionary
- Telemetry and event dictionary
- Ground test connection
- Ground operations and test procedures

## Working Architecture

```text
                    EMBER
                      |
        Autonomous Mission Operation
                      |
       +--------------+--------------+
       |              |              |
     Payload          IHU            EPS
       |              |              |
       +------ Status / Events -------+
                      |
                      v
              Flight Communications
                      |
                   RF Link
                      |
              Ground Radio / Modem
                      |
                      v
          Ground Operations Console
                      |
              Operator Monitoring
              Alerts / Logging
              Manual Commands
