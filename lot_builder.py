"""Step 1 of the dispatcher simulation: pick a compound, check cars into a
lot — the trip (route + stops on the map) is built live from the selected
cars' own destinations, not chosen separately. Live loading total = sum of
checked cars' loadingRatio. This is the "as-if" dispatcher gesture — not
the real CMA CGM software. Truck choice and the alert are separate, later
steps; not wired here.
"""

import pandas as pd
import streamlit as st

from mock_fleet import COMPOUNDS, MOCK_CARS
from theme import ACCENT, TEXT_SECONDARY
from trip_map import render_trip_map


def _cars_table(compound: str, selected_ids: set) -> pd.DataFrame:
    available = [c for c in MOCK_CARS if c["compoundId"] == compound and c["status"] == "disponible"]
    return pd.DataFrame([
        {"select": c["id"] in selected_ids, "id": c["id"], "model": c["model"], "category": c["category"],
         "loadingRatio": c["loadingRatio"], "destination": c["destination"]["city"]}
        for c in available
    ])


def _selected_destinations(ids: list) -> list[dict]:
    by_id = {c["id"]: c for c in MOCK_CARS}
    seen = {}
    for i in ids:
        dest = by_id[i]["destination"]
        seen[dest["city"]] = dest
    return list(seen.values())


def render_lot_builder() -> None:
    st.subheader("1. Compose the lot")
    compound = st.selectbox("Departure compound", COMPOUNDS, key="lot_compound")

    df = _cars_table(compound, set(st.session_state.get("lot_car_ids", [])))
    edited = st.data_editor(
        df, hide_index=True, height=260, key=f"lot_editor_{compound}",
        column_config={
            "select": st.column_config.CheckboxColumn("Pick"),
            "id": st.column_config.TextColumn("VIN"),
            "model": st.column_config.TextColumn("Model"),
            "category": st.column_config.TextColumn("Category"),
            "loadingRatio": st.column_config.NumberColumn("Loading", format="%.2f"),
            "destination": st.column_config.TextColumn("Destination"),
        },
        disabled=["id", "model", "category", "loadingRatio", "destination"],
    )
    selected = edited[edited["select"]]
    st.session_state.lot_car_ids = selected["id"].tolist()

    destinations = _selected_destinations(selected["id"].tolist())
    trip = render_trip_map(compound, destinations)
    st.session_state.lot_trip = trip
    if not trip:
        st.caption("Select at least one car to see its route on the map.")

    total = selected["loadingRatio"].sum()
    st.session_state.lot_loading = total
    st.markdown(
        '<div style="font-family:ui-monospace,monospace;font-size:11px;letter-spacing:.06em;'
        f'color:{TEXT_SECONDARY};margin-top:10px;">LOT LOADING</div>'
        f'<div style="font-family:ui-monospace,monospace;font-size:32px;font-weight:700;'
        f'color:{ACCENT};">{total:.2f}</div>',
        unsafe_allow_html=True,
    )
