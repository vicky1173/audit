# Audit Intelligence Suite

**Treasury, Banking & Quality Control Analytics Platform**

Enterprise-grade Streamlit application for Internal Audit, Treasury, Banking, and Quality Control analytics — inspired by Big 4 audit platforms.

## Features

- **Executive Dashboard** — KPI cards, risk matrix, trend charts, top exceptions
- **Treasury & Banking Audit** — Aging analysis, round-tripping detection, bank charges validation, idle cash analysis, authorisation control testing
- **Quality Control Analytics** — Rejection trends, accounting verification, QC clearance validation, vendor failures, rework costs
- **AI Risk Engine** — Composite risk scoring (Low / Medium / High / Critical)
- **Smart Findings Generator** — Observation, Risk, Impact, Recommendation, Management Action
- **Export** — PDF, Excel, CSV with company logo branding
- **Dark / Light Mode** — Glassmorphism UI with premium enterprise design

## Quick Start

```bash
cd audit-intelligence-suite
pip install -r requirements.txt
python scripts/create_logo.py
python scripts/generate_templates.py
streamlit run app.py
```

## Login Credentials

| Username | Password   |
|----------|------------|
| admin    | audit2024  |
| auditor  | audit2024  |
| cfo      | audit2024  |

## Sample Data

Download templates from the sidebar after login, or find them in `data/templates/`:

- `bank_statements_template.xlsx`
- `bank_reconciliation_template.xlsx`
- `qc_inspection_template.xlsx`
- `vendor_debit_notes_template.xlsx`
- `payment_records_template.xlsx`

## Project Structure

```
audit-intelligence-suite/
├── app.py                  # Main Streamlit entry point
├── requirements.txt
├── assets/logo.png         # Company logo (placeholder)
├── data/templates/         # Sample Excel templates
├── scripts/
│   ├── create_logo.py
│   └── generate_templates.py
└── src/
    ├── analytics/          # Treasury & QC analytics engines
    ├── ui/                 # Reusable UI components
    ├── auth.py             # Login & session management
    ├── config.py           # Configuration & schemas
    ├── data_loader.py      # Excel upload & validation
    ├── findings_generator.py
    ├── pages.py            # Page renderers
    ├── report_generator.py # PDF export
    ├── risk_engine.py      # AI risk scoring
    └── theme.py            # Dark/light CSS theming
```

## Tech Stack

streamlit · pandas · numpy · plotly · streamlit-aggrid · openpyxl · xlsxwriter · networkx · scikit-learn · reportlab
