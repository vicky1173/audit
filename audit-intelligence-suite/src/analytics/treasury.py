"""Treasury & Banking Audit Analytics Engine."""

from typing import Optional

import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.risk_engine import compute_risk_score, score_dataframe


def analyze_aging(recon_df: pd.DataFrame) -> dict:
    df = recon_df.copy()
    buckets = {
        "30+ Days": (df["Age Days"] >= 30).sum(),
        "60+ Days": (df["Age Days"] >= 60).sum(),
        "90+ Days": (df["Age Days"] >= 90).sum(),
        "180+ Days": (df["Age Days"] >= 180).sum(),
    }

    def priority(age):
        if age >= 180:
            return "Critical"
        if age >= 90:
            return "High"
        if age >= 60:
            return "Medium"
        if age >= 30:
            return "Low"
        return "Normal"

    def action(age):
        if age >= 180:
            return "Escalate to CFO — immediate write-off review"
        if age >= 90:
            return "Treasury manager sign-off required"
        if age >= 60:
            return "Investigate root cause and assign owner"
        if age >= 30:
            return "Monitor and reconcile within 15 days"
        return "Within policy"

    df["Priority"] = df["Age Days"].apply(priority)
    df["Recommended Action"] = df["Age Days"].apply(action)
    df["Risk Score"] = df.apply(
        lambda r: compute_risk_score(amount=r["Amount"], age_days=r["Age Days"]).score, axis=1
    )

    heatmap_data = df.groupby(["Status", pd.cut(df["Age Days"], bins=[0, 30, 60, 90, 180, 999], labels=["0-30", "31-60", "61-90", "91-180", "180+"])])["Amount"].sum().unstack(fill_value=0)

    trend = df.groupby(df["Date"].dt.to_period("M"))["Amount"].sum().reset_index()
    trend["Date"] = trend["Date"].astype(str)

    return {
        "summary": buckets,
        "exceptions": df[df["Age Days"] >= 30].sort_values("Age Days", ascending=False),
        "heatmap_data": heatmap_data,
        "trend": trend,
        "scored_df": df,
    }


def aging_heatmap_figure(heatmap_data: pd.DataFrame, chart_bg: str = "#111827") -> go.Figure:
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns.tolist(),
        y=heatmap_data.index.tolist(),
        colorscale="RdYlGn_r",
        text=np.round(heatmap_data.values, 0),
        texttemplate="%{text:,.0f}",
        textfont={"size": 10},
    ))
    fig.update_layout(
        title="Reconciliation Aging Heatmap",
        template="plotly_dark",
        paper_bgcolor=chart_bg,
        plot_bgcolor=chart_bg,
        height=400,
    )
    return fig


def detect_round_tripping(statements_df: pd.DataFrame, tolerance: float = 0.01) -> dict:
    df = statements_df.copy()
    df = df.sort_values(["Account Number", "Date"])

    patterns = []
    accounts = df["Account Number"].unique()

    for acct in accounts:
        acct_df = df[df["Account Number"] == acct]
        outflows = acct_df[acct_df["Debit"] > 0]
        inflows = acct_df[acct_df["Credit"] > 0]

        for _, out_row in outflows.iterrows():
            amount = out_row["Debit"]
            window = df[
                (df["Date"] >= out_row["Date"])
                & (df["Date"] <= out_row["Date"] + pd.Timedelta(days=30))
                & (df["Account Number"] != acct)
            ]
            returns = window[abs(window["Credit"] - amount) <= amount * tolerance]
            for _, ret in returns.iterrows():
                back = df[
                    (df["Account Number"] == acct)
                    & (df["Date"] >= ret["Date"])
                    & (df["Date"] <= ret["Date"] + pd.Timedelta(days=30))
                    & (abs(df["Credit"] - amount) <= amount * tolerance)
                ]
                if not back.empty:
                    prob = min(95, 60 + amount / 10000)
                    patterns.append({
                        "Source Account": acct,
                        "Intermediate Account": ret["Account Number"],
                        "Amount": amount,
                        "Pattern": "Circular Transfer",
                        "Risk Level": "High" if prob > 80 else "Medium",
                        "Probability Score": round(prob, 1),
                        "Date": out_row["Date"],
                    })

    patterns_df = pd.DataFrame(patterns) if patterns else pd.DataFrame(columns=[
        "Source Account", "Intermediate Account", "Amount", "Pattern",
        "Risk Level", "Probability Score", "Date",
    ])

    G = nx.DiGraph()
    for _, row in df.iterrows():
        if row["Debit"] > 0:
            G.add_edge(str(row["Account Number"]), "EXTERNAL", weight=row["Debit"])
        if row["Credit"] > 0:
            G.add_edge("EXTERNAL", str(row["Account Number"]), weight=row["Credit"])

    return {"patterns": patterns_df, "graph": G, "statements": df}


