"""
report_generator.py
Generates a professional PDF analysis report using ReportLab.
"""
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem,
)

from app.config import OUTPUT_DIR


def generate_report(analysis: dict) -> str:
    """
    analysis: dict combining candidate info, job title, scores, skills,
    recommendations, summary, and compatibility results.
    Returns the path to the generated PDF file.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"analysis_report_{analysis.get('id', 'draft')}.pdf"
    filepath = OUTPUT_DIR / filename

    doc = SimpleDocTemplate(
        str(filepath), pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=20, spaceAfter=6)
    h2 = ParagraphStyle("H2Custom", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#1e293b"))
    body = styles["BodyText"]

    story = []
    story.append(Paragraph("AI Resume Screening Report", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y %H:%M')}", body))
    story.append(Spacer(1, 10))

    # Candidate
    story.append(Paragraph("Candidate", h2))
    cand = analysis.get("candidate", {})
    cand_table = Table([
        ["Name", cand.get("name") or "Not detected"],
        ["Email", cand.get("email") or "Not detected"],
        ["Phone", cand.get("phone") or "Not detected"],
    ], colWidths=[100, 350])
    cand_table.setStyle(_table_style())
    story.append(cand_table)

    # Job
    story.append(Paragraph("Job", h2))
    story.append(Paragraph(f"Job Title: {analysis.get('job_title') or 'Not specified'}", body))

    # Match Analysis
    story.append(Paragraph("Match Analysis", h2))
    scores = analysis.get("scores", {})
    cats = scores.get("categories", {})
    score_rows = [["Overall Score", f"{scores.get('final_score', 0)}%"]]
    for cat_name, cat_score in cats.items():
        label = cat_name.replace("_", " ").title()
        score_rows.append([label, f"{cat_score}%"])
    score_table = Table(score_rows, colWidths=[150, 300])
    score_table.setStyle(_table_style())
    story.append(score_table)
    story.append(Paragraph(
        "Note: this score uses a weighted 7-category ATS model "
        "(keyword match, skills, semantic similarity, contact info, "
        "section structure, achievements, action verbs).",
        ParagraphStyle("note", parent=body, fontSize=8, textColor=colors.grey)
    ))

    # Matched skills
    story.append(Paragraph("Matched Skills", h2))
    matched = analysis.get("matched_skills", [])
    story.append(Paragraph(", ".join(matched) if matched else "None detected", body))

    # Missing skills
    story.append(Paragraph("Missing Skills", h2))
    missing = analysis.get("missing_skills", [])
    story.append(Paragraph(", ".join(missing) if missing else "None", body))

    # Recommendations
    story.append(Paragraph("Recommendations", h2))
    recs = analysis.get("recommendations", [])
    if recs:
        items = []
        for r in recs:
            topics = ", ".join(r.get("topics", []))
            items.append(ListItem(Paragraph(f"<b>{r['skill']}</b> ({r.get('level','')}) — {topics}", body)))
        story.append(ListFlowable(items, bulletType="bullet"))
    else:
        story.append(Paragraph("No recommendations — all required skills matched.", body))

    # Resume Summary
    story.append(Paragraph("Resume Summary", h2))
    story.append(Paragraph(analysis.get("summary") or "Not detected", body))

    # Experience & Projects (real extracted content, not just a boolean flag)
    story.append(Paragraph("Experience", h2))
    story.append(Paragraph(analysis.get("experience_text") or "Not detected", body))

    story.append(Paragraph("Projects", h2))
    story.append(Paragraph(analysis.get("projects_text") or "Not detected", body))

    # Resume Quality Checks
    story.append(Paragraph("Resume Quality Checks", h2))
    quality = analysis.get("quality", {})
    for check in quality.get("checks", []):
        mark = "PASS" if check["passed"] else "MISSING"
        story.append(Paragraph(f"[{mark}] {check['label']}", body))

    # Compatibility
    story.append(Paragraph("Resume Compatibility", h2))
    compat = analysis.get("compatibility", {})
    for ind in compat.get("indicators", []):
        mark = "PASS" if ind["ok"] else "CHECK"
        story.append(Paragraph(f"[{mark}] {ind['label']}", body))

    ats = compat.get("ats_score")
    if ats:
        story.append(Paragraph(f"ATS Readiness Score: {ats['overall_score']} — {ats['band']}", body))
        for name, cat in ats.get("categories", {}).items():
            story.append(Paragraph(f"  • {name.replace('_', ' ').title()}: {cat['score']}%", body))

    doc.build(story)
    return str(filepath)


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ])
