"""Fleet concentration: how much of the work sits on how many trucks.

The 'Transport Truck Licence Plate' column has 3 anomalous values (each with
thousands of trips, impossible for a single truck) that are almost certainly
placeholders for a missing/unassigned plate, not real trucks. They are
excluded here so the concentration figure reflects real trucks only.
"""

PLACEHOLDER_PLATES = ["TransportTruck_294048", "TransportTruck_359571", "TransportTruck_98598"]


def fleet_concentration(trips) -> dict:
    real = trips[~trips["Transport Truck Licence Plate"].isin(PLACEHOLDER_PLATES)]
    counts = real["Transport Truck Licence Plate"].value_counts()

    n_top = max(1, int(len(counts) * 0.10))
    top10_share = counts.head(n_top).sum() / counts.sum()

    same_city = (
        trips["Departure City"].astype(str).str.strip().str.upper()
        == trips["Delivery City"].astype(str).str.strip().str.upper()
    )

    return {
        "n_real_trucks": len(counts),
        "n_real_trips": len(real),
        "top10_share": top10_share,
        "same_city_n": int(same_city.sum()),
        "same_city_share": same_city.mean(),
    }
