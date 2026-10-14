# circuit-dx

**Working title:** *Does the Tester Matter? Measurement Hardware Effects on ML-Based Analog Circuit Fault Diagnosis*

An independent undergraduate research project by Stav Shaham (Software Engineering, Embry-Riddle Aeronautical University, Prescott).

> **Status:** 🟡 Setup — Weeks 1–2 (repository, inventory, board bring-up)

---

## Overview

When an analog circuit misbehaves, which component is to blame? This project trains machine-learning models to identify the faulty component in small analog filter circuits from their measured frequency response, and asks how much the **measurement hardware** affects how well that works.

Models are trained mainly on **SPICE simulations** (ngspice) with injected faults and realistic component tolerances, then tested on **real breadboard circuits** measured by three low-cost microcontrollers: an ESP32, a Raspberry Pi Pico 2 W and an Arduino Nano. All three measure the same signal at the same moment, so differences in accuracy come from the hardware, not the circuit.

## Research questions

| # | Question |
|---|---|
| **RQ1** | **Sim-to-real gap:** How much accuracy does a simulation-trained model lose on real measurements, for each board? |
| **RQ2** | **Bits vs. quality:** How do ADC resolution and noise affect diagnosis accuracy, and which faults are affected first? |
| **RQ3** | **Cross-device transfer:** Does a model trained on one board's data work on another's? Does calibration fix it? |
| **RQ4** | **Deployment:** Which models fit and run on each microcontroller, and how fast? |

## Hardware

| Board | Chip | ADC | DAC | Role |
|---|---|---|---|---|
| ESP32 devboard (ELEGOO, CP2102) | ESP32, Xtensa 240 MHz | 12-bit (noisy, nonlinear) | ✅ 8-bit (GPIO25/26) | **DAC** generates the test signal; **ADC** measures like the others (device A) |
| Raspberry Pi Pico 2 W | RP2350, Cortex-M33 150 MHz | 12-bit | ❌ | Measurement device B |
| Arduino Nano (CH340) | ATmega328P, 16 MHz | 10-bit | ❌ | Measurement device C |

**Why these three:** the ESP32 and Pico are both 12-bit but differ in noise and linearity (this isolates **ADC quality**); the Pico and Nano are both relatively clean but differ in resolution (this isolates **bits**).

Everything else is from starter kits: resistors, ceramic 100 nF ("104") capacitors, potentiometers, breadboards, jumper wires and a multimeter. **No budget required.**

## Circuits

### Circuit 1: Two-stage RC low-pass filter

```
ESP32 DAC ──[1k protect]──[R1]──┬──[R2]──┬──→ ESP32 ADC (GPIO34)
                                C1       C2 ├─→ Pico ADC  (GP26)
                                │        │  └─→ Nano A0
GND ────────────────────────────┴────────┴── all boards' GND connected
```

| Part | Value |
|---|---|
| R1, R2 | 10 kΩ |
| C1, C2 | 100 nF ceramic (104) |
| Protection resistor | 1 kΩ (never faulted; included in the netlist) |
| Cutoff | ~160 Hz per stage |
| Sweep | 10 Hz – 1.5 kHz, 5 kHz sampling on all boards |

Reference transfer function (R₁ includes the 1 kΩ protection resistor):

```
                                 1
H(s) = ───────────────────────────────────────────────────
        1 + s·(R1·C1 + R1·C2 + R2·C2) + s²·(R1·R2·C1·C2)
```

Evaluate at s = jω (ω = 2πf); the measured gain is |H(jω)|.

### Circuit 2: Passive band-pass filter (after Circuit 1 works)

High-pass (100 nF + 10 kΩ biased to 1.65 V) followed by low-pass (2 kΩ + 100 nF), for a passband of roughly **160–800 Hz**. The 1.65 V bias comes from a 10 kΩ/10 kΩ divider steadied by a 10 µF electrolytic capacitor.

### Fault model

Each faultable component (R1, R2, C1, C2) gets four fault types, giving **16 fault classes + healthy**:

| Fault | How it's built |
|---|---|
| Small drift (+10%) | 10 kΩ + 1 kΩ in series (or a potentiometer) |
| Medium drift (+20%) | 10 kΩ + 2 kΩ in series |
| Large drift (−50% / +100%) | Two parts in parallel / in series |
| Open | Component removed |
| Short | Jumper across the component |

Some faults look identical (e.g., C2 short vs. R2 open). These **ambiguity groups** are identified from simulation and reported, not treated as errors.

## Method

