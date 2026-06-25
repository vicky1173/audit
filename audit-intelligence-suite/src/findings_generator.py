"""Smart Audit Findings Generator."""

from datetime import datetime
from typing import Optional

import pandas as pd

from src.risk_engine import RiskLevel, compute_risk_score


def _finding(
    observation: str,
    risk: str,
    impact: str,
    recommendation: str,
    management_action: str,
    category: str,
    risk_score: float,
    likelihood: str = "Medium",
) -> dict:
    level = compute_risk_score(amount=risk_score * 10000, age_days=risk_score).level.value
    return {
        "id": f"FND-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "category": category,
        "observation": observation,
        "risk": risk,
        "impact": impact,
        "impact_level": impact if impact in ("Low", "Medium", "High", "Critical") else "Medium",
        "likelihood": likelihood,
        "recommendation": recommendation,
        "management_action": management_action,
        "risk_score": risk_score,
        "risk_level": level,
        "status": "Open",
        "created_at": datetime.now().isoformat(),
    }


def generate_treasury_findings(
    aging_df: Optional[pd.DataFrame] = None,
    round_trip_df: Optional[pd.DataFrame] = None,
    charges_df: Optional[pd.DataFrame] = None,
    idle_cash_df: Optional[pd.DataFrame] = None,
    auth_df: Optional[pd.DataFrame] = None,
) -> list[dict]:
    findings = []

    if aging_df is not None and not aging_df.empty:
        critical = aging_df[aging_df["Age Days"] >= 180]
        for _, row in critical.head(10).iterrows():
            findings.append(_finding(
                observation=f"Reconciliation item '{row.get('Recon Item', 'N/A')}' aged {row.get('Age Days', 0)} days.",
                risk="Extended unreconciled items indicate potential misstatement or fraud.",
                impact="High",
                recommendation="Escalate to Treasury Manager for immediate resolution.",
                management_action="Clear or write-off aged items within 30 days.",
                category="Treasury - Aging Reconciliation",
                risk_score=min(row.get("Age Days", 0) / 2, 100),
                likelihood="High" if row.get("Age Days", 0) >= 180 else "Medium",
            ))

    if round_trip_df is not None and not round_trip_df.empty:
        for _, row in round_trip_df.head(5).iterrows():
            findings.append(_finding(
                observation=f"Circular transaction detected: {row.get('Pattern', 'Round trip')} involving account {row.get('Source Account', 'N/A')}.",
                risk="Potential round-tripping or layering scheme.",
                impact="Critical",
                recommendation="Investigate related-party transfers and source of funds.",
                management_action="Freeze suspicious accounts pending investigation.",
                category="Treasury - Round Tripping",
                risk_score=row.get("Probability Score", 75),
                likelihood="High",
            ))

    if charges_df is not None and not charges_df.empty:
        overcharges = charges_df[charges_df.get("Flag", pd.Series()) == "Overcharge"] if "Flag" in charges_df.columns else charges_df
        for _, row in overcharges.head(5).iterrows():
            findings.append(_finding(
                observation=f"Bank charge variance of {row.get('Variance', 0):,.2f} on {row.get('Description', 'charge')}.",
                risk="Potential overcharge by banking institution.",
                impact="Medium",
                recommendation="Request charge breakdown from bank and recover overcharges.",
                management_action="Review bank fee schedule and dispute anomalies.",
                category="Treasury - Bank Charges",
                risk_score=min(abs(row.get("Variance", 0)) / 1000, 100),
            ))

    if idle_cash_df is not None and not idle_cash_df.empty:
        top_idle = idle_cash_df.nlargest(3, "Balance") if "Balance" in idle_cash_df.columns else idle_cash_df.head(3)
        for _, row in top_idle.iterrows():
            findings.append(_finding(
                observation=f"Account {row.get('Account Number', 'N/A')} has idle balance of {row.get('Balance', 0):,.2f} for {row.get('Idle Days', 0)} days.",
                risk="Excess liquidity not deployed to investment instruments.",
                impact="Medium",
                recommendation="Deploy surplus cash to approved investment vehicles.",
                management_action="Review treasury investment policy compliance.",
                category="Treasury - Idle Cash",
                risk_score=min(row.get("Idle Days", 0) / 3, 80),
            ))

    if auth_df is not None and not auth_df.empty:
        for _, row in auth_df.head(10).iterrows():
            findings.append(_finding(
                observation=f"Transaction {row.get('Transaction ID', 'N/A')}: Approver '{row.get('Approver', '')}' differs from authorised signatory '{row.get('Authorised Signatory', '')}'.",
                risk="Segregation of duties violation in payment authorisation.",
                impact="High",
                recommendation="Enforce dual-authorisation controls on payment platform.",
                management_action="Revoke unauthorised approver access immediately.",
                category="Treasury - Authorisation Control",
                risk_score=85,
                likelihood="High",
            ))

    return findings


