"""
TEP4175/FENT2321 - Assignment 1, Part 3
Airfoil polar analysis from QBlade/XFOIL exported files.

Put this script in the same folder as your exported QBlade files.
The script automatically searches for .txt, .dat, .plr and .polar files.

Expected original polar data:
    alpha, CL, CD
(or XFOIL/QBlade columns containing these quantities)

Expected Reynolds numbers:
    100000 and 1000000

Run:
    python assignment1_part3.py

The script creates:
    results/
        Figure1_CL_vs_alpha.png
        Figure2_CD_vs_alpha.png
        Figure3_CL_CD_vs_alpha.png
        Figure4_Viterna_360.png          (if .plr files are found)
        max_efficiency.txt
        processed_polar_Re100000.csv
        processed_polar_Re1000000.csv
"""

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# SETTINGS
# ============================================================

DATA_FOLDER = Path(".")
RESULTS_FOLDER = Path("results")

TARGET_RE = [100000, 1000000]
NCRIT = 5

RESULTS_FOLDER.mkdir(exist_ok=True)


# ============================================================
# FILE READING
# ============================================================

def extract_reynolds(text):
    """Try to find Reynolds number in a filename/header."""
    patterns = [
        r"Re\s*=\s*([0-9.eE+\-]+)",
        r"Reynolds\s*number\s*[:=]\s*([0-9.eE+\-]+)",
        r"Re\s*([0-9.eE+\-]+)",
    ]

    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            try:
                value = float(m.group(1))
                # Convert e.g. 1e5 to 100000
                if value > 0:
                    return int(round(value))
            except ValueError:
                pass

    # Search for common numbers in the name
    for value in TARGET_RE:
        if str(value) in text:
            return value

    return None


def read_polar_file(path):
    """
    Read a QBlade/XFOIL-style polar file.

    The function looks for columns containing:
        alpha
        CL
        CD

    It is deliberately tolerant of headers and whitespace.
    """
    text = path.read_text(errors="ignore")
    re_number = extract_reynolds(path.name + "\n" + text)

    # Read lines and identify numerical rows.
    rows = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        # Ignore obvious comments/header lines.
        if line.startswith(("#", "!", ";")):
            continue

        # Split on whitespace, comma, or semicolon.
        parts = re.split(r"[\s,;]+", line)

        numbers = []
        for p in parts:
            try:
                numbers.append(float(p))
            except ValueError:
                pass

        # XFOIL polar rows normally contain at least:
        # alpha CL CD CDp CM Top_Xtr Bot_Xtr
        if len(numbers) >= 3:
            rows.append(numbers)

    if not rows:
        raise ValueError(f"No numerical polar data found in {path}")

    # In standard XFOIL/QBlade output the first 3 relevant columns are
    # alpha, CL, CD. If there are many columns this remains valid.
    arr = np.array([row[:3] for row in rows], dtype=float)

    df = pd.DataFrame(arr, columns=["alpha", "CL", "CD"])

    # Remove impossible/header-like rows and duplicates.
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    df = df[(df["alpha"] >= -360) & (df["alpha"] <= 360)]
    df = df.sort_values("alpha").drop_duplicates("alpha")

    if len(df) < 3:
        raise ValueError(f"Too little usable polar data in {path}")

    df["CL_CD"] = df["CL"] / df["CD"].replace(0, np.nan)

    return df, re_number


# ============================================================
# FIND FILES
# ============================================================

all_files = []
for pattern in ("*.txt", "*.dat", "*.plr", "*.polar"):
    all_files.extend(DATA_FOLDER.glob(pattern))

# Don't accidentally read our own generated CSV files.
all_files = [p for p in all_files if p.parent.resolve() != RESULTS_FOLDER.resolve()]

if not all_files:
    raise FileNotFoundError(
        "No .txt, .dat, .plr or .polar files found. "
        "Put your QBlade exported files in the same folder as this script."
    )

original = {}
extrapolated = {}

