"""
Audit Intelligence Suite
Treasury, Banking & Quality Control Analytics Platform
"""

import streamlit as st

from src.auth import init_session_state, login, logout, require_auth
from src.config import APP_NAME, APP_TAGLINE, APP_VERSION, TEMPLATES_DIR
from src.pages import (
    render_executive_dashboard,
    render_quality_control,
    render_reports_export,
    render_treasury_banking,
)
from src.theme import DARK_THEME, LIGHT_THEME, get_theme_css
from src.ui.components import render_logo, render_logo_uploader

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()


def render_login():
    theme = DARK_THEME if st.session_state.dark_mode else LIGHT_THEME
    st.markdown(get_theme_css(theme), unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        render_logo(200)
        st.markdown(f'<div class="login-title">{APP_NAME}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="login-subtitle">{APP_TAGLINE}</div>', unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin / auditor / cfo")
            password = st.text_input("Password", type="password", placeholder="audit2024")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            if submitted:
                if login(username, password):
                    st.rerun()
                else:
                    st.error("Invalid credentials. Try admin / audit2024")

        st.caption(f"v{APP_VERSION} | Enterprise Audit Analytics Platform")
        st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar():
    theme = DARK_THEME if st.session_state.dark_mode else LIGHT_THEME

    with st.sidebar:
        render_logo(160)
        st.markdown(f"**{APP_NAME}**")
        st.caption(APP_TAGLINE)
        render_logo_uploader()
        st.divider()

        st.session_state.dark_mode = st.toggle(
            "Dark Mode",
            value=st.session_state.dark_mode,
            help="Toggle between dark and light themes",
        )

        st.caption(f"Signed in as **{st.session_state.username}**")

        pages = {
            "Executive Dashboard": "📊",
            "Treasury & Banking": "🏦",
            "Quality Control": "🔬",
            "Reports & Export": "📄",
        }

        for page, icon in pages.items():
            if st.button(f"{icon}  {page}", use_container_width=True, key=f"nav_{page}"):
                st.session_state.current_page = page

        st.divider()

        if TEMPLATES_DIR.exists():
            st.markdown("**Sample Templates**")
            for tpl in sorted(TEMPLATES_DIR.glob("*.xlsx")):
                with open(tpl, "rb") as f:
                    st.download_button(
                        f"📥 {tpl.stem.replace('_', ' ').title()}",
                        f.read(),
                        tpl.name,
                        key=f"dl_{tpl.name}",
                        use_container_width=True,
                    )

        st.divider()
        if st.button("Sign Out", use_container_width=True):
            logout()
            st.rerun()

        st.caption(f"© 2024 {APP_NAME} v{APP_VERSION}")


def main():
    if not require_auth():
        render_login()
        return

    theme = DARK_THEME if st.session_state.dark_mode else LIGHT_THEME
    st.markdown(get_theme_css(theme), unsafe_allow_html=True)

    render_sidebar()

    page = st.session_state.current_page
    if page == "Executive Dashboard":
        render_executive_dashboard()
    elif page == "Treasury & Banking":
        render_treasury_banking()
    elif page == "Quality Control":
        render_quality_control()
    elif page == "Reports & Export":
        render_reports_export()
    else:
        render_executive_dashboard()


if __name__ == "__main__":
    main()
