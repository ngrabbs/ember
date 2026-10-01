---
title: ""
---

```{=latex}
\renewcommand{\dsproject}{EMBER}
\renewcommand{\dssubtitle}{Communications Board}
\renewcommand{\dsrevision}{rev A}
\renewcommand{\dstagline}{1U CubeSat Comms Board --- 437 MHz BPSK Downlink, 145.9 MHz FM-AFSK Uplink, RP2040-Controlled}
\renewcommand{\dsorg}{MSU CubeSat -- EMBER}
\renewcommand{\dsdocrev}{Document Rev 0.1}
\renewcommand{\dsdate}{May 2026}
\renewcommand{\dslogo}{logo_dark.png}
% Override the dark-band title bar with the plain light version for this variant
\renewcommand{\datasheettitle}{%
  \noindent
  \begin{minipage}[c]{0.135\textwidth}
    \ifdefempty{\dslogo}{%
      \rule{0pt}{1em}%
    }{%
      \includegraphics[width=\linewidth,keepaspectratio]{\dslogo}%
    }%
  \end{minipage}%
  \hfill
  \begin{minipage}[c]{0.82\textwidth}
    \raggedleft
    {\Huge\bfseries\sffamily \dsproject}\\[0.15em]
    {\LARGE\sffamily \dssubtitle}\\[0.25em]
    {\sffamily\normalsize Hardware Revision: \dsrevision}
  \end{minipage}\\[0.5em]
  \noindent\rule{\textwidth}{0.8pt}\\[0.3em]
  \begin{center}\bfseries\sffamily\large \dstagline\end{center}
  \vspace{0.2em}%
}
\datasheettitle
\dsbegin
```

## Applications

- EMBER 1U--3U CubeSat platform (MSU senior capstone)
- University / educational CubeSat narrow-band telemetry and command
- AMSAT-style amateur-satellite VHF/UHF inverse-band comms

## Features

### Topology

- **70 cm BPSK downlink** / **2 m FM-AFSK uplink**, half-duplex
- Single Si5351A drives TX carrier (CLK0) and RX local oscillator (CLK1)
- RP2040 (Pico module) handles mod/demod and IHU SPI link
- Separate TX/RX SMA antennas (no diplexer)

### Electrical

- **TX:** 437 MHz BPSK, **+13 dBm** typ output
- TX chain: 74LVC1G86 XOR mod (145.67 MHz) → BFR92A tripler → 3-pole BPF → ADL5602 MMIC (+20 dB) → output BPF
- **RX:** 145.9 MHz FM-AFSK (1200/2200 Hz), **~1 dB system NF**
- RX chain: 2m BPF → PSA4-5043+ LNA → ADE-1+ passive mixer → Sallen-Key LPF (3.3 kHz) → MCP6022 → RP2040 ADC
- 5-pole LC LPF on LO line suppresses LO 3rd-harmonic at 437 MHz (~34 dB)

### SWaP

- CSKB stack-bus form factor (~96 × 90 mm), single board
- Mass < 80 g (estimated)
- **+3 V3 ~150 mA + +5 V ~140 mA ≈ 1.2 W** (RX active)

### Environment

- Operating temperature **−20 °C to +60 °C** (preliminary)
- 4-layer FR-4 (JLCPCB JLC04161H-7628), 1.6 mm
- 50 Ω microstrip (0.358 mm) on L1 referenced to L2 GND plane

```{=latex}
\columnbreak
```

```{=latex}
\begin{center}
\includegraphics[width=0.95\linewidth,keepaspectratio]{board.png}
\end{center}
\vspace{0.3em}
```

### Project Information

```{=latex}
\begin{tabular}{@{}p{0.32\linewidth}p{0.60\linewidth}@{}}
\hline
\bfseries Field & \bfseries Value \\
\hline
Project           & EMBER Comms \\
Schematic rev     & 1.3 \\
Board rev         & Rev A (in layout) \\
Repository        & \path{github.com/ngrabbs/ember} \\
Owner             & MSU CubeSat (capstone) \\
\hline
\end{tabular}
```

```{=latex}
\begin{dscallout}[BRING-UP STATUS]
\sffamily\small
Schematic complete (Rev 1.3); 4-layer PCB in layout. Si5351A clock
path verified on Adafruit breakout + Pico 2. RX front-end (PSA4 LNA
+ ADE-1+ mixer) replaces original SA612 due to EOL --- see
\path{design/rx_mixer_trade_study.md}. \textbf{Not flight-qualified.}
\end{dscallout}
```

### Protection \& Safety

- Reverse-polarity D4 + VSYS isolation D5 on +5 V / Pico inputs
- 2 m BPF protects LNA/mixer from 437 MHz self-TX (>40 dB)
- 5-pole LO LPF suppresses LO harmonics into the mixer
- 51 Ω IF port termination on ADE-1+
- Si5351A outputs disabled at boot --- TX off by default

### Interface

- CSKB H1/H2 stack-bus (2× Samtec ESQ-126-39-G-D)
- SPI0 (slave) + I\textsuperscript{2}C0 + IRQ to IHU via CSKB H1
- TX (J4) and RX (J5) on **MMCX in-board** connectors
- SWD debug header (J2, optional)

```{=latex}
\dsend
```
