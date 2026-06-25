"""Page renderers for Audit Intelligence Suite."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics.quality import (
    pareto_figure,
    rejection_trend_analysis,
    repeated_vendor_failures,
    validate_qc_clearance,
    validate_rework_costs,
    vendor_heatmap_figure,
    verify_rejected_accounting,
)
from src.analytics.treasury import (
    aging_heatmap_figure,
    analyze_aging,
    analyze_idle_cash,
    detect_round_tripping,
    idle_cash_figure,
    round_trip_sankey_figure,
    test_authorisation,
    validate_bank_charges,
)
from src.data_loader import (
    df_to_csv_bytes,
    df_to_excel_bytes,
    load_bank_recon,
    load_bank_statements,
    load_payment_records,
    load_qc_inspection,
    load_vendor_debit,
)
from src.findings_generator import findings_to_dataframe, generate_qc_findings, generate_treasury_findings
from src.config import QUALITY_MODULES, TREASURY_MODULES
from src.report_generator import generate_audit_pdf
from src.risk_engine import build_risk_matrix, compute_risk_score
from src.theme import DARK_THEME, LIGHT_THEME
from src.ui.components import (
    page_header,
    render_aggrid,
    render_audit_module_checklist,
    render_kpi_row,
    risk_gauge_figure,
    risk_matrix_figure,
    section_header,
)


def _chart_bg():
    return DARK_THEME["chart_bg"] if st.session_state.get("dark_mode", True) else LIGHT_THEME["chart_bg"]


def render_executive_dashboard():
    page_header("Executive Dashboard", "Real-time audit intelligence and KPI monitoring")

    bs = st.session_state.get("bank_statements")
    recon = st.session_state.get("bank_recon")
    qc = st.session_state.get("qc_inspection")
    findings = st.session_state.get("findings", [])

    total_accounts = bs["Account Number"].nunique() if bs is not None else 0
    total_vendors = qc["Vendor"].nunique() if qc is not None else 0
    total_txns = len(bs) if bs is not None else 0
    high_risk = sum(1 for f in findings if f.get("risk_level") in ("High Risk", "Critical Risk"))
    pending_recon = len(recon[recon["Status"].str.lower() != "cleared"]) if recon is not None else 0
    qc_failures = len(qc[qc["QC Status"].str.lower().isin(["fail", "failed", "reject"])]) if qc is not None else 0
    vendor_risk = round(qc.groupby("Vendor")["Rejected Qty"].sum().max() / max(qc["Inspected Qty"].sum(), 1) * 100, 1) if qc is not None and not qc.empty else 0
    audit_exceptions = len(findings)

    render_kpi_row([
        {"label": "Accounts Analysed", "value": f"{total_accounts:,}", "delta": "+12% vs prior"},
        {"label": "Total Vendors", "value": f"{total_vendors:,}", "delta": "Active"},
        {"label": "Transactions", "value": f"{total_txns:,}", "delta": "+8%"},
        {"label": "High Risk Findings", "value": str(high_risk), "delta": "Requires action", "delta_color": "inverse"},
        {"label": "Pending Recon", "value": str(pending_recon), "delta": "Open items"},
        {"label": "QC Failures", "value": str(qc_failures), "delta_color": "inverse" if qc_failures else "normal"},
        {"label": "Vendor Risk Score", "value": f"{vendor_risk}%"},
        {"label": "Audit Exceptions", "value": str(audit_exceptions), "delta": "Total findings"},
    ])

    c1, c2 = st.columns(2)
    with c1:
        section_header("Risk Overview")
        avg_risk = sum(f.get("risk_score", 0) for f in findings) / max(len(findings), 1)
        st.plotly_chart(risk_gauge_figure(avg_risk, "Portfolio Risk Score", _chart_bg()), use_container_width=True)

    with c2:
        section_header("Risk Matrix")
        matrix = build_risk_matrix(findings)
        st.plotly_chart(risk_matrix_figure(matrix, _chart_bg()), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        section_header("Exception Trend")
        if findings:
            trend_df = pd.DataFrame(findings)
            trend_df["month"] = pd.to_datetime(trend_df.get("created_at", pd.Timestamp.now())).dt.to_period("M").astype(str)
            monthly = trend_df.groupby("month").size().reset_index(name="count")
            fig = px.line(monthly, x="month", y="count", title="Findings Trend", markers=True, template="plotly_dark")
            fig.update_layout(paper_bgcolor=_chart_bg(), plot_bgcolor=_chart_bg(), height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Upload data and run analytics to populate trends.")

    with c4:
        section_header("Category Distribution")
        if findings:
            cat_df = pd.DataFrame(findings)["category"].value_counts().reset_index()
            cat_df.columns = ["Category", "Count"]
            fig = px.treemap(cat_df, path=["Category"], values="Count", title="Findings by Category", template="plotly_dark")
            fig.update_layout(paper_bgcolor=_chart_bg(), height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No findings yet.")

    section_header("Top 10 Exceptions")
    if findings:
        top = sorted(findings, key=lambda x: x.get("risk_score", 0), reverse=True)[:10]
        render_aggrid(findings_to_dataframe(top), height=350, key="exec_top_findings")
    else:
        st.info("Run Treasury or QC analytics to generate findings.")


def render_treasury_banking():
    bs = st.session_state.get("bank_statements")
    recon = st.session_state.get("bank_recon")
    page_header(
        "Treasury & Banking Audit",
        "Bank reconciliation, round-tripping, charges, idle cash & authorisation controls",
        stats=[
            {"label": "Statements", "value": f"{len(bs):,}" if bs is not None else "—"},
            {"label": "Recon Items", "value": f"{len(recon):,}" if recon is not None else "—"},
            {"label": "Procedures", "value": "5"},
        ],
    )

    section_header("Audit Scope — Module 27")
    render_audit_module_checklist(TREASURY_MODULES)

    tab_upload, tab_aging, tab_round, tab_charges, tab_idle, tab_auth = st.tabs([
        "📤 Data Upload", "⏳ Aging Analysis", "🔄 Round Tripping",
        "💳 Bank Charges", "💰 Idle Cash", "🔐 Authorisation",
    ])

    with tab_upload:
        section_header("Upload Treasury Datasets")
        c1, c2 = st.columns(2)
        with c1:
            bs_file = st.file_uploader("Bank Statements (.xlsx/.csv)", type=["xlsx", "xls", "csv"], key="bs_upload")
            if bs_file:
                df = load_bank_statements(bs_file)
                if df is not None:
                    st.session_state.bank_statements = df
                    st.success(f"Loaded {len(df):,} bank statement records")
                    render_aggrid(df.head(100), height=250, key="bs_preview")
        with c2:
            recon_file = st.file_uploader("Bank Reconciliation (.xlsx/.csv)", type=["xlsx", "xls", "csv"], key="recon_upload")
            if recon_file:
                df = load_bank_recon(recon_file)
                if df is not None:
                    st.session_state.bank_recon = df
                    st.success(f"Loaded {len(df):,} reconciliation items")
                    render_aggrid(df.head(100), height=250, key="recon_preview")

        if st.button("Run Treasury Analytics", type="primary"):
            _run_treasury_analytics()

    with tab_aging:
        recon = st.session_state.get("bank_recon")
        if recon is None:
            st.warning("Upload Bank Reconciliation data first.")
        else:
            result = analyze_aging(recon)
            render_kpi_row([
                {"label": "30+ Days", "value": str(result["summary"]["30+ Days"])},
                {"label": "60+ Days", "value": str(result["summary"]["60+ Days"])},
                {"label": "90+ Days", "value": str(result["summary"]["90+ Days"])},
                {"label": "180+ Days", "value": str(result["summary"]["180+ Days"]), "delta_color": "inverse"},
            ])
            st.plotly_chart(aging_heatmap_figure(result["heatmap_data"], _chart_bg()), use_container_width=True)
            fig = px.line(result["trend"], x="Date", y="Amount", title="Aging Trend", template="plotly_dark")
            fig.update_layout(paper_bgcolor=_chart_bg(), height=300)
            st.plotly_chart(fig, use_container_width=True)
        section_header("Exception Table")
        render_aggrid(result["exceptions"], height=350, key="aging_exceptions")
        if not result["exceptions"].empty:
            st.download_button(
                "Export exceptions to Excel",
                df_to_excel_bytes(result["exceptions"], "Aging Exceptions"),
                "aging_exceptions.xlsx",
                use_container_width=True,
                key="export_aging",
            )

    with tab_round:
        bs = st.session_state.get("bank_statements")
        if bs is None:
            st.warning("Upload Bank Statements first.")
        else:
            rt = detect_round_tripping(bs)
            st.plotly_chart(round_trip_sankey_figure(rt["patterns"], _chart_bg()), use_container_width=True)
            section_header("Detected Patterns")
            render_aggrid(rt["patterns"], height=350, key="round_trip_table")

    with tab_charges:
        bs = st.session_state.get("bank_statements")
        if bs is None:
            st.warning("Upload Bank Statements first.")
        else:
            charges = validate_bank_charges(bs)
            flagged = charges[charges["Flag"] != "OK"] if not charges.empty else charges
            render_kpi_row([
                {"label": "Total Charges", "value": str(len(charges))},
                {"label": "Exceptions", "value": str(len(flagged)), "delta_color": "inverse"},
                {"label": "Total Variance", "value": f"${charges['Variance'].sum():,.0f}" if not charges.empty else "$0"},
            ])
            if not charges.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(name="Actual", x=charges["Description"].head(10), y=charges["Actual"].head(10)))
                fig.add_trace(go.Bar(name="Expected", x=charges["Description"].head(10), y=charges["Expected"].head(10)))
                fig.update_layout(title="Actual vs Expected Charges", barmode="group", template="plotly_dark", paper_bgcolor=_chart_bg(), height=400)
                st.plotly_chart(fig, use_container_width=True)
            render_aggrid(flagged if not flagged.empty else charges, height=300, key="charges_table")

    with tab_idle:
        bs = st.session_state.get("bank_statements")
        if bs is None:
            st.warning("Upload Bank Statements first.")
        else:
            idle = analyze_idle_cash(bs)
            render_kpi_row([
                {"label": "Idle Accounts", "value": str(len(idle["idle_cash"]))},
                {"label": "Treasury Efficiency", "value": f"{idle['efficiency_score']}%"},
                {"label": "Opportunity Cost", "value": f"${idle['idle_cash']['Opportunity Cost'].sum():,.0f}" if not idle["idle_cash"].empty else "$0"},
            ])
            st.plotly_chart(idle_cash_figure(idle["idle_cash"], _chart_bg()), use_container_width=True)
            render_aggrid(idle["idle_cash"], height=300, key="idle_table")

    with tab_auth:
        bs = st.session_state.get("bank_statements")
        if bs is None:
            st.warning("Upload Bank Statements first.")
        else:
            violations = test_authorisation(bs)
            render_kpi_row([
                {"label": "Total Transactions", "value": str(len(bs))},
                {"label": "Violations", "value": str(len(violations)), "delta_color": "inverse"},
                {"label": "Control Rating", "value": "High Risk" if len(violations) > 0 else "Effective"},
            ])
            render_aggrid(violations, height=400, key="auth_violations")


def _run_treasury_analytics():
    bs = st.session_state.get("bank_statements")
    recon = st.session_state.get("bank_recon")

    aging_df = analyze_aging(recon)["exceptions"] if recon is not None else None
    rt_df = detect_round_tripping(bs)["patterns"] if bs is not None else None
    charges_df = validate_bank_charges(bs) if bs is not None else None
    idle_df = analyze_idle_cash(bs)["idle_cash"] if bs is not None else None
    auth_df = test_authorisation(bs) if bs is not None else None

    new_findings = generate_treasury_findings(aging_df, rt_df, charges_df, idle_df, auth_df)
    existing = st.session_state.get("findings", [])
    st.session_state.findings = existing + new_findings
    st.success(f"Generated {len(new_findings)} treasury audit findings.")


def render_quality_control():
    qc = st.session_state.get("qc_inspection")
    page_header(
        "Quality Control & Rejection Analytics",
        "QC inspection, vendor debit notes, clearance validation & rework costs",
        stats=[
            {"label": "QC Records", "value": f"{len(qc):,}" if qc is not None else "—"},
            {"label": "Vendors", "value": f"{qc['Vendor'].nunique():,}" if qc is not None else "—"},
            {"label": "Procedures", "value": "5"},
        ],
    )

    section_header("Audit Scope — Module 28")
    render_audit_module_checklist(QUALITY_MODULES)

    tab_upload, tab_reject, tab_accounting, tab_clearance, tab_vendor, tab_rework = st.tabs([
        "📤 Data Upload", "📉 Rejection Trends", "📋 Accounting Verification",
        "✅ QC Clearance", "🏭 Vendor Failures", "🔧 Rework Costs",
    ])

    with tab_upload:
        section_header("Upload QC Datasets")
        c1, c2, c3 = st.columns(3)
        with c1:
            qc_file = st.file_uploader("QC Inspection Data", type=["xlsx", "xls", "csv"], key="qc_upload")
            if qc_file:
                df = load_qc_inspection(qc_file)
                if df is not None:
                    st.session_state.qc_inspection = df
                    st.success(f"Loaded {len(df):,} QC records")
        with c2:
            debit_file = st.file_uploader("Vendor Debit Notes", type=["xlsx", "xls", "csv"], key="debit_upload")
            if debit_file:
                df = load_vendor_debit(debit_file)
                if df is not None:
                    st.session_state.vendor_debit = df
                    st.success(f"Loaded {len(df):,} debit notes")
        with c3:
            pay_file = st.file_uploader("Payment Records", type=["xlsx", "xls", "csv"], key="pay_upload")
            if pay_file:
                df = load_payment_records(pay_file)
                if df is not None:
                    st.session_state.payment_records = df
                    st.success(f"Loaded {len(df):,} payment records")

        if st.button("Run QC Analytics", type="primary"):
            _run_qc_analytics()

    with tab_reject:
        qc = st.session_state.get("qc_inspection")
        if qc is None:
            st.warning("Upload QC Inspection data first.")
        else:
            analysis = rejection_trend_analysis(qc)
            render_kpi_row([
                {"label": "Overall Rejection %", "value": f"{analysis['vendor']['Rejection %'].mean():.1f}%"},
                {"label": "Vendors", "value": str(len(analysis["vendor"]))},
                {"label": "Products", "value": str(len(analysis["product"]))},
                {"label": "Processes", "value": str(len(analysis["process"]))},
            ])
            st.plotly_chart(pareto_figure(analysis["vendor"], "Vendor", "Rejected", _chart_bg()), use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                fig = px.line(analysis["monthly_trend"], x="Date", y="Rejection %", title="Rejection Trend", template="plotly_dark", markers=True)
                fig.update_layout(paper_bgcolor=_chart_bg(), height=300)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig = px.scatter(analysis["vendor"], x="Inspected", y="Rejected", size="Rejection %", color="Rejection %",
                                 hover_name="Vendor", title="Vendor Rejection Bubble Chart", template="plotly_dark", color_continuous_scale="RdYlGn_r")
                fig.update_layout(paper_bgcolor=_chart_bg(), height=300)
                st.plotly_chart(fig, use_container_width=True)

    with tab_accounting:
        qc = st.session_state.get("qc_inspection")
        debit = st.session_state.get("vendor_debit")
        if qc is None or debit is None:
            st.warning("Upload both QC Inspection and Vendor Debit Notes data.")
        else:
            gaps = verify_rejected_accounting(qc, debit)
            render_kpi_row([
                {"label": "Unaccounted Items", "value": str(len(gaps))},
                {"label": "Total Gap", "value": f"${gaps['Unaccounted Value'].sum():,.0f}" if not gaps.empty else "$0"},
            ])
            render_aggrid(gaps, height=400, key="accounting_gaps")

    with tab_clearance:
        payments = st.session_state.get("payment_records")
        if payments is None:
            st.warning("Upload Payment Records first.")
        else:
            violations = validate_qc_clearance(payments)
            render_kpi_row([
                {"label": "Total Payments", "value": str(len(payments))},
                {"label": "Violations", "value": str(len(violations)), "delta_color": "inverse"},
            ])
            render_aggrid(violations, height=400, key="clearance_violations")

    with tab_vendor:
        qc = st.session_state.get("qc_inspection")
        if qc is None:
            st.warning("Upload QC Inspection data first.")
        else:
            vendor_stats = repeated_vendor_failures(qc)
            st.plotly_chart(vendor_heatmap_figure(vendor_stats, _chart_bg()), use_container_width=True)
            render_aggrid(vendor_stats, height=350, key="vendor_ranking")

    with tab_rework:
        qc = st.session_state.get("qc_inspection")
        if qc is None:
            st.warning("Upload QC Inspection data first.")
        else:
            rework = validate_rework_costs(qc)
            render_kpi_row([
                {"label": "Rework Batches", "value": str(len(qc[qc['Rework Qty'] > 0]))},
                {"label": "Cost Gaps", "value": str(len(rework))},
                {"label": "Financial Impact", "value": f"${rework['Cost Gap'].sum():,.0f}" if not rework.empty else "$0"},
            ])
            if not rework.empty:
                fig = px.waterfall(
                    x=rework["Batch"].head(8),
                    y=rework["Cost Gap"].head(8),
                    title="Rework Cost Impact Waterfall",
                )
                fig.update_layout(template="plotly_dark", paper_bgcolor=_chart_bg(), height=350)
                st.plotly_chart(fig, use_container_width=True)
            render_aggrid(rework, height=300, key="rework_table")


def _run_qc_analytics():
    qc = st.session_state.get("qc_inspection")
    debit = st.session_state.get("vendor_debit")
    payments = st.session_state.get("payment_records")

    rejection = rejection_trend_analysis(qc)["vendor"] if qc is not None else None
    accounting = verify_rejected_accounting(qc, debit) if qc is not None and debit is not None else None
    clearance = validate_qc_clearance(payments) if payments is not None else None
    vendor_fail = repeated_vendor_failures(qc) if qc is not None else None
    rework = validate_rework_costs(qc) if qc is not None else None

    new_findings = generate_qc_findings(rejection, accounting, clearance, vendor_fail, rework)
    existing = st.session_state.get("findings", [])
    st.session_state.findings = existing + new_findings
    st.success(f"Generated {len(new_findings)} QC audit findings.")


def render_reports_export():
    page_header("Reports & Export", "Executive audit reports, findings export, and management deliverables")

    findings = st.session_state.get("findings", [])
    findings_df = findings_to_dataframe(findings)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Findings", len(findings))
    with c2:
        critical = sum(1 for f in findings if f.get("risk_level") == "Critical Risk")
        st.metric("Critical", critical)
    with c3:
        open_items = sum(1 for f in findings if f.get("status") == "Open")
        st.metric("Open Items", open_items)

    section_header("Audit Findings")
    render_aggrid(findings_df, height=400, key="report_findings")

    section_header("Export Options")
    col1, col2, col3 = st.columns(3)

    summary = (
        f"This audit cycle identified {len(findings)} findings across treasury and quality control domains. "
        f"{sum(1 for f in findings if f.get('risk_level') in ('High Risk', 'Critical Risk'))} items require immediate management attention. "
        "Key themes include aging reconciliation items, authorisation control gaps, and supplier quality deterioration."
    )

    kpis = {
        "Total Findings": len(findings),
        "Critical/High": sum(1 for f in findings if f.get("risk_level") in ("High Risk", "Critical Risk")),
        "Open Items": open_items,
    }

    with col1:
        if st.button("Generate PDF Report", type="primary", use_container_width=True):
            pdf_bytes = generate_audit_pdf(findings, summary, st.session_state.get("username", "Auditor"), kpis)
            st.download_button("Download PDF", pdf_bytes, "audit_intelligence_report.pdf", "application/pdf", use_container_width=True)

    with col2:
        if not findings_df.empty:
            st.download_button(
                "Download Excel",
                df_to_excel_bytes(findings_df, "Audit Findings"),
                "audit_findings.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    with col3:
        if not findings_df.empty:
            st.download_button(
                "Download CSV",
                df_to_csv_bytes(findings_df),
                "audit_findings.csv",
                "text/csv",
                use_container_width=True,
            )

    section_header("Executive Summary Preview")
    st.markdown(f"*{summary}*")

    if findings:
        avg = sum(f.get("risk_score", 0) for f in findings) / len(findings)
        st.plotly_chart(risk_gauge_figure(avg, "Overall Audit Risk Score", _chart_bg()), use_container_width=True)
