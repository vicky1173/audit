"""Quality Control & Rejection Analytics Engine."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.risk_engine import compute_risk_score


def rejection_trend_analysis(qc_df: pd.DataFrame) -> dict:
    df = qc_df.copy()
    df["Rejection %"] = np_safe_pct(df["Rejected Qty"], df["Inspected Qty"])
    df["Defect Rate"] = df["Rejection %"]

    vendor = df.groupby("Vendor").agg(
        Inspected=("Inspected Qty", "sum"),
        Rejected=("Rejected Qty", "sum"),
    ).reset_index()
    vendor["Rejection %"] = np_safe_pct(vendor["Rejected"], vendor["Inspected"])

    product = df.groupby("Product").agg(
        Inspected=("Inspected Qty", "sum"),
        Rejected=("Rejected Qty", "sum"),
    ).reset_index()
    product["Rejection %"] = np_safe_pct(product["Rejected"], product["Inspected"])

    process = df.groupby("Process").agg(
        Inspected=("Inspected Qty", "sum"),
        Rejected=("Rejected Qty", "sum"),
    ).reset_index()
    process["Rejection %"] = np_safe_pct(process["Rejected"], process["Inspected"])

    monthly = df.groupby(df["Date"].dt.to_period("M")).agg(
        Rejected=("Rejected Qty", "sum"),
        Inspected=("Inspected Qty", "sum"),
    ).reset_index()
    monthly["Date"] = monthly["Date"].astype(str)
    monthly["Rejection %"] = np_safe_pct(monthly["Rejected"], monthly["Inspected"])

    return {
        "vendor": vendor.sort_values("Rejection %", ascending=False),
        "product": product.sort_values("Rejection %", ascending=False),
        "process": process.sort_values("Rejection %", ascending=False),
        "batch": df.groupby("Batch")["Rejected Qty"].sum().reset_index().sort_values("Rejected Qty", ascending=False),
        "monthly_trend": monthly,
        "raw": df,
    }


def np_safe_pct(num, denom):
    n = pd.to_numeric(num, errors="coerce").fillna(0)
    d = pd.to_numeric(denom, errors="coerce").replace(0, np.nan)
    return (n / d * 100).fillna(0).round(2)


def pareto_figure(summary_df: pd.DataFrame, label_col: str, value_col: str, chart_bg: str = "#111827") -> go.Figure:
    df = summary_df.sort_values(value_col, ascending=False).head(15).copy()
    df["Cumulative %"] = df[value_col].cumsum() / df[value_col].sum() * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df[label_col], y=df[value_col], name=value_col, marker_color="#3b82f6"), secondary_y=False)
    fig.add_trace(go.Scatter(x=df[label_col], y=df["Cumulative %"], name="Cumulative %", line=dict(color="#f59e0b", width=2)), secondary_y=True)
    fig.update_layout(title=f"Pareto Analysis — {label_col}", template="plotly_dark", paper_bgcolor=chart_bg, plot_bgcolor=chart_bg, height=420)
    fig.update_yaxes(title_text=value_col, secondary_y=False)
    fig.update_yaxes(title_text="Cumulative %", secondary_y=True, range=[0, 105])
    return fig


def verify_rejected_accounting(qc_df: pd.DataFrame, debit_df: pd.DataFrame, unit_cost: float = 100) -> pd.DataFrame:
    rejected = qc_df.groupby("Vendor").agg(Rejected_Qty=("Rejected Qty", "sum")).reset_index()
    rejected["Rejected Value"] = rejected["Rejected_Qty"] * unit_cost

    debits = debit_df.groupby("Vendor")["Amount"].sum().reset_index().rename(columns={"Amount": "Debit Note Total"})
    merged = rejected.merge(debits, on="Vendor", how="left")
    merged["Debit Note Total"] = merged["Debit Note Total"].fillna(0)
    merged["Unaccounted Value"] = (merged["Rejected Value"] - merged["Debit Note Total"]).clip(lower=0)
    merged["Flag"] = merged["Unaccounted Value"].apply(lambda v: "Missing Debit Note" if v > 0 else "Matched")
    return merged[merged["Flag"] != "Matched"]


def validate_qc_clearance(payment_df: pd.DataFrame) -> pd.DataFrame:
    df = payment_df.copy()
    violations = df[df["Payment Date"] < df["QC Clearance Date"]].copy()
    violations["Risk Classification"] = violations.apply(
        lambda r: "Critical" if (r["QC Clearance Date"] - r["Payment Date"]).days > 7 else "High",
        axis=1,
    )
    return violations


def repeated_vendor_failures(qc_df: pd.DataFrame) -> pd.DataFrame:
    df = qc_df.copy()
    failures = df[df["QC Status"].str.lower().isin(["fail", "failed", "reject", "rejected"])]
    vendor_stats = failures.groupby("Vendor").agg(
        Failure_Count=("QC Status", "count"),
        Total_Rejected=("Rejected Qty", "sum"),
        Avg_Rejection_Pct=("Rejected Qty", lambda x: x.sum()),
    ).reset_index()
    vendor_stats = vendor_stats.rename(columns={"Failure_Count": "Failure Count", "Avg_Rejection_Pct": "Total Rejected Qty"})

    all_vendors = df.groupby("Vendor")["Inspected Qty"].sum().reset_index()
    vendor_stats = vendor_stats.merge(all_vendors, on="Vendor")
    vendor_stats["Vendor Risk Score"] = vendor_stats.apply(
        lambda r: compute_risk_score(
            frequency=r["Failure Count"],
            qc_failures=min(r["Failure Count"] / 5, 1.0),
        ).score,
        axis=1,
    )
    return vendor_stats.sort_values("Vendor Risk Score", ascending=False)


def vendor_heatmap_figure(vendor_stats: pd.DataFrame, chart_bg: str = "#111827") -> go.Figure:
    if vendor_stats.empty:
        fig = go.Figure()
        fig.add_annotation(text="No vendor failure data", showarrow=False)
        fig.update_layout(template="plotly_dark", paper_bgcolor=chart_bg, height=350)
        return fig
    top = vendor_stats.head(10)
    fig = px.imshow(
        top[["Failure Count", "Total Rejected Qty", "Vendor Risk Score"]].values,
        x=["Failures", "Rejected Qty", "Risk Score"],
        y=top["Vendor"].tolist(),
        color_continuous_scale="RdYlGn_r",
        title="Supplier Risk Heatmap",
    )
    fig.update_layout(template="plotly_dark", paper_bgcolor=chart_bg, height=400)
    return fig


def validate_rework_costs(qc_df: pd.DataFrame, labour_rate: float = 25, material_rate: float = 50) -> pd.DataFrame:
    df = qc_df[qc_df["Rework Qty"] > 0].copy()
    if df.empty:
        return pd.DataFrame(columns=["Batch", "Vendor", "Rework Qty", "Expected Cost", "Cost Gap", "Flag"])

    df["Expected Cost"] = df["Rework Qty"] * (labour_rate + material_rate)
    df["Recorded Cost"] = df["Expected Cost"] * 0.7  # simulate partial recording
    df["Cost Gap"] = df["Expected Cost"] - df["Recorded Cost"]
    df["Flag"] = df["Cost Gap"].apply(lambda v: "Understated" if v > 100 else "OK")
    return df[df["Flag"] != "OK"][["Batch", "Vendor", "Rework Qty", "Expected Cost", "Cost Gap", "Flag"]]
