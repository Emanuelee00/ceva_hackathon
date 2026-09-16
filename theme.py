"""Centralized CEVA brand tokens + shared CSS, injected once from app.py.
Dark "control room" operations-console palette: BG_DEEP/NAVY are a deep
navy console background (not the CEVA logo's own navy, which is lighter —
chosen darker here for a data-console feel). ACCENT is CEVA red, close to
the official logo's pure #ff0000 (assets/ceva_logo_reversed.svg), reserved
for alerts, the active step, and the primary CTA — never used as decor.
Panels are translucent "glass" over that background rather than solid
white cards, per the control-room direction.
"""

import base64
from pathlib import Path

import streamlit as st

LOGO_PATH = Path(__file__).parent / "assets" / "ceva_logo_reversed.svg"
BG_IMAGE_PATH = Path(__file__).parent / "static" / "bg_compound.jpg"  # TODO: drop a compound / car-transporter photo here

BG_DEEP = "#071528"
NAVY = "#0B1E3D"
PANEL = "rgba(255,255,255,0.055)"
PANEL_BORDER = "rgba(255,255,255,0.13)"
ACCENT = "#E2231A"  # kept as ACCENT (not RED) — existing call sites import this name

TEXT_ON_DARK = "#FFFFFF"
TEXT_DIM = "rgba(255,255,255,0.70)"
TEXT_FAINT = "rgba(255,255,255,0.55)"
HAIRLINE = "rgba(255,255,255,0.10)"

# Back-compat aliases — existing call sites (alert_ui.py, proposals_ui.py,
# truck_picker.py, lot_builder.py) import these names; values now point at
# the dark-theme equivalents above instead of introducing a second set of
# imports everywhere.
TEXT_PRIMARY = TEXT_ON_DARK
TEXT_SECONDARY = TEXT_DIM
TEXT_MUTED = TEXT_FAINT
BORDER = HAIRLINE
SURFACE = PANEL
BG = BG_DEEP

DOT_ON_ROUTE = "#7BD69A"   # status: good / on-route
DOT_DETOUR = "#E8B24A"     # status: detour / needs attention
STATUS_ALERT = ACCENT      # status: under-optimized — always paired with icon + label, never color alone


