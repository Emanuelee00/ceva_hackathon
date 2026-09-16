"""Quantify the empty-km matching opportunity: for each empty-running trip,
was there already a compatible departure request nearby in time?

This turns "we recommend backhaul matching" into a measured result on the
real 2026 data: proximity = same French department (from the zip code),
timing = a departure within WINDOW_DAYS of the delivery that just emptied
the truck. It's a lower bound (no truck/capacity assignment, just: did the
demand exist), which is the right thing to disclose per criterion 03.
"""

from bisect import bisect_left, bisect_right

import pandas as pd

WINDOW_DAYS = 3


def department(zip_code) -> str:
    return str(zip_code).strip().zfill(5)[:2]


def build_trips(df: pd.DataFrame) -> pd.DataFrame:
    trips = df.drop_duplicates(subset="Trip Leg Number")[
        ["Trip Leg Number", "Departure Zip Code", "Delivery Zip Code", "Departure City", "Delivery City",
         "Departure Real date", "Real Delivery Date", "Empty Kilometers in the trip"]
    ].copy()
    for c in ["Departure Real date", "Real Delivery Date"]:
        trips[c] = pd.to_datetime(trips[c], errors="coerce")
    trips = trips.dropna(subset=["Departure Real date", "Real Delivery Date", "Departure Zip Code", "Delivery Zip Code"])
    trips["dep_dept"] = trips["Departure Zip Code"].apply(department)
    trips["del_dept"] = trips["Delivery Zip Code"].apply(department)
    return trips


def match_opportunity(trips: pd.DataFrame) -> dict:
    dep_index = {d: sorted(sub["Departure Real date"].tolist()) for d, sub in trips.groupby("dep_dept")}
    empty = trips[trips["Empty Kilometers in the trip"] > 0].copy()
    win = pd.Timedelta(days=WINDOW_DAYS)

    matched, examples = [], []
    cols = zip(empty["del_dept"], empty["Real Delivery Date"], empty["Delivery City"])
    for dept, dlv_date, dlv_city in cols:
        cands = dep_index.get(dept)
        is_match = bool(cands) and bisect_right(cands, dlv_date + win) > bisect_left(cands, dlv_date)
        matched.append(is_match)
        if is_match and len(examples) < 5:
            examples.append((dlv_city, dept, dlv_date.date().isoformat()))

    empty["matched"] = matched
    total_empty_km = empty["Empty Kilometers in the trip"].sum() / 1000
    matched_km = empty.loc[empty["matched"], "Empty Kilometers in the trip"].sum() / 1000

    return {
        "window_days": WINDOW_DAYS,
        "n_empty_trips": len(empty),
        "n_matched": int(empty["matched"].sum()),
        "matched_share": empty["matched"].mean(),
        "total_empty_km": total_empty_km,
        "matched_km": matched_km,
        "matched_km_share": matched_km / total_empty_km,
        "examples": examples,
    }
