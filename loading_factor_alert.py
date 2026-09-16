"""Dispatcher-facing check: does this trip's entered Loading Factor fall too
far below the truck's own historical maximum? Mirrors the real workflow —
dispatcher enters a truck + loading factor, we compare against that truck's
proven ceiling and flag under-loading.
"""

import pandas as pd

from fleet_analysis import PLACEHOLDER_PLATES

ALERT_GAP = 0.5


def real_trucks(df: pd.DataFrame) -> pd.DataFrame:
    return df[~df["Transport Truck Licence Plate"].isin(PLACEHOLDER_PLATES)]


def historical_max(df: pd.DataFrame, plate: str) -> float:
    rows = df[df["Transport Truck Licence Plate"] == plate]
    return float(rows["Loading Factor"].max())


def suggest_truck(df: pd.DataFrame, entered_lf: float, exclude_plate: str) -> dict | None:
    maxes = real_trucks(df).groupby("Transport Truck Licence Plate")["Loading Factor"].max()
    fits = maxes[(maxes.index != exclude_plate) & (maxes >= entered_lf - ALERT_GAP)]
    if fits.empty:
        return None
    best = fits.sort_values().index[0]
    return {"plate": best, "historical_max": float(fits.loc[best])}


def check_alert(df: pd.DataFrame, plate: str, entered_lf: float) -> dict:
    hist_max = historical_max(df, plate)
    gap = round(hist_max - entered_lf, 2)
    alert = gap > ALERT_GAP
    result = {"plate": plate, "entered_lf": entered_lf, "historical_max": hist_max, "gap": gap, "alert": alert}
    if alert:
        result["suggestion"] = suggest_truck(df, entered_lf, plate)
    return result


def truck_options(trips: pd.DataFrame, min_trips: int = 5, top_n: int = 50, max_loading_cap: float = 10.0) -> list[dict]:
    """Real trucks with enough history for a meaningful max, most-active
    first. Capped at max_loading_cap (the FVL glossary's "general rule"
    capacity) so the picker stays compatible with this simulation's mock
    car scale (calibrated around ~9-10) — trucks above that exist in the
    real data (a truck full of compact cars can legitimately sum past 10)
    but would make "cars to add" impractical to demo here.
    """
    real = real_trucks(trips)
    summary = real.groupby("Transport Truck Licence Plate")["Loading Factor"].agg(maxLoading="max", n_trips="count")
    summary = summary[(summary["n_trips"] >= min_trips) & (summary["maxLoading"] <= max_loading_cap)]
    summary = summary.sort_values("n_trips", ascending=False).head(top_n)
    return [
        {"id": plate, "plate": plate, "maxLoading": round(float(row.maxLoading), 2), "n_trips": int(row.n_trips)}
        for plate, row in summary.iterrows()
    ]
