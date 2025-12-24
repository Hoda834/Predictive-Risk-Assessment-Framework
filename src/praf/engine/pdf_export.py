from io import BytesIO
from typing import List, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def build_pdf(
    context: Dict[str, Any],
    risk_rows: List[Dict[str, Any]],
    control_rows: List[Dict[str, Any]],
    readiness: Dict[str, Any],
) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    x0 = 16 * mm
    y = height - 18 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x0, y, "Risk Assessment Summary")
    y -= 10 * mm

    c.setFont("Helvetica", 10)
    c.drawString(x0, y, f"Activity: {context.get('activity','')}")
    y -= 5 * mm
    c.drawString(x0, y, f"Stage: {context.get('stage','')}")
    y -= 5 * mm
    c.drawString(x0, y, f"Industry: {context.get('industry','')}")
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x0, y, "Decision readiness")
    y -= 6 * mm

    c.setFont("Helvetica", 10)
    c.drawString(x0, y, f"Status: {readiness.get('readiness','')}")
    y -= 5 * mm
    reasons = ", ".join(readiness.get("reasons", []) or [])
    c.drawString(x0, y, f"Reasons: {reasons}")
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x0, y, "Risk register (ranked)")
    y -= 6 * mm

    c.setFont("Helvetica", 9)
    for i, r in enumerate(risk_rows[:25], start=1):
        line = f"{i}. {r.get('risk','')}"
        c.drawString(x0, y, line[:110])
        y -= 4.5 * mm
        meta = f"Owner: {r.get('owner','')} | Pattern: {r.get('pattern','')} | Score: {r.get('score','')} | Priority: {r.get('priority','')}"
        c.drawString(x0, y, meta[:110])
        y -= 6 * mm
        if y < 25 * mm:
            c.showPage()
            y = height - 18 * mm
            c.setFont("Helvetica", 9)

    c.showPage()
    y = height - 18 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x0, y, "Control coverage matrix")
    y -= 6 * mm

    c.setFont("Helvetica", 9)
    for row in control_rows[:60]:
        line = f"{row.get('control_id','')} {row.get('control_title','')} | linked: {row.get('linked_risks',0)} | status: {row.get('status','')}"
        c.drawString(x0, y, line[:110])
        y -= 4.5 * mm
        if y < 25 * mm:
            c.showPage()
            y = height - 18 * mm
            c.setFont("Helvetica", 9)

    c.save()
    return buf.getvalue()
