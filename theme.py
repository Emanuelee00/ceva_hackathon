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

LOGO_PATH = Path(__file__).parent / "assets" / "ceva_logo.svg"

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
        f"""<style>
        .stApp {{ background: {BG}; }}
        h1, h2, h3, .stMarkdown p {{ color: {TEXT_PRIMARY}; }}
        [data-testid="stTabs"] button[role="tab"] {{ font-size: 14.5px; font-weight: 600; }}

        .ceva-header {{
            display: flex; align-items: center; justify-content: space-between;
            padding-bottom: 14px; margin-bottom: 6px; border-bottom: 1px solid {BORDER};
        }}
        .ceva-header-left {{ display: flex; align-items: center; gap: 14px; }}
        .ceva-header img {{ height: 30px; }}
        .ceva-product {{ font-size: 15px; font-weight: 600; color: {TEXT_PRIMARY}; letter-spacing: -0.2px; }}
        .ceva-product-sub {{ font-size: 12.5px; color: {TEXT_SECONDARY}; margin-top: 1px; }}
        .ceva-demo-tag {{
            font-size: 11px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase;
            color: {NAVY}; background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 4px;
            padding: 4px 9px;
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

        .ceva-card {{ border: 1px solid {BORDER}; border-radius: 8px; padding: 16px 18px; background: {SURFACE}; }}

        .ceva-stat-label {{
            font-size: 11px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: {TEXT_SECONDARY};
        }}
        .ceva-stat-value {{ font-size: 30px; font-weight: 700; color: {TEXT_PRIMARY}; line-height: 1.15; margin-top: 2px; }}
        .ceva-stat-value.accent {{ color: {ACCENT}; }}
        .ceva-stat-sub {{ font-size: 12px; color: {TEXT_MUTED}; margin-top: 3px; }}

        .ceva-meter-track {{ background: #EDECE7; border-radius: 3px; height: 7px; overflow: hidden; }}
        .ceva-meter-fill {{ height: 100%; border-radius: 3px; }}

        .ceva-badge {{
            display: inline-flex; align-items: center; gap: 5px; font-size: 10.5px; font-weight: 600;
            letter-spacing: .03em; text-transform: uppercase; padding: 3px 8px; border-radius: 4px;
            border: 1px solid transparent;
        }}
        .ceva-badge-real {{ color: {DOT_ON_ROUTE}; background: #EAF3EC; border-color: #D3E6D7; }}
        .ceva-badge-mock {{ color: {TEXT_SECONDARY}; background: #F0EFEC; border-color: {BORDER}; }}
        .ceva-badge-estimate {{ color: {DOT_DETOUR}; background: #FBF0DE; border-color: #EEDCB5; }}

        .ceva-empty {{
            border: 1px dashed {BORDER}; border-radius: 8px; padding: 20px; text-align: center;
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
