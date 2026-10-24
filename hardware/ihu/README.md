# Internal Housekeeping Unit Hardware

## Purpose

This directory tracks internal housekeeping unit architecture, board interfaces, and
bring-up validation for the system controller. The new PCB direction is STM32G0B1
with dual native CAN; existing Pico/Feather applications remain bench/test images.

## Architecture Snapshot

- New PCB MCU family: **STM32G0B1**, exact package pending pin/memory review
- Ground/demo GNSS: **ATGM336H-5N31**; flight suitability remains open
- Primary role: command authority, mode management, and telemetry aggregation
- Implemented FreeRTOS prototype: I2C EPS reads, jumper I2C comms status/ping, UART CLI
- Separate CAN Feather bench: single-bus packet transport and native EPS telemetry
- Intended production packet transport: dual native CAN controllers plus separate CAN A/B transceivers; STM32 port and failover remain open
- SPI: older board allocation; packet firmware is not implemented

## Documentation Map

- **Start here for PCB design:** [Hardware requirements and electrical interface specification](design/hardware_requirements.md) — decided/proposed/open matrix, supply/drive contracts and freeze gates
- Architecture and rationale: [`hardware/ihu/design/overview.md`](design/overview.md)
- Electrical and logical interfaces: [`hardware/ihu/design/interfaces.md`](design/interfaces.md)
- Bring-up and acceptance criteria: [`hardware/ihu/bringup/phase1_validation.md`](bringup/phase1_validation.md)

## Status Summary

- Decided: STM32 dual-native-CAN family direction and ATGM336H-5N31 for ground/demo
- Draft design specification: [requirements, electrical interfaces and open decisions](design/hardware_requirements.md)
- In progress: detailed interface closure, boot/runtime behavior, and bring-up plan
- Open items: pin-map freeze, watchdog policy, safe-mode entry/exit behavior

## Layout

- `design/`: architecture and design notes
- `kicad/`: PCB design source files
- `bringup/`: bring-up plans and bench notes
- `releases/`: fabrication and release artifacts
