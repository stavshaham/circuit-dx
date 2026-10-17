import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pathlib
from scipy.signal import freqs


def frequency_response(f, R1, R2, C1, C2):
    # H(s) = 1 / (1 + s * (R1*C1 + R1*C2 + R2*C2) + s^2 * (R1*R2*C1*C2))
    s = 1j * 2 * np.pi * f  # Converting frequency to complex frequency s = jω, where ω = 2πf
    return 1 / (1 + s * (R1 * C1 + R1 * C2 + R2 * C2) + s ** 2 * (R1 * R2 * C1 * C2))


def get_data(f, h):
    gain = np.abs(h)                        # How much of the wave gets through the filter
    gain_db = 20 * np.log10(gain)           # The gain but in decibels
    phase_deg = np.degrees(np.angle(h))     # How much of the output is delayed
    distance = np.abs(gain - gain_drop)     # The distance from the -3 dB point
    i = np.argmin(distance)                 # Index of the point closest to the -3 dB point
    cutoff = f[i]                           # The cutoff frequency at that index

    return gain, gain_db, phase_deg, i, cutoff


# Getting root path of the repository (sim/ → repository root)
repo_root = pathlib.Path(__file__).resolve().parent.parent

# Measured component values, looked up by part label
parts = pd.read_csv(repo_root / "parts.csv").set_index("id")

# Which physical part sits in which position of Circuit 1 (see logs/2026-10-16.md)
build_parts = {"Rp": "R1k-c", "R1": "R10k-a", "R2": "R10k-e",
               "C1": "C104-a", "C2": "C104-b"}

build = {pos: parts.loc[label, "measured"] for pos, label in build_parts.items()}

# Nominal design values (theory)
R1 = 10e3 + 1e3             # 10 kΩ + 1 kΩ protection resistor
R2 = 10e3                   # 10 kΩ resistor
C1 = 100e-9                 # 100 nF capacitor
C2 = 100e-9                 # 100 nF capacitor
gain_drop = 1 / np.sqrt(2)  # -3 dB point

# As-built values (measured parts; resistors in ohms, capacitors converted nF → F)
R1_build = float(build["R1"]) + float(build["Rp"])      # R1 + protection resistor
R2_build = float(build["R2"])                           # R2 resistor
C1_build = float(build["C1"]) * 1e-9                    # C1 capacitor
C2_build = float(build["C2"]) * 1e-9                    # C2 capacitor

# 200 log-spaced frequencies between 10 Hz and 1500 Hz
frequencies = np.logspace(np.log10(10), np.log10(1500), 200)

H_const = frequency_response(frequencies, R1, R2, C1, C2)
H_built = frequency_response(frequencies, R1_build, R2_build, C1_build, C2_build)

gain, gain_db, phase_deg, i, cutoff = get_data(frequencies, H_const)
gain_built, gain_db_built, phase_deg_built, i_built, cutoff_built = get_data(frequencies, H_built)

# Self-test: a low-pass filter's gain must only decrease with frequency
assert np.all(np.diff(gain) <= 0) and np.all(np.diff(gain_built) <= 0), \
    "Gain should only decrease with frequency"

print(f"As-built values: R1 = {R1_build:.0f} Ω, R2 = {R2_build:.0f} Ω, "
      f"C1 = {C1_build * 1e9:.1f} nF, C2 = {C2_build * 1e9:.1f} nF")
print(f"Cutoff frequency (nominal):  {cutoff:.1f} Hz")
print(f"Cutoff frequency (as-built): {cutoff_built:.1f} Hz")

# Self-test: compare with SciPy's freqs function
w, h = freqs([1], [R1 * R2 * C1 * C2, R1 * C1 + R1 * C2 + R2 * C2, 1],
             worN=frequencies * 2 * np.pi)
w_built, h_built = freqs([1], [R1_build * R2_build * C1_build * C2_build,
                               R1_build * C1_build + R1_build * C2_build + R2_build * C2_build, 1],
                         worN=frequencies * 2 * np.pi)
print("Max difference vs SciPy freqs (nominal): ", np.max(np.abs(np.abs(h) - gain)))
print("Max difference vs SciPy freqs (as-built):", np.max(np.abs(np.abs(h_built) - gain_built)))

# Results directory
results_dir = repo_root / "results"
results_dir.mkdir(exist_ok=True)

# Nominal (theory) curve
df = pd.DataFrame({
    "frequency": frequencies,
    "gain": gain,
    "gain_db": gain_db,
    "phase_deg": phase_deg
})
df.to_csv(results_dir / "circuit1_reference.csv", index=False)

# As-built curve
df_built = pd.DataFrame({
    "frequency": frequencies,
    "gain": gain_built,
    "gain_db": gain_db_built,
    "phase_deg": phase_deg_built
})
df_built.to_csv(results_dir / "circuit1_asbuilt.csv", index=False)

# Graphing
fig = go.Figure()

# Nominal curve (dashed)
fig.add_trace(go.Scatter(
    x=frequencies,
    y=gain_db,
    mode="lines",
    name="Nominal (theory)",
    line=dict(dash="dash")
))

# As-built curve (solid)
fig.add_trace(go.Scatter(
    x=frequencies,
    y=gain_db_built,
    mode="lines",
    name="As-built (measured parts)"
))

# Nominal cutoff (red dot)
fig.add_trace(go.Scatter(
    x=[cutoff],
    y=[gain_db[i]],
    name=f"Cutoff — nominal ({cutoff:.1f} Hz)",
    mode="markers",
    marker=dict(color="red", size=10),
))

# As-built cutoff (blue dot)
fig.add_trace(go.Scatter(
    x=[cutoff_built],
    y=[gain_db_built[i_built]],
    name=f"Cutoff — as-built ({cutoff_built:.1f} Hz)",
    mode="markers",
    marker=dict(color="blue", size=12, symbol="circle-open"),
))

fig.update_layout(
    title="Circuit 1 — Frequency Response (nominal vs as-built)",
    xaxis_title="Frequency (Hz)",
    yaxis_title="Gain (dB)",
    xaxis_type="log",
    yaxis=dict(range=[-45, 5]),
    template="plotly_dark"
)

# -3 dB guide line
fig.add_hline(y=-3, line_dash="dash", line_color="red",
              annotation_text="-3 dB", annotation_position="bottom right")

# Save the figure
fig.write_html(results_dir / "circuit1_reference.html", include_plotlyjs="cdn")