1. **Simulate** circuits in ngspice with random tolerances (±5–10%) and injected faults → simulated dataset.
2. **Measure** real circuits: the ESP32 generates a sine sweep, and all three boards compute per-frequency amplitudes on-board with the same Goertzel code.
3. **Train** models (random forest, SVM, decision tree, small neural network) on gain-per-frequency features.
4. **Evaluate** sim-to-real accuracy, cross-device transfer, and a virtual sweep over ADC resolution and noise.
5. **Deploy** models to the boards via emlearn and measure accuracy, memory and latency.

### Fair-comparison rules

- Identical algorithm (shared Goertzel library) on all boards
- Identical, timer-driven sample rate (5 kHz) on all boards
- All boards measure the same sweep simultaneously, triggered by an ESP32 sync pulse
- All three ADC inputs stay connected for every session, so the circuit's loading never changes

## Repository structure

```
circuit-dx/
├── README.md
├── logs/               research log: one file per work session, named by date
│   ├── _TEMPLATE.md    copy this to start a new day's log
│   └── 2026-10-14.md   e.g., YYYY-MM-DD.md
├── parts.csv           every labelled physical part (nominal + measured value)
├── circuits/           SPICE netlists, KiCad schematics, breadboard photos
├── firmware/           PlatformIO project: [env:esp32dev] [env:nano] [env:pico2w]
│   ├── lib/goertzel/   shared measurement code used by all boards
│   └── src/
├── sim/                fault injection, tolerance sampling, ngspice runs
├── data/
│   ├── sim/            generated (reproducible from code)
│   └── real/           measured: esp32/ pico2w/ nano/
├── ml/                 training, evaluation, degrade.py (virtual ADCs)
├── results/            figures and tables, tagged per experiment
└── paper/              write-up / poster
```

## Research log

Every work session gets its own file in `logs/`, named by date (`logs/YYYY-MM-DD.md`). Copy `logs/_TEMPLATE.md` to start a new one. If you work twice in one day, add a second section to the same file rather than creating a new one.

Each log records what was done, what was measured (with exact part labels), what surprised you, and what's next. Together they are the lab notebook behind the paper's methods section.

Commit each log with the work it describes, e.g., `docs(logs): 2026-10-14 — repo setup and research questions`.

## Tools

All free.

| Area | Tools |
|---|---|
| Firmware | CLion + PlatformIO; Pico C SDK (CMake) as fallback for the Pico 2 W |
| Simulation | ngspice, PySpice, LTspice (visual checks) |
| ML & analysis | Python, NumPy, pandas, scikit-learn, PyTorch (CPU), Plotly, PyCharm |
| Deployment | emlearn |
| Data logging | pyserial |
| Schematics | KiCad |
| Drivers | CP2102 (ESP32), CH340 (Nano) |

## Timeline (spring + summer 2027)

| Phase | Weeks | Work |
|---|---|---|
| **Core** | 1–2 | Inventory, part measurements, build Circuit 1, reference curve |
| | 3–5 | Shared Goertzel library + ESP32 sweep firmware; verify against theory |
| | 6–7 | SPICE pipeline + simulated dataset |
| | 8–10 | Real ESP32 data; RQ1 |
| **Extension A** | 11–12 | Nano firmware, three-board wiring, sync |
| | 13–14 | Pico 2 W firmware |
| | 15–17 | Three-board sessions; RQ2 + RQ3; virtual degradation sweep |
| **Extension B** | 18–20 | On-device deployment; RQ4 |
| **Write-up** | 21–23 | Paper or poster, public release |

The core alone is a complete study; extensions are added as time allows.

## Git workflow

- **Branching:** `main` always works. Use short-lived branches such as `feat/goertzel-firmware`, `feat/fault-injection` and `exp/rq2-resolution-sweep`.
- **Conventional commits**, scoped by area and board:
  - `feat(fw/esp32): add DAC sine sweep 10Hz–1.5kHz`
  - `fix(fw/nano): set EXTERNAL reference before first analogRead`
  - `hw(circuit1): add 1k protection resistor at DAC output`
  - `data(real): session 07 — C1 +100% drift, 10 sweeps, all boards`
  - `exp(rq1): sim-only model evaluated on real set`
- **Atomicity:** one commit per measurement session. Real data can't be regenerated, so each session records the fault, the exact labelled parts used, and which boards measured.
- **Tags:** tag every verified firmware milestone (`fw-v0.1-esp32-verified`) and every result set used in the paper (`results-rq1-v1`), so every figure can be reproduced exactly.

## Safety notes

- Everything runs at 3.3 V from USB. **Never connect the adjustable bench power supply to the boards.**
- The Nano is a 5 V board: send signals **only from the ESP32 to the Nano**, never the other way.
- Call `analogReference(EXTERNAL)` on the Nano **before** any `analogRead()` when AREF is connected.
- Only short across passive components, never across the power rails.

## License

To be decided before public release (MIT suggested for code, CC BY 4.0 for data).
