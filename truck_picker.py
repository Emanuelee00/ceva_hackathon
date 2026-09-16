"""Step 2 of the dispatcher simulation: pick a real truck (real license
plate, real historical max Loading Factor from the 2026 FVL data), see its
maxLoading next to the lot's current loading, and its real trip history.
Minimal on purpose — this step doesn't alert or suggest anything, that's
step 3.
"""

import pandas as pd
import streamlit as st

from theme import BORDER, TEXT_PRIMARY, TEXT_SECONDARY


def _truck_history(trips: pd.DataFrame, plate: str, limit: int = 15) -> pd.DataFrame:
    rows = trips[trips["Transport Truck Licence Plate"] == plate][["Departure Real date", "Loading Factor"]]
    rows = rows.dropna().sort_values("Departure Real date", ascending=False).head(limit)
    rows["Departure Real date"] = pd.to_datetime(rows["Departure Real date"], errors="coerce").dt.date
    return rows.rename(columns={"Departure Real date": "Date", "Loading Factor": "Loading"})


def render_truck_picker(trucks: list[dict], trips: pd.DataFrame) -> None:
    st.subheader("2. Assign a truck")
    labels = {t["id"]: f"{t['plate']} (max {t['maxLoading']}, {t['n_trips']} trips on record)" for t in trucks}
    truck_id = st.selectbox("Truck", list(labels), format_func=lambda i: labels[i], key="picked_truck_id")
    truck = next(t for t in trucks if t["id"] == truck_id)
    st.session_state.picked_truck = truck

    st.markdown(
        f'<div style="border:1px solid {BORDER};border-radius:8px;padding:12px 16px;margin:10px 0;font-size:13.5px;">'
        f'<b>{truck["plate"]}</b> · real truck, {truck["n_trips"]} trips in the 2026 FVL data'
        "</div>",
        unsafe_allow_html=True,
    )

    lot_loading = st.session_state.get("lot_loading", 0.0)
    c1, c2 = st.columns(2)
    for col, label, value in ((c1, "LOT LOADING", lot_loading), (c2, "TRUCK MAX LOADING", truck["maxLoading"])):
        with col:
            st.markdown(
                f'<div style="font-family:ui-monospace,monospace;font-size:11px;letter-spacing:.06em;'
                f'color:{TEXT_SECONDARY};">{label}</div>'
                f'<div style="font-family:ui-monospace,monospace;font-size:26px;font-weight:700;'
                f'color:{TEXT_PRIMARY};">{value:.2f}</div>',
                unsafe_allow_html=True,
            )

    with st.expander(f"Trip history — {truck['plate']} (most recent {min(15, truck['n_trips'])})"):
        st.dataframe(_truck_history(trips, truck["plate"]), hide_index=True, width="stretch")
