---
title: ""
---

```{=latex}
\renewcommand{\dsproject}{EMBER}
\renewcommand{\dssubtitle}{Electrical Power System (EPS)}
\renewcommand{\dsrevision}{rev A}
\renewcommand{\dstagline}{CubeSat Electrical Power System with MPPT Solar Charging and I\textsuperscript{2}C Telemetry}
\renewcommand{\dsorg}{MSU CubeSat -- EMBER}
\renewcommand{\dsdocrev}{Document Rev 0.1}
\renewcommand{\dsdate}{May 2026}
\renewcommand{\dslogo}{logo.png}
\datasheettitle
\dsbegin
```

## Applications

- EMBER 1U–3U CubeSat platform (MSU senior capstone)
- University and educational CubeSat power systems
- General-purpose Li-ion + MPPT solar bench development platforms

## Features

### Topology

- Body-mounted **4S solar array** input — 4× SM141K10TF modules per face, 4 faces parallel
- **2S2P LG INR18650 MJ1** Li-ion battery pack (7.0 Ah / 50.4 Wh nameplate)
- **7.27 V nominal** battery bus (8.4 V max, 5.0 V min)
- Two independent synchronous-buck rails: **+5 V** and **+3.3 V**

### Electrical

- **LTC4162-L** Multi-Cell MPPT Li-ion Step-Down Charger
  - Up to **3.2 A** charge current
  - **35 V** absolute max input
  - I\textsuperscript{2}C telemetry: V\textsubscript{IN}, V\textsubscript{BAT}, I\textsubscript{CHG}, T\textsubscript{BAT}, SoC, state register
- **TPS62933F** synchronous bucks (×2, one per output rail)
  - **3.8–30 V** input range, up to **3 A** continuous
  - Per-rail EN/UVLO programmable via resistor divider
  - 200 kHz – 2.2 MHz programmable switching
- Solar Voc up to ~28 V (4S cold), Vmp ~22 V — full margin to LTC4162 35 V ceiling
- Schottky-OR'd solar inputs (per-panel STPS1L30MF blocking + per-cell-array bypass)

### SWaP

- **PC/104-compatible CSKB stack-bus** form factor (~96 × 90 mm)
- Single-board EPS — no daughter cards required
- Mass: < 100 g (estimated, final TBD)
- Stack-bus integration via H1/H2 headers per the CSKB pinmap

### Environment

- Operating temperature: **−20 °C to +60 °C** (preliminary)
- Battery charge-disable below 0 °C via LTC4162 NTC (planned)
- 1 oz copper, FR-4, 4-layer (controlled-impedance candidate)
- 6 V/m EMC margin (preliminary, TBD on full chamber sweep)

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
Project           & EMBER EPS \\
Current revision  & Rev A (prototype, on bench) \\
Next revision     & Rev B (in design) \\
Repository        & \path{github.com/ngrabbs/ember} \\
Owner             & MSU CubeSat (capstone) \\
\hline
\end{tabular}
```

```{=latex}
\begin{dscallout}[BRING-UP STATUS]
\sffamily\small
Rev A is in active bench bring-up. LTC4162 charge path verified;
TPS62933F rail bring-up in progress (see \path{phase1_validation.md}).
\textbf{Not flight-qualified.}
\end{dscallout}
```

### Protection \& Safety

- **Remove-Before-Flight (RBF)** jumper for hard system inhibit
- LTC4162 NTC-based over/under-temperature charge inhibit
- Schottky blocking diodes prevent panel reverse current at night
- Per-cell-array bypass diodes on each panel string
- Charger-centric battery protection (independent BMS deferred)
- Soft-start on both bucks (33 nF C\textsubscript{SS}, ~5 ms ramp)

### Interface

- **CSKB stack-bus** (H1/H2) — locked per the CSKB pinmap
- **I\textsuperscript{2}C** to internal housekeeping unit (IHU) — charger telemetry
- **+5 V**, **+3.3 V** rails distributed on stack-bus
- Battery bus and GND on stack-bus
- Solar panel headers (5-pin, one per face) — dedicated, off-stack

```{=latex}
\dsend
```
