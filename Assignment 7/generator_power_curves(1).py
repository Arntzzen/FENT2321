"""
Generator + QBlade power-curve analysis
Based on the values/formulas in "Generator Design.xlsx".

Expected QBlade CSV:
    RPM,Power
    500,12.3
    550,15.8
    ...

If your QBlade export uses another separator/column names, edit the
CSV loading section below.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. VALUES EXTRACTED FROM Generator Design.xlsx
# ============================================================

# Turbine design point
RPM_DESIGN = 1579.0
TAERO_DESIGN = 1.823          # Nm

# Geometry
DIST_MIN = 0.045              # m
TCOIL = 0.015                 # m

# Rotor / flux
N_POLES = 2
B = 0.2                       # T

# Stator
N_PHASE = 1
D_CU = 0.00118                # m
N_TURN = 60
L_ACTIVE = 0.12               # m
L_CORR = 1.1
FW = 0.9
N_SERIES = 4
T_CU = 30                     # degC

# Miscellaneous
N0 = 28
LS0 = 0.0008                  # H
RPM0 = 1000.0                 # rpm
PLOSS0 = 75.0                 # W
PLOSS_OFFSET = 5.0            # W
T0 = 20.0                     # degC
ALPHA_CU = 3.9e-3             # 1/degC
RHO_CU = 1.68e-8              # ohm*m

# Resistance correction
C_C = 1.1

# Design load resistance from the spreadsheet
RLOAD_DESIGN = 20.61          # ohm


# ============================================================
# 2. FIXED GENERATOR PARAMETERS CALCULATED FROM THE SHEET
# ============================================================

# Wire length per turn:
# C27*(2*C26 + 2*2*pi()*(C15+C16/2)/C29)
L_TURN = L_CORR * (
    2 * L_ACTIVE
    + 4 * np.pi * (DIST_MIN + TCOIL / 2) / N_SERIES
)

# Length of wire per coil
L_COIL = L_TURN * N_TURN

# Total wire length in stator
L_STATOR = L_COIL * N_SERIES * N_PHASE

# Copper cross-sectional area
A_CU = np.pi * (D_CU / 2) ** 2

# Copper resistance per metre at operating temperature
R_COPPER = RHO_CU * (1 + ALPHA_CU * (T_CU - T0)) / A_CU

# Total stator resistance per phase
R_TOT = R_COPPER * L_STATOR * C_C

# Stator inductance per phase
L_S = LS0 * (N_TURN / N0) ** 2 * N_SERIES


# ============================================================
# 3. GENERATOR MODEL
# ============================================================

def generator_power(rpm, r_load):
    """
    Calculate generator input power for one or more RPM values.

    This follows the formulas in the Excel sheet:

        omega      = RPM*pi/30
        omega_e    = omega*(P/2)
        v_avg      = omega*(DistMin+tcoil/2)

        Einduced   = Nturn*B*v_avg*(2*Lactive)*Ns*fw/sqrt(2)

        Xs         = omega_e*Ls

        I          = Einduced /
                     sqrt((Rtot+Rload)^2 + Xs^2)

        Pload      = Vterm*I
                   = I^2*Rload

        Ploss,c    = Nphase*I^2*Rtot

        Ploss,m    = (RPM/RPM0)*Ploss0 + PLOSS_OFFSET

        Pgen       = Pload + Ploss,c + Ploss,m
    """

    rpm = np.asarray(rpm, dtype=float)
    r_load = np.asarray(r_load, dtype=float)

    omega = rpm * np.pi / 30.0
    omega_e = omega * (N_POLES / 2.0)

    v_avg = omega * (DIST_MIN + TCOIL / 2.0)

    e_induced = (
        N_TURN
        * B
        * v_avg
        * (2 * L_ACTIVE)
        * N_SERIES
        * FW
        / np.sqrt(2.0)
    )

    x_s = omega_e * L_S

    current = e_induced / np.sqrt(
        (R_TOT + r_load) ** 2 + x_s ** 2
    )

    v_terminal = current * r_load

    p_load = v_terminal * current
    p_loss_copper = N_PHASE * current**2 * R_TOT
    p_loss_mechanical = (rpm / RPM0) * PLOSS0 + PLOSS_OFFSET

    p_gen = p_load + p_loss_copper + p_loss_mechanical

    return p_gen


def generator_details(rpm, r_load):
    """Return all intermediate generator quantities."""
    rpm = float(rpm)
    r_load = float(r_load)

    omega = rpm * np.pi / 30.0
    omega_e = omega * (N_POLES / 2.0)
    v_avg = omega * (DIST_MIN + TCOIL / 2.0)

    e_induced = (
        N_TURN * B * v_avg * (2 * L_ACTIVE)
        * N_SERIES * FW / np.sqrt(2.0)
    )

    x_s = omega_e * L_S

    current = e_induced / np.sqrt(
        (R_TOT + r_load)**2 + x_s**2
    )

    v_terminal = current * r_load
    p_load = v_terminal * current
    p_loss_copper = N_PHASE * current**2 * R_TOT
    p_loss_mechanical = (rpm / RPM0) * PLOSS0 + PLOSS_OFFSET
    p_gen = p_load + p_loss_copper + p_loss_mechanical

    return {
        "RPM": rpm,
        "R_load": r_load,
        "omega": omega,
        "omega_e": omega_e,
        "v_avg": v_avg,
        "E_induced": e_induced,
        "X_s": x_s,
        "I": current,
        "V_terminal": v_terminal,
        "P_load": p_load,
        "P_loss_copper": p_loss_copper,
        "P_loss_mechanical": p_loss_mechanical,
        "P_gen": p_gen,
        "T_gen": p_gen / omega if omega != 0 else np.nan,
        "efficiency": p_load / p_gen if p_gen != 0 else np.nan,
    }


# ============================================================
# 4. LOAD QBlade DATA
# ============================================================

QBlade_FILE = "C:/Users/marku/Desktop/FENT2321/Assignment 7/power_rpm.csv"

# Change these if your CSV uses different column names.
RPM_COLUMN = "Rotational Speed [rpm]"
POWER_COLUMN = "Power [W]"

try:
    qblade = pd.read_csv(QBlade_FILE, sep=";")
except FileNotFoundError:
    print(f"\nCould not find '{QBlade_FILE}'.")
    print("Put your QBlade CSV in the same folder as this Python file.")
    print("The CSV should contain columns named RPM and Power.")
    print("\nThe generator model itself is ready to use.")
    print("\nExample:")
    print("RPM,Power")
    print("500,25.3")
    print("600,38.7")
    print("700,55.1")
    raise SystemExit

qblade = qblade[[RPM_COLUMN, POWER_COLUMN]].copy()
qblade = qblade.sort_values(RPM_COLUMN)

rpm_qblade = qblade[RPM_COLUMN].to_numpy(dtype=float)
p_aero = qblade[POWER_COLUMN].to_numpy(dtype=float)


# ============================================================
# 5. FIND RLOAD VALUES FOR RPMdesign-300, RPMdesign,
#    AND RPMdesign+300
# ============================================================

RPM_LOW = RPM_DESIGN - 300.0
RPM_HIGH = RPM_DESIGN + 300.0

# The design value is specified directly by the generator sheet.
rload_design = RLOAD_DESIGN


def interpolate_aero_power(rpm):
    """Interpolate QBlade rotor power at a requested RPM."""
    if rpm < rpm_qblade.min() or rpm > rpm_qblade.max():
        raise ValueError(
            f"RPM={rpm:.1f} is outside the QBlade data range "
            f"({rpm_qblade.min():.1f} to {rpm_qblade.max():.1f})."
        )
    return float(np.interp(rpm, rpm_qblade, p_aero))


def find_rload_for_target(rpm_target, target_power):
    """
    Find a load resistance for which:

        P_generator(rpm_target, Rload) = target_power

    The function scans a wide range of Rload values and finds all
    sign changes. If several solutions exist, the one closest to the
    design Rload is selected.
    """
    r_values = np.logspace(-3, 4, 5000)  # 0.001 ... 10000 ohm
    f_values = generator_power(rpm_target, r_values) - target_power

    roots = []

    for i in range(len(r_values) - 1):
        f1 = f_values[i]
        f2 = f_values[i + 1]

        if f1 == 0:
            roots.append(r_values[i])
        elif f1 * f2 < 0:
            # Linear interpolation in log(R) is sufficient for finding
            # a starting root in this dense scan.
            x1 = np.log10(r_values[i])
            x2 = np.log10(r_values[i + 1])

            root_x = x1 + (0 - f1) * (x2 - x1) / (f2 - f1)
            roots.append(10 ** root_x)

    if not roots:
        raise RuntimeError(
            f"No Rload found for RPM={rpm_target:.1f} and "
            f"target power={target_power:.2f} W."
        )

    # Choose the solution closest to the design resistance.
    return min(roots, key=lambda r: abs(r - RLOAD_DESIGN))


p_aero_low = interpolate_aero_power(RPM_LOW)
p_aero_design = interpolate_aero_power(RPM_DESIGN)
p_aero_high = interpolate_aero_power(RPM_HIGH)

rload_low = find_rload_for_target(RPM_LOW, p_aero_low)
rload_high = find_rload_for_target(RPM_HIGH, p_aero_high)


# ============================================================
# 6. CALCULATE THE THREE GENERATOR CURVES
# ============================================================

rloads = {
    f"Rload = {rload_low:.3f} Ω": rload_low,
    f"Rload = {rload_design:.3f} Ω": rload_design,
    f"Rload = {rload_high:.3f} Ω": rload_high,
}

generator_curves = {}

for label, rload in rloads.items():
    generator_curves[label] = generator_power(rpm_qblade, rload)


# ============================================================
# 7. PRINT IMPORTANT RESULTS
# ============================================================

print("\n============================================================")
print("GENERATOR PARAMETERS")
print("============================================================")
print(f"L_turn       = {L_TURN:.6f} m")
print(f"L_coil       = {L_COIL:.6f} m")
print(f"L_stator     = {L_STATOR:.6f} m")
print(f"A_cu         = {A_CU:.9e} m^2")
print(f"R_copper     = {R_COPPER:.6f} ohm/m")
print(f"R_tot        = {R_TOT:.6f} ohm")
print(f"L_s          = {L_S:.9f} H")

print("\n============================================================")
print("DESIGN POINT CHECK")
print("============================================================")
details = generator_details(RPM_DESIGN, RLOAD_DESIGN)

for key, value in details.items():
    print(f"{key:20s}: {value:.6f}")

print("\n============================================================")
print("THREE RLOAD VALUES")
print("============================================================")
print(f"Low RPM target:    {RPM_LOW:.0f} RPM")
print(f"QBlade power:      {p_aero_low:.3f} W")
print(f"Rload:             {rload_low:.6f} ohm")

print(f"\nDesign RPM target: {RPM_DESIGN:.0f} RPM")
print(f"QBlade power:      {p_aero_design:.3f} W")
print(f"Rload:             {rload_design:.6f} ohm")

print(f"\nHigh RPM target:   {RPM_HIGH:.0f} RPM")
print(f"QBlade power:      {p_aero_high:.3f} W")
print(f"Rload:             {rload_high:.6f} ohm")


# ============================================================
# 8. PLOT
# ============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    rpm_qblade,
    p_aero,
    linewidth=2.5,
    label="Rotor power"
)

for label, p_gen in generator_curves.items():
    plt.plot(
        rpm_qblade,
        p_gen,
        linewidth=2,
        label=f"Generator power ({label})"
    )

plt.axvline(RPM_LOW, linestyle="--", alpha=0.5)
plt.axvline(RPM_DESIGN, linestyle="--", alpha=0.5)
plt.axvline(RPM_HIGH, linestyle="--", alpha=0.5)

plt.xlabel("RPM")
plt.ylabel("Power [W]")
plt.title("Rotor and Generator Power Curves")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()
