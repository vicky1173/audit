"""Reusable Streamlit UI components."""

import base64
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

from src.config import APP_NAME, APP_TAGLINE, LOGO_PATH
from src.risk_engine import risk_level_color

CUSTOM_LOGO_KEY = "custom_logo_bytes"


def get_logo_bytes() -> bytes | None:
    if st.session_state.get(CUSTOM_LOGO_KEY):
        return st.session_state[CUSTOM_LOGO_KEY]
    if LOGO_PATH.exists():
        return LOGO_PATH.read_bytes()
    return None


def get_logo_base64() -> str:
    data = get_logo_bytes()
    if data:
        return base64.b64encode(data).decode()
    return ""


def render_logo(width: int = 180):
    b64 = get_logo_base64()
    if b64:
        st.image(f"data:image/png;base64,{b64}", width=width)
    else:
        st.markdown(f"### 🔷 {APP_NAME}")


def render_logo_uploader():
    st.caption("Replace with your company logo")
    uploaded = st.file_uploader(
        "Your logo",
        type=["png", "jpg", "jpeg", "svg", "webp"],
        key="logo_upload",
        label_visibility="collapsed",
    )
    if uploaded is not None:
        st.session_state[CUSTOM_LOGO_KEY] = uploaded.getvalue()
        st.success("Logo updated")
    if st.session_state.get(CUSTOM_LOGO_KEY) and st.button("Reset to default logo", use_container_width=True):
        st.session_state.pop(CUSTOM_LOGO_KEY, None)
        st.rerun()


def render_audit_module_checklist(modules: list[dict]):
    for module in modules:
        items_html = "".join(
            f'<div class="audit-module-item">• {item}</div>' for item in module["items"]
        )
        st.markdown(
            f"""
            <table class="audit-module-table">
                <thead>
                    <tr>
                        <th style="width:56px">#</th>
                        <th style="width:220px">Category</th>
                        <th>Audit Procedures</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="audit-module-id">{module["id"]}</td>
                        <td class="audit-module-title">{module["title"]}</td>
                        <td>{items_html}</td>
                    </tr>
                </tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )


def render_kpi_row(kpis: list[dict]):
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        with col:
            delta = kpi.get("delta")
            delta_color = kpi.get("delta_color", "normal")
            st.metric(
                label=kpi["label"],
                value=kpi["value"],
                delta=delta,
                delta_color=delta_color,
            )


def render_kpi_cards_html(kpis: list[dict]):
    cards_html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin-bottom:1.5rem;">'
    for kpi in kpis:
        delta_html = ""
        if kpi.get("delta"):
            color = "#10b981" if not str(kpi["delta"]).startswith("-") else "#ef4444"
            delta_html = f'<div class="kpi-delta" style="color:{color}">{kpi["delta"]}</div>'
        cards_html += f"""
        <div class="kpi-card">
            <div class="kpi-value">{kpi['value']}</div>
            <div class="kpi-label">{kpi['label']}</div>
            {delta_html}
        </div>"""
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)


def risk_gauge_figure(score: float, title: str = "Risk Score", chart_bg: str = "#111827") -> go.Figure:
    color = risk_level_color(
        "Critical Risk" if score >= 75 else "High Risk" if score >= 50 else "Medium Risk" if score >= 25 else "Low Risk"
    )
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 25], "color": "rgba(16,185,129,0.3)"},
                {"range": [25, 50], "color": "rgba(245,158,11,0.3)"},
                {"range": [50, 75], "color": "rgba(249,115,22,0.3)"},
                {"range": [75, 100], "color": "rgba(239,68,68,0.3)"},
            ],
        },
    ))
    fig.update_layout(template="plotly_dark", paper_bgcolor=chart_bg, height=280, margin=dict(t=50, b=20))
    return fig


def risk_matrix_figure(matrix: pd.DataFrame, chart_bg: str = "#111827") -> go.Figure:
    fig = go.Figure(data=go.Heatmap(
        z=matrix.values,
        x=matrix.columns.tolist(),
        y=matrix.index.tolist(),
        colorscale="RdYlGn_r",
        text=matrix.values,
        texttemplate="%{text}",
    ))
    fig.update_layout(
        title="Risk Matrix (Impact × Likelihood)",
        xaxis_title="Likelihood",
        yaxis_title="Impact",
        template="plotly_dark",
        paper_bgcolor=chart_bg,
        height=400,
    )
    return fig


def render_aggrid(df: pd.DataFrame, height: int = 400, key: str = "grid"):
    if df.empty:
        st.info("No data to display.")
        return None

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(filterable=True, sortable=True, resizable=True)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=15)
    gb.configure_grid_options(domLayout="normal")

    if "Risk Level" in df.columns:
        cell_style = JsCode("""
        function(params) {
            if (params.value === 'Critical Risk') return {backgroundColor: '#fef2f2', color: '#991b1b'};
            if (params.value === 'High Risk') return {backgroundColor: '#fff7ed', color: '#9a3412'};
            if (params.value === 'Medium Risk') return {backgroundColor: '#fffbeb', color: '#92400e'};
            if (params.value === 'Low Risk') return {backgroundColor: '#ecfdf5', color: '#065f46'};
            return {};
        }
        """)
        gb.configure_column("Risk Level", cellStyle=cell_style)

    if "Flag" in df.columns:
        flag_style = JsCode("""
        function(params) {
            if (params.value && params.value !== 'OK' && params.value !== 'Matched') {
                return {backgroundColor: '#fef2f2', color: '#991b1b', fontWeight: 'bold'};
            }
            return {};
        }
        """)
        gb.configure_column("Flag", cellStyle=flag_style)

    gb.configure_side_bar()
    grid_options = gb.build()
    return AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.NO_UPDATE,
        height=height,
        theme="streamlit",
        key=key,
        allow_unsafe_jscode=True,
    )


def section_header(title: str):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", stats: list[dict] | None = None):
    stats_html = ""
    if stats:
        stats_html = '<div class="hero-stats">' + "".join(
            f'<div class="hero-stat"><div class="hero-stat-value">{s["value"]}</div>'
            f'<div class="hero-stat-label">{s["label"]}</div></div>'
            for s in stats
        ) + "</div>"

    st.markdown(f"""
    <div class="header-banner">
        <h1>{title}</h1>
        <p>{subtitle or APP_TAGLINE}</p>
        {stats_html}
    </div>
    """, unsafe_allow_html=True)
