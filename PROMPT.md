# Audit Intelligence Suite — Master Build Prompt

Copy and paste this prompt to regenerate or extend the application with the same enterprise quality bar.

---

## Prompt

Develop a **production-grade Streamlit audit analytics application** with a **premium enterprise UI** (glassmorphism, dark/light mode, Inter typography, navy-blue audit checklist styling inspired by Big 4 workpapers).

### Branding
- Use the company logo in the sidebar, login screen, and PDF exports
- Allow logo upload/replacement at runtime (PNG, JPG, SVG, WebP)
- App name: **Audit Intelligence Suite**
- Tagline: **Treasury, Banking & Quality Control Analytics Platform**

### Authentication
- Simple login gate (admin / auditor / cfo — password: audit2024)
- Session state for uploaded datasets and generated findings

### Module 27 — Treasury & Banking
Build five audit procedures, each with **Excel/CSV import**, **interactive AG Grid tables**, **Plotly charts**, and **automated findings**:

1. **Age bank reconciliation items** — bucket 30/60/90/180+ days, heatmap, chase list with recommended actions
2. **Detect round-tripping** — pattern detection across related accounts, Sankey flow diagram
3. **Recompute bank charges/interest** — actual vs expected vs sanctioned rate, variance flags
4. **Flag idle balances** — accounts above threshold with no activity, opportunity cost calculation
5. **Verify authorisation** — compare Authorised Signatory vs Approver on transactions

**Required upload schemas:**
- Bank Statements: Date, Account Number, Transaction ID, Description, Debit, Credit, Balance, Approver, Authorised Signatory
- Bank Reconciliation: Recon Item, Date, Amount, Status, Age Days

### Module 28 — Quality Control & Rejections
Build five audit procedures with the same data/import/table/chart pattern:

1. **Rejection trends** — Pareto by vendor/process/product, monthly trend line, bubble chart
2. **Rejected-material accounting** — reconcile QC rejections vs vendor debit notes, flag gaps
3. **QC clearance vs payment** — flag payments before QC clearance date
4. **Repeated vendor failures** — rank vendors, risk heatmap
5. **Rework cost capture** — expected vs recorded rework cost, waterfall chart

**Required upload schemas:**
- QC Inspection: Date, Vendor, Product, Batch, Process, Inspected Qty, Rejected Qty, Rework Qty, QC Status, Inspector
- Vendor Debit Notes: Vendor, Debit Note No, Amount, Reason, Date
- Payment Records: Vendor, Invoice, Amount, Payment Date, QC Clearance Date

### Executive Dashboard
- 8 KPI metrics (accounts, vendors, transactions, high-risk findings, pending recon, QC failures, vendor risk, audit exceptions)
- Risk gauge, risk matrix (impact × likelihood), findings trend, category treemap
- Top 10 exceptions table

### AI Risk Engine & Findings
- Composite risk score (0–100) → Low / Medium / High / Critical
- Auto-generate findings with: Observation, Risk, Impact, Recommendation, Management Action, Owner, Due Date

### Reports & Export
- PDF audit report with logo branding
- Excel and CSV export of all findings
- Sidebar download links for sample Excel templates

### UI Requirements
- Wide layout, expanded sidebar navigation
- Tabbed sub-pages per audit procedure
- Styled audit scope table (module ID | category | procedure list) matching professional audit checklists
- Dark/light theme toggle with CSS custom properties
- streamlit-aggrid for filterable, sortable, paginated tables with conditional row styling on Risk Level and Flag columns

### Tech Stack
`streamlit`, `pandas`, `numpy`, `plotly`, `streamlit-aggrid`, `openpyxl`, `xlsxwriter`, `networkx`, `scikit-learn`, `reportlab`, `Pillow`

### Deliverables
1. `app.py` entry point
2. Modular `src/` package (analytics, ui, auth, config, data_loader, findings, reports, risk_engine, theme)
3. `scripts/create_logo.py` and `scripts/generate_templates.py`
4. Sample Excel templates in `data/templates/`
5. `requirements.txt` and `README.md`

Make it look **fantastic** — not a prototype. Every screen should feel like a paid SaaS audit platform.

---

## Quick run

```bash
cd audit-intelligence-suite
pip install -r requirements.txt
python scripts/create_logo.py
python scripts/generate_templates.py
streamlit run app.py
```

Login: **admin** / **audit2024**
