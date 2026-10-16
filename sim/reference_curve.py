import numpy as np
import pandas as pd
import plotly.graph_objs as go
import pathlib
from scipy.signal import freqs

# Constants, do not change these values
R1 = 10e3 + 1e3            # 10kΩ + 1kΩ of protection resistor
R2 = 10e3                   # 10kΩ resistor
C1 =  100e-9                 # 100nF capacitor
C2 =  100e-9                 # 100nF capacitor
gain_drop = 1/np.sqrt(2)    # Gain drop expected, -3dB point

frequencies = np.logspace(np.log10(10), np.log10(1500), 200)      # Creating a line frequency between 10Hz and 1500Hz with 200 points

# H(s) formula = 1 / (1 + s * (R1 * C1 + R1 * C2 + R2 * C2) + s**2 * (R1 * R2 * C1 * C2))
s = 1j  * 2 * np.pi * frequencies                                               # Converting frequency to complex frequency s = jω, where ω = 2πf
H = 1 / (1 + s * (R1 * C1 + R1 * C2 + R2 * C2) + s**2 * (R1 * R2 * C1 * C2))

gain = np.abs(H)                        # How much of the wave gets through the filter
gain_db = 20 * np.log10(gain)           # The gain but in decibels
phase_deg = np.degrees(np.angle(H))     # How much of the output is delayed
distance = np.abs(gain - gain_drop)     # The distance from the gain drop point
i = np.argmin(distance)                 # Taking the index of the minimum distance to find the cutoff frequency
cutoff = frequencies[i]                 # The cutoff frequency is the frequency at the index of the minimum distance

print(f"Cutoff frequency: {cutoff:.1f} Hz")

# Temporary printing the data to make sure (Almost as expected)
#for target in [10, 50, 100, 500, 1500]:
#    j = np.argmin(np.abs(frequencies - target))
#    print(f"{frequencies[j]:7.1f} Hz   gain {gain[j]:.3f}   {gain_db[j]:6.2f} dB   {phase_deg[j]:6.1f}°")

# Checking that the formula is correct by comparing to SciPy's freqs function
w, h = freqs([1], [R1 * R2 * C1 * C2, R1 * C1 + R1 * C2 + R2 * C2, 1], worN=frequencies * 2 * np.pi)
print ("Max difference vs SciPy freqs: ", np.max(np.abs(np.abs(h) - gain)))

# Getting root path of the repository to save the reference curve data
repo_root = pathlib.Path(__file__).resolve().parent.parent
# Getting the result directory, where we want to store the csv file
results_dir = repo_root / "results"
results_dir.mkdir(exist_ok=True)

# Creating a DataFrame with the frequency, gain, gain in dB, and phase in degrees
df = pd.DataFrame({
    "frequency": frequencies,
    "gain": gain,
    "gain_db": gain_db,
    "phase_deg": phase_deg
})

# Saving the DataFrame to a CSV file in the results directory
df.to_csv(results_dir / "circuit1_reference.csv", index=False)

# Graphing
fig = go.Figure()

# Creating the frequency response plot with gain in dB vs frequency
fig.add_trace(go.Scatter(
    x=frequencies,
    y=gain_db,
    mode='lines',
    name='Gain (dB)'
))

# Marking the cutoff frequency on the plot with a red dot
fig.add_trace(go.Scatter(
    x=[frequencies[i]],
    y=[gain_db[i]],
    name=f"Cutoff ({frequencies[i]:.1f} Hz)",
    mode="markers",
    marker=dict(color="red", size=10),
))

fig.update_layout(
    title='Circuit 1 — Reference Frequency Response (theory)',
    xaxis_title='Frequency (Hz)',
    yaxis_title='Gain (dB)',
    xaxis_type='log',
    yaxis=dict(range=[-40, 5]),
    template='plotly_dark'
)

# Adding a horizontal line at -3 dB to indicate the cutoff point
fig.add_hline(y=-3, line_dash="dash", line_color="red", annotation_text="-3 dB", annotation_position="bottom right")

# Saving the figure to a HTML file in the results directory
fig.write_html(results_dir / "circuit1_reference.html", include_plotlyjs='cdn')