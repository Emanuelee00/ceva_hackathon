"""Step 3 UI: the loading sub-optimization alert card (or a discreet OK
state), recalculated live from the lot + truck picked in steps 1-2. Also
hosts "Auto-optimize" — a real LangGraph cycle (agent/autofill_graph.py)
that repeatedly picks the best-fit car and adds it until the gap closes,
instead of the dispatcher clicking Select one car at a time.
"""

import streamlit as st

from agent.autofill_graph import build_autofill_graph
from loading_check import LOADING_ALERT_THRESHOLD, check_loading
from mock_fleet import MOCK_CARS
from theme import DOT_ON_ROUTE, STATUS_ALERT, TEXT_PRIMARY, TEXT_SECONDARY, stat_tile

STOP_REASON_TEXT = {
    "optimized": "Gap closed.",
    "no_candidates": "Stopped — no remaining candidate car fits without exceeding the truck's reference max.",
    "max_iterations": "Stopped — hit the iteration safety cap.",
}


def _run_autofill(truck: dict, lot_loading: float, threshold: float) -> None:
    compound = st.session_state.get("lot_compound")
    trip = st.session_state.get("lot_trip")
    if not trip:
        return
    cars = [c for c in MOCK_CARS if c["compoundId"] == compound and c["status"] == "disponible"]
    graph = build_autofill_graph(cars, trip)
    out = graph.invoke({
        "lot_car_ids": st.session_state.get("lot_car_ids", []), "lot_loading": lot_loading,
        "truck_max": truck["maxLoading"], "threshold": threshold,
        "added": [], "done": False, "stop_reason": None, "iterations": 0,
    }, config={"recursion_limit": 50})
    st.session_state.lot_car_ids = out["lot_car_ids"]
    st.session_state.autofill_log = {**out, "before_loading": lot_loading, "truck_max": truck["maxLoading"]}
    st.session_state.pop(f"lot_editor_{compound}", None)
    st.rerun()


def _render_autofill_log() -> None:
    log = st.session_state.pop("autofill_log", None)
    if not log:
        return
    before, after, truck_max = log["before_loading"], log["lot_loading"], log["truck_max"]
    with st.container(border=True):
        st.markdown(f"**Auto-optimize — {STOP_REASON_TEXT.get(log['stop_reason'], log['stop_reason'])}**")
        c1, c2, c3 = st.columns(3)
        c1.markdown(stat_tile("Loading — before", f"{before:.2f}"), unsafe_allow_html=True)
        c2.markdown(stat_tile("Loading — after", f"{after:.2f}", accent=True), unsafe_allow_html=True)
        c3.markdown(stat_tile("Gap — after", f"{truck_max - after:.2f}"), unsafe_allow_html=True)
        if log["added"]:
            st.caption("Cars added by the agent, in order:")
            for a in log["added"]:
                st.caption(f"+ {a['model']} ({a['loadingRatio']:.2f}) — running total {a['newTotal']:.2f}")
        else:
            st.caption("No car was added.")


def render_loading_alert() -> None:
    st.subheader("3. Check loading")
    truck = st.session_state.get("picked_truck")
    lot_loading = st.session_state.get("lot_loading", 0.0)
    if not truck:
        st.markdown('<div class="ceva-empty">Assign a truck above first.</div>', unsafe_allow_html=True)
        return

    threshold = st.slider(
        "Alert threshold (gap)", min_value=0.1, max_value=2.0,
        value=LOADING_ALERT_THRESHOLD, step=0.1, key="alert_threshold",
    )
    check = check_loading(lot_loading, truck["maxLoading"], threshold)

    if check["alert"]:
        pct = min(check["lot_loading"] / check["truck_max"], 1.0) * 100 if check["truck_max"] else 0
        with st.container(border=True):
            st.markdown(
                f'<div style="font-size:15px;font-weight:600;color:{TEXT_PRIMARY};">&#9888; Under-optimized trip</div>'
                f'<div style="font-size:13px;color:{TEXT_SECONDARY};margin-top:2px;">'
                f'Truck {truck["plate"]} has spare capacity that could be filled before departure.</div>',
                unsafe_allow_html=True,
            )
            g1, g2 = st.columns([1, 2])
            with g1:
                st.markdown(stat_tile("Gap", f"{check['gap']:.2f}", accent=True), unsafe_allow_html=True)
            with g2:
                st.markdown(
                    '<div style="padding-top:14px;">'
                    f'<div class="ceva-meter-track"><div class="ceva-meter-fill" '
                    f'style="width:{pct:.0f}%;background:{STATUS_ALERT};"></div></div>'
                    f'<div style="font-size:12px;color:{TEXT_SECONDARY};margin-top:7px;">'
                    f'{check["lot_loading"]:.2f} current / {check["truck_max"]:.2f} historical reference — '
                    f'{pct:.0f}% of reference used</div></div>',
                    unsafe_allow_html=True,
                )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("See cars to add", width="stretch"):
                    st.session_state.want_car_suggestions = True
            with c2:
                if st.button("Auto-optimize (agent)", type="primary", width="stretch"):
                    _run_autofill(truck, lot_loading, threshold)
    else:
        st.markdown(
            f'<div class="ceva-card" style="display:flex;align-items:center;gap:9px;">'
            f'<span style="color:{DOT_ON_ROUTE};font-size:16px;">&#10003;</span>'
            f'<span style="font-size:13.5px;color:{TEXT_PRIMARY};">Optimized loading — '
            f'{check["lot_loading"]:.2f} / {check["truck_max"]:.2f} historical reference '
            f'(gap {check["gap"]:.2f})</span></div>',
            unsafe_allow_html=True,
        )

    _render_autofill_log()
