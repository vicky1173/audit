"""Application configuration and constants."""

from pathlib import Path

APP_NAME = "Audit Intelligence Suite"
APP_TAGLINE = "Treasury, Banking & Quality Control Analytics Platform"
APP_VERSION = "1.0.0"

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
LOGO_PATH = ASSETS_DIR / "logo.png"

# Demo credentials (replace with SSO/LDAP in production)
DEMO_USERS = {
    "admin": "audit2024",
    "auditor": "audit2024",
    "cfo": "audit2024",
}

# Risk thresholds
RISK_THRESHOLDS = {
    "low": (0, 25),
    "medium": (25, 50),
    "high": (50, 75),
    "critical": (75, 100),
}

# Aging buckets (days)
AGING_BUCKETS = [30, 60, 90, 180]

# Required column schemas
BANK_STATEMENT_COLS = [
    "Date", "Account Number", "Transaction ID", "Description",
    "Debit", "Credit", "Balance", "Approver", "Authorised Signatory",
]

BANK_RECON_COLS = [
    "Recon Item", "Date", "Amount", "Status", "Age Days",
]

QC_INSPECTION_COLS = [
    "Date", "Vendor", "Product", "Batch", "Process",
    "Inspected Qty", "Rejected Qty", "Rework Qty", "QC Status", "Inspector",
]

VENDOR_DEBIT_COLS = [
    "Vendor", "Debit Note No", "Amount", "Reason", "Date",
]

PAYMENT_RECORDS_COLS = [
    "Vendor", "Invoice", "Amount", "Payment Date", "QC Clearance Date",
]

TREASURY_MODULES = [
    {
        "id": "27",
        "title": "Treasury & banking",
        "items": [
            "Age bank reconciliation items and chase long-pending entries",
            "Detect round-tripping of funds across related accounts",
            "Recompute bank charges/interest against sanctioned terms",
            "Flag idle balances that should have been swept or invested",
            "Verify authorised signatories vs actual transaction approvers",
        ],
    }
]

QUALITY_MODULES = [
    {
        "id": "28",
        "title": "Quality control & rejections",
        "items": [
            "Analyse rejection trends by vendor/process/product",
            "Verify rejected-material accounting and vendor debit notes",
            "Check whether QC clearance precedes payment/usage",
            "Flag repeated quality failures from same vendor",
            "Test rework cost capture and accounting",
        ],
    }
]
