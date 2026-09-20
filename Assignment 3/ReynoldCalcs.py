import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# ASSIGNMENT 3
# Preliminary Blade Design and Design-Point Rotor Performance
# ============================================================


# ============================================================
# 1. DESIGN PARAMETERS
# ============================================================

Z = 2                  # number of blades
V1 = 12.0              # wind speed [m/s]
R = 0.30               # rotor radius [m]
N = 15                 # number of blade elements

lambda_des = 6.5       # design tip-speed ratio

rho = 1.2              # air density [kg/m^3]
mu = 1.47e-5           # dynamic viscosity [kg/(m s)]

tol = 30000            # Reynolds convergence tolerance
max_iterations = 100   # maximum number of Step 2 iterations


# ============================================================
# 2. AIRFOIL DATA FROM AIRFOILTOOLS
#
# NACA 2414
#
# Values correspond to max(CL/CD)
# ============================================================

Re_data = np.array([100000, 200000, 500000, 1000000], dtype=float)

CL_data = np.array([0.9155, 0.8850, 0.8155, 0.8797])

CD_data = np.array([0.01903, 0.01424, 0.01027, 0.00977])

alpha_data_deg = np.array([6.50, 6.00, 5.00, 5.75])


# ============================================================
# 3. FUNCTION FOR AIRFOIL DATA INTERPOLATION
# ============================================================

def get_airfoil_data(Re):
    """
    Interpolate CL, CD and alpha_opt for a given Reynolds number.

    The Reynolds number must lie within the available
    AirfoilTools data range.
    """

    if Re < Re_data[0] or Re > Re_data[-1]:
        raise ValueError(
            f"Re = {Re:.0f} is outside the available "
            f"airfoil data range "
            f"({Re_data[0]:.0f} - {Re_data[-1]:.0f})."
        )

    CL = np.interp(Re, Re_data, CL_data)
    CD = np.interp(Re, Re_data, CD_data)
    alpha_opt_deg = np.interp(Re, Re_data, alpha_data_deg)

    return CL, CD, alpha_opt_deg


# ============================================================
# 4. HELPER FUNCTION FOR AXIAL INDUCTION FACTOR
# ============================================================


def calculate_a(lambda_r):
    """
    Solve:

    16a^3 - 24a^2 + a(9 - 3 lambda_r^2)
    - 1 + lambda_r^2 = 0

    Select the physical root 0 < a < 1
    closest to 1/3.
    """

    coefficients = [
        16,
        -24,
        9 - 3 * lambda_r**2,
        -1 + lambda_r**2
    ]

    roots = np.roots(coefficients)

    real_roots = [
        root.real
        for root in roots
        if abs(root.imag) < 1e-10
    ]

    valid_roots = [
        root
        for root in real_roots
        if 0 < root < 1
    ]

    if len(valid_roots) == 0:
        raise ValueError(
            f"No physical solution for a at lambda_r = {lambda_r:.4f}"
        )

    # Select root closest to ideal a = 1/3
    a = min(
        valid_roots,
        key=lambda x: abs(x - 1 / 3)
    )

    return a


# ============================================================
# 5. BLADE ELEMENT LOCATIONS
# ============================================================

dr = R / N

# Element centers
r_values = (np.arange(N) + 0.5) * dr

# Non-dimensional radial positions
r_R_values = r_values / R


# ============================================================
# 6. ROTATIONAL SPEED
# ============================================================

omega = lambda_des * V1 / R


# ============================================================
# 7. STEP 1
#
# Initial Reynolds number at r/R approximately 0.7
#
# Initial chord = 50 mm
# a = 1/3
# a' = 0
# ============================================================

c_initial = 0.050       # initial chord [m]

a_initial = 1 / 3
a_prime_initial = 0

# Find element closest to r/R = 0.7
index_07 = np.argmin(
    np.abs(r_R_values - 0.7)
)

r07 = r_values[index_07]
r_R_07 = r07 / R

# Local TSR
lambda_r07 = lambda_des * r_R_07

# Relative velocity using initial assumptions
W_first = np.sqrt(
    ((1 - a_initial) * V1)**2
    +
    ((1 + a_prime_initial) * omega * r07)**2
)

