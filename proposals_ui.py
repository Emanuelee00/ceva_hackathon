"""Step 4 UI: when the loading alert is active, show candidate cars from
the departure compound that would close the gap. Selecting one adds it to
the lot (steps 1 and 3 recompute live on rerun).
"""

import streamlit as st

from loading_check import check_loading
from mock_fleet import MOCK_CARS
from proposals import compute_proposals
from theme import DOT_DETOUR, DOT_ON_ROUTE, TEXT_DIM, TEXT_FAINT, panel_eyebrow

COLUMN_WIDTHS = [1.8, 1, 0.8, 0.8, 0.8, 1.1, 0.9, 0.8, 0.8]
HEADERS = ["Model", "Category", "Load", "Total", "Gap", "Integration", "Detour", "+Stop", ""]


def _dot_label(integration: str) -> str:
    color = DOT_ON_ROUTE if integration == "On route" else DOT_DETOUR
    return (
        f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;'
        f'background:{color};margin-right:6px;"></span>{integration}'
    )


def _select_car(car_id: str, compound: str) -> None:
    ids = st.session_state.get("lot_car_ids", [])
    if car_id not in ids:
        st.session_state.lot_car_ids = ids + [car_id]
    st.session_state.pop(f"lot_editor_{compound}", None)
    st.rerun()


def render_proposals() -> None:
    truck = st.session_state.get("picked_truck")
    lot_loading = st.session_state.get("lot_loading", 0.0)
    if not truck or not st.session_state.get("want_car_suggestions"):
        return
    if not check_loading(lot_loading, truck["maxLoading"])["alert"]:
        return

    compound = st.session_state.get("lot_compound")
    trip = st.session_state.get("lot_trip")
    if not trip:
        return

    lot_ids = set(st.session_state.get("lot_car_ids", []))
    candidates = [c for c in MOCK_CARS if c["compoundId"] == compound and c["status"] == "disponible" and c["id"] not in lot_ids]
    proposals = compute_proposals(candidates, trip, lot_loading, truck["maxLoading"])

    st.divider()
    st.markdown(panel_eyebrow("04", "Cars to add"), unsafe_allow_html=True)
    if not proposals:
        st.markdown('<div class="ceva-empty">No candidate car fits within the truck\'s reference max.</div>', unsafe_allow_html=True)
        return

    with st.container(border=True, key="panel-proposals"):
        for col, label in zip(st.columns(COLUMN_WIDTHS), HEADERS):
            col.markdown(
                f'<span style="white-space:nowrap;font-family:\'IBM Plex Mono\',monospace;font-size:10px;'
                f'letter-spacing:.06em;text-transform:uppercase;color:{TEXT_FAINT};">{label}</span>',
                unsafe_allow_html=True,
            )
        st.markdown('<div class="ceva-row-hairline"></div>', unsafe_allow_html=True)

        for p in proposals:
            car = p["car"]
            cols = st.columns(COLUMN_WIDTHS)
            cols[0].write(car["model"])
            cols[1].markdown(f'<span style="color:{TEXT_DIM}">{car["category"]}</span>', unsafe_allow_html=True)
            cols[2].markdown(f'<span class="ceva-mono">{car["loadingRatio"]:.2f}</span>', unsafe_allow_html=True)
            cols[3].markdown(f'<span class="ceva-mono">{p["newTotal"]:.2f}</span>', unsafe_allow_html=True)
            cols[4].markdown(f'<span class="ceva-mono" style="color:{TEXT_DIM}">{p["gapRemaining"]:.2f}</span>', unsafe_allow_html=True)
            cols[5].markdown(_dot_label(p["integration"]), unsafe_allow_html=True)
            cols[6].markdown(f'<span class="ceva-mono" style="color:{TEXT_DIM}">{p["detourKm"]:.1f}</span>', unsafe_allow_html=True)
            cols[7].markdown(f'<span style="color:{TEXT_DIM}">{"Yes" if p["stopAdded"] else "No"}</span>', unsafe_allow_html=True)
            if cols[8].button("Select", key=f"add_{car['id']}"):
                _select_car(car["id"], compound)
            st.markdown('<div class="ceva-row-hairline"></div>', unsafe_allow_html=True)
