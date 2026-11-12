import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================
DATA_DIR = Path("./projectDocs/wind_turbine_test_data/Increased Wind Speed")
OUTPUT_DIR = Path("./projectDocs/wind_turbine_plots")
OUTPUT_DIR.mkdir(exist_ok=True)

# Number of initial seconds to exclude from averages.
# Set to 0 to include all samples.
SKIP_FIRST_SECONDS = 0


# Connect each filename to its measured load resistance.
# Fill in the actual values from your experiment.
#
# Example:
# LOADS_OHM = {
#     "Group10_1_....txt": 100,
#     "Group10_2_....txt": 75,
# }

LOADS_OHM = {
    # "filename.txt": resistance_in_ohm,
}


# ============================================================
# COLUMN DEFINITIONS
# ============================================================

PHASE_VOLTAGES = [
    "Volt L1 SP",
    "Volt L2 SP",
    "Volt L3 SP"
]

PHASE_CURRENTS = [
    "Current L1 ST",
    "Current L2 ST",
    "Current L3 ST"
]

EFFICIENCIES = [
    "Mechanical efficiency",
    "Electrical efficiency",
    "Total efficiency"
]

PHASE_LABELS = [
    "Phase 1",
    "Phase 2",
    "Phase 3"
]

COLORS = [
    "tab:blue",
    "tab:orange",
    "tab:green"
]


# ============================================================
# READ ALL TXT FILES
# ============================================================

def read_measurement_file(filepath):
    df = pd.read_csv(filepath, sep="\t", decimal=",", encoding="utf-8-sig")
    # Remove empty columns
    df = df.dropna(axis=1, how="all")
    # Convert all measurement columns to numeric
    for col in df.columns:
        if col != "Time":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Convert timestamp
    df["Time"] = pd.to_datetime(df["Time"], format="%d.%m.%Y %H:%M:%S" # errors="coerce"
                                )
    # Time relative to start of measurement
    df["Elapsed time (s)"] = (
        df["Time"] - df["Time"].iloc[0]
    ).dt.total_seconds()
    # Optional removal of initial samples
    # df = df[
    #     df["Elapsed time (s)"] >= SKIP_FIRST_SECONDS
    # ].copy()
    return df


# ============================================================
# LOAD ALL MEASUREMENTS
# ============================================================

files = sorted(DATA_DIR.glob("*.txt"), key=lambda filepath: int(filepath.name.split("_")[1]))

if not files:
    raise FileNotFoundError(
        "No .txt files found in the data directory."
    )

measurements = {}

for filepath in files:
    df = read_measurement_file(filepath)
    measurements[filepath.name] = df
    print(
        f"{filepath.name}: "
        f"{len(df)} samples"
    )

# ============================================================
# CALCULATE AVERAGE VALUES FOR EACH TEST
# ============================================================

summary = []

for filename, df in measurements.items():

    row = {
        "Filename": filename,
        "Samples": len(df)
    }

    # Average of all numerical measurement columns
    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

    for col in numeric_columns:
        row[col] = df[col].mean()

    # Standard deviation of selected variables
    for col in [
        "Rotation speed",
        "Wind speed",
        "Torque",
        "Electric Power"
    ]:
        row[f"{col} std"] = df[col].std()

    # Add load resistance if available
    row["R_load"] = LOADS_OHM.get(
        filename,
        np.nan
    )

    summary.append(row)

results = pd.DataFrame(summary)

# Sort by load resistance if all values are available
if results["R_load"].notna().all():

    results = results.sort_values(
        "R_load"
    )

    x = results["R_load"].to_numpy()
    x_label = "Load resistance [Ω]"

else:

    # Otherwise use test number as x-axis
    x = np.arange(len(results))

    x_label = "Measurement"

    print(
        "\nWARNING: Load resistance values are missing."
        "\nPlots will use measurement number instead."
    )


print("\nAVERAGE MEASUREMENT RESULTS:")
print(results.to_string(index=False))

results.to_csv(
    OUTPUT_DIR / "measurement_summary.csv",
    index=False
)


# ============================================================
# GRAPH 1: MEASUREMENTS VS TIME
# ============================================================

time_variables = [
    ("Rotation speed", "Rotor speed [RPM]"),
    ("Wind speed", "Wind speed [m/s]"),
    ("Torque", "Torque [Nm]"),
    ("Electric Power", "Electrical power [W]")
]

fig, axes = plt.subplots(
    2, 2,
    figsize=(13, 9)
)

for ax, (column, ylabel) in zip(
    axes.flat,
    time_variables
):

    for filename, df in measurements.items():

        ax.plot(
            df["Elapsed time (s)"],
            df[column],
            marker=".",
            linewidth=1.5,
            label=filename
        )

    ax.set_xlabel("Time [s]")
    ax.set_ylabel(ylabel)
    ax.grid(True)
    ax.legend(fontsize=8)