# First Reynolds number
Re_first = rho * W_first * c_initial / mu


# Get initial aerodynamic data
CL_first, CD_first, alpha_first_deg = get_airfoil_data(Re_first)


print("\n" + "=" * 70)
print("STEP 1")
print("=" * 70)

print(f"Element closest to r/R = 0.7:")
print(f"r/R             = {r_R_07:.4f}")
print(f"r               = {r07:.6f} m")
print(f"Initial chord   = {c_initial:.6f} m")
print(f"lambda_r        = {lambda_r07:.4f}")
print(f"W               = {W_first:.4f} m/s")
print(f"Re_first        = {Re_first:.2f}")

print("\nInterpolated airfoil data:")
print(f"CL              = {CL_first:.6f}")
print(f"CD              = {CD_first:.6f}")
print(f"alpha_opt       = {alpha_first_deg:.4f} deg")


# ============================================================
# 8. STEP 2
#
# Iterate Reynolds number at r/R approximately 0.7
# ============================================================

Re_old = Re_first

print("\n" + "=" * 70)
print("STEP 2 - REYNOLDS NUMBER ITERATION")
print("=" * 70)

print(
    f"{'Iter':>5}"
    f"{'Re_old':>14}"
    f"{'CL':>10}"
    f"{'CD':>10}"
    f"{'alpha':>12}"
    f"{'a':>10}"
    f"{'a_prime':>12}"
    f"{'phi':>10}"
    f"{'chord':>12}"
    f"{'Re_new':>14}"
    f"{'error':>12}"
)

count = 0

for iteration in range(1, max_iterations + 1):

    # --------------------------------------------------------
    # Get CL, CD and alpha corresponding to current Re
    # --------------------------------------------------------

    CL, CD, alpha_opt_deg = get_airfoil_data(Re_old)

    alpha_opt_rad = np.radians(alpha_opt_deg)

    # --------------------------------------------------------
    # Local TSR at r/R approximately 0.7
    # --------------------------------------------------------

    lambda_r = lambda_r07

    # --------------------------------------------------------
    # Axial induction factor
    # --------------------------------------------------------

    a = calculate_a(lambda_r)

    # --------------------------------------------------------
    # Tangential induction factor
    # --------------------------------------------------------

    a_prime = (
        (1 - 3 * a)
        /
        (4 * a - 1)
    )

    # --------------------------------------------------------
    # Flow angle
    # --------------------------------------------------------

    phi = np.arctan(
        (1 - a)
        /
        ((1 + a_prime) * lambda_r)
    )

    # --------------------------------------------------------
    # Axial force coefficient
    # --------------------------------------------------------

    Ca = (
        CL * np.cos(phi)
        +
        CD * np.sin(phi)
    )

    # --------------------------------------------------------
    # Chord
    #
    # Standard BEM expression:
    #
    # c/R =
    # 8*pi*a*(r/R)*sin^2(phi)
    # ---------------------------------
    # (1-a)*Z*Ca
    # --------------------------------------------------------

    chord_R = (8 * np.pi * a * r_R_07 * np.sin(phi)**2 / ((1 - a) * Z * Ca))

    chord = chord_R * R

    # --------------------------------------------------------
    # Relative velocity
    # --------------------------------------------------------

    W = np.sqrt(((1 - a) * V1)**2 + ((1 + a_prime) * omega * r07)**2)

    # --------------------------------------------------------
    # New Reynolds number
    # --------------------------------------------------------

    Re_new = rho * W * chord / mu

    error = abs(Re_new - Re_old)

    print(
        f"{iteration:5d}"
        f"{Re_old:14.2f}"
        f"{CL:10.5f}"
        f"{CD:10.5f}"
        f"{alpha_opt_deg:12.4f}"
        f"{a:10.5f}"
        f"{a_prime:12.5f}"
        f"{np.degrees(phi):10.4f}"
        f"{chord:12.6f}"
        f"{Re_new:14.2f}"
        f"{error:12.2f}"
    )

    # --------------------------------------------------------
    # Check convergence
    # --------------------------------------------------------
    count += 1

    if error <= tol:

        Re_converged = Re_new
        CL_converged = CL
        CD_converged = CD
        alpha_converged_deg = alpha_opt_deg
        print(count)
        break

    # --------------------------------------------------------
    # Update Reynolds number
    # --------------------------------------------------------

    Re_old = Re_new

