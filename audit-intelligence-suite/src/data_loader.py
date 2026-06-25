"""Data loading and validation utilities."""

from io import BytesIO
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

from src.config import (
    BANK_RECON_COLS,
    BANK_STATEMENT_COLS,
    PAYMENT_RECORDS_COLS,
    QC_INSPECTION_COLS,
    VENDOR_DEBIT_COLS,
)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _validate_columns(df: pd.DataFrame, required: list[str]) -> Tuple[bool, list[str]]:
    missing = [c for c in required if c not in df.columns]
    return len(missing) == 0, missing


def load_uploaded_file(uploaded_file) -> Optional[pd.DataFrame]:
    if uploaded_file is None:
        return None
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Use .xlsx, .xls, or .csv")
            return None
        return _normalize_columns(df)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


def load_bank_statements(uploaded_file) -> Optional[pd.DataFrame]:
    df = load_uploaded_file(uploaded_file)
    if df is None:
        return None
    ok, missing = _validate_columns(df, BANK_STATEMENT_COLS)
    if not ok:
        st.error(f"Bank Statements missing columns: {', '.join(missing)}")
        return None
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for col in ["Debit", "Credit", "Balance"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def load_bank_recon(uploaded_file) -> Optional[pd.DataFrame]:
    df = load_uploaded_file(uploaded_file)
    if df is None:
        return None
    ok, missing = _validate_columns(df, BANK_RECON_COLS)
    if not ok:
        st.error(f"Bank Reconciliation missing columns: {', '.join(missing)}")
        return None
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    df["Age Days"] = pd.to_numeric(df["Age Days"], errors="coerce").fillna(0).astype(int)
    return df


def load_qc_inspection(uploaded_file) -> Optional[pd.DataFrame]:
    df = load_uploaded_file(uploaded_file)
    if df is None:
        return None
    ok, missing = _validate_columns(df, QC_INSPECTION_COLS)
    if not ok:
        st.error(f"QC Inspection missing columns: {', '.join(missing)}")
        return None
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for col in ["Inspected Qty", "Rejected Qty", "Rework Qty"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def load_vendor_debit(uploaded_file) -> Optional[pd.DataFrame]:
    df = load_uploaded_file(uploaded_file)
    if df is None:
        return None
    ok, missing = _validate_columns(df, VENDOR_DEBIT_COLS)
    if not ok:
        st.error(f"Vendor Debit Notes missing columns: {', '.join(missing)}")
        return None
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    return df


def load_payment_records(uploaded_file) -> Optional[pd.DataFrame]:
    df = load_uploaded_file(uploaded_file)
    if df is None:
        return None
    ok, missing = _validate_columns(df, PAYMENT_RECORDS_COLS)
    if not ok:
        st.error(f"Payment Records missing columns: {', '.join(missing)}")
        return None
    df["Payment Date"] = pd.to_datetime(df["Payment Date"], errors="coerce")
    df["QC Clearance Date"] = pd.to_datetime(df["QC Clearance Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    return df


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Data") -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return buf.getvalue()


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
