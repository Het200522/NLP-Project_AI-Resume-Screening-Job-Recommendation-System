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
    weights = scores.get("weights", {})
    score_rows = [["Overall Score", f"{scores.get('final_score', 0)}%"]]
    for cat_name, cat_score in cats.items():
        label = cat_name.replace("_", " ").title()
        if weights.get(cat_name) is not None:
            label = f"{label} ({weights[cat_name] * 100:.0f}%)"
        score_rows.append([label, "Not applicable" if cat_score is None else f"{cat_score}%"])
    score_table = Table(score_rows, colWidths=[220, 230])
    score_table.setStyle(_table_style())
    story.append(score_table)
    story.append(Paragraph(
        "Weighted multi-category ATS model. Categories that could not be "
        "evaluated for this role (for example experience, when the job "
        "description states no requirement) have their weight redistributed "
        "across the remaining categories.",
        ParagraphStyle("note", parent=body, fontSize=8, textColor=colors.grey)
    ))

    # Experience fit
    exp = analysis.get("experience") or {}
    if exp:
        story.append(Paragraph("Experience Fit", h2))
        story.append(Paragraph(
            f"Estimated experience: {exp.get('years', 0)} year(s). "
            f"Role requires: {exp.get('required') or 'not specified'}."
            + (f" Match: {exp.get('match_score')}%" if exp.get("match_score") is not None else ""),
            body,
        ))

    # Hard minimums the posting states, reported separately from the score
    knockouts = analysis.get("knockouts") or {}
    if knockouts.get("evaluated"):
        story.append(Paragraph("Hard Requirements (Knockout Gates)", h2))
        if knockouts.get("passed"):
            story.append(Paragraph("All hard requirements stated by the job description are met.", body))
        else:
            story.append(Paragraph(
                "The following stated requirements are not met: "
                + ", ".join(knockouts.get("failed", [])) + ".", body,
            ))
        for gate in knockouts.get("gates", []):
            mark = "MET" if gate["requirement_met"] else "NOT MET"
            story.append(Paragraph(
                f"[{mark}] {gate['label']} — {gate['requirement']}. {gate['detail']}", body,
            ))

    # Skills: flat ATS keyword match, every JD skill weighted equally
    total_skills = analysis.get("total_jd_skills") or 0
    matched_skills = analysis.get("matched_skills") or []
    missing_skills = analysis.get("missing_skills") or []
    coverage = (len(matched_skills) / total_skills * 100) if total_skills else 0.0

    story.append(Paragraph(
        f"Skills Matched ({len(matched_skills)} of {total_skills}, {coverage:.0f}% coverage)", h2
    ))
    story.append(Paragraph(", ".join(matched_skills) if matched_skills else "None detected", body))

    story.append(Paragraph("Skills Missing", h2))
    story.append(Paragraph(", ".join(missing_skills) if missing_skills else "None", body))

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
