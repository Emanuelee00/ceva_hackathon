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
MAP_BLUE = "#24D8FF"
MAP_ORIGIN = "#1464F4"

MARKER_CSS = (
    "background:{color};color:#061625;border-radius:50%;width:24px;height:24px;"
    "display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;"
    "font-family:sans-serif;border:2px solid #c5f6ff;box-shadow:0 0 16px #24d8ff99;"
)

OSRM_TRIP_URL = (
    "https://router.project-osrm.org/trip/v1/driving/{coords}"
    "?source=first&roundtrip=false&geometries=geojson&overview=full"
)

MAP_TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
MAP_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

MAP_STYLE = """<style>
.leaflet-container {background:#061625;font-family:Arial,sans-serif;}
.leaflet-tile-pane {filter:invert(1) grayscale(1) sepia(1) hue-rotate(165deg) saturate(2) brightness(.8) contrast(1.12);}
.leaflet-bar {border:1px solid #465263!important;box-shadow:0 3px 12px #0005!important;}
.leaflet-bar a {background:#172331;color:#edf2f7;border-bottom-color:#465263;}
.leaflet-bar a:hover {background:#29394d;color:white;}
.leaflet-control-attribution {background:#142030e8!important;color:#c5d0dc;}
.leaflet-control-attribution a {color:#c5d0dc;}
.leaflet-control-scale-line {background:#142030e8;color:#e3eaf2;border-color:#a1afc0;text-shadow:none;}
</style>"""


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


def _display_map(route_map: folium.Map, key: str, stop_count: int, distance: float | None) -> None:
    st.markdown(
        '<style>.st-key-route-map {background:#091b2e;border:1px solid #245271;'
        'border-top:3px solid #24d8ff;border-radius:10px;padding:16px;'
        'box-shadow:0 8px 28px #071b3030,0 0 18px #24d8ff12;overflow:hidden;}'
        '.st-key-route-map iframe {border:1px solid #245271;border-radius:6px;}'
        '.st-key-route-map [data-testid="stMetricValue"] {color:#e6faff;}'
        '.st-key-route-map [data-testid="stMetricLabel"] p {color:#a3c8df;}'
        '.route-map-title {font-size:11px;font-weight:800;letter-spacing:.12em;'
        'color:#24d8ff;margin-bottom:4px;}</style>',
        unsafe_allow_html=True,
    )
    with st.container(key="route-map"):
        st.markdown('<div class="route-map-title">ROUTE OVERVIEW</div>', unsafe_allow_html=True)
        st_folium(route_map, height=420, use_container_width=True, returned_objects=[], key=key)
        st.markdown(
            '<div style="font-size:11.5px;color:#a3c8df;">'
            f'<span style="color:{MAP_ORIGIN};">&#9679;</span> Departure compound &nbsp;&nbsp; '
            f'<span style="color:{MAP_BLUE};">&#9679;</span> Numbered delivery stops</div>',
            unsafe_allow_html=True,
        )
        stops_column, distance_column = st.columns(2)
        stops_column.metric("Delivery stops", stop_count)
        distance_column.metric("Total distance", f"{distance} km" if distance is not None else "—")


def render_trip_map(compound: str, destinations: list[dict]) -> dict | None:
    origin = COMPOUND_COORDS[compound]
    coords = (origin,) + tuple((d["lat"], d["lng"]) for d in destinations)
    names = [compound.replace("CEVA ", "")] + [d["city"] for d in destinations]

    solved = (_solve_trip(coords) or _fallback_trip(coords)) if destinations else {
        "order": [0], "line": [], "km": None,
    }
    order = solved["order"]

    m = folium.Map(
        location=origin, tiles=MAP_TILES, attr=MAP_ATTRIBUTION,
        control_scale=True, scroll_wheel_zoom=False, zoom_start=6,
    )
    m.get_root().header.add_child(folium.Element(MAP_STYLE))
    for stop_num, idx in enumerate(order):  # 0 = origin, unlabeled
        lat, lng = coords[idx]
        color = MAP_ORIGIN if stop_num == 0 else MAP_BLUE
        label = "" if stop_num == 0 else str(stop_num)
        tooltip = names[idx] if stop_num == 0 else f"{stop_num}. {names[idx]}"
        folium.Marker(
            [lat, lng], tooltip=tooltip,
            icon=folium.DivIcon(html=f'<div style="{MARKER_CSS.format(color=color)}">{label}</div>'),
        ).add_to(m)
    if destinations:
        folium.PolyLine(solved["line"], color=MAP_BLUE, weight=12, opacity=0.12).add_to(m)
        folium.PolyLine(solved["line"], color=MAP_BLUE, weight=7, opacity=0.25).add_to(m)
        folium.PolyLine(solved["line"], color=MAP_BLUE, weight=3, opacity=1).add_to(m)
        m.fit_bounds(list(coords), padding=(35, 35))

    key = "map_" + compound + "_" + "_".join(sorted(names[1:]))
    _display_map(m, key, len(coords) - 1, solved["km"])

    if not destinations:
        return None
    stops = [{"city": names[i], "lat": coords[i][0], "lng": coords[i][1]} for i in order[1:]]
    return {"stops": stops, "totalKm": solved["km"]}
