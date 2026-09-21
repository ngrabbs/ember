# Receiver mixer decision

[Design guide](README.md) · [Current RX chain](rx_chain.md)

**Decision record:** ADE-1+ replaced the earlier SA612 approach. The radio later
moved from VHF RX to 435 MHz RX on the shared UHF antenna. The original detailed
trade study is retained in Git history.

The current design uses a passive mixer with an LNA ahead of it and a baseband
amplifier afterward. That makes LO drive, conversion loss, receiver noise, and
mixer input headroom joint design constraints. Earlier VHF filter comparisons and
noise estimates are not acceptance results for the present receiver.

- [ADE-1+ physical package audit](../verification/components/u10_ade1_pinmap.md)
- [Mixer headroom with the proposed U9 replacement](analysis/u9_mixer_headroom.md)
- [RX qualification plan](../bringup/rx_test_plan.md)

The +7 dBm LO requirement and actual loaded receiver response must be checked
on the assembled board. A different LNA is not approved solely because it fits
the band or has more gain.
