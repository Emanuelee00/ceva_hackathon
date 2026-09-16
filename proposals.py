"""Step 4 logic: which candidate cars would close the loading gap, and how
they integrate into the current trip. Pure and testable — no Streamlit here.
"""

from math import atan2, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = radians(lat1), radians(lat2)
    dp, dl = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * atan2(sqrt(a), sqrt(1 - a))


def compute_proposals(candidates: list[dict], trip: dict, lot_loading: float, truck_max: float, limit: int = 8) -> list[dict]:
    stops = trip["stops"]
    stop_cities = {s["city"].strip().lower() for s in stops}

    proposals = []
    for car in candidates:
        new_total = round(lot_loading + car["loadingRatio"], 2)
        if new_total > truck_max:
            continue

        dest = car["destination"]
        if dest["city"].strip().lower() in stop_cities:
            integration, detour_km, stop_added = "On route", 0.0, False
        else:
            nearest = min(haversine_km(s["lat"], s["lng"], dest["lat"], dest["lng"]) for s in stops)
            integration, detour_km, stop_added = "Detour", round(2 * nearest, 1), True

        proposals.append({
            "car": car,
            "newTotal": new_total,
            "gapRemaining": round(truck_max - new_total, 2),
            "integration": integration,
            "detourKm": detour_km,
            "stopAdded": stop_added,
        })

    proposals.sort(key=lambda p: (p["detourKm"], -p["car"]["loadingRatio"]))
    return proposals[:limit]
