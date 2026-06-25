"""Authentication module."""

import streamlit as st

from src.config import DEMO_USERS


def init_session_state():
    defaults = {
        "authenticated": False,
        "username": None,
        "dark_mode": True,
        "bank_statements": None,
        "bank_recon": None,
        "qc_inspection": None,
        "vendor_debit": None,
        "payment_records": None,
        "findings": [],
        "current_page": "Executive Dashboard",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def login(username: str, password: str) -> bool:
    if username in DEMO_USERS and DEMO_USERS[username] == password:
        st.session_state.authenticated = True
        st.session_state.username = username
        return True
    return False


def logout():
    st.session_state.authenticated = False
    st.session_state.username = None


def require_auth():
    init_session_state()
    return st.session_state.authenticated