fig.suptitle(
    "Wind Turbine Measurements Over Time"
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "01_measurements_over_time.png",
    dpi=300
)


# ============================================================
# GRAPH 2: POWER, TORQUE AND RPM VS LOAD
# ============================================================

fig, axes = plt.subplots(
    2, 2,
    figsize=(13, 9)
)

power_variables = [
    ("Electric Power", "Electrical power [W]"),
    ("Mechanical power", "Mechanical power [W]"),
    ("Torque", "Torque [Nm]"),
    ("Rotation speed", "Rotor speed [RPM]")
]

for ax, (column, ylabel) in zip(
    axes.flat,
    power_variables
):

    ax.plot(
        x,
        results[column],
        marker="o",
        linewidth=2
    )

    ax.set_xlabel(x_label)
    ax.set_ylabel(ylabel)
    ax.grid(True)

fig.suptitle(
    "Wind Turbine Performance vs Load"
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "02_performance_vs_load.png",
    dpi=300
)


# ============================================================
# GRAPH 3: EFFICIENCY VS LOAD
# ============================================================

fig, ax = plt.subplots(figsize=(9, 6))

for column in EFFICIENCIES:

    ax.plot(
        x,
        results[column],
        marker="o",
        linewidth=2,
        label=column
    )

ax.set_xlabel(x_label)
ax.set_ylabel("Efficiency [%]")
ax.set_title("Wind Turbine Efficiency vs Load")

ax.grid(True)
ax.legend()

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "03_efficiency_vs_load.png",
    dpi=300
)


# ============================================================
# GRAPH 4: PHASE VOLTAGES AND CURRENTS VS LOAD
# ============================================================

fig, axes = plt.subplots(
    2, 1,
    figsize=(10, 10),
    sharex=True
)

for column, label, color in zip(
    PHASE_VOLTAGES,
    PHASE_LABELS,
    COLORS
):

    axes[0].plot(
        x,
        results[column],
        marker="o",
        linewidth=2,
        label=label,
        color=color
    )


for column, label, color in zip(
    PHASE_CURRENTS,
    PHASE_LABELS,
    COLORS
):

    axes[1].plot(
        x,
        results[column],
        marker="o",
        linewidth=2,
        label=label,
        color=color
    )


axes[0].set_ylabel("Voltage [V]")
axes[0].set_title("Phase Voltages")
axes[0].legend()
axes[0].grid(True)

axes[1].set_ylabel("Current [A]")
axes[1].set_xlabel(x_label)
axes[1].set_title("Phase Currents")
axes[1].legend()
axes[1].grid(True)

fig.suptitle(
    "Generator Phase Measurements vs Load"
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "04_phase_measurements_vs_load.png",
    dpi=300
)


# ============================================================
# GRAPH 5: TSR AND WIND SPEED VS LOAD
# ============================================================

fig, axes = plt.subplots(
    2, 1,
    figsize=(9, 9),
    sharex=True
)

axes[0].plot(
    x,
    results["TSR"],
    marker="o",
    linewidth=2
)

axes[0].set_ylabel("Tip Speed Ratio [-]")
axes[0].set_title("Tip Speed Ratio")
axes[0].grid(True)


axes[1].plot(
    x,
    results["Wind speed"],
    marker="o",
    linewidth=2,
    color="tab:orange"
)

axes[1].set_ylabel("Wind speed [m/s]")
axes[1].set_xlabel(x_label)
axes[1].set_title("Wind Speed")
axes[1].grid(True)

fig.suptitle(
    "Aerodynamic Operating Conditions"
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "05_aerodynamic_performance.png",
    dpi=300
)


# ============================================================
# GRAPH 6: DC VOLTAGE AND CURRENT VS LOAD
# ============================================================

fig, axes = plt.subplots(
    2, 1,
    figsize=(9, 9),
    sharex=True
)

axes[0].plot(
    x,
    results["Volt DC3 SP"],
    marker="o",
    linewidth=2
)

axes[0].set_ylabel("DC voltage [V]")
axes[0].set_title("DC Voltage")
axes[0].grid(True)


axes[1].plot(
    x,
    results["Current DC3 ST"],
    marker="o",
    linewidth=2,
    color="tab:orange"
)

axes[1].set_ylabel("DC current [A]")
axes[1].set_xlabel(x_label)
axes[1].set_title("DC Current")
axes[1].grid(True)

fig.suptitle(
    "DC Output Measurements"
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "06_dc_measurements_vs_load.png",
    dpi=300
)


# ============================================================
# SHOW ALL PLOTS
# ============================================================

plt.show()

print(
    f"\nAll plots saved in: {OUTPUT_DIR.resolve()}"
)
