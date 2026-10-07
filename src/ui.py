from __future__ import annotations

import streamlit as st


def apply_page_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #17212b;
            --muted: #667085;
            --line: #e4e9ef;
            --surface: #ffffff;
            --accent: #3157d5;
        }
        .stApp { background: #f5f7fa; color: var(--ink); }
        .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 4rem; }
        [data-testid="stHeader"] { background: rgba(245,247,250,.86); }
        [data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            box-shadow: 0 4px 16px rgba(26, 42, 65, .04);
        }
        [data-testid="stMetricLabel"] { color: var(--muted); }
        [data-testid="stMetricValue"] { color: var(--ink); }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface);
            border-color: var(--line);
            border-radius: 16px;
        }
        .dashboard-kicker {
            color: var(--accent);
            font-size: .82rem;
            font-weight: 750;
            letter-spacing: .08em;
            margin-bottom: .35rem;
        }
        .dashboard-title {
            color: var(--ink);
            font-size: clamp(2rem, 4vw, 3.3rem);
            font-weight: 800;
            line-height: 1.12;
            letter-spacing: -.04em;
            margin: 0;
        }
        .dashboard-subtitle {
            color: var(--muted);
            font-size: 1rem;
            margin: .7rem 0 1.4rem;
        }
        .section-title {
            color: var(--ink);
            font-size: 1.28rem;
            font-weight: 760;
            margin: .2rem 0 .1rem;
        }
        .section-note { color: var(--muted); font-size: .9rem; margin-bottom: .8rem; }
        .status-chip {
            display: inline-block;
            background: #e9efff;
            color: #2847ad;
            border-radius: 999px;
            font-size: .82rem;
            font-weight: 700;
            padding: .32rem .68rem;
            margin-right: .35rem;
        }
        @media (max-width: 780px) {
            .block-container { padding-top: 1.2rem; }
            .dashboard-title { font-size: 2rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, note: str | None = None) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if note:
        st.markdown(f'<div class="section-note">{note}</div>', unsafe_allow_html=True)


def format_number(value: float | int | None, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}"
