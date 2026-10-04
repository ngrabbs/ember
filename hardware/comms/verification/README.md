# Comms verification records

[Comms home](../README.md) · [Open work](../TODO.md)

These are **dated checks with a defined scope**, not automatic approval of the
current working tree. Retained evidence covers component identities, meaningful
layout/connectivity checks, and unresolved acceptance questions. Intermediate
repair logs are available in Git history.

## Latest recorded state

Latest: [top-ground stitching and RF impedance review](ground_stitching_rf_review.md).
100 new GND vias verified on three ground layers; DRC remains 0 errors /
0 unconnected / 1 warning. RF impedance acceptance has the explicit open
items recorded in that review.

[Power-plane cleanup and DRC evidence](evidence/power_plane_cleanup_2026-10-03.json).

The October 3 saved PCB has **0 non-excluded DRC errors, 0 unconnected items,
and 1 warning**: the fixed H1/H2 silkscreen-outline overlap. Five specific
PC/104 courtyard exclusions are restored; no header or mounting-hole position
was changed. The user's restored In2.Cu +3V3 plane now replaces approximately
193 mm of redundant outer-layer power routing. Local supply connections remain.
CLK0 trace width/clearance and remaining power-via spacing findings are fixed.

All 209 native schematic nets (551 nodes) match the PCB pad assignments with
zero mismatches. The fresh DRC separately checks routed continuity. The GUI
initially showed four cached mounting-hole library differences absent from the
fresh saved-board check; these were not globally ignored.

[Hardware TX mute and open checks](tx_startup_inhibit_review.md).
The latest RF corridor screen found a return-corridor edge intrusion near
TRIPLER_OUT, in addition to the antenna launch. It is not impedance or RF
qualification. Final electrical, RF, parts/mechanics
and manufacturing acceptance remain open. This is **not fabrication approval**.

## Component and connector audits

| Scope | Record |
|---|---|
| PSA4, Hottech transistors, XOR, capacitors, op amp | [Component mapping record](components/rf_pinmap_audit.md) |
| ADL5602 U8 | [U8 audit](components/u8_adl5602_pinmap.md) |
| ADE-1+ U10 | [U10 audit](components/u10_ade1_pinmap.md) |
| RF switch/supply/buffer | [Switch audit](components/rf_switch_pinmap.md) |
| D15 currently recorded package | [Antenna protection audit](components/antenna_esd_pinmap.md) |
| L16 prototype footprint | [L16 acceptance scope](components/l16_footprint_acceptance.md), [choke review](components/l16_choke_review.md) |
| Stack socket positions and logical numbering | [CSKB alignment](components/cskb_alignment_verification.md) |

The older [Samtec mating-face audit](components/samtec_pad_audit.md) is background;
its numbering and J6/J7 socket selection were superseded for these board instances.
Use the later alignment record and preserve J6/J7/J8 as DNP pin headers.

- [J9 drawing, RF exceptions and proposed fabrication requirements](j9_launch_and_fabrication_requirements.md) — October 3, 2026.
