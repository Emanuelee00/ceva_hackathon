"""How often does the dispatcher alert's own rule (gap vs. truck's historical
max, threshold 0.5) actually fire across the real 2026 data?

Comparing every trip to a truck's single best-ever Loading Factor
overstates the problem — by definition, most trips fall below a peak.
A percentile-based reference (median) is the defensible headline; the
max-based figure is reported alongside, labeled as an upper bound, not
hidden (criterion 03: disclose the limitation, don't just pick the bigger
number).
"""

import pandas as pd

from fleet_analysis import PLACEHOLDER_PLATES
from loading_check import LOADING_ALERT_THRESHOLD

MIN_TRIPS = 5


def compute_underloading_stats(trips: pd.DataFrame, threshold: float = LOADING_ALERT_THRESHOLD) -> dict:
    real = trips.dropna(subset=["Loading Factor", "Transport Truck Licence Plate"])
    real = real[~real["Transport Truck Licence Plate"].isin(PLACEHOLDER_PLATES)]
    counts = real["Transport Truck Licence Plate"].value_counts()
    qualifying = counts[counts >= MIN_TRIPS].index
    real = real[real["Transport Truck Licence Plate"].isin(qualifying)]

    grp = real.groupby("Transport Truck Licence Plate")["Loading Factor"]
    result = {"n_trips": len(real), "n_trucks": len(qualifying)}
    for label, ref in [("max", grp.transform("max")), ("median", grp.transform("median"))]:
        gap = ref - real["Loading Factor"]
        under = gap > threshold
        result[label] = {"share": round(under.mean(), 4), "mean_gap": round(gap.mean(), 2)}
    return result
