"""Sanity-check the FVL transport CSV before picking a hackathon problem.

Usage:
    make run
    uv run python analyze.py data/csv/fvl_transport_2026.csv
"""

import sys

import pandas as pd

DEFAULT_PATH = "data/csv/fvl_transport_2026.csv"


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"Total rows: {len(df)}")
    print(f"Columns: {df.columns.tolist()}\n")
    return df


def check_empty_km(df: pd.DataFrame) -> None:
    ek = df["Empty Kilometers in the trip"]
    dist = df["Trip Distance KM"]
    ratio = ek / dist

    print("--- EMPTY KM vs TRIP DISTANCE ---")
    print(ek.describe(), "\n")
    print(dist.describe(), "\n")
    print("Empty/distance ratio:\n", ratio.describe())
    print("Share of rows with empty > total distance:", (ek > dist).mean())
    print("Overall empty-km share:", round(ek.sum() / dist.sum(), 4), "\n")


def check_loading_factor(df: pd.DataFrame) -> None:
    lf = df["Loading Factor"]
    vpt = df["Number of Vehicle per Truck"]

    print("--- LOADING FACTOR ---")
    print(lf.describe(), "\n")
    print("Number of Vehicle per Truck (top values):\n", vpt.value_counts().head(10))
    print("Share of rows with LoadingFactor > VehiclePerTruck:", (lf > vpt).mean(), "\n")


def check_dates(df: pd.DataFrame) -> None:
    cols = ["Departure Real date", "Real Delivery Date", "Target Delivery Date"]
    for c in cols:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    imposs_delivery = (df["Real Delivery Date"] < df["Departure Real date"]).mean()
    target_before_dep = (df["Target Delivery Date"] < df["Departure Real date"]).mean()

    print("--- DATE QUALITY ---")
    print("Share of real delivery BEFORE departure:", round(imposs_delivery, 4))
    print("Share of target BEFORE departure:", round(target_before_dep, 4))
    print("Share of unparseable dates:\n", df[cols].isna().mean())

    ok = df["Real Delivery Date"] >= df["Departure Real date"]
    delay = (df.loc[ok, "Real Delivery Date"] - df.loc[ok, "Target Delivery Date"]).dt.days
    print("\nDelay vs target (days), consistent rows:\n", delay.describe())


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    df = load(path)
    check_empty_km(df)
    check_loading_factor(df)
    check_dates(df)


if __name__ == "__main__":
    main()
