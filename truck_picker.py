"""Step 2 of the dispatcher simulation: pick a real truck (real license
plate, real historical max Loading Factor from the 2026 FVL data), see its
maxLoading next to the lot's current loading, and its real trip history.
Minimal on purpose — this step doesn't alert or suggest anything, that's
step 3.
"""

import pandas as pd
import streamlit as st

from theme import badge, stat_tile


def _truck_history(trips: pd.DataFrame, plate: str, limit: int = 15) -> pd.DataFrame:
    rows = trips[trips["Transport Truck Licence Plate"] == plate][["Departure Real date", "Loading Factor"]]
    rows = rows.dropna().sort_values("Departure Real date", ascending=False).head(limit)
    rows["Departure Real date"] = pd.to_datetime(rows["Departure Real date"], errors="coerce").dt.date
    return rows.rename(columns={"Departure Real date": "Date", "Loading Factor": "Loading"})


def render_truck_picker(trucks: list[dict], trips: pd.DataFrame) -> None:
    h1, h2 = st.columns([3, 1])
    h1.subheader("2. Assign a truck")
    h2.markdown(
        f'<div style="text-align:right;margin-top:8px;">{badge("real", "Real fleet data")}</div>',
        unsafe_allow_html=True,
    )
    labels = {t["id"]: f"{t['plate']} (max {t['maxLoading']}, {t['n_trips']} trips on record)" for t in trucks}
    truck_id = st.selectbox("Truck", list(labels), format_func=lambda i: labels[i], key="picked_truck_id")
    truck = next(t for t in trucks if t["id"] == truck_id)
    st.session_state.picked_truck = truck

    with st.container(border=True):
        st.markdown(f"**{truck['plate']}** · real truck, {truck['n_trips']} trips in the 2026 FVL data")
        lot_loading = st.session_state.get("lot_loading", 0.0)
        c1, c2 = st.columns(2)
        c1.markdown(stat_tile("Lot loading", f"{lot_loading:.2f}"), unsafe_allow_html=True)
        c2.markdown(
            stat_tile("Truck max (historical reference)", f"{truck['maxLoading']:.2f}"),
            unsafe_allow_html=True,
        )

    with st.expander(f"Trip history — {truck['plate']} (most recent {min(15, truck['n_trips'])})"):
        st.caption("Historical reference only — the highest Loading Factor this truck has recorded, not a certified physical capacity.")
        st.dataframe(_truck_history(trips, truck["plate"]), hide_index=True, width="stretch")