else:
    raise RuntimeError(
        "Step 2 did not converge within the maximum "
        "number of iterations."
    )


print("\nStep 2 converged:")
print(f"Re_converged    = {Re_converged:.2f}")
print(f"CL              = {CL_converged:.6f}")
print(f"CD              = {CD_converged:.6f}")
print(f"alpha_opt       = {alpha_converged_deg:.4f} deg")
print(f"CL/CD           = {CL_converged / CD_converged:.2f}")


# ============================================================
# 9. STEP 3
#
# Calculate chord and twist distribution
#
# Important:
# Use the CONVERGED CL, CD and alpha_opt from Step 2
# for the blade design.
# ============================================================

print("\n" + "=" * 70)
print("STEP 3 - BLADE GEOMETRY")
print("=" * 70)


# Arrays for results

a_values = np.zeros(N)
a_prime_values = np.zeros(N)
phi_values_deg = np.zeros(N)
theta_values_deg = np.zeros(N)
chord_values = np.zeros(N)
chord_R_values = np.zeros(N)
W_values = np.zeros(N)
Re_local_values = np.zeros(N)

Ca_values = np.zeros(N)


for i, r in enumerate(r_values):

    # --------------------------------------------------------
    # Local TSR
    # --------------------------------------------------------

    x = r / R

    lambda_r = lambda_des * x

    # --------------------------------------------------------
    # Axial induction
    # --------------------------------------------------------

    a = calculate_a(lambda_r)

    # --------------------------------------------------------
    # Tangential induction
    # --------------------------------------------------------

    a_prime = (
        (1 - 3 * a)
        /
        (4 * a - 1)
    )

    # --------------------------------------------------------
    # Flow angle
    # --------------------------------------------------------

    phi = np.arctan(
        (1 - a)
        /
        ((1 + a_prime) * lambda_r)
    )

    # --------------------------------------------------------
    # Use converged airfoil coefficients
    # --------------------------------------------------------

    CL = CL_converged
    CD = CD_converged

    # --------------------------------------------------------
    # Axial force coefficient
    # --------------------------------------------------------

    Ca = (
        CL * np.cos(phi)
        +
        CD * np.sin(phi)
    )

    # --------------------------------------------------------
    # Chord
    # --------------------------------------------------------

    chord_R = (
        8
        * np.pi
        * a
        * x
        * np.sin(phi)**2
        /
        (
            (1 - a)
            * Z
            * Ca
        )
    )

    chord = chord_R * R

    # --------------------------------------------------------
    # Twist angle
    #
    # theta = phi - alpha_opt
    # --------------------------------------------------------

    phi_deg = np.degrees(phi)

    theta_deg = (
        phi_deg
        -
        alpha_converged_deg
    )

    # --------------------------------------------------------
    # Relative velocity
    # --------------------------------------------------------

    W = np.sqrt(
        ((1 - a) * V1)**2
        +
        ((1 + a_prime) * omega * r)**2
    )

    # --------------------------------------------------------
    # Local Reynolds number
    #
    # NOTE:
    # This is calculated for reporting.
    # CL/CD are kept at the converged Step 2 values,
    # following the prescribed design approach.
    # --------------------------------------------------------

    Re_local = rho * W * chord / mu

    # --------------------------------------------------------
    # Store
    # --------------------------------------------------------

    a_values[i] = a
    a_prime_values[i] = a_prime
    phi_values_deg[i] = phi_deg
    theta_values_deg[i] = theta_deg
    chord_values[i] = chord
    chord_R_values[i] = chord_R
    W_values[i] = W
    Re_local_values[i] = Re_local
    Ca_values[i] = Ca


# ============================================================
# 10. PRINT BLADE TABLE
# ============================================================

