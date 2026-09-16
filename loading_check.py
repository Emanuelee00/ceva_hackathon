"""Step 3: alert the dispatcher when the assigned truck is under-filled
relative to its own maxLoading. This is the core value-add — kept as pure,
UI-free logic so the threshold and the rule are easy to find and change.
"""

LOADING_ALERT_THRESHOLD = 0.5


def check_loading(lot_loading: float, truck_max: float, threshold: float = LOADING_ALERT_THRESHOLD) -> dict:
    gap = round(truck_max - lot_loading, 2)
    return {
        "lot_loading": lot_loading,
        "truck_max": truck_max,
        "gap": gap,
        "alert": gap > threshold,
    }
