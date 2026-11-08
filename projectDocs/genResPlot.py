import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

EXCEL_FILE = "./projectDocs/Generator test resultater.xlsx"
SHEET_NAME = "Ark"

OUTPUT_DIR = Path("./projectDocs/generator_plots")
OUTPUT_DIR.mkdir(exist_ok=True)

DESIGN_RPM = 1579

# Common plot settings
plt.rcParams.update({
    "figure.figsize": (10, 6),
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "legend.fontsize": 10,
    "lines.linewidth": 2,
    "lines.markersize": 7,
    "axes.grid": True,
    "grid.alpha": 0.3,
})


# ============================================================
# READ EXCEL DATA
# ============================================================

# Load generator measurements (Excel rows 12-27)
data = pd.read_excel(
    EXCEL_FILE,
    sheet_name=SHEET_NAME,
    usecols="B:S",
    skiprows=11,
    nrows=15
)

# Load no-load voltage measurements (Excel rows 5-8)
no_load = pd.read_excel(
    EXCEL_FILE,
    sheet_name=SHEET_NAME,
    usecols="C,D,H,K",
    skiprows=4,
    nrows=3
)

# Sort data by load resistance and RPM
data = data.sort_values(
    by=["Rload_approximated (ohm)", "n (rpm)"]
)

# Identify load resistances
loads = sorted(
    data["Rload_approximated (ohm)"].unique(),
    reverse=True
)

# Give each load resistance its own color
colors = plt.cm.viridis(
    [i / (len(loads) - 1) for i in range(len(loads))]
)


# ============================================================
# GRAPH 1: ELECTRICAL OUTPUT POWER VS RPM
# ============================================================

fig, ax = plt.subplots()

for resistance, color in zip(loads, colors):

    subset = data[
        data["Rload_approximated (ohm)"] == resistance
    ]

    ax.plot(
        subset["n (rpm)"],
        subset["Pload (W)"],
        marker="o",
        color=color,
        label=f"{resistance:.0f} Ω"
    )

ax.axvline(
    DESIGN_RPM,
    color="black",
    linestyle="--",
    alpha=0.7,
    label=f"Design speed ({DESIGN_RPM} RPM)"
)

ax.set_title("Electrical Output Power vs Rotational Speed")
ax.set_xlabel("Rotational speed [RPM]")
ax.set_ylabel("Electrical output power [W]")

ax.legend(title="Load resistance")
ax.grid(True)

fig.tight_layout()
fig.savefig(
    OUTPUT_DIR / "01_output_power.png",
    dpi=300,
    bbox_inches="tight"
)


# ============================================================
# GRAPH 2: GENERATOR EFFICIENCY VS RPM
# ============================================================

fig, ax = plt.subplots()

for resistance, color in zip(loads, colors):

    subset = data[
        data["Rload_approximated (ohm)"] == resistance
    ]

    ax.plot(
        subset["n (rpm)"],
        subset["efficiency (%)"],
        marker="o",
        color=color,
        label=f"{resistance:.0f} Ω"
    )

ax.axvline(
    DESIGN_RPM,
    color="black",
    linestyle="--",
    alpha=0.7,
    label=f"Design speed ({DESIGN_RPM} RPM)"
)

ax.set_title("Generator Efficiency vs Rotational Speed")
ax.set_xlabel("Rotational speed [RPM]")
ax.set_ylabel("Efficiency [%]")

ax.set_ylim(bottom=0)

ax.legend(title="Load resistance")
ax.grid(True)

fig.tight_layout()
fig.savefig(
    OUTPUT_DIR / "02_efficiency.png",
    dpi=300,
    bbox_inches="tight"
)


# ============================================================
# GRAPH 3: MECHANICAL INPUT POWER VS ELECTRICAL OUTPUT POWER
# ============================================================

fig, ax = plt.subplots()

for resistance, color in zip(loads, colors):

    subset = data[
        data["Rload_approximated (ohm)"] == resistance
    ]

    # Mechanical input power (solid line)
    ax.plot(
        subset["n (rpm)"],
        subset["Pin (W)"],
        marker="o",
        linestyle="-",
        color=color
    )

    # Electrical output power (dashed line)
    ax.plot(
        subset["n (rpm)"],
        subset["Pload (W)"],
        marker="s",
        linestyle="--",
        color=color
    )

# Legend 1: Load resistance (colors)
load_legend = [
    Line2D(
        [0], [0],
        color=color,
        linewidth=2,
        label=f"{resistance:.0f} Ω"
    )
    for resistance, color in zip(loads, colors)
]

legend1 = ax.legend(
    handles=load_legend,
    title="Load resistance",
    loc="upper left",
    bbox_to_anchor=(0, 1)
)

ax.add_artist(legend1)

# Legend 2: Power type (line styles)
power_legend = [
    Line2D(
        [0], [0],
        color="black",
        linestyle="-",
        marker="o",
        label="Mechanical input power"
    ),
    Line2D(
        [0], [0],
        color="black",
        linestyle="--",
        marker="s",
        label="Electrical output power"
    )
]

ax.legend(
    handles=power_legend,
    title="Power type",
    loc="upper left",
    bbox_to_anchor=(0.0925, 1)
)


# ============================================================
# GRAPH 4: INDUCED NO-LOAD VOLTAGE VS RPM
# ============================================================

fig, ax = plt.subplots()

phases = {
    "EA1": "EA1 (V)",
    "EA2": "EA2 (V)",
    "EA3": "EA3 (V)"
}

for phase, column in phases.items():

    ax.plot(
        no_load["n (rpm)"],
        no_load[column],
        marker="o",
        label=phase
    )

ax.axvline(
    DESIGN_RPM,
    color="black",
    linestyle="--",
    alpha=0.7,
    label=f"Design speed ({DESIGN_RPM} RPM)"
)

ax.set_title("Induced No-Load Voltage vs Rotational Speed")
ax.set_xlabel("Rotational speed [RPM]")
ax.set_ylabel("Induced voltage [V]")

ax.legend(title="Generator phase")
ax.grid(True)

fig.tight_layout()
fig.savefig(
    OUTPUT_DIR / "04_no_load_voltage.png",
    dpi=300,
    bbox_inches="tight"
)


# ============================================================
# SHOW ALL GRAPHS
# ============================================================

plt.show()

print(f"All graphs saved to: {OUTPUT_DIR.resolve()}")
