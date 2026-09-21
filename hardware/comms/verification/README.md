# Comms verification records

[Comms home](../README.md) · [Open work](../TODO.md)

These are **dated checks with a defined scope**, not automatic approval of the
current working tree. Retained evidence covers component identities, meaningful
layout/connectivity checks, and unresolved acceptance questions. Intermediate
repair logs are available in Git history.

## Latest recorded state

The latest ordering-field pass records **0 DRC errors, 1 existing header-silkscreen
warning, 0 unconnected items**. The earlier RF review checked 181 native nets
against the PCB. Native ERC exclusions and the header courtyard exception remain
part of those records. RF performance, physical fit, and final sourcing remain open.
No checks were rerun during documentation cleanup.

- [RF review and warning disposition](rf_review_435mhz.md)
- [Baseband bias/filter and header exception](baseband_and_header_review.md)
- [Latest ordering-field validation](../bom/evidence/remaining_field_completion.md)
- [Numerical RF review evidence](evidence/rf_review_validation.json)

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