def round_trip_sankey_figure(patterns_df: pd.DataFrame, chart_bg: str = "#111827") -> go.Figure:
    if patterns_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No round-tripping patterns detected", showarrow=False)
        fig.update_layout(template="plotly_dark", paper_bgcolor=chart_bg, height=400)
        return fig

    sources, targets, values = [], [], []
    labels = list(set(
        patterns_df["Source Account"].astype(str).tolist()
        + patterns_df["Intermediate Account"].astype(str).tolist()
    ))
    label_map = {l: i for i, l in enumerate(labels)}

    for _, row in patterns_df.iterrows():
        sources.append(label_map[str(row["Source Account"])])
        targets.append(label_map[str(row["Intermediate Account"])])
        values.append(row["Amount"])

    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=labels),
        link=dict(source=sources, target=targets, value=values),
    )])
    fig.update_layout(title="Round-Tripping Flow Analysis", template="plotly_dark", paper_bgcolor=chart_bg, height=450)
    return fig


def validate_bank_charges(statements_df: pd.DataFrame, rate: float = 0.001) -> pd.DataFrame:
    df = statements_df.copy()
    charge_keywords = ["charge", "fee", "interest", "penalty", "commission"]
    mask = df["Description"].str.lower().str.contains("|".join(charge_keywords), na=False)
    charges = df[mask].copy()

    if charges.empty:
        return pd.DataFrame(columns=["Date", "Description", "Actual", "Expected", "Variance", "Flag"])

    charges["Actual"] = charges["Debit"].where(charges["Debit"] > 0, charges["Credit"])
    charges["Expected"] = charges["Balance"].abs() * rate
    charges["Variance"] = charges["Actual"] - charges["Expected"]
    charges["Flag"] = charges["Variance"].apply(
        lambda v: "Overcharge" if v > 50 else ("Undercharge" if v < -50 else "OK")
    )
    return charges[["Date", "Description", "Actual", "Expected", "Variance", "Flag"]].rename(columns={"Description": "Description"})


def analyze_idle_cash(statements_df: pd.DataFrame, idle_threshold_days: int = 30) -> dict:
    df = statements_df.copy()
    df = df.sort_values(["Account Number", "Date"])

    results = []
    for acct, grp in df.groupby("Account Number"):
        grp = grp.sort_values("Date")
        last_txn = grp["Date"].max()
        avg_balance = grp["Balance"].mean()
        idle_days = (df["Date"].max() - last_txn).days if pd.notna(last_txn) else 0
        opportunity_cost = avg_balance * 0.05 * (idle_days / 365)

        if idle_days >= idle_threshold_days and avg_balance > 10000:
            results.append({
                "Account Number": acct,
                "Balance": round(avg_balance, 2),
                "Idle Days": idle_days,
                "Opportunity Cost": round(opportunity_cost, 2),
                "Last Transaction": last_txn,
            })

    idle_df = pd.DataFrame(results)
    efficiency = max(0, 100 - len(results) * 5) if not idle_df.empty else 95

    return {"idle_cash": idle_df, "efficiency_score": efficiency}


def idle_cash_figure(idle_df: pd.DataFrame, chart_bg: str = "#111827") -> go.Figure:
    if idle_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No idle cash identified", showarrow=False)
        fig.update_layout(template="plotly_dark", paper_bgcolor=chart_bg, height=350)
        return fig
    fig = px.bar(
        idle_df, x="Account Number", y="Balance", color="Idle Days",
        title="Idle Cash by Account", template="plotly_dark",
    )
    fig.update_layout(paper_bgcolor=chart_bg, plot_bgcolor=chart_bg, height=400)
    return fig


def test_authorisation(statements_df: pd.DataFrame) -> pd.DataFrame:
    df = statements_df.copy()
    df["Approver"] = df["Approver"].astype(str).str.strip()
    df["Authorised Signatory"] = df["Authorised Signatory"].astype(str).str.strip()
    violations = df[
        (df["Approver"] != df["Authorised Signatory"])
        & (df["Approver"] != "nan")
        & (df["Authorised Signatory"] != "nan")
    ].copy()
    violations["Control Risk Rating"] = "High"
    return violations
