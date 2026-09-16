"""Extra summary views over the trip data, used as agent tool backends:
empty-km cost broken down by origin, and delivery delay by vehicles/truck.
"""

import pandas as pd

from cost_estimate import ALLIN_COST_PER_KM_EUR, CO2_PER_KM_G, FUEL_COST_PER_KM_EUR


def compute_summary(df, trips) -> dict:
    empty_km = trips["empty_km"].sum()
    total_km = trips["dist_km"].sum()

    by_origin = (
        df.drop_duplicates(subset="Trip Leg Number")
        .dropna(subset=["Trip Distance KM", "Empty Kilometers in the trip"])
        .assign(empty_km=lambda d: d["Empty Kilometers in the trip"] / 1000)
        .groupby("Departure Name")["empty_km"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    return {
        "n_trips": len(trips),
        "total_km": total_km,
        "empty_km": empty_km,
        "empty_share": empty_km / total_km,
        "cost_fuel": empty_km * FUEL_COST_PER_KM_EUR,
        "cost_allin": empty_km * ALLIN_COST_PER_KM_EUR,
        "co2_t": empty_km * CO2_PER_KM_G / 1_000_000,
        "top_origins": list(by_origin.items()),
    }


def origin_empty_share(df: pd.DataFrame, cost_trips: pd.DataFrame, names: list) -> dict:
    """Real empty-km share per named origin — used by the roadmap's
    'scale to more origins' demo, so it shows real numbers, not a promise.
    """
    merged = df.drop_duplicates(subset="Trip Leg Number")[["Trip Leg Number", "Departure Name"]].merge(
        cost_trips[["Trip Leg Number", "dist_km", "empty_km"]], on="Trip Leg Number"
    )
    result = {}
    for name in names:
        sub = merged[merged["Departure Name"] == name]
        total = sub["dist_km"].sum()
        result[name] = round(sub["empty_km"].sum() / total, 4) if total else 0.0
    return result


def delay_by_vehicle_count(df) -> list:
    d = pd.to_datetime(df["Real Delivery Date"], errors="coerce")
    t = pd.to_datetime(df["Target Delivery Date"], errors="coerce")
    dep = pd.to_datetime(df["Departure Real date"], errors="coerce")
    ok = d >= dep

    clean = df.loc[ok, ["Number of Vehicle per Truck"]].copy()
    clean["delay_days"] = (d.loc[ok] - t.loc[ok]).dt.days

    g = clean.groupby("Number of Vehicle per Truck")["delay_days"].agg(
        n_rows="count", mean_delay="mean"
    )
    g["pct_gt7"] = clean.groupby("Number of Vehicle per Truck")["delay_days"].apply(lambda x: (x > 7).mean())
    g = g[g["n_rows"] >= 100].sort_index()
    return list(g.reset_index().itertuples(index=False, name=None))