print(
    f"\n"
    f"{'i':>3}"
    f"{'r/R':>8}"
    f"{'c/R':>10}"
    f"{'theta':>12}"
    f"{'a':>10}"
    f"{'a_prime':>12}"
    f"{'Re':>14}"
)

for i in range(N):

    print(
        f"{i + 1:3d}"
        f"{r_R_values[i]:8.3f}"
        f"{chord_R_values[i]:10.4f}"
        f"{theta_values_deg[i]:12.3f}"
        f"{a_values[i]:10.4f}"
        f"{a_prime_values[i]:12.5f}"
        f"{Re_local_values[i]:14.0f}"
    )


# ============================================================
# 11. BLADE FORCES
#
# dT'  = axial force per unit blade span
#
# dQ'  = torque contribution per unit blade span
#
# Cn = CL*cos(phi) + CD*sin(phi)
# Ct = CL*sin(phi) - CD*cos(phi)
# ============================================================

CL = CL_converged
CD = CD_converged

Cn_values = (
    CL * np.cos(np.radians(phi_values_deg))
    +
    CD * np.sin(np.radians(phi_values_deg))
)

Ct_values = (
    CL * np.sin(np.radians(phi_values_deg))
    -
    CD * np.cos(np.radians(phi_values_deg))
)


# Axial force per unit span [N/m]
dT_dr_values = (
    0.5
    * rho
    * W_values**2
    * chord_values
    * Cn_values
)


# Torque per unit span [N]
dQ_dr_values = (
    0.5
    * rho
    * W_values**2
    * chord_values
    * Ct_values
    * r_values
)


# ============================================================
# 12. TOTAL THRUST AND TORQUE
# ============================================================

# Multiply by number of blades Z
T_total = Z * np.sum(dT_dr_values * dr)

Q_total = Z * np.sum(dQ_dr_values * dr)


# ============================================================
# 13. POWER
# ============================================================

P_total = omega * Q_total


# ============================================================
# 14. POWER AND THRUST COEFFICIENTS
# ============================================================

A = np.pi * R**2

P_available = (
    0.5
    * rho
    * A
    * V1**3
)

T_reference = (
    0.5
    * rho
    * A
    * V1**2
)

CP = P_total / P_available

CT = T_total / T_reference


# ============================================================
# 15. FINAL RESULTS
# ============================================================

print("\n" + "=" * 70)
print("FINAL DESIGN-POINT RESULTS")
print("=" * 70)

print(f"Z                   = {Z}")
print(f"V1                  = {V1:.2f} m/s")
print(f"R                   = {R:.3f} m")
print(f"N                   = {N}")
print(f"lambda_des          = {lambda_des:.2f}")
print(f"omega               = {omega:.3f} rad/s")

print("\nAirfoil:")
print("NACA 2414")

print("\nStep 2:")
print(f"Re_first            = {Re_first:.2f}")
print(f"Re_converged        = {Re_converged:.2f}")
print(f"CL                  = {CL_converged:.6f}")
print(f"CD                  = {CD_converged:.6f}")
print(f"alpha_opt           = {alpha_converged_deg:.4f} deg")
print(f"CL/CD               = {CL_converged / CD_converged:.2f}")

print("\nRotor performance:")
print(f"Total thrust T      = {T_total:.4f} N")
print(f"Total torque Q      = {Q_total:.4f} Nm")
print(f"Power P             = {P_total:.4f} W")
print(f"CP                  = {CP:.4f}")
print(f"CT                  = {CT:.4f}")


# ============================================================
# 16. SANITY CHECKS
# ============================================================

print("\n" + "=" * 70)
print("SANITY CHECKS")
print("=" * 70)

# Most of the blade should have a close-to-ideal axial induction
mid_blade = (
    (r_R_values >= 0.2)
    &
    (r_R_values <= 0.9)
)

a_average = np.mean(a_values[mid_blade])

print(f"Average a, 0.2 <= r/R <= 0.9 = {a_average:.4f}")
print(f"Ideal a = 1/3 = {1/3:.4f}")

print(f"\nMaximum CP = Betz limit = {16/27:.4f}")
print(f"Calculated CP = {CP:.4f}")

print(f"\nIdeal CT = 8/9 = {8/9:.4f}")
print(f"Calculated CT = {CT:.4f}")