@st.cache_data
def logo_data_uri() -> str:
    svg = LOGO_PATH.read_text()
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def inject_base_css() -> None:
    if BG_IMAGE_PATH.exists():
        app_bg = (
            f'linear-gradient(180deg, rgba(7,21,40,.84) 0%, rgba(7,21,40,.95) 40%, {BG_DEEP} 100%), '
            f'url("app/static/{BG_IMAGE_PATH.name}"); background-size: cover; background-attachment: fixed;'
        )
    else:
        app_bg = f"{BG_DEEP};"

    st.markdown(
        f"""<link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800;900&family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
        .stApp {{ background: {app_bg} color: {TEXT_ON_DARK}; }}
        body, .stMarkdown p, .stCaption, [data-testid="stCaptionContainer"] {{ color: {TEXT_DIM}; }}
        h1, h2, h3, label {{ color: {TEXT_ON_DARK}; }}
        h1, h2, h3, [data-testid="stTab"] p {{
            font-family: "Archivo", sans-serif !important; font-weight: 800 !important;
        }}
        hr {{ border-color: {HAIRLINE} !important; }}

        [data-testid="stTab"] {{
            letter-spacing: .06em; text-transform: uppercase; padding-top: 10px; color: {TEXT_DIM};
        }}
        [data-testid="stTab"] p {{ font-size: 13px !important; }}
        [data-testid="stTab"][aria-selected="true"] p {{ color: {TEXT_ON_DARK} !important; }}

        .stButton button, [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"] {{
            border-radius: 0 !important; font-family: "Archivo", sans-serif; font-weight: 800;
            letter-spacing: .05em; text-transform: uppercase; font-size: 12.5px !important;
        }}
        [data-testid="stBaseButton-secondary"] {{
            background: transparent !important; border: 1px solid {TEXT_ON_DARK} !important; color: {TEXT_ON_DARK} !important;
        }}
        [data-testid="stBaseButton-secondary"]:hover {{
            background: {ACCENT} !important; border-color: {ACCENT} !important; color: #fff !important;
        }}
        .st-key-see_cars_btn button:hover {{
            background: {TEXT_ON_DARK} !important; border-color: {TEXT_ON_DARK} !important; color: {NAVY} !important;
        }}
        [data-testid="stBaseButton-primary"] {{
            background: {ACCENT} !important; border: 1px solid {ACCENT} !important; color: #fff !important;
        }}
        [data-testid="stBaseButton-primary"]:hover {{ opacity: .85; }}

        /* Streamlit 1.63 gives a bordered st.container() no stable testid of its
           own — border-radius/background come from an unpredictable emotion-cache
           class. Give every such container an explicit key="panel-..." (stable
           st-key-panel-* class Streamlit does generate) and target that instead. */
        [class*="st-key-panel-"] {{
            border-radius: 0 !important; background: {PANEL} !important; border: 1px solid {PANEL_BORDER} !important;
        }}
        [data-testid="stChatMessage"] {{
            background: {PANEL}; border: 1px solid {PANEL_BORDER}; border-radius: 0; padding: 14px 16px;
        }}
        [data-testid="stMetricValue"] {{
            font-family: "IBM Plex Mono", monospace !important; font-variant-numeric: tabular-nums;
        }}
        [data-testid="stMetricLabel"] p {{
            font-family: "Archivo", sans-serif !important; font-weight: 700 !important; letter-spacing: .05em;
            text-transform: uppercase; font-size: 11px !important; color: {TEXT_DIM} !important;
        }}

        .ceva-header {{
            display: flex; align-items: center; justify-content: space-between;
            background:
                linear-gradient(90deg, rgba(7,21,40,.90) 0%, rgba(7,21,40,.72) 45%, rgba(7,21,40,.38) 100%),
                url("app/static/ceva_banner.png") center 58% / cover no-repeat,
                {NAVY};
            border-bottom: 1px solid {HAIRLINE};
            margin: -1rem -5vw 28px -5vw; padding: 32px 5vw;
            min-height: 180px; box-sizing: border-box; gap: 24px;
        }}
        .ceva-header-left {{ display: flex; align-items: center; gap: 18px; }}
        .ceva-header img {{ height: 36px; }}
        .ceva-header-rule {{ width: 1px; height: 30px; background: {HAIRLINE}; }}
        .ceva-product {{
            font-family: "Archivo", sans-serif; font-weight: 900; font-size: 21px; color: {TEXT_ON_DARK};
            letter-spacing: .02em; text-transform: uppercase; line-height: 1.1;
        }}
        .ceva-product-sub {{ font-size: 12px; color: {TEXT_DIM}; margin-top: 3px; }}
        .ceva-header-right {{ display: flex; align-items: center; gap: 12px; }}
        .ceva-live-chip {{
            font-family: "IBM Plex Mono", monospace; font-size: 11px; font-weight: 500; letter-spacing: .1em;
            color: {TEXT_ON_DARK}; border: 1px solid {HAIRLINE}; padding: 6px 12px;
        }}
        .ceva-demo-tag {{
            font-family: "Archivo", sans-serif; font-size: 11px; font-weight: 800; letter-spacing: .05em;
            text-transform: uppercase; color: #fff; background: {ACCENT}; padding: 7px 14px;
        }}
        @media (max-width: 800px) {{
            .ceva-header {{ flex-wrap: wrap; min-height: 200px; background-position: center, 65% 58%; }}
            .ceva-header-left {{ gap: 12px; }}
            .ceva-header img {{ height: 28px; }}
            .ceva-product {{ font-size: 17px; }}
            .ceva-product-sub {{ font-size: 11px; }}
        }}

        .ceva-rail {{ margin: 4px 0 26px 0; }}
        .ceva-rail-track {{ height: 2px; background: {HAIRLINE}; margin-bottom: 10px; }}
        .ceva-rail-fill {{ height: 100%; background: {ACCENT}; }}
        .ceva-rail-labels {{ display: flex; justify-content: space-between; }}
        .ceva-rail-label {{
            font-family: "IBM Plex Mono", monospace; font-size: 11px; letter-spacing: .08em;
            text-transform: uppercase; color: {TEXT_FAINT};
        }}
        .ceva-rail-label.done {{ color: {TEXT_ON_DARK}; }}
        .ceva-rail-label.current {{ color: {ACCENT}; }}

        .ceva-eyebrow {{
            font-family: "Archivo", sans-serif; font-weight: 800; font-size: 13px; letter-spacing: .08em;
            text-transform: uppercase; color: {TEXT_ON_DARK};
        }}

        .ceva-card {{ border: 1px solid {PANEL_BORDER}; padding: 16px 18px; background: {PANEL}; }}

        .ceva-stat-label {{
            font-size: 11px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: {TEXT_DIM};
            font-family: "Archivo", sans-serif;
        }}
        .ceva-stat-value {{
            font-family: "IBM Plex Mono", monospace; font-variant-numeric: tabular-nums;
            font-size: 44px; font-weight: 500; color: {TEXT_ON_DARK}; line-height: 1.15; margin-top: 2px;
        }}
        .ceva-stat-value.accent {{ color: {ACCENT}; }}
        .ceva-stat-sub {{ font-size: 12px; color: {TEXT_FAINT}; margin-top: 3px; }}

        .ceva-meter-track {{ background: rgba(255,255,255,.15); height: 7px; overflow: hidden; }}
        .ceva-meter-fill {{ height: 100%; background: {TEXT_ON_DARK}; }}

        .ceva-badge {{
            display: inline-flex; align-items: center; gap: 5px; font-size: 10.5px; font-weight: 700;
            letter-spacing: .03em; text-transform: uppercase; padding: 3px 8px;
            border: 1px solid transparent; font-family: "Archivo", sans-serif; background: transparent;
        }}
        .ceva-badge-real {{ color: {DOT_ON_ROUTE}; border-color: {DOT_ON_ROUTE}; }}
        .ceva-badge-mock {{ color: {TEXT_DIM}; border-color: {HAIRLINE}; }}
        .ceva-badge-estimate {{ color: {DOT_DETOUR}; border-color: {DOT_DETOUR}; }}

        .ceva-empty {{
            border: 1px dashed {HAIRLINE}; padding: 20px; text-align: center;
            color: {TEXT_DIM}; font-size: 13px;
        }}

        .ceva-plate {{
            font-family: "Archivo", sans-serif; font-weight: 900; font-size: 26px; color: {TEXT_ON_DARK};
            letter-spacing: .01em; font-variant-numeric: tabular-nums;
        }}
        .ceva-plate-sub {{ font-size: 12.5px; color: {TEXT_DIM}; margin-top: 4px; }}

        .ceva-chip {{
            display: inline-flex; align-items: center; font-family: "IBM Plex Mono", monospace; font-size: 11px;
            font-weight: 600; letter-spacing: .08em; text-transform: uppercase; padding: 4px 10px;
        }}
        .ceva-chip-alert {{ background: {ACCENT}; color: #fff; }}
        .ceva-chip-ok {{ border: 1px solid {DOT_ON_ROUTE}; color: {DOT_ON_ROUTE}; }}

        .ceva-alert-panel {{ background: rgba(226,35,26,.13); border: 1px solid rgba(226,35,26,.5); padding: 22px 24px; }}
        .ceva-ok-panel {{
            background: {PANEL}; border: 1px solid {HAIRLINE}; padding: 18px 22px;
            display: flex; align-items: center; gap: 12px;
        }}
        .ceva-alert-title {{
            font-family: "Archivo", sans-serif; font-weight: 900; font-size: 26px; text-transform: uppercase;
            color: {TEXT_ON_DARK}; margin-top: 10px;
        }}
        .ceva-gap-value {{
            font-family: "IBM Plex Mono", monospace; font-weight: 500; font-size: 44px; color: {ACCENT};
            font-variant-numeric: tabular-nums; line-height: 1;
        }}

        .ceva-row-hairline {{ border-bottom: 1px solid {HAIRLINE}; margin: 6px 0; }}
        .ceva-mono {{ font-family: "IBM Plex Mono", monospace; font-variant-numeric: tabular-nums; }}
        </style>""",
        unsafe_allow_html=True,
    )


def stat_tile(label: str, value: str, sub: str = "", accent: bool = False) -> str:
    cls = "ceva-stat-value accent" if accent else "ceva-stat-value"
    sub_html = f'<div class="ceva-stat-sub">{sub}</div>' if sub else ""
    return f'<div class="ceva-stat-label">{label}</div><div class="{cls}">{value}</div>{sub_html}'


def badge(kind: str, text: str) -> str:
    return f'<span class="ceva-badge ceva-badge-{kind}">{text}</span>'


def panel_eyebrow(number: str, title: str, badge_html: str = "") -> str:
    return (
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        f'<span class="ceva-eyebrow">{number} — {title}</span>{badge_html}</div>'
    )