for path in all_files:
    try:
        df, re_number = read_polar_file(path)

        if re_number in TARGET_RE:
            # .plr files are normally the Viterna/extrapolated data.
            # Files with an angular range larger than the normal XFOIL
            # range are also treated as extrapolated.
            is_360 = path.suffix.lower() == ".plr" or (
                df["alpha"].min() < -25 and df["alpha"].max() > 25
            )

            if is_360:
                extrapolated[re_number] = (path, df)
            else:
                original[re_number] = (path, df)

            print(f"Read: {path.name:35s} Re = {re_number:,}  rows = {len(df)}")

    except Exception as exc:
        print(f"Skipped {path.name}: {exc}")


# ============================================================
# CHECK ORIGINAL DATA
# ============================================================

missing = [Re for Re in TARGET_RE if Re not in original]

if missing:
    print("\nWARNING:")
    print("Could not automatically identify original polar files for:")
    for Re in missing:
        print(f"  Re = {Re:,}")

    print("\nIf your filenames/header do not contain the Reynolds number,")
    print("rename them, for example:")
    print("  polar_Re100000.txt")
    print("  polar_Re1000000.txt")

    raise SystemExit


# ============================================================
# PLOT ORIGINAL POLARS
# ============================================================

labels = {
    100000: r"$Re=1\times10^5$",
    1000000: r"$Re=1\times10^6$",
}

# Figure 1: CL vs alpha
plt.figure(figsize=(8, 5))
for Re in TARGET_RE:
    df = original[Re][1]
    plt.plot(df["alpha"], df["CL"], linewidth=1.8, label=labels[Re])

plt.xlabel(r"Angle of attack, $\alpha$ [deg]")
plt.ylabel(r"Lift coefficient, $C_L$ [-]")
plt.title(r"$C_L$ versus angle of attack")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS_FOLDER / "Figure1_CL_vs_alpha.png", dpi=300)
plt.show()


# Figure 2: CD vs alpha
plt.figure(figsize=(8, 5))
for Re in TARGET_RE:
    df = original[Re][1]
    plt.plot(df["alpha"], df["CD"], linewidth=1.8, label=labels[Re])

plt.xlabel(r"Angle of attack, $\alpha$ [deg]")
plt.ylabel(r"Drag coefficient, $C_D$ [-]")
plt.title(r"$C_D$ versus angle of attack")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS_FOLDER / "Figure2_CD_vs_alpha.png", dpi=300)
plt.show()


# Figure 3: CL/CD vs alpha
plt.figure(figsize=(8, 5))
for Re in TARGET_RE:
    df = original[Re][1]
    plt.plot(df["alpha"], df["CL_CD"], linewidth=1.8, label=labels[Re])

plt.xlabel(r"Angle of attack, $\alpha$ [deg]")
plt.ylabel(r"Aerodynamic efficiency, $C_L/C_D$ [-]")
plt.title(r"$C_L/C_D$ versus angle of attack")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS_FOLDER / "Figure3_CL_CD_vs_alpha.png", dpi=300)
plt.show()


# ============================================================
# MAXIMUM AERODYNAMIC EFFICIENCY
# ============================================================

summary = []

for Re in TARGET_RE:
    df = original[Re][1].copy()

    valid = df[np.isfinite(df["CL_CD"])].copy()

    # Normally the physically useful maximum is positive CL/CD.
    valid = valid[valid["CD"] > 0]

    idx = valid["CL_CD"].idxmax()

    alpha_max = valid.loc[idx, "alpha"]
    efficiency_max = valid.loc[idx, "CL_CD"]
    CL_at_max = valid.loc[idx, "CL"]
    CD_at_max = valid.loc[idx, "CD"]

    summary.append({
        "Re": Re,
        "alpha_at_max_CL_CD_deg": alpha_max,
        "max_CL_CD": efficiency_max,
        "CL_at_max": CL_at_max,
        "CD_at_max": CD_at_max,
    })

summary_df = pd.DataFrame(summary)
summary_df.to_csv(RESULTS_FOLDER / "maximum_efficiency.csv", index=False)