if CP < 16 / 27:
    print("CP sanity check: OK")
else:
    print("CP sanity check: WARNING")

if abs(CT - 8 / 9) < 0.1:
    print("CT sanity check: OK")
else:
    print("CT sanity check: WARNING")


# ============================================================
# 17. PLOTS
# ============================================================

# ------------------------------------------------------------
# Chord distribution
# ------------------------------------------------------------

plt.figure(figsize=(7, 5))

plt.plot(
    r_R_values,
    chord_R_values,
    "o-"
)

plt.xlabel("r/R")
plt.ylabel("Chord c/R")
plt.title("Blade chord distribution")
plt.grid(True)

plt.tight_layout()
plt.show()


# ------------------------------------------------------------
# Twist distribution
# ------------------------------------------------------------

plt.figure(figsize=(7, 5))

plt.plot(
    r_R_values,
    theta_values_deg,
    "o-"
)

plt.xlabel("r/R")
plt.ylabel("Twist angle θ [deg]")
plt.title("Blade twist distribution")
plt.grid(True)

plt.tight_layout()
plt.show()


# ------------------------------------------------------------
# Axial induction
# ------------------------------------------------------------

plt.figure(figsize=(7, 5))

plt.plot(
    r_R_values,
    a_values,
    "o-"
)

plt.axhline(
    1 / 3,
    linestyle="--",
    label="a = 1/3"
)

plt.xlabel("r/R")
plt.ylabel("Axial induction factor a")
plt.title("Axial induction distribution")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()


# ------------------------------------------------------------
# Tangential induction
# ------------------------------------------------------------

plt.figure(figsize=(7, 5))

plt.plot(
    r_R_values,
    a_prime_values,
    "o-"
)

plt.xlabel("r/R")
plt.ylabel("Tangential induction factor a'")
plt.title("Tangential induction distribution")
plt.grid(True)

plt.tight_layout()
plt.show()


# ------------------------------------------------------------
# Reynolds number distribution
# ------------------------------------------------------------

plt.figure(figsize=(7, 5))

plt.plot(
    r_R_values,
    Re_local_values,
    "o-"
)

plt.xlabel("r/R")
plt.ylabel("Reynolds number")
plt.title("Reynolds number along blade")
plt.grid(True)

plt.tight_layout()
plt.show()


# ============================================================
# 18. ALL PLOTS IN ONE FIGURE
# ============================================================

fig, axes = plt.subplots(3, 2, figsize=(12, 13))
axes = axes.ravel()

# Chord distribution
axes[0].plot(r_R_values, chord_R_values, "o-")
axes[0].set_xlabel("r/R")
axes[0].set_ylabel("Chord c/R")
axes[0].set_title("Blade chord distribution")
axes[0].grid(True)

# Twist distribution
axes[1].plot(r_R_values, theta_values_deg, "o-")
axes[1].set_xlabel("r/R")
axes[1].set_ylabel("Twist angle θ [deg]")
axes[1].set_title("Blade twist distribution")
axes[1].grid(True)

# Axial induction
axes[2].plot(r_R_values, a_values, "o-")
axes[2].axhline(1 / 3, linestyle="--", label="a = 1/3")
axes[2].set_xlabel("r/R")
axes[2].set_ylabel("Axial induction factor a")
axes[2].set_title("Axial induction distribution")
axes[2].legend()
axes[2].grid(True)

# Tangential induction
axes[3].plot(r_R_values, a_prime_values, "o-")
axes[3].set_xlabel("r/R")
axes[3].set_ylabel("Tangential induction factor a'")
axes[3].set_title("Tangential induction distribution")
axes[3].grid(True)

# Reynolds number distribution
axes[4].plot(r_R_values, Re_local_values, "o-")
axes[4].set_xlabel("r/R")
axes[4].set_ylabel("Reynolds number")
axes[4].set_title("Reynolds number along blade")
axes[4].grid(True)

# Hide the unused sixth subplot.
axes[5].set_visible(False)

fig.suptitle("Blade design distributions", fontsize=16)
fig.tight_layout()
plt.show()