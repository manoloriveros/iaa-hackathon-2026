"""Renderiza el informe Markdown dentro del límite de cinco páginas. No accede a datos."""
import hashlib
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from pypdf import PdfReader

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "docs/archivo/semana1/INFORME_SEMANA1.md"
OUT = REPO / "docs/informe_semana1.pdf"
ink = colors.HexColor("#172b38")
brand = colors.HexColor("#174f59")
muted = colors.HexColor("#526574")
styles = {
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10.3, leading=14.5, textColor=ink, spaceAfter=8, alignment=TA_LEFT),
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=23, leading=27, textColor=brand, spaceAfter=10, keepWithNext=True),
    "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=brand, spaceBefore=12, spaceAfter=8, keepWithNext=True),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=9, leading=12, textColor=muted, spaceAfter=12),
    "table": ParagraphStyle("cell", fontName="Helvetica", fontSize=9.1, leading=12, textColor=ink),
    "head": ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=9.1, leading=12, textColor=brand),
}


def inline(s):
    s = s.replace("–", "-").replace("—", "-").replace("\u2011", "-").replace("\u202f", " ")
    s = escape(s)
    s = re.sub(r"`([^`]+)`", r'<font name="Courier" size="8">\1</font>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#174f59"><u>\1</u></link>', s)
    return s


def footer(canvas, doc):
    w, h = A4
    canvas.setStrokeColor(colors.HexColor("#d8e0e5"))
    canvas.line(42, h-39, w-42, h-39)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(muted)
    canvas.drawString(42, h-28, "IAA AI HACKATHON 2026  |  SEMANA 1  |  19 OCT 2026")
    canvas.drawString(42, 27, "Borrador para revisión del participante")
    canvas.drawRightString(w-42, 27, "Página " + str(doc.page))


def table_widths(headers):
    width = A4[0] - 84
    if len(headers) == 2:
        return [width * .32, width * .68]
    if headers[0] == "Ramo":
        return [width * .14, width * .36, width * .50]
    if headers[0] == "Candidato":
        return [width * .28, width * .36, width * .36]
    return [width * .23, width * .30, width * .47]


def main():
    text = SOURCE.read_text(encoding="utf-8")
    story = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for i, block in enumerate(blocks):
        if block.startswith("# "):
            story.append(Paragraph(inline(block[2:]), styles["title"]))
        elif block.startswith("## "):
            if block[3:] in {"Del coste observado al coste último", "Resultados y decisiones"}:
                story.append(PageBreak())
            story.append(Paragraph(inline(block[3:]), styles["section"]))
        elif block.lstrip().startswith("|"):
            rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in block.splitlines() if l.strip()]
            rows = [r for r in rows if not all(re.fullmatch(r"[-: ]+", c) for c in r)]
            if len({len(row) for row in rows}) != 1:
                raise ValueError("Tabla con columnas inconsistentes")
            cells = [[Paragraph(inline(c), styles["head"] if j==0 else styles["table"]) for c in row] for j,row in enumerate(rows)]
            t = Table(cells, colWidths=table_widths(rows[0]), repeatRows=1, hAlign="LEFT")
            t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#eaf0f2")),
                                  ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),7),
                                  ("RIGHTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),5),
                                  ("BOTTOMPADDING",(0,0),(-1,-1),5),
                                  ("LINEBELOW",(0,0),(-1,-1),.4,colors.HexColor("#d8e0e5"))]))
            story += [t,Spacer(1,9)]
        else:
            style = styles["subtitle"] if i == 1 else styles["body"]
            story.append(Paragraph(inline(" ".join(block.splitlines())), style))
    doc = SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=54,bottomMargin=43,
                            title="Una prima de riesgo para cada periodo de póliza",author="Participante, con asistencia de Codex y Claude")
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    reader = PdfReader(OUT)
    check = {"paginas":len(reader.pages),"fuente_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             "pdf_sha256":hashlib.sha256(OUT.read_bytes()).hexdigest(),
             "texto_por_pagina":[len(p.extract_text()) for p in reader.pages],"estado":"pendiente_inspeccion_visual"}
    (REPO / "registro/verificacion_pdf.json").write_text(json.dumps(check,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(check))
    if not 1 <= len(reader.pages) <= 5:
        raise RuntimeError("El PDF no cumple el límite de cinco páginas; ajustar antes de entregar")


if __name__=="__main__":
    main()
