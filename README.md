# circuit-dx

**Does the Tester Matter? Measurement Hardware Effects on ML-Based Analog Circuit Fault Diagnosis**

Stav Shaham · Department of Software Engineering, Embry-Riddle Aeronautical University, Prescott, AZ

**Status:** In progress — experimental setup

---

## Abstract

Machine-learning approaches to analog circuit fault diagnosis are typically developed and evaluated on simulated data or on laboratory-grade instruments. In practice, low-cost test equipment often relies on microcontroller-based data acquisition, whose analog-to-digital converters differ substantially in resolution, noise and linearity. This project investigates how these measurement-hardware characteristics affect diagnostic accuracy.

Classifiers are trained primarily on SPICE simulations with injected component faults and realistic tolerances, then evaluated on physical circuits measured simultaneously by three low-cost microcontrollers: an ESP32, a Raspberry Pi Pico 2 W and an Arduino Nano. Because all three devices sample the same stimulus at the same time, observed differences in accuracy can be attributed to the measurement hardware rather than to the circuit under test.

## Research Questions

| ID | Question |
|---|---|
| **RQ1** | **Simulation-to-reality gap:** How much diagnostic accuracy does a simulation-trained model lose when applied to physical measurements from each device? |
| **RQ2** | **Resolution versus quality:** How do ADC resolution and noise affect diagnostic accuracy, and which fault types degrade first? |
| **RQ3** | **Cross-device transfer:** Does a model trained on one device's measurements generalize to another's, and can calibration close the gap? |
| **RQ4** | **On-device deployment:** Which models fit within each microcontroller's resources, and what are their inference latency and memory requirements? |

## Experimental Setup

### Measurement Devices

| Device | Processor | ADC | DAC | Role |
|---|---|---|---|---|
| ESP32 (ESP32-WROOM-32) | Xtensa LX6, 240 MHz | 12-bit | 8-bit | Stimulus generation (DAC) and measurement (ADC) |
| Raspberry Pi Pico 2 W | RP2350 (Arm Cortex-M33), 150 MHz | 12-bit | — | Measurement |
| Arduino Nano | ATmega328P, 16 MHz | 10-bit | — | Measurement |

The device selection allows two effects to be separated. The ESP32 and Pico 2 W share a nominal 12-bit resolution but differ in noise and linearity, isolating **converter quality**. The Pico 2 W and Nano differ primarily in nominal resolution, isolating **bit depth**.

### Circuit Under Test 1: Two-Stage RC Low-Pass Filter

```
ESP32 DAC ──[R_p]──[R1]──┬──[R2]──┬──→ ESP32 ADC (GPIO34)
                         C1       C2 ├─→ Pico 2 W ADC (GP26)
                         │        │  └─→ Nano A0
GND ─────────────────────┴────────┴── common ground (all devices)
```

| Component | Value |
|---|---|
| R1, R2 | 10 kΩ |
| C1, C2 | 100 nF (ceramic) |
| R_p (series protection, not faulted) | 1 kΩ |
| Cutoff frequency (per stage) | ≈ 160 Hz |
| Stimulus | Sine sweep, 10 Hz – 1.5 kHz |
| Sampling rate | 5 kHz on all devices |

The reference transfer function, with R1 including the series protection resistor, is

```
                                 1
H(s) = ───────────────────────────────────────────────────
        1 + s·(R1·C1 + R1·C2 + R2·C2) + s²·(R1·R2·C1·C2)
```

evaluated at s = jω (ω = 2πf), where the measured quantity is the gain |H(jω)|.

### Circuit Under Test 2: Passive Band-Pass Filter

A high-pass stage (100 nF, 10 kΩ referenced to a 1.65 V bias) followed by a low-pass stage (2 kΩ, 100 nF), giving a passband of approximately 160–800 Hz. The bias is derived from a 10 kΩ/10 kΩ divider decoupled by a 10 µF capacitor.

### Fault Model

Each faultable component (R1, R2, C1, C2) is subjected to the fault types below, yielding 16 fault classes plus a nominal (fault-free) class.

