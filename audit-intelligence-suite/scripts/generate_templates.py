"""Generate sample Excel data templates for Audit Intelligence Suite."""

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "data" / "templates"
np.random.seed(42)


def _dates(n, start="2024-01-01"):
    base = pd.Timestamp(start)
    return [base + timedelta(days=int(x)) for x in np.random.randint(0, 365, n)]


def bank_statements(n=200):
    accounts = [f"ACC-{1000+i}" for i in range(5)]
    base = pd.Timestamp("2024-01-01")
    rows = []
    for i in range(n):
        acct = np.random.choice(accounts)
        debit = round(np.random.uniform(0, 50000), 2) if np.random.random() > 0.5 else 0
        credit = round(np.random.uniform(0, 50000), 2) if debit == 0 else 0
        signatories = ["John Smith", "Jane Doe", "Robert Chen"]
        approver = np.random.choice(signatories + ["Unauthorized User"] * 2)
        rows.append({
            "Date": base + timedelta(days=int(np.random.randint(0, 365))),
            "Account Number": acct,
            "Transaction ID": f"TXN-{10000+i}",
            "Description": np.random.choice(["Wire Transfer", "Bank Charge", "Interest Fee", "Vendor Payment", "Deposit"]),
            "Debit": debit,
            "Credit": credit,
            "Balance": round(np.random.uniform(100000, 5000000), 2),
            "Approver": approver,
            "Authorised Signatory": np.random.choice(signatories),
        })
    return pd.DataFrame(rows)


def bank_reconciliation(n=80):
    statuses = ["Open", "Pending", "Cleared", "Disputed"]
    rows = []
    for i in range(n):
        age = int(np.random.choice([5, 15, 45, 75, 120, 200], p=[0.2, 0.2, 0.2, 0.15, 0.15, 0.1]))
        rows.append({
            "Recon Item": f"RECON-{2000+i}",
            "Date": datetime(2024, 1, 1) + timedelta(days=np.random.randint(0, 300)),
            "Amount": round(np.random.uniform(1000, 500000), 2),
            "Status": np.random.choice(statuses),
            "Age Days": age,
        })
    return pd.DataFrame(rows)


def qc_inspection(n=150):
    vendors = ["Acme Corp", "Global Supplies", "Prime Materials", "TechParts Ltd", "QualityFirst Inc"]
    products = ["Widget A", "Component B", "Assembly C", "Module D"]
    processes = ["Incoming", "In-Process", "Final", "Packaging"]
    base = pd.Timestamp("2024-01-01")
    rows = []
    for i in range(n):
        inspected = int(np.random.randint(100, 5000))
        rejected = int(inspected * np.random.uniform(0, 0.12))
        rework = int(rejected * np.random.uniform(0, 0.5))
        rows.append({
            "Date": base + timedelta(days=int(np.random.randint(0, 365))),
            "Vendor": np.random.choice(vendors),
            "Product": np.random.choice(products),
            "Batch": f"BATCH-{3000+i}",
            "Process": np.random.choice(processes),
            "Inspected Qty": inspected,
            "Rejected Qty": rejected,
            "Rework Qty": rework,
            "QC Status": np.random.choice(["Pass", "Fail", "Conditional"], p=[0.7, 0.2, 0.1]),
            "Inspector": np.random.choice(["Inspector A", "Inspector B", "Inspector C"]),
        })
    return pd.DataFrame(rows)


def vendor_debit_notes(n=40):
    vendors = ["Acme Corp", "Global Supplies", "Prime Materials", "TechParts Ltd", "QualityFirst Inc"]
    rows = []
    for i in range(n):
        rows.append({
            "Vendor": np.random.choice(vendors),
            "Debit Note No": f"DN-{4000+i}",
            "Amount": round(np.random.uniform(500, 50000), 2),
            "Reason": np.random.choice(["Quality Rejection", "Short Supply", "Damage", "Specification Deviation"]),
            "Date": _dates(1)[0],
        })
    return pd.DataFrame(rows)


def payment_records(n=60):
    vendors = ["Acme Corp", "Global Supplies", "Prime Materials", "TechParts Ltd", "QualityFirst Inc"]
    rows = []
    for i in range(n):
        clearance = datetime(2024, 6, 1) + timedelta(days=np.random.randint(0, 180))
        payment_offset = np.random.randint(-10, 30)
        rows.append({
            "Vendor": np.random.choice(vendors),
            "Invoice": f"INV-{5000+i}",
            "Amount": round(np.random.uniform(5000, 200000), 2),
            "Payment Date": clearance + timedelta(days=payment_offset),
            "QC Clearance Date": clearance,
        })
    return pd.DataFrame(rows)


def main():
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    datasets = {
        "bank_statements_template": bank_statements(),
        "bank_reconciliation_template": bank_reconciliation(),
        "qc_inspection_template": qc_inspection(),
        "vendor_debit_notes_template": vendor_debit_notes(),
        "payment_records_template": payment_records(),
    }
    for name, df in datasets.items():
        path = TEMPLATES_DIR / f"{name}.xlsx"
        df.to_excel(path, index=False)
        print(f"Created {path} ({len(df)} rows)")


if __name__ == "__main__":
    main()
