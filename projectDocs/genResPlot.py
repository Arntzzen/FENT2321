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

# phase_powers = pd.read_excel(
#     EXCEL_FILE,
#     sheet_name=SHEET_NAME,
#     usecols="G, J, M",
#     skiprows=11,
#     nrows=15
# )


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
    loc="upper left"
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
    loc="upper right"
)

ax.legend(
    handles=power_legend,
    title="Power type",
    loc="upper left",
    bbox_to_anchor=(0.1525, 1)
)

ax.set_title("Mechanical Input Power vs Electrical Output Power")
ax.set_xlabel("Rotational speed [RPM]")
ax.set_ylabel("Power [W]")

ax.grid(True)

fig.tight_layout()
fig.savefig(
    OUTPUT_DIR / "03_power_balance.png",
    dpi=300,
    bbox_inches="tight"
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
# GRAPH 5: POWER vs R_load
# ============================================================

# Filter measurements at design speed
design_data = data[
    data["n (rpm)"] == DESIGN_RPM
].copy()

# Sort by load resistance (ascending)
design_data = design_data.sort_values(
    by="Rload_approximated (ohm)"
)

fig, ax = plt.subplots()

# Phase 1
ax.plot(
    design_data["Rload_approximated (ohm)"],
    design_data["P1(W)"],
    marker="o",
    label="Phase 1"
)

# Phase 2
ax.plot(
    design_data["Rload_approximated (ohm)"],
    design_data["P2(W)"],
    marker="s",
    label="Phase 2"
)

# Phase 3
ax.plot(
    design_data["Rload_approximated (ohm)"],
    design_data["P3 (W)"],
    marker="^",
    label="Phase 3"
)

# Total electrical power
ax.plot(
    design_data["Rload_approximated (ohm)"],
    design_data["Pload (W)"],
    marker="D",
    linestyle="--",
    linewidth=2.5,
    label="Total power"
)

ax.set_title(
    f"Phase and Total Power vs Load Resistance ({DESIGN_RPM} RPM)"
)

ax.set_xlabel("Load resistance [Ω]")
ax.set_ylabel("Electrical power [W]")

ax.legend(title="Power type")
ax.grid(True)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "05_phase_total_power.png",
    dpi=300,
    bbox_inches="tight"
)





# ============================================================
# GRAPH 6: TOTAL POWER AND EFFICIENCY VS LOAD RESISTANCE
# ============================================================

fig, ax1 = plt.subplots()

# Secondary y-axis for efficiency
ax2 = ax1.twinx()

rpms = sorted(data["n (rpm)"].unique())

colors_rpm = plt.cm.viridis(
    [i / (len(rpms) - 1) for i in range(len(rpms))]
)

for rpm, color in zip(rpms, colors_rpm):

    subset = data[
        data["n (rpm)"] == rpm
    ].sort_values(
        by="Rload_approximated (ohm)"
    )

    # Total electrical power
    ax1.plot(
        subset["Rload_approximated (ohm)"],
        subset["Pload (W)"],
        marker="o",
        linestyle="-",
        color=color,
        linewidth=2,
        label=f"{rpm:.0f} RPM"
    )

    # Efficiency
    ax2.plot(
        subset["Rload_approximated (ohm)"],
        subset["efficiency (%)"],
        marker="s",
        linestyle="--",
        color=color,
        linewidth=2
    )

# Axis labels
ax1.set_xlabel("Load resistance [Ω]")
ax1.set_ylabel("Total electrical power [W]")
ax2.set_ylabel("Efficiency [%]")

ax1.set_title("Total Electrical Power and Efficiency vs Load Resistance")

ax1.grid(True)

# Legend 1: Rotational speed (colors)
rpm_legend = [
    Line2D(
        [0], [0],
        color=color,
        linewidth=2,
        label=f"{rpm:.0f} RPM"
    )
    for rpm, color in zip(rpms, colors_rpm)
]

legend1 = ax1.legend(
    handles=rpm_legend,
    title="Rotational speed",
    loc="upper left"
)

ax1.add_artist(legend1)

# Legend 2: Parameter (line styles)
parameter_legend = [
    Line2D(
        [0], [0],
        color="black",
        linestyle="-",
        marker="o",
        label="Total electrical power"
    ),
    Line2D(
        [0], [0],
        color="black",
        linestyle="--",
        marker="s",
        label="Efficiency"
    )
]

ax1.legend(
    handles=parameter_legend,
    title="Parameter",
    loc="upper right"
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "06_total_power_efficiency.png",
    dpi=300,
    bbox_inches="tight"
)




# ============================================================
# GRAPH 7: PHASE VOLTAGE AND CURRENT VS LOAD RESISTANCE
# ============================================================

fig, axes = plt.subplots(
    nrows=3,
    ncols=2,
    figsize=(13, 12),
    sharex=True
)

