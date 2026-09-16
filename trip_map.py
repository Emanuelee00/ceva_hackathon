"""Leaflet map (via folium) for the trip built from the cars currently
selected in the lot: the compound is the unlabeled origin (stop 0), then
each distinct selected destination is numbered from 1, ordered and
connected by a road-following route (OSRM's Trip service solves the
visiting order), with stop count and total km alongside. No car selected
-> no trip.
"""

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

from mock_fleet import COMPOUND_COORDS
from proposals import haversine_km
from theme import ACCENT, NAVY, TEXT_SECONDARY

MARKER_CSS = (
    "background:{color};color:#fff;border-radius:50%;width:24px;height:24px;"
    "display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;"
    "font-family:sans-serif;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.3);"
)

OSRM_TRIP_URL = (
    "https://router.project-osrm.org/trip/v1/driving/{coords}"
    "?source=first&roundtrip=false&geometries=geojson&overview=full"
)

DARK_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
DARK_TILES_ATTR = "Esri, HERE, Garmin, OpenStreetMap contributors"


@st.cache_data(ttl=3600)
def _solve_trip(coords: tuple) -> dict | None:
    """Optimal visiting order + road geometry + distance through `coords`
    (origin first), via the public OSRM Trip service. None if unreachable
    — caller falls back to a straight-line, input-order route.
    """
    coord_str = ";".join(f"{lng},{lat}" for lat, lng in coords)
    try:
        resp = requests.get(OSRM_TRIP_URL.format(coords=coord_str), timeout=5)
        resp.raise_for_status()
        data = resp.json()
        trip = data["trips"][0]
        order = sorted(range(len(coords)), key=lambda i: data["waypoints"][i]["waypoint_index"])
        line = [(lat, lng) for lng, lat in trip["geometry"]["coordinates"]]
        return {"order": order, "line": line, "km": round(trip["distance"] / 1000, 1)}
    except (requests.RequestException, KeyError, IndexError):
        return None


def _fallback_trip(coords: tuple) -> dict:
    km = sum(haversine_km(*coords[i], *coords[i + 1]) for i in range(len(coords) - 1))
    return {"order": list(range(len(coords))), "line": list(coords), "km": round(km, 1)}


def render_trip_map(compound: str, destinations: list[dict]) -> dict | None:
    if not destinations:
        return None
    origin = COMPOUND_COORDS[compound]
    coords = (origin,) + tuple((d["lat"], d["lng"]) for d in destinations)
    names = [compound.replace("CEVA ", "")] + [d["city"] for d in destinations]

    solved = _solve_trip(coords) or _fallback_trip(coords)
    order = solved["order"]

    m = folium.Map(location=origin, tiles=DARK_TILES, attr=DARK_TILES_ATTR)
    for stop_num, idx in enumerate(order):  # 0 = origin, unlabeled
        lat, lng = coords[idx]
        color = NAVY if stop_num == 0 else ACCENT
        label = "" if stop_num == 0 else str(stop_num)
        tooltip = names[idx] if stop_num == 0 else f"{stop_num}. {names[idx]}"
        folium.Marker(
            [lat, lng], tooltip=tooltip,
            icon=folium.DivIcon(html=f'<div style="{MARKER_CSS.format(color=color)}">{label}</div>'),
        ).add_to(m)
    folium.PolyLine(solved["line"], color=ACCENT, weight=3, opacity=0.8).add_to(m)
    m.fit_bounds(list(coords), padding=(24, 24))

    col1, col2 = st.columns([2, 1])
    with col1:
        key = "map_" + compound + "_" + "_".join(sorted(names[1:]))
        st_folium(m, height=280, width=None, returned_objects=[], key=key)
        st.markdown(
            f'<div style="font-size:11.5px;color:{TEXT_SECONDARY};margin-top:4px;">'
            f'<span style="color:{NAVY};">&#9679;</span> Origin (compound) &nbsp;&nbsp; '
            f'<span style="color:{ACCENT};">&#9679;</span> Numbered delivery stops, in visiting order</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.metric("Stops", len(coords) - 1)
        st.metric("Total distance", f"{solved['km']} km")

    stops = [{"city": names[i], "lat": coords[i][0], "lng": coords[i][1]} for i in order[1:]]
    return {"stops": stops, "totalKm": solved["km"]}
