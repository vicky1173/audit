"""PDF and export report generator."""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.config import APP_NAME, APP_TAGLINE, LOGO_PATH


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1e3a5f"),
        spaceAfter=12,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="SectionHead",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=16,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
    ))
    return styles


def generate_audit_pdf(
    findings: list[dict],
    executive_summary: str,
    username: str,
    kpis: Optional[dict] = None,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = _styles()
    story = []

    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH), width=2 * inch, height=0.8 * inch)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(APP_NAME, styles["ReportTitle"]))
    story.append(Paragraph("Executive Audit Report", styles["Heading2"]))
    story.append(Paragraph(APP_TAGLINE, styles["BodyText2"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y %H:%M')}", styles["BodyText2"]))
    story.append(Paragraph(f"Prepared by: {username or 'Internal Audit'}", styles["BodyText2"]))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Executive Summary", styles["SectionHead"]))
    story.append(Paragraph(executive_summary, styles["BodyText2"]))
    story.append(Spacer(1, 0.2 * inch))

    if kpis:
        story.append(Paragraph("Key Metrics", styles["SectionHead"]))
        kpi_data = [["Metric", "Value"]] + [[k, str(v)] for k, v in kpis.items()]
        kpi_table = Table(kpi_data, colWidths=[3 * inch, 2 * inch])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Audit Findings", styles["SectionHead"]))
    if not findings:
        story.append(Paragraph("No findings identified during this audit cycle.", styles["BodyText2"]))
    else:
        for i, f in enumerate(findings[:25], 1):
            story.append(Paragraph(f"Finding #{i}: {f.get('category', 'General')}", styles["Heading3"]))
            story.append(Paragraph(f"<b>Observation:</b> {f.get('observation', '')}", styles["BodyText2"]))
            story.append(Paragraph(f"<b>Risk:</b> {f.get('risk', '')}", styles["BodyText2"]))
            story.append(Paragraph(f"<b>Impact:</b> {f.get('impact', '')} | <b>Risk Level:</b> {f.get('risk_level', 'N/A')} ({f.get('risk_score', 0)})", styles["BodyText2"]))
            story.append(Paragraph(f"<b>Recommendation:</b> {f.get('recommendation', '')}", styles["BodyText2"]))
            story.append(Paragraph(f"<b>Management Action:</b> {f.get('management_action', '')}", styles["BodyText2"]))
            story.append(Spacer(1, 0.15 * inch))

    story.append(PageBreak())
    story.append(Paragraph("Appendix — Risk Rating Methodology", styles["SectionHead"]))
    story.append(Paragraph(
        "Risk scores are computed using a weighted composite model considering amount, frequency, "
        "age, vendor history, approval violations, and QC failure rates. "
        "Ratings: Low (0-25), Medium (25-50), High (50-75), Critical (75-100).",
        styles["BodyText2"],
    ))

    doc.build(story)
    return buf.getvalue()
