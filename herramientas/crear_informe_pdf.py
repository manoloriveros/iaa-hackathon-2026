"""Renderiza el informe Markdown en cinco páginas para revisión. No accede a datos."""
import hashlib
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from pypdf import PdfReader

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "docs/INFORME_SEMANA1.md"
OUT = REPO / "docs/informe_semana1.pdf"
ink = colors.HexColor("#172b38")
brand = colors.HexColor("#174f59")
muted = colors.HexColor("#526574")
styles = {
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10.3, leading=14.5, textColor=ink, spaceAfter=8, alignment=TA_LEFT),
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=brand, spaceAfter=14),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=9, leading=12, textColor=muted, spaceAfter=12),
    "table": ParagraphStyle("cell", fontName="Helvetica", fontSize=9.2, leading=12, textColor=ink),
    "head": ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=9.2, leading=12, textColor=brand),
}


def inline(s):
    s = s.replace("–", "-").replace("—", "-").replace("\u2011", "-").replace("\u202f", " ")
    s = escape(s)
    s = re.sub(r"`([^`]+)`", r'<font name="Courier" size="8">\1</font>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    return s


def footer(canvas, doc):
    w, h = A4
    canvas.setStrokeColor(colors.HexColor("#d8e0e5"))
    canvas.line(42, h-39, w-42, h-39)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(muted)
    canvas.drawString(42, h-28, "IAA AI HACKATHON 2026  |  SEMANA 1  |  19 OCT 2026")
    canvas.drawString(42, 27, "Borrador de revisión. Semana 2, aprobación humana y reproducción completa pendientes.")
    canvas.drawRightString(w-42, 27, str(doc.page) + " / 5")


def main():
    text = SOURCE.read_text(encoding="utf-8")
    sections = re.split(r"^## ", text, flags=re.M)[1:]
    if len(sections) != 5:
        raise ValueError("Se esperan cinco secciones de informe")
    story = []
    for i, section in enumerate(sections):
        title, body = section.split("\n", 1)
        if i:
            story.append(PageBreak())
        story.append(Paragraph(inline(title), styles["title"]))
        if i == 0:
            story.append(Paragraph("Prima de riesgo por periodo de póliza | Candidato S30, respaldo S22 | Revisión propia asistida por IA", styles["subtitle"]))
        blocks = re.split(r"\n\s*\n", body.strip())
        for block in blocks:
            if block.lstrip().startswith("|"):
                rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in block.splitlines() if l.strip()]
                rows = [r for r in rows if not all(re.fullmatch(r"[-: ]+", c) for c in r)]
                width = A4[0] - 84
                widths = ([70,width-130,60] if rows[0][-1]=="Peso" else [65,150,width-215]) if len(rows[0])==3 else None
                cells = [[Paragraph(inline(c), styles["head"] if j==0 else styles["table"]) for c in row] for j,row in enumerate(rows)]
                t = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
                t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#eaf0f2")),
                                      ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),6),
                                      ("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),4),
                                      ("BOTTOMPADDING",(0,0),(-1,-1),4),
                                      ("LINEBELOW",(0,0),(-1,-1),.4,colors.HexColor("#d8e0e5"))]))
                story += [t,Spacer(1,9)]
            else:
                story.append(Paragraph(inline(" ".join(block.splitlines())), styles["body"]))
    doc = SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=54,bottomMargin=43,
                            title="Semana 1 - Prima de riesgo - Borrador de revisión",author="Participante, con asistencia de Codex y Claude")
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    reader = PdfReader(OUT)
    check = {"paginas":len(reader.pages),"fuente_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             "pdf_sha256":hashlib.sha256(OUT.read_bytes()).hexdigest(),
             "texto_por_pagina":[len(p.extract_text()) for p in reader.pages],"estado":"pendiente_inspeccion_visual"}
    (REPO / "registro/verificacion_pdf.json").write_text(json.dumps(check,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(check))
    if len(reader.pages)!=5:
        raise RuntimeError("El PDF no cumple el límite de cinco páginas; ajustar antes de entregar")


if __name__=="__main__":
    main()