with open(RESULTS_FOLDER / "max_efficiency.txt", "w", encoding="utf-8") as f:
    f.write("Maximum aerodynamic efficiency\n")
    f.write("================================\n\n")
    f.write(f"Ncrit = {NCRIT}\n\n")

    for row in summary:
        f.write(f"Re = {row['Re']:,}\n")
        f.write(f"Maximum CL/CD = {row['max_CL_CD']:.4f}\n")
        f.write(
            f"Angle of attack at maximum CL/CD = "
            f"{row['alpha_at_max_CL_CD_deg']:.3f} deg\n"
        )
        f.write(f"CL = {row['CL_at_max']:.4f}\n")
        f.write(f"CD = {row['CD_at_max']:.5f}\n\n")

print("\n==============================")
print("MAXIMUM AERODYNAMIC EFFICIENCY")
print("==============================")
print(summary_df.to_string(index=False))


# ============================================================
# SAVE PROCESSED ORIGINAL DATA
# ============================================================

for Re in TARGET_RE:
    df = original[Re][1]
    df.to_csv(
        RESULTS_FOLDER / f"processed_polar_Re{Re}.csv",
        index=False
    )


# ============================================================
# VITERNA / 360 DEGREE POLARS
# ============================================================

if extrapolated:
    plt.figure(figsize=(9, 5))

    for Re in TARGET_RE:
        if Re in extrapolated:
            path, df = extrapolated[Re]

            # Plot CL on left axis
            plt.plot(
                df["alpha"],
                df["CL"],
                linewidth=1.5,
                label=fr"$C_L$, Re={Re:.0e}"
            )

    plt.xlabel(r"Angle of attack, $\alpha$ [deg]")
    plt.ylabel(r"Lift coefficient, $C_L$ [-]")
    plt.title(r"Viterna-extrapolated $C_L$ over $360^\circ$")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(RESULTS_FOLDER / "Figure4_Viterna_CL_360.png", dpi=300)
    plt.show()

    # CD
    plt.figure(figsize=(9, 5))

    for Re in TARGET_RE:
        if Re in extrapolated:
            path, df = extrapolated[Re]
            plt.plot(
                df["alpha"],
                df["CD"],
                linewidth=1.5,
                label=fr"$C_D$, Re={Re:.0e}"
            )

    plt.xlabel(r"Angle of attack, $\alpha$ [deg]")
    plt.ylabel(r"Drag coefficient, $C_D$ [-]")
    plt.title(r"Viterna-extrapolated $C_D$ over $360^\circ$")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(RESULTS_FOLDER / "Figure5_Viterna_CD_360.png", dpi=300)
    plt.show()

    # CL/CD
    plt.figure(figsize=(9, 5))

    for Re in TARGET_RE:
        if Re in extrapolated:
            path, df = extrapolated[Re]

            efficiency = df["CL"] / df["CD"].replace(0, np.nan)

            plt.plot(
                df["alpha"],
                efficiency,
                linewidth=1.5,
                label=fr"$C_L/C_D$, Re={Re:.0e}"
            )

    plt.xlabel(r"Angle of attack, $\alpha$ [deg]")
    plt.ylabel(r"$C_L/C_D$ [-]")
    plt.title(r"Viterna-extrapolated aerodynamic efficiency over $360^\circ$")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(RESULTS_FOLDER / "Figure6_Viterna_CL_CD_360.png", dpi=300)
    plt.show()

else:
    print("\nNo Viterna .plr files were automatically detected.")
    print("Export the two extended polars from QBlade and put them")
    print("in the same folder as this script.")


# ============================================================
# REPORT-READY TEXT
# ============================================================

print("\n\nREPORT NOTES")
print("============")

for row in summary:
    print(
        f"For Re = {row['Re']:,}, the maximum aerodynamic efficiency "
        f"was CL/CD = {row['max_CL_CD']:.3f} at "
        f"alpha = {row['alpha_at_max_CL_CD_deg']:.2f} degrees."
    )

print(
    "\nThe exact discussion of Reynolds-number effects should be based "
    "on the shapes and values in Figures 1-3."
)

print(
    "\nRemember to compare the calculated maximum CL/CD and alpha "
    "with the corresponding Airfoil Tools data, as required in Section 3.3."
)

print("\nDone. Results are saved in:", RESULTS_FOLDER.resolve())
