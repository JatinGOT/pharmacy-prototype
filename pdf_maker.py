"""Builds the printable PDF transcription with ReportLab."""
import io, datetime
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

TEAL = colors.HexColor("#0F766E")
NA = "[not stated on original]"


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(15 * mm, 10 * mm, "Digital transcription - not a prescription. Prepared with a prototype tool; not a certified clinical or pharmacy system.")
    canvas.drawRightString(195 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def make_pdf(rows, patient, doctor, rx_date, verified_by):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=20 * mm, title="Digital Transcription")
    ss = getSampleStyleSheet()
    cell = ParagraphStyle("cell", parent=ss["Normal"], fontSize=8.5, leading=11)
    head = ParagraphStyle("head", parent=cell, textColor=colors.white, fontName="Helvetica-Bold")
    title = ParagraphStyle("t", parent=ss["Title"], fontSize=17, textColor=TEAL)
    warn = ParagraphStyle("w", parent=ss["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#991B1B"))
    p = lambda s, st=cell: Paragraph(escape(str(s).strip()) or NA, st)

    story = [Paragraph("DIGITAL TRANSCRIPTION OF A PRESCRIPTION", title)]
    box = Table([[Paragraph("<b>This is NOT a prescription.</b> It is a typed copy of an original prescription written by a "
                            "doctor, checked by a person. It is not issued, signed or endorsed by the prescriber. "
                            "If anything differs from the original, <b>the original prevails</b>. Nothing has been "
                            "added, guessed or substituted.", warn)]], colWidths=[180 * mm])
    box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#991B1B")),
                             ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
                             ("PADDING", (0, 0), (-1, -1), 6)]))
    story += [box, Spacer(1, 8)]

    info = [[p("Patient name / reference"), p(patient or ""), p("Prescriber (as written)"), p(doctor or "")],
            [p("Date on original"), p(rx_date or ""), p("Transcribed on"), p(datetime.date.today().strftime("%d-%m-%Y"))],
            [p("Verified by"), p(verified_by), p(""), p("")]]
    t = Table(info, colWidths=[38 * mm, 52 * mm, 38 * mm, 52 * mm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                           ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F7F6")),
                           ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F0F7F6")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [t, Spacer(1, 10)]

    data = [[Paragraph(h, head) for h in ["#", "Medicine", "Strength", "Dose / Frequency", "Duration", "Doctor's original line"]]]
    for i, (_, r) in enumerate(rows.iterrows(), 1):
        data.append([p(i), p(r["Medicine"]), p(r["Strength"]), p(r["Dose / Frequency"]), p(r["Duration"]),
                     p(r.get("Original line", "") or "(added manually)")])
    mt = Table(data, colWidths=[8 * mm, 45 * mm, 22 * mm, 38 * mm, 22 * mm, 45 * mm], repeatRows=1)
    mt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), TEAL), ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6FAF9")]),
                            ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [mt, Spacer(1, 14),
              Paragraph("Fields marked [not stated on original] were not written by the prescriber (or could not be read) "
                        "and have deliberately been left blank.", cell),
              Spacer(1, 18), Paragraph("Verified by (signature): ______________________________", cell)]
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