phase_colors = ["tab:blue", "tab:orange", "tab:green"]

voltage_columns = [
    ("U1 (V)", "Phase 1"),
    ("U2 (V)", "Phase 2"),
    ("U3 (V)", "Phase 3")
]

current_columns = [
    ("I1 (A)", "Phase 1"),
    ("I2 (A)", "Phase 2"),
    ("I3 (A)", "Phase 3")
]

for row, rpm in enumerate(rpms):

    subset = data[
        data["n (rpm)"] == rpm
    ].sort_values(
        by="Rload_approximated (ohm)"
    )

    ax_voltage = axes[row, 0]
    ax_current = axes[row, 1]

    # Plot voltage for each phase
    for (column, label), color in zip(
        voltage_columns, phase_colors
    ):
        ax_voltage.plot(
            subset["Rload_approximated (ohm)"],
            subset[column],
            marker="o",
            linewidth=2,
            color=color,
            label=label
        )

    # Plot current for each phase
    for (column, label), color in zip(
        current_columns, phase_colors
    ):
        ax_current.plot(
            subset["Rload_approximated (ohm)"],
            subset[column],
            marker="o",
            linewidth=2,
            color=color,
            label=label
        )

    # Titles
    ax_voltage.set_title(f"Voltage at {rpm:.0f} RPM")
    ax_current.set_title(f"Current at {rpm:.0f} RPM")

    # Y-axis labels
    ax_voltage.set_ylabel("Voltage [V]")
    ax_current.set_ylabel("Current [A]")

    # Legends
    ax_voltage.legend(title="Phase")
    ax_current.legend(title="Phase")

    # Grid
    ax_voltage.grid(True)
    ax_current.grid(True)

# X-axis labels
axes[2, 0].set_xlabel("Load resistance [Ω]")
axes[2, 1].set_xlabel("Load resistance [Ω]")

fig.suptitle(
    "Phase Voltage and Current vs Load Resistance",
    fontsize=15,
    y=1.01
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "07_phase_voltage_current.png",
    dpi=300,
    bbox_inches="tight"
)




# ============================================================
# GRAPH 8: PHASE VOLTAGE VS LOAD RESISTANCE
# ============================================================

fig, axes = plt.subplots(
    nrows=3,
    ncols=1,
    figsize=(10, 12),
    sharex=True
)

phase_columns = [
    ("U1 (V)", "Phase 1"),
    ("U2 (V)", "Phase 2"),
    ("U3 (V)", "Phase 3")
]

phase_colors = ["tab:blue", "tab:orange", "tab:green"]

for ax, rpm in zip(axes, rpms):

    subset = data[
        data["n (rpm)"] == rpm
    ].sort_values(
        by="Rload_approximated (ohm)"
    )

    for (column, label), color in zip(
        phase_columns, phase_colors
    ):
        ax.plot(
            subset["Rload_approximated (ohm)"],
            subset[column],
            marker="o",
            linewidth=2,
            color=color,
            label=label
        )

    ax.set_title(f"Phase Voltage at {rpm:.0f} RPM")
    ax.set_ylabel("Voltage [V]")

    ax.legend(title="Phase")
    ax.grid(True)

axes[-1].set_xlabel("Load resistance [Ω]")

fig.suptitle(
    "Phase Current vs Load Resistance",
    fontsize=15
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "08_phase_voltage.png",
    dpi=300,
    bbox_inches="tight"
)



# ============================================================
# GRAPH 9: PHASE CURRENT VS LOAD RESISTANCE
# ============================================================

fig, axes = plt.subplots(
    nrows=3,
    ncols=1,
    figsize=(10, 12),
    sharex=True
)

phase_columns = [
    ("I1 (A)", "Phase 1"),
    ("I2 (A)", "Phase 2"),
    ("I3 (A)", "Phase 3")
]

phase_colors = ["tab:blue", "tab:orange", "tab:green"]

for ax, rpm in zip(axes, rpms):

    subset = data[
        data["n (rpm)"] == rpm
    ].sort_values(
        by="Rload_approximated (ohm)"
    )

    for (column, label), color in zip(
        phase_columns, phase_colors
    ):
        ax.plot(
            subset["Rload_approximated (ohm)"],
            subset[column],
            marker="o",
            linewidth=2,
            color=color,
            label=label
        )

    ax.set_title(f"Phase Current at {rpm:.0f} RPM")
    ax.set_ylabel("Current [A]")

    ax.legend(title="Phase")
    ax.grid(True)

axes[-1].set_xlabel("Load resistance [Ω]")

fig.suptitle(
    "Phase Current vs Load Resistance",
    fontsize=15
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "09_phase_current.png",
    dpi=300,
    bbox_inches="tight"
)




# ============================================================
# SHOW ALL GRAPHS
# ============================================================

plt.show()

print(f"All graphs saved to: {OUTPUT_DIR.resolve()}")
