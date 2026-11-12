from pathlib import Path
import pandas as pd

DATA_DIR = Path("./projectDocs/wind_turbine_test_data/Original Data")

PRINTOUT_DIR = Path("./projectDocs/wind_turbine_test_data/Increased Wind Speed")
PRINTOUT_DIR.mkdir(parents=True, exist_ok=True)


# Function to increase wind speed of all rows in the "Wind speed"-column by 2%
def increase_wind_speed(df: pd.DataFrame) -> pd.DataFrame:
    # Increase measured wind speed by 2%
    df["Wind speed"] *= 1.02
    return df

# Read file function
def read_file(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, sep="\t", decimal=",", encoding="utf-8-sig")
    # Remove empty columns
    df = df.dropna(axis=1, how="all")
    # Convert all measurement columns to numeric
    for col in df.columns:
        if col != "Time":
            df.loc[:, col] = pd.to_numeric(df[col], errors="coerce")
    df["Time"] = pd.to_datetime(df["Time"], format="%d.%m.%Y %H:%M:%S")
    return df

# Load measurements
files = sorted(DATA_DIR.glob("*.txt"), key=lambda filepath: int(filepath.name.split("_")[1]))

if not files:
    raise FileNotFoundError(
        "No .txt files found in the data directory."
    )

# Dictionary dersom man ønsker å fylle denne med {filnavn: df} for hver fil
# measurements = {}

for filepath in files:
    df = increase_wind_speed(
        read_file(filepath)
        )
    df["Time"] = df["Time"].dt.strftime("%d.%m.%Y %H:%M:%S")
    output_path = PRINTOUT_DIR / filepath.name
    df.to_csv(output_path,
              sep="\t", decimal=",",
              index=False,
              encoding="utf-8-sig"
              )
    print(f"{filepath.name}: {len(df)} samples -> Saved to {output_path.parent.parent.name}/{output_path.parent.name}/")