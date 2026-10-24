# IHU demo 0.1.0 — hardware-test candidate

Download [ihu_demo.uf2](ihu_demo.uf2) with GitHub’s **Download raw file** button.
Do not save the GitHub HTML preview as a UF2. This is for the original non-wireless
RP2040 Pico/Pico H; it is not the CAN Feather firmware.

Follow the [installation and demo walkthrough](../../../../docs/user/ihu-pico-demo.md).
The UF2 was built from clean source commit
`0ef4637d04fcde414c456777acd0cd58697cb903`. Later packaging/docs commits do not change
its embedded source identity. [Build manifest](manifest.json) and
[SHA-256 checksum](SHA256SUMS) identify this exact candidate.

Build and host tests passed. Austin can flash this candidate to perform the
physical USB/GPIO and repeated-demo checklist in the guide. Hardware acceptance
is still pending; this is not a flight image or a hardware-qualified release.
