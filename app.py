"""Interactive agentic dashboard: chat with the FVL transport analysis via a
local LLM + LangGraph router over a fixed set of deterministic tools, plus a
staged dispatcher simulation (compose a lot, assign a truck, then — later —
an alert) on the "Dispatcher check" tab.
"""

import streamlit as st

from analyze import DEFAULT_PATH, load
from cost_estimate import trip_level_empty_km
from alert_ui import render_loading_alert
from loading_check import LOADING_ALERT_THRESHOLD
from loading_factor_alert import truck_options
from lot_builder import render_lot_builder
from matching_opportunity import build_trips
from proposals_ui import render_proposals
from theme import ACCENT, TEXT_SECONDARY
from truck_picker import render_truck_picker
from underloading_stats import compute_underloading_stats
from agent.graph import build_graph
from agent.tools import methodology

st.set_page_config(page_title="FVL Transport — Agentic Dashboard", layout="wide")


@st.cache_resource
def load_data():
    df = load(DEFAULT_PATH)
    frames = {
        "cost": trip_level_empty_km(df),
        "match": build_trips(df),
        "fleet_raw": df.drop_duplicates(subset="Trip Leg Number"),
    }
    return df, frames


@st.cache_resource
def get_graph():
    df, frames = load_data()
    return build_graph(df, frames)


def render_result(tool: str, result: dict) -> None:
    if tool == "empty_km_cost":
        c1, c2, c3 = st.columns(3)
        c1.metric("Empty km share", f"{result['empty_share']:.1%}")
        c2.metric("All-in cost", f"€{result['cost_allin']:,.0f}")
        c3.metric("CO2", f"{result['co2_t']:,.0f} t")
        st.bar_chart({name: km for name, km in result["top_origins"]})
    elif tool == "matching_opportunity":
        c1, c2 = st.columns(2)
        c1.metric("Matched share (trips)", f"{result['matched_share']:.1%}")
        c2.metric("Matched share (km)", f"{result['matched_km_share']:.1%}")
    elif tool == "geo_mismatch":
        st.metric("Correlation", f"{result['correlation']:.2f}")
        st.write("Over-served:", result["over_served"])
        st.write("Under-served:", result["under_served"])
    elif tool == "fleet_concentration":
        c1, c2 = st.columns(2)
        c1.metric("Top 10% trucks handle", f"{result['top10_share']:.1%}")
        c2.metric("Same-city trips", f"{result['same_city_share']:.1%}")
    elif tool == "delay_analysis":
        st.dataframe(result["rows"])
    elif tool == "loading_factor_alert" and "historical_max" in result:
        c1, c2 = st.columns(2)
        c1.metric("Historical max", result["historical_max"])
        c2.metric("Gap", result["gap"])

    note = methodology(tool, result)
    if note:
        with st.expander("Data & assumptions used"):
            st.markdown(note)


def render_chat() -> None:
    graph = get_graph()
    if "history" not in st.session_state:
        st.session_state.history = []

    for turn in st.session_state.history:
        with st.chat_message(turn["role"]):
            st.write(turn["content"])
            if turn.get("tool") and turn.get("result"):
                render_result(turn["tool"], turn["result"])

    if question := st.chat_input("Ask about empty km, matching, geography, fleet, or delays..."):
        st.session_state.history.append({"role": "user", "content": question})
        with st.spinner("Thinking..."):
            out = graph.invoke({"question": question, "top_n": 10})
        st.session_state.history.append({
            "role": "assistant", "content": out["answer"],
            "tool": out.get("tool"), "result": out.get("result"),
        })
        st.rerun()


def render_dispatcher_form() -> None:
    _, frames = load_data()
    trucks = truck_options(frames["fleet_raw"])

    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        render_lot_builder()
    with col2:
        render_truck_picker(trucks, frames["fleet_raw"])
        st.divider()
        render_loading_alert()
    render_proposals()

    threshold = st.session_state.get("alert_threshold", LOADING_ALERT_THRESHOLD)
    stats = compute_underloading_stats(frames["fleet_raw"], threshold)
    st.caption(
        f"Real-data check: applying this same rule (gap > {threshold:.1f}) to all {stats['n_trips']:,} real 2026 trips "
        f"across {stats['n_trucks']} trucks — {stats['median']['share']:.0%} fall short of their truck's *typical* "
        f"(median) load. Comparing against each truck's single best-ever load instead shows {stats['max']['share']:.0%}, "
        "but that's an upper bound, not a fair benchmark — a truck's best day isn't a realistic target."
    )


def main() -> None:
    st.markdown(
        '<div style="display:flex;align-items:baseline;gap:12px;margin-bottom:4px;">'
        f'<span style="font-size:19px;font-weight:700;color:{ACCENT};letter-spacing:-0.3px;">CEVA</span>'
        f'<span style="font-size:14px;color:{TEXT_SECONDARY};">Transport — Agentic Dashboard</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    tab1, tab2 = st.tabs(["Dispatcher check", "Ask the data"])
    with tab1:
        render_dispatcher_form()
    with tab2:
        render_chat()


if __name__ == "__main__":
    main()