| Fault type | Physical realization |
|---|---|
| Parametric drift, +10% | 10 kΩ + 1 kΩ in series, or potentiometer |
| Parametric drift, +20% | 10 kΩ + 2 kΩ in series |
| Parametric drift, −50% / +100% | Two components in parallel / in series |
| Open circuit | Component removed |
| Short circuit | Component bypassed |

Fault classes that produce indistinguishable responses (for example, a shorted C2 and an open R2) form **ambiguity groups**. These are identified from simulation and reported explicitly rather than treated as classification errors.

## Methodology

1. **Simulation.** Circuits are simulated in ngspice with component values sampled within tolerance (±5–10%) and with injected faults, producing a labelled training dataset.
2. **Measurement.** The ESP32 generates a sine sweep, and each device computes per-frequency amplitudes on-board using the Goertzel algorithm.
3. **Training.** Random forest, support vector machine, decision tree and small neural network classifiers are trained on gain-per-frequency features.
4. **Evaluation.** Models are evaluated on physical measurements from each device, across devices, and against a simulated sweep of ADC resolution and noise levels.
5. **Deployment.** Selected models are exported to C via emlearn and evaluated on each device for accuracy, memory footprint and latency.

### Controls

- All devices execute an identical measurement algorithm from a single shared library.
- All devices sample at an identical, timer-driven rate.
- All devices measure each sweep simultaneously, synchronized by a trigger signal from the ESP32.
- All ADC inputs remain connected throughout every session, holding circuit loading constant.
- Every physical component is individually labelled and measured, and each measurement session records the exact components used.

## Repository Structure

```
circuit-dx/
├── circuits/                SPICE netlists, schematics, breadboard photographs
├── data/
│   ├── real/                physical measurements, by device
│   │   ├── esp32/
│   │   ├── nano/
│   │   └── pico2w/
│   └── sim/                 simulated data (reproducible from sim/)
├── firmware/                Arduino sketchbook
│   ├── esp32_sweep/
│   │   └── esp32_sweep.ino      stimulus generation, measurement, synchronization
│   ├── libraries/
│   │   └── Goertzel/            shared measurement library
│   ├── nano_measure/
│   │   └── nano_measure.ino     measurement
│   └── pico2w_measure/
│       └── pico2w_measure.ino   measurement
├── logs/                    dated research log (YYYY-MM-DD.md)
├── ml/                      model training, evaluation, ADC degradation study
├── paper/                   manuscript and poster
├── results/                 figures and tables
├── sim/                     fault injection and circuit simulation
├── parts.csv                component inventory with nominal and measured values
└── README.md
```

## Building the Firmware

The firmware is built with Arduino IDE 2.x using the following board packages:

| Device | Board package | Board selection |
|---|---|---|
| ESP32 | esp32 (Espressif Systems) | ESP32 Dev Module |
| Arduino Nano | Arduino AVR Boards | Arduino Nano, processor ATmega328P (Old Bootloader) for most clone boards |
| Raspberry Pi Pico 2 W | Raspberry Pi Pico/RP2040/RP2350 (Earle F. Philhower, III) | Raspberry Pi Pico 2W |

The `firmware/` directory is an Arduino sketchbook. Setting the IDE's **Sketchbook location** (File → Preferences) to this directory makes the shared `Goertzel` library available to all three sketches.

## Software Dependencies

| Purpose | Software |
|---|---|
| Firmware | Arduino IDE 2.x |
| Circuit simulation | ngspice, PySpice |
| Data acquisition | Python, pyserial |
| Analysis and modelling | NumPy, pandas, scikit-learn, PyTorch, Plotly |
| Model deployment | emlearn |
| Schematics | KiCad |

## Reproducibility

- Simulated datasets are fully regenerable from the code in `sim/`.
- Physical measurement sessions are committed individually, each with the fault configuration, component labels and participating devices.
- Firmware versions and result sets used in publications are identified by Git tags.
- Commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

## License

License terms will be specified prior to public release.
