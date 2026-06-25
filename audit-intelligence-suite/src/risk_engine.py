"""AI Risk Scoring Engine."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class RiskLevel(str, Enum):
    LOW = "Low Risk"
    MEDIUM = "Medium Risk"
    HIGH = "High Risk"
    CRITICAL = "Critical Risk"


@dataclass
class RiskScore:
    score: float
    level: RiskLevel
    factors: dict


def _classify(score: float) -> RiskLevel:
    if score >= 75:
        return RiskLevel.CRITICAL
    if score >= 50:
        return RiskLevel.HIGH
    if score >= 25:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def compute_risk_score(
    amount: float = 0,
    frequency: float = 0,
    age_days: float = 0,
    vendor_history: float = 0,
    approval_violations: float = 0,
    qc_failures: float = 0,
    weights: Optional[dict] = None,
) -> RiskScore:
    """Composite risk score (0-100) from normalized factors."""
    w = weights or {
        "amount": 0.20,
        "frequency": 0.15,
        "age": 0.15,
        "vendor_history": 0.15,
        "approval": 0.20,
        "qc": 0.15,
    }

    amount_norm = min(amount / 1_000_000, 1.0) * 100
    freq_norm = min(frequency / 10, 1.0) * 100
    age_norm = min(age_days / 180, 1.0) * 100
    vendor_norm = min(vendor_history, 1.0) * 100
    approval_norm = min(approval_violations, 1.0) * 100
    qc_norm = min(qc_failures, 1.0) * 100

    score = (
        w["amount"] * amount_norm
        + w["frequency"] * freq_norm
        + w["age"] * age_norm
        + w["vendor_history"] * vendor_norm
        + w["approval"] * approval_norm
        + w["qc"] * qc_norm
    )
    score = round(min(max(score, 0), 100), 1)

    factors = {
        "Amount Impact": round(amount_norm, 1),
        "Frequency": round(freq_norm, 1),
        "Age": round(age_norm, 1),
        "Vendor History": round(vendor_norm, 1),
        "Approval Violations": round(approval_norm, 1),
        "QC Failures": round(qc_norm, 1),
    }
    return RiskScore(score=score, level=_classify(score), factors=factors)


def score_dataframe(
    df: pd.DataFrame,
    amount_col: str = "Amount",
    age_col: Optional[str] = "Age Days",
) -> pd.DataFrame:
    """Add risk score columns to a dataframe."""
    out = df.copy()
    amounts = pd.to_numeric(out.get(amount_col, 0), errors="coerce").fillna(0)
    ages = pd.to_numeric(out.get(age_col, 0), errors="coerce").fillna(0) if age_col else pd.Series(0, index=out.index)

    scores, levels = [], []
    for amt, age in zip(amounts, ages):
        rs = compute_risk_score(amount=amt, age_days=age)
        scores.append(rs.score)
        levels.append(rs.level.value)
    out["Risk Score"] = scores
    out["Risk Level"] = levels
    return out


def risk_level_color(level: str) -> str:
    mapping = {
        "Low Risk": "#10b981",
        "Medium Risk": "#f59e0b",
        "High Risk": "#f97316",
        "Critical Risk": "#ef4444",
    }
    return mapping.get(level, "#6b7280")


def build_risk_matrix(findings: list[dict]) -> pd.DataFrame:
    """Impact vs Likelihood matrix counts."""
    matrix = pd.DataFrame(0, index=["Low", "Medium", "High", "Critical"], columns=["Low", "Medium", "High", "Critical"])
    for f in findings:
        impact = f.get("impact", "Medium")
        likelihood = f.get("likelihood", "Medium")
        if impact in matrix.index and likelihood in matrix.columns:
            matrix.loc[impact, likelihood] += 1
    return matrix