def generate_qc_findings(
    rejection_summary: Optional[pd.DataFrame] = None,
    accounting_df: Optional[pd.DataFrame] = None,
    clearance_df: Optional[pd.DataFrame] = None,
    vendor_failures: Optional[pd.DataFrame] = None,
    rework_df: Optional[pd.DataFrame] = None,
) -> list[dict]:
    findings = []

    if rejection_summary is not None and not rejection_summary.empty:
        high_reject = rejection_summary[rejection_summary.get("Rejection %", pd.Series(0)) > 5] if "Rejection %" in rejection_summary.columns else rejection_summary.head(3)
        for _, row in high_reject.iterrows():
            findings.append(_finding(
                observation=f"Vendor '{row.get('Vendor', 'N/A')}' rejection rate at {row.get('Rejection %', 0):.1f}%.",
                risk="Supplier quality below acceptable threshold.",
                impact="Medium",
                recommendation="Conduct supplier quality audit and implement corrective action plan.",
                management_action="Place vendor on quality watch list.",
                category="QC - Rejection Trend",
                risk_score=min(row.get("Rejection %", 0) * 10, 100),
            ))

    if accounting_df is not None and not accounting_df.empty:
        for _, row in accounting_df.head(10).iterrows():
            findings.append(_finding(
                observation=f"Unaccounted rejection value of {row.get('Unaccounted Value', 0):,.2f} for vendor {row.get('Vendor', 'N/A')}.",
                risk="Rejected material not matched to vendor debit note.",
                impact="High",
                recommendation="Issue debit note or adjust inventory records.",
                management_action="Reconcile rejected material with accounts payable.",
                category="QC - Rejected Material Accounting",
                risk_score=70,
            ))

    if clearance_df is not None and not clearance_df.empty:
        for _, row in clearance_df.head(10).iterrows():
            findings.append(_finding(
                observation=f"Payment to vendor {row.get('Vendor', 'N/A')} on {row.get('Payment Date', 'N/A')} before QC clearance.",
                risk="Payment made prior to quality clearance — control violation.",
                impact="Critical",
                recommendation="Implement system hold on payments until QC clearance.",
                management_action="Recover payment or obtain retrospective QC approval.",
                category="QC - Clearance Validation",
                risk_score=90,
                likelihood="High",
            ))

    if vendor_failures is not None and not vendor_failures.empty:
        for _, row in vendor_failures.head(5).iterrows():
            findings.append(_finding(
                observation=f"Vendor '{row.get('Vendor', 'N/A')}' has {row.get('Failure Count', 0)} recurring quality failures.",
                risk="Chronic supplier quality deterioration.",
                impact="High",
                recommendation="Consider alternative suppliers and enforce SLA penalties.",
                management_action="Initiate vendor performance review.",
                category="QC - Repeated Vendor Failures",
                risk_score=min(row.get("Vendor Risk Score", 50), 100),
            ))

    if rework_df is not None and not rework_df.empty:
        for _, row in rework_df.head(5).iterrows():
            findings.append(_finding(
                observation=f"Rework cost gap of {row.get('Cost Gap', 0):,.2f} for batch {row.get('Batch', 'N/A')}.",
                risk="Rework costs not fully captured in accounting entries.",
                impact="Medium",
                recommendation="Post adjusting journal entries for understated rework costs.",
                management_action="Review cost allocation methodology.",
                category="QC - Rework Cost",
                risk_score=55,
            ))

    return findings


def findings_to_dataframe(findings: list[dict]) -> pd.DataFrame:
    if not findings:
        return pd.DataFrame(columns=[
            "id", "category", "observation", "risk", "impact", "recommendation",
            "management_action", "risk_score", "risk_level", "status",
        ])
    return pd.DataFrame(findings)
