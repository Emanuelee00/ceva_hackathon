"""Centralized CEVA brand tokens + shared CSS, injected once from app.py.
Navy/red are lifted from the official logo file (assets/ceva_logo.svg,
2023 CEVA Logistics mark, sourced from Wikimedia Commons) so the palette
reads as one system with the mark in the header. RED is stepped down from
the logo's pure #ff0000 for WCAG AA contrast on filled surfaces (white on
#ff0000 is 4.0:1, under the 4.5:1 text minimum; #d6001c clears 5.4:1 while
reading as the same hue next to the mark).
"""

import base64
from pathlib import Path

import streamlit as st

LOGO_PATH = Path(__file__).parent / "assets" / "ceva_logo_reversed.svg"  # white+red, for the navy header

NAVY = "#1D2546"
ACCENT = "#D6001C"  # kept as ACCENT (not RED) — existing call sites import this name

BG = "#F6F6F4"
SURFACE = "#FFFFFF"
BORDER = "#E3E2DD"

TEXT_PRIMARY = "#181A22"
TEXT_SECONDARY = "#6B6B68"
TEXT_MUTED = "#9A9994"

DOT_ON_ROUTE = "#2E7D46"   # status: good / on-route
DOT_DETOUR = "#B0740A"     # status: detour / needs attention
STATUS_ALERT = ACCENT      # status: under-optimized — always paired with icon + label, never color alone


@st.cache_data
def _logo_data_uri() -> str:
    svg = LOGO_PATH.read_text()
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def logo_data_uri() -> str:
    return _logo_data_uri()


def inject_base_css() -> None:
    st.markdown(
        f"""<link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800;900&display=swap" rel="stylesheet">
        <style>
        .stApp {{ background: {BG}; }}
        h1, h2, h3, .stMarkdown p {{ color: {TEXT_PRIMARY}; }}
        h1, h2, h3, [data-testid="stTab"] p {{
            font-family: "Archivo", sans-serif !important; font-weight: 800 !important;
        }}
        [data-testid="stTab"] {{
            letter-spacing: .05em; text-transform: uppercase; padding-top: 10px;
        }}
        [data-testid="stTab"] p {{ font-size: 13.5px !important; }}
        .stButton button, [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"] {{
            border-radius: 0 !important; font-family: "Archivo", sans-serif; font-weight: 800;
            letter-spacing: .03em; text-transform: uppercase; font-size: 12.5px !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 0 !important; }}

        .ceva-header {{
            display: flex; align-items: center; justify-content: space-between;
            background: {NAVY}; margin: -1rem -5vw 28px -5vw; padding: 30px 5vw;
        }}
        .ceva-header-left {{ display: flex; align-items: center; gap: 18px; }}
        .ceva-header img {{ height: 42px; }}
        .ceva-product {{
            font-family: "Archivo", sans-serif; font-weight: 900; font-size: 20px; color: #fff;
            letter-spacing: .01em; text-transform: uppercase; line-height: 1.1;
        }}
        .ceva-product-sub {{ font-size: 12.5px; color: rgba(255,255,255,.68); margin-top: 3px; }}
        .ceva-demo-tag {{
            font-family: "Archivo", sans-serif; font-size: 11px; font-weight: 800; letter-spacing: .05em;
            text-transform: uppercase; color: #fff; background: {ACCENT};
            padding: 7px 14px;
        }}

        .ceva-steps {{ display: flex; align-items: center; gap: 0; margin: 4px 0 22px 0; }}
        .ceva-step {{ display: flex; align-items: center; gap: 8px; }}
        .ceva-step-dot {{
            width: 20px; height: 20px; border-radius: 50%; flex-shrink: 0;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 700; border: 1.5px solid {BORDER}; color: {TEXT_MUTED};
        }}
        .ceva-step.done .ceva-step-dot {{ background: {NAVY}; border-color: {NAVY}; color: #fff; }}
        .ceva-step.active .ceva-step-dot {{ background: {ACCENT}; border-color: {ACCENT}; color: #fff; }}
        .ceva-step-label {{ font-size: 12.5px; font-weight: 600; color: {TEXT_MUTED}; }}
        .ceva-step.done .ceva-step-label, .ceva-step.active .ceva-step-label {{ color: {TEXT_PRIMARY}; }}
        .ceva-step-arrow {{ color: {BORDER}; margin: 0 14px; font-size: 13px; }}

        .ceva-card {{ border: 1px solid {BORDER}; padding: 16px 18px; background: {SURFACE}; }}

        .ceva-stat-label {{
            font-size: 11px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: {TEXT_SECONDARY};
            font-family: "Archivo", sans-serif;
        }}
        .ceva-stat-value {{ font-size: 30px; font-weight: 700; color: {TEXT_PRIMARY}; line-height: 1.15; margin-top: 2px; }}
        .ceva-stat-value.accent {{ color: {ACCENT}; }}
        .ceva-stat-sub {{ font-size: 12px; color: {TEXT_MUTED}; margin-top: 3px; }}

        .ceva-meter-track {{ background: #EDECE7; height: 7px; overflow: hidden; }}
        .ceva-meter-fill {{ height: 100%; }}

        .ceva-badge {{
            display: inline-flex; align-items: center; gap: 5px; font-size: 10.5px; font-weight: 700;
            letter-spacing: .03em; text-transform: uppercase; padding: 3px 8px;
            border: 1px solid transparent; font-family: "Archivo", sans-serif;
        }}
        .ceva-badge-real {{ color: {DOT_ON_ROUTE}; background: #EAF3EC; border-color: #D3E6D7; }}
        .ceva-badge-mock {{ color: {TEXT_SECONDARY}; background: #F0EFEC; border-color: {BORDER}; }}
        .ceva-badge-estimate {{ color: {DOT_DETOUR}; background: #FBF0DE; border-color: #EEDCB5; }}

        .ceva-empty {{
            border: 1px dashed {BORDER}; padding: 20px; text-align: center;
            color: {TEXT_SECONDARY}; font-size: 13px;
        }}
        </style>""",
        unsafe_allow_html=True,
    )


def stat_tile(label: str, value: str, sub: str = "", accent: bool = False) -> str:
    cls = "ceva-stat-value accent" if accent else "ceva-stat-value"
    sub_html = f'<div class="ceva-stat-sub">{sub}</div>' if sub else ""
    return f'<div class="ceva-stat-label">{label}</div><div class="{cls}">{value}</div>{sub_html}'


def badge(kind: str, text: str) -> str:
    return f'<span class="ceva-badge ceva-badge-{kind}">{text}</span>'
